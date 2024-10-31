"""lambda function to get payment and transfers balance"""
import os
import stripe

stripe.api_key = os.environ["stripe_api_key"]

def lambda_handler(event, context):
    """lambda handler"""
    balance = stripe.Balance.retrieve()
    return balance
