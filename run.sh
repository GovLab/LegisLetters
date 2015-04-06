#!/bin/bash

docker rm -f legisletters || :

docker run \
  -p 9200:9200 \
  -v "${PWD}/scripts:/scripts" \
  -d --name legisletters -e -v thegovlab/legisletters
