#!/usr/bin/env python3

import os

from aws_cdk import (
    aws_lambda as _lambda,
    aws_lambda_python_alpha as _lambda_python,
    aws_events as events,
    aws_events_targets as targets,
    Stack, Duration
)
from constructs import Construct
from dotenv import load_dotenv
load_dotenv()


# Read .env file
with open('./sora_cam_smart_plug/.env') as f:
    env_vars = {line.split('=')[0]: line.split('=')[1].replace("\n", "")
                for line in f}


# check interval by minutes
CHECK_INTERVAL_MINUTES = int(os.environ.get(
    'CHECK_INTERVAL_MINUTES', 60))


class LambdaCronStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create the Lambda function
        my_lambda = _lambda_python.PythonFunction(
            self, 'SoraCamSmartPlug',
            runtime=_lambda.Runtime.PYTHON_3_9,
            entry='lambda/',
            handler='handler',
            timeout=Duration.seconds(120),
            architecture=_lambda.Architecture.X86_64,
            environment=env_vars
        )

        # Create CloudWatch Event Rule for Lambda to execute every
        # CHECK_INTERVAL_MINUTES minutes
        rule = events.Rule(
            self, 'Rule',
            schedule=events.Schedule.rate(Duration.minutes(
                CHECK_INTERVAL_MINUTES))
        )

        # Set the Lambda function as the target of the Rule
        rule.add_target(targets.LambdaFunction(my_lambda))
