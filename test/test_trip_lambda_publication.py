import unittest
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from trips.trip_lambda_publication import lambda_handler

class TestLambdaHandler(unittest.TestCase):


    def test_lambda_handler_success(self):
      response = lambda_handler()

if __name__ == "__main__":
    unittest.main()
