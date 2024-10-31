"""script to send money to connected account"""
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
    destination_user_id = event["body-json"]["userId"]
    try:
        destination_user_data = user_data_table.get_item(
            Key={"user_id": destination_user_id})["Item"]
        external_account = stripe.Account.retrieve_external_account(
          destination_user_data["stripe_id"], destination_user_data["account_id"])
        stripe.Payout.create(
            amount=event["body-json"]["amount"],
            currency=event["body-json"]["currency"],
            destination=external_account.id,# ID del método de pago externo (cuenta bancaria)
            description='Payout to user account',
            source_type='bank_account'
        )
        return success_return_parser("","")
    except ClientError:
        return error_return_parser("", "")
    except stripe.error.StripeError:
        return error_return_parser("", "")
