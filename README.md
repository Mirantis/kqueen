# KQueen - Kubernetes cluster manager

[![Build Status](https://travis-ci.org/Mirantis/kqueen.svg?branch=master)](https://travis-ci.org/Mirantis/kqueen)
[![PyPI version](https://badge.fury.io/py/kqueen.svg)](https://badge.fury.io/py/kqueen)
[![Coverage Status](https://coveralls.io/repos/github/Mirantis/kqueen/badge.svg?branch=master)](https://coveralls.io/github/Mirantis/kqueen?branch=master)

## Development

* Bootstrap environment

```
mkvirtualenv -p /usr/bin/python3 kqueen
pip3 install -r requirements.txt
pip3 install --editable .
docker-compose up -d
kqueen
```

* Clean etcd storage and prepare examples

```
etcdctl rm --recursive /kqueen
./devenv.py
```


* Bootstrap for tests

```
docker-compose -f docker-compose.yml -f docker-compose.test.yml up
```

* Bootstrap for demo with unofficial images.

```
docker-compose -f docker-compose.yml -f docker-compose.demo.yml up
```


## Configuration

We load configuration from file `config/dev.py` by default and this can be configured by `KQUEEN_CONFIG_FILE` environment variable. Any environment variable matching name `KQUEEN_*` will be loaded and saved to configuration.

| Configuration option | Type | Default value | Description |
| --- | --- | --- | --- |
| `KQUEEN_CONFIG_FILE` | Environment variable | `config/dev.py` | Configuration file to load |

## Documentation

For full documenation please refer to [kqueen.readthedocs.io](http://kqueen.readthedocs.io).
