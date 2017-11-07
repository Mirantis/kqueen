from kqueen.server import create_app


def test_main(monkeypatch):
    global started
    started = False

    def fake_run():
        global started
        started = True

    monkeypatch.setattr('kqueen.server.run', fake_run)

    from kqueen import __main__

    assert started, 'run() not executed'


def test_setup(monkeypatch):
    class fake_setup:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    monkeypatch.setattr('setuptools.setup', fake_setup)

    filename = 'README.md'

    from setup import long_description
    assert open(filename, 'r').read() == long_description


def test_app_config():
    app = create_app(config_file='nonexistent_file.py')
    assert hasattr(app, 'config')
