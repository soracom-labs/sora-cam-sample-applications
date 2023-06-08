#!/usr/bin/env python3

import aws_cdk as cdk

from sora_cam_smart_plug.sora_cam_smart_plug_stack import LambdaCronStack

app = cdk.App()
LambdaCronStack(app, "sora-cam-smart-plug")

app.synth()
