"""lambda function to handle ws clients connections"""
import json
import boto3
from boto3.dynamodb.conditions import Key
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError

CONNECTIONS_TABLE = 'connections'
USER_CONNECTIONS_TABLE = 'user_connections'
MESSAGES_TABLE = 'messages'

connections_table = boto3.resource("dynamodb").Table(CONNECTIONS_TABLE)
user_connections_table = boto3.resource("dynamodb").Table(USER_CONNECTIONS_TABLE)
messages_table = boto3.resource("dynamodb").Table(MESSAGES_TABLE)
queue_object = boto3.client('sqs')

MESSAGES_Q = 'https://sqs.eu-west-1.amazonaws.com/416737519422/receive_message_q'

def get_unreceived_messages(user_id):
    """function to retrieve unread messages"""
    messages = messages_table.query(
        IndexName='receiver_id-timestamp-index',
        KeyConditionExpression=Key('receiver_id').eq(user_id),
        FilterExpression=Attr('message_status').eq('unreceived'),
        ScanIndexForward=False,)["Items"]
    for element in messages:
        queue_object.send_message(
            QueueUrl = MESSAGES_Q, MessageBody = json.dumps(element),
            MessageAttributes = {'receiver_id': {'DataType': 'String','StringValue': user_id}})

def lambda_handler(event, context):
    """connections lambda handler"""
    connection_id = event['requestContext']['connectionId']
    connected_at = event['requestContext']['connectedAt']
    user_id = event['queryStringParameters']['userId']
    update_expression = 'SET is_connected = :value1,\
        connection_id = :value2, last_connection = :value3'
    expression_attribute_values = {
        ':value1': True, ':value2': connection_id, ':value3': connected_at}
    try:
        user_connections_table.update_item(
            Key={'user_id': user_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values
        )
        connections_table.put_item(Item = {
            'connection_id': connection_id,
            'user_id': user_id
        })
        response = user_connections_table.get_item(Key={'user_id': user_id})['Item']
        if response['unread_messages'] is True:
            get_unreceived_messages(user_id)
        body = {"statusCode": 200}
    except ClientError:
        body = {"statusCode": 503}
    return body
