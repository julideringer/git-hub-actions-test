"""Lambda function to handle confirm user mail"""
import os
import boto3
from botocore.exceptions import ClientError
from common_tools.payload_parser import success_return_parser, error_return_parser

USERS_TABLE = "users"

client = boto3.client("cognito-idp", os.environ["region_name"])
users_table = boto3.resource("dynamodb").Table(USERS_TABLE)

def admin_update_user(**kargs):
    """method to update user attributes"""
    kargs["kargs"]["UserPoolId"] = os.environ["userpool_id"]
    response = client.admin_update_user_attributes(**kargs["kargs"])
    return response

def lambda_handler(event, context) -> str:
    """lambda handler"""
    user_id = event["params"]["path"]["id"]
    try:
        user_object = users_table.get_item(Key={"user_id": user_id})["Item"]
        user_attributes = {
            "Username": user_id,
            "UserAttributes": [{"Name": "email", "Value": user_object["email"]}]
        }
        admin_update_user(kargs=user_attributes)
        return success_return_parser(f"Confirmation email has been send to {user_id}",
                                     None)
    except ClientError:
        return error_return_parser(f"Couldn't send code to {user_id}", None)
