#!/bin/bash -e

curl -XPOST 'http://localhost:9200/legisletters/_close?pretty=true'
curl -XPUT 'http://localhost:9200/legisletters/_settings?pretty=true' -d @legisletters/settings.json
curl -XPOST 'http://localhost:9200/legisletters/_open?pretty=true'
