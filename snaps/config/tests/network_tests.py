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

from snaps.config.network import (
    NetworkConfigError, NetworkConfig, SubnetConfig, SubnetConfigError,
    IPv6Mode, PortConfig, PortConfigError)


class NetworkConfigUnitTests(unittest.TestCase):
    """
    Tests the construction of the NetworkConfig class
    """

    def test_no_params(self):
        with self.assertRaises(NetworkConfigError):
            NetworkConfig()

    def test_empty_config(self):
        with self.assertRaises(NetworkConfigError):
            NetworkConfig(**dict())

    def test_name_only(self):
        settings = NetworkConfig(name='foo')
        self.assertEqual('foo', settings.name)
        self.assertTrue(settings.admin_state_up)
        self.assertIsNone(settings.shared)
        self.assertIsNone(settings.project_name)
        self.assertFalse(settings.external)
        self.assertIsNone(settings.network_type)
        self.assertIsNone(settings.segmentation_id)
        self.assertEqual(0, len(settings.subnet_settings))

    def test_config_with_name_only(self):
        settings = NetworkConfig(**{'name': 'foo'})
        self.assertEqual('foo', settings.name)
        self.assertTrue(settings.admin_state_up)
        self.assertIsNone(settings.shared)
        self.assertIsNone(settings.project_name)
        self.assertFalse(settings.external)
        self.assertIsNone(settings.network_type)
        self.assertIsNone(settings.segmentation_id)
        self.assertEqual(0, len(settings.subnet_settings))

    def test_all(self):
        sub_settings = SubnetConfig(name='foo-subnet', cidr='10.0.0.0/24')
        settings = NetworkConfig(
            name='foo', admin_state_up=False, shared=True, project_name='bar',
            external=True, network_type='vlan', physical_network='phy',
            segmentation_id=2366, subnet_settings=[sub_settings])
        self.assertEqual('foo', settings.name)
        self.assertFalse(settings.admin_state_up)
        self.assertTrue(settings.shared)
        self.assertEqual('bar', settings.project_name)
        self.assertTrue(settings.external)
        self.assertEqual('vlan', settings.network_type)
        self.assertEqual('phy', settings.physical_network)
        self.assertEqual(2366, settings.segmentation_id)
        self.assertEqual(1, len(settings.subnet_settings))
        self.assertEqual('foo-subnet', settings.subnet_settings[0].name)

    def test_config_all(self):
        settings = NetworkConfig(
            **{'name': 'foo', 'admin_state_up': False, 'shared': True,
               'project_name': 'bar', 'external': True, 'network_type': 'vlan',
               'physical_network': 'phy',
               'segmentation_id': 2366,
               'subnets':
                   [{'subnet': {'name': 'foo-subnet',
                                'cidr': '10.0.0.0/24'}}]})
        self.assertEqual('foo', settings.name)
        self.assertFalse(settings.admin_state_up)
        self.assertTrue(settings.shared)
        self.assertEqual('bar', settings.project_name)
        self.assertTrue(settings.external)
        self.assertEqual('vlan', settings.network_type)
        self.assertEqual('phy', settings.physical_network)
        self.assertEqual(2366, settings.segmentation_id)
        self.assertEqual(1, len(settings.subnet_settings))
        self.assertEqual('foo-subnet', settings.subnet_settings[0].name)


