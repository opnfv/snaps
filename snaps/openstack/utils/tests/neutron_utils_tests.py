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
import uuid

from neutronclient.common.exceptions import NotFound, BadRequest

from snaps.config.network import NetworkConfig, SubnetConfig, PortConfig
from snaps.config.security_group import (
    SecurityGroupConfig, SecurityGroupRuleConfig, Direction)
from snaps.openstack.tests import openstack_tests
from snaps.openstack.tests import validation_utils
from snaps.openstack.tests.os_source_file_test import OSComponentTestCase
from snaps.openstack.utils import keystone_utils
from snaps.openstack.utils import neutron_utils
from snaps.openstack.utils.neutron_utils import NeutronException

__author__ = 'spisarski'

ip_1 = '10.55.1.100'
ip_2 = '10.55.1.200'


class NeutronSmokeTests(OSComponentTestCase):
    """
    Tests to ensure that the neutron client can communicate with the cloud
    """

    def test_neutron_connect_success(self):
        """
        Tests to ensure that the proper credentials can connect.
        """
        neutron = neutron_utils.neutron_client(self.os_creds, self.os_session)

        networks = neutron.list_networks()

        found = False
        networks = networks.get('networks')
        for network in networks:
            if network.get('name') == self.ext_net_name:
                found = True
        self.assertTrue(found)

    def test_neutron_connect_fail(self):
        """
        Tests to ensure that the improper credentials cannot connect.
        """
        from snaps.openstack.os_credentials import OSCreds

        with self.assertRaises(Exception):
            neutron = neutron_utils.neutron_client(
                OSCreds(username='user', password='pass', auth_url='url',
                        project_name='project'))
            neutron.list_networks()

    def test_retrieve_ext_network_name(self):
        """
        Tests the neutron_utils.get_external_network_names to ensure the
        configured self.ext_net_name is contained within the returned list
        :return:
        """
        neutron = neutron_utils.neutron_client(self.os_creds, self.os_session)
        ext_networks = neutron_utils.get_external_networks(neutron)
        found = False
        for network in ext_networks:
            if network.name == self.ext_net_name:
                found = True
                break
        self.assertTrue(found)


class NeutronUtilsNetworkTests(OSComponentTestCase):
    """
    Test for creating networks via neutron_utils.py
    """

    def setUp(self):
        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.port_name = str(guid) + '-port'
        self.neutron = neutron_utils.neutron_client(
            self.os_creds, self.os_session)
        self.keystone = keystone_utils.keystone_client(
            self.os_creds, self.os_session)
        self.network = None
        self.net_config = openstack_tests.get_pub_net_config(
            project_name=self.os_creds.project_name,
            net_name=guid + '-pub-net')

    def tearDown(self):
        """
        Cleans the remote OpenStack objects
        """
        if self.network:
            neutron_utils.delete_network(self.neutron, self.network)

        super(self.__class__, self).__clean__()

    def test_create_network(self):
        """
        Tests the neutron_utils.create_network() function
        """
        self.network = neutron_utils.create_network(
            self.neutron, self.os_creds, self.net_config.network_settings)
        self.assertEqual(self.net_config.network_settings.name,
                         self.network.name)
        self.assertTrue(validate_network(
            self.neutron, self.keystone,
            self.net_config.network_settings.name, True,
            self.os_creds.project_name))
        self.assertEqual(len(self.net_config.network_settings.subnet_settings),
                         len(self.network.subnets))

    def test_create_network_empty_name(self):
        """
        Tests the neutron_utils.create_network() function with an empty
        network name
        """
        with self.assertRaises(Exception):
            self.network = neutron_utils.create_network(
                self.neutron, self.os_creds,
                network_settings=NetworkConfig(name=''))

    def test_create_network_null_name(self):
        """
        Tests the neutron_utils.create_network() function when the network
        name is None
        """
        with self.assertRaises(Exception):
            self.network = neutron_utils.create_network(
                self.neutron, self.os_creds,
                network_settings=NetworkConfig())


