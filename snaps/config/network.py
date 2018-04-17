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
import enum
from neutronclient.common.utils import str2bool

from snaps.openstack.utils import keystone_utils, neutron_utils


class NetworkConfig(object):
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
                                 (required when network_type is 'flat')
        :param segmentation_id: the id of the segmentation
                                 (this is required when network_type is 'vlan')
        :param subnets or subnet_settings: List of SubnetConfig objects.
        :return:
        """

        self.project_id = None

        self.name = kwargs.get('name')
        if kwargs.get('admin_state_up') is not None:
            self.admin_state_up = str2bool(str(kwargs['admin_state_up']))
        else:
            self.admin_state_up = True

        if kwargs.get('shared') is not None:
            self.shared = str2bool(str(kwargs['shared']))
        else:
            self.shared = None

        self.project_name = kwargs.get('project_name')

        if kwargs.get('external') is not None:
            self.external = str2bool(str(kwargs.get('external')))
        else:
            self.external = False

        self.network_type = kwargs.get('network_type')
        self.physical_network = kwargs.get('physical_network')
        self.segmentation_id = kwargs.get('segmentation_id')

        self.subnet_settings = list()
        subnet_settings = kwargs.get('subnets')
        if not subnet_settings:
            subnet_settings = kwargs.get('subnet_settings', list())
        if subnet_settings:
            for subnet_config in subnet_settings:
                if isinstance(subnet_config, SubnetConfig):
                    self.subnet_settings.append(subnet_config)
                else:
                    self.subnet_settings.append(
                        SubnetConfig(**subnet_config['subnet']))

        if not self.name or len(self.name) < 1:
            raise NetworkConfigError('Name required for networks')

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
                session = keystone_utils.keystone_session(os_creds)
                keystone = keystone_utils.keystone_client(os_creds, session)
                try:
                    project = keystone_utils.get_project(
                        keystone=keystone, project_name=self.project_name)
                    if project:
                        return project.id
                finally:
                    keystone_utils.close_session(session)

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
                raise NetworkConfigError(
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


class NetworkConfigError(Exception):
    """
    Exception to be thrown when networks settings attributes are incorrect
    """


class IPv6Mode(enum.Enum):
    """
    A rule's direction
    """
    slaac = 'slaac'
    stateful = 'dhcpv6-stateful'
    stateless = 'dhcpv6-stateless'


class SubnetConfig(object):
    """
    Class representing a subnet configuration
    """

    def __init__(self, **kwargs):
        """
        Constructor - all parameters are optional except cidr (subnet mask)
        :param name: The subnet name (required)
        :param cidr: The CIDR (required)
        :param ip_version: The IP version, which is 4 or 6 (required)
        :param project_name: The name of the project who owns the network.
                             Only administrative users can specify a project ID
                             other than their own. You cannot change this value
                             through authorization policies (optional)
        :param start: The start address for the allocation pools (optional)
        :param end: The end address for the allocation pools (optional)
        :param gateway_ip: The gateway IP address (optional). When not
                           configured, the IP address will be automatically
                           assigned; when 'none', no gateway address will be
                           assigned, else the value must be valid
        :param enable_dhcp: Set to true if DHCP is enabled and false if DHCP is
                            disabled (optional)
        :param dns_nameservers: A list of DNS name servers for the subnet.
                                Specify each name server as an IP address
                                and separate multiple entries with a space.
                                For example [8.8.8.7 8.8.8.8]
                                (default [])
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
        :param destination: The destination for static route (optional)
        :param nexthop: The next hop for the destination (optional)
        :param ipv6_ra_mode: an instance of the IPv6Mode enum
                             (optional when enable_dhcp is True)
        :param ipv6_address_mode: an instance of the IPv6Mode enum
                                  (optional when enable_dhcp is True)
        :raise: SubnetConfigError when config does not have or cidr values
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

        if 'dns_nameservers' in kwargs:
            self.dns_nameservers = kwargs.get('dns_nameservers')
        else:
            self.dns_nameservers = list()

        self.host_routes = kwargs.get('host_routes')
        self.destination = kwargs.get('destination')
        self.nexthop = kwargs.get('nexthop')
        self.ipv6_ra_mode = map_mode(kwargs.get('ipv6_ra_mode'))
        self.ipv6_address_mode = map_mode(kwargs.get('ipv6_address_mode'))

        if not self.name or not self.cidr:
            raise SubnetConfigError('Name and cidr required for subnets')

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
            session = keystone_utils.keystone_session(os_creds)
            keystone = keystone_utils.keystone_client(os_creds, session)
            try:
                project = keystone_utils.get_project(
                    keystone=keystone, project_name=self.project_name)
            finally:
                keystone_utils.close_session(session)
            project_id = None
            if project:
                project_id = project.id
            if project_id:
                out['tenant_id'] = project_id
            else:
                raise SubnetConfigError(
                    'Could not find project ID for project named - ' +
                    self.project_name)
        if self.start and self.end:
            out['allocation_pools'] = [{'start': self.start, 'end': self.end}]
        if self.gateway_ip:
            if self.gateway_ip == 'none':
                out['gateway_ip'] = None
            else:
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
            out['ipv6_ra_mode'] = self.ipv6_ra_mode.value
        if self.ipv6_address_mode:
            out['ipv6_address_mode'] = self.ipv6_address_mode.value
        return out


