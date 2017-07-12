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
from snaps.domain.network import Port, SecurityGroup, SecurityGroupRule


class PortDomainObjectTests(unittest.TestCase):
    """
    Tests the construction of the snaps.domain.network.Port class
    """

    def test_construction_kwargs(self):
        ips = ['10', '11']
        port = Port(
            **{'name': 'name', 'id': 'id', 'ips': ips})
        self.assertEqual('name', port.name)
        self.assertEqual('id', port.id)
        self.assertEqual(ips, port.ips)

    def test_construction_named(self):
        ips = ['10', '11']
        port = Port(ips=ips, id='id', name='name')
        self.assertEqual('name', port.name)
        self.assertEqual('id', port.id)
        self.assertEqual(ips, port.ips)


class SecurityGroupDomainObjectTests(unittest.TestCase):
    """
    Tests the construction of the snaps.domain.test.SecurityGroup class
    """

    def test_construction_proj_id_kwargs(self):
        sec_grp = SecurityGroup(
            **{'name': 'name', 'id': 'id',
               'project_id': 'foo'})
        self.assertEqual('name', sec_grp.name)
        self.assertEqual('id', sec_grp.id)
        self.assertEqual('foo', sec_grp.project_id)

    def test_construction_tenant_id_kwargs(self):
        sec_grp = SecurityGroup(
            **{'name': 'name', 'id': 'id',
               'tenant_id': 'foo'})
        self.assertEqual('name', sec_grp.name)
        self.assertEqual('id', sec_grp.id)
        self.assertEqual('foo', sec_grp.project_id)

    def test_construction_named(self):
        sec_grp = SecurityGroup(tenant_id='foo', id='id', name='name')
        self.assertEqual('name', sec_grp.name)
        self.assertEqual('id', sec_grp.id)
        self.assertEqual('foo', sec_grp.project_id)


class SecurityGroupRuleDomainObjectTests(unittest.TestCase):
    """
    Tests the construction of the snaps.domain.test.SecurityGroupRule class
    """

    def test_construction_kwargs(self):
        sec_grp_rule = SecurityGroupRule(
            **{'id': 'id', 'security_group_id': 'grp_id',
               'description': 'desc', 'direction': 'dir', 'ethertype': 'eType',
               'port_range_min': '10.0.0.100', 'port_range_max': '10.0.0.200',
               'protocol': 'proto', 'remote_group_id': 'group_id',
               'remote_ip_prefix': 'ip_prefix'})
        self.assertEqual('id', sec_grp_rule.id)
        self.assertEqual('grp_id', sec_grp_rule.security_group_id)
        self.assertEqual('desc', sec_grp_rule.description)
        self.assertEqual('dir', sec_grp_rule.direction)
        self.assertEqual('eType', sec_grp_rule.ethertype)
        self.assertEqual('10.0.0.100', sec_grp_rule.port_range_min)
        self.assertEqual('10.0.0.200', sec_grp_rule.port_range_max)
        self.assertEqual('proto', sec_grp_rule.protocol)
        self.assertEqual('group_id', sec_grp_rule.remote_group_id)
        self.assertEqual('ip_prefix', sec_grp_rule.remote_ip_prefix)

    def test_construction_named(self):
        sec_grp_rule = SecurityGroupRule(
            remote_ip_prefix='ip_prefix', remote_group_id='group_id',
            protocol='proto', port_range_min='10.0.0.100',
            port_range_max='10.0.0.200', ethertype='eType',
            direction='dir', description='desc', security_group_id='grp_id',
            id='id')
        self.assertEqual('id', sec_grp_rule.id)
        self.assertEqual('grp_id', sec_grp_rule.security_group_id)
        self.assertEqual('desc', sec_grp_rule.description)
        self.assertEqual('dir', sec_grp_rule.direction)
        self.assertEqual('eType', sec_grp_rule.ethertype)
        self.assertEqual('10.0.0.100', sec_grp_rule.port_range_min)
        self.assertEqual('10.0.0.200', sec_grp_rule.port_range_max)
        self.assertEqual('proto', sec_grp_rule.protocol)
        self.assertEqual('group_id', sec_grp_rule.remote_group_id)
        self.assertEqual('ip_prefix', sec_grp_rule.remote_ip_prefix)
