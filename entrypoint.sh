#!/bin/bash

export prometheus_multiproc_dir="$(mktemp -d)"
BOOTSTRAP_ADMIN="${BOOTSTRAP_ADMIN:-0}"
BOOTSTRAP_ADMIN_USERNAME="${BOOTSTRAP_ADMIN_USERNAME:-admin}"
BOOTSTRAP_ADMIN_PASSWORD="${BOOTSTRAP_ADMIN_PASSWORD:-default}"
BOOTSTRAP_ADMIN_ORGANIZATION="${BOOTSTRAP_ADMIN_ORGANIZATION:-DemoOrg}"
BOOTSTRAP_ADMIN_NAMESPACE="${BOOTSTRAP_ADMIN_NAMESPACE:-demoorg}"

if [[ "$BOOTSTRAP_ADMIN" > 0 ]] ; then
    python bootstrap_admin.py ${BOOTSTRAP_ADMIN_ORGANIZATION} ${BOOTSTRAP_ADMIN_NAMESPACE} ${BOOTSTRAP_ADMIN_USERNAME} ${BOOTSTRAP_ADMIN_PASSWORD}
fi

# Setup permissions
chown -R kqueen:kqueen /tmp /code /var/log/kqueen 2>/dev/null || :
chmod -R 700 /tmp /code /var/log/kqueen 2>/dev/null || :

exec gosu kqueen "$@"
