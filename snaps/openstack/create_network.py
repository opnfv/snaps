# Copyright (c) 2017 Cable Television Laboratories, Inc. ("CableLabs")
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
import logging

from neutronclient.common.exceptions import NotFound

from snaps.openstack.utils import keystone_utils, neutron_utils

__author__ = 'spisarski'

logger = logging.getLogger('OpenStackNetwork')


class OpenStackNetwork:
    """
    Class responsible for creating a network in OpenStack
    """

    def __init__(self, os_creds, network_settings):
        """
        Constructor - all parameters are required
        :param os_creds: The credentials to connect with OpenStack
        :param network_settings: The settings used to create a network
        """
        self.__os_creds = os_creds
        self.network_settings = network_settings
        self.__neutron = neutron_utils.neutron_client(self.__os_creds)

        # Attributes instantiated on create()
        self.__network = None
        self.__subnets = list()

    def create(self, cleanup=False):
        """
        Responsible for creating not only the network but then a private subnet, router, and an interface to the router.
        :param cleanup: When true, only perform lookups for OpenStack objects.
        :return: the created network object or None
        """
        try:
            logger.info('Creating neutron network %s...' % self.network_settings.name)
            net_inst = neutron_utils.get_network(self.__neutron, self.network_settings.name,
                                                 self.network_settings.get_project_id(self.__os_creds))
            if net_inst:
                self.__network = net_inst
            else:
                if not cleanup:
                    self.__network = neutron_utils.create_network(self.__neutron, self.__os_creds,
                                                                  self.network_settings)
                else:
                    logger.info('Network does not exist and will not create as in cleanup mode')
                    return
            logger.debug("Network '%s' created successfully" % self.__network['network']['id'])

            logger.debug('Creating Subnets....')
            for subnet_setting in self.network_settings.subnet_settings:
                sub_inst = neutron_utils.get_subnet_by_name(self.__neutron, subnet_setting.name)
                if sub_inst:
                    self.__subnets.append(sub_inst)
                    logger.debug("Subnet '%s' created successfully" % sub_inst['subnet']['id'])
                else:
                    if not cleanup:
                        self.__subnets.append(neutron_utils.create_subnet(self.__neutron, subnet_setting,
                                                                          self.__os_creds, self.__network))

            return self.__network
        except Exception as e:
            logger.error('Unexpected exception thrown while creating network - ' + str(e))
            self.clean()
            raise e

    def clean(self):
        """
        Removes and deletes all items created in reverse order.
        """
        for subnet in self.__subnets:
            try:
                logger.info('Deleting subnet with name ' + subnet['subnet']['name'])
                neutron_utils.delete_subnet(self.__neutron, subnet)
            except NotFound as e:
                logger.warning('Error deleting subnet with message - ' + str(e))
                pass
        self.__subnets = list()

        if self.__network:
            try:
                neutron_utils.delete_network(self.__neutron, self.__network)
            except NotFound:
                pass

            self.__network = None

    def get_network(self):
        """
        Returns the created OpenStack network object
        :return: the OpenStack network object
        """
        return self.__network

    def get_subnets(self):
        """
        Returns the OpenStack subnet objects
        :return:
        """
        return self.__subnets


