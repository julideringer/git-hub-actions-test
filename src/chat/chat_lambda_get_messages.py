"""lambda function to retrieve historical messages"""
import boto3
from boto3.dynamodb.conditions import Key
from common_tools.payload_parser import error_return_parser, success_return_parser

MESSAGES_TABLE = "messages"

messages_table = boto3.resource("dynamodb").Table(MESSAGES_TABLE)

def lambda_handler(event, context):
    """lambda handler"""
    chat_id = event["params"]["path"]["id"]
    chat_response = messages_table.query(
        IndexName = "chat_id-timestamp-index",
        KeyConditionExpression=Key("chat_id").eq(chat_id)
    )["Items"]
    if len(chat_response) == 0:
        return success_return_parser("empty chat", [])
    return success_return_parser(None, chat_response)
