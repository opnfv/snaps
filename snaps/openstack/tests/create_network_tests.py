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

from neutronclient.common.exceptions import BadRequest

from snaps.config.network import (
    NetworkConfig, SubnetConfig, SubnetConfigError, NetworkConfigError,
    PortConfigError, IPv6Mode)
from snaps.openstack import create_router
from snaps.openstack.create_network import (
    OpenStackNetwork, NetworkSettings, SubnetSettings, PortSettings)
from snaps.openstack.tests import openstack_tests
from snaps.openstack.tests.os_source_file_test import (
    OSIntegrationTestCase, OSComponentTestCase)
from snaps.openstack.utils import neutron_utils, keystone_utils
from snaps.openstack.utils.tests import neutron_utils_tests
from snaps.openstack.create_network import IPv6Mode as IPv6Mode_old

__author__ = 'spisarski'


class NetworkSettingsUnitTests(unittest.TestCase):
    """
    Tests the construction of the NetworkSettings class
    """

    def test_no_params(self):
        with self.assertRaises(NetworkConfigError):
            NetworkSettings()

    def test_empty_config(self):
        with self.assertRaises(NetworkConfigError):
            NetworkSettings(**dict())

    def test_name_only(self):
        settings = NetworkSettings(name='foo')
        self.assertEqual('foo', settings.name)
        self.assertTrue(settings.admin_state_up)
        self.assertIsNone(settings.shared)
        self.assertIsNone(settings.project_name)
        self.assertFalse(settings.external)
        self.assertIsNone(settings.network_type)
        self.assertIsNone(settings.segmentation_id)
        self.assertEqual(0, len(settings.subnet_settings))

    def test_config_with_name_only(self):
        settings = NetworkSettings(**{'name': 'foo'})
        self.assertEqual('foo', settings.name)
        self.assertTrue(settings.admin_state_up)
        self.assertIsNone(settings.shared)
        self.assertIsNone(settings.project_name)
        self.assertFalse(settings.external)
        self.assertIsNone(settings.network_type)
        self.assertIsNone(settings.segmentation_id)
        self.assertEqual(0, len(settings.subnet_settings))

    def test_all(self):
        sub_settings = SubnetSettings(name='foo-subnet', cidr='10.0.0.0/24')
        settings = NetworkSettings(name='foo', admin_state_up=False,
                                   shared=True, project_name='bar',
                                   external=True,
                                   network_type='vlan', physical_network='phy',
                                   segmentation_id=2366,
                                   subnet_settings=[sub_settings])
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
        settings = NetworkSettings(
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


class SubnetSettingsUnitTests(unittest.TestCase):
    """
    Tests the construction of the SubnetSettings class
    """

    def test_no_params(self):
        with self.assertRaises(SubnetConfigError):
            SubnetSettings()

    def test_empty_config(self):
        with self.assertRaises(SubnetConfigError):
            SubnetSettings(**dict())

    def test_name_only(self):
        with self.assertRaises(SubnetConfigError):
            SubnetSettings(name='foo')

    def test_config_with_name_only(self):
        with self.assertRaises(SubnetConfigError):
            SubnetSettings(**{'name': 'foo'})

    def test_name_cidr_only(self):
        settings = SubnetSettings(name='foo', cidr='10.0.0.0/24')
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
        settings = SubnetSettings(**{'name': 'foo', 'cidr': '10.0.0.0/24'})
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
        settings = SubnetSettings(
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
        self.assertEqual(IPv6Mode_old.stateful.value,
                         settings.ipv6_ra_mode.value)
        self.assertEqual(IPv6Mode_old.slaac.value,
                         settings.ipv6_address_mode.value)

    def test_all_type_enums(self):
        host_routes = {'destination': '0.0.0.0/0', 'nexthop': '123.456.78.9'}
        settings = SubnetSettings(
            name='foo', cidr='10.0.0.0/24', ip_version=6,
            project_name='bar-project', start='10.0.0.2', end='10.0.0.101',
            gateway_ip='10.0.0.1', enable_dhcp=False,
            dns_nameservers=['8.8.8.8'], host_routes=[host_routes],
            destination='dest', nexthop='hop',
            ipv6_ra_mode=IPv6Mode_old.stateful,
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
        self.assertEqual(IPv6Mode.stateful.value, settings.ipv6_ra_mode.value)
        self.assertEqual(IPv6Mode.slaac.value,
                         settings.ipv6_address_mode.value)

    def test_config_all(self):
        host_routes = {'destination': '0.0.0.0/0', 'nexthop': '123.456.78.9'}
        settings = SubnetSettings(
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
        self.assertEqual(IPv6Mode.stateless.value, settings.ipv6_ra_mode.value)
        self.assertEqual(IPv6Mode.slaac.value,
                         settings.ipv6_address_mode.value)


class PortSettingsUnitTests(unittest.TestCase):
    """
    Tests the construction of the PortSettings class
    """

    def test_no_params(self):
        with self.assertRaises(PortConfigError):
            PortSettings()

    def test_empty_config(self):
        with self.assertRaises(PortConfigError):
            PortSettings(**dict())

    def test_name_only(self):
        with self.assertRaises(PortConfigError):
            PortSettings(name='foo')

    def test_config_name_only(self):
        with self.assertRaises(PortConfigError):
            PortSettings(**{'name': 'foo'})

    def test_name_netname_only(self):
        settings = PortSettings(name='foo', network_name='bar')
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
        settings = PortSettings(**{'name': 'foo', 'network_name': 'bar'})
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

    def test_all(self):
        ip_addrs = [{'subnet_name', 'foo-sub', 'ip', '10.0.0.10'}]
        allowed_address_pairs = {'10.0.0.101', '1234.5678'}

        settings = PortSettings(name='foo', network_name='bar',
                                admin_state_up=False,
                                project_name='foo-project',
                                mac_address='1234', ip_addrs=ip_addrs,
                                security_groups=['foo_grp_id'],
                                allowed_address_pairs=allowed_address_pairs,
                                opt_value='opt value', opt_name='opt name',
                                device_owner='owner',
                                device_id='device number')
        self.assertEqual('foo', settings.name)
        self.assertEqual('bar', settings.network_name)
        self.assertFalse(settings.admin_state_up)
        self.assertEqual('foo-project', settings.project_name)
        self.assertEqual('1234', settings.mac_address)
        self.assertEqual(ip_addrs, settings.ip_addrs)
        self.assertEqual(1, len(settings.security_groups))
        self.assertEqual('foo_grp_id', settings.security_groups[0])
        self.assertEqual(allowed_address_pairs, settings.allowed_address_pairs)
        self.assertEqual('opt value', settings.opt_value)
        self.assertEqual('opt name', settings.opt_name)
        self.assertEqual('owner', settings.device_owner)
        self.assertEqual('device number', settings.device_id)

    def test_config_all(self):
        ip_addrs = [{'subnet_name', 'foo-sub', 'ip', '10.0.0.10'}]
        allowed_address_pairs = {'10.0.0.101', '1234.5678'}

        settings = PortSettings(
            **{'name': 'foo', 'network_name': 'bar', 'admin_state_up': False,
               'project_name': 'foo-project', 'mac_address': '1234',
               'ip_addrs': ip_addrs, 'security_groups': ['foo_grp_id'],
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
        self.assertEqual('foo_grp_id', settings.security_groups[0])
        self.assertEqual(allowed_address_pairs, settings.allowed_address_pairs)
        self.assertEqual('opt value', settings.opt_value)
        self.assertEqual('opt name', settings.opt_name)
        self.assertEqual('owner', settings.device_owner)
        self.assertEqual('device number', settings.device_id)


class CreateNetworkSuccessTests(OSIntegrationTestCase):
    """
    Test for the CreateNetwork class defined in create_nework.py
    """

    def setUp(self):
        """
        Sets up object for test
        """
        super(self.__class__, self).__start__()

        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.net_config = openstack_tests.get_pub_net_config(
            project_name=self.os_creds.project_name,
            net_name=guid + '-pub-net', subnet_name=guid + '-pub-subnet',
            router_name=guid + '-pub-router', external_net=self.ext_net_name,
            netconf_override=self.netconf_override)

        self.neutron = neutron_utils.neutron_client(
            self.os_creds, self.os_session)

        # Initialize for cleanup
        self.net_creator = None
        self.router_creator = None

    def tearDown(self):
        """
        Cleans the network
        """
        if self.router_creator:
            self.router_creator.clean()

        if self.net_creator:
            self.net_creator.clean()

        super(self.__class__, self).__clean__()

    def test_create_network_without_router(self):
        """
        Tests the creation of an OpenStack network without a router.
        """
        # Create Network
        self.net_creator = OpenStackNetwork(
            self.os_creds, self.net_config.network_settings)
        network = self.net_creator.create()

        # Validate network was created
        self.assertTrue(neutron_utils_tests.validate_network(
            self.neutron, self.keystone,
            self.net_creator.network_settings.name, True,
            self.os_creds.project_name))

        # Validate subnets
        self.assertTrue(neutron_utils_tests.validate_subnet(
            self.neutron, network,
            self.net_creator.network_settings.subnet_settings[0].name,
            self.net_creator.network_settings.subnet_settings[0].cidr, True))

    def test_create_delete_network(self):
        """
        Tests the creation of an OpenStack network, it's deletion, then cleanup
        """
        # Create Network
        self.net_creator = OpenStackNetwork(
            self.os_creds, self.net_config.network_settings)
        self.net_creator.create()

        # Validate network was created
        self.assertTrue(neutron_utils_tests.validate_network(
            self.neutron, self.keystone,
            self.net_creator.network_settings.name, True,
            self.os_creds.project_name))

        neutron_utils.delete_network(
            self.neutron, self.net_creator.get_network())
        self.assertIsNone(neutron_utils.get_network(
            self.neutron, self.keystone,
            network_settings=self.net_creator.network_settings,
            project_name=self.os_creds.project_name))

        # This shall not throw an exception here
        self.net_creator.clean()

    def test_create_network_with_router(self):
        """
        Tests the creation of an OpenStack network with a router.
        """
        # Create Network
        self.net_creator = OpenStackNetwork(
            self.os_creds, self.net_config.network_settings)
        network = self.net_creator.create()

        # Create Router
        self.router_creator = create_router.OpenStackRouter(
            self.os_creds, self.net_config.router_settings)
        self.router_creator.create()

        # Validate network was created
        self.assertTrue(neutron_utils_tests.validate_network(
            self.neutron, self.keystone,
            self.net_creator.network_settings.name, True,
            self.os_creds.project_name))

        # Validate subnets
        self.assertTrue(neutron_utils_tests.validate_subnet(
            self.neutron, network,
            self.net_creator.network_settings.subnet_settings[0].name,
            self.net_creator.network_settings.subnet_settings[0].cidr, True))

        # Validate routers
        neutron_utils_tests.validate_router(
            self.neutron, self.keystone,
            self.router_creator.router_settings.name,
            self.os_creds.project_name, True)

        neutron_utils_tests.validate_interface_router(
            self.router_creator.get_internal_router_interface(),
            self.router_creator.get_router(),
            self.net_creator.get_network().subnets[0])

    def test_create_networks_same_name(self):
        """
        Tests the creation of an OpenStack network and ensures that the
        OpenStackNetwork object will not create a second.
        """
        # Create Network
        self.net_creator = OpenStackNetwork(
            self.os_creds, self.net_config.network_settings)
        self.net_creator.create()

        self.net_creator2 = OpenStackNetwork(
            self.os_creds, self.net_config.network_settings)
        self.net_creator2.create()

        self.assertEqual(self.net_creator.get_network().id,
                         self.net_creator2.get_network().id)

    def test_create_network_router_admin_user_to_new_project(self):
        """
        Tests the creation of an OpenStack network to the the current using
        the credentials to the admin project.
        """
        # Create Network/Subnet where the project names have been changed
        project_name = self.os_creds.project_name
        config = self.net_config.network_settings
        config.project_name = project_name
        config.subnet_settings[0].project_name = project_name

        self.net_creator = OpenStackNetwork(self.admin_os_creds, config)
        self.net_creator.create()

        retrieved_net = neutron_utils.get_network(
            self.neutron, self.keystone,
            network_name=self.net_config.network_settings.name,
            project_name=self.os_creds.project_name)

        self.assertEqual(self.net_creator.get_network().id, retrieved_net.id)

        # Initialize with actual credentials
        config.project_name = None
        config.subnet_settings[0].project_name = None
        proj_net_creator = OpenStackNetwork(self.os_creds, config)
        proj_net = proj_net_creator.create()
        self.assertEqual(retrieved_net, proj_net)

        # Create Router
        self.net_config.router_settings.project_name = project_name
        self.router_creator = create_router.OpenStackRouter(
            self.admin_os_creds, self.net_config.router_settings)
        self.router_creator.create()

        retrieved_router = neutron_utils.get_router(
            self.neutron, self.keystone,
            router_settings=self.router_creator.router_settings,
            project_name=self.os_creds.project_name)
        self.assertEqual(
            self.router_creator.get_router().id, retrieved_router.id)

    def test_create_network_router_new_user_to_admin_project(self):
        """
        Tests the creation of an OpenStack network and router with the admin
        user to the new project.
        """
        # Create Network/Subnet where the project names have been changed
        new_project_name = self.os_creds.project_name
        self.net_config.network_settings.project_name = new_project_name
        self.net_config.network_settings.subnet_settings[0].project_name = \
            new_project_name
        self.net_creator = OpenStackNetwork(
            self.admin_os_creds, self.net_config.network_settings)
        self.net_creator.create()

        retrieved_net = neutron_utils.get_network(
            self.neutron, self.keystone,
            network_settings=self.net_config.network_settings,
            project_name=self.os_creds.project_name)

        self.assertEqual(self.net_creator.get_network().id, retrieved_net.id)

        # Create Router
        self.net_config.router_settings.project_name = new_project_name
        self.router_creator = create_router.OpenStackRouter(
            self.admin_os_creds, self.net_config.router_settings)
        self.router_creator.create()

        retrieved_router = neutron_utils.get_router(
            self.neutron, self.keystone,
            router_settings=self.router_creator.router_settings,
            project_name=self.os_creds.project_name)
        self.assertEqual(
            self.router_creator.get_router().id, retrieved_router.id)


class CreateNetworkGatewayTests(OSIntegrationTestCase):
    """
    Test for the CreateNetwork class defined in create_nework.py
    """

    def setUp(self):
        """
        Sets up object for test
        """
        super(self.__class__, self).__start__()

        self.guid = self.__class__.__name__ + '-' + str(uuid.uuid4())

        self.neutron = neutron_utils.neutron_client(
            self.os_creds, self.os_session)

        self.ip_prfx = '10.1.0.'

        # Initialize for cleanup
        self.net_creator = None

    def tearDown(self):
        """
        Cleans the network
        """
        if self.net_creator:
            self.net_creator.clean()

        super(self.__class__, self).__clean__()

    def test_create_subnet_default_gateway_ip(self):
        """
        Tests the creation of an OpenStack network with a subnet that has a
        default value assigned to the gateway IP.
        """
        # Create Network
        subnet_config = SubnetConfig(
            name=self.guid + '-subnet', cidr=self.ip_prfx + '0/24')
        net_config = NetworkConfig(
            name=self.guid + '-net', subnets=[subnet_config])
        self.net_creator = OpenStackNetwork(
            self.os_creds, net_config)
        out_net = self.net_creator.create()

        # Validate network was created
        self.assertTrue(neutron_utils_tests.validate_network(
            self.neutron, self.keystone,
            self.net_creator.network_settings.name, True,
            self.os_creds.project_name))

        # Validate subnets
        self.assertTrue(neutron_utils_tests.validate_subnet(
            self.neutron, out_net,
            self.net_creator.network_settings.subnet_settings[0].name,
            self.net_creator.network_settings.subnet_settings[0].cidr, True))

        self.assertEqual(self.ip_prfx + '1', out_net.subnets[0].gateway_ip)

    def test_create_subnet_valid_gateway_ip(self):
        """
        Tests the creation of an OpenStack network with a subnet that has a
        valid value assigned to the gateway IP.
        """
        # Create Network
        subnet_config = SubnetConfig(
            name=self.guid + '-subnet', cidr=self.ip_prfx + '0/24',
            gateway_ip=self.ip_prfx + '2')
        net_config = NetworkConfig(
            name=self.guid + '-net', subnets=[subnet_config])
        self.net_creator = OpenStackNetwork(
            self.os_creds, net_config)
        out_net = self.net_creator.create()

        # Validate network was created
        self.assertTrue(neutron_utils_tests.validate_network(
            self.neutron, self.keystone,
            self.net_creator.network_settings.name, True,
            self.os_creds.project_name))

        # Validate subnets
        self.assertTrue(neutron_utils_tests.validate_subnet(
            self.neutron, out_net,
            self.net_creator.network_settings.subnet_settings[0].name,
            self.net_creator.network_settings.subnet_settings[0].cidr, True))

        self.assertEqual(self.ip_prfx + '2', out_net.subnets[0].gateway_ip)

    def test_create_subnet_no_gateway(self):
        """
        Tests the creation of an OpenStack network with a subnet that has a
        valid value assigned to the gateway IP.
        """
        # Create Network
        subnet_config = SubnetConfig(
            name=self.guid + '-subnet', cidr=self.ip_prfx + '0/24',
            gateway_ip='none')
        net_config = NetworkConfig(
            name=self.guid + '-net', subnets=[subnet_config])
        self.net_creator = OpenStackNetwork(
            self.os_creds, net_config)
        out_net = self.net_creator.create()

        # Validate network was created
        self.assertTrue(neutron_utils_tests.validate_network(
            self.neutron, self.keystone,
            self.net_creator.network_settings.name, True,
            self.os_creds.project_name))

        # Validate subnets
        self.assertTrue(neutron_utils_tests.validate_subnet(
            self.neutron, out_net,
            self.net_creator.network_settings.subnet_settings[0].name,
            self.net_creator.network_settings.subnet_settings[0].cidr, True))

        self.assertIsNone(out_net.subnets[0].gateway_ip)

    def test_create_subnet_invalid_gateway_ip(self):
        """
        Tests the creation of an OpenStack network with a subnet that has an
        invalid value assigned to the gateway IP.
        """
        # Create Network
        subnet_config = SubnetConfig(
            name=self.guid + '-subnet', cidr=self.ip_prfx + '0/24',
            gateway_ip='foo')
        net_config = NetworkConfig(
            name=self.guid + '-net', subnets=[subnet_config])
        self.net_creator = OpenStackNetwork(
            self.os_creds, net_config)

        with self.assertRaises(BadRequest):
            self.net_creator.create()


class CreateNetworkIPv6Tests(OSIntegrationTestCase):
    """
    Test for the CreateNetwork class defined in create_nework.py when
    """

    def setUp(self):
        """
        Sets up object for test
        """
        super(self.__class__, self).__start__()

        self.guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.neutron = neutron_utils.neutron_client(
            self.os_creds, self.os_session)

        # Initialize for cleanup
        self.net_creator = None

    def tearDown(self):
        """
        Cleans the network
        """
        if self.net_creator:
            self.net_creator.clean()

        super(self.__class__, self).__clean__()

    def test_create_network_one_ipv6_subnet(self):
        """
        Tests the creation of an OpenStack network without a router.
        """
        # Create Network
        subnet_settings = SubnetConfig(
            name=self.guid + '-subnet', cidr='1:1:0:0:0:0:0:0/64',
            ip_version=6)
        network_settings = NetworkConfig(
            name=self.guid + '-net', subnet_settings=[subnet_settings])

        self.net_creator = OpenStackNetwork(self.os_creds, network_settings)
        self.net_creator.create()

        # Validate network was created
        self.assertTrue(neutron_utils_tests.validate_network(
            self.neutron, self.keystone,
            self.net_creator.network_settings.name, True,
            self.os_creds.project_name))

        network = self.net_creator.get_network()
        self.assertEqual(1, len(network.subnets))
        subnet = network.subnets[0]

        self.assertEqual(network.id, subnet.network_id)
        self.assertEqual(subnet_settings.name, subnet.name)
        self.assertEqual('1:1::/64', subnet.cidr)
        self.assertEqual(6, subnet.ip_version)
        self.assertEqual(0, len(subnet.dns_nameservers))

    def test_create_network_ipv4_ipv6_subnet(self):
        """
        Tests the creation of an OpenStack network without a router.
        """
        # Create Network
        subnet4_settings = SubnetConfig(
            name=self.guid + '-subnet4', cidr='10.0.1.0/24', ip_version=4)
        subnet6_settings = SubnetConfig(
            name=self.guid + '-subnet6', cidr='1:1:0:0:0:0:0:0/64',
            ip_version=6)

        network_settings = NetworkConfig(
            name=self.guid + '-net',
            subnet_settings=[subnet4_settings, subnet6_settings])

        self.net_creator = OpenStackNetwork(self.os_creds, network_settings)
        self.net_creator.create()

        # Validate network was created
        network = self.net_creator.get_network()
        self.assertEqual(2, len(network.subnets))

        subnet4 = None
        subnet6 = None
        for subnet in network.subnets:
            if subnet.name == subnet4_settings.name:
                subnet4 = subnet
            if subnet.name == subnet6_settings.name:
                subnet6 = subnet

        # Validate IPv4 subnet
        self.assertEqual(network.id, subnet4.network_id)
        self.assertEqual(subnet4_settings.name, subnet4.name)
        self.assertEqual(subnet4_settings.cidr, subnet4.cidr)
        self.assertEqual(4, subnet4.ip_version)
        self.assertEqual(0, len(subnet4.dns_nameservers))

        # Validate IPv6 subnet
        self.assertEqual(network.id, subnet6.network_id)
        self.assertEqual(subnet6_settings.name, subnet6.name)
        self.assertEqual('1:1::/64', subnet6.cidr)
        self.assertEqual(6, subnet6.ip_version)
        self.assertEqual(0, len(subnet6.dns_nameservers))


class CreateNetworkTypeTests(OSComponentTestCase):
    """
    Test for the CreateNetwork class defined in create_nework.py for testing
    creating networks of different types
    """

    def setUp(self):
        """
        Sets up object for test
        """
        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.net_config = openstack_tests.get_pub_net_config(
            project_name=self.os_creds.project_name,
            net_name=guid + '-pub-net', subnet_name=guid + '-pub-subnet')

        self.neutron = neutron_utils.neutron_client(
            self.os_creds, self.os_session)
        self.keystone = keystone_utils.keystone_client(
            self.os_creds, self.os_session)

        # Initialize for cleanup
        self.net_creator = None

    def tearDown(self):
        """
        Cleans the network
        """
        if self.net_creator:
            self.net_creator.clean()

        super(self.__class__, self).__clean__()

    def test_create_network_type_vlan(self):
        """
        Tests the creation of an OpenStack network of type vlan.
        """
        # Create Network
        network_type = 'vlan'
        net_settings = NetworkConfig(
            name=self.net_config.network_settings.name,
            subnet_settings=self.net_config.network_settings.subnet_settings,
            network_type=network_type)

        # When setting the network_type, creds must be admin
        self.net_creator = OpenStackNetwork(self.os_creds, net_settings)
        network = self.net_creator.create()

        # Validate network was created
        self.assertTrue(neutron_utils_tests.validate_network(
            self.neutron, self.keystone, net_settings.name, True,
            self.os_creds.project_name))

        self.assertEquals(network_type, network.type)

    def test_create_network_type_vlan_with_physical_net_and_seg_id(self):
        """
        Tests the creation of an OpenStack network of type vlan with
        specified physical network and segmentation id.
        """
        # Create Network
        network_type = 'vlan'

        # The two values must be variable to work on all OpenStack pods
        physical_network = 'datacentre'
        segmentation_id = 2366

        net_settings = NetworkConfig(
            name=self.net_config.network_settings.name,
            subnet_settings=self.net_config.network_settings.subnet_settings,
            network_type=network_type,
            physical_network=physical_network,
            segmentation_id=segmentation_id)

        # When setting the network_type, creds must be admin
        self.net_creator = OpenStackNetwork(self.os_creds, net_settings)
        network = self.net_creator.create()

        # Validate network was created
        self.assertTrue(neutron_utils_tests.validate_network(
            self.neutron, self.keystone, net_settings.name, True,
            self.os_creds.project_name))

        self.assertEquals(network_type, network.type)

    def test_create_network_type_vxlan(self):
        """
        Tests the creation of an OpenStack network of type vxlan.
        """
        # Create Network
        network_type = 'vxlan'
        net_settings = NetworkConfig(
            name=self.net_config.network_settings.name,
            subnet_settings=self.net_config.network_settings.subnet_settings,
            network_type=network_type)

        # When setting the network_type, creds must be admin
        self.net_creator = OpenStackNetwork(self.os_creds, net_settings)
        network = self.net_creator.create()

        # Validate network was created
        self.assertTrue(neutron_utils_tests.validate_network(
            self.neutron, self.keystone, net_settings.name, True,
            self.os_creds.project_name))

        self.assertEqual(network_type, network.type)

    def test_create_network_type_flat(self):
        """
        Tests the creation of an OpenStack network of type flat.
        """
        # Create Network
        network_type = 'flat'

        # This value must be variable to work on all OpenStack pods
        physical_network = 'datacentre'

        net_settings = NetworkConfig(
            name=self.net_config.network_settings.name,
            subnet_settings=self.net_config.network_settings.subnet_settings,
            network_type=network_type, physical_network=physical_network)
        self.net_creator = OpenStackNetwork(self.os_creds, net_settings)
        network = self.net_creator.create()

        # Validate network was created
        self.assertTrue(neutron_utils_tests.validate_network(
            self.neutron, self.keystone, net_settings.name, True,
            self.os_creds.project_name))

        self.assertEquals(network_type, network.type)

    def test_create_network_type_foo(self):
        """
        Tests the creation of an OpenStack network of type foo which should
        raise an exception.
        """
        # Create Network
        network_type = 'foo'
        net_settings = NetworkConfig(
            name=self.net_config.network_settings.name,
            subnet_settings=self.net_config.network_settings.subnet_settings,
            network_type=network_type)
        self.net_creator = OpenStackNetwork(self.os_creds, net_settings)
        with self.assertRaises(Exception):
            self.net_creator.create()


class CreateMultipleNetworkTests(OSIntegrationTestCase):
    """
    Test for the CreateNetwork class and how it interacts with networks
    groups within other projects with the same name
    """

    def setUp(self):
        """
        Sets up object for test
        """
        super(self.__class__, self).__start__()

        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.net_config = openstack_tests.get_pub_net_config(
            project_name=self.os_creds.project_name,
            net_name=guid + '-pub-net', subnet_name=guid + '-pub-subnet')

        self.neutron = neutron_utils.neutron_client(
            self.os_creds, self.os_session)

        # Initialize for cleanup
        self.admin_net_creator = None
        self.proj_net_creator = None

    def tearDown(self):
        """
        Cleans the network
        """
        if self.admin_net_creator:
            self.admin_net_creator.clean()
        if self.proj_net_creator:
            self.proj_net_creator.clean()

        super(self.__class__, self).__clean__()

    def test_network_same_name_diff_proj(self):
        """
        Tests the creation of an OpenStackNetwork with the same name
        within a different project/tenant when not configured but implied by
        the OSCreds.
        """
        # Create Network

        self.admin_net_creator = OpenStackNetwork(
            self.admin_os_creds, self.net_config.network_settings)
        self.admin_net_creator.create()

        self.proj_net_creator = OpenStackNetwork(
            self.os_creds, self.net_config.network_settings)
        self.proj_net_creator.create()

        self.assertNotEqual(
            self.admin_net_creator.get_network().id,
            self.proj_net_creator.get_network().id)

        admin_creator2 = OpenStackNetwork(
            self.admin_os_creds, self.net_config.network_settings)
        admin_creator2.create()
        self.assertEqual(
            self.admin_net_creator.get_network(), admin_creator2.get_network())

        proj_creator2 = OpenStackNetwork(
            self.os_creds, self.net_config.network_settings)
        proj_creator2.create()
        self.assertEqual(self.proj_net_creator.get_network(),
                         proj_creator2.get_network())

    def test_network_create_by_admin_to_different_project(self):
        """
        Tests the creation of an OpenStackNetwork by the admin user and
        initialize again with tenant credentials.
        """
        # Create Network

        net_settings = self.net_config.network_settings

        net_settings.project_name = self.os_creds.project_name

        self.admin_net_creator = OpenStackNetwork(
            self.admin_os_creds, net_settings)
        self.admin_net_creator.create()

        self.proj_net_creator = OpenStackNetwork(
            self.os_creds, self.net_config.network_settings)
        self.proj_net_creator.create()

        self.assertEqual(
            self.admin_net_creator.get_network().id,
            self.proj_net_creator.get_network().id)
