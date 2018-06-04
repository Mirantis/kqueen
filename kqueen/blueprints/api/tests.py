from flask import url_for
from kqueen.conftest import app, AuthHeader
from uuid import uuid4

import pytest

methods = ['GET', 'POST', 'PATCH', 'DELETE']
url_skip = ['/api/v1/health']


def generate_arg(name):
    """Return sample argument value for argument name."""
    if name == 'pk':
        return uuid4()
    if name == 'filename':
        return 'test.json'
    if name == 'page':
        return '0'
    raise KeyError('Argument name {} not known'.format(name))


def skip_rule(rule):
    return not rule.endpoint.startswith('api.')


def get_urls():
    """List all used urls, including pks."""
    app_instance = app()
    app_instance.config['SERVER_NAME'] = 'server'
    urls = []

    for rule in app_instance.url_map.iter_rules():
        if skip_rule(rule):
            continue

        options = {'_external': False}
        for arg_name in rule.arguments:
            options[arg_name] = generate_arg(arg_name)

        with app_instance.app_context():
            url = url_for(rule.endpoint, **options)
            if url not in url_skip:
                urls.append(url)

    return urls


def test_root(client):
    test_auth_header = AuthHeader()
    response = client.get(url_for('api.index'), headers=test_auth_header.get(client))

    assert response.json == {'response': 'Kqueen ready!'}
    test_auth_header.destroy()


# TODO: fix bad request code
@pytest.mark.skip('not working yet')
@pytest.mark.parametrize('method_name', methods)
@pytest.mark.parametrize('url', get_urls())
def test_all_views_require_token(client, method_name, url):
    method = getattr(client, method_name.lower())
    response = method(
        url,
        data='{}',
        content_type='application/json',
    )
    assert response.status_code in {401, 405}
