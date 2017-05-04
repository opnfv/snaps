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

from snaps.openstack.utils import keystone_utils
from snaps.openstack.create_security_group import SecurityGroupSettings, SecurityGroupRuleSettings, Direction
from snaps.openstack.tests import openstack_tests
from snaps.openstack.utils import neutron_utils
from snaps.openstack.create_network import NetworkSettings, SubnetSettings, PortSettings
from snaps.openstack import create_router
from snaps.openstack.tests.os_source_file_test import OSComponentTestCase
from snaps.openstack.tests import validation_utils

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
        neutron = neutron_utils.neutron_client(self.os_creds)

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
                OSCreds(username='user', password='pass', auth_url='url', project_name='project'))
            neutron.list_networks()

    def test_retrieve_ext_network_name(self):
        """
        Tests the neutron_utils.get_external_network_names to ensure the configured self.ext_net_name is contained
        within the returned list
        :return:
        """
        neutron = neutron_utils.neutron_client(self.os_creds)
        ext_networks = neutron_utils.get_external_networks(neutron)
        found = False
        for network in ext_networks:
            if network['network']['name'] == self.ext_net_name:
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
        self.neutron = neutron_utils.neutron_client(self.os_creds)
        self.network = None
        self.net_config = openstack_tests.get_pub_net_config(net_name=guid + '-pub-net')

    def tearDown(self):
        """
        Cleans the remote OpenStack objects
        """
        if self.network:
            neutron_utils.delete_network(self.neutron, self.network)
            validate_network(self.neutron, self.network['network']['name'], False)

    def test_create_network(self):
        """
        Tests the neutron_utils.create_neutron_net() function
        """
        self.network = neutron_utils.create_network(self.neutron, self.os_creds, self.net_config.network_settings)
        self.assertEqual(self.net_config.network_settings.name, self.network['network']['name'])
        self.assertTrue(validate_network(self.neutron, self.net_config.network_settings.name, True))

    def test_create_network_empty_name(self):
        """
        Tests the neutron_utils.create_neutron_net() function with an empty network name
        """
        with self.assertRaises(Exception):
            self.network = neutron_utils.create_network(self.neutron, self.os_creds,
                                                        network_settings=NetworkSettings(name=''))

    def test_create_network_null_name(self):
        """
        Tests the neutron_utils.create_neutron_net() function when the network name is None
        """
        with self.assertRaises(Exception):
            self.network = neutron_utils.create_network(self.neutron, self.os_creds,
                                                        network_settings=NetworkSettings())