class NeutronUtilsSubnetTests(OSComponentTestCase):
    """
    Test for creating networks with subnets via neutron_utils.py
    """

    def setUp(self):
        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.port_name = str(guid) + '-port'
        self.neutron = neutron_utils.neutron_client(
            self.os_creds, self.os_session)
        self.keystone = keystone_utils.keystone_client(
            self.os_creds, self.os_session)
        self.network = None
        self.net_config = openstack_tests.get_pub_net_config(
            project_name=self.os_creds.project_name,
            net_name=guid + '-pub-net', subnet_name=guid + '-pub-subnet',
            external_net=self.ext_net_name)

    def tearDown(self):
        """
        Cleans the remote OpenStack objects
        """
        if self.network:
            try:
                neutron_utils.delete_network(self.neutron, self.network)
            except:
                pass

        super(self.__class__, self).__clean__()

    def test_create_subnet(self):
        """
        Tests the neutron_utils.create_network() function
        """
        self.network = neutron_utils.create_network(
            self.neutron, self.os_creds, self.net_config.network_settings)
        self.assertEqual(self.net_config.network_settings.name,
                         self.network.name)
        self.assertTrue(validate_network(
            self.neutron, self.keystone,
            self.net_config.network_settings.name, True,
            self.os_creds.project_name))

        subnet_setting = self.net_config.network_settings.subnet_settings[0]
        self.assertTrue(validate_subnet(
            self.neutron, self.network, subnet_setting.name,
            subnet_setting.cidr, True))

        subnet_query1 = neutron_utils.get_subnet(
            self.neutron, self.network, subnet_name=subnet_setting.name)
        self.assertEqual(self.network.subnets[0], subnet_query1)

        subnet_query2 = neutron_utils.get_subnets_by_network(self.neutron,
                                                             self.network)
        self.assertIsNotNone(subnet_query2)
        self.assertEqual(1, len(subnet_query2))
        self.assertEqual(self.network.subnets[0], subnet_query2[0])

        subnet_query3 = neutron_utils.get_subnet_by_name(
            self.neutron, self.keystone, subnet_setting.name,
            self.os_creds.project_name)
        self.assertIsNotNone(subnet_query3)
        self.assertEqual(self.network.subnets[0], subnet_query3)

    def test_create_subnet_null_name(self):
        """
        Tests the neutron_utils.create_neutron_subnet() function for an
        Exception when the subnet name is None
        """
        self.network = neutron_utils.create_network(
            self.neutron, self.os_creds, self.net_config.network_settings)
        self.assertEqual(self.net_config.network_settings.name,
                         self.network.name)
        self.assertTrue(validate_network(
            self.neutron, self.keystone,
            self.net_config.network_settings.name, True,
            self.os_creds.project_name))

        with self.assertRaises(Exception):
            SubnetConfig(cidr=self.net_config.subnet_cidr)

    def test_create_subnet_empty_name(self):
        """
        Tests the neutron_utils.create_network() function with an empty
        name
        """
        self.network = neutron_utils.create_network(
            self.neutron, self.os_creds, self.net_config.network_settings)
        self.assertEqual(self.net_config.network_settings.name,
                         self.network.name)
        self.assertTrue(validate_network(
            self.neutron, self.keystone,
            self.net_config.network_settings.name, True,
            self.os_creds.project_name))

        subnet_setting = self.net_config.network_settings.subnet_settings[0]
        self.assertTrue(validate_subnet(
            self.neutron, self.network, subnet_setting.name,
            subnet_setting.cidr, True))
        self.assertFalse(validate_subnet(
            self.neutron, self.network, '', subnet_setting.cidr, True))

        subnet_query1 = neutron_utils.get_subnet(
            self.neutron, self.network, subnet_name=subnet_setting.name)
        self.assertEqual(self.network.subnets[0], subnet_query1)

        subnet_query2 = neutron_utils.get_subnets_by_network(
            self.neutron, self.network)
        self.assertIsNotNone(subnet_query2)
        self.assertEqual(1, len(subnet_query2))
        self.assertEqual(self.network.subnets[0], subnet_query2[0])

    def test_create_subnet_null_cidr(self):
        """
        Tests the neutron_utils.create_neutron_subnet() function for an
        Exception when the subnet CIDR value is None
        """
        self.net_config.network_settings.subnet_settings[0].cidr = None
        with self.assertRaises(Exception):
            self.network = neutron_utils.create_network(
                self.neutron, self.os_creds, self.net_config.network_settings)

    def test_create_subnet_empty_cidr(self):
        """
        Tests the neutron_utils.create_neutron_subnet() function for an
        Exception when the subnet CIDR value is empty
        """
        self.net_config.network_settings.subnet_settings[0].cidr = ''
        with self.assertRaises(Exception):
            self.network = neutron_utils.create_network(
                self.neutron, self.os_creds, self.net_config.network_settings)


