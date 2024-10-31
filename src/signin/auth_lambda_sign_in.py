"""Lambda function to handle sign_in process"""
import os
import hmac
import base64
import hashlib
import boto3
from botocore.exceptions import ClientError
from common_tools.payload_parser import success_return_parser, error_return_parser

USERS_TABLE = 'users'

users_table = boto3.resource('dynamodb').Table(USERS_TABLE)
client = boto3.client('cognito-idp', os.environ['region_name'])

def _secret_hash(username):
    key = os.environ['client_secret'].encode()
    msg = bytes(username + os.environ['client_id'], 'utf-8')
    secret_hash = base64.b64encode(
        hmac.new(key, msg, digestmod=hashlib.sha256).digest()).decode()
    return secret_hash

def start_sign_in(**kwargs):
    """This method signs in a given user name and retrieve the tokens"""
    kargs = {
        'ClientId': os.environ['client_id'],
        'AuthFlow': kwargs["kwargs"]["AuthFlow"],
        'AuthParameters': {'USERNAME': kwargs["kwargs"]["username"],
                           'PASSWORD': kwargs["kwargs"]["password"]}
    }
    if 'client_secret' in os.environ:
        kargs['AuthParameters']['SECRET_HASH'] = _secret_hash(kwargs["kwargs"]["username"])
    response = client.initiate_auth(**kargs)
    return response

def get_user_id(access_token):
    """function to retrieve user id from access token"""
    return client.get_user(AccessToken=access_token)["Username"]

def lambda_handler(event, context) -> str:
    """
    An AWS lambda handler that receives events from an API GW and starts the sign in process 
    for new users on the application. Takes the required attributes and interact with cognito 
    IDP to retrieve the access and refresh token.
    
    :param username [str]: the username of the user that is starting the sign_in process
    :param password [str]: the password given from the user to start the sign_in process
    """
    try:
        event["body-json"]["AuthFlow"] = 'USER_PASSWORD_AUTH'
        token = start_sign_in(kwargs=event["body-json"])
        user_id = get_user_id(token["AuthenticationResult"]["AccessToken"])
        update_expression = 'SET device_token = :value1, platform = :value2'
        expression_attribute_values = {
            ':value1': event['body-json']["deviceToken"],
            ':value2': event['body-json']["platform"]}
        users_table.update_item(
            Key={'user_id': user_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values
        )
        return success_return_parser(
            "Login successfully",
            {
                "accessToken": token["AuthenticationResult"]["AccessToken"],
                "refreshToken": token["AuthenticationResult"]["RefreshToken"],
                "idToken": token["AuthenticationResult"]["IdToken"],
                "stripeApiKey": os.environ["stripe_api_key"],
                #"mapsApiKey": os.environ["google_maps_api_key"]
            })
    except ClientError:
        return error_return_parser("Login failed", None)
