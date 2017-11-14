#!/bin/bash

export prometheus_multiproc_dir="$(mktemp -d)"

exec gunicorn --config kqueen/gunicorn.py kqueen.wsgi
