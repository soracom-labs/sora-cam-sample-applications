# SoraCam and Smart Plug

Find offline cameras via [SoraCam listSoraCamDevices API](https://users.soracom.io/ja-jp/tools/api/reference/#/SoraCam/listSoraCamDevices), and turn off and on a smart plug.

## Configuration

The following variables must be set at the `sora_cam_smart_plug/.env` file.

- `SORACOM_AUTH_KEY_ID`: SORACOM API Key
- `SORACOM_AUTH_KEY`:  SORACOM API Token
- `SWITCH_BOT_TOKEN`: SwitchBot API Token
- `SWITCH_BOT_SECRET`: SwitchBot API Secret
- `CHECK_INTERVAL_MINUTES`: Interval (minutes) to be executed periodically by AWS Lambda

## Installation

```bash
cdk deploy
```

## License
This project is open source and available under the MIT License.
