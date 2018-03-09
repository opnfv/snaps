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
import unittest
import uuid

from snaps.config.security_group import (
    SecurityGroupConfig,  SecurityGroupRuleConfig,
    SecurityGroupRuleConfigError, SecurityGroupConfigError)
from snaps.openstack import create_security_group
from snaps.openstack.create_security_group import (
    SecurityGroupSettings, SecurityGroupRuleSettings, Direction, Ethertype,
    Protocol, OpenStackSecurityGroup)
from snaps.openstack.tests import validation_utils
from snaps.openstack.tests.os_source_file_test import OSIntegrationTestCase
from snaps.openstack.utils import neutron_utils

__author__ = 'spisarski'


class SecurityGroupRuleSettingsUnitTests(unittest.TestCase):
    """
    Tests the construction of the SecurityGroupRuleSettings class
    """

    def test_no_params(self):
        with self.assertRaises(SecurityGroupRuleConfigError):
            SecurityGroupRuleSettings()

    def test_empty_config(self):
        with self.assertRaises(SecurityGroupRuleConfigError):
            SecurityGroupRuleSettings(**dict())

    def test_name_only(self):
        with self.assertRaises(SecurityGroupRuleConfigError):
            SecurityGroupRuleSettings(sec_grp_name='foo')

    def test_config_with_name_only(self):
        with self.assertRaises(SecurityGroupRuleConfigError):
            SecurityGroupRuleSettings(**{'sec_grp_name': 'foo'})

    def test_name_and_direction(self):
        settings = SecurityGroupRuleSettings(sec_grp_name='foo',
                                             direction=Direction.ingress)
        self.assertEqual('foo', settings.sec_grp_name)
        self.assertEqual(Direction.ingress.value, settings.direction.value)

    def test_config_name_and_direction(self):
        settings = SecurityGroupRuleSettings(
            **{'sec_grp_name': 'foo', 'direction': 'ingress'})
        self.assertEqual('foo', settings.sec_grp_name)
        self.assertEqual(Direction.ingress.value, settings.direction.value)

    def test_proto_ah_str(self):
        settings = SecurityGroupRuleSettings(
            **{'sec_grp_name': 'foo', 'direction': 'ingress',
               'protocol': 'ah'})
        self.assertEqual('foo', settings.sec_grp_name)
        self.assertEqual(Direction.ingress.value, settings.direction.value)
        self.assertEqual(Protocol.ah.value, settings.protocol.value)

    def test_proto_ah_value(self):
        settings = SecurityGroupRuleSettings(
            **{'sec_grp_name': 'foo', 'direction': 'ingress',
               'protocol': 51})
        self.assertEqual('foo', settings.sec_grp_name)
        self.assertEqual(Direction.ingress.value, settings.direction.value)
        self.assertEqual(Protocol.ah.value, settings.protocol.value)

    def test_proto_any(self):
        settings = SecurityGroupRuleSettings(
            **{'sec_grp_name': 'foo', 'direction': 'ingress',
               'protocol': 'any'})
        self.assertEqual('foo', settings.sec_grp_name)
        self.assertEqual(Direction.ingress.value, settings.direction.value)
        self.assertEqual(Protocol.null.value, settings.protocol.value)

    def test_proto_null(self):
        settings = SecurityGroupRuleSettings(
            **{'sec_grp_name': 'foo', 'direction': 'ingress',
               'protocol': 'null'})
        self.assertEqual('foo', settings.sec_grp_name)
        self.assertEqual(Direction.ingress.value, settings.direction.value)
        self.assertEqual(Protocol.null.value, settings.protocol.value)

    def test_all(self):
        settings = SecurityGroupRuleSettings(
            sec_grp_name='foo', description='fubar',
            direction=Direction.egress, remote_group_id='rgi',
            protocol=Protocol.icmp, ethertype=Ethertype.IPv6, port_range_min=1,
            port_range_max=2,
            remote_ip_prefix='prfx')
        self.assertEqual('foo', settings.sec_grp_name)
        self.assertEqual('fubar', settings.description)
        self.assertEqual(Direction.egress.value, settings.direction.value)
        self.assertEqual('rgi', settings.remote_group_id)
        self.assertEqual(Protocol.icmp.value, settings.protocol.value)
        self.assertEqual(Ethertype.IPv6.value, settings.ethertype.value)
        self.assertEqual(1, settings.port_range_min)
        self.assertEqual(2, settings.port_range_max)
        self.assertEqual('prfx', settings.remote_ip_prefix)

    def test_config_all(self):
        settings = SecurityGroupRuleSettings(
            **{'sec_grp_name': 'foo',
               'description': 'fubar',
               'direction': 'egress',
               'remote_group_id': 'rgi',
               'protocol': 'tcp',
               'ethertype': 'IPv6',
               'port_range_min': 1,
               'port_range_max': 2,
               'remote_ip_prefix': 'prfx'})
        self.assertEqual('foo', settings.sec_grp_name)
        self.assertEqual('fubar', settings.description)
        self.assertEqual(Direction.egress.value, settings.direction.value)
        self.assertEqual('rgi', settings.remote_group_id)
        self.assertEqual(Protocol.tcp.value, settings.protocol.value)
        self.assertEqual(Ethertype.IPv6.value, settings.ethertype.value)
        self.assertEqual(1, settings.port_range_min)
        self.assertEqual(2, settings.port_range_max)
        self.assertEqual('prfx', settings.remote_ip_prefix)


