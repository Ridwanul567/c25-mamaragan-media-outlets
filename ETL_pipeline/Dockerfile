FROM public.ecr.aws/lambda/python:latest

WORKDIR ${LAMBDA_TASK_ROOT}

COPY requirements.txt .

RUN pip3 install -r requirements.txt

COPY collect_data.py .
COPY enrich_data.py .
COPY write_data.py .
COPY pipeline.py .
COPY .env .

CMD [ "pipeline.handler" ]