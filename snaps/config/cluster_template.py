# Copyright (c) 2016 Cable Television Laboratories, Inc. ("CableLabs")
#                    and others.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import enum
from neutronclient.common.utils import str2bool


class ServerType(enum.Enum):
    """
    The cluter server types supported
    """
    vm = 'vm'
    baremetal = 'baremetal'


class ContainerOrchestrationEngine(enum.Enum):
    """
    The types of supported COEs
    """
    kubernetes = 'kubernetes'
    swarm = 'swarm'
    mesos = 'mesos'


class DockerStorageDriver(enum.Enum):
    """
    Drivers for managing storage for the images in the container's writable
    layer
    """
    devicemapper = 'devicemapper'
    overlay = 'overlay'


class ClusterTemplateConfig(object):
    """
    Configuration settings for OpenStack cluster template creation
    """

    def __init__(self, **kwargs):
        """
        Constructor
        :param name: the cluster template's name (required)
        :param image: name or ID of the base image in Glance used to boot the
                      cluster's servers. The image must have the attribute
                      'os-distro' defined as appropriate for the cluster
                      driver (required)
        :param keypair: name or ID of the keypair to gain cluster machine
                        access (required)
        :param network_driver: The name of a network driver for providing the
                               networks for the containers. Note that this is
                               different and separate from the Neutron network
                               for the bay/cluster. The operation and
                               networking model are specific to the particular
                               driver (optional)
        :param external_net: name or IDof the external Neutron network to
                             provide connectivity to the cluster (required)
        :param floating_ip_enabled: Whether enable or not using the floating IP
                                    of cloud provider. Some cloud providers
                                    used floating IP, some used public IP,
                                    thus Magnum provide this option for
                                    specifying the choice of using floating IP
                                    (default - True)
        :param docker_volume_size: The size in GB for the local storage on each
                                   server for the Docker daemon to cache the
                                   images and host the containers. Cinder
                                   volumes provide the storage. The default is
                                   25 GB. For the devicemapper storage driver,
                                   the minimum value is 3GB. For the overlay
                                   storage driver, the minimum value is 1GB.
                                   (default - 3)
        :param server_type: ServerType enumeration (default - vm)
        :param flavor: name or ID of the nova flavor for booting the node
                       servers (default - m1.small)
        :param master_flavor: name or ID of the nova flavor of the master node
                              for this cluster (optional)
        :param coe: ContainerOrchestrationEngine enum instance
                    (default - kubernetes)
        :param fixed_net: name of a Neutron network to provide connectivity
                          to the internal network for the cluster
                          (optional)
        :param fixed_subnet: Fixed subnet that are using to allocate network
                             address for nodes in bay/cluster (optional)
        :param registry_enabled: Docker images by default are pulled from the
                                 public Docker registry, but in some cases,
                                 users may want to use a private registry.
                                 This option provides an alternative registry
                                 based on the Registry V2: Magnum will create a
                                 local registry in the bay/cluster backed by
                                 swift to host the images (default - True)
        :param insecure_registry: The URL pointing to the user's own private
                                  insecure docker registry to deploy and run
                                  docker containers (optional)
        :param docker_storage_driver: DockerStorageDriver enum instance to
                                      manage storage for the images and
                                      container's writable layer
                                      (default - devicemapper)
        :param dns_nameserver: The DNS nameserver for the servers and
                               containers in the bay/cluster to use.
                               This is configured in the private Neutron
                               network for the bay/cluster.
                               (default provided by Magnum - 8.8.8.8)
        :param public: denotes whether or not the cluster template is public
                       (default False)
        :param tls_disabled: denotes whether or not TLS should be enabled
                             (default False)
        :param http_proxy: host:port for a proxy to use when direct HTTP
                           access from the servers to sites on the external
                           internet is blocked (optional)
        :param https_proxy: host:port for a proxy to use when direct HTTPS
                            access from the servers to sites on the external
                            internet is blocked (optional)
        :param no_proxy: comma separated list of IPs that should not be
                         redirected through the proxy (optional)
        :param volume_driver: The name of a volume driver for managing the
                              persistent storage for the containers. The
                              functionality supported are specific to the
                              driver (optional)
        :param master_lb_enabled: Since multiple masters may exist in a
                                  bay/cluster, a Neutron load balancer is
                                  created to provide the API endpoint for the
                                  bay/cluster and to direct requests to the
                                  masters. In some cases, such as when the
                                  LBaaS service is not available, this option
                                  can be set to false to create a bay/cluster
                                  without the load balancer. In this case, one
                                  of the masters will serve as the API endpoint
                                  (default - True)
        :param labels: Arbitrary labels in the form of a dict. The accepted
                       keys and valid values are defined in the bay/cluster
                       drivers. They are used as a way to pass additional
                       parameters that are specific to a bay/cluster driver.
                       (optional)
        """
        self.name = kwargs.get('name')
        self.image = kwargs.get('image')
        self.keypair = kwargs.get('keypair')
        self.network_driver = kwargs.get('network_driver')
        self.external_net = kwargs.get('external_net')
        self.floating_ip_enabled = str2bool(
            str(kwargs.get('floating_ip_enabled', True)))
        self.docker_volume_size = int(kwargs.get('docker_volume_size', 3))
        self.server_type = map_server_type(
            kwargs.get('server_type', ServerType.vm))
        self.flavor = kwargs.get('flavor')
        self.master_flavor = kwargs.get('master_flavor')
        self.coe = map_coe(
            kwargs.get('coe', ContainerOrchestrationEngine.kubernetes))
        self.fixed_net = kwargs.get('fixed_net')
        self.fixed_subnet = kwargs.get('fixed_subnet')
        self.registry_enabled = str2bool(
            str(kwargs.get('registry_enabled', True)))
        self.insecure_registry = kwargs.get('insecure_registry')
        self.docker_storage_driver = map_docker_storage_driver(
            kwargs.get('docker_storage_driver',
                       DockerStorageDriver.devicemapper))
        self.dns_nameserver = kwargs.get('dns_nameserver')
        self.public = str2bool(str(kwargs.get('public', False)))
        self.tls_disabled = str2bool(str(kwargs.get('tls_disabled', False)))
        self.http_proxy = kwargs.get('http_proxy')
        self.https_proxy = kwargs.get('https_proxy')
        self.no_proxy = kwargs.get('no_proxy')
        self.volume_driver = kwargs.get('volume_driver')
        self.master_lb_enabled = str2bool(
            str(kwargs.get('master_lb_enabled', True)))
        self.labels = kwargs.get('labels')

        if (not self.name or not self.image or not self.keypair
                or not self.external_net):
            raise ClusterTemplateConfigError(
                'The attributes name, image, keypair, and '
                'external_net are required for ClusterTemplateConfig')

    def magnum_dict(self):
        """
        Returns a dictionary object representing this object.
        This is meant to be sent into as kwargs into the Magnum client

        :return: the dictionary object
        """
        out = dict()

        if self.name:
            out['name'] = self.name
        if self.image:
            out['image_id'] = self.image
        if self.keypair:
            out['keypair_id'] = self.keypair
        if self.network_driver:
            out['network_driver'] = self.network_driver
        if self.external_net:
            out['external_network_id'] = self.external_net
        if self.floating_ip_enabled:
            out['floating_ip_enabled'] = self.floating_ip_enabled
        if self.docker_volume_size:
            out['docker_volume_size'] = self.docker_volume_size
        if self.server_type:
            out['server_type'] = self.server_type.value
        if self.flavor:
            out['flavor_id'] = self.flavor
        if self.master_flavor:
            out['master_flavor_id'] = self.master_flavor
        if self.coe:
            out['coe'] = self.coe.value
        if self.fixed_net:
            out['fixed_network'] = self.fixed_net
        if self.fixed_subnet:
            out['fixed_subnet'] = self.fixed_subnet
        if self.registry_enabled:
            out['registry_enabled'] = self.registry_enabled
        if self.insecure_registry:
            out['insecure_registry'] = self.insecure_registry
        if self.docker_storage_driver:
            out['docker_storage_driver'] = self.docker_storage_driver.value
        if self.dns_nameserver:
            out['dns_nameserver'] = self.dns_nameserver
        if self.public:
            out['public'] = self.public
        if self.tls_disabled:
            out['tls_disabled'] = self.tls_disabled
        if self.http_proxy:
            out['http_proxy'] = self.http_proxy
        if self.https_proxy:
            out['https_proxy'] = self.https_proxy
        if self.no_proxy:
            out['no_proxy'] = self.no_proxy
        if self.volume_driver:
            out['volume_driver'] = self.volume_driver
        if self.master_lb_enabled:
            out['master_lb_enabled'] = self.master_lb_enabled
        if self.labels:
            out['labels'] = self.labels
        return out


