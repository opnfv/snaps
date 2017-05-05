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
from snaps.openstack.utils import neutron_utils
from snaps.openstack.utils import keystone_utils

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
        self.__neutron = neutron_utils.neutron_client(os_creds)
        self.__keystone = keystone_utils.keystone_client(os_creds)

        # Attributes instantiated on create()
        self.__security_group = None

        # dict where the rule settings object is the key
        self.__rules = dict()

    def create(self, cleanup=False):
        """
        Responsible for creating the security group.
        :param cleanup: Denotes whether or not this is being called for cleanup or not
        :return: the OpenStack security group object
        """
        logger.info('Creating security group %s...' % self.sec_grp_settings.name)

        self.__security_group = neutron_utils.get_security_group(self.__neutron, self.sec_grp_settings.name)
        if not self.__security_group and not cleanup:
            # Create the security group
            self.__security_group = neutron_utils.create_security_group(self.__neutron, self.__keystone,
                                                                        self.sec_grp_settings)

            # Get the rules added for free
            auto_rules = neutron_utils.get_rules_by_security_group(self.__neutron, self.__security_group)

            ctr = 0
            for auto_rule in auto_rules:
                auto_rule_setting = self.__generate_rule_setting(auto_rule)
                self.__rules[auto_rule_setting] = auto_rule
                ctr += 1

            # Create the custom rules
            for sec_grp_rule_setting in self.sec_grp_settings.rule_settings:
                custom_rule = neutron_utils.create_security_group_rule(self.__neutron, sec_grp_rule_setting)
                self.__rules[sec_grp_rule_setting] = custom_rule

            # Refresh security group object to reflect the new rules added to it
            self.__security_group = neutron_utils.get_security_group(self.__neutron, self.sec_grp_settings.name)
        else:
            # Populate rules
            existing_rules = neutron_utils.get_rules_by_security_group(self.__neutron, self.__security_group)

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
        :param rule: the rule from which to create the SecurityGroupRuleSettings object
        :return: the newly instantiated SecurityGroupRuleSettings object
        """
        rule_dict = rule['security_group_rule']
        sec_grp_name = None
        if rule_dict['security_group_id']:
            sec_grp = neutron_utils.get_security_group_by_id(self.__neutron, rule_dict['security_group_id'])
            if sec_grp:
                sec_grp_name = sec_grp['security_group']['name']

        setting = SecurityGroupRuleSettings(description=rule_dict['description'],
                                            direction=rule_dict['direction'], ethertype=rule_dict['ethertype'],
                                            port_range_min=rule_dict['port_range_min'],
                                            port_range_max=rule_dict['port_range_max'], protocol=rule_dict['protocol'],
                                            remote_group_id=rule_dict['remote_group_id'],
                                            remote_ip_prefix=rule_dict['remote_ip_prefix'], sec_grp_name=sec_grp_name)
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
                neutron_utils.delete_security_group(self.__neutron, self.__security_group)
            except NotFound as e:
                logger.warning('Security Group not found, cannot delete - ' + str(e))

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
        new_rule = neutron_utils.create_security_group_rule(self.__neutron, rule_setting)
        self.__rules[rule_setting] = new_rule
        self.sec_grp_settings.rule_settings.append(rule_setting)

    def remove_rule(self, rule_id=None, rule_setting=None):
        """
        Removes a rule to this security group by id, name, or rule_setting object
        :param rule_id: the rule's id
        :param rule_setting: the rule's setting object
        """
        rule_to_remove = None
        if rule_id or rule_setting:
            if rule_id:
                rule_to_remove = neutron_utils.get_rule_by_id(self.__neutron, self.__security_group, rule_id)
            elif rule_setting:
                rule_to_remove = self.__rules.get(rule_setting)

        if rule_to_remove:
            neutron_utils.delete_security_group_rule(self.__neutron, rule_to_remove)
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

    def __init__(self, config=None, name=None, description=None, project_name=None,
                 rule_settings=list()):
        """
        Constructor - all parameters are optional
        :param config: Should be a dict object containing the configuration settings using the attribute names below
                       as each member's the key and overrides any of the other parameters.
        :param name: The keypair name.
        :param description: The security group's description
        :param project_name: The name of the project under which the security group will be created
        :return:
        """
        if config:
            self.name = config.get('name')
            self.description = config.get('description')
            self.project_name = config.get('project_name')
            self.rule_settings = list()
            if config.get('rules') and type(config['rules']) is list:
                for config_rule in config['rules']:
                    self.rule_settings.append(SecurityGroupRuleSettings(config=config_rule))
        else:
            self.name = name
            self.description = description
            self.project_name = project_name
            self.rule_settings = rule_settings

        if not self.name:
            raise Exception('The attribute name is required')

        for rule_setting in self.rule_settings:
            if rule_setting.sec_grp_name is not self.name:
                raise Exception('Rule settings must correspond with the name of this security group')

    def dict_for_neutron(self, keystone):
        """
        Returns a dictionary object representing this object.
        This is meant to be converted into JSON designed for use by the Neutron API

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
            project = keystone_utils.get_project(keystone, self.project_name)
            project_id = None
            if project:
                project_id = project.id
            if project_id:
                out['project_id'] = project_id
            else:
                raise Exception('Could not find project ID for project named - ' + self.project_name)

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


