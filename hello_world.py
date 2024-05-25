def lambda_handler(event, context):
    print("hola")
    return {
        'statusCode': 200,
        'body': 'Hello, World!'
    }