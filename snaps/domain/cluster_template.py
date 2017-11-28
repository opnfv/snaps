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


class ClusterTemplate(object):
    """
    Class for OpenStack cluster template domain object
    """

    def __init__(self, **kwargs):
        """
        Constructor
        :param id: the cluster template's UUID
        :param name: the cluster template's name
        :param image: name or ID of the base image in Glance used to boot the
                      cluster's servers. The image must have the attribute
                      'os-distro' defined as appropriate for the cluster
                      driver
        :param keypair: name or ID of the keypair to gain cluster machine
                        access
        :param network_driver: The name of a network driver for providing the
                               networks for the containers. Note that this is
                               different and separate from the Neutron network
                               for the bay/cluster. The operation and
                               networking model are specific to the particular
                               driver
        :param external_net: name or IDof the external Neutron network to
                             provide connectivity to the cluster
        :param floating_ip_enabled: Whether enable or not using the floating IP
                                    of cloud provider. Some cloud providers
                                    used floating IP, some used public IP,
                                    thus Magnum provide this option for
                                    specifying the choice of using floating IP
        :param docker_volume_size: The size in GB for the local storage on each
                                   server for the Docker daemon to cache the
                                   images and host the containers. Cinder
                                   volumes provide the storage. The default is
                                   25 GB. For the devicemapper storage driver,
                                   the minimum value is 3GB. For the overlay
                                   storage driver, the minimum value is 1GB.
        :param server_type: server type string
        :param flavor: name or ID of the nova flavor for booting the node
                       servers
        :param master_flavor: name or ID of the nova flavor of the master node
                              for this cluster
        :param coe: ContainerOrchestrationEngine enum instance
        :param fixed_net: name of a Neutron network to provide connectivity
                          to the internal network for the cluster
        :param fixed_subnet: Fixed subnet that are using to allocate network
                             address for nodes in bay/cluster
        :param registry_enabled: Docker images by default are pulled from the
                                 public Docker registry, but in some cases,
                                 users may want to use a private registry.
                                 This option provides an alternative registry
                                 based on the Registry V2: Magnum will create a
                                 local registry in the bay/cluster backed by
                                 swift to host the images
        :param insecure_registry: The URL pointing to the user's own private
                                  insecure docker registry to deploy and run
                                  docker containers
        :param docker_storage_driver: DockerStorageDriver enum instance to
                                      manage storage for the images and
                                      container's writable layer
        :param dns_nameserver: The DNS nameserver for the servers and
                               containers in the bay/cluster to use.
                               This is configured in the private Neutron
                               network for the bay/cluster.
        :param public: denotes whether or not the cluster type is public
        :param tls_disabled: denotes whether or not TLS should be enabled
        :param http_proxy: host:port for a proxy to use when direct HTTP
                           access from the servers to sites on the external
                           internet is blocked
        :param https_proxy: host:port for a proxy to use when direct HTTPS
                            access from the servers to sites on the external
                            internet is blocked
        :param no_proxy: comma separated list of IPs that should not be
                         redirected through the proxy
        :param volume_driver: The name of a volume driver for managing the
                              persistent storage for the containers. The
                              functionality supported are specific to the
                              driver
        :param master_lb_enabled: Since multiple masters may exist in a
                                  bay/cluster, a Neutron load balancer is
                                  created to provide the API endpoint for the
                                  bay/cluster and to direct requests to the
                                  masters. In some cases, such as when the
                                  LBaaS service is not available, this option
                                  can be set to false to create a bay/cluster
                                  without the load balancer. In this case, one
                                  of the masters will serve as the API endpoint
        :param labels: Arbitrary labels in the form of a dict. The accepted
                       keys and valid values are defined in the bay/cluster
                       drivers. They are used as a way to pass additional
                       parameters that are specific to a bay/cluster driver.
        """
        self.id = kwargs.get('id')
        self.name = kwargs.get('name')
        self.image = kwargs.get('image')
        self.keypair = kwargs.get('keypair')
        self.network_driver = kwargs.get('network_driver')
        self.external_net = kwargs.get('external_net')
        self.floating_ip_enabled = kwargs.get('floating_ip_enabled')
        self.docker_volume_size = int(kwargs.get('docker_volume_size', 3))
        self.server_type = kwargs.get('server_type')
        self.flavor = kwargs.get('flavor')
        self.master_flavor = kwargs.get('master_flavor')
        self.coe = kwargs.get('coe')
        self.fixed_net = kwargs.get('fixed_net')
        self.fixed_subnet = kwargs.get('fixed_subnet')
        self.registry_enabled = kwargs.get('registry_enabled')
        self.insecure_registry = kwargs.get('insecure_registry')
        self.docker_storage_driver = kwargs.get('docker_storage_driver')
        self.dns_nameserver = kwargs.get('dns_nameserver')
        self.public = kwargs.get('public', False)
        self.tls_disabled = kwargs.get('tls_disabled')
        self.http_proxy = kwargs.get('http_proxy')
        self.https_proxy = kwargs.get('https_proxy')
        self.no_proxy = kwargs.get('no_proxy')
        self.volume_driver = kwargs.get('volume_driver')
        self.master_lb_enabled = kwargs.get('master_lb_enabled', True)
        self.labels = kwargs.get('labels')

    def __eq__(self, other):
        labels_eq = False
        if (self.labels and isinstance(self.labels, dict)
                and len(self.labels) == 0):
            if (other.labels and isinstance(other.labels, dict)
                    and len(other.labels) == 0):
                labels_eq = True
        elif not self.labels:
            if (not other.labels or
                    (isinstance(other.labels, dict)
                     and len(other.labels) == 0)):
                labels_eq = True
        else:
            labels_eq = self.labels == other.labels

        return (self.name == other.name
                and self.id == other.id
                and self.image == other.image
                and self.keypair == other.keypair
                and self.network_driver == other.network_driver
                and self.external_net == other.external_net
                and self.floating_ip_enabled == other.floating_ip_enabled
                and self.docker_volume_size == other.docker_volume_size
                and self.server_type == other.server_type
                and self.flavor == other.flavor
                and self.master_flavor == other.master_flavor
                and self.coe == other.coe
                and self.fixed_net == other.fixed_net
                and self.fixed_subnet == other.fixed_subnet
                and self.registry_enabled == other.registry_enabled
                and self.insecure_registry == other.insecure_registry
                and self.docker_storage_driver == other.docker_storage_driver
                and self.dns_nameserver == other.dns_nameserver
                and self.public == other.public
                and self.tls_disabled == other.tls_disabled
                and self.http_proxy == other.http_proxy
                and self.https_proxy == other.https_proxy
                and self.no_proxy == other.no_proxy
                and self.volume_driver == other.volume_driver
                and self.master_lb_enabled == other.master_lb_enabled
                and labels_eq)
