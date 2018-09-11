from .base import BaseEngine
from kqueen.config import current_config
from kqueen.server import app
from kqueen import kubeapi

import base64
import copy
import ipaddress
import json
import logging
import openstack
import os
import shlex
import shutil
import subprocess
import time
import yaml
import uuid

logger = logging.getLogger("kqueen_api")
config = current_config()


class OpenstackKubesprayEngine(BaseEngine):
    """OpenStack Kubespray engine.

    This engine can provision k8s cluster in OpenStack cloud.

    Ansible and Kubespray should be installed and configured.

    Path to kubespray may be configured by setting KS_KUBESPRAY_PATH,
    e.g. by setting environment variable KQUEEN_KS_KUBESPRAY_PATH.

    Known to work with kubespray-2.5.0, ansible-2.4.3.0 and
    ubuntu 16.04 image.

    """
    name = "openstack_kubespray"
    verbose_name = "Openstack Kubespray Engine"
    parameter_schema = {
        "cluster": {
            "ssh_key_name": {
                "type": "text",
                "order": 10,
                "label": "SSH key name",
                "validators": {
                    "required": True,
                },
            },
            "ssh_username": {
                "type": "text",
                "order": 15,
                "label": "SSH username",
                "default": "ubuntu",
                "validators": {
                    "required": True,
                },
            },
            "image_name": {
                "type": "text",
                "order": 20,
                "label": "Image name",
                "validators": {
                    "required": True,
                },
            },
            "master_flavor": {
                "type": "text",
                "order": 30,
                "label": "Master flavor",
                "validators": {
                    "required": True,
                },
            },
            "slave_flavor": {
                "type": "text",
                "order": 30,
                "label": "Slave flavor",
                "validators": {
                    "required": True,
                },
            },
            "master_count": {
                "type": "integer",
                "order": 40,
                "default": 3,
                "label": "Master node count",
                "help_message": "Must be odd number",
                "validators": {
                    "required": True,
                    "parity": "odd",
                },
            },
            "slave_count": {
                "type": "integer",
                "order": 50,
                "default": 1,
                "label": "Slave node count",
                "validators": {
                    "required": True,
                },
            },
            "floating_network": {
                "order": 60,
                "type": "text",
                "label": "Floating network name or id",
                "default": "public",
            },
            "docker_bip_network": {
                "type": "text",
                "order": 70,
                "label": "Docker0 bridge IP",
                "default": "10.13.0.1/16",
                "help_message": "network IP and netmask in CIDR format",
                "validators": {
                    "cidr": True,
                },
            },
            "dns_nameservers": {
                "type": "text",
                "order": 80,
                "label": "Comma separated list of nameservers",
                "default": config.KS_DEFAULT_NAMESERVERS,
                "validators": {
                    "ip_list": True,
                },
            },
            "availability_zone": {
                "type": "text",
                "order": 90,
                "label": "Availability zone",
                "default": "nova",
            },
        },
        "provisioner": {
            "auth_url": {
                "type": "text",
                "label": "Auth URL",
                "order": 10,
                "validators": {
                    "required": True,
                    "url": True,
                },
            },
            "username": {
                "type": "text",
                "label": "Username",
                "order": 20,
                "validators": {
                    "required": True,
                },
            },
            "password": {
                "type": "password",
                "label": "Password",
                "order": 30,
                "validators": {
                    "required": True,
                },
            },
            "domain_name": {
                "type": "text",
                "label": "Domain name",
                "help_message": "Leave empty if using keystone v2",
                "order": 40,
            },
            "project_id": {
                "type": "text",
                "label": "Project ID",
                "help_message": "Tenant ID if using keystone v2",
                "order": 50,
                "validators": {
                    "required": True,
                },
            },
            "region_name": {
                "type": "text",
                "order": 60,
                "label": "Region name",
                "default": "RegionOne",
                "validators": {
                    "required": True,
                }
            },
            "identity_interface": {
                "type": "text",
                "label": "Identity interface",
                "order": 70,
                "default": "public",
                "validators": {
                    "required": True,
                }
            },
        }
    }

    def __init__(self, cluster, *args, **kwargs):
        """
        :param kqueen.models.Cluster cluster:
        """
        super().__init__(cluster, *args, **kwargs)
        short_uuid = base64.b32encode(uuid.UUID(cluster.id).bytes)[:26].lower()
        self.stack_name = "kq-" + short_uuid.decode('ascii')
        self.ks = Kubespray(
            cluster_id=cluster.id,
            ssh_username=kwargs["ssh_username"],
            clusters_path=config.KS_FILES_PATH,
            kubespray_path=config.KS_KUBESPRAY_PATH,
            os_kwargs=kwargs,
        )
        self.os = OpenStack(
            self.stack_name,
            os_kwargs=kwargs,
            cluster=cluster,
            extra_ssh_key=self.ks.get_ssh_key(),
        )

    def provision(self):
        try:
            self.os.validate_cluster_metadata()

            self.cluster.state = config.CLUSTER_PROVISIONING_STATE
            self.cluster.save()
            app.executor.submit(self._run_provisioning)
        except Exception as e:
            self.cluster.state = config.CLUSTER_ERROR_STATE
            self.cluster.metadata['status_message'] = repr(e)
            self.cluster.save()
            # Reraise error to return correct error code
            raise e
        return True, None

    def _run_provisioning(self):
        try:
            resources = self.os.provision()
            self.cluster.metadata["resources"] = resources
            node_count = len(resources["masters"] + resources["slaves"])
            self.cluster.metadata["node_count"] = node_count
            self.cluster.save()
            self.allow_addresses_for_calico(resources)
            kubeconfig = self.ks.deploy(resources)
            self.cluster.kubeconfig = kubeconfig
            self.cluster.state = config.CLUSTER_OK_STATE
            logger.info("Cluster provision completed")
        except Exception as e:
            self.cluster.state = config.CLUSTER_ERROR_STATE
            logger.exception("Failed to provision cluster: %s" % e)
            self.cluster.metadata['status_message'] = getattr(e, 'details', repr(e))
            if getattr(self.ks, 'ansible_log'):
                self.cluster.metadata['status_message'] += "\n More details can be found " \
                                                           "at {}".format(self.ks.ansible_log)
        finally:
            self.cluster.save()

    def allow_addresses_for_calico(self, resources):
        kube_service_addresses = '10.233.0.0/18'
        kube_pods_subnet = '10.233.64.0/18'
        vm_ids = [i['id'] for i in (*resources['masters'], *resources['slaves'])]
        neutron = self.os.get_neutron_client()

        for p in neutron.list_ports(network_id=resources['network_id'])['ports']:
            if p['device_id'] in vm_ids:
                neutron.update_port(p['id'],
                                    {'port': {'allowed_address_pairs': [{'ip_address': kube_service_addresses},
                                                                        {'ip_address': kube_pods_subnet}]}})

    def deprovision(self):
        try:
            pvc_names = self._cleanup_pvc()
        except Exception as e:
            logger.warning("Unable to cleanup pvc: %s" % e)
            pvc_names = []
        try:
            self.ks.delete()
        except Exception as e:
            logger.warning("Unable to cleanup kubespray data: %s" % e)
        try:
            self.os.deprovision(volume_names=pvc_names)
        except Exception as e:
            logger.exception("Unable to remove cluster: %s" % e)
            self.cluster.state = config.CLUSTER_ERROR_STATE
            self.cluster.save()
            return False, e
        return True, None

    def _cleanup_pvc(self):
        kubernetes = kubeapi.KubernetesAPI(cluster=self.cluster)
        body = kubeapi.client.V1DeleteOptions()

        # delete storage classes first
        for sc in kubernetes.api_storagev1.list_storage_class().items:
            name = sc.to_dict()["metadata"]["name"]
            kubernetes.api_storagev1.delete_storage_class(name, body)

        # collect persistent volume claims
        pvc_names = []
        for pvc in kubernetes.api_corev1.list_persistent_volume_claim_for_all_namespaces().items:
            pvc_names.append(pvc.to_dict()["spec"]["volume_name"])
        return pvc_names

    def _scale_up(self, new_slave_count):
        try:
            old_resources = copy.deepcopy(self.cluster.metadata["resources"])
            resources = {}
            resources = self.os.grow(resources=self.cluster.metadata["resources"],
                                     new_slave_count=new_slave_count)
            self.ks.scale(resources)
        except Exception as e:
            logger.exception("Failed to resize cluster: %s" % e)
            if "slaves" in resources:
                if len(resources["slaves"]) != len(old_resources["slaves"]):
                    old_ids = [slave["hostname"] for slave in old_resources["slaves"]]
                    ids = [slave["hostname"] for slave in resources["slaves"]]
                    self.os.shrink(resources=resources,
                                   remove_hostnames=set(ids) - set(old_ids))
                    self.cluster.metadata["resources"] = old_resources
        else:
            self.cluster.metadata["resources"] = resources
            self.cluster.metadata["slave_count"] = new_slave_count
            self.cluster.metadata["node_count"] = new_slave_count + self.cluster.metadata["master_count"]
        finally:
            self.cluster.state = config.CLUSTER_OK_STATE
            self.cluster.save()

    def _scale_down(self, new_slave_count):
        try:
            resources = self.cluster.metadata["resources"]
            remove_hostnames = self.ks.shrink(resources,
                                              new_slave_count=new_slave_count)
            resources = self.os.shrink(resources=resources,
                                       remove_hostnames=remove_hostnames)
        except Exception as e:
            logger.exception("Failed to resize cluster: %s" % e)
        else:
            self.cluster.metadata["resources"] = resources
            self.cluster.metadata["slave_count"] = new_slave_count
            self.cluster.metadata["node_count"] = new_slave_count + self.cluster.metadata["master_count"]
        finally:
            self.cluster.state = config.CLUSTER_OK_STATE
            self.cluster.save()

    def resize(self, node_count):
        logger.info("Resize to %s nodes requested" % node_count)
        # NOTE(sskripnick) kqueen-ui sends node_count as a string
        node_count = int(node_count)
        master_count = len(self.cluster.metadata["resources"]["masters"])
        new_slave_count = node_count - master_count
        if new_slave_count <= 0:
            return False, "There are should be at least one slave node besides master nodes"
        current_slave_count = len(self.cluster.metadata["resources"]["slaves"])
        delta = new_slave_count - current_slave_count

        if delta == 0:
            return False, "Cluster already has %s nodes" % node_count
        self.cluster.state = config.CLUSTER_UPDATING_STATE
        self.cluster.save()
        if delta > 0:
            logger.info("Scaling up %s -> %s slaves" % (current_slave_count, new_slave_count))
            app.executor.submit(self._scale_up, new_slave_count)
            return True, "Resizing started"
        else:
            logger.info("Scaling down %s -> %s slaves" % (current_slave_count, new_slave_count))
            app.executor.submit(self._scale_down, new_slave_count)
            return True, "Resizing started"

    def get_kubeconfig(self):
        return self.cluster.kubeconfig

    def cluster_get(self):
        return {
            "key": self.stack_name,       # (str) this record should be cached under this key if you choose to cache
            "name": self.stack_name,      # (str) name of the cluster in its respective backend
            "id": self.cluster.id,        # (str or UUID) id of `kqueen.models.Cluster` object in KQueen database
            "state": self.cluster.state,  # (str) state of cluster on backend represented by app.config["CLUSTER_[FOO]_STATE"]
            "metadata": {},               # any keys specific for the Provisioner implementation
        }

    def cluster_list(self):
        return []

    @classmethod
    def engine_status(cls, **kwargs):
        try:
            for cmd in ("KS_SSH_KEYGEN_CMD", "KS_SSH_CMD", "KS_ANSIBLE_CMD",
                        "KS_ANSIBLE_PLAYBOOK_CMD"):
                if not os.access(config.get(cmd), os.X_OK):
                    logger.error("Unable to access cluster: '%s' is not properly configured" % cmd)
                    return config.PROVISIONER_ERROR_STATE
            cluster_yml = os.path.join(config.KS_KUBESPRAY_PATH, "cluster.yml")
            if not os.access(cluster_yml, os.R_OK):
                logger.error("KS_KUBESPRAY_PATH is not properly configured")
                return config.PROVISIONER_ERROR_STATE
            OpenStack.connection_status(kwargs)
            return config.PROVISIONER_OK_STATE
        except Exception as e:
            logging.exception("Error engine status: %s", e)
            return config.PROVISIONER_ERROR_STATE