class SecurityGroupRuleSettings:
    """
    Class representing a keypair configuration
    """

    def __init__(self, config=None, sec_grp_name=None, description=None, direction=None,
                 remote_group_id=None, protocol=None, ethertype=None, port_range_min=None, port_range_max=None,
                 sec_grp_rule=None, remote_ip_prefix=None):
        """
        Constructor - all parameters are optional
        :param config: Should be a dict object containing the configuration settings using the attribute names below
                       as each member's the key and overrides any of the other parameters.
        :param sec_grp_name: The security group's name on which to add the rule. (required)
        :param description: The rule's description
        :param direction: An enumeration of type create_security_group.RULE_DIRECTION (required)
        :param remote_group_id: The group ID to associate with this rule (this should be changed to group name
                                once snaps support Groups) (optional)
        :param protocol: An enumeration of type create_security_group.RULE_PROTOCOL or a string value that will be
                         mapped accordingly (optional)
        :param ethertype: An enumeration of type create_security_group.RULE_ETHERTYPE (optional)
        :param port_range_min: The minimum port number in the range that is matched by the security group rule. When
                               the protocol is TCP or UDP, this value must be <= port_range_max. When the protocol is
                               ICMP, this value must be an ICMP type.
        :param port_range_max: The maximum port number in the range that is matched by the security group rule. When
                               the protocol is TCP or UDP, this value must be <= port_range_max. When the protocol is
                               ICMP, this value must be an ICMP type.
        :param sec_grp_rule: The OpenStack rule object to a security group rule object to associate
                             (note: Cannot be set using the config object nor can I see any real uses for this
                             parameter)
        :param remote_ip_prefix: The remote IP prefix to associate with this metering rule packet (optional)

        TODO - Need to support the tenant...
        """

        if config:
            self.description = config.get('description')
            self.sec_grp_name = config.get('sec_grp_name')
            self.remote_group_id = config.get('remote_group_id')
            self.direction = None
            if config.get('direction'):
                self.direction = map_direction(config['direction'])

            self.protocol = None
            if config.get('protocol'):
                self.protocol = map_protocol(config['protocol'])
            else:
                self.protocol = Protocol.null

            self.ethertype = None
            if config.get('ethertype'):
                self.ethertype = map_ethertype(config['ethertype'])

            self.port_range_min = config.get('port_range_min')
            self.port_range_max = config.get('port_range_max')
            self.remote_ip_prefix = config.get('remote_ip_prefix')
        else:
            self.description = description
            self.sec_grp_name = sec_grp_name
            self.remote_group_id = remote_group_id
            self.direction = map_direction(direction)
            self.protocol = map_protocol(protocol)
            self.ethertype = map_ethertype(ethertype)
            self.port_range_min = port_range_min
            self.port_range_max = port_range_max
            self.sec_grp_rule = sec_grp_rule
            self.remote_ip_prefix = remote_ip_prefix

        if not self.direction or not self.sec_grp_name:
            raise Exception('direction and sec_grp_name are required')

    def dict_for_neutron(self, neutron):
        """
        Returns a dictionary object representing this object.
        This is meant to be converted into JSON designed for use by the Neutron API

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
        if self.protocol:
            out['protocol'] = self.protocol.name
        if self.sec_grp_name:
            sec_grp = neutron_utils.get_security_group(neutron, self.sec_grp_name)
            if sec_grp:
                out['security_group_id'] = sec_grp['security_group']['id']
            else:
                raise Exception('Cannot locate security group with name - ' + self.sec_grp_name)
        if self.remote_group_id:
            out['remote_group_id'] = self.remote_group_id
        if self.sec_grp_rule:
            out['security_group_rule'] = self.sec_grp_rule
        if self.remote_ip_prefix:
            out['remote_ip_prefix'] = self.remote_ip_prefix

        return {'security_group_rule': out}

    def rule_eq(self, rule):
        """
        Returns True if this setting created the rule
        :param rule: the rule to evaluate
        :return: T/F
        """
        rule_dict = rule['security_group_rule']

        if self.description is not None:
            if rule_dict['description'] is not None and rule_dict['description'] != '':
                return False
        elif self.description != rule_dict['description']:
            if rule_dict['description'] != '':
                return False

        if self.direction.name != rule_dict['direction']:
            return False

        if self.ethertype and rule_dict.get('ethertype'):
            if self.ethertype.name != rule_dict['ethertype']:
                return False

        if self.port_range_min and rule_dict.get('port_range_min'):
            if self.port_range_min != rule_dict['port_range_min']:
                return False

        if self.port_range_max and rule_dict.get('port_range_max'):
            if self.port_range_max != rule_dict['port_range_max']:
                return False

        if self.protocol and rule_dict.get('protocol'):
            if self.protocol.name != rule_dict['protocol']:
                return False

        if self.remote_group_id and rule_dict.get('remote_group_id'):
            if self.remote_group_id != rule_dict['remote_group_id']:
                return False

        if self.remote_ip_prefix and rule_dict.get('remote_ip_prefix'):
            if self.remote_ip_prefix != rule_dict['remote_ip_prefix']:
                return False

        return True

    def __eq__(self, other):
        return self.description == other.description and \
               self.direction == other.direction and \
               self.port_range_min == other.port_range_min and \
               self.port_range_max == other.port_range_max and \
               self.ethertype == other.ethertype and \
               self.protocol == other.protocol and \
               self.sec_grp_name == other.sec_grp_name and \
               self.remote_group_id == other.remote_group_id and \
               self.sec_grp_rule == other.sec_grp_rule and \
               self.remote_ip_prefix == other.remote_ip_prefix

    def __hash__(self):
        return hash((self.sec_grp_name, self.description, self.direction, self.remote_group_id,
                     self.protocol, self.ethertype, self.port_range_min, self.port_range_max, self.sec_grp_rule,
                     self.remote_ip_prefix))


def map_direction(direction):
    """
    Takes a the direction value maps it to the Direction enum. When None return None
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
            raise Exception('Invalid Direction - ' + dir_str)


def map_protocol(protocol):
    """
    Takes a the protocol value maps it to the Protocol enum. When None return None
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
            raise Exception('Invalid Protocol - ' + proto_str)


def map_ethertype(ethertype):
    """
    Takes a the ethertype value maps it to the Ethertype enum. When None return None
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
            raise Exception('Invalid Ethertype - ' + eth_str)