class SecurityGroupSettingsUnitTests(unittest.TestCase):
    """
    Tests the construction of the SecurityGroupSettings class
    """

    def test_no_params(self):
        with self.assertRaises(SecurityGroupConfigError):
            SecurityGroupSettings()

    def test_empty_config(self):
        with self.assertRaises(SecurityGroupConfigError):
            SecurityGroupSettings(**dict())

    def test_name_only(self):
        settings = SecurityGroupSettings(name='foo')
        self.assertEqual('foo', settings.name)

    def test_config_with_name_only(self):
        settings = SecurityGroupSettings(**{'name': 'foo'})
        self.assertEqual('foo', settings.name)

    def test_invalid_rule(self):
        rule_setting = SecurityGroupRuleSettings(
            sec_grp_name='bar', direction=Direction.ingress,
            description='test_rule_1')
        with self.assertRaises(SecurityGroupConfigError):
            SecurityGroupSettings(name='foo', rule_settings=[rule_setting])

    def test_all(self):
        rule_settings = list()
        rule_settings.append(SecurityGroupRuleSettings(
            sec_grp_name='bar', direction=Direction.egress,
            description='test_rule_1'))
        rule_settings.append(SecurityGroupRuleSettings(
            sec_grp_name='bar', direction=Direction.ingress,
            description='test_rule_2'))
        settings = SecurityGroupSettings(
            name='bar', description='fubar', project_name='foo',
            rule_settings=rule_settings)

        self.assertEqual('bar', settings.name)
        self.assertEqual('fubar', settings.description)
        self.assertEqual('foo', settings.project_name)
        self.assertEqual(rule_settings[0], settings.rule_settings[0])
        self.assertEqual(rule_settings[1], settings.rule_settings[1])

    def test_config_all(self):
        settings = SecurityGroupSettings(
            **{'name': 'bar',
               'description': 'fubar',
               'project_name': 'foo',
               'rules': [
                   {'sec_grp_name': 'bar', 'direction': 'ingress'}]})

        self.assertEqual('bar', settings.name)
        self.assertEqual('fubar', settings.description)
        self.assertEqual('foo', settings.project_name)
        self.assertEqual(1, len(settings.rule_settings))
        self.assertEqual('bar', settings.rule_settings[0].sec_grp_name)
        self.assertEqual(Direction.ingress.value,
                         settings.rule_settings[0].direction.value)


