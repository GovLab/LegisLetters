#!/bin/bash -e

docker rm -f legisletters || :

docker run \
  -p 9200:9200 \
  -p 80:80 \
  -e PYTHONPATH=/ \
  -v "${PWD}/dist":/site \
  -v "${PWD}/legisletters":/legisletters \
  -v "${PWD}/scripts":/scripts \
  -v "${PWD}/congress-legislators":/congress-legislators \
  -v "${PWD}/mappings":/mappings \
  -v "${PWD}/config":/usr/share/elasticsearch/config \
  -v "${PWD}/esdata":/usr/share/elasticsearch/data \
  -d --name legisletters thegovlab/legisletters

docker exec -d legisletters nginx
#docker exec -d legisletters /docker-entrypoint.sh elasticsearch
# -e ES_HEAP_SIZE=768m \
