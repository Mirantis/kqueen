#!/bin/bash
TIMESTAMP=$(date +'%Y%m%d-%H%M%S')
HOSTNAME=$(hostname --fqdn)

DATADIR="/mnt/storage/kqueen/etcd/"
BACKUPDIR="/mnt/storage/backup/backup-${HOSTNAME}-${TIMESTAMP}"

etcdctl backup --data-dir "${DATADIR}" --backup-dir "${BACKUPDIR}"
