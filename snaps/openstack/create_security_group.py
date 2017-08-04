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

import enum
from neutronclient.common.exceptions import NotFound
from snaps.openstack.utils import keystone_utils
from snaps.openstack.utils import neutron_utils

__author__ = 'spisarski'

logger = logging.getLogger('OpenStackSecurityGroup')


class OpenStackSecurityGroup:
    """
    Class responsible for creating Security Groups
    """

    def __init__(self, os_creds, sec_grp_settings):
        """
        Constructor - all parameters are required
        :param os_creds: The credentials to connect with OpenStack
        :param sec_grp_settings: The settings used to create a security group
        """
        self.__os_creds = os_creds
        self.sec_grp_settings = sec_grp_settings
        self.__neutron = None
        self.__keystone = None

        # Attributes instantiated on create()
        self.__security_group = None

        # dict where the rule settings object is the key
        self.__rules = dict()

    def create(self, cleanup=False):
        """
        Responsible for creating the security group.
        :param cleanup: Denotes whether or not this is being called for cleanup
        :return: the OpenStack security group object
        """
        self.__neutron = neutron_utils.neutron_client(self.__os_creds)
        self.__keystone = keystone_utils.keystone_client(self.__os_creds)

        logger.info(
            'Creating security group %s...' % self.sec_grp_settings.name)

        self.__security_group = neutron_utils.get_security_group(
            self.__neutron, sec_grp_settings=self.sec_grp_settings)
        if not self.__security_group and not cleanup:
            # Create the security group
            self.__security_group = neutron_utils.create_security_group(
                self.__neutron, self.__keystone,
                self.sec_grp_settings)

            # Get the rules added for free
            auto_rules = neutron_utils.get_rules_by_security_group(
                self.__neutron, self.__security_group)

            ctr = 0
            for auto_rule in auto_rules:
                auto_rule_setting = self.__generate_rule_setting(auto_rule)
                self.__rules[auto_rule_setting] = auto_rule
                ctr += 1

            # Create the custom rules
            for sec_grp_rule_setting in self.sec_grp_settings.rule_settings:
                custom_rule = neutron_utils.create_security_group_rule(
                    self.__neutron, sec_grp_rule_setting)
                self.__rules[sec_grp_rule_setting] = custom_rule

            # Refresh security group object to reflect the new rules added
            self.__security_group = neutron_utils.get_security_group(
                self.__neutron, sec_grp_settings=self.sec_grp_settings)
        else:
            # Populate rules
            existing_rules = neutron_utils.get_rules_by_security_group(
                self.__neutron, self.__security_group)

            for existing_rule in existing_rules:
                # For Custom Rules
                rule_setting = self.__get_setting_from_rule(existing_rule)
                ctr = 0
                if not rule_setting:
                    # For Free Rules
                    rule_setting = self.__generate_rule_setting(existing_rule)
                    ctr += 1

                self.__rules[rule_setting] = existing_rule

        return self.__security_group

    def __generate_rule_setting(self, rule):
        """
        Creates a SecurityGroupRuleSettings object for a given rule
        :param rule: the rule from which to create the
                    SecurityGroupRuleSettings object
        :return: the newly instantiated SecurityGroupRuleSettings object
        """
        sec_grp = neutron_utils.get_security_group_by_id(
            self.__neutron, rule.security_group_id)

        setting = SecurityGroupRuleSettings(
            description=rule.description,
            direction=rule.direction,
            ethertype=rule.ethertype,
            port_range_min=rule.port_range_min,
            port_range_max=rule.port_range_max,
            protocol=rule.protocol,
            remote_group_id=rule.remote_group_id,
            remote_ip_prefix=rule.remote_ip_prefix,
            sec_grp_name=sec_grp.name)
        return setting

    def clean(self):
        """
        Removes and deletes the rules then the security group.
        """
        for setting, rule in self.__rules.items():
            try:
                neutron_utils.delete_security_group_rule(self.__neutron, rule)
            except NotFound as e:
                logger.warning('Rule not found, cannot delete - ' + str(e))
                pass
        self.__rules = dict()

        if self.__security_group:
            try:
                neutron_utils.delete_security_group(self.__neutron,
                                                    self.__security_group)
            except NotFound as e:
                logger.warning(
                    'Security Group not found, cannot delete - ' + str(e))

            self.__security_group = None

    def get_security_group(self):
        """
        Returns the OpenStack security group object
        :return:
        """
        return self.__security_group

    def get_rules(self):
        """
        Returns the associated rules
        :return:
        """
        return self.__rules

    def add_rule(self, rule_setting):
        """
        Adds a rule to this security group
        :param rule_setting: the rule configuration
        """
        rule_setting.sec_grp_name = self.sec_grp_settings.name
        new_rule = neutron_utils.create_security_group_rule(self.__neutron,
                                                            rule_setting)
        self.__rules[rule_setting] = new_rule
        self.sec_grp_settings.rule_settings.append(rule_setting)

    def remove_rule(self, rule_id=None, rule_setting=None):
        """
        Removes a rule to this security group by id, name, or rule_setting
        object
        :param rule_id: the rule's id
        :param rule_setting: the rule's setting object
        """
        rule_to_remove = None
        if rule_id or rule_setting:
            if rule_id:
                rule_to_remove = neutron_utils.get_rule_by_id(
                    self.__neutron, self.__security_group, rule_id)
            elif rule_setting:
                rule_to_remove = self.__rules.get(rule_setting)

        if rule_to_remove:
            neutron_utils.delete_security_group_rule(self.__neutron,
                                                     rule_to_remove)
            rule_setting = self.__get_setting_from_rule(rule_to_remove)
            if rule_setting:
                self.__rules.pop(rule_setting)
            else:
                logger.warning('Rule setting is None, cannot remove rule')

    def __get_setting_from_rule(self, rule):
        """
        Returns the associated RuleSetting object for a given rule
        :param rule: the Rule object
        :return: the associated RuleSetting object or None
        """
        for rule_setting in self.sec_grp_settings.rule_settings:
            if rule_setting.rule_eq(rule):
                return rule_setting
        return None


