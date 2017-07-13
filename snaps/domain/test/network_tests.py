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
from snaps.domain.network import (
    Port, SecurityGroup, SecurityGroupRule,  Router, InterfaceRouter)


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


class RouterDomainObjectTests(unittest.TestCase):
    """
    Tests the construction of the snaps.domain.network.Router class
    """

    def test_construction_kwargs(self):
        sec_grp = Router(
            **{'name': 'name', 'id': 'id', 'status': 'hello',
               'tenant_id': '1234', 'admin_state_up': 'yes',
               'external_gateway_info': 'no'})
        self.assertEqual('name', sec_grp.name)
        self.assertEqual('id', sec_grp.id)
        self.assertEqual('hello', sec_grp.status)
        self.assertEqual('1234', sec_grp.tenant_id)
        self.assertEqual('yes', sec_grp.admin_state_up)
        self.assertEqual('no', sec_grp.external_gateway_info)

    def test_construction_named(self):
        sec_grp = Router(
            external_gateway_info='no', admin_state_up='yes', tenant_id='1234',
            status='hello', id='id', name='name')
        self.assertEqual('name', sec_grp.name)
        self.assertEqual('id', sec_grp.id)
        self.assertEqual('hello', sec_grp.status)
        self.assertEqual('1234', sec_grp.tenant_id)
        self.assertEqual('yes', sec_grp.admin_state_up)
        self.assertEqual('no', sec_grp.external_gateway_info)


class InterfaceRouterDomainObjectTests(unittest.TestCase):
    """
    Tests the construction of the snaps.domain.network.InterfaceRouter class
    """

    def test_construction_kwargs(self):
        sec_grp = InterfaceRouter(
            **{'id': 'id', 'subnet_id': 'foo', 'port_id': 'bar'})
        self.assertEqual('id', sec_grp.id)
        self.assertEqual('foo', sec_grp.subnet_id)
        self.assertEqual('bar', sec_grp.port_id)

    def test_construction_named(self):
        sec_grp = InterfaceRouter(port_id='bar', subnet_id='foo', id='id')
        self.assertEqual('id', sec_grp.id)
        self.assertEqual('foo', sec_grp.subnet_id)
        self.assertEqual('bar', sec_grp.port_id)


class SecurityGroupDomainObjectTests(unittest.TestCase):
    """
    Tests the construction of the snaps.domain.network.SecurityGroup class
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
    Tests the construction of the snaps.domain.network.SecurityGroupRule class
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
