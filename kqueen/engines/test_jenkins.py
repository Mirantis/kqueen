from .jenkins import JenkinsEngine


class TestJenkinsInit:
    def setup(self):
        pass

    def test_init_jenkins(self, cluster):
        JenkinsEngine(cluster)

    def test_init_jenkins_with_kwargs(self, cluster):
        engine = JenkinsEngine(cluster, username='foo', password='bar')
        assert engine.username == 'foo'
        assert engine.password == 'bar'
