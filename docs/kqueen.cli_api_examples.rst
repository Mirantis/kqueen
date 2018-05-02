Kqueen CLI API Examples
-----------------------

Obtain bearer token and authenticate to kqueen:

.. code-block:: bash

   $ TOKEN=$(curl -s -H "Content-Type: application/json" --data '{ "username": "admin", "password": "default" }' -X POST 127.0.0.1:5000/api/v1/auth | jq -r '.access_token')
   $ echo $TOKEN

List organizations

.. code-block:: bash

   $ curl -s -H "Authorization: Bearer $TOKEN" 127.0.0.1:5000/api/v1/organizations | jq

Check the clusters:

.. code-block:: bash

   $ curl -s -H "Authorization: Bearer $TOKEN" 127.0.0.1:5000/api/v1/clusters | jq


List users

.. code-block:: bash

   $ curl -s -H "Authorization: Bearer $TOKEN" 127.0.0.1:5000/api/v1/users | jq


Create new organization "testorg"

.. code-block:: bash

   $ curl -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" --data '{ "name": "testorg", "namespace": "testorg" }' -X POST 127.0.0.1:5000/api/v1/organizations | jq