class NeutronUtilsSubnetTests(OSComponentTestCase):
    """
    Test for creating networks with subnets via neutron_utils.py
    """

    def setUp(self):
        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.port_name = str(guid) + '-port'
        self.neutron = neutron_utils.neutron_client(self.os_creds)
        self.network = None
        self.subnet = None
        self.net_config = openstack_tests.get_pub_net_config(
            net_name=guid + '-pub-net', subnet_name=guid + '-pub-subnet', external_net=self.ext_net_name)

    def tearDown(self):
        """
        Cleans the remote OpenStack objects
        """
        if self.subnet:
            neutron_utils.delete_subnet(self.neutron, self.subnet)
            validate_subnet(self.neutron, self.subnet.get('name'),
                            self.net_config.network_settings.subnet_settings[0].cidr, False)

        if self.network:
            neutron_utils.delete_network(self.neutron, self.network)
            validate_network(self.neutron, self.network['network']['name'], False)

    def test_create_subnet(self):
        """
        Tests the neutron_utils.create_neutron_net() function
        """
        self.network = neutron_utils.create_network(self.neutron, self.os_creds, self.net_config.network_settings)
        self.assertEqual(self.net_config.network_settings.name, self.network['network']['name'])
        self.assertTrue(validate_network(self.neutron, self.net_config.network_settings.name, True))

        self.subnet = neutron_utils.create_subnet(self.neutron, self.net_config.network_settings.subnet_settings[0],
                                                  self.os_creds, network=self.network)
        validate_subnet(self.neutron, self.net_config.network_settings.subnet_settings[0].name,
                        self.net_config.network_settings.subnet_settings[0].cidr, True)

    def test_create_subnet_null_name(self):
        """
        Tests the neutron_utils.create_neutron_subnet() function for an Exception when the subnet name is None
        """
        self.network = neutron_utils.create_network(self.neutron, self.os_creds, self.net_config.network_settings)
        self.assertEqual(self.net_config.network_settings.name, self.network['network']['name'])
        self.assertTrue(validate_network(self.neutron, self.net_config.network_settings.name, True))

        with self.assertRaises(Exception):
            SubnetSettings(cidr=self.net_config.subnet_cidr)

    def test_create_subnet_empty_name(self):
        """
        Tests the neutron_utils.create_neutron_net() function with an empty name
        """
        self.network = neutron_utils.create_network(self.neutron, self.os_creds, self.net_config.network_settings)
        self.assertEqual(self.net_config.network_settings.name, self.network['network']['name'])
        self.assertTrue(validate_network(self.neutron, self.net_config.network_settings.name, True))

        neutron_utils.create_subnet(self.neutron, self.net_config.network_settings.subnet_settings[0],
                                    self.os_creds, network=self.network)
        validate_subnet(self.neutron, '', self.net_config.network_settings.subnet_settings[0].cidr, True)

    def test_create_subnet_null_cidr(self):
        """
        Tests the neutron_utils.create_neutron_subnet() function for an Exception when the subnet CIDR value is None
        """
        self.network = neutron_utils.create_network(self.neutron, self.os_creds, self.net_config.network_settings)
        self.assertEqual(self.net_config.network_settings.name, self.network['network']['name'])
        self.assertTrue(validate_network(self.neutron, self.net_config.network_settings.name, True))

        with self.assertRaises(Exception):
            sub_sets = SubnetSettings(cidr=None, name=self.net_config.subnet_name)
            neutron_utils.create_subnet(self.neutron, sub_sets, self.os_creds, network=self.network)

    def test_create_subnet_empty_cidr(self):
        """
        Tests the neutron_utils.create_neutron_subnet() function for an Exception when the subnet CIDR value is empty
        """
        self.network = neutron_utils.create_network(self.neutron, self.os_creds, self.net_config.network_settings)
        self.assertEqual(self.net_config.network_settings.name, self.network['network']['name'])
        self.assertTrue(validate_network(self.neutron, self.net_config.network_settings.name, True))

        with self.assertRaises(Exception):
            sub_sets = SubnetSettings(cidr='', name=self.net_config.subnet_name)
            neutron_utils.create_subnet(self.neutron, sub_sets, self.os_creds, network=self.network)


