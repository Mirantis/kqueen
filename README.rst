KQueen - Kubernetes cluster manager
===================================


.. image:: https://travis-ci.org/Mirantis/kqueen.svg?branch=master
    :target: https://travis-ci.org/Mirantis/kqueen

.. image:: https://badge.fury.io/py/kqueen.svg
    :target: https://badge.fury.io/py/kqueen

.. image:: https://coveralls.io/repos/github/Mirantis/kqueen/badge.svg?branch=master
    :target: https://coveralls.io/github/Mirantis/kqueen?branch=master


Development
-----------

-  Bootstrap kqueen environment

::

    mkvirtualenv -p /usr/bin/python3 kqueen
    pip3 install -r requirements.txt
    pip3 install --editable .
    # start etcd in container
    docker-compose up -d # start
    kqueen

-  Clean etcd storage and prepare examples

`devenv.py` will create few objects to provides basic developer environment. It will also try to download `kubeconfig` file for real cluster but it requires access to Mirantis VPN. However, it can be workarounded by creating file `kubeconfig_remote` in repository root and this file will be used instead of downloading it.

::

    etcdctl rm --recursive /kqueen
    ./devenv.py

Demo environment
----------------

-  Without local Kubernetes

::

    docker-compose -f docker-compose.yml -f docker-compose.demo.yml up

-  Including local Kubernetes (without ``kubelet``)

::

    docker-compose -f docker-compose.yml -f docker-compose.demo.yml -f docker-compose.kubernetes.yml up

-  You can add some example data by running

::

    docker-compose -f docker-compose.yml -f docker-compose.demo.yml exec kqueen ./devenv.py

It will add user ``admin`` with password ``default`` and few of testing
objects.

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
