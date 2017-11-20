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

from snaps.config.security_group import (
    Direction, SecurityGroupConfig,  SecurityGroupRuleConfig,
    SecurityGroupConfigError, Protocol, Ethertype,
    SecurityGroupRuleConfigError)


class SecurityGroupRuleConfigUnitTests(unittest.TestCase):
    """
    Tests the construction of the SecurityGroupRuleConfig class
    """

    def test_no_params(self):
        with self.assertRaises(SecurityGroupRuleConfigError):
            SecurityGroupRuleConfig()

    def test_empty_config(self):
        with self.assertRaises(SecurityGroupRuleConfigError):
            SecurityGroupRuleConfig(**dict())

    def test_name_only(self):
        with self.assertRaises(SecurityGroupRuleConfigError):
            SecurityGroupRuleConfig(sec_grp_name='foo')

    def test_config_with_name_only(self):
        with self.assertRaises(SecurityGroupRuleConfigError):
            SecurityGroupRuleConfig(**{'sec_grp_name': 'foo'})

    def test_name_and_direction(self):
        settings = SecurityGroupRuleConfig(sec_grp_name='foo',
                                           direction=Direction.ingress)
        self.assertEqual('foo', settings.sec_grp_name)
        self.assertEqual(Direction.ingress, settings.direction)

    def test_config_name_and_direction(self):
        settings = SecurityGroupRuleConfig(
            **{'sec_grp_name': 'foo', 'direction': 'ingress'})
        self.assertEqual('foo', settings.sec_grp_name)
        self.assertEqual(Direction.ingress, settings.direction)

    def test_proto_ah_str(self):
        settings = SecurityGroupRuleConfig(
            **{'sec_grp_name': 'foo', 'direction': 'ingress',
               'protocol': 'ah'})
        self.assertEqual('foo', settings.sec_grp_name)
        self.assertEqual(Direction.ingress, settings.direction)
        self.assertEqual(Protocol.ah, settings.protocol)

    def test_proto_ah_value(self):
        settings = SecurityGroupRuleConfig(
            **{'sec_grp_name': 'foo', 'direction': 'ingress',
               'protocol': 51})
        self.assertEqual('foo', settings.sec_grp_name)
        self.assertEqual(Direction.ingress, settings.direction)
        self.assertEqual(Protocol.ah, settings.protocol)

    def test_proto_any(self):
        settings = SecurityGroupRuleConfig(
            **{'sec_grp_name': 'foo', 'direction': 'ingress',
               'protocol': 'any'})
        self.assertEqual('foo', settings.sec_grp_name)
        self.assertEqual(Direction.ingress, settings.direction)
        self.assertEqual(Protocol.null, settings.protocol)

    def test_proto_null(self):
        settings = SecurityGroupRuleConfig(
            **{'sec_grp_name': 'foo', 'direction': 'ingress',
               'protocol': 'null'})
        self.assertEqual('foo', settings.sec_grp_name)
        self.assertEqual(Direction.ingress, settings.direction)
        self.assertEqual(Protocol.null, settings.protocol)

    def test_all(self):
        settings = SecurityGroupRuleConfig(
            sec_grp_name='foo', description='fubar',
            direction=Direction.egress, remote_group_id='rgi',
            protocol=Protocol.icmp, ethertype=Ethertype.IPv6, port_range_min=1,
            port_range_max=2,
            remote_ip_prefix='prfx')
        self.assertEqual('foo', settings.sec_grp_name)
        self.assertEqual('fubar', settings.description)
        self.assertEqual(Direction.egress, settings.direction)
        self.assertEqual('rgi', settings.remote_group_id)
        self.assertEqual(Protocol.icmp, settings.protocol)
        self.assertEqual(Ethertype.IPv6, settings.ethertype)
        self.assertEqual(1, settings.port_range_min)
        self.assertEqual(2, settings.port_range_max)
        self.assertEqual('prfx', settings.remote_ip_prefix)

    def test_config_all(self):
        settings = SecurityGroupRuleConfig(
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
        self.assertEqual(Direction.egress, settings.direction)
        self.assertEqual('rgi', settings.remote_group_id)
        self.assertEqual(Protocol.tcp, settings.protocol)
        self.assertEqual(Ethertype.IPv6, settings.ethertype)
        self.assertEqual(1, settings.port_range_min)
        self.assertEqual(2, settings.port_range_max)
        self.assertEqual('prfx', settings.remote_ip_prefix)


class SecurityGroupConfigUnitTests(unittest.TestCase):
    """
    Tests the construction of the SecurityGroupConfig class
    """

    def test_no_params(self):
        with self.assertRaises(SecurityGroupConfigError):
            SecurityGroupConfig()

    def test_empty_config(self):
        with self.assertRaises(SecurityGroupConfigError):
            SecurityGroupConfig(**dict())

    def test_name_only(self):
        settings = SecurityGroupConfig(name='foo')
        self.assertEqual('foo', settings.name)

    def test_config_with_name_only(self):
        settings = SecurityGroupConfig(**{'name': 'foo'})
        self.assertEqual('foo', settings.name)

    def test_invalid_rule(self):
        rule_setting = SecurityGroupRuleConfig(
            sec_grp_name='bar', direction=Direction.ingress,
            description='test_rule_1')
        with self.assertRaises(SecurityGroupConfigError):
            SecurityGroupConfig(name='foo', rule_settings=[rule_setting])

    def test_all(self):
        rule_settings = list()
        rule_settings.append(SecurityGroupRuleConfig(
            sec_grp_name='bar', direction=Direction.egress,
            description='test_rule_1'))
        rule_settings.append(SecurityGroupRuleConfig(
            sec_grp_name='bar', direction=Direction.ingress,
            description='test_rule_2'))
        settings = SecurityGroupConfig(
            name='bar', description='fubar', project_name='foo',
            rule_settings=rule_settings)

        self.assertEqual('bar', settings.name)
        self.assertEqual('fubar', settings.description)
        self.assertEqual('foo', settings.project_name)
        self.assertEqual(rule_settings[0], settings.rule_settings[0])
        self.assertEqual(rule_settings[1], settings.rule_settings[1])

    def test_config_all(self):
        settings = SecurityGroupConfig(
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
        self.assertEqual(Direction.ingress,
                         settings.rule_settings[0].direction)
