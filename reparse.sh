#!/bin/bash

docker exec legisletters /scripts/update_settings.sh
docker exec legisletters python /legisletters/parser.py
