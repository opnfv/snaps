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
    Port, SecurityGroup, SecurityGroupRule, Router, InterfaceRouter, Network,
    Subnet)


class NetworkObjectTests(unittest.TestCase):
    """
    Tests the construction of the snaps.domain.network.Network class
    """

    def test_construction_kwargs_1(self):
        subnet = Subnet(
            **{'name': 'foo', 'id': 'bar', 'project_id': 'proj1',
               'network_id': 'foo-bar'})
        network = Network(
            **{'name': 'foo', 'id': 'bar', 'project_id': 'proj1',
               'provider:network_type': 'flat', 'admin_state_up': False,
               'shared': True, 'router:external': False, 'subnets': [subnet]})
        self.assertEqual('foo', network.name)
        self.assertEqual('bar', network.id)
        self.assertEqual('proj1', network.project_id)
        self.assertEqual('flat', network.type)
        self.assertFalse(network.admin_state_up)
        self.assertFalse(network.external)
        self.assertTrue(network.shared)
        self.assertEqual([subnet], network.subnets)

    def test_construction_kwargs_2(self):
        subnet = Subnet(
            **{'name': 'foo', 'id': 'bar', 'project_id': 'proj1',
               'network_id': 'foo-bar'})
        network = Network(
            **{'name': 'foo', 'id': 'bar', 'project_id': 'proj1',
               'type': 'flat', 'admin_state_up': False, 'shared': True,
               'external': False, 'subnets': [subnet]})
        self.assertEqual('foo', network.name)
        self.assertEqual('bar', network.id)
        self.assertEqual('proj1', network.project_id)
        self.assertEqual('flat', network.type)
        self.assertFalse(network.admin_state_up)
        self.assertFalse(network.external)
        self.assertTrue(network.shared)
        self.assertEqual([subnet], network.subnets)

    def test_construction_named(self):
        subnet = Subnet(
            **{'name': 'foo', 'id': 'bar', 'project_id': 'proj1',
               'network_id': 'foo-bar'})
        network = Network(
            name='foo', id='bar', project_id='proj1', type='flat',
            admin_state_up=False, shared=True, external=False,
            subnets=[subnet])
        self.assertEqual('foo', network.name)
        self.assertEqual('bar', network.id)
        self.assertEqual('proj1', network.project_id)
        self.assertEqual('flat', network.type)
        self.assertFalse(network.admin_state_up)
        self.assertFalse(network.external)
        self.assertTrue(network.shared)
        self.assertEqual([subnet], network.subnets)


class SubnetObjectTests(unittest.TestCase):
    """
    Tests the construction of the snaps.domain.network.Subnet class
    """

    def test_construction_kwargs(self):
        subnet = Subnet(
            **{'name': 'foo', 'id': 'bar', 'project_id': 'proj1',
               'cidr': '10.0.0.0/24', 'ip_version': 4,
               'gateway_ip': '10.0.0.1', 'enable_dhcp': True,
               'dns_nameservers': ['8.8.8.8'], 'host_routes': list(),
               'ipv6_ra_mode': 'hello', 'ipv6_address_mode': 'world'})
        self.assertEqual('foo', subnet.name)
        self.assertEqual('bar', subnet.id)
        self.assertEqual('proj1', subnet.project_id)
        self.assertEqual('10.0.0.0/24', subnet.cidr)
        self.assertEqual(4, subnet.ip_version)
        self.assertEqual('10.0.0.1', subnet.gateway_ip)
        self.assertTrue(subnet.enable_dhcp)
        self.assertEqual(1, len(subnet.dns_nameservers))
        self.assertEqual('8.8.8.8', subnet.dns_nameservers[0])
        self.assertEqual(list(), subnet.host_routes)
        self.assertEqual('hello', subnet.ipv6_ra_mode)
        self.assertEqual('world', subnet.ipv6_address_mode)

    def test_construction_named(self):
        subnet = Subnet(
            name='foo', id='bar', project_id='proj1', cidr='10.0.0.0/24',
            ip_version=4, gateway_ip='10.0.0.1', enable_dhcp=True,
            dns_nameservers=['8.8.8.8'], host_routes=list(),
            ipv6_ra_mode='hello', ipv6_address_mode='world')
        self.assertEqual('foo', subnet.name)
        self.assertEqual('bar', subnet.id)
        self.assertEqual('proj1', subnet.project_id)
        self.assertEqual('10.0.0.0/24', subnet.cidr)
        self.assertEqual(4, subnet.ip_version)
        self.assertEqual('10.0.0.1', subnet.gateway_ip)
        self.assertTrue(subnet.enable_dhcp)
        self.assertEqual(1, len(subnet.dns_nameservers))
        self.assertEqual('8.8.8.8', subnet.dns_nameservers[0])
        self.assertEqual(list(), subnet.host_routes)
        self.assertEqual('hello', subnet.ipv6_ra_mode)
        self.assertEqual('world', subnet.ipv6_address_mode)


