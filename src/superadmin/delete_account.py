"""function to delete stripe account"""
import stripe

stripe.api_key = "sk_test_51OhwUsCvpYLTdgxQq9Vuo87nkTzJqDTywVioThhFt2eMdrnZTGHWiwdeCvG4ttTA9nwiCp87gR4P7MyO1hjXAZuo00U7G7Aoxc"
response = stripe.Account.delete("acct_1Pw5QNCWpE8abo8N")

print(response)
