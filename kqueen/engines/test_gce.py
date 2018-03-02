from .gce import GceEngine
import requests

PROVISIONER_PARAMETERS = {
    'project': 'username:password',
    'zone': '-'
}

SERVICE_ACCOUNT_INFO = {
    'type': 'service_account',
    'project_id': 'XXXXXXXXX',
    'private_key_id': 'd2f2c568d42fb1ed5f5ea0db9aa6f5f774f98467',
    'private_key': '-----BEGIN PRIVATE KEY-----\n-----END PRIVATE KEY-----\n',
    'client_email': 'compute@gserviceaccount.com',
    'client_id': 'XXXXXXXXXX',
    'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
    'token_uri': 'https://accounts.google.com/o/oauth2/token',
    'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs',
    'client_x509_cert_url': 'XXXXXXXXXXXXXXXX'
}


class TestGce:
    # TODO provide valid client mocking or define testing credentials
    # to get access to all google client methods
    def test_cluster_list(self, cluster, monkeypatch):
        def fake_init(self, cluster):
            # Client initialization
            self.service_account_info = SERVICE_ACCOUNT_INFO
            self.project = PROVISIONER_PARAMETERS.get('project', '')
            self.zone = PROVISIONER_PARAMETERS.get('zone', '-')
            self.client = self._get_client()
            # Cache settings
            self.cache_timeout = 5 * 60

        def fake_client(self):
            return True

        def fake_cluster_list(self):
            # Dummy check instead of client mocking or defining valid credentials
            test_url = 'https://container.googleapis.com/v1/projects/project/zones/zone/clusters?alt=json'
            headers = {'Accept': 'application/json'}
            response = requests.get(test_url, headers=headers)
            if response.status_code == 401:
                return True
            return False

        monkeypatch.setattr(GceEngine, '__init__', fake_init)
        monkeypatch.setattr(GceEngine, '_get_client', fake_client)
        monkeypatch.setattr(GceEngine, 'cluster_list', fake_cluster_list)
        engine = GceEngine(cluster)

        assert engine.cluster_list()
