"""function to retrieve bank account"""
import os
import boto3
from botocore.exceptions import ClientError
import stripe
from common_tools.payload_parser import success_return_parser, error_return_parser

stripe.api_key = os.environ["stripe_api_key"]

USER_DATA_TABLE = "user_data"

user_data_table = boto3.resource("dynamodb").Table(USER_DATA_TABLE)

def lambda_handler(event, context):
    """lambda handler"""
    user_id = event["params"]["path"]["id"]
    try:
        user_data = user_data_table.get_item(Key={"user_id": user_id})["Item"]
        bank_account = stripe.Account.retrieve_external_account(
            user_data["stripe_id"], user_data["account_id"])
        return success_return_parser("", {"last4": bank_account.last4})
    except ClientError as error:
        return error_return_parser(
            error.response["Error"]["Message"], error.response["Error"]["Code"])
