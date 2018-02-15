from collections import defaultdict
from kqueen.models import Organization
from kqueen.models import User
from prometheus_client import Gauge

import asyncio
import logging

logger = logging.getLogger('kqueen_api')

metrics = {
    'users_by_namespace': Gauge('users_by_namespace', 'Number of users in namespace', ['namespace']),
    'users_by_role': Gauge('users_by_role', 'Number of users by role', ['role']),
    'users_active': Gauge('users_active', 'Number of users by role'),
    'organization_count': Gauge('organization_count', 'Number of organizations'),
}


class MetricUpdater:
    def __init__(self):
        self.data = {}

        self.get_data()

    def update_metrics(self):
        # get or establish event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                raise RuntimeError('Loop already closed')
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        futures = []

        for metric_name, metric in metrics.items():

            update_function_name = 'update_metric_{}'.format(metric_name)

            logger.debug('Updating metric {metric_name}, with function {function}'.format(
                metric_name=metric_name,
                function=update_function_name,
            ))

            try:
                fnc = getattr(self, update_function_name)
            except AttributeError:
                msg = 'Missing update function {function} for metric {metric_name}'.format(
                    metric_name=metric_name,
                    function=update_function_name
                )

                raise Exception(msg)

            # run update function
            future = loop.run_in_executor(None, fnc, metric)
            futures.append(future)

        # run all updates
        asyncio.wait(futures)
        loop.close()

    def get_data(self):
        # users
        cls = User
        namespace = None

        sum = defaultdict(lambda: defaultdict(lambda: 0))

        for obj_id, obj in cls.list(namespace, True).items():
            user_dict = obj.get_dict(True)

            user_namespace = user_dict['organization']['namespace']
            user_role = user_dict['role']
            user_active = user_dict['active']

            sum['namespace'][user_namespace] += 1
            sum['roles'][user_role] += 1
            sum['active'][user_active] += 1

        self.data['users'] = sum

        # organizations
        objs = Organization.list(None, False)
        self.data['organizations'] = len(objs)

    def update_metric_users_by_namespace(self, metric):
        for namespace, count in self.data['users']['namespace'].items():
            metric.labels(namespace).set(count)

    def update_metric_users_by_role(self, metric):
        for role, count in self.data['users']['roles'].items():
            metric.labels(role).set(count)

    def update_metric_users_active(self, metric):
        metric.set(self.data['users']['active'][True])

    def update_metric_organization_count(self, metric):
        metric.set(self.data['organizations'])
