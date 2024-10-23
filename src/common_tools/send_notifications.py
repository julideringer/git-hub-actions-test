"""lambda function to retrieve and send notifications"""
import boto3

ANDRIOD_ARN = 'arn:aws:sns:eu-west-1:416737519422:app/GCM/MUBE'
IOS_ARN = ''

sns_client = boto3.client('sns')

def lambda_handler(event, context):
    """lambda handler"""
    for record in event['Records']:
        message_attributes = record.get('messageAttributes')
        platform_arn = IOS_ARN
        if message_attributes["platform"] == 'android':
            platform_arn = ANDRIOD_ARN
        response = sns_client.create_platform_endpoint(
            PlatformApplicationArn=platform_arn,
            Token=message_attributes["device_token"])
        endpoint_arn = response['EndpointArn']
        response = sns_client.publish(
            TargetArn=endpoint_arn,
            Message=record["body"],
            MessageStructure='json'
        )
