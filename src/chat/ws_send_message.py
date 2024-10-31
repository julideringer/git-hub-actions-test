"""lambda function to handle $on_connect RK for chat messaging application"""
import json
import uuid
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

USER_CONNECTIONS_TABLE = "user_connections"
MESSAGES_TABLE = "messages"
DOMAIN = "2iu4ktth0g.execute-api.eu-west-1.amazonaws.com"
STAGE = "demo"

user_connections_table = boto3.resource("dynamodb").Table(USER_CONNECTIONS_TABLE)
messages_table = boto3.resource("dynamodb").Table(MESSAGES_TABLE)
apigw_management_client = boto3.client("apigatewaymanagementapi",
                                    endpoint_url = f"https://{DOMAIN}/{STAGE}")

def lambda_handler(event, context = None):
    """lambda handler for chat messaging"""
    body = event.get("body")
    body = json.loads(body if body is not None else "{"message": ""}")
    receiver_id = body.get("receiver")
    body["message_id"] = str(uuid.uuid4())
    body["db_timestamp"] = str(datetime.now().isoformat(timespec="seconds"))
    body["message_status"] = "received"
    receiver_connection = user_connections_table.get_item(Key={
        "user_id": receiver_id})["Item"]["connection_id"]
    try:
        messages_table.put_item(Item={
            "sender_id": body.get("sender"),
            "receiver_id": receiver_id,
            "timestamp": body.get("timestamp"),
            "message": body.get("message"),
            "type": body.get("type"),
            "db_timestamp": str(datetime.now().isoformat(timespec="seconds")),
            "message_id": body.get("message_id"),
            "message_status": body.get("message_status"),
            "chat_id": body.get("chat_id"),
            "action": body.get("action")
        })
        apigw_management_client.post_to_connection(Data=json.dumps(body).encode("utf-8"),
                                                   ConnectionId=receiver_connection)
        response = {"statusCode": 200, "body":"received"}
    except ClientError:
        messages_table.update_item(
            Key={"message_id": body.get("message_id")},
            UpdateExpression="SET message_status = :val1",
            ExpressionAttributeValues={":val1": "unreceived"}
        )
        user_connections_table.update_item(
            Key={"user_id": receiver_id},
            UpdateExpression="SET unread_messages = :val1",
            ExpressionAttributeValues={":val1": True}
        )
        response = {"statusCode": 200, "body": "delivered"}
    return response
