from celery import Celery, group
from kqueen.models import Cluster, Organization
from kqueen.server import cache, create_app


def make_celery(app):
    celery = Celery(app.import_name, backend=app.config['CELERY_RESULT_BACKEND'],
                    broker=app.config['CELERY_BROKER_URL'])
    celery.conf.beat_schedule = app.config.get('CELERY_BEAT_SCHEDULE', {})
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery


flask_app = create_app()
celery = make_celery(flask_app)


class UniqueTask(celery.Task):
    LOCK_DURATION = 60
    _lock_key = None

    def lock(self):
        if not self._lock_key:
            raise Exception('_lock_key needs to be set on self, before calling lock.')
        return cache.set(self._lock_key, True, self.LOCK_DURATION)

    def unlock(self):
        if not self._lock_key:
            raise Exception('_lock_key needs to be set on self, before calling unlock.')
        return cache.delete(self._lock_key)

    def is_locked(self):
        if not self._lock_key:
            raise Exception('_lock_key needs to be set on self, before calling is_locked.')
        value = cache.get(self._lock_key)
        return value if value else False

    def run(self, *args, **kwargs):
        '''
        Test if locked. Lock if not. Do something. Unlock.
        '''
        self._lock_key = 'unique-task'
        if self.is_locked():
            return
        self.lock()
        # DO SOMETHING

    def after_return(self, *args, **kwargs):
        self.unlock()
        return super().after_return(*args, **kwargs)


class ClusterStatus(UniqueTask):
    name = 'cluster_status'
    ignore_result = True
    time_limit = 30

    def run(self, namespace, cluster_id):
        print('Fetching status of cluster {} ...'.format(cluster_id))
        self._lock_key = 'task-cluster-status-{}-lock'.format(cluster_id)
        # Test lock
        if self.is_locked():
            return
        # Lock
        self.lock()
        # Main
        status_key = 'task-cluster-status-{}'.format(cluster_id)
        cluster = Cluster.load(namespace, cluster_id)
        try:
            status = cluster.status()
            cache.set(status_key, status, 30)
            print('Status of cluster {} successfully cached!'.format(cluster_id))
        except Exception:
            # Invalidate current cache, if we are unable to contact backend
            cache.delete(status_key)

celery.tasks.register(ClusterStatus())


class ClusterBackendData(UniqueTask):
    name = 'cluster_backend_data'
    ignore_result = True
    time_limit = 30

    def run(self, namespace, cluster_id):
        print('Fetching backend data for cluster {} ...'.format(cluster_id))
        self._lock_key = 'task-cluster-backend-data-{}-lock'.format(cluster_id)
        # Test lock
        if self.is_locked():
            return
        # Lock
        self.lock()
        # Main
        backend_data_key = 'task-cluster-backend-data-{}'.format(cluster_id)
        cluster = Cluster.load(namespace, cluster_id)
        try:
            backend_data = cluster.engine.cluster_get()
            cache.set(backend_data_key, backend_data, 30)
            print('Backend data for cluster {} successfully cached!'.format(cluster_id))
        except Exception:
            # Invalidate current cache, if we are unable to contact backend
            cache.delete(backend_data_key)

celery.tasks.register(ClusterBackendData())


class UpdateClusters(celery.Task):
    name = 'update_clusters'
    ignore_result = True

    def run(self):
        print('Cluster update started ...')
        get_backend_data = celery.tasks[ClusterBackendData.name]
        get_status = celery.tasks[ClusterStatus.name]
        namespaces = [o.namespace for o in Organization.list(None).values()]
        for namespace in namespaces:
            clusters = [c for c in Cluster.list(namespace).values()]
            # Launch and forget
            backend_data = group([get_backend_data.s(namespace, c.id) for c in clusters])
            backend_data.apply_async()
            statuses = group([get_status.s(namespace, c.id) for c in clusters])
            statuses.apply_async()

celery.tasks.register(UpdateClusters())
