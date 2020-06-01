FROM python:3

RUN mkdir -p /usr/src/app/MindReader

WORKDIR MindReader


COPY ./MindReader/MessageQueue ./
COPY ./MindReader/Database ./
COPY ./MindReader/IOAccess ./
COPY ./MindReader/utils ./
COPY ./MindReader/defaults.py ./


ENV PYTHONUNBUFFERED=1
WORKDIR ../
COPY ./requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt


CMD ["python" , "-m", "MindReader.parsers" , "run-parser", "rabbitmq://message-queue:5672", "mongo://database:27017"]