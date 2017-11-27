from flask import current_app
from flask import url_for

import pytest


@pytest.mark.usefixtures('client_class')
class TestMetrics:
    def setup(self):
        self.url = url_for('metrics.root')
        self.response = self.client.get(self.url)
        self.content = self.response.data.decode(self.response.charset)

    def test_assert_status(self):
        assert self.response.status_code == 200


class TestAccess:
    def setup(self):
        self.url = url_for('metrics.root')

    @pytest.mark.parametrize('whitelist,code', [
        ('127.0.0.0/8', 200),
        ('8.8.8.8/32', 401),
        ('2001:db8:a0b:12f0::/64', 401),
    ])
    def test_metrics_acccess(self, client, monkeypatch, whitelist, code):
        monkeypatch.setitem(current_app.config, 'PROMETHEUS_WHITELIST', whitelist)

        response = client.get(self.url)
        assert response.status_code == code
