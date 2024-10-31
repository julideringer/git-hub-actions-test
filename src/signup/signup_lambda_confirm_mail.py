"""Lambda function to handle confirm user mail"""
import os
import time
import hmac
from datetime import datetime
import base64
import hashlib
import boto3
from botocore.exceptions import ClientError
import stripe
from common_tools.payload_parser import success_return_parser, error_return_parser

USERS_TABLE = "users"
USERS_CONNECTIONS_TABLE = "user_connections"
USERS_RESERVATIONS_TABLE = "user_reservations"
USERS_REQUESTS_TABLE = "user_requests"
USERS_DATA_TABLE = "user_data"
USERS_CHAT_TABLE = "user_chats"

users_table = boto3.resource("dynamodb").Table(USERS_TABLE)
user_connections_table = boto3.resource("dynamodb").Table(USERS_CONNECTIONS_TABLE)
user_reservations_table = boto3.resource("dynamodb").Table(USERS_RESERVATIONS_TABLE)
user_requests_table = boto3.resource("dynamodb").Table(USERS_REQUESTS_TABLE)
user_data_table = boto3.resource("dynamodb").Table(USERS_DATA_TABLE)
user_chats_table = boto3.resource("dynamodb").Table(USERS_CHAT_TABLE)

cognito_client = boto3.client("cognito-idp", os.environ["region_name"])

def create_stripe_customer(email, full_name):
    """function to create customer in stripe"""
    customer = stripe.Customer.create(email=email, name=full_name)
    return customer

def create_stripe_connected_account(**kargs):
    """function to create connected account in stripe"""
    birthday = kargs["kargs"]["birthdate"].split("/")
    name = kargs["kargs"]["name"].split(' ')
    try:
        account = stripe.Account.create(
                type="custom",
                country="ES",
                email=kargs["kargs"]["email"],
                business_type="individual",
                business_profile={
                    "url": "https://bemube.com",
                },
                individual={
                    "first_name": name[0],
                    "last_name": name[1],
                    "email": kargs["kargs"]["email"],
                    "dob": {
                        "day": birthday[0],
                        "month": birthday[1],
                        "year": birthday[2]
                    }
                },
                tos_acceptance={
                    "date": int(time.time()),
                    "ip": kargs["kargs"]["source-ip"]
                },
                capabilities={
                    "card_payments": {"requested": False},
                    "transfers": {"requested": True}
                }
            )
        return account
    except stripe.error.StripeError as e:
        raise stripe.error.StripeError from e

def cognito_get_user_info(username):
    """retrieve user info"""
    #TODO: add last name to user pool and to this function
    kargs = {
        "UserPoolId": os.environ["userpool_id"],
        "Username": username
    }
    user_attributes = cognito_client.admin_get_user(**kargs)["UserAttributes"]
    email, verified, name, gender, birthdate = None, None, None, None, None
    for attribute in user_attributes:
        if attribute["Name"] == "email_verified":
            verified = attribute["Value"]
        if attribute["Name"] == "name":
            name = attribute["Value"]
        if attribute["Name"] == "gender":
            gender = attribute["Value"]
        if attribute["Name"] == "birthdate":
            birthdate = attribute["Value"]
        if attribute["Name"] == "email":
            email = attribute["Value"]
    return email, verified, name, gender, birthdate

def _secret_hash(username):
    key = os.environ["client_secret"].encode()
    message = bytes(username + os.environ["client_id"], "utf-8")
    secret_hash = base64.b64encode(
        hmac.new(key, message, digestmod=hashlib.sha256).digest()).decode()
    return secret_hash

def confirm_user_mail(**kwargs):
    """
    This method confirms the code sended to the mail
    """
    kargs = {
        "ClientId": os.environ["client_id"],
        "Username": kwargs["kwargs"]["userId"],
        "ConfirmationCode": kwargs["kwargs"]["confirmationCode"]
    }
    if "client_secret" in os.environ:
        kargs["SecretHash"] = _secret_hash(kwargs["kwargs"]["userId"])
    response = cognito_client.confirm_sign_up(**kargs)
    return response

def describe_user_pool():
    """retrieve userpool info for Oauth2.0 authentication"""
    kargs = {
        "UserPoolId": os.environ["userpool_id"],
        "ClientId": os.environ["client_id"]
    }
    response = cognito_client.describe_user_pool_client(**kargs)
    user_pool_configuration = {}
    user_pool_configuration["clientId"] = response["UserPoolClient"]["ClientId"]
    if response["UserPoolClient"].get("ClientSecret"):
        user_pool_configuration["clientSecret"] = response["UserPoolClient"]["ClientSecret"]
    user_pool_configuration["callbackUrls"] = []
    user_pool_configuration["callbackUrls"] = response["UserPoolClient"]["CallbackURLs"]
    user_pool_configuration["allowedOauthFlows"] = []
    user_pool_configuration["allowedOauthFlows"] = response["UserPoolClient"]["AllowedOAuthFlows"]
    user_pool_configuration["allowedOauthScopes"] = []
    user_pool_configuration["allowedOauthScopes"] = response["UserPoolClient"]["AllowedOAuthScopes"]
    return user_pool_configuration

def lambda_handler(event, context) -> str:
    """
    An AWS lambda handler that receives events from an API GW and confirms the email account
    from the given user. Finishing in that way the sign_up proces.
    Takes the required attributes and interact with cognito IDP to do the onboarding.
    
    :param username [str]: the username of the user that is starting the sign_up process
    :param confirmation_code [str]: the single use code to validate the user email 
    """
    user_id = event["body-json"]["userId"]
    user_pool_configuration = {}
    try:
        user_pool_configuration = describe_user_pool()
        confirm_user_mail(kwargs = event["body-json"])
        email, verified, name, gender, birthdate = cognito_get_user_info(user_id)
        user_info = {
            "user_id": user_id, "name": name, "last_name": "", "verified": False, "gender": gender,
            "birthdate": birthdate, "email": email, "picture": "", "address": "", "biography": "",
            "creation_date": str(datetime.now().isoformat(timespec="seconds"))}
        if verified == "true":
            user_info["verified"] = True
        users_table.put_item(Item=user_info)
        customer = create_stripe_customer(email, name)
        user_info["source-ip"] = event["context"]["source-ip"]
        stripe_cc = create_stripe_connected_account(kargs=user_info)
        user_reservations_table.put_item(Item = {"user_id": user_id, "reservations": []})
        user_requests_table.put_item(Item = {"user_id": user_id, "requests": []})
        user_chats_table.put_item(Item = {"user_id": user_id, "chat_sessions": []})
        user_data_table.put_item(Item = {"user_id": user_id, "push": True, "account_id": "",
                                         "stripe_id": stripe_cc.id, "customer_id": customer.id, 
                                         "device_token": "", "platform": ""})
        user_connections_table.put_item(Item = {"user_id": user_id, "connection_id": "",
                                                "is_connected": False, "last_connection": "",
                                                "unread_messages": False})
        return success_return_parser(f"{user_id} has been registered properly",
                                     user_pool_configuration)
    except ClientError as error:
        return error_return_parser(
             error.response["Error"]["Message"], error.response["Error"]["Code"])
