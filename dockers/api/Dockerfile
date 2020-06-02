FROM python:3


RUN mkdir -p /usr/src/app/MindReader

WORKDIR MindReader

ENV WAITFORIT=1

COPY ./MindReader/Database ./Database
COPY ./MindReader/IOAccess ./IOAccess
COPY ./MindReader/utils ./utils
COPY ./MindReader/defaults.py ./
COPY ./MindReader/api.py ./
COPY ./MindReader/static ./static
COPY ./MindReader/templates ./templates

ENV PYTHONUNBUFFERED=1
WORKDIR ../
COPY ./requirements.txt ./
RUN pip install --no-cache-dir click requests flask flask-cors wrapt timeago pymongo protobuf

CMD ["python", "-m", "MindReader.api", "run-api-server", "mongo://database:27017", "--host", "0.0.0.0"]


