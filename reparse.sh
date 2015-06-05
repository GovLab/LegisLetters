#!/bin/bash

source .env/bin/activate
export PYTHONPATH=$PWD
python legisletters/parser.py
