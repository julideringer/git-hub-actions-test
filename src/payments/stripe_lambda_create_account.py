"""lambda function to register users into stripe"""
import os
import time
import stripe
import boto3
from botocore.exceptions import ClientError
from common_tools.payload_parser import success_return_parser, error_return_parser

stripe.api_key = os.environ["stripe_api_key"]
USER_DATA_TABLE = "user_data"

user_data_table = boto3.resource("dynamodb").Table(USER_DATA_TABLE)

def create_stripe_connected_account(**kwargs):
    """function to create connected account in stripe"""
    birthday = kwargs["kwargs"]["birthdate"].split("/")
    try:
        account = stripe.Account.create(
                type="custom",
                country="ES",
                email=kwargs["kwargs"]["email"],
                business_type="individual",
                business_profile={
                    "url": "https://bemube.com",
                },
                individual={
                    "first_name": kwargs["kwargs"]["name"],
                    "last_name": kwargs["kwargs"]["lastName"],
                    "email": kwargs["kwargs"]["email"],
                    "dob": {
                        "day": birthday[0],
                        "month": birthday[1],
                        "year": birthday[2]
                    }
                },
                tos_acceptance={
                    "date": int(time.time()),
                    "ip": kwargs["kwargs"]["source-ip"]
                },
                capabilities={
                    "card_payments": {"requested": False},
                    "transfers": {"requested": True}
                }
            )
        return account
    except stripe.error.StripeError as e:
        raise stripe.error.StripeError from e

def lambda_handler(event, context):
    """lambda handler"""
    event["body-json"]["source-ip"] = event["context"]["source-ip"]
    account = create_stripe_connected_account(kwargs = event["body-json"])
    try:
        customer = stripe.Customer.create(
            email=event["body-json"]["email"],
            name=event["body-json"]["name"] + event["body-json"]["lastName"]
        )
        user_data_table.update_item(
            Key={"user_id": event["body-json"]["userId"]},
            UpdateExpression= "SET stripe_id = :val1, customer_id = :val2",
            ExpressionAttributeValues= {":val1": account.id,
                                        ":val2": customer.id})
        return success_return_parser("", None)
    except ClientError as error:
        return error_return_parser(error, "")
