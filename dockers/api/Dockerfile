FROM python:3


RUN mkdir -p /usr/src/app/MindReader

WORKDIR MindReader


COPY ./MindReader/Database ./Database
COPY ./MindReader/IOAccess ./IOAccess
COPY ./MindReader/utils ./utils
COPY ./MindReader/defaults.py ./
COPY ./MindReader/api.py ./

ENV PYTHONUNBUFFERED=1
WORKDIR ../
COPY ./requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "-m", "MindReader.api", "run-server-api", "mongo://database:27017"]