class PortDomainObjectTests(unittest.TestCase):
    """
    Tests the construction of the snaps.domain.network.Port class
    """

    def test_construction_ips_kwargs(self):
        ips = ['10', '11']
        port = Port(
            **{'name': 'foo', 'id': 'bar', 'description': 'test desc',
               'ips': ips, 'mac_address': 'abc123',
               'allowed_address_pairs': list(), 'admin_state_up': False,
               'device_id': 'def456', 'device_owner': 'joe',
               'network_id': 'ghi789', 'port_security_enabled': False,
               'security_groups': list(), 'tenant_id': 'jkl098'})
        self.assertEqual('foo', port.name)
        self.assertEqual('bar', port.id)
        self.assertEqual('test desc', port.description)
        self.assertEqual(ips, port.ips)
        self.assertEqual('abc123', port.mac_address)
        self.assertEqual(list(), port.allowed_address_pairs)
        self.assertFalse(port.admin_state_up)
        self.assertEqual('def456', port.device_id)
        self.assertEqual('joe', port.device_owner)
        self.assertEqual('ghi789', port.network_id)
        self.assertFalse(port.port_security_enabled)
        self.assertEqual(list(), port.security_groups)
        self.assertEqual(list(), port.security_groups)

    def test_construction_fixed_ips_kwargs(self):
        ips = ['10', '11']
        port = Port(
            **{'name': 'foo', 'id': 'bar', 'description': 'test desc',
               'fixed_ips': ips, 'mac_address': 'abc123',
               'allowed_address_pairs': list(), 'admin_state_up': False,
               'device_id': 'def456', 'device_owner': 'joe',
               'network_id': 'ghi789', 'port_security_enabled': False,
               'security_groups': list(), 'tenant_id': 'jkl098'})
        self.assertEqual('foo', port.name)
        self.assertEqual('bar', port.id)
        self.assertEqual('test desc', port.description)
        self.assertEqual(ips, port.ips)
        self.assertEqual('abc123', port.mac_address)
        self.assertEqual(list(), port.allowed_address_pairs)
        self.assertFalse(port.admin_state_up)
        self.assertEqual('def456', port.device_id)
        self.assertEqual('joe', port.device_owner)
        self.assertEqual('ghi789', port.network_id)
        self.assertFalse(port.port_security_enabled)
        self.assertEqual(list(), port.security_groups)
        self.assertEqual(list(), port.security_groups)

    def test_construction_named_ips(self):
        ips = ['10', '11']
        port = Port(
            mac_address='abc123', description='test desc', ips=ips, id='bar',
            name='foo', allowed_address_pairs=list(), admin_state_up=False,
            device_id='def456', device_owner='joe', network_id='ghi789',
            port_security_enabled=False, security_groups=list(),
            tenant_id='jkl098')
        self.assertEqual('foo', port.name)
        self.assertEqual('bar', port.id)
        self.assertEqual('test desc', port.description)
        self.assertEqual(ips, port.ips)
        self.assertEqual('abc123', port.mac_address)
        self.assertEqual(list(), port.allowed_address_pairs)
        self.assertFalse(port.admin_state_up)
        self.assertEqual('def456', port.device_id)
        self.assertEqual('joe', port.device_owner)
        self.assertEqual('ghi789', port.network_id)
        self.assertFalse(port.port_security_enabled)
        self.assertEqual(list(), port.security_groups)
        self.assertEqual(list(), port.security_groups)

    def test_construction_named_fixed_ips(self):
        ips = ['10', '11']
        port = Port(
            mac_address='abc123', description='test desc', fixed_ips=ips,
            id='bar', name='foo', allowed_address_pairs=list(),
            admin_state_up=False, device_id='def456', device_owner='joe',
            network_id='ghi789', port_security_enabled=False,
            security_groups=list(), tenant_id='jkl098')
        self.assertEqual('foo', port.name)
        self.assertEqual('bar', port.id)
        self.assertEqual('test desc', port.description)
        self.assertEqual(ips, port.ips)
        self.assertEqual('abc123', port.mac_address)
        self.assertEqual(list(), port.allowed_address_pairs)
        self.assertFalse(port.admin_state_up)
        self.assertEqual('def456', port.device_id)
        self.assertEqual('joe', port.device_owner)
        self.assertEqual('ghi789', port.network_id)
        self.assertFalse(port.port_security_enabled)
        self.assertEqual(list(), port.security_groups)
        self.assertEqual(list(), port.security_groups)


