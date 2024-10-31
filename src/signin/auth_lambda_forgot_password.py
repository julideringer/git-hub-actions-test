"""lambda function to handle forgot password request"""
import os
import hmac
import base64
import hashlib
import boto3
from botocore.exceptions import ClientError
from common_tools.payload_parser import error_return_parser, success_return_parser

client = boto3.client('cognito-idp', os.environ['region_name'])

def _secret_hash(username):
    key = os.environ['client_secret'].encode()
    msg = bytes(username + os.environ['client_id'], 'utf-8')
    secret_hash = base64.b64encode(
        hmac.new(key, msg, digestmod=hashlib.sha256).digest()).decode()
    return secret_hash

def forgot_password(username) -> str:
    """
    This method is in charge of change the user password on the user pool
    """
    kargs = {
            'ClientId': os.environ['client_id'],
            'Username': username
        }
    if 'client_secret' in os.environ:
        kargs['SecretHash'] = _secret_hash(username)
    response = client.forgot_password(**kargs)
    return response

def lambda_handler(event, context):
    """
    An AWS lambda handler that receives events from the Access API GW and 
    starts the forgot password process. The lambda receives the username
    and sends a validation code to the verified email.
    
    :param username [str]: the username of the user that is starting the
    forgot_password request
    """
    username = event["body-json"]["username"]
    try:
        forgot_password(username)
        return success_return_parser(f"Email has been sent to {username}", None)
    except ClientError:
        return error_return_parser("Error sending confirmation email", None)
