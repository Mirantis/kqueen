# KQueen - Kubernetes cluster manager

[![Build Status](https://travis-ci.org/Mirantis/kqueen.svg?branch=master)](https://travis-ci.org/Mirantis/kqueen)
[![PyPI version](https://badge.fury.io/py/kqueen.svg)](https://badge.fury.io/py/kqueen)
[![Coverage Status](https://coveralls.io/repos/github/Mirantis/kqueen/badge.svg?branch=master)](https://coveralls.io/github/Mirantis/kqueen?branch=master)

## Development

* Bootstrap kqueen environment

```
mkvirtualenv -p /usr/bin/python3 kqueen
pip3 install -r requirements.txt
pip3 install --editable .
# start etcd in container
docker-compose up -d # start
kqueen
```

* Clean etcd storage and prepare examples

```
etcdctl rm --recursive /kqueen
./devenv.py
```


## Demo environment

* Without local Kubernetes

```
docker-compose -f docker-compose.yml -f docker-compose.demo.yml up
```

* Including local Kubernetes (without `kubelet`)

```
docker-compose -f docker-compose.yml -f docker-compose.demo.yml -f docker-compose.kubernetes.yml up
```

* You can add some example data by running

```
docker-compose -f docker-compose.yml -f docker-compose.demo.yml exec kqueen ./devenv.py
```

It will add user `admin` with password `default` and few of testing objects.

## Configuration

We load configuration from file `config/dev.py` by default and this can be configured by `KQUEEN_CONFIG_FILE` environment variable. Any environment variable matching name `KQUEEN_*` will be loaded and saved to configuration.

| Configuration option | Type | Default value | Description |
| --- | --- | --- | --- |
| `KQUEEN_CONFIG_FILE` | Environment variable | `config/dev.py` | Configuration file to load |

## Documentation

For full documenation please refer to [kqueen.readthedocs.io](http://kqueen.readthedocs.io).
