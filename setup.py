from setuptools import setup, find_packages

version = '0.2'

with open('README.md') as f:
    long_description = ''.join(f.readlines())

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
    install_requires=[
        'python-jenkins',
        'requests',
        'kubernetes',
        'flask',
        'pyyaml',
        'python-etcd',
    ],
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
