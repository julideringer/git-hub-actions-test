FROM public.ecr.aws/lambda/python:3.10

ENV region_name "eu-west-1"
ENV userpool_id "eu-west-1_r1Tb8Zi5m"

COPY requirements.txt ${LAMBDA_TASK_ROOT}
COPY lambda_function.py ${LAMBDA_TASK_ROOT}

RUN pip install -r requirements.txt

CMD ["lambda_function.lambda_handler"]