class NetworkSettings:
    """
    Class representing a network configuration
    """

    def __init__(self, config=None, name=None, admin_state_up=True, shared=None, project_name=None,
                 external=False, network_type=None, physical_network=None, subnet_settings=list()):
        """
        Constructor - all parameters are optional
        :param config: Should be a dict object containing the configuration settings using the attribute names below
                       as each member's the key and overrides any of the other parameters.
        :param name: The network name.
        :param admin_state_up: The administrative status of the network. True = up / False = down (default True)
        :param shared: Boolean value indicating whether this network is shared across all projects/tenants. By default,
                       only administrative users can change this value.
        :param project_name: Admin-only. The name of the project that will own the network. This project can be
                             different from the project that makes the create network request. However, only
                             administrative users can specify a project ID other than their own. You cannot change this
                             value through authorization policies.
        :param external: when true, will setup an external network (default False).
        :param network_type: the type of network (i.e. vlan|flat).
        :param physical_network: the name of the physical network (this is required when network_type is 'flat')
        :param subnet_settings: List of SubnetSettings objects.
        :return:
        """

        self.project_id = None

        if config:
            self.name = config.get('name')
            if config.get('admin_state_up') is not None:
                self.admin_state_up = bool(config['admin_state_up'])
            else:
                self.admin_state_up = admin_state_up

            if config.get('shared') is not None:
                self.shared = bool(config['shared'])
            else:
                self.shared = None

            self.project_name = config.get('project_name')

            if config.get('external') is not None:
                self.external = bool(config.get('external'))
            else:
                self.external = external

            self.network_type = config.get('network_type')
            self.physical_network = config.get('physical_network')

            self.subnet_settings = list()
            if config.get('subnets'):
                for subnet_config in config['subnets']:
                    self.subnet_settings.append(SubnetSettings(config=subnet_config['subnet']))

        else:
            self.name = name
            self.admin_state_up = admin_state_up
            self.shared = shared
            self.project_name = project_name
            self.external = external
            self.network_type = network_type
            self.physical_network = physical_network
            self.subnet_settings = subnet_settings

        if not self.name or len(self.name) < 1:
            raise Exception('Name required for networks')

    def get_project_id(self, os_creds):
        """
        Returns the project ID for a given project_name or None
        :param os_creds: the credentials required for keystone client retrieval
        :return: the ID or None
        """
        if self.project_id:
            return self.project_id
        else:
            if self.project_name:
                keystone = keystone_utils.keystone_client(os_creds)
                project = keystone_utils.get_project(keystone, self.project_name)
                if project:
                    return project.id

        return None

    def dict_for_neutron(self, os_creds):
        """
        Returns a dictionary object representing this object.
        This is meant to be converted into JSON designed for use by the Neutron API

        TODO - expand automated testing to exercise all parameters

        :param os_creds: the OpenStack credentials
        :return: the dictionary object
        """
        out = dict()

        if self.name:
            out['name'] = self.name
        if self.admin_state_up is not None:
            out['admin_state_up'] = self.admin_state_up
        if self.shared:
            out['shared'] = self.shared
        if self.project_name:
            project_id = self.get_project_id(os_creds)
            if project_id:
                out['project_id'] = project_id
            else:
                raise Exception('Could not find project ID for project named - ' + self.project_name)
        if self.network_type:
            out['provider:network_type'] = self.network_type
        if self.physical_network:
            out['provider:physical_network'] = self.physical_network
        if self.external:
            out['router:external'] = self.external
        return {'network': out}