class RouterDomainObjectTests(unittest.TestCase):
    """
    Tests the construction of the snaps.domain.network.Router class
    """

    def test_construction_kwargs(self):
        router = Router(
            **{'name': 'name', 'id': 'id', 'status': 'hello',
               'tenant_id': '1234', 'admin_state_up': 'yes',
               'external_gateway_info': 'no'})
        self.assertEqual('name', router.name)
        self.assertEqual('id', router.id)
        self.assertEqual('hello', router.status)
        self.assertEqual('1234', router.tenant_id)
        self.assertEqual('yes', router.admin_state_up)
        self.assertIsNone(router.external_fixed_ips)
        self.assertIsNone(router.external_network_id)

    def test_construction_named(self):
        router = Router(
            external_gateway_info='no', admin_state_up='yes', tenant_id='1234',
            status='hello', id='id', name='name')
        self.assertEqual('name', router.name)
        self.assertEqual('id', router.id)
        self.assertEqual('hello', router.status)
        self.assertEqual('1234', router.tenant_id)
        self.assertEqual('yes', router.admin_state_up)
        self.assertIsNone(router.external_fixed_ips)
        self.assertIsNone(router.external_network_id)

    def test_ext_gateway_named(self):
        router = Router(
            external_fixed_ips=['456', '789'], external_network_id='123',
            admin_state_up='yes', tenant_id='1234', status='hello', id='id',
            name='name')
        self.assertEqual('name', router.name)
        self.assertEqual('id', router.id)
        self.assertEqual('hello', router.status)
        self.assertEqual('1234', router.tenant_id)
        self.assertEqual('yes', router.admin_state_up)
        self.assertEqual(['456', '789'], router.external_fixed_ips)
        self.assertEqual('123', router.external_network_id)

    def test_ext_net_ips_named(self):
        ext_gateway = {'network_id': '123',
                       'external_fixed_ips': ['456', '789']}
        router = Router(
            external_gateway_info=ext_gateway, admin_state_up='yes',
            tenant_id='1234', status='hello', id='id', name='name')
        self.assertEqual('name', router.name)
        self.assertEqual('id', router.id)
        self.assertEqual('hello', router.status)
        self.assertEqual('1234', router.tenant_id)
        self.assertEqual('yes', router.admin_state_up)
        self.assertEqual(['456', '789'], router.external_fixed_ips)
        self.assertEqual('123', router.external_network_id)


