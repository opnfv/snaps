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
from neutronclient.common.exceptions import NotFound, Conflict

from snaps.config.security_group import (
    SecurityGroupConfig, SecurityGroupRuleConfig)
from snaps.openstack.openstack_creator import OpenStackNetworkObject
from snaps.openstack.utils import neutron_utils

__author__ = 'spisarski'

logger = logging.getLogger('OpenStackSecurityGroup')


class OpenStackSecurityGroup(OpenStackNetworkObject):
    """
    Class responsible for managing a Security Group in OpenStack
    """

    def __init__(self, os_creds, sec_grp_settings):
        """
        Constructor - all parameters are required
        :param os_creds: The credentials to connect with OpenStack
        :param sec_grp_settings: The settings used to create a security group
        """
        super(self.__class__, self).__init__(os_creds)

        self.sec_grp_settings = sec_grp_settings

        # Attributes instantiated on create()
        self.__security_group = None

        # dict where the rule settings object is the key
        self.__rules = dict()

    def initialize(self):
        """
        Loads existing security group.
        :return: the security group domain object
        """
        super(self.__class__, self).initialize()

        self.__security_group = neutron_utils.get_security_group(
            self._neutron, self._keystone,
            sec_grp_settings=self.sec_grp_settings,
            project_name=self._os_creds.project_name)
        if self.__security_group:
            # Populate rules
            existing_rules = neutron_utils.get_rules_by_security_group(
                self._neutron, self.__security_group)

            for existing_rule in existing_rules:
                # For Custom Rules
                rule_setting = self.__get_setting_from_rule(existing_rule)
                self.__rules[rule_setting] = existing_rule

            self.__security_group = neutron_utils.get_security_group_by_id(
                self._neutron, self.__security_group.id)

        return self.__security_group

    def create(self):
        """
        Responsible for creating the security group.
        :return: the security group domain object
        """
        self.initialize()

        if not self.__security_group:
            logger.info(
                'Creating security group %s...' % self.sec_grp_settings.name)

            self.__security_group = neutron_utils.create_security_group(
                self._neutron, self._keystone, self.sec_grp_settings)

            # Get the rules added for free
            auto_rules = neutron_utils.get_rules_by_security_group(
                self._neutron, self.__security_group)

            ctr = 0
            for auto_rule in auto_rules:
                auto_rule_setting = self.__generate_rule_setting(auto_rule)
                self.__rules[auto_rule_setting] = auto_rule
                ctr += 1

            # Create the custom rules
            for sec_grp_rule_setting in self.sec_grp_settings.rule_settings:
                try:
                    custom_rule = neutron_utils.create_security_group_rule(
                        self._neutron, self._keystone, sec_grp_rule_setting,
                        self._os_creds.project_name)
                    self.__rules[sec_grp_rule_setting] = custom_rule
                except Conflict as e:
                    logger.warn('Unable to create rule due to conflict - %s',
                                e)

            # Refresh security group object to reflect the new rules added
            self.__security_group = neutron_utils.get_security_group_by_id(
                self._neutron, self.__security_group.id)

        return self.__security_group

    def __generate_rule_setting(self, rule):
        """
        Creates a SecurityGroupRuleConfig object for a given rule
        :param rule: the rule from which to create the
                    SecurityGroupRuleConfig object
        :return: the newly instantiated SecurityGroupRuleConfig object
        """
        sec_grp = neutron_utils.get_security_group_by_id(
            self._neutron, rule.security_group_id)

        setting = SecurityGroupRuleConfig(
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
                neutron_utils.delete_security_group_rule(self._neutron, rule)
            except NotFound as e:
                logger.warning('Rule not found, cannot delete - ' + str(e))
                pass
        self.__rules = dict()

        if self.__security_group:
            try:
                neutron_utils.delete_security_group(self._neutron,
                                                    self.__security_group)
            except NotFound as e:
                logger.warning(
                    'Security Group not found, cannot delete - ' + str(e))

            self.__security_group = None

        super(self.__class__, self).clean()

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
        new_rule = neutron_utils.create_security_group_rule(
            self._neutron, self._keystone, rule_setting,
            self._os_creds.project_name)
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
                    self._neutron, self.__security_group, rule_id)
            elif rule_setting:
                rule_to_remove = self.__rules.get(rule_setting)

        if rule_to_remove:
            neutron_utils.delete_security_group_rule(self._neutron,
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


class SecurityGroupSettings(SecurityGroupConfig):
    """
    Class to hold the configuration settings required for creating OpenStack
    SecurityGroup objects
    deprecated - use snaps.config.security_group.SecurityGroupConfig instead
    """

    def __init__(self, **kwargs):
        from warnings import warn
        warn('Use snaps.config.security_group.SecurityGroupConfig instead',
             DeprecationWarning)
        super(self.__class__, self).__init__(**kwargs)


class Direction(enum.Enum):
    """
    A rule's direction
    deprecated - use snaps.config.security_group.Direction
    """
    ingress = 'ingress'
    egress = 'egress'


class Protocol(enum.Enum):
    """
    A rule's protocol
    deprecated - use snaps.config.security_group.Protocol
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
    deprecated - use snaps.config.security_group.Ethertype
    """
    IPv4 = 4
    IPv6 = 6


class SecurityGroupRuleSettings(SecurityGroupRuleConfig):
    """
    Class to hold the configuration settings required for creating OpenStack
    SecurityGroupRule objects
    deprecated - use snaps.config.security_group.SecurityGroupRuleConfig
    instead
    """

    def __init__(self, **kwargs):
        from warnings import warn
        warn('Use snaps.config.security_group.SecurityGroupRuleConfig instead',
             DeprecationWarning)
        super(self.__class__, self).__init__(**kwargs)