class SubnetSettings:
    """
    Class representing a subnet configuration
    """

    def __init__(self, config=None, cidr=None, ip_version=4, name=None, project_name=None, start=None,
                 end=None, gateway_ip=None, enable_dhcp=None, dns_nameservers=None, host_routes=None, destination=None,
                 nexthop=None, ipv6_ra_mode=None, ipv6_address_mode=None):
        """
        Constructor - all parameters are optional except cidr (subnet mask)
        :param config: Should be a dict object containing the configuration settings using the attribute names below
                       as each member's the key and overrides any of the other parameters.
        :param cidr: The CIDR. REQUIRED if config parameter is None
        :param ip_version: The IP version, which is 4 or 6.
        :param name: The subnet name.
        :param project_name: The name of the project who owns the network. Only administrative users can specify a
                             project ID other than their own. You cannot change this value through authorization
                             policies.
        :param start: The start address for the allocation pools.
        :param end: The end address for the allocation pools.
        :param gateway_ip: The gateway IP address.
        :param enable_dhcp: Set to true if DHCP is enabled and false if DHCP is disabled.
        :param dns_nameservers: A list of DNS name servers for the subnet. Specify each name server as an IP address
                                and separate multiple entries with a space. For example [8.8.8.7 8.8.8.8].
        :param host_routes: A list of host route dictionaries for the subnet. For example:
                                "host_routes":[
                                    {
                                        "destination":"0.0.0.0/0",
                                        "nexthop":"123.456.78.9"
                                    },
                                    {
                                        "destination":"192.168.0.0/24",
                                        "nexthop":"192.168.0.1"
                                    }
                                ]
        :param destination: The destination for static route
        :param nexthop: The next hop for the destination.
        :param ipv6_ra_mode: A valid value is dhcpv6-stateful, dhcpv6-stateless, or slaac.
        :param ipv6_address_mode: A valid value is dhcpv6-stateful, dhcpv6-stateless, or slaac.
        :raise: Exception when config does not have or cidr values are None
        """
        if not dns_nameservers:
            dns_nameservers = ['8.8.8.8']

        if config:
            self.cidr = config['cidr']
            if config.get('ip_version'):
                self.ip_version = config['ip_version']
            else:
                self.ip_version = ip_version

            # Optional attributes that can be set after instantiation
            self.name = config.get('name')
            self.project_name = config.get('project_name')
            self.start = config.get('start')
            self.end = config.get('end')
            self.gateway_ip = config.get('gateway_ip')
            self.enable_dhcp = config.get('enable_dhcp')

            if config.get('dns_nameservers'):
                self.dns_nameservers = config.get('dns_nameservers')
            else:
                self.dns_nameservers = dns_nameservers

            self.host_routes = config.get('host_routes')
            self.destination = config.get('destination')
            self.nexthop = config.get('nexthop')
            self.ipv6_ra_mode = config.get('ipv6_ra_mode')
            self.ipv6_address_mode = config.get('ipv6_address_mode')
        else:
            # Required attributes
            self.cidr = cidr
            self.ip_version = ip_version

            # Optional attributes that can be set after instantiation
            self.name = name
            self.project_name = project_name
            self.start = start
            self.end = end
            self.gateway_ip = gateway_ip
            self.enable_dhcp = enable_dhcp
            self.dns_nameservers = dns_nameservers
            self.host_routes = host_routes
            self.destination = destination
            self.nexthop = nexthop
            self.ipv6_ra_mode = ipv6_ra_mode
            self.ipv6_address_mode = ipv6_address_mode

        if not self.name or not self.cidr:
            raise Exception('Name and cidr required for subnets')

    def dict_for_neutron(self, os_creds, network=None):
        """
        Returns a dictionary object representing this object.
        This is meant to be converted into JSON designed for use by the Neutron API
        :param os_creds: the OpenStack credentials
        :param network: (Optional) the network object on which the subnet will be created
        :return: the dictionary object
        """
        out = {
            'cidr': self.cidr,
            'ip_version': self.ip_version,
        }

        if network:
            out['network_id'] = network['network']['id']
        if self.name:
            out['name'] = self.name
        if self.project_name:
            keystone = keystone_utils.keystone_client(os_creds)
            project = keystone_utils.get_project(keystone, self.project_name)
            project_id = None
            if project:
                project_id = project.id
            if project_id:
                out['project_id'] = project_id
            else:
                raise Exception('Could not find project ID for project named - ' + self.project_name)
        if self.start and self.end:
            out['allocation_pools'] = [{'start': self.start, 'end': self.end}]
        if self.gateway_ip:
            out['gateway_ip'] = self.gateway_ip
        if self.enable_dhcp is not None:
            out['enable_dhcp'] = self.enable_dhcp
        if self.dns_nameservers and len(self.dns_nameservers) > 0:
            out['dns_nameservers'] = self.dns_nameservers
        if self.host_routes and len(self.host_routes) > 0:
            out['host_routes'] = self.host_routes
        if self.destination:
            out['destination'] = self.destination
        if self.nexthop:
            out['nexthop'] = self.nexthop
        if self.ipv6_ra_mode:
            out['ipv6_ra_mode'] = self.ipv6_ra_mode
        if self.ipv6_address_mode:
            out['ipv6_address_mode'] = self.ipv6_address_mode
        return out


