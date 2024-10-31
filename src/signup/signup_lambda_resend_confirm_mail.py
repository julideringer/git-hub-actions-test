"""Lambda function to handle confirm user mail"""
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
    msg = bytes(username + os.environ["client_id"], "utf-8")
    secret_hash = base64.b64encode(
        hmac.new(key, msg, digestmod=hashlib.sha256).digest()).decode()
    return secret_hash

def get_user(username) -> str:
    """
    This method is in charge of get user info
    """
    kargs = {
        "UserPoolId": os.environ["userpool_id"],
        "Username": username
    }
    response = client.admin_get_user(**kargs)
    return response

def resend_user_code(username):
    """
    This method asks for a new confirmation code for a given user
    """
    kargs = {
        "ClientId": os.environ["client_id"],
        "Username": username
    }
    if "client_secret" in os.environ:
        kargs["SecretHash"] = _secret_hash(username)
    response = client.resend_confirmation_code(**kargs)
    return response

def lambda_handler(event, context) -> str:
    """lambda handler"""
    username = event["body-json"]["userId"]
    try:
        if get_user(event["body-json"]["username"])["UserStatus"] == "UNCONFIRMED":
            resend_user_code(username)
            return success_return_parser(f"Confirmation email has been send to {username}",
                                         None)
        return success_return_parser("User is already confirmed", None)
    except ClientError:
        return error_return_parser(f"Couldn't send code to {username}", None)