class NeutronUtilsIPv6Tests(OSComponentTestCase):
    """
    Test for creating IPv6 networks with subnets via neutron_utils.py
    """

    def setUp(self):
        self.guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.neutron = neutron_utils.neutron_client(
            self.os_creds, self.os_session)
        self.network = None

    def tearDown(self):
        """
        Cleans the remote OpenStack objects
        """
        if self.network:
            try:
                neutron_utils.delete_network(self.neutron, self.network)
            except:
                pass

        super(self.__class__, self).__clean__()

    def test_create_network_slaac(self):
        """
        Tests the neutron_utils.create_network() with an IPv6 subnet where DHCP
        is True and IPv6 modes are slaac
        """
        sub_setting = SubnetConfig(
            name=self.guid + '-subnet', cidr='1:1:0:0:0:0:0:0/64',
            ip_version=6, dns_nameservers=['2620:0:ccc:0:0:0:0:2'],
            gateway_ip='1:1:0:0:0:0:0:1', start='1:1::ff', end='1:1::ffff',
            enable_dhcp=True, ipv6_ra_mode='slaac', ipv6_address_mode='slaac')
        self.network_settings = NetworkConfig(
            name=self.guid + '-net', subnet_settings=[sub_setting])

        self.network = neutron_utils.create_network(
            self.neutron, self.os_creds, self.network_settings)
        self.assertEqual(self.network_settings.name, self.network.name)

        subnet_settings = self.network_settings.subnet_settings[0]
        self.assertEqual(1, len(self.network.subnets))
        subnet = self.network.subnets[0]

        self.assertEqual(self.network.id, subnet.network_id)
        self.assertEqual(subnet_settings.name, subnet.name)
        self.assertEqual(subnet_settings.start, subnet.start)
        self.assertEqual(subnet_settings.end, subnet.end)
        self.assertEqual('1:1::/64', subnet.cidr)
        self.assertEqual(6, subnet.ip_version)
        self.assertEqual(1, len(subnet.dns_nameservers))
        self.assertEqual(
            sub_setting.dns_nameservers[0], subnet.dns_nameservers[0])
        self.assertTrue(subnet.enable_dhcp)
        self.assertEqual(
            subnet_settings.ipv6_ra_mode.value, subnet.ipv6_ra_mode)
        self.assertEqual(
            subnet_settings.ipv6_address_mode.value, subnet.ipv6_address_mode)

    def test_create_network_stateful(self):
        """
        Tests the neutron_utils.create_network() with an IPv6 subnet where DHCP
        is True and IPv6 modes are stateful
        """
        sub_setting = SubnetConfig(
            name=self.guid + '-subnet', cidr='1:1:0:0:0:0:0:0/64',
            ip_version=6, dns_nameservers=['2620:0:ccc:0:0:0:0:2'],
            gateway_ip='1:1:0:0:0:0:0:1', start='1:1::ff', end='1:1::ffff',
            enable_dhcp=True, ipv6_ra_mode='dhcpv6-stateful',
            ipv6_address_mode='dhcpv6-stateful')
        self.network_settings = NetworkConfig(
            name=self.guid + '-net', subnet_settings=[sub_setting])

        self.network = neutron_utils.create_network(
            self.neutron, self.os_creds, self.network_settings)

        self.assertEqual(self.network_settings.name, self.network.name)

        subnet_settings = self.network_settings.subnet_settings[0]
        self.assertEqual(1, len(self.network.subnets))
        subnet = self.network.subnets[0]

        self.assertEqual(self.network.id, subnet.network_id)
        self.assertEqual(subnet_settings.name, subnet.name)
        self.assertEqual(subnet_settings.start, subnet.start)
        self.assertEqual(subnet_settings.end, subnet.end)
        self.assertEqual('1:1::/64', subnet.cidr)
        self.assertEqual(6, subnet.ip_version)
        self.assertEqual(1, len(subnet.dns_nameservers))
        self.assertEqual(
            sub_setting.dns_nameservers[0], subnet.dns_nameservers[0])
        self.assertTrue(subnet.enable_dhcp)
        self.assertEqual(
            subnet_settings.ipv6_ra_mode.value, subnet.ipv6_ra_mode)
        self.assertEqual(
            subnet_settings.ipv6_address_mode.value, subnet.ipv6_address_mode)

    def test_create_network_stateless(self):
        """
        Tests the neutron_utils.create_network() when DHCP is enabled and
        the RA and address modes are both 'slaac'
        """
        sub_setting = SubnetConfig(
            name=self.guid + '-subnet', cidr='1:1:0:0:0:0:0:0/64',
            ip_version=6, dns_nameservers=['2620:0:ccc:0:0:0:0:2'],
            gateway_ip='1:1:0:0:0:0:0:1', start='1:1::ff', end='1:1::ffff',
            enable_dhcp=True, ipv6_ra_mode='dhcpv6-stateless',
            ipv6_address_mode='dhcpv6-stateless')
        self.network_settings = NetworkConfig(
            name=self.guid + '-net', subnet_settings=[sub_setting])

        self.network = neutron_utils.create_network(
            self.neutron, self.os_creds, self.network_settings)

        self.assertEqual(self.network_settings.name, self.network.name)

        subnet_settings = self.network_settings.subnet_settings[0]
        self.assertEqual(1, len(self.network.subnets))
        subnet = self.network.subnets[0]

        self.assertEqual(self.network.id, subnet.network_id)
        self.assertEqual(subnet_settings.name, subnet.name)
        self.assertEqual(subnet_settings.start, subnet.start)
        self.assertEqual(subnet_settings.end, subnet.end)
        self.assertEqual('1:1::/64', subnet.cidr)
        self.assertEqual(6, subnet.ip_version)
        self.assertEqual(1, len(subnet.dns_nameservers))
        self.assertEqual(
            sub_setting.dns_nameservers[0], subnet.dns_nameservers[0])
        self.assertTrue(subnet.enable_dhcp)
        self.assertEqual(
            subnet_settings.ipv6_ra_mode.value, subnet.ipv6_ra_mode)
        self.assertEqual(
            subnet_settings.ipv6_address_mode.value, subnet.ipv6_address_mode)

    def test_create_network_no_dhcp_slaac(self):
        """
        Tests the neutron_utils.create_network() for a BadRequest when
        DHCP is not enabled and the RA and address modes are both 'slaac'
        """
        sub_setting = SubnetConfig(
            name=self.guid + '-subnet', cidr='1:1:0:0:0:0:0:0/64',
            ip_version=6, dns_nameservers=['2620:0:ccc:0:0:0:0:2'],
            gateway_ip='1:1:0:0:0:0:0:1', start='1:1::ff', end='1:1::ffff',
            enable_dhcp=False, ipv6_ra_mode='slaac', ipv6_address_mode='slaac')
        self.network_settings = NetworkConfig(
            name=self.guid + '-net', subnet_settings=[sub_setting])

        with self.assertRaises(BadRequest):
            self.network = neutron_utils.create_network(
                self.neutron, self.os_creds, self.network_settings)

    def test_create_network_invalid_start_ip(self):
        """
        Tests the neutron_utils.create_network() that contains one IPv6 subnet
        with an invalid start IP to ensure Neutron assigns it the smallest IP
        possible
        """
        sub_setting = SubnetConfig(
            name=self.guid + '-subnet', cidr='1:1::/48', ip_version=6,
            start='foo')
        self.network_settings = NetworkConfig(
            name=self.guid + '-net', subnet_settings=[sub_setting])

        self.network = neutron_utils.create_network(
            self.neutron, self.os_creds, self.network_settings)

        self.assertEqual('1:1::2', self.network.subnets[0].start)
        self.assertEqual(
            '1:1:0:ffff:ffff:ffff:ffff:ffff', self.network.subnets[0].end)

    def test_create_network_invalid_end_ip(self):
        """
        Tests the neutron_utils.create_network() that contains one IPv6 subnet
        with an invalid end IP to ensure Neutron assigns it the largest IP
        possible
        """
        sub_setting = SubnetConfig(
            name=self.guid + '-subnet', cidr='1:1::/48', ip_version=6,
            end='bar')
        self.network_settings = NetworkConfig(
            name=self.guid + '-net', subnet_settings=[sub_setting])

        self.network = neutron_utils.create_network(
            self.neutron, self.os_creds, self.network_settings)

        self.assertEqual('1:1::2', self.network.subnets[0].start)
        self.assertEqual(
            '1:1:0:ffff:ffff:ffff:ffff:ffff', self.network.subnets[0].end)

    def test_create_network_with_bad_cidr(self):
        """
        Tests the neutron_utils.create_network() for a BadRequest when
        the subnet CIDR is invalid
        """
        sub_setting = SubnetConfig(
            name=self.guid + '-subnet', cidr='1:1:1:/48', ip_version=6)
        self.network_settings = NetworkConfig(
            name=self.guid + '-net', subnet_settings=[sub_setting])

        with self.assertRaises(BadRequest):
            self.network = neutron_utils.create_network(
                self.neutron, self.os_creds, self.network_settings)

    def test_create_network_invalid_gateway_ip(self):
        """
        Tests the neutron_utils.create_network() for a BadRequest when
        the subnet gateway IP is invalid
        """
        sub_setting = SubnetConfig(
            name=self.guid + '-subnet', cidr='1:1::/48', ip_version=6,
            gateway_ip='192.168.0.1')
        self.network_settings = NetworkConfig(
            name=self.guid + '-net', subnet_settings=[sub_setting])

        with self.assertRaises(BadRequest):
            self.network = neutron_utils.create_network(
                self.neutron, self.os_creds, self.network_settings)

    def test_create_network_with_bad_dns(self):
        """
        Tests the neutron_utils.create_network() for a BadRequest when
        the DNS IP is invalid
        """
        sub_setting = SubnetConfig(
            name=self.guid + '-subnet', cidr='1:1::/48', ip_version=6,
            dns_nameservers=['foo'])
        self.network_settings = NetworkConfig(
            name=self.guid + '-net', subnet_settings=[sub_setting])

        with self.assertRaises(BadRequest):
            self.network = neutron_utils.create_network(
                    self.neutron, self.os_creds, self.network_settings)


