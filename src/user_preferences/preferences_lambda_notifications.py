"""Lambda function to handle confirm user mail"""
import boto3
from botocore.exceptions import ClientError
from src.common_tools.payload_parser import success_return_parser, error_return_parser

USER_DATA_TABLE = "user_data"

user_data_table = boto3.resource("dynamodb").Table(USER_DATA_TABLE)

def lambda_handler(event, context) -> str:
    """lambda handler"""
    user_id = event["body-json"]["username"]
    try:
        user_data_table.update_item(
            Key={"user_id": user_id},
            UpdateExpression="set #nm = :n",
            ExpressionAttributeNames={"#nm": "push"},
            ExpressionAttributeValues={":n": event["body-json"]["push"]})
        #TODO: AÑADIR EMAIL NOTIFICATIONS
        if event["body-json"]["push"] is True:
            return success_return_parser(f"{user_id} has activated push notifications", None)
        return success_return_parser(f"{user_id} has disabled push notifications", None)
    except ClientError as error:
        return error_return_parser(error.response["Error"]["Message"],
                                   error.response["Error"]["Code"])
