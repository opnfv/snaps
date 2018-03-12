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

from snaps.openstack.utils import keystone_utils, neutron_utils


class SecurityGroupConfig(object):
    """
    Class representing a keypair configuration
    """

    def __init__(self, **kwargs):
        """
        Constructor
        :param name: The security group's name (required)
        :param description: The security group's description (optional)
        :param project_name: The name of the project under which the security
                             group will be created
        :param rule_settings: a list of SecurityGroupRuleConfig objects
        :return:
        """
        self.name = kwargs.get('name')
        self.description = kwargs.get('description')
        self.project_name = kwargs.get('project_name')
        self.rule_settings = list()

        rule_settings = kwargs.get('rules')
        if not rule_settings:
            rule_settings = kwargs.get('rule_settings')

        if rule_settings:
            for rule_setting in rule_settings:
                if isinstance(rule_setting, SecurityGroupRuleConfig):
                    self.rule_settings.append(rule_setting)
                else:
                    rule_setting['sec_grp_name'] = self.name
                    self.rule_settings.append(SecurityGroupRuleConfig(
                        **rule_setting))

        if not self.name:
            raise SecurityGroupConfigError('The attribute name is required')

        for rule_setting in self.rule_settings:
            if rule_setting.sec_grp_name != self.name:
                raise SecurityGroupConfigError(
                    'Rule settings must correspond with the name of this '
                    'security group')

    def dict_for_neutron(self, keystone):
        """
        Returns a dictionary object representing this object.
        This is meant to be converted into JSON designed for use by the Neutron
        API

        TODO - expand automated testing to exercise all parameters
        :param keystone: the Keystone client
        :return: the dictionary object
        """
        out = dict()

        if self.name:
            out['name'] = self.name
        if self.description:
            out['description'] = self.description
        if self.project_name:
            project = keystone_utils.get_project(
                keystone=keystone, project_name=self.project_name)
            project_id = None
            if project:
                project_id = project.id
            if project_id:
                out['tenant_id'] = project_id
            else:
                raise SecurityGroupConfigError(
                    'Could not find project ID for project named - ' +
                    self.project_name)

        return {'security_group': out}


class Direction(enum.Enum):
    """
    A rule's direction
    """
    ingress = 'ingress'
    egress = 'egress'


class Protocol(enum.Enum):
    """
    A rule's protocol
    """
    ah = 51
    dccp = 33
    egp = 8
    esp = 50
    gre = 47
    icmp = 1
    icmpv6 = 58
    igmp = 2
    ipv6_encap = 41
    ipv6_frag = 44
    ipv6_icmp = 58
    ipv6_nonxt = 59
    ipv6_opts = 60
    ipv6_route = 43
    ospf = 89
    pgm = 113
    rsvp = 46
    sctp = 132
    tcp = 6
    udp = 17
    udplite = 136
    vrrp = 112
    any = 'any'
    null = 'null'


class Ethertype(enum.Enum):
    """
    A rule's ethertype
    """
    IPv4 = 4
    IPv6 = 6


class SecurityGroupConfigError(Exception):
    """
    Exception to be thrown when security group settings attributes are
    invalid
    """