class NeutronUtilsRouterTests(OSComponentTestCase):
    """
    Test for creating routers via neutron_utils.py
    """

    def setUp(self):
        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.port_name = str(guid) + '-port'
        self.neutron = neutron_utils.neutron_client(
            self.os_creds, self.os_session)
        self.keystone = keystone_utils.keystone_client(
            self.os_creds, self.os_session)
        self.network = None
        self.port = None
        self.router = None
        self.interface_router = None
        self.net_config = openstack_tests.get_pub_net_config(
            project_name=self.os_creds.project_name,
            net_name=guid + '-pub-net', subnet_name=guid + '-pub-subnet',
            router_name=guid + '-pub-router', external_net=self.ext_net_name)

    def tearDown(self):
        """
        Cleans the remote OpenStack objects
        """
        if self.interface_router:
            neutron_utils.remove_interface_router(
                self.neutron, self.router, self.network.subnets[0])

        if self.router:
            try:
                neutron_utils.delete_router(self.neutron, self.router)
                validate_router(
                    self.neutron, self.keystone, self.router.name,
                    self.os_creds.project_name, False)
            except:
                pass

        if self.port:
            try:
                neutron_utils.delete_port(self.neutron, self.port)
            except:
                pass

        if self.network:
            neutron_utils.delete_network(self.neutron, self.network)

        super(self.__class__, self).__clean__()

    def test_create_router_simple(self):
        """
        Tests the neutron_utils.create_router()
        """
        self.router = neutron_utils.create_router(
            self.neutron, self.os_creds, self.net_config.router_settings)
        validate_router(
            self.neutron, self.keystone, self.net_config.router_settings.name,
            self.os_creds.project_name, True)

    def test_create_router_with_public_interface(self):
        """
        Tests the neutron_utils.create_router() function with a pubic interface
        """
        subnet_setting = self.net_config.network_settings.subnet_settings[0]
        self.net_config = openstack_tests.OSNetworkConfig(
            self.os_creds.project_name, self.net_config.network_settings.name,
            subnet_setting.name, subnet_setting.cidr,
            self.net_config.router_settings.name, self.ext_net_name)
        self.router = neutron_utils.create_router(
            self.neutron, self.os_creds, self.net_config.router_settings)
        validate_router(
            self.neutron, self.keystone, self.net_config.router_settings.name,
            self.os_creds.project_name, True)

        ext_net = neutron_utils.get_network(
            self.neutron, self.keystone, network_name=self.ext_net_name)
        self.assertEqual(self.router.external_network_id, ext_net.id)

    def test_add_interface_router(self):
        """
        Tests the neutron_utils.add_interface_router() function
        """
        self.network = neutron_utils.create_network(
            self.neutron, self.os_creds, self.net_config.network_settings)
        self.assertEqual(self.net_config.network_settings.name,
                         self.network.name)
        self.assertTrue(validate_network(
            self.neutron, self.keystone,
            self.net_config.network_settings.name, True,
            self.os_creds.project_name))

        subnet_setting = self.net_config.network_settings.subnet_settings[0]
        self.assertTrue(validate_subnet(
            self.neutron, self.network, subnet_setting.name,
            subnet_setting.cidr, True))

        self.router = neutron_utils.create_router(
            self.neutron, self.os_creds, self.net_config.router_settings)
        validate_router(
            self.neutron, self.keystone, self.net_config.router_settings.name,
            self.os_creds.project_name, True)

        self.interface_router = neutron_utils.add_interface_router(
            self.neutron, self.router, self.network.subnets[0])
        validate_interface_router(self.interface_router, self.router,
                                  self.network.subnets[0])

    def test_add_interface_router_null_router(self):
        """
        Tests the neutron_utils.add_interface_router() function for an
        Exception when the router value is None
        """
        self.network = neutron_utils.create_network(
            self.neutron, self.os_creds, self.net_config.network_settings)
        self.assertEqual(self.net_config.network_settings.name,
                         self.network.name)
        self.assertTrue(validate_network(
            self.neutron, self.keystone,
            self.net_config.network_settings.name, True,
            self.os_creds.project_name))

        subnet_setting = self.net_config.network_settings.subnet_settings[0]
        self.assertTrue(validate_subnet(
            self.neutron, self.network, subnet_setting.name,
            subnet_setting.cidr, True))

        with self.assertRaises(NeutronException):
            self.interface_router = neutron_utils.add_interface_router(
                self.neutron, self.router, self.network.subnets[0])

    def test_add_interface_router_null_subnet(self):
        """
        Tests the neutron_utils.add_interface_router() function for an
        Exception when the subnet value is None
        """
        self.network = neutron_utils.create_network(
            self.neutron, self.os_creds, self.net_config.network_settings)
        self.assertEqual(self.net_config.network_settings.name,
                         self.network.name)
        self.assertTrue(validate_network(
            self.neutron, self.keystone,
            self.net_config.network_settings.name, True,
            self.os_creds.project_name))

        self.router = neutron_utils.create_router(
            self.neutron, self.os_creds, self.net_config.router_settings)
        validate_router(
            self.neutron, self.keystone, self.net_config.router_settings.name,
            self.os_creds.project_name, True)

        with self.assertRaises(NeutronException):
            self.interface_router = neutron_utils.add_interface_router(
                self.neutron, self.router, None)

    def test_add_interface_router_missing_subnet(self):
        """
        Tests the neutron_utils.add_interface_router() function for an
        Exception when the subnet object has been deleted
        """
        self.network = neutron_utils.create_network(
            self.neutron, self.os_creds, self.net_config.network_settings)
        self.assertEqual(self.net_config.network_settings.name,
                         self.network.name)
        self.assertTrue(validate_network(
            self.neutron, self.keystone,
            self.net_config.network_settings.name, True,
            self.os_creds.project_name))

        self.router = neutron_utils.create_router(
            self.neutron, self.os_creds, self.net_config.router_settings)
        validate_router(
            self.neutron, self.keystone, self.net_config.router_settings.name,
            self.os_creds.project_name, True)

        for subnet in self.network.subnets:
            neutron_utils.delete_subnet(self.neutron, subnet)

        with self.assertRaises(NotFound):
            self.interface_router = neutron_utils.add_interface_router(
                self.neutron, self.router, self.network.subnets[0])

    def test_create_port(self):
        """
        Tests the neutron_utils.create_port() function
        """
        self.network = neutron_utils.create_network(
            self.neutron, self.os_creds, self.net_config.network_settings)
        self.assertEqual(self.net_config.network_settings.name,
                         self.network.name)
        self.assertTrue(validate_network(
            self.neutron, self.keystone,
            self.net_config.network_settings.name, True,
            self.os_creds.project_name))

        subnet_setting = self.net_config.network_settings.subnet_settings[0]
        self.assertTrue(validate_subnet(
            self.neutron, self.network, subnet_setting.name,
            subnet_setting.cidr, True))

        self.port = neutron_utils.create_port(
            self.neutron, self.os_creds, PortConfig(
                name=self.port_name,
                ip_addrs=[{
                    'subnet_name': subnet_setting.name,
                    'ip': ip_1}],
                network_name=self.net_config.network_settings.name))
        validate_port(self.neutron, self.port, self.port_name)

    def test_create_port_empty_name(self):
        """
        Tests the neutron_utils.create_port() function
        """
        self.network = neutron_utils.create_network(
            self.neutron, self.os_creds, self.net_config.network_settings)
        self.assertEqual(self.net_config.network_settings.name,
                         self.network.name)
        self.assertTrue(validate_network(
            self.neutron, self.keystone,
            self.net_config.network_settings.name, True,
            self.os_creds.project_name))

        subnet_setting = self.net_config.network_settings.subnet_settings[0]
        self.assertTrue(validate_subnet(
            self.neutron, self.network, subnet_setting.name,
            subnet_setting.cidr, True))

        self.port = neutron_utils.create_port(
            self.neutron, self.os_creds, PortConfig(
                name=self.port_name,
                network_name=self.net_config.network_settings.name,
                ip_addrs=[{
                    'subnet_name': subnet_setting.name,
                    'ip': ip_1}]))
        validate_port(self.neutron, self.port, self.port_name)

    def test_create_port_null_name(self):
        """
        Tests the neutron_utils.create_port() when the port name value is None
        """
        self.network = neutron_utils.create_network(
            self.neutron, self.os_creds, self.net_config.network_settings)
        self.assertEqual(self.net_config.network_settings.name,
                         self.network.name)
        self.assertTrue(validate_network(
            self.neutron, self.keystone,
            self.net_config.network_settings.name, True,
            self.os_creds.project_name))

        subnet_setting = self.net_config.network_settings.subnet_settings[0]
        self.assertTrue(validate_subnet(
            self.neutron, self.network, subnet_setting.name,
            subnet_setting.cidr, True))

        self.port = neutron_utils.create_port(
            self.neutron, self.os_creds,
            PortConfig(
                network_name=self.net_config.network_settings.name,
                ip_addrs=[{
                    'subnet_name': subnet_setting.name,
                    'ip': ip_1}]))

        port = neutron_utils.get_port_by_id(self.neutron, self.port.id)
        self.assertEqual(self.port, port)

    def test_create_port_null_network_object(self):
        """
        Tests the neutron_utils.create_port() function for an Exception when
        the network object is None
        """
        with self.assertRaises(Exception):
            self.port = neutron_utils.create_port(
                self.neutron, self.os_creds,
                PortConfig(
                    name=self.port_name,
                    network_name=self.net_config.network_settings.name,
                    ip_addrs=[{
                        'subnet_name':
                            self.net_config.network_settings.subnet_settings[
                                0].name,
                        'ip': ip_1}]))

    def test_create_port_null_ip(self):
        """
        Tests the neutron_utils.create_port() function for an Exception when
        the IP value is None
        """
        self.network = neutron_utils.create_network(
            self.neutron, self.os_creds, self.net_config.network_settings)
        self.assertEqual(self.net_config.network_settings.name,
                         self.network.name)
        self.assertTrue(validate_network(
            self.neutron, self.keystone,
            self.net_config.network_settings.name, True,
            self.os_creds.project_name))

        subnet_setting = self.net_config.network_settings.subnet_settings[0]
        self.assertTrue(validate_subnet(
            self.neutron, self.network, subnet_setting.name,
            subnet_setting.cidr, True))

        with self.assertRaises(Exception):
            self.port = neutron_utils.create_port(
                self.neutron, self.os_creds,
                PortConfig(
                    name=self.port_name,
                    network_name=self.net_config.network_settings.name,
                    ip_addrs=[{
                        'subnet_name': subnet_setting.name,
                        'ip': None}]))

    def test_create_port_invalid_ip(self):
        """
        Tests the neutron_utils.create_port() function for an Exception when
        the IP value is None
        """
        self.network = neutron_utils.create_network(
            self.neutron, self.os_creds, self.net_config.network_settings)
        self.assertEqual(self.net_config.network_settings.name,
                         self.network.name)
        self.assertTrue(validate_network(
            self.neutron, self.keystone,
            self.net_config.network_settings.name, True,
            self.os_creds.project_name))

        subnet_setting = self.net_config.network_settings.subnet_settings[0]
        self.assertTrue(validate_subnet(
            self.neutron, self.network, subnet_setting.name,
            subnet_setting.cidr, True))

        with self.assertRaises(Exception):
            self.port = neutron_utils.create_port(
                self.neutron, self.os_creds,
                PortConfig(
                    name=self.port_name,
                    network_name=self.net_config.network_settings.name,
                    ip_addrs=[{
                        'subnet_name': subnet_setting.name,
                        'ip': 'foo'}]))

    def test_create_port_invalid_ip_to_subnet(self):
        """
        Tests the neutron_utils.create_port() function for an Exception when
        the IP value is None
        """
        self.network = neutron_utils.create_network(
            self.neutron, self.os_creds, self.net_config.network_settings)
        self.assertEqual(self.net_config.network_settings.name,
                         self.network.name)
        self.assertTrue(validate_network(
            self.neutron, self.keystone,
            self.net_config.network_settings.name, True,
            self.os_creds.project_name))

        subnet_setting = self.net_config.network_settings.subnet_settings[0]
        self.assertTrue(validate_subnet(
            self.neutron, self.network, subnet_setting.name,
            subnet_setting.cidr, True))

        with self.assertRaises(Exception):
            self.port = neutron_utils.create_port(
                self.neutron, self.os_creds,
                PortConfig(
                    name=self.port_name,
                    network_name=self.net_config.network_settings.name,
                    ip_addrs=[{
                        'subnet_name': subnet_setting.name,
                        'ip': '10.197.123.100'}]))


