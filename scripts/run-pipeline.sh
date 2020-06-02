#!/bin/bash

docker build -t api -f dockers/api/Dockerfile .
docker build -t server -f dockers/server/Dockerfile .
docker build -t saver -f dockers/saver/Dockerfile .
docker build -t parsers -f dockers/parsers/Dockerfile .
docker-compose up

