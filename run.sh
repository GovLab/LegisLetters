#!/bin/bash -e

docker rm -f legisletters || :

docker run \
  -p 9200:9200 \
  -p 8000:80 \
  -e PYTHONPATH=/ \
  -v "${PWD}/dist:/site" \
  -v "${PWD}/legisletters:/legisletters" \
  -v "${PWD}/config":/usr/share/elasticsearch/config \
  -v "${PWD}/esdata":/usr/share/elasticsearch/data \
  -d --name legisletters thegovlab/legisletters

docker exec -d legisletters nginx
docker exec -d legisletters /docker-entrypoint.sh elasticsearch
#docker exec legisletters bash -c 'PYTHONPATH=/ python /legisletters/scraper.py'
