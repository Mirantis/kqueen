from .aks import AksEngine


class TestAksInit:
    def setup(self):
        pass

    def test_init_aks(self, cluster):
        AksEngine(cluster)
