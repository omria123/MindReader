FROM python:3


RUN mkdir -p /usr/src/app/MindReader

WORKDIR MindReader

ENV WAITFORIT=1

COPY ./MindReader/parsers ./parsers
COPY ./MindReader/MessageQueue ./MessageQueue
COPY ./MindReader/IOAccess ./IOAccess
COPY ./MindReader/utils ./utils
COPY ./MindReader/defaults.py ./

ENV PYTHONUNBUFFERED=1
WORKDIR ../

RUN pip install --no-cache-dir pika requests wrapt click matplotlib seaborn Pillow protobuf

CMD ["python" , "-m", "MindReader.parsers" , "run-parser", "rabbitmq://messagequeue:5672"]
