"""lambda function to re send chat messages when user reconnects"""
import os
import json
from base64 import b64encode
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

USER_CONNECTIONS_TABLE = 'user_connections'
MESSAGES_TABLE = 'messages'
CHAT_TABLE = 'chat'
TRIPS_TABLE = 'trips'
USERS_TABLE = 'users'
DOMAIN = '2iu4ktth0g.execute-api.eu-west-1.amazonaws.com'
STAGE = 'demo'

users_table = boto3.resource("dynamodb").Table(USERS_TABLE)
user_connections_table = boto3.resource('dynamodb').Table(USER_CONNECTIONS_TABLE)
messages_table = boto3.resource('dynamodb').Table(MESSAGES_TABLE)
chat_table = boto3.resource('dynamodb').Table(CHAT_TABLE)
trips_table = boto3.resource('dynamodb').Table(TRIPS_TABLE)
trips_reservations_table = boto3.resource('dynamodb').Table('trips_reservations')
queue_object = boto3.client('sqs')
client = boto3.client('cognito-idp', os.environ['region_name'])
s3 = boto3.client('s3')
apigw_management_client = boto3.client("apigatewaymanagementapi",
                                    endpoint_url = f"https://{DOMAIN}/{STAGE}")

def get_user_info_from_objectb64(user_object):
    """method to get user info for a set of trips"""
    user_info_dict = {}
    user_info_dict["name"] = user_object["name"]
    if user_object.get("verified"):
        user_info_dict["verified"] = user_object["verified"]
    if user_object.get("picture"):
        response = s3.get_object(
            Bucket="mube-s3bucket", Key=user_object["picture"])["Body"].read()
        user_info_dict["picture"] = b64encode(response).decode("utf-8")
    return user_info_dict

def lambda_handler(event, context):
    """lambda handler"""
    for record in event['Records']:
        message = json.loads(record['body'])
        if message['action'] == 'reservationRequest' or message['action'] == 'reservationConfirmation':
            chat_object = chat_table.get_item(Key={'chat_id': message['chat_id']})['Item']
            message['trip'] = trips_table.get_item(Key={'trip_id': chat_object['trip_id']})['Item']
            user_object = users_table.get_item(Key={'user_id': message['sender_id']})["Item"]
            message['user_info'] = get_user_info_from_objectb64(user_object)
            if message['action'] == 'reservationRequest':
                trips_reservations = trips_reservations_table.query(
                    IndexName='user_id-trip_id-index',
                    KeyConditionExpression=Key('user_id').eq(message['sender_id'])\
                        &Key('trip_id').eq(message['trip']['trip_id']))['Items'][0]
                message['reservation_id'] = trips_reservations['reservation_id']
        receiver_id = record['messageAttributes']['receiver_id']['stringValue']
        receiver_connection = user_connections_table.get_item(Key={
            'user_id': receiver_id})['Item']['connection_id']
        try:
            apigw_management_client.post_to_connection(Data=json.dumps(message).encode('utf-8'),
                                                ConnectionId=receiver_connection)
            messages_table.update_item(
                Key={'message_id': message['message_id']},
                UpdateExpression='SET message_status = :val1',
                ExpressionAttributeValues={':val1': 'received'}
            )
        except ClientError as error:
            print({"success": False, "error_message": error.response['Error']['Message'],
                "error_code": error.response['Error']['Code'], "data": None})
            return False
    return True
