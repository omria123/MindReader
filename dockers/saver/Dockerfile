FROM python:3

RUN mkdir -p /usr/src/app/MindReader

WORKDIR MindReader

ENV WAITFORIT=1
COPY ./MindReader/MessageQueue ./MessageQueue
COPY ./MindReader/Database ./Database
COPY ./MindReader/IOAccess ./IOAccess
COPY ./MindReader/utils ./utils
COPY ./MindReader/defaults.py ./
COPY ./MindReader/saver.py ./


ENV PYTHONUNBUFFERED=1
WORKDIR ../
COPY ./requirements.txt ./
RUN pip install --no-cache-dir pika pymongo requests wrapt click protobuf


CMD ["python" , "-m", "MindReader.saver" , "run-saver", "rabbitmq://messagequeue:5672", "mongo://database:27017"]
