from flask import url_for


def test_root(client, auth_header):
    response = client.get(url_for('api.index'), headers=auth_header)

    assert response.json == {'response': 'Gutten tag!'}
