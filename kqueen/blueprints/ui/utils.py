def status_for_cluster_detail(_status):
    status = {}
    podcount = 0

    nodes = []
    if 'nodes' in _status:
        for node in _status['nodes']:
            node_name = node['metadata']['name']
            excluded_addr_types = ['LegacyHostIP', 'InternalDNS', 'ExternalDNS', 'Hostname']
            node_ip = [
                a['type'] + ': ' + a['address']
                for a in node['status']['addresses']
                if a['type'] not in excluded_addr_types
            ]
            node_os = {
                'os': node['status']['node_info']['os_image'],
                'kernel': node['status']['node_info']['kernel_version']
            }
            node_status = []
            for sc in node['status']['conditions']:
                if sc['type'] != 'Ready':
                    if sc['status'] == 'False':
                        icon = 'ok'
                    else:
                        icon = 'remove'
                    node_status.append({
                        'type': sc['type'],
                        'icon': icon
                    })
            _ram = int(node['status']['allocatable']['memory'].replace('Ki', '')) / 1000000
            ram = '{:10.2f}'.format(_ram)
            cpu = node['status']['allocatable']['cpu']
            node_size = cpu + '/' + ram
            pods = int(_status.get('nodes_pods', {}).get(node['metadata']['name']))
            podcount += pods
            maxpods = int(node['status']['allocatable']['pods'])
            percentage = (pods / maxpods) * 100
            node_pods = {
              'pods': pods,
              'maxpods': maxpods,
              'percentage': percentage
            }
            nodes.append({
                'name': node_name,
                'ip': node_ip,
                'os': node_os,
                'status': node_status,
                'size': node_size,
                'pods': node_pods,
            })
    status['nodes'] = nodes

    deployments = []
    if 'deployments' in _status:
        for deployment in _status['deployments']:
            deployment_name = deployment['metadata']['name']
            deployment_namespace = deployment['metadata']['namespace']
            _ready = deployment.get('status', {}).get('ready_replicas', '0')
            ready = int(_ready) if _ready else 0
            _desired = deployment.get('spec', {}).get('replicas', '0')
            desired = int(_desired) if _desired else 0
            percentage = 0
            if desired > 0:
                percentage = (ready / desired) * 100
            deployment_replicas = {
                'ready': ready,
                'desired': desired,
                'percentage': percentage
            }
            containers = deployment.get('spec', {}).get('template', {}).get('spec', {}).get('containers', [])
            deployment_containers = [
                {
                    'name': c['name'],
                    'image': c['image']
                }
                for c
                in containers
            ]
            deployments.append({
                'name': deployment_name,
                'namespace': deployment_namespace,
                'replicas': deployment_replicas,
                'containers': deployment_containers
            })
    status['deployments'] = deployments

    services = []
    if 'services' in _status:
        for service in _status['services']:
            service_name = service['metadata']['name']
            service_namespace = service['metadata']['namespace']
            service_cluster_ip = service['spec']['cluster_ip']
            _ports = service.get('spec', {}).get('ports', [])
            ports = _ports or []
            service_ports = [
                '%s/%s %s' % (p['port'], p['protocol'], p.get('name', ''))
                for p
                in ports
            ]
            ingress = service.get('status', {}).get('load_balancer', {}).get('ingress', [])
            service_external_ip = []
            if ingress:
                for endpoint in ingress:
                    _port_map = {
                        80: 'http',
                        8080: 'http',
                        443: 'https',
                        4430: 'https',
                        6443: 'https'
                    }
                    hostname = endpoint.get('hostname', '')
                    if hostname:
                        for port in ports:
                            _port = port['port']
                            proto = _port_map[_port] if _port in _port_map else 'http'
                            service_external_ip.append('%s://%s:%s' % (proto, hostname, _port))
            services.append({
                'name': service_name,
                'namespace': service_namespace,
                'cluster_ip': service_cluster_ip,
                'ports': service_ports,
                'external_ip': service_external_ip
            })
    status['services'] = services

    status['addons'] = _status['addons'] if 'addons' in _status else []
    status['overview'] = {
        'namespaces': 2,
        'nodes': len(status['nodes']),
        'deployments': len(status['deployments']),
        'pods': podcount,
        'services': len(status['services'])
    }

    return status
