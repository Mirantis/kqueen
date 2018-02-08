KQueen - Kubernetes cluster manager
===================================


.. image:: https://travis-ci.org/Mirantis/kqueen.svg?branch=master
    :target: https://travis-ci.org/Mirantis/kqueen

.. image:: https://badge.fury.io/py/kqueen.svg
    :target: https://badge.fury.io/py/kqueen

.. image:: https://coveralls.io/repos/github/Mirantis/kqueen/badge.svg?branch=master
    :target: https://coveralls.io/github/Mirantis/kqueen?branch=master

.. image:: https://readthedocs.org/projects/kqueen/badge/?version=master
    :target: http://kqueen.readthedocs.io/en/master/?badge=master

Overview
--------

More information about KQueen Architecture and use cases is described in `RATIONALE <RATIONALE.md>`_ file.

Requirements
-----------

-  Python v3.6 and higher.
-  Pip v3 and higher.
-  Docker stable release (v17.03 and higher is preferable).
-  Docker-compose stable release (v1.16.0 and higher is preferable).

::

    mkvirtualenv -p /usr/bin/python3 kqueen

Development
-----------

-  Bootstrap kqueen environment

::

    virtualenv -p /usr/bin/python3 kqueen
    source ./kqueen/bin/activate
    pip3 install -e ".[dev]"
    pip3 install --editable .
    # start etcd in container
    docker-compose up -d # start
    kqueen

-  Clean etcd storage and prepare examples

`devenv.py` will create few objects to provides basic developer environment. It will also try to download `kubeconfig` file for real cluster but it requires access to Mirantis VPN. However, it can be workarounded by creating file `kubeconfig_remote` in repository root and this file will be used instead of downloading it.

::

    # exec in kqueen-api container
    etcdctl rm --recursive /kqueen
    ./devenv.py

- Run flask shell

::

    # exec in kqueen-api container
    export FLASK_APP=kqueen.server
    export prometheus_multiproc_dir=$(mktemp -d)
    flask shell

- Test access token with `curl`

::

    TOKEN=$(curl -s -H "Content-Type: application/json" --data '{"username":"admin","password":"default"}' -X POST localhost:5000/api/v1/auth | jq -r '.access_token'); echo $TOKEN; curl -H "Authorization: Bearer $TOKEN" localhost:5000/api/v1/clusters

- Image updating

There are two ways to test development changes. Its possible to create a separate branch and push PR, then TravisCI build image and push it on Docker Hub automatically. Or just rebuild kqueen api-image locally:

::

   docker build -t kqueen/api:your_tag kqueen/

Demo environment
----------------

- Make sure you can reach Jenkins server defined in `JENKINS_API_URL` variable in file `kqueen/config/prod.py`.
- Run these commands to run Kqueen API and UI in containers.

::

    docker-compose -f docker-compose.yml -f docker-compose.demo.yml up

- You can login using user `admin` and password `default`. Default username and password can be changed in `docker-compose.demo.yml` file before first start of API.


Configuration
-------------

We load configuration from file ``config/dev.py`` by default and this
can be configured by ``KQUEEN_CONFIG_FILE`` environment variable. Any
environment variable matching name ``KQUEEN_*`` will be loaded and saved
to configuration.

Documentation
-------------

For full documenation please refer to
`kqueen.readthedocs.io <http://kqueen.readthedocs.io>`__.

.. |Build Status| image:: https://travis-ci.org/Mirantis/kqueen.svg?branch=master
   :target: https://travis-ci.org/Mirantis/kqueen
.. |PyPI version| image:: https://badge.fury.io/py/kqueen.svg
   :target: https://badge.fury.io/py/kqueen
.. |Coverage Status| image:: https://coveralls.io/repos/github/Mirantis/kqueen/badge.svg?branch=master
   :target: https://coveralls.io/github/Mirantis/kqueen?branch=master

DEMOs
-----

**Generic KQueen Overview**

.. image:: https://img.youtube.com/vi/PCAwCxPQc2A/0.jpg
   :target: https://www.youtube.com/watch?v=PCAwCxPQc2A&t=1s

**AKS (Azure) in KQueen**

.. image:: https://img.youtube.com/vi/xHydnJGcs2k/0.jpg
   :target: https://youtu.be/xHydnJGcs2k
