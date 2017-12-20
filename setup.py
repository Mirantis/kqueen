"""Setup for kqueen package."""

from setuptools import setup, find_packages

version = '0.15'

with open('README.rst') as f:
    long_description = ''.join(f.readlines())

test_require = [
    'coveralls',
    'faker',
    'flake8',
    'pytest',
    'pytest-cov',
    'pytest-env',
    'pytest-flask',
    'pytest-ordering',
]

setup(
    name='kqueen',
    version=version,
    description='Kubernetes cluster orchestrator',
    long_description=long_description,
    author='Tomáš Kukrál',
    author_email='tomas.kukral@6shore.net',
    license='MIT',
    url='https://github.com/Mirantis/kqueen/',
    download_url='https://github.com/Mirantis/kqueen/archive/v{}.tar.gz'.format(version),
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=[
        'bcrypt',
        'Flask==0.12.2',
        'Flask-JWT==0.3.2',
        'flask-swagger-ui',
        'gunicorn',
        'kubernetes',
        'pycrypto',
        'prometheus_client',
        'python-etcd',
        'python-jenkins',
        'pyyaml',
        'requests',
        'google-api-python-client==1.6.4',
        'google-auth==1.2.1',
        'google-auth-httplib2==0.0.3',
        'azure==2.0.0',
        'azure-mgmt-containerservice',
    ],
    setup_requires=[
        'pytest-runner',
    ],
    tests_require=test_require,
    extras_require={
        'dev': test_require + [
            'ipython',
            'sphinx',
            'sphinx-autobuild',
            'sphinx_rtd_theme',
        ]
    },
    classifiers=[
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
    entry_points={
        'console_scripts': [
            'kqueen = kqueen.server:run',
        ],
    },
)
