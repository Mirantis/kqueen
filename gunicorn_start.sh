#!/bin/bash

export PYTHONPATH=`pwd`
gunicorn --bind 0.0.0.0:5000 --workers 4 kqueen.server