class NeutronUtilsSecurityGroupTests(OSComponentTestCase):
    """
    Test for creating security groups via neutron_utils.py
    """

    def setUp(self):
        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.sec_grp_name = guid + 'name'

        self.security_groups = list()
        self.security_group_rules = list()
        self.neutron = neutron_utils.neutron_client(
            self.os_creds, self.os_session)
        self.keystone = keystone_utils.keystone_client(
            self.os_creds, self.os_session)

    def tearDown(self):
        """
        Cleans the remote OpenStack objects
        """
        for rule in self.security_group_rules:
            neutron_utils.delete_security_group_rule(self.neutron, rule)

        for security_group in self.security_groups:
            try:
                neutron_utils.delete_security_group(self.neutron,
                                                    security_group)
            except:
                pass

        super(self.__class__, self).__clean__()

    def test_create_delete_simple_sec_grp(self):
        """
        Tests the neutron_utils.create_security_group() function
        """
        sec_grp_settings = SecurityGroupConfig(name=self.sec_grp_name)
        security_group = neutron_utils.create_security_group(
            self.neutron, self.keystone, sec_grp_settings)

        self.assertTrue(sec_grp_settings.name, security_group.name)

        sec_grp_get = neutron_utils.get_security_group(
            self.neutron, self.keystone, sec_grp_settings=sec_grp_settings)
        self.assertIsNotNone(sec_grp_get)
        self.assertTrue(validation_utils.objects_equivalent(
            security_group, sec_grp_get))

        neutron_utils.delete_security_group(self.neutron, security_group)
        sec_grp_get = neutron_utils.get_security_group(
            self.neutron, self.keystone, sec_grp_settings=sec_grp_settings)
        self.assertIsNone(sec_grp_get)

    def test_create_sec_grp_no_name(self):
        """
        Tests the SecurityGroupConfig constructor and
        neutron_utils.create_security_group() function to ensure that
        attempting to create a security group without a name will raise an
        exception
        """
        with self.assertRaises(Exception):
            sec_grp_settings = SecurityGroupConfig()
            self.security_groups.append(
                neutron_utils.create_security_group(
                    self.neutron, self.keystone, sec_grp_settings))

    def test_create_sec_grp_no_rules(self):
        """
        Tests the neutron_utils.create_security_group() function
        """
        sec_grp_settings = SecurityGroupConfig(
            name=self.sec_grp_name, description='hello group')
        self.security_groups.append(
            neutron_utils.create_security_group(
                self.neutron, self.keystone, sec_grp_settings))

        self.assertTrue(sec_grp_settings.name, self.security_groups[0].name)
        self.assertEqual(sec_grp_settings.name, self.security_groups[0].name)

        sec_grp_get = neutron_utils.get_security_group(
            self.neutron, self.keystone, sec_grp_settings=sec_grp_settings)
        self.assertIsNotNone(sec_grp_get)
        self.assertEqual(self.security_groups[0], sec_grp_get)

    def test_create_sec_grp_one_rule(self):
        """
        Tests the neutron_utils.create_security_group() function
        """

        sec_grp_rule_settings = SecurityGroupRuleConfig(
            sec_grp_name=self.sec_grp_name, direction=Direction.ingress)
        sec_grp_settings = SecurityGroupConfig(
            name=self.sec_grp_name, description='hello group',
            rule_settings=[sec_grp_rule_settings])

        self.security_groups.append(
            neutron_utils.create_security_group(
                self.neutron, self.keystone, sec_grp_settings))
        free_rules = neutron_utils.get_rules_by_security_group(
            self.neutron, self.security_groups[0])
        for free_rule in free_rules:
            self.security_group_rules.append(free_rule)

        keystone = keystone_utils.keystone_client(
            self.os_creds, self.os_session)
        self.security_group_rules.append(
            neutron_utils.create_security_group_rule(
                self.neutron, keystone, sec_grp_settings.rule_settings[0],
                self.os_creds.project_name))

        # Refresh object so it is populated with the newly added rule
        security_group = neutron_utils.get_security_group(
            self.neutron, self.keystone, sec_grp_settings=sec_grp_settings)

        rules = neutron_utils.get_rules_by_security_group(
            self.neutron, security_group)

        self.assertTrue(
            validation_utils.objects_equivalent(
                 self.security_group_rules, rules))

        self.assertTrue(sec_grp_settings.name, security_group.name)

        sec_grp_get = neutron_utils.get_security_group(
            self.neutron, self.keystone, sec_grp_settings=sec_grp_settings)
        self.assertIsNotNone(sec_grp_get)
        self.assertEqual(security_group, sec_grp_get)

    def test_get_sec_grp_by_id(self):
        """
        Tests the neutron_utils.create_security_group() function
        """

        self.security_groups.append(neutron_utils.create_security_group(
            self.neutron, self.keystone,
            SecurityGroupConfig(
                name=self.sec_grp_name + '-1', description='hello group')))
        self.security_groups.append(neutron_utils.create_security_group(
            self.neutron, self.keystone,
            SecurityGroupConfig(
                name=self.sec_grp_name + '-2', description='hello group')))

        sec_grp_1b = neutron_utils.get_security_group_by_id(
            self.neutron, self.security_groups[0].id)
        sec_grp_2b = neutron_utils.get_security_group_by_id(
            self.neutron, self.security_groups[1].id)

        self.assertEqual(self.security_groups[0].id, sec_grp_1b.id)
        self.assertEqual(self.security_groups[1].id, sec_grp_2b.id)

    def test_create_list_sec_grp_no_rules(self):
        """
        Tests the neutron_utils.create_security_group() and
        list_security_groups function
        """
        sec_grp_settings = SecurityGroupConfig(
            name=self.sec_grp_name + "-1", description='hello group')
        self.security_groups.append(neutron_utils.create_security_group(
            self.neutron, self.keystone, sec_grp_settings))

        sec_grp_settings2 = SecurityGroupConfig(
            name=self.sec_grp_name + "-2", description='hola group')
        self.security_groups.append(neutron_utils.create_security_group(
            self.neutron, self.keystone, sec_grp_settings2))

        returned_sec_groups = neutron_utils.list_security_groups(self.neutron)

        self.assertIsNotNone(returned_sec_groups)
        worked = 0
        for sg in returned_sec_groups:
            if sec_grp_settings.name == sg.name:
                worked += 1
            elif sec_grp_settings2.name == sg.name:
                worked += 1

        self.assertEqual(worked, 2)


