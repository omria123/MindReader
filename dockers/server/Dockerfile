FROM python:3

RUN mkdir -p /usr/src/app/MindReader

WORKDIR /usr/src/app/MindReader

RUN ls

COPY ./MindReader/defaults.py ./
COPY ./MindReader/utils ./utils
COPY ./MindReader/IOAccess ./IOAccess
COPY ./MindReader/parsers ./parsers
COPY ./MindReader/server.py ./
COPY ./MindReader/protocol ./protocol

COPY ./MindReader/MessageQueue ./MessageQueue

ENV PYTHONUNBUFFERED=1
WORKDIR /usr/src/app
COPY ./requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt



CMD ["python", "-m", "MindReader.server", "run-server", "rabbitmq://message-queue:5672", "--data-dir", "/usr/src/app/data"]