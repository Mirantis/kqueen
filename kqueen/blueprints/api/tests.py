from flask import url_for
from kqueen.conftest import app
from uuid import uuid4

import pytest

methods = ['GET', 'POST', 'PATCH', 'DELETE']
url_skip = ['/api/v1/health']


def generate_arg(name):
    """Return sample argument value for argument name."""

    if name == 'pk':
        return uuid4()

    elif name == 'filename':
        return 'test.json'
    else:
        raise KeyError('Argument name {} not known'.format(name))


def get_urls():
    """List all used urls, including pks."""
    app_instance = app()
    app_instance.config['SERVER_NAME'] = 'server'
    urls = []

    for rule in app_instance.url_map.iter_rules():
        options = {'_external': False}
        for arg_name in rule.arguments:
            options[arg_name] = generate_arg(arg_name)

        with app_instance.app_context():
            url = url_for(rule.endpoint, **options)
            if url not in url_skip:
                urls.append(url)

    return urls


def test_root(client, auth_header):
    response = client.get(url_for('api.index'), headers=auth_header)

    assert response.json == {'response': 'Gutten tag!'}


@pytest.mark.parametrize('method_name', methods)
@pytest.mark.parametrize('url', get_urls())
def test_all_views_require_token(client, method_name, url):
    method = getattr(client, method_name.lower())
    response = method(
        url,
        data='{}',
        content_type='application/json',
    )
    assert response.status_code > 400