class SecurityGroupSettings:
    """
    Class representing a keypair configuration
    """

    def __init__(self, **kwargs):
        """
        Constructor - all parameters are optional
        :param name: The keypair name.
        :param description: The security group's description
        :param project_name: The name of the project under which the security
                             group will be created
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
                if isinstance(rule_setting, SecurityGroupRuleSettings):
                    self.rule_settings.append(rule_setting)
                else:
                    self.rule_settings.append(SecurityGroupRuleSettings(
                        **rule_setting))

        if not self.name:
            raise SecurityGroupSettingsError('The attribute name is required')

        for rule_setting in self.rule_settings:
            if rule_setting.sec_grp_name is not self.name:
                raise SecurityGroupSettingsError(
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
                raise SecurityGroupSettingsError(
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
    icmp = 'icmp'
    tcp = 'tcp'
    udp = 'udp'
    null = 'null'


class Ethertype(enum.Enum):
    """
    A rule's ethertype
    """
    IPv4 = 4
    IPv6 = 6


class SecurityGroupSettingsError(Exception):
    """
    Exception to be thrown when security group settings attributes are
    invalid
    """


class SecurityGroupRuleSettings:
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
                               port_range_max. When the protocol is ICMP, this
                               value must be an ICMP type.
        :param port_range_max: The maximum port number in the range that is
                               matched by the security group rule. When the
                               protocol is TCP or UDP, this value must be <=
                               port_range_max. When the protocol is ICMP, this
                               value must be an ICMP type.
        :param sec_grp_rule: The OpenStack rule object to a security group rule
                             object to associate
                             (note: Cannot be set using the config object nor
                             can I see any real uses for this parameter)
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
            raise SecurityGroupRuleSettingsError(
                'direction and sec_grp_name are required')

    def dict_for_neutron(self, neutron):
        """
        Returns a dictionary object representing this object.
        This is meant to be converted into JSON designed for use by the Neutron
        API

        :param neutron: the neutron client for performing lookups
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
        if self.protocol and self.protocol.name != 'null':
            out['protocol'] = self.protocol.name
        if self.sec_grp_name:
            sec_grp = neutron_utils.get_security_group(
                neutron, sec_grp_name=self.sec_grp_name)
            if sec_grp:
                out['security_group_id'] = sec_grp.id
            else:
                raise SecurityGroupRuleSettingsError(
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
            if (rule.description is not None and
                    rule.description != ''):
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
    if not direction:
        return None
    if isinstance(direction, Direction):
        return direction
    else:
        dir_str = str(direction)
        if dir_str == 'egress':
            return Direction.egress
        elif dir_str == 'ingress':
            return Direction.ingress
        else:
            raise SecurityGroupRuleSettingsError(
                'Invalid Direction - ' + dir_str)


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
    elif isinstance(protocol, Protocol):
        return protocol
    else:
        proto_str = str(protocol)
        if proto_str == 'icmp':
            return Protocol.icmp
        elif proto_str == 'tcp':
            return Protocol.tcp
        elif proto_str == 'udp':
            return Protocol.udp
        elif proto_str == 'null':
            return Protocol.null
        else:
            raise SecurityGroupRuleSettingsError(
                'Invalid Protocol - ' + proto_str)


def map_ethertype(ethertype):
    """
    Takes a the ethertype value maps it to the Ethertype enum. When None return
    None
    :param ethertype: the ethertype value
    :return: the Ethertype enum object
    :raise: Exception if value is invalid
    """
    if not ethertype:
        return None
    elif isinstance(ethertype, Ethertype):
        return ethertype
    else:
        eth_str = str(ethertype)
        if eth_str == 'IPv6':
            return Ethertype.IPv6
        elif eth_str == 'IPv4':
            return Ethertype.IPv4
        else:
            raise SecurityGroupRuleSettingsError(
                'Invalid Ethertype - ' + eth_str)


class SecurityGroupRuleSettingsError(Exception):
    """
    Exception to be thrown when security group rule settings attributes are
    invalid
    """
