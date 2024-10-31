"""delete costumer"""
import stripe

stripe.api_key = "sk_test_51OhwUsCvpYLTdgxQq9Vuo87nkTzJqDTywVioThhFt2eM\
  drnZTGHWiwdeCvG4ttTA9nwiCp87gR4P7MyO1hjXAZuo00U7G7Aoxc"

stripe.Customer.delete("cus_QWnvhSu2EK8vIW")