def map_mode(mode):
    """
    Takes a the direction value maps it to the Direction enum. When None return
    None
    :param mode: the mode value
    :return: the IPv6Mode enum object
    :raise: SubnetConfigError if value is invalid
    """
    if not mode:
        return None
    if isinstance(mode, IPv6Mode):
        return mode
    elif isinstance(mode, str):
        mode_str = str(mode)
        if mode_str == 'slaac':
            return IPv6Mode.slaac
        elif mode_str == 'dhcpv6-stateful':
            return IPv6Mode.stateful
        elif mode_str == 'stateful':
            return IPv6Mode.stateful
        elif mode_str == 'dhcpv6-stateless':
            return IPv6Mode.stateless
        elif mode_str == 'stateless':
            return IPv6Mode.stateless
        else:
            raise SubnetConfigError('Invalid mode - ' + mode_str)
    else:
        return map_mode(mode.value)


class SubnetConfigError(Exception):
    """
    Exception to be thrown when subnet settings attributes are incorrect
    """


class PortConfig(object):
    """
    Class representing a port configuration
    """

    def __init__(self, **kwargs):
        """
        Constructor
        :param name: A symbolic name for the port (optional).
        :param network_name: The name of the network on which to create the
                             port (required).
        :param admin_state_up: A boolean value denoting the administrative
                               status of the port (default = True)
        :param project_name: The name of the project who owns the network.
                             Only administrative users can specify a project ID
                             other than their own. You cannot change this value
                             through authorization policies (optional)
        :param mac_address: The MAC address. If you specify an address that is
                            not valid, a Bad Request (400) status code is
                            returned. If you do not specify a MAC address,
                            OpenStack Networking tries to allocate one. If a
                            failure occurs, a Service Unavailable (503) status
                            code is returned (optional)
        :param ip_addrs: A list of dict objects where each contains two keys
                         'subnet_name' and 'ip' values which will get mapped to
                         self.fixed_ips. These values will be directly
                         translated into the fixed_ips dict (optional)
        :param security_groups: One or more security group IDs.
        :param port_security_enabled: When True, security groups will be
                                      applied to the port else not
                                      (default - True)
        :param allowed_address_pairs: A dictionary containing a set of zero or
                                      more allowed address pairs. An address
                                      pair contains an IP address and MAC
                                      address (optional)
        :param opt_value: The extra DHCP option value (optional)
        :param opt_name: The extra DHCP option name (optional)
        :param device_owner: The ID of the entity that uses this port.
                             For example, a DHCP agent (optional)
        :param device_id: The ID of the device that uses this port.
                          For example, a virtual server (optional)
        :param extra_dhcp_opts: k/v of options to use with your DHCP (optional)
        :return:
        """
        if 'port' in kwargs:
            kwargs = kwargs['port']

        self.name = kwargs.get('name')
        self.network_name = kwargs.get('network_name')

        if kwargs.get('admin_state_up') is not None:
            self.admin_state_up = str2bool(str(kwargs['admin_state_up']))
        else:
            self.admin_state_up = True

        self.project_name = kwargs.get('project_name')
        self.mac_address = kwargs.get('mac_address')
        self.ip_addrs = kwargs.get('ip_addrs')
        self.security_groups = kwargs.get('security_groups')

        if kwargs.get('port_security_enabled') is not None:
            self.port_security_enabled = str2bool(
                str(kwargs['port_security_enabled']))
        else:
            self.port_security_enabled = None

        self.allowed_address_pairs = kwargs.get('allowed_address_pairs')
        self.opt_value = kwargs.get('opt_value')
        self.opt_name = kwargs.get('opt_name')
        self.device_owner = kwargs.get('device_owner')
        self.device_id = kwargs.get('device_id')
        self.extra_dhcp_opts = kwargs.get('extra_dhcp_opts')

        if not self.network_name:
            raise PortConfigError(
                'The attribute network_name is required')

    def __get_fixed_ips(self, neutron, network):
        """
        Sets the self.fixed_ips value
        :param neutron: the Neutron client
        :param network: the SNAPS-OO network domain object
        :return: None
        """
        fixed_ips = list()
        if self.ip_addrs:

            for ip_addr_dict in self.ip_addrs:
                subnet = neutron_utils.get_subnet(
                    neutron, network, subnet_name=ip_addr_dict['subnet_name'])
                if subnet:
                    if 'ip' in ip_addr_dict:
                        fixed_ips.append({'ip_address': ip_addr_dict['ip'],
                                          'subnet_id': subnet.id})
                else:
                    raise PortConfigError(
                        'Invalid port configuration, subnet does not exist '
                        'with name - ' + ip_addr_dict['subnet_name'])

        return fixed_ips

    def dict_for_neutron(self, neutron, os_creds):
        """
        Returns a dictionary object representing this object.
        This is meant to be converted into JSON designed for use by the Neutron
        API

        TODO - expand automated testing to exercise all parameters
        :param neutron: the Neutron client
        :param keystone: the Keystone client
        :param os_creds: the OpenStack credentials
        :return: the dictionary object
        """
        out = dict()
        session = keystone_utils.keystone_session(os_creds)
        keystone = keystone_utils.keystone_client(os_creds, session)

        project_name = os_creds.project_name
        if self.project_name:
            project_name = project_name
        try:
            network = neutron_utils.get_network(
                neutron, keystone, network_name=self.network_name,
                project_name=project_name)
        finally:
            if session:
                keystone_utils.close_session(session)

        if not network:
            raise PortConfigError(
                'Cannot locate network with name - ' + self.network_name
                + ' in project - ' + str(project_name))

        out['network_id'] = network.id

        if self.admin_state_up is not None:
            out['admin_state_up'] = self.admin_state_up
        if self.name:
            out['name'] = self.name
        if self.project_name:
            project = keystone_utils.get_project(
                keystone=keystone, project_name=self.project_name)
            project_id = None
            if project:
                project_id = project.id
            if project_id:
                out['tenant_id'] = project_id
            else:
                raise PortConfigError(
                    'Could not find project ID for project named - ' +
                    self.project_name)
        if self.mac_address:
            out['mac_address'] = self.mac_address

        fixed_ips = self.__get_fixed_ips(neutron, network)
        if fixed_ips and len(fixed_ips) > 0:
            out['fixed_ips'] = fixed_ips

        if self.security_groups:
            sec_grp_ids = list()
            for sec_grp_name in self.security_groups:
                sec_grp = neutron_utils.get_security_group(
                    neutron, keystone, sec_grp_name=sec_grp_name,
                    project_name=self.project_name)
                if sec_grp:
                    sec_grp_ids.append(sec_grp.id)
            out['security_groups'] = sec_grp_ids
        if self.port_security_enabled is not None:
            out['port_security_enabled'] = self.port_security_enabled
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
        if self.extra_dhcp_opts:
            out['extra_dhcp_opts'] = self.extra_dhcp_opts
        return {'port': out}

    def __eq__(self, other):
        return (self.name == other.name and
                self.network_name == other.network_name and
                self.admin_state_up == other.admin_state_up and
                self.project_name == other.project_name and
                self.mac_address == other.mac_address and
                self.ip_addrs == other.ip_addrs and
                # self.fixed_ips == other.fixed_ips and
                self.security_groups == other.security_groups and
                self.allowed_address_pairs == other.allowed_address_pairs and
                self.opt_value == other.opt_value and
                self.opt_name == other.opt_name and
                self.device_owner == other.device_owner and
                self.device_id == other.device_id)


class PortConfigError(Exception):
    """
    Exception to be thrown when port settings attributes are incorrect
    """
