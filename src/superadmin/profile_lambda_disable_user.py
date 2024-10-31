"""Lambda function to handle sign_up process"""
import os
import boto3
from botocore.exceptions import ClientError
from src.common_tools.payload_parser import success_return_parser, error_return_parser

client = boto3.client("cognito-idp", os.environ["region_name"])

def disable_user(**kwargs):
    """
    This method disable a user registered with Amazon Cognito
    """
    kargs = {
        "Username": kwargs["kwargs"]["Username"],
        "UserPoolId": kwargs["kwargs"]["UserPoolId"],
       }
    response = client.admin_disable_user(**kargs)
    return response

def lambda_handler(event, context) -> str:
    """
    An AWS lambda handler that receives events from an API GW and starts the disble process 
    for  users on the application. Takes the required attributes and interact with cognito 
    IDP to do the onboarding.
    
    :param Username [str]: the Username of the user that is starting the disable process
    :param UserPoolId [str]: the UserPoolId given from the user to start the disable process
    """
    username = event["body-json"]["Username"]
    try:
        disable_user(kwargs=event["body-json"]["Username"])
        return success_return_parser(f"User {username} disabled", None)
    except ClientError:
        return error_return_parser(f"Unable to disble {username} user", None)
