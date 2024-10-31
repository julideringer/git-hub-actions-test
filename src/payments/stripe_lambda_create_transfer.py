"""lambda function to transfer money between connected accounts"""
import os
import stripe
import boto3
from botocore.exceptions import ClientError
from common_tools.payload_parser import success_return_parser, error_return_parser

USER_DATA_TABLE = "user_data"

stripe.api_key = os.environ["stripe_api_key"]
user_data_table = boto3.resource("dynamodb").Table(USER_DATA_TABLE)

def lambda_handler(event, context):
    """lambda handler"""
    destination_id = event["body-json"]["destination"]
    try:
        destination_user_data = user_data_table.get_item(Key={"user_id": destination_id})["Item"]
        transfer = stripe.Transfer.create(
            amount=event["body-json"]["amount"],
            currency="eur",
            destination=destination_user_data["account_id"])
        return success_return_parser("", "")
    except stripe.error.StripeError:
        return error_return_parser("", None)
    except ClientError:
        return error_return_parser("", None)