class InterfaceRouterDomainObjectTests(unittest.TestCase):
    """
    Tests the construction of the snaps.domain.network.InterfaceRouter class
    """

    def test_construction_kwargs(self):
        intf_router = InterfaceRouter(
            **{'id': 'id', 'subnet_id': 'foo', 'port_id': 'bar'})
        self.assertEqual('id', intf_router.id)
        self.assertEqual('foo', intf_router.subnet_id)
        self.assertEqual('bar', intf_router.port_id)

    def test_construction_named(self):
        intf_router = InterfaceRouter(port_id='bar', subnet_id='foo', id='id')
        self.assertEqual('id', intf_router.id)
        self.assertEqual('foo', intf_router.subnet_id)
        self.assertEqual('bar', intf_router.port_id)


class SecurityGroupDomainObjectTests(unittest.TestCase):
    """
    Tests the construction of the snaps.domain.network.SecurityGroup class
    """

    def test_construction_proj_id_kwargs(self):
        sec_grp = SecurityGroup(
            **{'name': 'name', 'id': 'id', 'project_id': 'foo',
               'description': 'test desc',
               'rules': [
                    {'id': 'id', 'security_group_id': 'grp_id',
                     'description': 'desc', 'direction': 'dir',
                     'ethertype': 'eType', 'port_range_min': '10.0.0.100',
                     'port_range_max': '10.0.0.200', 'protocol': 'proto',
                     'remote_group_id': 'group_id',
                     'remote_ip_prefix': 'ip_prefix'}
               ]})
        self.assertEqual('name', sec_grp.name)
        self.assertEqual('id', sec_grp.id)
        self.assertEqual('test desc', sec_grp.description)
        self.assertEqual('foo', sec_grp.project_id)

        self.assertEqual(1, len(sec_grp.rules))
        rule = sec_grp.rules[0]
        self.assertEqual('id', rule.id)
        self.assertEqual('grp_id', rule.security_group_id)
        self.assertEqual('desc', rule.description)
        self.assertEqual('dir', rule.direction)
        self.assertEqual('eType', rule.ethertype)
        self.assertEqual('10.0.0.100', rule.port_range_min)
        self.assertEqual('10.0.0.200', rule.port_range_max)
        self.assertEqual('proto', rule.protocol)
        self.assertEqual('group_id', rule.remote_group_id)
        self.assertEqual('ip_prefix', rule.remote_ip_prefix)

    def test_construction_tenant_id_kwargs(self):
        sec_grp = SecurityGroup(
            **{'name': 'name', 'id': 'id',
               'tenant_id': 'foo'})
        self.assertEqual('name', sec_grp.name)
        self.assertEqual('id', sec_grp.id)
        self.assertEqual('foo', sec_grp.project_id)
        self.assertIsNone(sec_grp.description)
        self.assertEqual(0, len(sec_grp.rules))

    def test_construction_named(self):
        rules = [SecurityGroupRule(
            **{'id': 'id', 'security_group_id': 'grp_id',
               'description': 'desc', 'direction': 'dir',
               'ethertype': 'eType', 'port_range_min': '10.0.0.100',
               'port_range_max': '10.0.0.200', 'protocol': 'proto',
               'remote_group_id': 'group_id',
               'remote_ip_prefix': 'ip_prefix'}
        )]
        sec_grp = SecurityGroup(description='test desc', tenant_id='foo',
                                id='id', name='name', rules=rules)
        self.assertEqual('name', sec_grp.name)
        self.assertEqual('id', sec_grp.id)
        self.assertEqual('test desc', sec_grp.description)
        self.assertEqual('foo', sec_grp.project_id)

        self.assertEqual(1, len(sec_grp.rules))
        rule = sec_grp.rules[0]
        self.assertEqual('id', rule.id)
        self.assertEqual('grp_id', rule.security_group_id)
        self.assertEqual('desc', rule.description)
        self.assertEqual('dir', rule.direction)
        self.assertEqual('eType', rule.ethertype)
        self.assertEqual('10.0.0.100', rule.port_range_min)
        self.assertEqual('10.0.0.200', rule.port_range_max)
        self.assertEqual('proto', rule.protocol)
        self.assertEqual('group_id', rule.remote_group_id)
        self.assertEqual('ip_prefix', rule.remote_ip_prefix)


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
