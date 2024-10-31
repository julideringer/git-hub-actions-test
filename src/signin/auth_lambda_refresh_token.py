"""Lambda function to refresh the token"""
import os
import hmac
import base64
import hashlib
import boto3
from botocore.exceptions import ClientError
from common_tools.payload_parser import success_return_parser, error_return_parser

client = boto3.client("cognito-idp", os.environ["region_name"])

def _secret_hash(username):
    key = os.environ["client_secret"].encode()
    message = bytes(username + os.environ["client_id"], "utf-8")
    secret_hash = base64.b64encode(
        hmac.new(key, message, digestmod=hashlib.sha256).digest()).decode()
    return secret_hash

def start_sign_in(**kwargs):
    """
    This method receives a valid refresh_token and sends back updated
    access token and id token. For this lambda specifically is only
    to send back the refresh token.
    """
    kargs = {
        "ClientId": os.environ["client_id"],
        "AuthFlow": kwargs["kwargs"]["AuthFlow"],
        "AuthParameters": {"REFRESH_TOKEN": kwargs["kwargs"]["RefreshToken"]}
    }
    if "client_secret" in os.environ:
        kargs["AuthParameters"]["SECRET_HASH"] = _secret_hash(kwargs["kwargs"]["username"])
    response = client.initiate_auth(**kargs)
    return response

def lambda_handler(event, context) -> str:
    """
    An AWS lambda handler that receives events from an API GW and refreshs tokens.
    The user sends the old refresh token and asks for the new one.

    :param username [str]: the username of the user that is requesting the token
    :param refresh_token [str]: the token used to get the new tokens
    """
    try:
        kargs = {
            "RefreshToken": event["params"]["header"]["refreshToken"],
            "AuthFlow": "REFRESH_TOKEN",
            "Username": event["body-json"]["username"]
        }
        response = start_sign_in(kwargs=kargs)
        return success_return_parser(
            "Successfull operation",
            {
                "accessToken": response["AuthenticationResult"]["AccessToken"],
                "idToken": response["AuthenticationResult"]["IdToken"],
                "tokenType": response["AuthenticationResult"]["TokenType"]
            })
    except ClientError:
        return error_return_parser("Operation failed", None)
