"""lambda function to respond auth challenge"""
import os
import hmac
import base64
import hashlib
import boto3

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
    msg = bytes(username + os.environ['client_id'], 'utf-8')
    secret_hash = base64.b64encode(
        hmac.new(key, msg, digestmod=hashlib.sha256).digest()).decode()
    return secret_hash

def respond_auth_challenge(**kwargs):
    """method that respond auth challenge"""
    kargs = {
        'UserPoolId': os.environ['userpool_id'],
        'ClientId': os.environ['client_id'],
        'ChallengeName': 'PASSWORD_VERIFIER',
        'ChallengeResponse': {
            'PASSWORD_CLAIM_SIGNATURE': '',
            'PASSWORD_CLAIM_SECRET_BLOCK': 'Oahkrpb/NwJKIdj9N7qCnMTHvzRUA0CK0yV/gTET/MtL9c0Ty8o7mzTg/42f0sewE+Gi7vN7fKn0w09PPcl0nSYmtNHlXNwaFKdFe0HxNxSAPQy+KigYUlpQQiwiLKaMFaqIXc8ACiprnbFPE4m8rFsoFUSLsj7JYU5X2LytqW0IYazlggaTuPs7HJdYo457RJGnSfZ9TcwyoANvsY+WTKOKOaekuXEEIkVHCvW+ycwTrP/V+bVf/FfkgU6RX4OIdsG5PehqV+TW2JeXs11bzuY+GaxxVHxFD0o9uPwt89AMuW1OLEQJRCCYZI9R30YWal/v2iQxGtETiaRi9TVF7OZykKotJWH/mIUHEZy+7H7vIg/V4wO00XhIW2LT6wCeTlHPiYRCnJhwVMjNm0WywIf+MRXSWmaWBhg0+KqGxFEPmJrPaw0i+yK89AK7Tbfrro64P0thkV8sgiHN2m8Cz6cQKZWh7RCFCy5FjWA7yBncPd7d5qU+/GE9okqbutLCSxSGxuYW01IuZ9dMSvJ0y/RDEcQIAz4k25WY3G9TQ/hs3Q7MNwuGyiI0eZlz5f6v15JPAdD1/Jc3V0dn+pAhHR07WvRQjzITiZhgN3fHFIZ/EPoaK671E1cIdAR3qiocMfx/pXi9HsbiIh1wVQ+oBNKZ1nr05OMd2OFYQgu68E16w9o+qV9o0drPRajC+SaOrtA86KburclfUVmSw8uAgT+91uD1voZ/nXIztWTGYGcNK+79X3ZOioed+0rg0tUq26iC7NtJZq/aJDZtgEKkyC+SQqRWQMlXZEpTcosn6RpdIdh9oEQ5qZYsvlLQ/vRSAM6N15nF3RfozNPct3ce3YbbF77HDoDWdXE7XB698BdDcYjD2fcH6ibTF4NN2s5+/kjnuIuEqhu6L3Ft9OAWL++cT0tZ6rJSU6wEr2OnYwXIMIheeR7IESxpom0vs+jutj072KiPw5fN+B8zxBz0vWXrrb0Q5I1pMQBxharY5T6GSkUAbrPCzf8k9tc6oZ5696rXu8uvEQS/rG2nhkD0XU4TZgqacaYzDooaMpXR7J3o9Y81CaFcDtXdGuLncEmBa1xL3s8YbOkk+f9oPbaWVFyAucpF84ImMXU604bazVsls7glOExEo5rhbG/BMjD5SNjmiZLkuXLTilK8oCvjhQ1tpMIzH4hQSIfmnhAA3ZnmHYNmxdVlQ86av1VK6m8h12oImoCb1dew1xBVOHTOly+VuucXC9wfHNzw/+4mUIS9EAyuFZWYErmrIPoHJX16bbFhqwiYJbo3QEFinbrWVdOfG+90BMGbDiJbBF+lGlt7w0nAFf1DeqWijepFBp//7QgMfHiiclCu5pnHdpURBUSy3w2WEoSmGuVvnQk0ZwDqi0Tjktkn5HC/A+y318FYpz3yBLipCogr0F1AXNsAi3nQENXCwkga6W24torbLJK+e2hqNUT4/cWiN3VKZE99T7oB+g==',
            'TIMESTAMP': '',
            'USERNAME': 'maldonadosalinasdaniel@gmail.com'
        }
    }
    if os.environ['client_secret']:
        kargs["AuthParameters"]["SECRET_HASH"] = _secret_hash(kwargs["kwargs"]["Username"])
    response = client.admin_respond_auth_challenge(**kargs)
