#!/usr/bin/env python3

import os
import logging
import json
import time
import hashlib
import hmac
import base64
import uuid
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor

import requests

_DEBUG = os.environ.get('DEBUG', 'True').lower() in ['true', '1']

# log settings
FORMAT = '%(levelname)s %(asctime)s \
    %(funcName)s %(filename)s %(lineno)d %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
if _DEBUG:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)

API_HOST = 'https://api.switch-bot.com'
PLUG_LIST_URL = f"{API_HOST}/v1.1/devices"
PLUG_STATUS_URL = f"{API_HOST}/v1.1/devices/deviceId/status"
PLUG_COMMAND_URL = f"{API_HOST}/v1.1/devices/deviceId/commands"

TIMEOUT = 10
WAIT_SECOND_SHORT = 3
WAIT_SECOND_LONG = 30

SWITCH_BOT_TOKEN = os.environ.get(
    "SWITCH_BOT_TOKEN", "")
SWITCH_BOT_SECRET = os.environ.get(
    "SWITCH_BOT_SECRET", "")

CHECK_ONLINE = os.environ.get(
    "CHECK_ONLINE", False)

SORACOM_ENDPOINT = os.environ.get(
    'SORACOM_ENDPOINT', 'https://jp.api.soracom.io/')

SORACOM_AUTH_KEY_ID = os.environ.get(
    "SORACOM_AUTH_KEY_ID", "")
SORACOM_AUTH_KEY = os.environ.get(
    "SORACOM_AUTH_KEY", "")
SORA_CAM_BASE_PATH = 'v1/sora_cam/devices'

apiHeader = {}
nonce = uuid.uuid4()
t = int(round(time.time() * 1000))
string_to_sign = f'{SWITCH_BOT_TOKEN}{t}{nonce}'
string_to_sign = bytes(string_to_sign, 'utf-8')
secret = bytes(SWITCH_BOT_SECRET, 'utf-8')

sign = base64.b64encode(hmac.new(
    secret, msg=string_to_sign, digestmod=hashlib.sha256).digest())

# Build api header JSON
apiHeader['Authorization'] = SWITCH_BOT_TOKEN
apiHeader['Content-Type'] = 'application/json'
apiHeader['charset'] = 'utf8'
apiHeader['t'] = str(t)
apiHeader['sign'] = sign
apiHeader['nonce'] = str(nonce)


def _get_request(url):
    logger.debug("url: %s", url)
    res = requests.get(
        url,
        headers=apiHeader,
        timeout=TIMEOUT)
    res.raise_for_status()
    data = res.json()
    if data['message'] == 'success':
        logger.debug("status: %s", res.status_code)
        return res.json()
    return {}


def _post_request(url, params):
    logger.debug("url: %s params: %s", url, params)
    res = requests.post(
        url,
        data=json.dumps(params),
        headers=apiHeader,
        timeout=TIMEOUT)
    res.raise_for_status()
    data = res.json()
    if data['message'] == 'success':
        logger.debug("status: %s", res.status_code)
        return res.json()
    return {}


def smart_plug_toggle(device_id):
    params = {
        "command": "toggle",
        "commandType": "command",
        "parameter": "default",
    }
    url = PLUG_COMMAND_URL.replace('deviceId', device_id)
    return _post_request(url, params)


def smart_plug_off(device_id):
    params = {
        "command": "turnOff",
        "commandType": "command",
        "parameter": "default",
    }
    url = PLUG_COMMAND_URL.replace('deviceId', device_id)
    return _post_request(url, params)


def smart_plug_on(device_id):
    params = {
        "command": "turnOn",
        "commandType": "command",
        "parameter": "default",
    }
    url = PLUG_COMMAND_URL.replace('deviceId', device_id)
    return _post_request(url, params)


def smart_plug_status(device_id):
    url = PLUG_STATUS_URL.replace('deviceId', device_id)
    return _get_request(url)


def find_plug_by_name(camera_name):
    # get plug list
    res = _get_request(PLUG_LIST_URL)
    plug_list = res.get('body', []).get('deviceList', [])
    for plug in plug_list:
        logger.debug("camera_name: %s, plug: %s", camera_name, plug)
        if camera_name == plug.get('deviceName', ''):
            return plug
    return None


def off_on_smart_plug(camera_name):
    plug = find_plug_by_name(camera_name)
    if not plug:
        logger.info("can't find a smart plug for %s", camera_name)
        return False
    logger.info("off/onn plug: %s", plug)
    device_id = plug.get('deviceId', '')
    _ = smart_plug_off(device_id)
    logger.debug("%s is off", plug)
    time.sleep(WAIT_SECOND_SHORT)
    _ = smart_plug_on(device_id)
    logger.debug("%s is on", plug)
    return True


def get_offline_cameras():
    url = urljoin(SORACOM_ENDPOINT, 'v1/auth')
    payload = {
        "authKeyId": SORACOM_AUTH_KEY_ID,
        "authKey": SORACOM_AUTH_KEY,
    }
    try:
        response = requests.post(
            url=url, json=payload,
            timeout=TIMEOUT)
    except Exception as error:
        logger.error("failed to authenticate: %s", error, exc_info=True)
        raise
    param = response.json()

    headers = {
        'X-Soracom-API-Key': param.get('apiKey'),
        'X-Soracom-Token': param.get('token'),
        'accept': "application/json",
        'Content-Type': "application/json"
    }
    url = urljoin(SORACOM_ENDPOINT, SORA_CAM_BASE_PATH)
    try:
        response = requests.get(
            headers=headers,
            url=url,
            timeout=TIMEOUT)
    except Exception as error:
        logger.error("failed to get devices: %s", error, exc_info=True)
        raise
    device_list = response.json()
    off_line_devices = []
    for device in device_list:
        if not device.get('connected', True):
            device_status = {}
            device_status['device_name'] = device.get('name', None)
            device_status['device_id'] = device.get('deviceId', None)
            device_status['last_connection'] = device.get(
                'lastConnectedTime', None)
            off_line_devices.append(device_status)
    return off_line_devices


def handler(event, context):
    # list offline cameras
    off_cameras = get_offline_cameras()
    logger.debug("off_line_cameras: %s", off_cameras)

    # turn off and on smart plug for offline cameras
    camera_name_list = [
        camera.get('device_name', '') for camera in off_cameras]
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(
            executor.map(
                off_on_smart_plug,
                camera_name_list))
    for camera_id, result in zip(camera_name_list, results):
        if result:
            logger.info("Plug for Camera: %s is turned off/on.", camera_id)
        else:
            logger.info("Plug for Camera: %s can't be turned \
                off/on.", camera_id)