class NeutronUtilsFloatingIpTests(OSComponentTestCase):
    """
    Test basic nova keypair functionality
    """

    def setUp(self):
        """
        Instantiates the CreateImage object that is responsible for downloading
        and creating an OS image file within OpenStack
        """
        self.neutron = neutron_utils.neutron_client(
            self.os_creds, self.os_session)
        self.keystone = keystone_utils.keystone_client(
            self.os_creds, self.os_session)
        self.floating_ip = None

    def tearDown(self):
        """
        Cleans the image and downloaded image file
        """
        if self.floating_ip:
            try:
                neutron_utils.delete_floating_ip(
                    self.neutron, self.floating_ip)
            except:
                pass

        super(self.__class__, self).__clean__()

    def test_floating_ips(self):
        """
        Tests the creation of a floating IP
        :return:
        """
        initial_fips = neutron_utils.get_floating_ips(self.neutron)

        self.floating_ip = neutron_utils.create_floating_ip(
            self.neutron, self.keystone, self.ext_net_name)
        all_fips = neutron_utils.get_floating_ips(self.neutron)
        self.assertEqual(len(initial_fips) + 1, len(all_fips))
        returned = neutron_utils.get_floating_ip(self.neutron,
                                                 self.floating_ip)
        self.assertEqual(self.floating_ip.id, returned.id)
        self.assertEqual(self.floating_ip.ip, returned.ip)


