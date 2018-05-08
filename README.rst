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
------------

-  Python v3.6 and higher.
-  Pip v3 and higher.
-  Docker stable release (v17.03 and higher is preferable).
-  Docker-compose stable release (v1.16.0 and higher is preferable).


Demo environment
----------------

- Make sure you can reach Jenkins server defined in `JENKINS_API_URL` variable in file `kqueen/config/prod.py`.
- Run these commands to run Kqueen API and UI in containers.

  ::

    docker-compose -f docker-compose.yml -f docker-compose.demo.yml up

  or with mounted etcd data directory:

  ::

    docker-compose -f docker-compose.etcd-volume.yml -f docker-compose.demo.yml up

- You can login using user `admin` and password `default`.
  Default username and password can be changed in `docker-compose.demo.yml` file before first start of API.


- Navigate to UI

  * http://127.0.0.1:5080/
  * http://127.0.0.1:5000/api/docs/


Development
-----------

- Install dependencies

    ::

      # Debian/Ubuntu
      sudo apt-get install libsasl2-dev python-dev libldap2-dev libssl-dev

      # RedHat/CentOS:
      sudo yum install python-devel openldap-devel

- Prepare python virtual environment

  ::

    python -m ensurepip --default-pip
    pip install --user pipenv
    pipenv --python 3.6
    pipenv install --dev

    pipenv shell


- Start docker container with etcd storage

  ::

    docker-compose up -d

- Initialize kqueen db: add *admin* user with *default* password

  ::

     ./bootstrap_admin.py DemoOrg demoorg admin default
- You can start KQueen API service directly

  ::

    kqueen &
    chrome --new-tab http://127.0.0.1:5000/api/docs/

- Prepare kubernetes config file

 Kubernetes configuration file that describes existing cluster can be used in Kqueen.
 Rename it with *kubernetes_remote* and place to the root of the project.
 For test purposes this file can be empty, but should be added manually.


How-to's
^^^^^^^^

- Clean etcd storage after previous runs

  ::

    etcdctl rm --recursive /kqueen

- Add admin user, organization, mock clusters and provisioners to etcd storage at once, execute the following

  ::

    ./devenv.py

- To add a single *admin* user with *default* password within associated *DemoOrg* organization in provided *demoorg* namespace, execute the following

  ::

    ./bootstrap_admin.py DemoOrg demoorg admin default

- Test access token. *curl*,  *jq* should be installed in your system

  ::

    TOKEN=$(curl -s -H "Content-Type: application/json" --data '{"username":"admin","password":"default"}' -X POST localhost:5000/api/v1/auth | jq -r '.access_token')
    echo $TOKEN
    curl -H "Authorization: Bearer $TOKEN" localhost:5000/api/v1/clusters

- Set up flask shell for manual testing and debugging

  ::

    export FLASK_APP=kqueen.server
    export prometheus_multiproc_dir=$(mktemp -d)
    flask shell

- Update Docker image with code changes

There are two ways to test development changes. First is automatic: create a separate branch and push PR, then TravisCI
build image and push it on Docker Hub automatically. Second one is just rebuild kqueen api-image locally:

  ::

   docker build -t kqueen/api:your_tag .

Configuration
-------------

We load configuration from file ``config/dev.py`` by default and this
can be configured by ``KQUEEN_CONFIG_FILE`` environment variable. Any
environment variable matching name ``KQUEEN_*`` will be loaded and saved
to configuration.

Documentation
-------------

Full documentation including API reference can be found at
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