class CreateSecurityGroupTests(OSIntegrationTestCase):
    """
    Test for the CreateSecurityGroup class defined in create_security_group.py
    """

    def setUp(self):
        """
        Instantiates the CreateSecurityGroup object that is responsible for
        downloading and creating an OS image file within OpenStack
        """
        super(self.__class__, self).__start__()

        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.sec_grp_name = guid + 'name'
        self.neutron = neutron_utils.neutron_client(
            self.os_creds, self.os_session)

        # Initialize for cleanup
        self.sec_grp_creator = None

    def tearDown(self):
        """
        Cleans the image and downloaded image file
        """
        if self.sec_grp_creator:
            self.sec_grp_creator.clean()

        super(self.__class__, self).__clean__()

    def test_create_group_without_rules(self):
        """
        Tests the creation of an OpenStack Security Group without custom rules.
        """
        # Create Security Group
        sec_grp_settings = SecurityGroupConfig(name=self.sec_grp_name,
                                               description='hello group')
        self.sec_grp_creator = create_security_group.OpenStackSecurityGroup(
            self.os_creds, sec_grp_settings)
        self.sec_grp_creator.create()

        sec_grp = neutron_utils.get_security_group(
            self.neutron, self.keystone, sec_grp_settings=sec_grp_settings)
        self.assertIsNotNone(sec_grp)

        validation_utils.objects_equivalent(
            self.sec_grp_creator.get_security_group(), sec_grp)
        rules = neutron_utils.get_rules_by_security_group(
            self.neutron, self.sec_grp_creator.get_security_group())
        self.assertEqual(len(self.sec_grp_creator.get_rules()), len(rules))
        validation_utils.objects_equivalent(self.sec_grp_creator.get_rules(),
                                            rules)

        self.assertTrue(
            validate_sec_grp(
                self.neutron, self.keystone,
                self.sec_grp_creator.sec_grp_settings,
                self.sec_grp_creator.get_security_group()))

    def test_create_group_admin_user_to_new_project(self):
        """
        Tests the creation of an OpenStack Security Group without custom rules.
        """
        # Create Security Group
        sec_grp_settings = SecurityGroupConfig(
            name=self.sec_grp_name, description='hello group',
            project_name=self.os_creds.project_name)
        self.sec_grp_creator = OpenStackSecurityGroup(
            self.admin_os_creds, sec_grp_settings)
        self.sec_grp_creator.create()

        sec_grp = neutron_utils.get_security_group(
            self.neutron, self.keystone, sec_grp_settings=sec_grp_settings)
        self.assertIsNotNone(sec_grp)

        validation_utils.objects_equivalent(
            self.sec_grp_creator.get_security_group(), sec_grp)
        rules = neutron_utils.get_rules_by_security_group(
            self.neutron, self.sec_grp_creator.get_security_group())
        self.assertEqual(len(self.sec_grp_creator.get_rules()), len(rules))
        validation_utils.objects_equivalent(self.sec_grp_creator.get_rules(),
                                            rules)

        self.assertTrue(
            validate_sec_grp(
                self.neutron, self.keystone,
                self.sec_grp_creator.sec_grp_settings,
                self.sec_grp_creator.get_security_group(), rules))

        self.assertEqual(self.sec_grp_creator.get_security_group().id,
                         sec_grp.id)

        proj_creator = OpenStackSecurityGroup(
            self.os_creds, SecurityGroupConfig(name=self.sec_grp_name))
        proj_creator.create()

        self.assertEqual(self.sec_grp_creator.get_security_group().id,
                         proj_creator.get_security_group().id)

    def test_create_group_new_user_to_admin_project(self):
        """
        Tests the creation of an OpenStack Security Group without custom rules.
        """
        # Create Security Group
        sec_grp_settings = SecurityGroupConfig(
            name=self.sec_grp_name, description='hello group',
            project_name=self.os_creds.project_name)
        self.sec_grp_creator = create_security_group.OpenStackSecurityGroup(
            self.admin_os_creds, sec_grp_settings)
        self.sec_grp_creator.create()

        sec_grp = neutron_utils.get_security_group(
            self.neutron, self.keystone, sec_grp_settings=sec_grp_settings)
        self.assertIsNotNone(sec_grp)

        validation_utils.objects_equivalent(
            self.sec_grp_creator.get_security_group(), sec_grp)
        rules = neutron_utils.get_rules_by_security_group(
            self.neutron, self.sec_grp_creator.get_security_group())
        self.assertEqual(len(self.sec_grp_creator.get_rules()), len(rules))
        validation_utils.objects_equivalent(self.sec_grp_creator.get_rules(),
                                            rules)

        self.assertTrue(
            validate_sec_grp(
                self.neutron, self.keystone,
                self.sec_grp_creator.sec_grp_settings,
                self.sec_grp_creator.get_security_group(), rules))

    def test_create_delete_group(self):
        """
        Tests the creation of an OpenStack Security Group without custom rules.
        """
        # Create Security Group
        sec_grp_settings = SecurityGroupConfig(name=self.sec_grp_name,
                                               description='hello group')
        self.sec_grp_creator = create_security_group.OpenStackSecurityGroup(
            self.os_creds, sec_grp_settings)
        created_sec_grp = self.sec_grp_creator.create()
        self.assertIsNotNone(created_sec_grp)

        self.assertTrue(
            validate_sec_grp(
                self.neutron, self.keystone,
                self.sec_grp_creator.sec_grp_settings,
                self.sec_grp_creator.get_security_group()))

        neutron_utils.delete_security_group(self.neutron, created_sec_grp)
        self.assertIsNone(neutron_utils.get_security_group(
            self.neutron, self.keystone,
            sec_grp_settings=self.sec_grp_creator.sec_grp_settings))

        self.sec_grp_creator.clean()

    def test_create_group_with_one_simple_rule(self):
        """
        Tests the creation of an OpenStack Security Group with one simple
        custom rule.
        """
        # Create Security Group
        sec_grp_rule_settings = list()
        sec_grp_rule_settings.append(
            SecurityGroupRuleConfig(
                sec_grp_name=self.sec_grp_name, direction=Direction.ingress,
                description='test_rule_1'))
        sec_grp_settings = SecurityGroupConfig(
            name=self.sec_grp_name, description='hello group',
            rule_settings=sec_grp_rule_settings)
        self.sec_grp_creator = create_security_group.OpenStackSecurityGroup(
            self.os_creds, sec_grp_settings)
        self.sec_grp_creator.create()

        sec_grp = neutron_utils.get_security_group(
            self.neutron, self.keystone, sec_grp_settings=sec_grp_settings)
        validation_utils.objects_equivalent(
            self.sec_grp_creator.get_security_group(), sec_grp)
        rules = neutron_utils.get_rules_by_security_group(
            self.neutron, self.sec_grp_creator.get_security_group())
        self.assertEqual(len(self.sec_grp_creator.get_rules()), len(rules))
        validation_utils.objects_equivalent(self.sec_grp_creator.get_rules(),
                                            rules)

        self.assertTrue(
            validate_sec_grp(
                self.neutron, self.keystone,
                self.sec_grp_creator.sec_grp_settings,
                self.sec_grp_creator.get_security_group(), rules))

    def test_create_group_with_one_complex_rule(self):
        """
        Tests the creation of an OpenStack Security Group with one simple
        custom rule.
        """
        # Create Security Group
        sec_grp_rule_settings = list()
        sec_grp_rule_settings.append(
            SecurityGroupRuleConfig(
                sec_grp_name=self.sec_grp_name, direction=Direction.egress,
                protocol=Protocol.udp, ethertype=Ethertype.IPv4,
                port_range_min=10, port_range_max=20,
                description='test_rule_1'))
        sec_grp_settings = SecurityGroupConfig(
            name=self.sec_grp_name, description='hello group',
            rule_settings=sec_grp_rule_settings)
        self.sec_grp_creator = create_security_group.OpenStackSecurityGroup(
            self.os_creds, sec_grp_settings)
        self.sec_grp_creator.create()

        sec_grp = neutron_utils.get_security_group(
            self.neutron, self.keystone, sec_grp_settings=sec_grp_settings)
        validation_utils.objects_equivalent(
            self.sec_grp_creator.get_security_group(), sec_grp)
        rules = neutron_utils.get_rules_by_security_group(
            self.neutron, self.sec_grp_creator.get_security_group())
        self.assertEqual(len(self.sec_grp_creator.get_rules()), len(rules))
        validation_utils.objects_equivalent(self.sec_grp_creator.get_rules(),
                                            rules)

        self.assertTrue(
            validate_sec_grp(
                self.neutron, self.keystone,
                self.sec_grp_creator.sec_grp_settings,
                self.sec_grp_creator.get_security_group(), rules))

    def test_create_group_with_several_rules(self):
        """
        Tests the creation of an OpenStack Security Group with one simple
        custom rule.
        """
        # Create Security Group
        sec_grp_rule_settings = list()
        sec_grp_rule_settings.append(
            SecurityGroupRuleConfig(
                sec_grp_name=self.sec_grp_name, direction=Direction.ingress,
                description='test_rule_1'))
        sec_grp_rule_settings.append(
            SecurityGroupRuleConfig(
                sec_grp_name=self.sec_grp_name, direction=Direction.egress,
                protocol=Protocol.udp, ethertype=Ethertype.IPv6,
                description='test_rule_2'))
        sec_grp_rule_settings.append(
            SecurityGroupRuleConfig(
                sec_grp_name=self.sec_grp_name, direction=Direction.egress,
                protocol=Protocol.udp, ethertype=Ethertype.IPv4,
                port_range_min=10, port_range_max=20,
                description='test_rule_3'))
        sec_grp_settings = SecurityGroupConfig(
            name=self.sec_grp_name, description='hello group',
            rule_settings=sec_grp_rule_settings)
        self.sec_grp_creator = create_security_group.OpenStackSecurityGroup(
            self.os_creds, sec_grp_settings)
        self.sec_grp_creator.create()

        sec_grp = neutron_utils.get_security_group(
            self.neutron, self.keystone, sec_grp_settings=sec_grp_settings)
        validation_utils.objects_equivalent(
            self.sec_grp_creator.get_security_group(), sec_grp)
        rules = neutron_utils.get_rules_by_security_group(
            self.neutron, self.sec_grp_creator.get_security_group())
        self.assertEqual(len(self.sec_grp_creator.get_rules()), len(rules))
        validation_utils.objects_equivalent(self.sec_grp_creator.get_rules(),
                                            rules)

        self.assertTrue(
            validate_sec_grp(
                self.neutron, self.keystone,
                self.sec_grp_creator.sec_grp_settings,
                self.sec_grp_creator.get_security_group(), rules))

    def test_add_rule(self):
        """
        Tests the creation of an OpenStack Security Group with one simple
        custom rule then adds one after creation.
        """
        # Create Security Group
        sec_grp_rule_settings = list()
        sec_grp_rule_settings.append(
            SecurityGroupRuleConfig(
                sec_grp_name=self.sec_grp_name, direction=Direction.ingress,
                description='test_rule_1'))
        sec_grp_settings = SecurityGroupConfig(
            name=self.sec_grp_name, description='hello group',
            rule_settings=sec_grp_rule_settings)
        self.sec_grp_creator = create_security_group.OpenStackSecurityGroup(
            self.os_creds, sec_grp_settings)
        self.sec_grp_creator.create()

        sec_grp = neutron_utils.get_security_group(
            self.neutron, self.keystone, sec_grp_settings=sec_grp_settings)
        validation_utils.objects_equivalent(
            self.sec_grp_creator.get_security_group(), sec_grp)

        rules = neutron_utils.get_rules_by_security_group(
            self.neutron, self.sec_grp_creator.get_security_group())

        self.assertTrue(
            validate_sec_grp(
                self.neutron, self.keystone,
                self.sec_grp_creator.sec_grp_settings,
                self.sec_grp_creator.get_security_group(), rules))

        rules = neutron_utils.get_rules_by_security_group(
            self.neutron, self.sec_grp_creator.get_security_group())
        self.assertEqual(len(self.sec_grp_creator.get_rules()), len(rules))
        validation_utils.objects_equivalent(self.sec_grp_creator.get_rules(),
                                            rules)

        self.sec_grp_creator.add_rule(SecurityGroupRuleConfig(
            sec_grp_name=self.sec_grp_creator.sec_grp_settings.name,
            direction=Direction.egress, protocol=Protocol.icmp,
            description='test_rule_2'))
        rules2 = neutron_utils.get_rules_by_security_group(
            self.neutron, self.sec_grp_creator.get_security_group())
        self.assertEqual(len(rules) + 1, len(rules2))

    def test_remove_rule_by_id(self):
        """
        Tests the creation of an OpenStack Security Group with two simple
        custom rules then removes one by the rule ID.
        """
        # Create Security Group
        sec_grp_rule_settings = list()
        sec_grp_rule_settings.append(
            SecurityGroupRuleConfig(
                sec_grp_name=self.sec_grp_name, direction=Direction.ingress,
                description='test_rule_1'))
        sec_grp_rule_settings.append(
            SecurityGroupRuleConfig(
                sec_grp_name=self.sec_grp_name, direction=Direction.egress,
                protocol=Protocol.udp, ethertype=Ethertype.IPv6,
                description='test_rule_2'))
        sec_grp_rule_settings.append(
            SecurityGroupRuleConfig(
                sec_grp_name=self.sec_grp_name, direction=Direction.egress,
                protocol=Protocol.udp, ethertype=Ethertype.IPv4,
                port_range_min=10, port_range_max=20,
                description='test_rule_3'))
        sec_grp_settings = SecurityGroupConfig(
            name=self.sec_grp_name, description='hello group',
            rule_settings=sec_grp_rule_settings)
        self.sec_grp_creator = create_security_group.OpenStackSecurityGroup(
            self.os_creds, sec_grp_settings)
        self.sec_grp_creator.create()

        sec_grp = neutron_utils.get_security_group(
            self.neutron, self.keystone, sec_grp_settings=sec_grp_settings)
        validation_utils.objects_equivalent(
            self.sec_grp_creator.get_security_group(), sec_grp)
        rules = neutron_utils.get_rules_by_security_group(
            self.neutron, self.sec_grp_creator.get_security_group())
        self.assertEqual(len(self.sec_grp_creator.get_rules()), len(rules))
        validation_utils.objects_equivalent(self.sec_grp_creator.get_rules(),
                                            rules)

        self.assertTrue(
            validate_sec_grp(
                self.neutron, self.keystone,
                self.sec_grp_creator.sec_grp_settings,
                self.sec_grp_creator.get_security_group(), rules))

        self.sec_grp_creator.remove_rule(
            rule_id=rules[0].id)
        rules_after_del = neutron_utils.get_rules_by_security_group(
            self.neutron,
            self.sec_grp_creator.get_security_group())
        self.assertEqual(len(rules) - 1, len(rules_after_del))

    def test_remove_rule_by_setting(self):
        """
        Tests the creation of an OpenStack Security Group with two simple
        custom rules then removes one by the rule setting object
        """
        # Create Security Group
        sec_grp_rule_settings = list()
        sec_grp_rule_settings.append(
            SecurityGroupRuleConfig(
                sec_grp_name=self.sec_grp_name, direction=Direction.ingress,
                description='test_rule_1'))
        sec_grp_rule_settings.append(
            SecurityGroupRuleConfig(
                sec_grp_name=self.sec_grp_name, direction=Direction.egress,
                protocol=Protocol.udp, ethertype=Ethertype.IPv6,
                description='test_rule_2'))
        sec_grp_rule_settings.append(
            SecurityGroupRuleConfig(
                sec_grp_name=self.sec_grp_name, direction=Direction.egress,
                protocol=Protocol.udp, ethertype=Ethertype.IPv4,
                port_range_min=10, port_range_max=20,
                description='test_rule_3'))
        sec_grp_settings = SecurityGroupConfig(
            name=self.sec_grp_name, description='hello group',
            rule_settings=sec_grp_rule_settings)
        self.sec_grp_creator = create_security_group.OpenStackSecurityGroup(
            self.os_creds, sec_grp_settings)
        self.sec_grp_creator.create()

        sec_grp = neutron_utils.get_security_group(
            self.neutron, self.keystone, sec_grp_settings=sec_grp_settings)
        validation_utils.objects_equivalent(
            self.sec_grp_creator.get_security_group(), sec_grp)

        rules = neutron_utils.get_rules_by_security_group(
            self.neutron, self.sec_grp_creator.get_security_group())
        self.assertEqual(len(self.sec_grp_creator.get_rules()), len(rules))
        validation_utils.objects_equivalent(self.sec_grp_creator.get_rules(),
                                            rules)

        self.assertTrue(
            validate_sec_grp(
                self.neutron, self.keystone,
                self.sec_grp_creator.sec_grp_settings,
                self.sec_grp_creator.get_security_group(), rules))

        self.sec_grp_creator.remove_rule(rule_setting=sec_grp_rule_settings[0])
        rules_after_del = neutron_utils.get_rules_by_security_group(
            self.neutron,
            self.sec_grp_creator.get_security_group())
        self.assertEqual(len(rules) - 1, len(rules_after_del))