"""
Validation routines
"""


def validate_network(neutron, keystone, name, exists, project_name):
    """
    Returns true if a network for a given name DOES NOT exist if the exists
    parameter is false conversely true. Returns false if a network for a given
    name DOES exist if the exists parameter is true conversely false.
    :param neutron: The neutron client
    :param keystone: The keystone client
    :param name: The expected network name
    :param exists: Whether or not the network name should exist or not
    :param project_name: the associated project name
    :return: True/False
    """
    network = neutron_utils.get_network(
        neutron, keystone, network_name=name, project_name=project_name)
    if exists and network:
        return True
    if not exists and not network:
        return True
    return False


def validate_subnet(neutron, network, name, cidr, exists):
    """
    Returns true if a subnet for a given name DOES NOT exist if the exists
    parameter is false conversely true. Returns false if a subnet for a given
    name DOES exist if the exists parameter is true conversely false.
    :param neutron: The neutron client
    :param network: The SNAPS-OO Network domain object
    :param name: The expected subnet name
    :param cidr: The expected CIDR value
    :param exists: Whether or not the network name should exist or not
    :return: True/False
    """
    subnet = neutron_utils.get_subnet(
        neutron, network, subnet_name=name)
    if exists and subnet and subnet.name == name:
        return subnet.cidr == cidr
    if not exists and not subnet:
        return True
    return False