class SecurityGroupRuleConfig(object):
    """
    Class representing a keypair configuration
    """

    def __init__(self, **kwargs):
        """
        Constructor - all parameters are optional
        :param sec_grp_name: The security group's name on which to add the
                             rule. (required)
        :param description: The rule's description
        :param direction: An enumeration of type
                          create_security_group.RULE_DIRECTION (required)
        :param remote_group_id: The group ID to associate with this rule
                                (this should be changed to group name once
                                snaps support Groups) (optional)
        :param protocol: An enumeration of type
                         create_security_group.RULE_PROTOCOL or a string value
                         that will be mapped accordingly (optional)
        :param ethertype: An enumeration of type
                          create_security_group.RULE_ETHERTYPE (optional)
        :param port_range_min: The minimum port number in the range that is
                               matched by the security group rule. When the
                               protocol is TCP or UDP, this value must be <=
                               port_range_max.
        :param port_range_max: The maximum port number in the range that is
                               matched by the security group rule. When the
                               protocol is TCP or UDP, this value must be <=
                               port_range_max.
        :param remote_ip_prefix: The remote IP prefix to associate with this
                                 metering rule packet (optional)

        TODO - Need to support the tenant...
        """

        self.description = kwargs.get('description')
        self.sec_grp_name = kwargs.get('sec_grp_name')
        self.remote_group_id = kwargs.get('remote_group_id')
        self.direction = None
        if kwargs.get('direction'):
            self.direction = map_direction(kwargs['direction'])

        self.protocol = None
        if kwargs.get('protocol'):
            self.protocol = map_protocol(kwargs['protocol'])
        else:
            self.protocol = Protocol.null

        self.ethertype = None
        if kwargs.get('ethertype'):
            self.ethertype = map_ethertype(kwargs['ethertype'])

        self.port_range_min = kwargs.get('port_range_min')
        self.port_range_max = kwargs.get('port_range_max')
        self.remote_ip_prefix = kwargs.get('remote_ip_prefix')

        if not self.direction or not self.sec_grp_name:
            raise SecurityGroupRuleConfigError(
                'direction and sec_grp_name are required')

    def dict_for_neutron(self, neutron, keystone, project_name):
        """
        Returns a dictionary object representing this object.
        This is meant to be converted into JSON designed for use by the Neutron
        API
        :param neutron: the neutron client for performing lookups
        :param keystone: the keystone client for performing lookups
        :param project_name: the name of the project associated with the group
        :return: the dictionary object
        """
        out = dict()

        if self.description:
            out['description'] = self.description
        if self.direction:
            out['direction'] = self.direction.name
        if self.port_range_min:
            out['port_range_min'] = self.port_range_min
        if self.port_range_max:
            out['port_range_max'] = self.port_range_max
        if self.ethertype:
            out['ethertype'] = self.ethertype.name
        if self.protocol and self.protocol.value != 'null':
            out['protocol'] = self.protocol.value
        if self.sec_grp_name:
            sec_grp = neutron_utils.get_security_group(
                neutron, keystone, sec_grp_name=self.sec_grp_name,
                project_name=project_name)
            if sec_grp:
                out['security_group_id'] = sec_grp.id
            else:
                raise SecurityGroupRuleConfigError(
                    'Cannot locate security group with name - ' +
                    self.sec_grp_name)
        if self.remote_group_id:
            out['remote_group_id'] = self.remote_group_id
        if self.remote_ip_prefix:
            out['remote_ip_prefix'] = self.remote_ip_prefix

        return {'security_group_rule': out}

    def rule_eq(self, rule):
        """
        Returns True if this setting created the rule
        :param rule: the rule to evaluate
        :return: T/F
        """
        if self.description is not None:
            if rule.description is not None and rule.description != '':
                return False
        elif self.description != rule.description:
            if rule.description != '':
                return False

        if self.direction.name != rule.direction:
            return False

        if self.ethertype and rule.ethertype:
            if self.ethertype.name != rule.ethertype:
                return False

        if self.port_range_min and rule.port_range_min:
            if self.port_range_min != rule.port_range_min:
                return False

        if self.port_range_max and rule.port_range_max:
            if self.port_range_max != rule.port_range_max:
                return False

        if self.protocol and rule.protocol:
            if self.protocol.name != rule.protocol:
                return False

        if self.remote_group_id and rule.remote_group_id:
            if self.remote_group_id != rule.remote_group_id:
                return False

        if self.remote_ip_prefix and rule.remote_ip_prefix:
            if self.remote_ip_prefix != rule.remote_ip_prefix:
                return False

        return True

    def __eq__(self, other):
        return (
            self.description == other.description and
            self.direction == other.direction and
            self.port_range_min == other.port_range_min and
            self.port_range_max == other.port_range_max and
            self.ethertype == other.ethertype and
            self.protocol == other.protocol and
            self.sec_grp_name == other.sec_grp_name and
            self.remote_group_id == other.remote_group_id and
            self.remote_ip_prefix == other.remote_ip_prefix)

    def __hash__(self):
        return hash((self.sec_grp_name, self.description, self.direction,
                     self.remote_group_id,
                     self.protocol, self.ethertype, self.port_range_min,
                     self.port_range_max, self.remote_ip_prefix))


def map_direction(direction):
    """
    Takes a the direction value maps it to the Direction enum. When None return
    None
    :param direction: the direction value
    :return: the Direction enum object
    :raise: Exception if value is invalid
    """
    if not direction or 'None' == str(direction):
        return None
    if isinstance(direction, enum.Enum):
        if direction.__class__.__name__ == 'Direction':
            return direction
        else:
            raise SecurityGroupRuleConfigError(
                'Invalid class - ' + direction.__class__.__name__)
    elif isinstance(direction, str):
        dir_str = str(direction)
        if dir_str == 'egress':
            return Direction.egress
        elif dir_str == 'ingress':
            return Direction.ingress
        else:
            raise SecurityGroupRuleConfigError(
                'Invalid Direction - ' + dir_str)
    else:
        return map_direction(str(direction))


def map_protocol(protocol):
    """
    Takes a the protocol value maps it to the Protocol enum. When None return
    None
    :param protocol: the protocol value
    :return: the Protocol enum object
    :raise: Exception if value is invalid
    """
    if not protocol:
        return None
    elif isinstance(protocol, enum.Enum):
        if protocol.__class__.__name__ == 'Protocol':
            return protocol
        else:
            raise SecurityGroupRuleConfigError(
                'Invalid class - ' + protocol.__class__.__name__)
    elif isinstance(protocol, str) or isinstance(protocol, int):
        for proto_enum in Protocol:
            if proto_enum.name == protocol or proto_enum.value == protocol:
                if proto_enum == Protocol.any:
                    return Protocol.null
                return proto_enum
        raise SecurityGroupRuleConfigError(
            'Invalid Protocol - ' + str(protocol))
    else:
        return map_protocol(str(protocol))


def map_ethertype(ethertype):
    """
    Takes a the ethertype value maps it to the Ethertype enum. When None return
    None
    :param ethertype: the ethertype value
    :return: the Ethertype enum object
    :raise: Exception if value is invalid
    """
    if not ethertype or 'None' == str(ethertype):
        return None
    elif isinstance(ethertype, enum.Enum):
        if ethertype.__class__.__name__ == 'Ethertype':
            return ethertype
        else:
            raise SecurityGroupRuleConfigError(
                'Invalid class - ' + ethertype.__class__.__name__)
    elif isinstance(ethertype, str) or isinstance(ethertype, int):
        eth_str = str(ethertype)
        if eth_str == 'IPv6' or eth_str == '6':
            return Ethertype.IPv6
        elif eth_str == 'IPv4' or eth_str == '4':
            return Ethertype.IPv4
        else:
            raise SecurityGroupRuleConfigError(
                'Invalid Ethertype - ' + eth_str)
    else:
        return map_ethertype(str(ethertype))


class SecurityGroupRuleConfigError(Exception):
    """
    Exception to be thrown when security group rule settings attributes are
    invalid
    """
