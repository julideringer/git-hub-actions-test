"""lambda function to remove user from user pool"""
import os
import boto3
from botocore.exceptions import ClientError
from common_tools.get_user_info import get_user_info
from common_tools.payload_parser import dict_parser_to_camel_case
from common_tools.payload_parser import success_return_parser, error_return_parser

USERS_TABLE = "users"

client = boto3.client("cognito-idp", os.environ["region_name"])

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

users_table = boto3.resource("dynamodb").Table(USERS_TABLE)
def lambda_handler(event, context):
    """lambda habdler"""
    try:
        user_id = event["params"]["querystring"]["userId"]
        get_user(user_id)
        user_object = users_table.get_item(Key={"user_id": user_id})["Item"]
        return success_return_parser(None, dict_parser_to_camel_case(get_user_info(user_object)))
    except ClientError:
        return error_return_parser("Unable to retrieve user", None)