class SubnetConfigUnitTests(unittest.TestCase):
    """
    Tests the construction of the SubnetConfig class
    """

    def test_no_params(self):
        with self.assertRaises(SubnetConfigError):
            SubnetConfig()

    def test_empty_config(self):
        with self.assertRaises(SubnetConfigError):
            SubnetConfig(**dict())

    def test_name_only(self):
        with self.assertRaises(SubnetConfigError):
            SubnetConfig(name='foo')

    def test_config_with_name_only(self):
        with self.assertRaises(SubnetConfigError):
            SubnetConfig(**{'name': 'foo'})

    def test_name_cidr_only(self):
        settings = SubnetConfig(name='foo', cidr='10.0.0.0/24')
        self.assertEqual('foo', settings.name)
        self.assertEqual('10.0.0.0/24', settings.cidr)
        self.assertEqual(4, settings.ip_version)
        self.assertIsNone(settings.project_name)
        self.assertIsNone(settings.start)
        self.assertIsNone(settings.end)
        self.assertIsNone(settings.enable_dhcp)
        self.assertEqual(0, len(settings.dns_nameservers))
        self.assertIsNone(settings.host_routes)
        self.assertIsNone(settings.destination)
        self.assertIsNone(settings.nexthop)
        self.assertIsNone(settings.ipv6_ra_mode)
        self.assertIsNone(settings.ipv6_address_mode)

    def test_config_with_name_cidr_only(self):
        settings = SubnetConfig(**{'name': 'foo', 'cidr': '10.0.0.0/24'})
        self.assertEqual('foo', settings.name)
        self.assertEqual('10.0.0.0/24', settings.cidr)
        self.assertEqual(4, settings.ip_version)
        self.assertIsNone(settings.project_name)
        self.assertIsNone(settings.start)
        self.assertIsNone(settings.end)
        self.assertIsNone(settings.gateway_ip)
        self.assertIsNone(settings.enable_dhcp)
        self.assertEqual(0, len(settings.dns_nameservers))
        self.assertIsNone(settings.host_routes)
        self.assertIsNone(settings.destination)
        self.assertIsNone(settings.nexthop)
        self.assertIsNone(settings.ipv6_ra_mode)
        self.assertIsNone(settings.ipv6_address_mode)

    def test_all_string_enums(self):
        host_routes = {'destination': '0.0.0.0/0', 'nexthop': '123.456.78.9'}
        settings = SubnetConfig(
            name='foo', cidr='10.0.0.0/24', ip_version=6,
            project_name='bar-project', start='10.0.0.2', end='10.0.0.101',
            gateway_ip='10.0.0.1', enable_dhcp=False,
            dns_nameservers=['8.8.8.8'], host_routes=[host_routes],
            destination='dest', nexthop='hop', ipv6_ra_mode='dhcpv6-stateful',
            ipv6_address_mode='slaac')
        self.assertEqual('foo', settings.name)
        self.assertEqual('10.0.0.0/24', settings.cidr)
        self.assertEqual(6, settings.ip_version)
        self.assertEqual('bar-project', settings.project_name)
        self.assertEqual('10.0.0.2', settings.start)
        self.assertEqual('10.0.0.101', settings.end)
        self.assertEqual('10.0.0.1', settings.gateway_ip)
        self.assertEqual(False, settings.enable_dhcp)
        self.assertEqual(1, len(settings.dns_nameservers))
        self.assertEqual('8.8.8.8', settings.dns_nameservers[0])
        self.assertEqual(1, len(settings.host_routes))
        self.assertEqual(host_routes, settings.host_routes[0])
        self.assertEqual('dest', settings.destination)
        self.assertEqual('hop', settings.nexthop)
        self.assertEqual(IPv6Mode.stateful, settings.ipv6_ra_mode)
        self.assertEqual(IPv6Mode.slaac, settings.ipv6_address_mode)

    def test_all_type_enums(self):
        host_routes = {'destination': '0.0.0.0/0', 'nexthop': '123.456.78.9'}
        settings = SubnetConfig(
            name='foo', cidr='10.0.0.0/24', ip_version=6,
            project_name='bar-project', start='10.0.0.2', end='10.0.0.101',
            gateway_ip='10.0.0.1', enable_dhcp=False,
            dns_nameservers=['8.8.8.8'], host_routes=[host_routes],
            destination='dest', nexthop='hop', ipv6_ra_mode=IPv6Mode.stateful,
            ipv6_address_mode=IPv6Mode.slaac)
        self.assertEqual('foo', settings.name)
        self.assertEqual('10.0.0.0/24', settings.cidr)
        self.assertEqual(6, settings.ip_version)
        self.assertEqual('bar-project', settings.project_name)
        self.assertEqual('10.0.0.2', settings.start)
        self.assertEqual('10.0.0.101', settings.end)
        self.assertEqual('10.0.0.1', settings.gateway_ip)
        self.assertEqual(False, settings.enable_dhcp)
        self.assertEqual(1, len(settings.dns_nameservers))
        self.assertEqual('8.8.8.8', settings.dns_nameservers[0])
        self.assertEqual(1, len(settings.host_routes))
        self.assertEqual(host_routes, settings.host_routes[0])
        self.assertEqual('dest', settings.destination)
        self.assertEqual('hop', settings.nexthop)
        self.assertEqual(IPv6Mode.stateful, settings.ipv6_ra_mode)
        self.assertEqual(IPv6Mode.slaac, settings.ipv6_address_mode)

    def test_config_all(self):
        host_routes = {'destination': '0.0.0.0/0', 'nexthop': '123.456.78.9'}
        settings = SubnetConfig(
            **{'name': 'foo', 'cidr': '10.0.0.0/24', 'ip_version': 6,
               'project_name': 'bar-project', 'start': '10.0.0.2',
               'end': '10.0.0.101',
               'gateway_ip': '10.0.0.1', 'enable_dhcp': False,
               'dns_nameservers': ['8.8.8.8'], 'host_routes': [host_routes],
               'destination': 'dest', 'nexthop': 'hop',
               'ipv6_ra_mode': 'dhcpv6-stateless',
               'ipv6_address_mode': 'slaac'})
        self.assertEqual('foo', settings.name)
        self.assertEqual('10.0.0.0/24', settings.cidr)
        self.assertEqual(6, settings.ip_version)
        self.assertEqual('bar-project', settings.project_name)
        self.assertEqual('10.0.0.2', settings.start)
        self.assertEqual('10.0.0.101', settings.end)
        self.assertEqual('10.0.0.1', settings.gateway_ip)
        self.assertEqual(False, settings.enable_dhcp)
        self.assertEqual(1, len(settings.dns_nameservers))
        self.assertEqual('8.8.8.8', settings.dns_nameservers[0])
        self.assertEqual(1, len(settings.host_routes))
        self.assertEqual(host_routes, settings.host_routes[0])
        self.assertEqual('dest', settings.destination)
        self.assertEqual('hop', settings.nexthop)
        self.assertEqual(IPv6Mode.stateless, settings.ipv6_ra_mode)
        self.assertEqual(IPv6Mode.slaac, settings.ipv6_address_mode)