class NeutronUtilsRouterTests(OSComponentTestCase):
    """
    Test for creating routers via neutron_utils.py
    """

    def setUp(self):
        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.port_name = str(guid) + '-port'
        self.neutron = neutron_utils.neutron_client(self.os_creds)
        self.network = None
        self.subnet = None
        self.port = None
        self.router = None
        self.interface_router = None
        self.net_config = openstack_tests.get_pub_net_config(
            net_name=guid + '-pub-net', subnet_name=guid + '-pub-subnet',
            router_name=guid + '-pub-router', external_net=self.ext_net_name)

    def tearDown(self):
        """
        Cleans the remote OpenStack objects
        """
        if self.interface_router:
            neutron_utils.remove_interface_router(self.neutron, self.router, self.subnet)

        if self.router:
            neutron_utils.delete_router(self.neutron, self.router)
            validate_router(self.neutron, self.router.get('name'), False)

        if self.port:
            neutron_utils.delete_port(self.neutron, self.port)

        if self.subnet:
            neutron_utils.delete_subnet(self.neutron, self.subnet)
            validate_subnet(self.neutron, self.subnet.get('name'),
                            self.net_config.network_settings.subnet_settings[0].cidr, False)

        if self.network:
            neutron_utils.delete_network(self.neutron, self.network)
            validate_network(self.neutron, self.network['network']['name'], False)

    def test_create_router_simple(self):
        """
        Tests the neutron_utils.create_neutron_net() function when an external gateway is requested
        """
        self.router = neutron_utils.create_router(self.neutron, self.os_creds, self.net_config.router_settings)
        validate_router(self.neutron, self.net_config.router_settings.name, True)

    def test_create_router_with_public_interface(self):
        """
        Tests the neutron_utils.create_neutron_net() function when an external gateway is requested
        """
        self.net_config = openstack_tests.OSNetworkConfig(
            self.net_config.network_settings.name,
            self.net_config.network_settings.subnet_settings[0].name,
            self.net_config.network_settings.subnet_settings[0].cidr, self.net_config.router_settings.name,
            self.ext_net_name)
        self.router = neutron_utils.create_router(self.neutron, self.os_creds, self.net_config.router_settings)
        validate_router(self.neutron, self.net_config.router_settings.name, True)
        # TODO - Add validation that the router gatway has been set

    def test_create_router_empty_name(self):
        """
        Tests the neutron_utils.create_neutron_net() function
        """
        with self.assertRaises(Exception):
            this_router_settings = create_router.RouterSettings(name='')
            self.router = neutron_utils.create_router(self.neutron, self.os_creds, this_router_settings)

    def test_create_router_null_name(self):
        """
        Tests the neutron_utils.create_neutron_subnet() function when the subnet CIDR value is None
        """
        with self.assertRaises(Exception):
            this_router_settings = create_router.RouterSettings()
            self.router = neutron_utils.create_router(self.neutron, self.os_creds, this_router_settings)
            validate_router(self.neutron, None, True)

    def test_add_interface_router(self):
        """
        Tests the neutron_utils.add_interface_router() function
        """
        self.network = neutron_utils.create_network(self.neutron, self.os_creds, self.net_config.network_settings)
        self.assertEqual(self.net_config.network_settings.name, self.network['network']['name'])
        self.assertTrue(validate_network(self.neutron, self.net_config.network_settings.name, True))

        self.subnet = neutron_utils.create_subnet(self.neutron, self.net_config.network_settings.subnet_settings[0],
                                                  self.os_creds, self.network)
        validate_subnet(self.neutron, self.net_config.network_settings.subnet_settings[0].name,
                        self.net_config.network_settings.subnet_settings[0].cidr, True)

        self.router = neutron_utils.create_router(self.neutron, self.os_creds, self.net_config.router_settings)
        validate_router(self.neutron, self.net_config.router_settings.name, True)

        self.interface_router = neutron_utils.add_interface_router(self.neutron, self.router, self.subnet)
        validate_interface_router(self.interface_router, self.router, self.subnet)

    def test_add_interface_router_null_router(self):
        """
        Tests the neutron_utils.add_interface_router() function for an Exception when the router value is None
        """
        self.network = neutron_utils.create_network(self.neutron, self.os_creds, self.net_config.network_settings)
        self.assertEqual(self.net_config.network_settings.name, self.network['network']['name'])
        self.assertTrue(validate_network(self.neutron, self.net_config.network_settings.name, True))

        self.subnet = neutron_utils.create_subnet(self.neutron, self.net_config.network_settings.subnet_settings[0],
                                                  self.os_creds, self.network)
        validate_subnet(self.neutron, self.net_config.network_settings.subnet_settings[0].name,
                        self.net_config.network_settings.subnet_settings[0].cidr, True)

        with self.assertRaises(Exception):
            self.interface_router = neutron_utils.add_interface_router(self.neutron, self.router, self.subnet)

    def test_add_interface_router_null_subnet(self):
        """
        Tests the neutron_utils.add_interface_router() function for an Exception when the subnet value is None
        """
        self.network = neutron_utils.create_network(self.neutron, self.os_creds, self.net_config.network_settings)
        self.assertEqual(self.net_config.network_settings.name, self.network['network']['name'])
        self.assertTrue(validate_network(self.neutron, self.net_config.network_settings.name, True))

        self.router = neutron_utils.create_router(self.neutron, self.os_creds, self.net_config.router_settings)
        validate_router(self.neutron, self.net_config.router_settings.name, True)

        with self.assertRaises(Exception):
            self.interface_router = neutron_utils.add_interface_router(self.neutron, self.router, self.subnet)

    def test_create_port(self):
        """
        Tests the neutron_utils.create_port() function
        """
        self.network = neutron_utils.create_network(self.neutron, self.os_creds, self.net_config.network_settings)
        self.assertEqual(self.net_config.network_settings.name, self.network['network']['name'])
        self.assertTrue(validate_network(self.neutron, self.net_config.network_settings.name, True))

        self.subnet = neutron_utils.create_subnet(self.neutron, self.net_config.network_settings.subnet_settings[0],
                                                  self.os_creds, self.network)
        validate_subnet(self.neutron, self.net_config.network_settings.subnet_settings[0].name,
                        self.net_config.network_settings.subnet_settings[0].cidr, True)

        self.port = neutron_utils.create_port(
            self.neutron, self.os_creds, PortSettings(
                name=self.port_name,
                ip_addrs=[{'subnet_name': self.net_config.network_settings.subnet_settings[0].name, 'ip': ip_1}],
                network_name=self.net_config.network_settings.name))
        validate_port(self.neutron, self.port, self.port_name)

    def test_create_port_empty_name(self):
        """
        Tests the neutron_utils.create_port() function
        """
        self.network = neutron_utils.create_network(self.neutron, self.os_creds, self.net_config.network_settings)
        self.assertEqual(self.net_config.network_settings.name, self.network['network']['name'])
        self.assertTrue(validate_network(self.neutron, self.net_config.network_settings.name, True))

        self.subnet = neutron_utils.create_subnet(self.neutron, self.net_config.network_settings.subnet_settings[0],
                                                  self.os_creds, self.network)
        validate_subnet(self.neutron, self.net_config.network_settings.subnet_settings[0].name,
                        self.net_config.network_settings.subnet_settings[0].cidr, True)

        self.port = neutron_utils.create_port(
            self.neutron, self.os_creds, PortSettings(
                name=self.port_name, network_name=self.net_config.network_settings.name,
                ip_addrs=[{'subnet_name': self.net_config.network_settings.subnet_settings[0].name, 'ip': ip_1}]))
        validate_port(self.neutron, self.port, self.port_name)

    def test_create_port_null_name(self):
        """
        Tests the neutron_utils.create_port() function for an Exception when the port name value is None
        """
        self.network = neutron_utils.create_network(self.neutron, self.os_creds, self.net_config.network_settings)
        self.assertEqual(self.net_config.network_settings.name, self.network['network']['name'])
        self.assertTrue(validate_network(self.neutron, self.net_config.network_settings.name, True))

        self.subnet = neutron_utils.create_subnet(self.neutron, self.net_config.network_settings.subnet_settings[0],
                                                  self.os_creds, self.network)
        validate_subnet(self.neutron, self.net_config.network_settings.subnet_settings[0].name,
                        self.net_config.network_settings.subnet_settings[0].cidr, True)

        with self.assertRaises(Exception):
            self.port = neutron_utils.create_port(self.neutron, self.os_creds, PortSettings(
                network_name=self.net_config.network_settings.name,
                ip_addrs=[{'subnet_name': self.net_config.network_settings.subnet_settings.name, 'ip': ip_1}]))

    def test_create_port_null_network_object(self):
        """
        Tests the neutron_utils.create_port() function for an Exception when the network object is None
        """
        self.network = neutron_utils.create_network(self.neutron, self.os_creds, self.net_config.network_settings)
        self.assertEqual(self.net_config.network_settings.name, self.network['network']['name'])
        self.assertTrue(validate_network(self.neutron, self.net_config.network_settings.name, True))

        self.subnet = neutron_utils.create_subnet(self.neutron, self.net_config.network_settings.subnet_settings[0],
                                                  self.os_creds, self.network)
        validate_subnet(self.neutron, self.net_config.network_settings.subnet_settings[0].name,
                        self.net_config.network_settings.subnet_settings[0].cidr, True)

        with self.assertRaises(Exception):
            self.port = neutron_utils.create_port(self.neutron, self.os_creds, PortSettings(
                self.neutron, self.port_name, self.net_config.network_settings.name,
                ip_addrs=[{'subnet_name': self.net_config.network_settings.subnet_settings.name, 'ip': ip_1}]))

    def test_create_port_null_ip(self):
        """
        Tests the neutron_utils.create_port() function for an Exception when the IP value is None
        """
        self.network = neutron_utils.create_network(self.neutron, self.os_creds, self.net_config.network_settings)
        self.assertEqual(self.net_config.network_settings.name, self.network['network']['name'])
        self.assertTrue(validate_network(self.neutron, self.net_config.network_settings.name, True))

        self.subnet = neutron_utils.create_subnet(self.neutron, self.net_config.network_settings.subnet_settings[0],
                                                  self.os_creds, self.network)
        validate_subnet(self.neutron, self.net_config.network_settings.subnet_settings[0].name,
                        self.net_config.network_settings.subnet_settings[0].cidr, True)

        with self.assertRaises(Exception):
            self.port = neutron_utils.create_port(self.neutron, self.os_creds, PortSettings(
                name=self.port_name, network_name=self.net_config.network_settings.name,
                ip_addrs=[{'subnet_name': self.net_config.network_settings.subnet_settings.name, 'ip': None}]))

    def test_create_port_invalid_ip(self):
        """
        Tests the neutron_utils.create_port() function for an Exception when the IP value is None
        """
        self.network = neutron_utils.create_network(self.neutron, self.os_creds, self.net_config.network_settings)
        self.assertEqual(self.net_config.network_settings.name, self.network['network']['name'])
        self.assertTrue(validate_network(self.neutron, self.net_config.network_settings.name, True))

        self.subnet = neutron_utils.create_subnet(self.neutron, self.net_config.network_settings.subnet_settings[0],
                                                  self.os_creds, self.network)
        validate_subnet(self.neutron, self.net_config.network_settings.subnet_settings[0].name,
                        self.net_config.network_settings.subnet_settings[0].cidr, True)

        with self.assertRaises(Exception):
            self.port = neutron_utils.create_port(self.neutron, self.os_creds, PortSettings(
                name=self.port_name, network_name=self.net_config.network_settings.name,
                ip_addrs=[{'subnet_name': self.net_config.network_settings.subnet_settings.name, 'ip': 'foo'}]))

    def test_create_port_invalid_ip_to_subnet(self):
        """
        Tests the neutron_utils.create_port() function for an Exception when the IP value is None
        """
        self.network = neutron_utils.create_network(self.neutron, self.os_creds, self.net_config.network_settings)
        self.assertEqual(self.net_config.network_settings.name, self.network['network']['name'])
        self.assertTrue(validate_network(self.neutron, self.net_config.network_settings.name, True))

        self.subnet = neutron_utils.create_subnet(self.neutron, self.net_config.network_settings.subnet_settings[0],
                                                  self.os_creds, self.network)
        validate_subnet(self.neutron, self.net_config.network_settings.subnet_settings[0].name,
                        self.net_config.network_settings.subnet_settings[0].cidr, True)

        with self.assertRaises(Exception):
            self.port = neutron_utils.create_port(self.neutron, self.os_creds, PortSettings(
                name=self.port_name, network_name=self.net_config.network_settings.name,
                ip_addrs=[{'subnet_name': self.net_config.network_settings.subnet_settings.name,
                          'ip': '10.197.123.100'}]))