class ClusterTemplateConfigError(Exception):
    """
    Exception to be thrown when a cluster template configuration is incorrect
    """


def map_server_type(server_type):
    """
    Takes a the server_type value maps it to the ServerType enum. When None
    return None
    :param server_type: the server_type value to map
    :return: the ServerType enum object
    :raise: ClusterTemplateConfigError if value is invalid
    """
    if not server_type:
        return None
    if isinstance(server_type, ServerType):
        return server_type
    elif isinstance(server_type, str):
        for this_type in ServerType:
            if this_type.value == server_type:
                return this_type
        raise ClusterTemplateConfigError(
            'Invalid server type - ' + server_type)


def map_coe(coe):
    """
    Takes a the coe value maps it to the ContainerOrchestrationEngine enum.
    When None return None
    :param coe: the COE value to map
    :return: the ContainerOrchestrationEngine enum object
    :raise: ClusterTemplateConfigError if value is invalid
    """
    if not coe:
        return None
    if isinstance(coe, ContainerOrchestrationEngine):
        return coe
    elif isinstance(coe, str):
        for this_type in ContainerOrchestrationEngine:
            if this_type.value == coe:
                return this_type
        raise ClusterTemplateConfigError('Invalid COE - ' + coe)


def map_docker_storage_driver(driver):
    """
    Takes a the coe value maps it to the ContainerOrchestrationEngine enum.
    When None return None
    :param driver: the docker storage driver value to map
    :return: the DockerStorageDriver enum object
    :raise: ClusterTemplateConfigError if value is invalid
    """
    if not driver:
        return None
    if isinstance(driver, DockerStorageDriver):
        return driver
    elif isinstance(driver, str):
        for this_type in DockerStorageDriver:
            if this_type.value == driver:
                return this_type
        raise ClusterTemplateConfigError(
            'Invalid DockerStorageDriver - ' + driver)
