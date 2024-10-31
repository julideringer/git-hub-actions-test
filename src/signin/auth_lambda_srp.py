"""Lambda function to handle sign_in process"""
import os
import hmac
import base64
import hashlib
import boto3
import srp
#from botocore.exceptions import ClientError

if not 'region_name' in os.environ:
    os.environ['region_name'] = 'eu-west-1'
if not 'userpool_id' in os.environ:
    os.environ['userpool_id'] = 'eu-west-1_r1Tb8Zi5m'
if not 'client_id' in os.environ:
    os.environ['client_id'] = 'i9mf5ov9e7k31ttm44fedokdv'
if not 'client_secret' in os.environ:
    os.environ['client_secret'] = 'ql513tc5o1jtipohla48k1pa632bflqqlptq2caq29h3cd061s9'

client = boto3.client('cognito-idp', os.environ['region_name'])

def _secret_hash(username):
    key = os.environ['client_secret'].encode()
    message = bytes(username + os.environ['client_id'], 'utf-8')
    secret_hash = base64.b64encode(
        hmac.new(key, msg, digestmod=hashlib.sha256).digest()).decode()
    return secret_hash

def start_sign_in(**kwargs):
    """
    This method signs in a given user name and retrieve the tokens
    """
    usr = srp.User(kwargs["kwargs"]["Username"], kwargs["kwargs"]["Password"])
    uname, A = usr.start_authentication()
    A = str(A)
    kargs = {
        'UserPoolId': os.environ['userpool_id'],
        'ClientId': os.environ['client_id'],
        'AuthFlow': kwargs["kwargs"]["AuthFlow"],
        'AuthParameters': {'USERNAME': kwargs["kwargs"]["Username"],
                           'SRP_A': str(usr.A)}
    }
    if os.environ['client_secret']:
        kargs['AuthParameters']['SECRET_HASH'] = _secret_hash(kwargs["kwargs"]["Username"])
    response = client.admin_initiate_auth(**kargs)
    return response

def lambda_handler(event, context) -> str:
    """
    An AWS lambda handler that receives events from an API GW and starts the sign in process 
    for new users on the application. Takes the required attributes and interact with cognito 
    IDP to retrieve the access and refresh token.
    
    :param username [str]: the username of the user that is starting the sign_in process
    :param password [str]: the password given from the user to start the sign_in process
    """
    #try:
    event["body-json"]["AuthFlow"] = 'USER_SRP_AUTH'
    token = start_sign_in(kwargs=event["body-json"])
    body = {"success": True,
            "data": {
                "message": "Login successfully",
                "info": {
                    "accessToken": token["AuthenticationResult"]["AccessToken"],
                    "refreshToken": token["AuthenticationResult"]["RefreshToken"],
                    "idToken": token["AuthenticationResult"]["IdToken"]
                }
            }
    }
    #except ClientError:
    #    body = {
    #        "success": False,
    #        "data": None,
    #        "message": "Unable to login user"
    #    }
    return body

msg = {
    "body-json": {
        "Username": "maldonadosalinasdaniel@gmail.com",
        "Password": "12345Test@."
    },
    "params": {
        "path": {},
        "querystring": {},
        "header": {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Authorization": "Bearer eyJraWQiOiJXeHZGbW5USGowTUszWUhpdGs0OUo0ZVYwRVpYd1pTUGZFN2hUT1l4ZDU0PSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiJkMTgxMTlmMS1kOTU2LTRmZGMtOTRjYS1kYzc4ZDhmMGM5NWMiLCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAuZXUtd2VzdC0xLmFtYXpvbmF3cy5jb21cL2V1LXdlc3QtMV9yMVRiOFppNW0iLCJjbGllbnRfaWQiOiJpOW1mNW92OWU3azMxdHRtNDRmZWRva2R2Iiwib3JpZ2luX2p0aSI6IjBhZGRmMDQ1LTQ2ZGYtNGQ5NS04YjcwLWE3YjFiMDVjMGU2MSIsImV2ZW50X2lkIjoiYzhiYTY3YTAtYjg4Yi00YzJkLTg0M2ItOWJiMmM1ZWZiZGI5IiwidG9rZW5fdXNlIjoiYWNjZXNzIiwic2NvcGUiOiJhd3MuY29nbml0by5zaWduaW4udXNlci5hZG1pbiIsImF1dGhfdGltZSI6MTcwNTgzMTg2NiwiZXhwIjoxNzA1ODM1NDY2LCJpYXQiOjE3MDU4MzE4NjYsImp0aSI6IjQ0ZDIzNjhhLWJhYTAtNDJjOS1hNmYwLWZiZDA2N2RjMDY5MSIsInVzZXJuYW1lIjoiZDE4MTE5ZjEtZDk1Ni00ZmRjLTk0Y2EtZGM3OGQ4ZjBjOTVjIn0.mvc8sP9Xy2X4v3_NxGlPIykbNuf6dgT02FOsezXfQNY1wy0etBWdM3eshD4295kyrq6rmKEvPa63TKe1kWgjEd9D57H3BSdjp3L2ztxZrdTej5IWcRFMCJE42-EdwNHNlO0QQdFw6DQZbv-qHGo8RF5mZ_Zv7zKsAk9a1EkrVzXkJwXMmYPHT1ghPJqk8wfl4N3bxYkapux9YWvsUAadJ5fa1RFpK-fu_PPbQ2gOUZ6nxJd7_rBB6oMvsWcbPr5g-ck1EMLbONdZVLj7rjTdDXgf8OfCyg_agNQAEXAotBqfATmZb87GwjbaXfm_WU0duHPrSRir-VAw_d0j6VKX5Q",
            "Cache-Control": "no-cache",
            "Content-Type": "application/json",
            "Host": "api.bemube.com",
            "Postman-Token": "24b5b17c-9c64-498b-9ebf-431f098e5352",
            "User-Agent": "PostmanRuntime/7.36.1",
            "X-Amzn-Trace-Id": "Root=1-65abeb8d-1c991529685224a36159291a",
            "X-Forwarded-For": "79.145.12.70",
            "X-Forwarded-Port": "443",
            "X-Forwarded-Proto": "https"
        }
    },
    "stage-variables": {},
    "context": {
        "account-id": "",
        "api-id": "pggu9lt9qc",
        "api-key": "",
        "authorizer-principal-id": "",
        "caller": "",
        "cognito-authentication-provider": "",
        "cognito-authentication-type": "",
        "cognito-identity-id": "",
        "cognito-identity-pool-id": "",
        "http-method": "PATCH",
        "stage": "dev",
        "source-ip": "79.145.12.70",
        "user": "",
        "user-agent": "PostmanRuntime/7.36.1",
        "user-arn": "",
        "request-id": "2c4de8f5-8ed6-42d6-9e94-b7cce830121c",
        "resource-id": "b4q89t",
        "resource-path": "/users/profile"
    }
}

print(lambda_handler(msg, None))
