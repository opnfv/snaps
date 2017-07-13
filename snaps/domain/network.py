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


class Network:
    """
    SNAPS domain object for interface routers. Should contain attributes that
    are shared amongst cloud providers
    """
    def __init__(self, **kwargs):
        """
        Constructor
        """
        self.name = kwargs.get('name')
        self.id = kwargs.get('id')
        self.type = kwargs.get('provider:network_type')

    def __eq__(self, other):
        return (self.name == other.name and self.id == other.id and
                self.type == other.type)


class Subnet:
    """
    SNAPS domain object for interface routers. Should contain attributes that
    are shared amongst cloud providers
    """
    def __init__(self, **kwargs):
        """
        Constructor
        """
        self.name = kwargs.get('name')
        self.id = kwargs.get('id')
        self.cidr = kwargs.get('cidr')

    def __eq__(self, other):
        return (self.name == other.name and self.id == other.id and
                self.cidr == other.cidr)


class Port:
    """
    SNAPS domain object for ports. Should contain attributes that
    are shared amongst cloud providers
    """
    def __init__(self, **kwargs):
        """
        Constructor
        :param name: the security group's name
        :param id: the security group's id
        :param ips: a list of IP addresses
        """
        self.name = kwargs.get('name')
        self.id = kwargs.get('id')
        self.ips = kwargs.get('ips')
        self.mac_address = kwargs.get('mac_address')
        self.allowed_address_pairs = kwargs.get('allowed_address_pairs')

    def __eq__(self, other):
        return (self.name == other.name and self.id == other.id and
                self.ips == other.ips, self.mac_address == other.mac_address)


class Router:
    """
    SNAPS domain object for routers. Should contain attributes that are shared
    amongst cloud providers
    """
    def __init__(self, **kwargs):
        """
        Constructor
        :param name: the router's name
        :param id: the router's id
        """
        self.name = kwargs.get('name')
        self.id = kwargs.get('id')
        self.status = kwargs.get('status')
        self.tenant_id = kwargs.get('tenant_id')
        self.admin_state_up = kwargs.get('admin_state_up')
        self.external_gateway_info = kwargs.get('external_gateway_info')

    def __eq__(self, other):
        return (self.name == other.name and self.id == other.id and
                self.status == other.status and
                self.tenant_id == other.tenant_id and
                self.admin_state_up == other.admin_state_up and
                self.external_gateway_info == other.external_gateway_info)


class InterfaceRouter:
    """
    SNAPS domain object for interface routers. Should contain attributes that
    are shared amongst cloud providers
    """
    def __init__(self, **kwargs):
        """
        Constructor
        """
        self.id = kwargs.get('id')
        self.subnet_id = kwargs.get('subnet_id')
        self.port_id = kwargs.get('port_id')

    def __eq__(self, other):
        return (self.id == other.id and self.subnet_id == other.subnet_id and
                self.port_id == other.port_id)


class SecurityGroup:
    """
    SNAPS domain object for SecurityGroups. Should contain attributes that
    are shared amongst cloud providers
    """
    def __init__(self, **kwargs):
        """
        Constructor
        :param name: the security group's name
        :param id: the security group's id
        """
        self.name = kwargs.get('name')
        self.id = kwargs.get('id')
        self.project_id = kwargs.get('project_id', kwargs.get('tenant_id'))

    def __eq__(self, other):
        return (self.name == other.name and self.id == other.id and
                self.project_id == other.project_id)


class SecurityGroupRule:
    """
    SNAPS domain object for Security Group Rules. Should contain attributes
    that are shared amongst cloud providers
    """
    def __init__(self, **kwargs):
        """
        Constructor
        :param id: the security group rule's id
        :param sec_grp_id: the ID of the associated security group
        :param description: the security group rule's description
        :param direction: the security group rule's direction
        :param ethertype: the security group rule's ethertype
        :param port_range_min: the security group rule's port_range_min
        :param port_range_max: the security group rule's port_range_max
        :param protocol: the security group rule's protocol
        :param remote_group_id: the security group rule's remote_group_id
        :param remote_ip_prefix: the security group rule's remote_ip_prefix
        """
        self.id = kwargs.get('id')
        self.security_group_id = kwargs.get('security_group_id')
        self.description = kwargs.get('description')
        self.direction = kwargs.get('direction')
        self.ethertype = kwargs.get('ethertype')
        self.port_range_min = kwargs.get('port_range_min')
        self.port_range_max = kwargs.get('port_range_max')
        self.protocol = kwargs.get('protocol')
        self.remote_group_id = kwargs.get('remote_group_id')
        self.remote_ip_prefix = kwargs.get('remote_ip_prefix')

    def __eq__(self, other):
        return (self.id == other.id and
                self.security_group_id == other.security_group_id and
                self.description == other.description and
                self.direction == other.direction and
                self.ethertype == other.ethertype and
                self.port_range_min == other.port_range_min and
                self.port_range_max == other.port_range_max and
                self.protocol == other.protocol and
                self.remote_group_id == other.remote_group_id and
                self.remote_ip_prefix == other.remote_ip_prefix)