class Kubespray:
    """Kubespray wrapper.

    This approach is not scalable. It may be solved by storing ssh
    keys in db and running ansible on the one of the master nodes.

    :param str cluster_id:
    :param str ssh_username:
    :param str clusters_path:
    :param str kubespray_path:
    :param dict os_kwargs:

    """

    def __init__(self, *, cluster_id, ssh_username,
                 clusters_path, kubespray_path, os_kwargs):
        self.cluster_id = cluster_id
        self.ssh_username = ssh_username
        self.clusters_path = clusters_path
        self.kubespray_path = kubespray_path
        self.os_kwargs = os_kwargs
        self.ssh_common_args = ("-o", "UserKnownHostsFile=/dev/null",
                                "-o", "StrictHostKeyChecking=no",
                                "-i", os.path.join(clusters_path, "ssh_key"))
        self._make_files_dir()

    def deploy(self, resources):
        inventory = self._generate_inventory(resources)
        self._save_inventory(inventory, "hosts.json")
        self._create_group_vars()
        self._wait_for_ping()
        self._add_fip_to_lo(resources)
        self._run_ansible()
        return self._get_kubeconfig(resources["masters"][0]["fip"])

    def _add_fip_to_lo(self, resources):
        """Add floating ip to loopback interface.

        This is workaround for buggy deployments where node can't reach
        itself by floating ip.
        """
        cmd_fmt = (
            "sudo /bin/sh -c 'cat > /etc/rc.local <<EOF\n"
            "/sbin/ip addr add %s/32 scope host dev lo\n"
            "EOF'"
        )
        for master in resources["masters"]:
            ip = master["fip"]
            host = "@".join((self.ssh_username, ip))
            ssh_cmd = ("ssh", host) + self.ssh_common_args
            try:
                subprocess.check_call(ssh_cmd + (cmd_fmt % ip, ))
                subprocess.check_call(ssh_cmd + ("sudo /bin/sh /etc/rc.local", ))
            except subprocess.CalledProcessError as e:
                raise RuntimeError("Enable to add a loopback "
                                   "to make localhost accessible by floating IP. "
                                   "The reason is: {}".format(e))

    def scale(self, resources):
        inventory = self._generate_inventory(resources)
        self._save_inventory(inventory, "hosts.json")
        self._wait_for_ping()
        self._run_ansible(playbook="scale.yml")

    def shrink(self, resources, *, new_slave_count):
        hostnames = [s["hostname"] for s in resources["slaves"]]
        hostnames.sort()
        slaves_left = hostnames[:new_slave_count]
        inv = self._generate_inventory(resources, keep_slaves=slaves_left)
        self._save_inventory(inv, "remove.json")
        self._run_ansible(playbook="remove-node.yml", inventory="remove.json")
        return hostnames[new_slave_count:]

    def delete(self):
        shutil.rmtree(self._get_cluster_path())

    def _save_inventory(self, inventory, filename):
        with open(self._get_cluster_path(filename), "w") as fp:
            json.dump(inventory, fp, indent=4)

    def _create_group_vars(self):
        src = os.path.join(self.kubespray_path, "inventory/sample/group_vars")
        dst = self._get_cluster_path("group_vars")
        shutil.copytree(src, dst)

        with open(os.path.join(dst, "all.yml"), "a") as all_yaml:
            data_to_add = {'cloud_provider': 'openstack'}
            image_var_names = [var_name for var_name in dir(config) if var_name.endswith(('_IMAGE_REPO', '_IMAGE_TAG'))]
            image_variables = {k.lower(): getattr(config, k) for k in image_var_names}
            data_to_add.update(image_variables)

            yaml.dump(data_to_add, all_yaml, default_flow_style=False)

    def _make_files_dir(self):
        os.makedirs(self._get_cluster_path(), exist_ok=True)

    def _generate_inventory(self, resources, keep_slaves=None):
        """Generate inventory object for kubespray.

        :param list keep_slaves: list of slaves to keep when generating
                                 inventory for removing nodes (see link below)
        https://github.com/kubernetes-incubator/kubespray/blob/v2.5.0/docs/getting-started.md#remove-nodes

        :param dict resources: dict with masters and slaves details
        Resources may look like this:
        {
            "masters": [
                {"hostname": "host-1", "ip": "10.1.1.1", "fip": "172.16.1.1"},
                {"hostname": "host-2", "ip": "10.1.1.2", "fip": "172.16.1.2"},
                {"hostname": "host-3", "ip": "10.1.1.3", "fip": "172.16.1.3"},
            ],
            "slaves": [
                {"hostname": "host-4", "ip": "10.1.1.4"},
                {"hostname": "host-5", "ip": "10.1.1.5"},
            ],
        }

        Return value is json serializable object to be used as kubespray
        inventory file.

        """
        keep_slaves = keep_slaves or []
        ssh_common_args = " ".join(self.ssh_common_args)
        conf = {
            "all": {"hosts": {}},
            "kube-master": {
                "hosts": {},
                "vars": {
                    "ansible_ssh_common_args": ssh_common_args
                },
            },
            "kube-node": {"hosts": {}},
            "keep-slaves": {"hosts": {}},
            "etcd": {"hosts": {}},
            "vault": {"hosts": {}},
            "k8s-cluster": {"children": {"kube-node": None,
                                         "kube-master": None}},
        }
        for master in resources["masters"]:
            conf["all"]["hosts"][master["hostname"]] = {
                "access_ip": master["fip"],
                "ansible_host": master["fip"],
                "ansible_user": self.ssh_username,
                "ansible_become": True,
            }
            conf["kube-master"]["hosts"][master["hostname"]] = None
            conf["etcd"]["hosts"][master["hostname"]] = None
            conf["vault"]["hosts"][master["hostname"]] = None
        for slave in resources["slaves"]:
            conf["all"]["hosts"][slave["hostname"]] = {
                "ansible_host": slave["ip"],
                "ansible_user": self.ssh_username,
                "ansible_become": True,
            }
            if slave["hostname"] not in keep_slaves:
                conf["kube-node"]["hosts"][slave["hostname"]] = None

        user = shlex.quote(self.ssh_username)
        ip = shlex.quote(resources["masters"][0]["fip"])
        ssh_args_fmt = "-o ProxyCommand=\"ssh {user}@{ip} {args} -W %h:%p\" {args}"
        ssh_args = ssh_args_fmt.format(user=user, ip=ip,
                                       args=ssh_common_args)
        conf["kube-node"]["vars"] = {"ansible_ssh_common_args": ssh_args}
        conf["keep-slaves"]["vars"] = {"ansible_ssh_common_args": ssh_args}
        return conf

    def _get_cluster_path(self, *args):
        return os.path.join(self.clusters_path, self.cluster_id, *args)

    def _wait_for_ping(self, retries=30, sleep=10):
        args = [config.KS_ANSIBLE_CMD, "-m",
                "ping", "all", "-i", "hosts.json"]
        while retries:
            retries -= 1
            time.sleep(sleep)
            cp = subprocess.run(args, cwd=self._get_cluster_path())
            if cp.returncode == 0:
                return
        raise RuntimeError("At least one node is unreachable")

    def _construct_env(self):
        env = os.environ.copy()
        env.update({
            "OS_PROJECT_ID": self.os_kwargs["project_id"],
            "OS_TENANT_ID": self.os_kwargs["project_id"],
            "OS_REGION_NAME": self.os_kwargs["region_name"],
            "OS_USER_DOMAIN_NAME": self.os_kwargs["domain_name"],
            "OS_PROJECT_NAME": self.os_kwargs["project_id"],
            "OS_PASSWORD": self.os_kwargs["password"],
            "OS_AUTH_URL": self.os_kwargs["auth_url"],
            "OS_USERNAME": self.os_kwargs["username"],
            "OS_INTERFACE": self.os_kwargs["identity_interface"],
        })
        return env

    def _run_ansible(self, inventory="hosts.json", playbook="cluster.yml"):
        inventory = self._get_cluster_path(inventory)
        args = [
            config.KS_ANSIBLE_PLAYBOOK_CMD, "-b", "-i",
            inventory, playbook,
            "--extra-vars", "delete_nodes_confirmation=yes",
            "--extra-vars", "docker_dns_servers_strict=no",
        ]
        env = self._construct_env()
        self.ansible_log = os.path.join(self._get_cluster_path(), "ansible_log_for_{0}_playbook.txt".format(playbook))
        with open(self.ansible_log, "a+") as log_file:
            pipe = subprocess.Popen(
                args,
                stdin=subprocess.DEVNULL,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                cwd=self.kubespray_path,
                env=env,
            )
            pipe.wait()
        if pipe.returncode:
            with open(self.ansible_log, "r") as log_file:
                result = log_file.read()
            if result.find("fatal:"):
                raise RuntimeError("Ansible command execution failed ({})".format(" ".join(args)))

    def _get_kubeconfig(self, ip):
        cat_kubeconf = "sudo cat /etc/kubernetes/admin.conf"
        host = "@".join((self.ssh_username, ip))
        args = ("ssh", host) + self.ssh_common_args + (cat_kubeconf,)
        kubeconfig = yaml.safe_load(subprocess.check_output(args))
        kubeconfig["clusters"][0]["cluster"]["server"] = "https://%s:6443" % ip
        return kubeconfig

    def get_ssh_key(self):
        """Generate ssh keypair if not exist.

        Return public key as string.
        """
        os.makedirs(config.KS_FILES_PATH, exist_ok=True)
        ssh_key_path = os.path.join(config.KS_FILES_PATH, "ssh_key")
        if not os.path.exists(ssh_key_path):
            cmd = [config.KS_SSH_KEYGEN_CMD, "-P", "", "-f", ssh_key_path]
            subprocess.check_call(cmd)
        with open(ssh_key_path + ".pub", "r") as key_file:
            return key_file.read()


