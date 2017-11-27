from .aks import AksEngine


class TestAksInit:

    def test_init_aks(self, cluster, monkeypatch):
        def fake_client(self):
            return True

        monkeypatch.setattr(AksEngine, '_get_client', fake_client)
        AksEngine(cluster)
