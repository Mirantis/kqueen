from kubernetes import client
from kubernetes import config

import jenkins
import requests
import json

import logging
logging.getLogger('kubernetes.requests.packages.urllib3.connectionpool').setLevel(logging.CRITICAL)

jenkins_url = 'https://ci.mcp.mirantis.net'
job_name = 'deploy-aws-k8s_ha_calico'

client.configuration.logger['urllib3_logger'].setLevel(logging.CRITICAL)
client.configuration.logger['package_logger'].setLevel(logging.CRITICAL)
import logging
import requests
logging.getLogger(requests.packages.urllib3.__package__).setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)

def main():

    server = jenkins.Jenkins(jenkins_url)
    job = server.get_job_info(job_name)
    for build in job['builds']:
        build_info = server.get_build_info(job_name, build['number'])

        if build_info['result'] == 'SUCCESS':
            stack_name = build_info['description'].split(' ')[0]

            # outputs
            response = requests.get(build_info['url'] + 'artifact/outputs.json')
            try:
                outputs = response.json()
            except json.decoder.JSONDecodeError:
                print('Failed json')
                continue

            response = requests.get(build_info['url'] + 'artifact/kubeconfig')
            kubeconfig = response.text

            with open('/tmp/kubeconfig', 'w') as f:
                f.write(kubeconfig)

            print("Cluster: {}".format(stack_name))
            print("API: {}".format(outputs['kubernetes_apiserver']))

            cl = config.new_client_from_config(config_file='/tmp/kubeconfig', persist_config=False)
            api_instance = client.CoreV1Api(api_client=cl)

            try:
                api_response = api_instance.list_node()
                print('Nodes: ' + str([i.metadata.name for i in api_response.items]) + "\n")
            except:
                print('No nodes - cluster offline')
