"""lambda function to handle the confirmation of the forgot password request"""
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

def confirm_forgot_password(**kwargs) -> str:
    """
    This method is in charge of change the user password on the user pool
    """
    kargs = {
        "ClientId": os.environ["client_id"],
        "Username": kwargs["kwargs"]["username"],
        "Password": kwargs["kwargs"]["password"],
        "ConfirmationCode": kwargs["kwargs"]["code"]
    }
    if "client_secret" in os.environ:
        kargs["SecretHash"] = _secret_hash(kwargs["kwargs"]["username"])
    response = client.confirm_forgot_password(**kargs)
    return response

def lambda_handler(event, context):
    """
    An AWS lambda handler that receives events from the Access API GW to
    confirm the new password. The lambda receives the confirmation code and
    the new password.

    :param username [str]: username of the user to change the password
    :param confirmation_code [str]: the confirmation code for the password change
    :param new_password [str]: the new password of the user
    """
    try:
        confirm_forgot_password(kwargs=event["body-json"])
        return success_return_parser("Password changed", None)
    except ClientError:
        return error_return_parser("Error changing password", None)