def validate_sec_grp(neutron, keystone, sec_grp_settings, sec_grp,
                     rules=list()):
    """
    Returns True is the settings on a security group are properly contained
    on the SNAPS SecurityGroup domain object
    :param neutron: the neutron client
    :param keystone: the keystone client
    :param sec_grp_settings: the security group configuration
    :param sec_grp: the SNAPS-OO security group object
    :param rules: collection of SNAPS-OO security group rule objects
    :return: T/F
    """
    return (sec_grp.description == sec_grp_settings.description and
            sec_grp.name == sec_grp_settings.name and
            validate_sec_grp_rules(
                neutron, keystone, sec_grp_settings.rule_settings, rules))


def validate_sec_grp_rules(neutron, keystone, rule_settings, rules):
    """
    Returns True is the settings on a security group rule are properly
    contained on the SNAPS SecurityGroupRule domain object.
    This function will only operate on rules that contain a description as
    this is the only means to tell if the rule is custom or defaulted by
    OpenStack
    :param neutron: the neutron client
    :param keystone: the keystone client
    :param rule_settings: collection of SecurityGroupRuleConfig objects
    :param rules: a collection of SecurityGroupRule domain objects
    :return: T/F
    """

    for rule_setting in rule_settings:
        if rule_setting.description:
            match = False
            for rule in rules:
                sec_grp = neutron_utils.get_security_group(
                    neutron, keystone, sec_grp_name=rule_setting.sec_grp_name)

                setting_eth_type = create_security_group.Ethertype.IPv4
                if rule_setting.ethertype:
                    setting_eth_type = rule_setting.ethertype

                if not sec_grp:
                    return False

                proto_str = 'null'
                if rule.protocol:
                    proto_str = rule.protocol

                if (rule.description == rule_setting.description and
                    rule.direction == rule_setting.direction.name and
                    rule.ethertype == setting_eth_type.name and
                    rule.port_range_max == rule_setting.port_range_max and
                    rule.port_range_min == rule_setting.port_range_min and
                    proto_str == str(rule_setting.protocol.value) and
                    rule.remote_group_id == rule_setting.remote_group_id and
                    rule.remote_ip_prefix == rule_setting.remote_ip_prefix and
                        rule.security_group_id == sec_grp.id):
                    match = True
                    break

            if not match:
                return False

    return True


