"""create external bank account"""
import os
import boto3
from botocore.exceptions import ClientError
import stripe
from common_tools.payload_parser import success_return_parser, error_return_parser


stripe.api_key = os.environ["stripe_api_key"]

USER_DATA_TABLE = "user_data"

user_data_table = boto3.resource("dynamodb").Table(USER_DATA_TABLE)

def add_address(cc_id, address_object):
    """function to add address"""
    stripe.Account.modify(
        connected_account_id = cc_id,
        individual = {
            "address": {
                "city": address_object["city"],
                "country": address_object["country"],
                "line1": address_object["line1"],
                "postal_code": address_object["postalCode"],
                "state": address_object["state"]}
            }
        )

def create_bank_account(account_id, account_number, holder_name, holder_type="individual"):
    """function to create a bank account in stripe"""
    bank_account_token = stripe.Token.create(
        bank_account={
            "country": "ES",
            "currency": "eur",
            "account_holder_name": holder_name,
            "account_holder_type": holder_type,
            "account_number": account_number
        },
    )
    external_account = stripe.Account.create_external_account(
        account_id, external_account=bank_account_token.id)
    return external_account

def lambda_handler(event, context):
    """lambda_handler"""
    user_id = event["body-json"]["userId"]
    try:
        user_data = user_data_table.get_item(Key={"user_id": user_id})["Item"]
        connected_account_id = user_data["stripe_id"]
        bank_account = create_bank_account(
            connected_account_id,
            event["body-json"]["accountNumber"], event["body-json"]["holderName"])
        stripe.Account.modify_external_account(
            connected_account_id, bank_account.id, default_for_currency=True)
        if user_data["account_id"]:
            stripe.Account.delete_external_account(connected_account_id, user_data["account_id"])
        add_address(connected_account_id, event["body-json"]["address"])
        user_data_table.update_item(
            Key={"user_id": user_id},
            UpdateExpression= "SET account_id = :val1",
            ExpressionAttributeValues= {":val1": bank_account.id})
        return success_return_parser("Bank account created properly", None)
    except stripe.error.StripeError as e:
        return error_return_parser(e.user_message, None)
    except ClientError as error:
        return error_return_parser(error.response["Error"]["Message"],
                                   error.response["Error"]["Code"])