class PortSettings:
    """
    Class representing a port configuration
    """

    def __init__(self, config=None, name=None, network_name=None, admin_state_up=True, project_name=None,
                 mac_address=None, ip_addrs=None, fixed_ips=None, security_groups=None, allowed_address_pairs=None,
                 opt_value=None, opt_name=None, device_owner=None, device_id=None):
        """
        Constructor - all parameters are optional
        :param config: Should be a dict object containing the configuration settings using the attribute names below
                       as each member's the key and overrides any of the other parameters.
        :param name: A symbolic name for the port.
        :param network_name: The name of the network on which to create the port.
        :param admin_state_up: A boolean value denoting the administrative status of the port. True = up / False = down
        :param project_name: The name of the project who owns the network. Only administrative users can specify a
                             project ID other than their own. You cannot change this value through authorization
                             policies.
        :param mac_address: The MAC address. If you specify an address that is not valid, a Bad Request (400) status
                            code is returned. If you do not specify a MAC address, OpenStack Networking tries to
                            allocate one. If a failure occurs, a Service Unavailable (503) status code is returned.
        :param ip_addrs: A list of dict objects where each contains two keys 'subnet_name' and 'ip' values which will
                         get mapped to self.fixed_ips.
                         These values will be directly translated into the fixed_ips dict
        :param fixed_ips: A dict where the key is the subnet IDs and value is the IP address to assign to the port
        :param security_groups: One or more security group IDs.
        :param allowed_address_pairs: A dictionary containing a set of zero or more allowed address pairs. An address
                                      pair contains an IP address and MAC address.
        :param opt_value: The extra DHCP option value.
        :param opt_name: The extra DHCP option name.
        :param device_owner: The ID of the entity that uses this port. For example, a DHCP agent.
        :param device_id: The ID of the device that uses this port. For example, a virtual server.
        :return:
        """
        self.network = None

        if config:
            self.name = config.get('name')
            self.network_name = config.get('network_name')

            if config.get('admin_state_up') is not None:
                self.admin_state_up = bool(config['admin_state_up'])
            else:
                self.admin_state_up = admin_state_up

            self.project_name = config.get('project_name')
            self.mac_address = config.get('mac_address')
            self.ip_addrs = config.get('ip_addrs')
            self.fixed_ips = config.get('fixed_ips')
            self.security_groups = config.get('security_groups')
            self.allowed_address_pairs = config.get('allowed_address_pairs')
            self.opt_value = config.get('opt_value')
            self.opt_name = config.get('opt_name')
            self.device_owner = config.get('device_owner')
            self.device_id = config.get('device_id')
        else:
            self.name = name
            self.network_name = network_name
            self.admin_state_up = admin_state_up
            self.project_name = project_name
            self.mac_address = mac_address
            self.ip_addrs = ip_addrs
            self.fixed_ips = fixed_ips
            self.security_groups = security_groups
            self.allowed_address_pairs = allowed_address_pairs
            self.opt_value = opt_value
            self.opt_name = opt_name
            self.device_owner = device_owner
            self.device_id = device_id

        if not self.name or not self.network_name:
            raise Exception('The attributes neutron, name, and network_name are required for PortSettings')

    def __set_fixed_ips(self, neutron):
        """
        Sets the self.fixed_ips value
        :param neutron: the Neutron client
        :return: None
        """
        if not self.fixed_ips and self.ip_addrs:
            self.fixed_ips = list()

            for ip_addr_dict in self.ip_addrs:
                subnet = neutron_utils.get_subnet_by_name(neutron, ip_addr_dict['subnet_name'])
                if subnet:
                    self.fixed_ips.append({'ip_address': ip_addr_dict['ip'], 'subnet_id': subnet['subnet']['id']})
                else:
                    raise Exception('Invalid port configuration, subnet does not exist with name - ' +
                                    ip_addr_dict['subnet_name'])

    def dict_for_neutron(self, neutron, os_creds):
        """
        Returns a dictionary object representing this object.
        This is meant to be converted into JSON designed for use by the Neutron API

        TODO - expand automated testing to exercise all parameters
        :param neutron: the Neutron client
        :param os_creds: the OpenStack credentials
        :return: the dictionary object
        """
        self.__set_fixed_ips(neutron)

        out = dict()

        project_id = None
        if self.project_name:
            keystone = keystone_utils.keystone_client(os_creds)
            project = keystone_utils.get_project(keystone, self.project_name)
            if project:
                project_id = project.id

        if not self.network:
            self.network = neutron_utils.get_network(neutron, self.network_name, project_id)
        if not self.network:
            raise Exception('Cannot locate network with name - ' + self.network_name)

        out['network_id'] = self.network['network']['id']

        if self.admin_state_up is not None:
            out['admin_state_up'] = self.admin_state_up
        if self.name:
            out['name'] = self.name
        if self.project_name:
            if project_id:
                out['project_id'] = project_id
            else:
                raise Exception('Could not find project ID for project named - ' + self.project_name)
        if self.mac_address:
            out['mac_address'] = self.mac_address
        if self.fixed_ips and len(self.fixed_ips) > 0:
            out['fixed_ips'] = self.fixed_ips
        if self.security_groups:
            out['security_groups'] = self.security_groups
        if self.allowed_address_pairs and len(self.allowed_address_pairs) > 0:
            out['allowed_address_pairs'] = self.allowed_address_pairs
        if self.opt_value:
            out['opt_value'] = self.opt_value
        if self.opt_name:
            out['opt_name'] = self.opt_name
        if self.device_owner:
            out['device_owner'] = self.device_owner
        if self.device_id:
            out['device_id'] = self.device_id
        return {'port': out}
