#!/bin/bash

source .env/bin/activate
export PYTHONPATH=$PWD
./update_settings.sh
python legisletters/parser.py
