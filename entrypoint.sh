#!/bin/bash
set -ex

# export additional variables
export prometheus_multiproc_dir="$(mktemp -d)"
BOOTSTRAP_ADMIN="${BOOTSTRAP_ADMIN:-False}"
BOOTSTRAP_ADMIN_USERNAME="${BOOTSTRAP_ADMIN_USERNAME:-admin}"
BOOTSTRAP_ADMIN_PASSWORD="${BOOTSTRAP_ADMIN_PASSWORD:-default}"
BOOTSTRAP_ADMIN_ORGANIZATION="${BOOTSTRAP_ADMIN_ORGANIZATION:-DemoOrg}"
BOOTSTRAP_ADMIN_NAMESPACE="${BOOTSTRAP_ADMIN_NAMESPACE:-demoorg}"

if [[ "$BOOTSTRAP_ADMIN" == "True" ]] ; then
    python bootstrap_admin.py ${BOOTSTRAP_ADMIN_ORGANIZATION} ${BOOTSTRAP_ADMIN_NAMESPACE} ${BOOTSTRAP_ADMIN_USERNAME} ${BOOTSTRAP_ADMIN_PASSWORD}
fi

exec gunicorn --config kqueen/gunicorn.py kqueen.wsgi