class CreateMultipleSecurityGroupTests(OSIntegrationTestCase):
    """
    Test for the CreateSecurityGroup class and how it interacts with security
    groups within other projects with the same name
    """

    def setUp(self):
        """
        Instantiates the CreateSecurityGroup object that is responsible for
        downloading and creating an OS image file within OpenStack
        """
        super(self.__class__, self).__start__()

        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.sec_grp_name = guid + 'name'
        self.neutron = neutron_utils.neutron_client(
            self.os_creds, self.os_session)

        # Initialize for cleanup
        self.admin_sec_grp_config = SecurityGroupConfig(
            name=self.sec_grp_name, description='hello group')
        self.sec_grp_creator_admin = OpenStackSecurityGroup(
            self.admin_os_creds, self.admin_sec_grp_config)
        self.sec_grp_creator_admin.create()
        self.sec_grp_creator_proj = None

    def tearDown(self):
        """
        Cleans the image and downloaded image file
        """
        if self.sec_grp_creator_admin:
            self.sec_grp_creator_admin.clean()
        if self.sec_grp_creator_proj:
            self.sec_grp_creator_proj.clean()

        super(self.__class__, self).__clean__()

    def test_sec_grp_same_name_diff_proj(self):
        """
        Tests the creation of an OpenStack Security Group with the same name
        within a different project/tenant.
        """
        # Create Security Group
        sec_grp_config = SecurityGroupConfig(
            name=self.sec_grp_name, description='hello group')
        self.sec_grp_creator_proj = OpenStackSecurityGroup(
            self.os_creds, sec_grp_config)
        self.sec_grp_creator_proj.create()

        self.assertNotEqual(
            self.sec_grp_creator_admin.get_security_group().id,
            self.sec_grp_creator_proj.get_security_group().id)

        admin_sec_grp_creator = OpenStackSecurityGroup(
            self.admin_os_creds, self.admin_sec_grp_config)
        admin_sec_grp_creator.create()
        self.assertEqual(self.sec_grp_creator_admin.get_security_group().id,
                         admin_sec_grp_creator.get_security_group().id)

        proj_sec_grp_creator = OpenStackSecurityGroup(
            self.os_creds, sec_grp_config)
        proj_sec_grp_creator.create()
        self.assertEqual(self.sec_grp_creator_proj.get_security_group().id,
                         proj_sec_grp_creator.get_security_group().id)
