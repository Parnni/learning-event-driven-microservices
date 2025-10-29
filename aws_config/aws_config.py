import os
from typing import Dict

import localstack.sdk.aws
from dotenv import load_dotenv

load_dotenv()


def load_aws_config() -> Dict[str, str]:
    """Loads AWS config."""
    debug = str(os.getenv("DEBUG", "0")) == "1"

    if debug:
        client = localstack.sdk.aws.AWSClient()
        return {
            "endpoint_url": client.configuration.host,
            "region_name": "us-east-1",
            "aws_access_key_id": "test",
            "aws_secret_access_key": "test",
        }

    required = ["AWS_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]
    for key in required:
        if not os.getenv(key):
            raise RuntimeError(f"Missing required AWS environment variable: {key}")

    return {
        "endpoint_url": str(os.getenv("AWS_ENDPOINT_URL")),
        "region_name": str(os.getenv("AWS_REGION")),
        "aws_access_key_id": str(os.getenv("AWS_ACCESS_KEY_ID")),
        "aws_secret_access_key": str(os.getenv("AWS_SECRET_ACCESS_KEY")),
    }
