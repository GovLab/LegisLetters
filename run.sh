#!/bin/bash

docker rm -f legisletters || :

docker run \
  -p 9200:9200 \
  -e PYTHONPATH=/ \
  -v "${PWD}/legisletters:/legisletters" \
  -d --name legisletters -e -v thegovlab/legisletters

docker exec legisletters bash -c 'PYTHONPATH=/ python /legisletters/scraper.py'