def validate_router(neutron, keystone, name, project_name, exists):
    """
    Returns true if a router for a given name DOES NOT exist if the exists
    parameter is false conversely true. Returns false if a router for a given
    name DOES exist if the exists parameter is true conversely false.
    :param neutron: The neutron client
    :param keystone: The keystone client
    :param name: The expected router name
    :param project_name: The name of the project in which the router should
                         exist
    :param exists: Whether or not the network name should exist or not
    :return: True/False
    """
    router = neutron_utils.get_router(
        neutron, keystone, router_name=name, project_name=project_name)
    if exists and router:
        return True
    return False


def validate_interface_router(interface_router, router, subnet):
    """
    Returns true if the router ID & subnet ID have been properly included into
    the interface router object
    :param interface_router: the SNAPS-OO InterfaceRouter domain object
    :param router: to validate against the interface_router
    :param subnet: to validate against the interface_router
    :return: True if both IDs match else False
    """
    subnet_id = interface_router.subnet_id
    router_id = interface_router.port_id

    return subnet.id == subnet_id and router.id == router_id


def validate_port(neutron, port_obj, this_port_name):
    """
    Returns true if a port for a given name DOES NOT exist if the exists
    parameter is false conversely true. Returns false if a port for a given
    name DOES exist if the exists parameter is true conversely false.
    :param neutron: The neutron client
    :param port_obj: The port object to lookup
    :param this_port_name: The expected router name
    :return: True/False
    """
    os_ports = neutron.list_ports()
    for os_port, os_port_insts in os_ports.items():
        for os_inst in os_port_insts:
            if os_inst['id'] == port_obj.id:
                return os_inst['name'] == this_port_name
    return False
