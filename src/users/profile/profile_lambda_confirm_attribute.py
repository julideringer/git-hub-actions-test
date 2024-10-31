"""Lambda function to handle confirm user mail"""
import os
import boto3
from botocore.exceptions import ClientError
from common_tools.payload_parser import success_return_parser, error_return_parser

USERS_TABLE = "users"

client = boto3.client("cognito-idp", os.environ["region_name"])
users_table = boto3.resource("dynamodb").Table(USERS_TABLE)

def confirm_attribute(**kwargs):
    """
    This method confirms the code sended to the mail
    """
    kargs = {
        "AccessToken": kwargs["kwargs"]["accessToken"],
        "AttributeName": kwargs["kwargs"]["attributeType"],
        "Code": kwargs["kwargs"]["code"]
    }
    response = client.verify_user_attribute(**kargs)
    return response

def lambda_handler(event, context) -> str:
    """lambda handler"""
    event["body-json"]["accessToken"] = event["params"]["header"]["Authorization"].split(" ")[1]
    user_id = event["params"]["path"]["id"]
    attribute_type = event["body-json"]["attributeType"]
    try:
        confirm_attribute(kwargs=event["body-json"])
        users_table.update_item(
            Key={"user_id": user_id},
            UpdateExpression="set #nm = :n",
            ExpressionAttributeNames={"#nm": "verified"},
            ExpressionAttributeValues={":n": True})
        return success_return_parser(f"{user_id} {attribute_type} confirmed", None)
    except ClientError as error:
        return error_return_parser(error.response["Error"]["Message"],
                                   error.response["Error"]["Code"])
