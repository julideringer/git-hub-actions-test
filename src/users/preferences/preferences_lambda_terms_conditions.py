"""Lambda function to handle sign_up process"""
from io import BytesIO
import boto3
import pdfplumber
from botocore.exceptions import ClientError
from common_tools.payload_parser import success_return_parser, error_return_parser

BUCKET_NAME = "mube-s3bucket"
FILE_NAME = "mubeprivacypolicy.pdf"

s3 = boto3.client("s3")

def pdf_to_json(pdf_path):
    """function translate from pdf to json""" 
    data = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if text:
                page_data = {"page_number": page_num, "text": text}
                data.append(page_data)
    return data

def lambda_handler(event, context) -> str:
    """lambda handler"""
    try:
        response = s3.get_object(Bucket=BUCKET_NAME, Key=FILE_NAME)
        pdf_content = response["Body"].read()
        pdf_stream = BytesIO(pdf_content)
        json_data = pdf_to_json(pdf_stream)
        return success_return_parser("File PDF procesed correctly", json_data)
    except ClientError as error:
        return error_return_parser(error.response["Error"]["Message"],
                                   error.response["Error"]["Code"])
