from tempfile import mkstemp

import json
import os
import re
import six
import subprocess


class HelmMissingDependency(Exception):
    pass


class HelmCallError(Exception):
    pass


class HelmWrapper:
    def __init__(self, kubeconfig):
        # check for helm binary
        self.kubepath = ''
        try:
            self._call('which helm')
        except HelmCallError:
            raise HelmMissingDependency('Helm binary is required to use HelmWrapper.')
        if not isinstance(kubeconfig, dict):
            raise TypeError('Kubeconfig must be dictionary.')
        self.kubehandle, self.kubepath = mkstemp(prefix='khelm-')
        with open(self.kubepath, 'w') as outfile:
            json.dump(kubeconfig, outfile)

    def __del__(self):
        try:
            os.close(self.kubehandle)
            os.remove(self.kubepath)
        except Exception:
            pass

    def _call(self, cmd):
        if isinstance(cmd, six.string_types):
            cmd = cmd.split()
        env = os.environ.copy()
        env['KUBECONFIG'] = self.kubepath
        res = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode != 0:
            raise HelmCallError(res.stderr.decode('utf-8'))
        return res.stdout.decode('utf-8')

    def _no_parse(self, response):
        return {'raw': response}

    def _parse_helm_horizontal_list(self, response, keys):
        parsed = []
        lines = response.splitlines()
        if lines:
            del lines[0]
            for line in lines:
                parsed_line = re.split(r'\t+', line)
                clean_line = [ch.rstrip() for ch in parsed_line]
                item = dict(zip(keys, clean_line))
                parsed.append(item)
        return parsed

    def delete(self, release):
        raw = self._call('helm delete {}'.format(release))
        return self._no_parse(raw)

    def get(self, release):
        raw = self._call('helm get {}'.format(release))
        return self._no_parse(raw)

    def _parse_history(self, response):
        keys = ['revision', 'updated', 'status', 'chart', 'description']
        return self._parse_helm_horizontal_list(response, keys)

    def history(self, release):
        raw = self._call('helm history {}'.format(release))
        return self._parse_history(raw)

    def init(self):
        raw = self._call('helm init')
        return self._no_parse(raw)

    def install(self, chart):
        raw = self._call('helm install {}'.format(chart))
        return self._no_parse(raw)

    def _parse_list(self, response):
        keys = ['name', 'revision', 'updated', 'status', 'chart', 'namespace']
        return self._parse_helm_horizontal_list(response, keys)

    def list(self):
        raw = self._call('helm list')
        return self._parse_list(raw)

    def repo_update(self):
        raw = self._call('helm repo update')
        return self._no_parse(raw)

    def reset(self):
        raw = self._call('helm reset')
        return self._no_parse(raw)
