"""create stripe customer script"""
import stripe


stripe.api_key = "sk_test_51OhwUsCvpYLTdgxQq9Vuo87nkTzJqDTywVioThhFt2eM\
  drnZTGHWiwdeCvG4ttTA9nwiCp87gR4P7MyO1hjXAZuo00U7G7Aoxc"

customer = stripe.Customer.create(
    email="antonio@valdecasas.net",
    name="antonio garcia valdecasas"
)

print(customer)
