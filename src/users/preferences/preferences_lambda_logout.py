"""lambda function to logout"""
import os
import boto3
from botocore.exceptions import ClientError
from common_tools.payload_parser import success_return_parser, error_return_parser

client = boto3.client("cognito-idp", os.environ["region_name"])

def logout_function(username) -> str:
    """logout user from application"""
    response = client.admin_user_global_sign_out(
        UserPoolId=os.environ["userpool_id"],
        Username=username)
    return response

def lambda_handler(event, context):
    """lambda handler"""
    user_id = event["params"]["path"]["id"]
    try:
        logout_function(user_id)
        return success_return_parser(f"{user_id} logged out", None)
    except ClientError as error:
        return error_return_parser(error.response["Error"]["Message"],
                                   error.response["Error"]["Code"])
