"""lambda function to remove user from user pool"""
import os
import boto3
from botocore.exceptions import ClientError
from src.common_tools.payload_parser import success_return_parser, error_return_parser

USERS_TABLE = "users"

client = boto3.client("cognito-idp", os.environ["region_name"])
table = boto3.client("dynamodb")

def delete_user(access_token) -> str:
    """function to delete user from user pool"""
    kargs = {"AccessToken": access_token}
    response = client.delete_user(**kargs)
    return response

def lambda_handler(event, context):
    """lambda habdler"""
    access_token = event["params"]["header"]["Authorization"].split(" ")[1]
    user_id = event["params"]["querystring"]["userId"]
    try:
        delete_user(access_token)
        table.delete_item(TableName=USERS_TABLE, Key={"user_id": {"S": user_id}})
        return success_return_parser("User has been removed successfully", None)
    except ClientError:
        return error_return_parser("unable to delete User", None)
