"""Lambda function to handle sign_up process"""
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

def sign_up_user(cognito_idp_client, **kwargs):
    """
    This method sign up a new user with Amazon Cognito
    """
    kargs = {
        "ClientId": os.environ["client_id"],
        "Username": kwargs["kwargs"]["userId"],
        "Password": kwargs["kwargs"]["password"],
        "UserAttributes": [{"Name": "email", "Value": kwargs["kwargs"]["email"]},
                            {"Name": "birthdate", "Value": kwargs["kwargs"]["birthdate"]},
                            {"Name": "gender", "Value": kwargs["kwargs"]["gender"]},
                            {"Name": "phone_number", "Value": kwargs["kwargs"]["phoneNumber"]},
                            {"Name": "name", "Value": kwargs["kwargs"]["name"]}]}
                            #{"Name": "last_name", "Value": kwargs["kwargs"]["lastName"]}]}
    if "client_secret" in os.environ:
        kargs["SecretHash"] = _secret_hash(kwargs["kwargs"]["userId"])
    response = cognito_idp_client.sign_up(**kargs)
    return response

def lambda_handler(event, context) -> str:
    """lambda handler"""
    username = event["body-json"]["userId"]
    try:
        response = sign_up_user(client, kwargs=event["body-json"])
        return success_return_parser(f"Confirmation email has been sent to {username}",
                                     {"userId": response["UserSub"]})
    except ClientError:
        return error_return_parser(f"Couldn't add user {username}", None)