class NeutronUtilsSecurityGroupTests(OSComponentTestCase):
    """
    Test for creating security groups via neutron_utils.py
    """

    def setUp(self):
        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.sec_grp_name = guid + 'name'

        self.security_group = None
        self.security_group_rules = list()
        self.neutron = neutron_utils.neutron_client(self.os_creds)
        self.keystone = keystone_utils.keystone_client(self.os_creds)

    def tearDown(self):
        """
        Cleans the remote OpenStack objects
        """
        for rule in self.security_group_rules:
            neutron_utils.delete_security_group_rule(self.neutron, rule)

        if self.security_group:
            neutron_utils.delete_security_group(self.neutron, self.security_group)

    def test_create_delete_simple_sec_grp(self):
        """
        Tests the neutron_utils.create_security_group() function
        """
        sec_grp_settings = SecurityGroupSettings(name=self.sec_grp_name)
        self.security_group = neutron_utils.create_security_group(self.neutron, self.keystone, sec_grp_settings)

        self.assertTrue(sec_grp_settings.name, self.security_group['security_group']['name'])

        sec_grp_get = neutron_utils.get_security_group(self.neutron, sec_grp_settings.name)
        self.assertIsNotNone(sec_grp_get)
        self.assertTrue(validation_utils.objects_equivalent(
            self.security_group['security_group'], sec_grp_get['security_group']))

        neutron_utils.delete_security_group(self.neutron, self.security_group)
        sec_grp_get = neutron_utils.get_security_group(self.neutron, sec_grp_settings.name)
        self.assertIsNone(sec_grp_get)
        self.security_group = None

    def test_create_sec_grp_no_name(self):
        """
        Tests the SecurityGroupSettings constructor and neutron_utils.create_security_group() function to ensure
        that attempting to create a security group without a name will raise an exception
        """
        with self.assertRaises(Exception):
            sec_grp_settings = SecurityGroupSettings()
            self.security_group = neutron_utils.create_security_group(self.neutron, self.keystone, sec_grp_settings)

    def test_create_sec_grp_no_rules(self):
        """
        Tests the neutron_utils.create_security_group() function
        """
        sec_grp_settings = SecurityGroupSettings(name=self.sec_grp_name, description='hello group')
        self.security_group = neutron_utils.create_security_group(self.neutron, self.keystone, sec_grp_settings)

        self.assertTrue(sec_grp_settings.name, self.security_group['security_group']['name'])
        self.assertTrue(sec_grp_settings.description, self.security_group['security_group']['description'])

        sec_grp_get = neutron_utils.get_security_group(self.neutron, sec_grp_settings.name)
        self.assertIsNotNone(sec_grp_get)
        self.assertTrue(validation_utils.objects_equivalent(
            self.security_group['security_group'], sec_grp_get['security_group']))

    def test_create_sec_grp_one_rule(self):
        """
        Tests the neutron_utils.create_security_group() function
        """

        sec_grp_rule_settings = SecurityGroupRuleSettings(sec_grp_name=self.sec_grp_name, direction=Direction.ingress)
        sec_grp_settings = SecurityGroupSettings(name=self.sec_grp_name, description='hello group',
                                                 rule_settings=[sec_grp_rule_settings])

        self.security_group = neutron_utils.create_security_group(self.neutron, self.keystone, sec_grp_settings)
        free_rules = neutron_utils.get_rules_by_security_group(self.neutron, self.security_group)
        for free_rule in free_rules:
            self.security_group_rules.append(free_rule)

        self.security_group_rules.append(
            neutron_utils.create_security_group_rule(self.neutron, sec_grp_settings.rule_settings[0]))

        # Refresh object so it is populated with the newly added rule
        self.security_group = neutron_utils.get_security_group(self.neutron, sec_grp_settings.name)

        rules = neutron_utils.get_rules_by_security_group(self.neutron, self.security_group)

        self.assertTrue(validation_utils.objects_equivalent(self.security_group_rules, rules))

        self.assertTrue(sec_grp_settings.name, self.security_group['security_group']['name'])
        self.assertTrue(sec_grp_settings.description, self.security_group['security_group']['description'])

        sec_grp_get = neutron_utils.get_security_group(self.neutron, sec_grp_settings.name)
        self.assertIsNotNone(sec_grp_get)
        self.assertTrue(validation_utils.objects_equivalent(
            self.security_group['security_group'], sec_grp_get['security_group']))


