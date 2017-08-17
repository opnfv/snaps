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
        self.__neutron = None

        # Attributes instantiated on create()
        self.__network = None
        self.__subnets = list()

    def create(self, cleanup=False):
        """
        Responsible for creating not only the network but then a private
        subnet, router, and an interface to the router.
        :param cleanup: When true, only perform lookups for OpenStack objects.
        :return: the created network object or None
        """
        self.__neutron = neutron_utils.neutron_client(self.__os_creds)

        logger.info(
            'Creating neutron network %s...' % self.network_settings.name)
        net_inst = neutron_utils.get_network(
            self.__neutron, network_settings=self.network_settings,
            project_id=self.network_settings.get_project_id(self.__os_creds))
        if net_inst:
            self.__network = net_inst
        else:
            if not cleanup:
                self.__network = neutron_utils.create_network(
                    self.__neutron, self.__os_creds, self.network_settings)
            else:
                logger.info(
                    'Network does not exist and will not create as in cleanup'
                    ' mode')
                return
        logger.debug(
            "Network '%s' created successfully" % self.__network.id)

        logger.debug('Creating Subnets....')
        for subnet_setting in self.network_settings.subnet_settings:
            sub_inst = neutron_utils.get_subnet(
                self.__neutron, subnet_settings=subnet_setting)
            if sub_inst:
                self.__subnets.append(sub_inst)
                logger.debug(
                    "Subnet '%s' created successfully" % sub_inst.id)
            else:
                if not cleanup:
                    self.__subnets.append(
                        neutron_utils.create_subnet(
                            self.__neutron, subnet_setting, self.__os_creds,
                            self.__network))

        return self.__network

    def clean(self):
        """
        Removes and deletes all items created in reverse order.
        """
        for subnet in self.__subnets:
            try:
                logger.info(
                    'Deleting subnet with name ' + subnet.name)
                neutron_utils.delete_subnet(self.__neutron, subnet)
            except NotFound as e:
                logger.warning(
                    'Error deleting subnet with message - ' + str(e))
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

    def __init__(self, **kwargs):
        """
        Constructor - all parameters are optional
        :param name: The network name.
        :param admin_state_up: The administrative status of the network.
                               True = up / False = down (default True)
        :param shared: Boolean value indicating whether this network is shared
                       across all projects/tenants. By default, only
                       administrative users can change this value.
        :param project_name: Admin-only. The name of the project that will own
                             the network. This project can be different from
                             the project that makes the create network request.
                             However, only administrative users can specify a
                             project ID other than their own. You cannot change
                             this value through authorization policies.
        :param external: when true, will setup an external network
                         (default False).
        :param network_type: the type of network (i.e. vlan|flat).
        :param physical_network: the name of the physical network
                                 (this is required when network_type is 'flat')
        :param segmentation_id: the id of the segmentation
                                 (this is required when network_type is 'vlan')
        :param subnets or subnet_settings: List of SubnetSettings objects.
        :return:
        """

        self.project_id = None

        self.name = kwargs.get('name')
        if kwargs.get('admin_state_up') is not None:
            self.admin_state_up = bool(kwargs['admin_state_up'])
        else:
            self.admin_state_up = True

        if kwargs.get('shared') is not None:
            self.shared = bool(kwargs['shared'])
        else:
            self.shared = None

        self.project_name = kwargs.get('project_name')

        if kwargs.get('external') is not None:
            self.external = bool(kwargs.get('external'))
        else:
            self.external = False

        self.network_type = kwargs.get('network_type')
        self.physical_network = kwargs.get('physical_network')
        self.segmentation_id = kwargs.get('segmentation_id')

        self.subnet_settings = list()
        subnet_settings = kwargs.get('subnets')
        if not subnet_settings:
            subnet_settings = kwargs.get('subnet_settings')
        if subnet_settings:
            for subnet_config in subnet_settings:
                if isinstance(subnet_config, SubnetSettings):
                    self.subnet_settings.append(subnet_config)
                else:
                    self.subnet_settings.append(
                        SubnetSettings(**subnet_config['subnet']))

        if not self.name or len(self.name) < 1:
            raise NetworkSettingsError('Name required for networks')

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
                project = keystone_utils.get_project(
                    keystone=keystone, project_name=self.project_name)
                if project:
                    return project.id

        return None

    def dict_for_neutron(self, os_creds):
        """
        Returns a dictionary object representing this object.
        This is meant to be converted into JSON designed for use by the Neutron
        API
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
                out['tenant_id'] = project_id
            else:
                raise NetworkSettingsError(
                    'Could not find project ID for project named - ' +
                    self.project_name)
        if self.network_type:
            out['provider:network_type'] = self.network_type
        if self.physical_network:
            out['provider:physical_network'] = self.physical_network
        if self.segmentation_id:
            out['provider:segmentation_id'] = self.segmentation_id
        if self.external:
            out['router:external'] = self.external
        return {'network': out}


class NetworkSettingsError(Exception):
    """
    Exception to be thrown when networks settings attributes are incorrect
    """


class SubnetSettings:
    """
    Class representing a subnet configuration
    """

    def __init__(self, **kwargs):
        """
        Constructor - all parameters are optional except cidr (subnet mask)
        :param cidr: The CIDR. REQUIRED if config parameter is None
        :param ip_version: The IP version, which is 4 or 6.
        :param name: The subnet name.
        :param project_name: The name of the project who owns the network.
                             Only administrative users can specify a project ID
                             other than their own. You cannot change this value
                             through authorization policies.
        :param start: The start address for the allocation pools.
        :param end: The end address for the allocation pools.
        :param gateway_ip: The gateway IP address.
        :param enable_dhcp: Set to true if DHCP is enabled and false if DHCP is
                            disabled.
        :param dns_nameservers: A list of DNS name servers for the subnet.
                                Specify each name server as an IP address
                                and separate multiple entries with a space.
                                For example [8.8.8.7 8.8.8.8].
        :param host_routes: A list of host route dictionaries for the subnet.
                            For example:
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
        :param ipv6_ra_mode: A valid value is dhcpv6-stateful,
                             dhcpv6-stateless, or slaac.
        :param ipv6_address_mode: A valid value is dhcpv6-stateful,
                                  dhcpv6-stateless, or slaac.
        :raise: SubnetSettingsError when config does not have or cidr values
                are None
        """
        self.cidr = kwargs.get('cidr')
        if kwargs.get('ip_version'):
            self.ip_version = kwargs['ip_version']
        else:
            self.ip_version = 4

        # Optional attributes that can be set after instantiation
        self.name = kwargs.get('name')
        self.project_name = kwargs.get('project_name')
        self.start = kwargs.get('start')
        self.end = kwargs.get('end')
        self.gateway_ip = kwargs.get('gateway_ip')
        self.enable_dhcp = kwargs.get('enable_dhcp')

        if kwargs.get('dns_nameservers'):
            self.dns_nameservers = kwargs.get('dns_nameservers')
        else:
            self.dns_nameservers = ['8.8.8.8']

        self.host_routes = kwargs.get('host_routes')
        self.destination = kwargs.get('destination')
        self.nexthop = kwargs.get('nexthop')
        self.ipv6_ra_mode = kwargs.get('ipv6_ra_mode')
        self.ipv6_address_mode = kwargs.get('ipv6_address_mode')

        if not self.name or not self.cidr:
            raise SubnetSettingsError('Name and cidr required for subnets')

    def dict_for_neutron(self, os_creds, network=None):
        """
        Returns a dictionary object representing this object.
        This is meant to be converted into JSON designed for use by the Neutron
        API
        :param os_creds: the OpenStack credentials
        :param network: The network object on which the subnet will be created
                        (optional)
        :return: the dictionary object
        """
        out = {
            'cidr': self.cidr,
            'ip_version': self.ip_version,
        }

        if network:
            out['network_id'] = network.id
        if self.name:
            out['name'] = self.name
        if self.project_name:
            keystone = keystone_utils.keystone_client(os_creds)
            project = keystone_utils.get_project(
                keystone=keystone, project_name=self.project_name)
            project_id = None
            if project:
                project_id = project.id
            if project_id:
                out['tenant_id'] = project_id
            else:
                raise SubnetSettingsError(
                    'Could not find project ID for project named - ' +
                    self.project_name)
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


class SubnetSettingsError(Exception):
    """
    Exception to be thrown when subnet settings attributes are incorrect
    """


class PortSettings:
    """
    Class representing a port configuration
    """

    def __init__(self, **kwargs):
        """
        Constructor - all parameters are optional
        :param name: A symbolic name for the port.
        :param network_name: The name of the network on which to create the
                             port.
        :param admin_state_up: A boolean value denoting the administrative
                               status of the port. True = up / False = down
        :param project_name: The name of the project who owns the network.
                             Only administrative users can specify a project ID
                             other than their own. You cannot change this value
                             through authorization policies.
        :param mac_address: The MAC address. If you specify an address that is
                            not valid, a Bad Request (400) status code is
                            returned. If you do not specify a MAC address,
                            OpenStack Networking tries to allocate one. If a
                            failure occurs, a Service Unavailable (503) status
                            code is returned.
        :param ip_addrs: A list of dict objects where each contains two keys
                         'subnet_name' and 'ip' values which will get mapped to
                         self.fixed_ips. These values will be directly
                         translated into the fixed_ips dict
        :param fixed_ips: A dict where the key is the subnet IDs and value is
                          the IP address to assign to the port
        :param security_groups: One or more security group IDs.
        :param allowed_address_pairs: A dictionary containing a set of zero or
                                      more allowed address pairs. An address
                                      pair contains an IP address and MAC
                                      address.
        :param opt_value: The extra DHCP option value.
        :param opt_name: The extra DHCP option name.
        :param device_owner: The ID of the entity that uses this port.
                             For example, a DHCP agent.
        :param device_id: The ID of the device that uses this port.
                          For example, a virtual server.
        :return:
        """
        if 'port' in kwargs:
            kwargs = kwargs['port']

        self.network = None

        self.name = kwargs.get('name')
        self.network_name = kwargs.get('network_name')

        if kwargs.get('admin_state_up') is not None:
            self.admin_state_up = bool(kwargs['admin_state_up'])
        else:
            self.admin_state_up = True

        self.project_name = kwargs.get('project_name')
        self.mac_address = kwargs.get('mac_address')
        self.ip_addrs = kwargs.get('ip_addrs')
        self.fixed_ips = kwargs.get('fixed_ips')
        self.security_groups = kwargs.get('security_groups')
        self.allowed_address_pairs = kwargs.get('allowed_address_pairs')
        self.opt_value = kwargs.get('opt_value')
        self.opt_name = kwargs.get('opt_name')
        self.device_owner = kwargs.get('device_owner')
        self.device_id = kwargs.get('device_id')

        if not self.name or not self.network_name:
            raise PortSettingsError(
                'The attributes neutron, name, and network_name are required '
                'for PortSettings')

    def __set_fixed_ips(self, neutron):
        """
        Sets the self.fixed_ips value
        :param neutron: the Neutron client
        :return: None
        """
        if not self.fixed_ips and self.ip_addrs:
            self.fixed_ips = list()

            for ip_addr_dict in self.ip_addrs:
                subnet = neutron_utils.get_subnet(
                    neutron, subnet_name=ip_addr_dict['subnet_name'])
                if subnet and 'ip' in ip_addr_dict:
                    self.fixed_ips.append({'ip_address': ip_addr_dict['ip'],
                                           'subnet_id': subnet.id})
                else:
                    raise PortSettingsError(
                        'Invalid port configuration, subnet does not exist '
                        'with name - ' + ip_addr_dict['subnet_name'])

    def dict_for_neutron(self, neutron, os_creds):
        """
        Returns a dictionary object representing this object.
        This is meant to be converted into JSON designed for use by the Neutron
        API

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
            project = keystone_utils.get_project(
                keystone=keystone, project_name=self.project_name)
            if project:
                project_id = project.id

        if not self.network:
            self.network = neutron_utils.get_network(
                neutron, network_name=self.network_name, project_id=project_id)
        if not self.network:
            raise PortSettingsError(
                'Cannot locate network with name - ' + self.network_name)

        out['network_id'] = self.network.id

        if self.admin_state_up is not None:
            out['admin_state_up'] = self.admin_state_up
        if self.name:
            out['name'] = self.name
        if self.project_name:
            if project_id:
                out['tenant_id'] = project_id
            else:
                raise PortSettingsError(
                    'Could not find project ID for project named - ' +
                    self.project_name)
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

    def __eq__(self, other):
        return (self.name == other.name and
                self.network_name == other.network_name and
                self.admin_state_up == other.admin_state_up and
                self.project_name == other.project_name and
                self.mac_address == other.mac_address and
                self.ip_addrs == other.ip_addrs and
                self.fixed_ips == other.fixed_ips and
                self.security_groups == other.security_groups and
                self.allowed_address_pairs == other.allowed_address_pairs and
                self.opt_value == other.opt_value and
                self.opt_name == other.opt_name and
                self.device_owner == other.device_owner and
                self.device_id == other.device_id)


class PortSettingsError(Exception):
    """
    Exception to be thrown when port settings attributes are incorrect
    """
