"""lambda function to handle the normal change of password"""
import os
import boto3
from botocore.exceptions import ClientError
from common_tools.payload_parser import success_return_parser, error_return_parser

client = boto3.client("cognito-idp", os.environ["region_name"])

def change_password(**kwargs) -> str:
    """
    This method is in charge of change the user password on the user pool
    """
    kargs = {
        "PreviousPassword": kwargs["kwargs"]["previousPassword"],
        "ProposedPassword": kwargs["kwargs"]["proposedPassword"],
        "AccessToken": kwargs["kwargs"]["accessToken"]
    }
    response = client.change_password(**kargs)
    return response

def lambda_handler(event, context):
    """lambda handler"""
    try:
        kargs = event["body-json"]
        kargs["accessToken"] = event["params"]["header"]["Authorization"].split(" ")[1]
        change_password(kwargs=kargs)
        return success_return_parser("Changed Password successfully", None)
    except ClientError as error:
        return error_return_parser(error.response["Error"]["Message"],
                                   error.response["Error"]["Code"])