"""
Validation routines
"""


def validate_network(neutron, name, exists):
    """
    Returns true if a network for a given name DOES NOT exist if the exists parameter is false conversely true.
    Returns false if a network for a given name DOES exist if the exists parameter is true conversely false.
    :param neutron: The neutron client
    :param name: The expected network name
    :param exists: Whether or not the network name should exist or not
    :return: True/False
    """
    network = neutron_utils.get_network(neutron, name)
    if exists and network:
        return True
    if not exists and not network:
        return True
    return False


def validate_subnet(neutron, name, cidr, exists):
    """
    Returns true if a subnet for a given name DOES NOT exist if the exists parameter is false conversely true.
    Returns false if a subnet for a given name DOES exist if the exists parameter is true conversely false.
    :param neutron: The neutron client
    :param name: The expected subnet name
    :param cidr: The expected CIDR value
    :param exists: Whether or not the network name should exist or not
    :return: True/False
    """
    subnet = neutron_utils.get_subnet_by_name(neutron, name)
    if exists and subnet:
        return subnet.get('cidr') == cidr
    if not exists and not subnet:
        return True
    return False


def validate_router(neutron, name, exists):
    """
    Returns true if a router for a given name DOES NOT exist if the exists parameter is false conversely true.
    Returns false if a router for a given name DOES exist if the exists parameter is true conversely false.
    :param neutron: The neutron client
    :param name: The expected router name
    :param exists: Whether or not the network name should exist or not
    :return: True/False
    """
    router = neutron_utils.get_router_by_name(neutron, name)
    if exists and router:
        return True
    return False


def validate_interface_router(interface_router, router, subnet):
    """
    Returns true if the router ID & subnet ID have been properly included into the interface router object
    :param interface_router: the object to validate
    :param router: to validate against the interface_router
    :param subnet: to validate against the interface_router
    :return: True if both IDs match else False
    """
    subnet_id = interface_router.get('subnet_id')
    router_id = interface_router.get('port_id')

    return subnet.get('id') == subnet_id and router.get('id') == router_id


def validate_port(neutron, port_obj, this_port_name):
    """
    Returns true if a port for a given name DOES NOT exist if the exists parameter is false conversely true.
    Returns false if a port for a given name DOES exist if the exists parameter is true conversely false.
    :param neutron: The neutron client
    :param port_obj: The port object to lookup
    :param this_port_name: The expected router name
    :return: True/False
    """
    ports = neutron.list_ports()
    for port, port_insts in ports.items():
        for inst in port_insts:
            if inst['id'] == port_obj['port']['id']:
                return inst['name'] == this_port_name
    return False
