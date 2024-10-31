"""lambda function to manage disconnect ws client"""
import boto3
from botocore.exceptions import ClientError

CONNECTIONS_TABLE = 'connections'
USER_CONNECTIONS_TABLE = 'user_connections'

connections_table = boto3.resource("dynamodb").Table(CONNECTIONS_TABLE)
user_connections_table = boto3.resource("dynamodb").Table(USER_CONNECTIONS_TABLE)

def lambda_handler(event, context):
    """lambda_handler"""
    connection_id = event['requestContext']['connectionId']
    try:
        user_id = connections_table.get_item(Key={
            'connection_id': connection_id})['Item']['user_id']
        update_expression = 'SET is_connected = :value1, connection_id = :value2'
        expression_attribute_values = {':value1': False, ':value2': ''}
        user_connections_table.update_item(
            Key={'user_id': user_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values
        )
        connections_table.delete_item(Key={"connection_id": connection_id})
        body = {"statusCode": 200}
    except ClientError:
        body = {"statusCode": 503}
    return body