class OpenStack:
    """Openstack client wrapper."""

    def __init__(self, stack_name, *, os_kwargs, cluster, extra_ssh_key):
        self.c = OpenStack.get_connection(os_kwargs)
        self.c.authorize()
        self.cluster = cluster
        self.extra_ssh_key = extra_ssh_key
        self.stack_name = stack_name
        self.os_kwargs = os_kwargs
        self.meta = {}

    def validate_cluster_metadata(self):
        def validate_ip(address):
            address = address.strip()
            # Raises ValueError if IP address is not valid
            ipaddress.ip_address(address)
            return address

        mc = self.cluster.metadata["master_count"]
        if mc % 2 == 0:
            raise ValueError("Master node count must be an odd number")
        self.meta["master_count"] = mc
        self.meta["slave_count"] = self.cluster.metadata["slave_count"]
        self.meta["docker_bip_network"] = self.cluster.metadata.get("docker_bip_network", "10.13.0.1/16")

        self.meta["dns"] = [validate_ip(ip) for ip in
                            self.cluster.metadata.get("dns_nameservers", []).split(",")]

        try:
            self.meta["image"] = self.c.get_image(self.cluster.metadata["image_name"])
            if self.meta["image"] is None:
                raise ValueError("Image '%s' is not found" % self.cluster.metadata["image_name"])
            self.meta["master_flavor"] = self.c.get_flavor(self.cluster.metadata["master_flavor"])
            if self.meta["master_flavor"] is None:
                raise ValueError("Flavor for master '%s' is not found" % self.cluster.metadata["master_flavor"])
            self.meta["slave_flavor"] = self.c.get_flavor(self.cluster.metadata["slave_flavor"])
            if self.meta["slave_flavor"] is None:
                raise ValueError("Flavor for slave '%s' is not found" % self.cluster.metadata["master_flavor"])
            # Check that required fields are provided (KeyError is raised if not)
            self.cluster.metadata["ssh_key_name"]
            self.cluster.metadata["ssh_username"]
        except KeyError as e:
            raise ValueError("Required parameter is not set: {}".format(e))

        self.meta["ext_net"] = self.c.get_network(self.cluster.metadata["floating_network"])
        if self.meta["ext_net"] is None:
            raise ValueError("External network '%s' is not found" % self.cluster.metadata["floating_network"])

        azone = self.cluster.metadata.get("availability_zone")
        if azone and azone not in self.c.list_availability_zone_names():
            raise ValueError("Availability zone '{}' is not found".format(self.cluster.metadata["availability_zone"]))
        else:
            self.meta["azone"] = azone

    def provision(self):

        resources = {
            "masters": [],
            "slaves": [],
        }
        network = self.c.create_network(self.stack_name)
        subnet = self.c.create_subnet(network, cidr="10.1.0.0/16",
                                      subnet_name=self.stack_name,
                                      dns_nameservers=self.meta['dns'])
        router = self.c.create_router(name=self.stack_name,
                                      ext_gateway_net_id=self.meta['ext_net'].id)
        self.c.add_router_interface(router, subnet["id"])
        resources["router_id"] = router["id"]
        resources["network_id"] = network["id"]
        resources["subnet_id"] = subnet["id"]
        for master in self._boot_servers(name=self.stack_name,
                                         servers_range=range(self.meta["master_count"]),
                                         image=self.meta['image'],
                                         flavor=self.meta['master_flavor'],
                                         network=network):
            if master.status == 'ERROR':
                raise RuntimeError('Could not spawn the instance with id {0}. Check Openstack logs'.format(master.id))

            fip = self.c.create_floating_ip("public", server=master)
            resources["masters"].append({
                "id": master.id,
                "fip": fip.floating_ip_address,
                "ip": list(master.addresses.values())[0][0]["addr"],
                "floating_ip_id": fip.id,
                "hostname": master.name,
            })
        for slave in self._boot_servers(name=self.stack_name,
                                        servers_range=range(self.meta["slave_count"]),
                                        image=self.meta['image'],
                                        flavor=self.meta['slave_flavor'],
                                        network=network,
                                        add_random_suffix=True):
            if slave.status == 'ERROR':
                raise RuntimeError('Could not spawn the instance with id {0}. Check Openstack logs'.format(slave.id))
            resources["slaves"].append({
                "id": slave.id,
                "ip": list(slave.addresses.values())[0][0]["addr"],
                "hostname": slave.name,
            })
        return resources

    def deprovision(self, volume_names):
        self._cleanup_lbaas()
        server_ids = []
        floating_ips = []
        for server in self.c.list_servers():
            if server.name.startswith(self.stack_name):
                server_ids.append(server.id)
                if server.public_v4:
                    floating_ips.append(server.public_v4)
                self.c.delete_server(server.id)
        router = self.c.get_router(self.stack_name)
        if router is not None:
            for i in self.c.list_router_interfaces(router):
                self.c.remove_router_interface(router, port_id=i.id)
            self.c.delete_router(router.id)
        self.c.delete_network(self.stack_name)
        for sid in server_ids:
            while self.c.get_server(sid):
                time.sleep(5)
        for fip in self.c.list_floating_ips():
            if fip.floating_ip_address in floating_ips:
                logger.info("Deleting floating ip %s" % fip.floating_ip_address)
                self.c.delete_floating_ip(fip.id)
        if volume_names:
            for v in self.c.block_storage.volumes():
                pvc_name = v.metadata.get("kubernetes.io/created-for/pv/name")
                if pvc_name in volume_names:
                    logger.info("Deleting volume %s" % v.id)
                    self.c.delete_volume(v.id, wait=False)

    def grow(self, *, resources, new_slave_count):
        current_slave_count = len(resources["slaves"])
        servers_range = range(current_slave_count, new_slave_count)
        new_slaves = self._boot_servers(
            name=self.stack_name,
            servers_range=servers_range,
            image=self.cluster.metadata["image_name"],
            flavor=self.cluster.metadata["slave_flavor"],
            network=self.c.get_network(resources["network_id"]),
            add_random_suffix=True,
        )
        for slave in new_slaves:
            resources["slaves"].append({
                "id": slave.id,
                "ip": list(slave.addresses.values())[0][0]["addr"],
                "hostname": slave.name,
            })
        return resources

    def shrink(self, *, resources, remove_hostnames):
        slaves = []
        for slave in resources["slaves"]:
            if slave["hostname"] in remove_hostnames:
                self.c.delete_server(slave["id"])
            else:
                slaves.append(slave)
        resources["slaves"] = slaves
        return resources

    def _get_userdata(self):
        docker_bip = {"bip": self.meta["docker_bip_network"]}
        userdata = {
            "manage_etc_hosts": True,
            "package_update": True,
            "packages": ["python"],
            "ssh_authorized_keys": [self.extra_ssh_key],
            "write_files": [
                {
                    "content": json.dumps(docker_bip),
                    "path": "/etc/docker/daemon.json",
                },
            ],
        }
        return "#cloud-config\n" + yaml.dump(userdata)

    def _boot_servers(self, *, name, servers_range, image, flavor, network,
                      add_random_suffix=False):
        server_ids = []
        for i in servers_range:
            hostname = "-".join((name, str(i)))
            if add_random_suffix:
                hostname += "-" + base64.b32encode(os.urandom(10)).decode("ascii").lower()
            server = self.c.create_server(
                name=hostname,
                image=image,
                flavor=flavor,
                userdata=self._get_userdata(),
                network=network,
                availability_zone=self.os_kwargs.get("availability_zone", "nova"),
                key_name=self.cluster.metadata["ssh_key_name"],
            )
            server_ids.append(server.id)
        retries = 50
        while retries:
            retries -= 1
            time.sleep(6)
            for sid in server_ids:
                server = self.c.get_server(sid)
                if server.status == "BUILD":
                    break
            else:
                break
        return [self.c.get_server(sid) for sid in server_ids]

    def get_neutron_client(self):
        from keystoneauth1 import identity
        from keystoneauth1 import session
        from neutronclient.v2_0 import client
        auth = identity.Password(
            auth_url=self.os_kwargs["auth_url"],
            username=self.os_kwargs["username"],
            password=self.os_kwargs["password"],
            user_domain_name=self.os_kwargs["domain_name"],
            project_id=self.os_kwargs["project_id"],
        )
        sess = session.Session(auth=auth)
        neutron = client.Client(session=sess,
                                region_name=self.os_kwargs["region_name"],
                                endpoint_type=self.os_kwargs["identity_interface"])
        return neutron

    def _cleanup_lbaas(self):
        # NOTE(sskripnick) openstacksdk does not support neutron lbaas
        neutron = self.get_neutron_client()
        for n in neutron.list_networks()["networks"]:
            if n["name"] != self.stack_name:
                continue
            for p in neutron.list_ports(network_id=n["id"])["ports"]:
                if p["device_owner"] != "neutron:LOADBALANCERV2":
                    continue
                lb = neutron.show_loadbalancer(p["device_id"])["loadbalancer"]
                for pool in lb["pools"]:
                    # NOTE(sskripnick) use direct call due to bug in delete_pool method
                    neutron.delete("/lbaas/pools/%s" % pool["id"])
                for listener in lb["listeners"]:
                    neutron.delete_listener(listener["id"])
                neutron.delete_loadbalancer(lb["id"])

    @staticmethod
    def get_connection(os_kwargs):
        return openstack.connection.Connection(
            auth_url=os_kwargs["auth_url"],
            project_id=os_kwargs["project_id"],
            username=os_kwargs["username"],
            domain_name=os_kwargs["domain_name"] or None,
            identity_interface=os_kwargs["identity_interface"],
            password=os_kwargs["password"],
        )

    @staticmethod
    def connection_status(os_kwargs):
        c = OpenStack.get_connection(os_kwargs)
        c.authorize()
