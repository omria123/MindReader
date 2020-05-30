FROM python:3
WORKDIR /usr/src/app

ENV PYTHONUNBUFFERED=1

COPY ../requirements.txt ./
COPY ../MindReader/defaults.py ./
COPY ../MindReader/utils ./utils

COPY ../MindReader/server.py ./


