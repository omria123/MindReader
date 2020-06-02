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
COPY ./requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python" , "-m", "MindReader.parsers" , "run-parser", "rabbitmq://messagequeue:5672"]