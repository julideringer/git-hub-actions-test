"""delete bank account"""
import stripe

stripe.api_key = "sk_test_51OhwUsCvpYLTdgxQq9Vuo87nkTzJqDTywVioThhFt2eMdrnZTGHWiwdeCvG4ttTA9nwiCp87gR4P7MyO1hjXAZuo00U7G7Aoxc"
response = stripe.Account.delete_external_account("acct_1QBebVCsIcZqOTdh", "ba_1QBer0CsIcZqOTdhHQXojXz7")
print(response)
