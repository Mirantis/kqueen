def test_dummy():
    assert True


def test_main(monkeypatch):
    global started
    started = False

    def fake_run():
        global started
        started = True

    monkeypatch.setattr('kqueen.server.run', fake_run)

    from kqueen import __main__
    print(dir(__main__))

    assert started, 'run() not executed'