class PortConfigUnitTests(unittest.TestCase):
    """
    Tests the construction of the PortConfig class
    """

    def test_no_params(self):
        with self.assertRaises(PortConfigError):
            PortConfig()

    def test_empty_config(self):
        with self.assertRaises(PortConfigError):
            PortConfig(**dict())

    def test_name_only(self):
        with self.assertRaises(PortConfigError):
            PortConfig(name='foo')

    def test_config_name_only(self):
        with self.assertRaises(PortConfigError):
            PortConfig(**{'name': 'foo'})

    def test_name_netname_only(self):
        settings = PortConfig(name='foo', network_name='bar')
        self.assertEqual('foo', settings.name)
        self.assertEqual('bar', settings.network_name)
        self.assertTrue(settings.admin_state_up)
        self.assertIsNone(settings.project_name)
        self.assertIsNone(settings.mac_address)
        self.assertIsNone(settings.ip_addrs)
        self.assertIsNone(settings.security_groups)
        self.assertIsNone(settings.allowed_address_pairs)
        self.assertIsNone(settings.opt_value)
        self.assertIsNone(settings.opt_name)
        self.assertIsNone(settings.device_owner)
        self.assertIsNone(settings.device_id)

    def test_config_with_name_netname_only(self):
        settings = PortConfig(**{'name': 'foo', 'network_name': 'bar'})
        self.assertEqual('foo', settings.name)
        self.assertEqual('bar', settings.network_name)
        self.assertTrue(settings.admin_state_up)
        self.assertIsNone(settings.project_name)
        self.assertIsNone(settings.mac_address)
        self.assertIsNone(settings.ip_addrs)
        self.assertIsNone(settings.security_groups)
        self.assertIsNone(settings.port_security_enabled)
        self.assertIsNone(settings.allowed_address_pairs)
        self.assertIsNone(settings.opt_value)
        self.assertIsNone(settings.opt_name)
        self.assertIsNone(settings.device_owner)
        self.assertIsNone(settings.device_id)

    def test_all(self):
        ip_addrs = [{'subnet_name', 'foo-sub', 'ip', '10.0.0.10'}]
        allowed_address_pairs = {'10.0.0.101', '1234.5678'}

        settings = PortConfig(
            name='foo', network_name='bar', admin_state_up=False,
            project_name='foo-project', mac_address='1234', ip_addrs=ip_addrs,
            security_groups=['foo_grp_id'], port_security_enabled=False,
            allowed_address_pairs=allowed_address_pairs, opt_value='opt value',
            opt_name='opt name', device_owner='owner',
            device_id='device number')
        self.assertEqual('foo', settings.name)
        self.assertEqual('bar', settings.network_name)
        self.assertFalse(settings.admin_state_up)
        self.assertEqual('foo-project', settings.project_name)
        self.assertEqual('1234', settings.mac_address)
        self.assertEqual(ip_addrs, settings.ip_addrs)
        self.assertEqual(1, len(settings.security_groups))
        self.assertFalse(settings.port_security_enabled)
        self.assertEqual('foo_grp_id', settings.security_groups[0])
        self.assertFalse(settings.port_security_enabled)
        self.assertEqual(allowed_address_pairs, settings.allowed_address_pairs)
        self.assertEqual('opt value', settings.opt_value)
        self.assertEqual('opt name', settings.opt_name)
        self.assertEqual('owner', settings.device_owner)
        self.assertEqual('device number', settings.device_id)

    def test_config_all(self):
        ip_addrs = [{'subnet_name', 'foo-sub', 'ip', '10.0.0.10'}]
        allowed_address_pairs = {'10.0.0.101', '1234.5678'}

        settings = PortConfig(
            **{'name': 'foo', 'network_name': 'bar', 'admin_state_up': False,
               'project_name': 'foo-project', 'mac_address': '1234',
               'ip_addrs': ip_addrs, 'security_groups': ['foo_grp_id'],
               'port_security_enabled': 'false',
               'allowed_address_pairs': allowed_address_pairs,
               'opt_value': 'opt value', 'opt_name': 'opt name',
               'device_owner': 'owner', 'device_id': 'device number'})
        self.assertEqual('foo', settings.name)
        self.assertEqual('bar', settings.network_name)
        self.assertFalse(settings.admin_state_up)
        self.assertEqual('foo-project', settings.project_name)
        self.assertEqual('1234', settings.mac_address)
        self.assertEqual(ip_addrs, settings.ip_addrs)
        self.assertEqual(1, len(settings.security_groups))
        self.assertFalse(settings.port_security_enabled)
        self.assertEqual('foo_grp_id', settings.security_groups[0])
        self.assertEqual(allowed_address_pairs, settings.allowed_address_pairs)
        self.assertEqual('opt value', settings.opt_value)
        self.assertEqual('opt name', settings.opt_name)
        self.assertEqual('owner', settings.device_owner)
        self.assertEqual('device number', settings.device_id)
