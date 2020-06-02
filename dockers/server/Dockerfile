FROM python:3

RUN mkdir -p /usr/src/app/MindReader

WORKDIR /usr/src/app/MindReader

ENV WAITFORIT=1

COPY ./MindReader/defaults.py ./
COPY ./MindReader/utils ./utils
COPY ./MindReader/IOAccess ./IOAccess
COPY ./MindReader/parsers ./parsers
COPY ./MindReader/server.py ./
COPY ./MindReader/protocol ./protocol

COPY ./MindReader/MessageQueue ./MessageQueue

ENV PYTHONUNBUFFERED=1
WORKDIR /usr/src/app
RUN pip install requests flask click matplotlib seaborn wrapt Pillow pika protobuf


CMD ["python", "-m", "MindReader.server", "run-server", "rabbitmq://messagequeue:5672", "--data-dir", "/usr/src/app/data", "--host", "0.0.0.0"]
