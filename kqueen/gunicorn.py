from kqueen.config import current_config
from prometheus_client import multiprocess

import multiprocessing
import os

app_config = current_config()

bind = "{host}:{port}".format(
    host=app_config.get('KQUEEN_HOST'),
    port=app_config.get('KQUEEN_PORT'),
)
workers = multiprocessing.cpu_count() * 2 + 1

# check for prometheus settings
if 'prometheus_multiproc_dir' not in os.environ:
    raise Exception('Variable prometheus_multiproc_dir is required')


def child_exit(server, worker):
    multiprocess.mark_process_dead(worker.pid)
