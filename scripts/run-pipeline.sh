#!/bin/bash

docker-compose up

docker rm api server saver parser messagequeue database


echo "make sure to clean after you in docker/dockers_data (sudo required)"
