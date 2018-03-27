from tempfile import mkstemp

import asyncio
import concurrent.futures
import json
import os
import re
import six
import subprocess
import yaml


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

    async def _get_catalog(self, loop, chart_names):
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [
                loop.run_in_executor(
                    executor,
                    self.inspect,
                    cname
                )
                for cname in chart_names
            ]
        for result in await asyncio.gather(*futures):
            results.append(result)
        return results

    def catalog(self):
        charts = self.search()
        chart_names = [c['name'] for c in charts]
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.SelectorEventLoop()
        charts = loop.run_until_complete(self._get_catalog(loop, chart_names))
        return charts

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

    def _parse_inspect(self, response):
        _chart = response.split('\n---')[0]
        _values = response.split('\n---')[1]
        try:
            chart = yaml.load(_chart)
        except Exception:
            chart = {}
        try:
            values = yaml.load(_values)
        except Exception:
            values = {}
        return {
            'chart': chart,
            'values': values
        }

    def inspect(self, chart):
        raw = self._call('helm inspect {}'.format(chart))
        return self._parse_inspect(raw)

    def install(self, chart, release_name=None, overrides=None):
        cmd = 'helm install'
        if release_name:
            cmd = cmd + ' --name={}'.format(release_name)
        if overrides and isinstance(overrides, dict):
            ovrdhandle, ovrdpath = mkstemp(prefix='khelm-ovrd-')
            with open(ovrdpath, 'w') as outfile:
                json.dump(overrides, outfile)
            cmd = cmd + ' -f {}'.format(ovrdpath)
        cmd = cmd + ' {}'.format(chart)
        raw = self._call(cmd)
        try:
            os.close(ovrdhandle)
            os.remove(ovrdpath)
        except Exception:
            pass
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

    def _parse_search(self, response):
        keys = ['name', 'version', 'description']
        return self._parse_helm_horizontal_list(response, keys)

    def search(self, chart=None):
        cmd = 'helm search'
        if chart:
            cmd = cmd + ' {}'.format(chart)
        raw = self._call(cmd)
        return self._parse_search(raw)

    def version(self):
        raw = self._call('helm version')
        return self._no_parse(raw)
