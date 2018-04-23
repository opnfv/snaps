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

from snaps.config.network import PortConfig, NetworkConfig, PortConfigError
from snaps.config.router import RouterConfigError, RouterConfig
from snaps.config.security_group import SecurityGroupConfig
from snaps.openstack import create_network
from snaps.openstack import create_router
from snaps.openstack.create_network import OpenStackNetwork
from snaps.openstack.create_router import RouterSettings, OpenStackRouter
from snaps.openstack.create_security_group import OpenStackSecurityGroup
from snaps.openstack.tests.os_source_file_test import OSIntegrationTestCase
from snaps.openstack.utils import neutron_utils, settings_utils, keystone_utils

__author__ = 'mmakati'

cidr1 = '10.200.201.0/24'
cidr2 = '10.200.202.0/24'
static_gateway_ip1 = '10.200.201.1'
static_gateway_ip2 = '10.200.202.1'


class RouterSettingsUnitTests(unittest.TestCase):
    """
    Class for testing the RouterSettings class
    """

    def test_no_params(self):
        with self.assertRaises(RouterConfigError):
            RouterSettings()

    def test_empty_config(self):
        with self.assertRaises(RouterConfigError):
            RouterSettings(**dict())

    def test_name_only(self):
        settings = RouterSettings(name='foo')
        self.assertEqual('foo', settings.name)
        self.assertIsNone(settings.project_name)
        self.assertIsNone(settings.external_gateway)
        self.assertTrue(settings.admin_state_up)
        self.assertIsNone(settings.enable_snat)
        self.assertIsNotNone(settings.internal_subnets)
        self.assertTrue(isinstance(settings.internal_subnets, list))
        self.assertEqual(0, len(settings.internal_subnets))
        self.assertIsNotNone(settings.port_settings)
        self.assertTrue(isinstance(settings.port_settings, list))
        self.assertEqual(0, len(settings.port_settings))

    def test_config_with_name_only(self):
        settings = RouterSettings(**{'name': 'foo'})
        self.assertEqual('foo', settings.name)
        self.assertIsNone(settings.project_name)
        self.assertIsNone(settings.external_gateway)
        self.assertTrue(settings.admin_state_up)
        self.assertIsNone(settings.enable_snat)
        self.assertIsNotNone(settings.internal_subnets)
        self.assertTrue(isinstance(settings.internal_subnets, list))
        self.assertEqual(0, len(settings.internal_subnets))
        self.assertIsNotNone(settings.port_settings)
        self.assertTrue(isinstance(settings.port_settings, list))
        self.assertEqual(0, len(settings.port_settings))

    def test_all(self):
        port_settings = PortConfig(name='foo', network_name='bar')
        settings = RouterSettings(
            name='foo', project_name='bar', external_gateway='foo_gateway',
            admin_state_up=True, enable_snat=False,
            internal_subnets=['10.0.0.1/24'], interfaces=[port_settings])
        self.assertEqual('foo', settings.name)
        self.assertEqual('bar', settings.project_name)
        self.assertEqual('foo_gateway', settings.external_gateway)
        self.assertTrue(settings.admin_state_up)
        self.assertFalse(settings.enable_snat)
        self.assertIsNotNone(settings.internal_subnets)
        self.assertTrue(isinstance(settings.internal_subnets, list))
        self.assertEqual(1, len(settings.internal_subnets))
        self.assertEqual(['10.0.0.1/24'], settings.internal_subnets)
        self.assertEqual([port_settings], settings.port_settings)

    def test_config_all(self):
        settings = RouterSettings(
            **{'name': 'foo', 'project_name': 'bar',
               'external_gateway': 'foo_gateway', 'admin_state_up': True,
               'enable_snat': False, 'internal_subnets': ['10.0.0.1/24'],
               'interfaces':
                   [{'port': {'name': 'foo-port',
                              'network_name': 'bar-net'}}]})
        self.assertEqual('foo', settings.name)
        self.assertEqual('bar', settings.project_name)
        self.assertEqual('foo_gateway', settings.external_gateway)
        self.assertTrue(settings.admin_state_up)
        self.assertFalse(settings.enable_snat)
        self.assertIsNotNone(settings.internal_subnets)
        self.assertTrue(isinstance(settings.internal_subnets, list))
        self.assertEqual(1, len(settings.internal_subnets))
        self.assertEqual(['10.0.0.1/24'], settings.internal_subnets)
        self.assertEqual(
            [PortConfig(**{'name': 'foo-port', 'network_name': 'bar-net'})],
            settings.port_settings)


class CreateRouterSuccessTests(OSIntegrationTestCase):
    """
    Class for testing routers with various positive scenarios expected to
    succeed
    """

    def setUp(self):
        """
        Initializes objects used for router testing
        """
        super(self.__class__, self).__start__()

        self.guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.router_creator = None
        self.network_creator1 = None
        self.network_creator2 = None
        self.neutron = neutron_utils.neutron_client(
            self.os_creds, self.os_session)

    def tearDown(self):
        """
        Cleans the remote OpenStack objects used for router testing
        """
        if self.router_creator:
            self.router_creator.clean()

        if self.network_creator1:
            self.network_creator1.clean()

        if self.network_creator2:
            self.network_creator2.clean()

        super(self.__class__, self).__clean__()

    def test_create_router_vanilla(self):
        """
        Test creation of a most basic router with minimal options.
        """
        router_settings = RouterConfig(
            name=self.guid + '-pub-router', external_gateway=self.ext_net_name)

        self.router_creator = create_router.OpenStackRouter(
            self.os_creds, router_settings)
        self.router_creator.create()

        router = neutron_utils.get_router(
            self.neutron, self.keystone, router_settings=router_settings,
            project_name=self.os_creds.project_name)
        self.assertIsNotNone(router)

        self.assertEqual(self.router_creator.get_router(), router)

        self.check_router_recreation(router, router_settings)

    def test_create_router_admin_user_to_new_project(self):
        """
        Test creation of a most basic router with the admin user pointing
        to the new project.
        """
        router_settings = RouterConfig(
            name=self.guid + '-pub-router', external_gateway=self.ext_net_name,
            project_name=self.os_creds.project_name)

        self.router_creator = create_router.OpenStackRouter(
            self.admin_os_creds, router_settings)
        self.router_creator.create()

        router = neutron_utils.get_router(
            self.neutron, self.keystone, router_settings=router_settings,
            project_name=self.os_creds.project_name)
        self.assertIsNotNone(router)

        self.assertEqual(self.router_creator.get_router().id, router.id)

        self.check_router_recreation(router, router_settings)

    def test_create_router_new_user_as_admin_project(self):
        """
        Test creation of a most basic router with the new user pointing
        to the admin project.
        """
        router_settings = RouterConfig(
            name=self.guid + '-pub-router', external_gateway=self.ext_net_name,
            project_name=self.os_creds.project_name)

        self.router_creator = create_router.OpenStackRouter(
            self.admin_os_creds, router_settings)
        self.router_creator.create()

        router = neutron_utils.get_router(
            self.neutron, self.keystone, router_settings=router_settings,
            project_name=self.os_creds.project_name)
        self.assertIsNotNone(router)

        self.assertEqual(self.router_creator.get_router().id, router.id)

        self.check_router_recreation(router, router_settings)

    def test_create_delete_router(self):
        """
        Test that clean() will not raise an exception if the router is deleted
        by another process.
        """
        self.router_settings = RouterConfig(
            name=self.guid + '-pub-router', external_gateway=self.ext_net_name)

        self.router_creator = create_router.OpenStackRouter(
            self.os_creds, self.router_settings)
        created_router = self.router_creator.create()
        self.assertIsNotNone(created_router)
        retrieved_router = neutron_utils.get_router(
            self.neutron, self.keystone, router_settings=self.router_settings,
            project_name=self.os_creds.project_name)
        self.assertIsNotNone(retrieved_router)

        neutron_utils.delete_router(self.neutron, created_router)

        retrieved_router = neutron_utils.get_router(
            self.neutron, self.keystone, router_settings=self.router_settings,
            project_name=self.os_creds.project_name)
        self.assertIsNone(retrieved_router)

        # Should not raise an exception
        self.router_creator.clean()

    def test_create_router_admin_state_false(self):
        """
        Test creation of a basic router with admin state down.
        """
        router_settings = RouterConfig(
            name=self.guid + '-pub-router', admin_state_up=False)

        self.router_creator = create_router.OpenStackRouter(self.os_creds,
                                                            router_settings)
        self.router_creator.create()

        router = neutron_utils.get_router(
            self.neutron, self.keystone, router_settings=router_settings,
            project_name=self.os_creds.project_name)
        self.assertIsNotNone(router)

        self.assertEqual(self.router_creator.get_router(), router)

        self.check_router_recreation(router, router_settings)

    def test_create_router_admin_state_True(self):
        """
        Test creation of a basic router with admin state Up.
        """
        router_settings = RouterConfig(
            name=self.guid + '-pub-router', admin_state_up=True)

        self.router_creator = create_router.OpenStackRouter(
            self.os_creds, router_settings)
        self.router_creator.create()

        router = neutron_utils.get_router(
            self.neutron, self.keystone, router_settings=router_settings,
            project_name=self.os_creds.project_name)
        self.assertIsNotNone(router)

        self.assertEqual(self.router_creator.get_router(), router)

        self.check_router_recreation(router, router_settings)

    def test_create_router_private_network(self):
        """
        Test creation of a router connected with two private networks and no
        external gateway
        """
        network_settings1 = NetworkConfig(
            name=self.guid + '-pub-net1',
            subnet_settings=[
                create_network.SubnetConfig(
                    cidr=cidr1, name=self.guid + '-pub-subnet1',
                    gateway_ip=static_gateway_ip1)])
        network_settings2 = NetworkConfig(
            name=self.guid + '-pub-net2',
            subnet_settings=[
                create_network.SubnetConfig(
                    cidr=cidr2, name=self.guid + '-pub-subnet2',
                    gateway_ip=static_gateway_ip2)])

        self.network_creator1 = OpenStackNetwork(self.os_creds,
                                                 network_settings1)
        self.network_creator2 = OpenStackNetwork(self.os_creds,
                                                 network_settings2)

        self.network_creator1.create()
        self.network_creator2.create()

        port_settings = [
            create_network.PortConfig(
                name=self.guid + '-port1',
                ip_addrs=[{
                    'subnet_name':
                        network_settings1.subnet_settings[0].name,
                    'ip': static_gateway_ip1
                }],
                network_name=network_settings1.name),
            create_network.PortConfig(
                name=self.guid + '-port2',
                ip_addrs=[{
                    'subnet_name': network_settings2.subnet_settings[0].name,
                    'ip': static_gateway_ip2
                }],
                network_name=network_settings2.name)]

        router_settings = RouterConfig(
            name=self.guid + '-pub-router', port_settings=port_settings)
        self.router_creator = create_router.OpenStackRouter(
            self.os_creds, router_settings)
        self.router_creator.create()

        router = neutron_utils.get_router(
            self.neutron, self.keystone, router_settings=router_settings,
            project_name=self.os_creds.project_name)

        self.assertEqual(router, self.router_creator.get_router())

        # Instantiate second identical creator to ensure a second router
        # has not been created
        router_creator2 = create_router.OpenStackRouter(
            self.os_creds, router_settings)
        router2 = router_creator2.create()
        self.assertIsNotNone(self.router_creator.get_router(), router2)

        self.check_router_recreation(router2, router_settings)

    def test_create_router_external_network(self):
        """
        Test creation of a router connected to an external network and a
        private network.
        """
        network_settings = NetworkConfig(
            name=self.guid + '-pub-net1',
            subnet_settings=[
                create_network.SubnetConfig(
                    cidr=cidr1, name=self.guid + '-pub-subnet1',
                    gateway_ip=static_gateway_ip1)])
        self.network_creator1 = OpenStackNetwork(self.os_creds,
                                                 network_settings)
        self.network_creator1.create()

        port_settings = [
            create_network.PortConfig(
                name=self.guid + '-port1',
                ip_addrs=[{
                    'subnet_name': network_settings.subnet_settings[0].name,
                    'ip': static_gateway_ip1}],
                network_name=network_settings.name)]

        router_settings = RouterConfig(
            name=self.guid + '-pub-router', external_gateway=self.ext_net_name,
            port_settings=port_settings)
        self.router_creator = create_router.OpenStackRouter(
            self.os_creds, router_settings)
        self.router_creator.create()

        router = neutron_utils.get_router(
            self.neutron, self.keystone, router_settings=router_settings,
            project_name=self.os_creds.project_name)

        self.assertEquals(router, self.router_creator.get_router())

        self.check_router_recreation(router, router_settings)

    def test_create_router_with_ext_port(self):
        """
        Test creation of a router with a port to an external network as an
        'admin' user.
        """
        port_settings = [
            create_network.PortConfig(
                name=self.guid + '-port1',
                network_name=self.ext_net_name)]

        router_settings = RouterConfig(
            name=self.guid + '-pub-router', port_settings=port_settings)
        self.router_creator = create_router.OpenStackRouter(
            self.admin_os_creds, router_settings)
        self.router_creator.create()

        admin_neutron = neutron_utils.neutron_client(
            self.admin_os_creds, self.admin_os_session)
        admin_keystone = keystone_utils.keystone_client(
            self.admin_os_creds, self.admin_os_session)
        router = neutron_utils.get_router(
            admin_neutron, admin_keystone, router_settings=router_settings,
            project_name=self.admin_os_creds.project_name)

        self.assertIsNotNone(router)
        self.assertEquals(router, self.router_creator.get_router())

        ext_net = neutron_utils.get_network(
            admin_neutron, admin_keystone, network_name=self.ext_net_name)

        self.assertIsNotNone(ext_net)
        self.assertIsNotNone(router.port_subnets)

        id_found = False
        for port, subnets in router.port_subnets:
            self.assertIsNotNone(subnets)
            self.assertIsNotNone(port)

            if ext_net.id == port.network_id:
                id_found = True
                for subnet in subnets:
                    self.assertIsNotNone(subnet)
                    self.assertEqual(ext_net.id, subnet.network_id)
        self.assertTrue(id_found)

    def check_router_recreation(self, router, orig_settings):
        """
        Validates the derived RouterConfig with the original
        :param router: the Router domain object to test
        :param orig_settings: the original RouterConfig object that was
                              responsible for creating the router
        :return: the derived RouterConfig object
        """
        derived_settings = settings_utils.create_router_config(
            self.neutron, router)
        self.assertIsNotNone(derived_settings)
        self.assertEqual(
            orig_settings.enable_snat, derived_settings.enable_snat)
        self.assertEqual(orig_settings.external_gateway,
                         derived_settings.external_gateway)
        self.assertEqual(orig_settings.name, derived_settings.name)
        self.assertEqual(orig_settings.internal_subnets,
                         derived_settings.internal_subnets)

        if orig_settings.external_gateway:
            self.assertEqual(len(orig_settings.port_settings),
                             len(derived_settings.port_settings))
        else:
            self.assertEqual(len(orig_settings.port_settings),
                             len(derived_settings.port_settings))

        if len(orig_settings.port_settings) > 0:
            self.assertEqual(orig_settings.port_settings[0].name,
                             derived_settings.port_settings[0].name)

        if len(orig_settings.port_settings) > 1:
            self.assertEqual(orig_settings.port_settings[1].name,
                             derived_settings.port_settings[1].name)

        return derived_settings


class CreateRouterNegativeTests(OSIntegrationTestCase):
    """
    Class for testing routers with various negative scenarios expected to fail.
    """

    def setUp(self):
        """
        Initializes objects used for router testing
        """
        super(self.__class__, self).__start__()

        self.guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.network_creator = None
        self.router_creator = None

    def tearDown(self):
        """
        Cleans the remote OpenStack objects used for router testing
        """
        if self.router_creator:
            self.router_creator.clean()

        if self.network_creator:
            self.network_creator.clean()

        super(self.__class__, self).__clean__()

    def test_create_router_noname(self):
        """
        Test creating a router without a name.
        """
        with self.assertRaises(RouterConfigError):
            router_settings = RouterConfig(
                name=None, external_gateway=self.ext_net_name)
            self.router_creator = create_router.OpenStackRouter(
                self.os_creds, router_settings)
            self.router_creator.create()

    def test_create_router_invalid_gateway_name(self):
        """
        Test creating a router without a valid network gateway name.
        """
        with self.assertRaises(RouterConfigError):
            router_settings = RouterConfig(
                name=self.guid + '-pub-router',
                external_gateway="Invalid_name")
            self.router_creator = create_router.OpenStackRouter(
                self.os_creds, router_settings)
            self.router_creator.create()

    def test_create_router_admin_ports(self):
        """
        Test creation of a router with ports to subnets owned by the admin
        project
        """
        network_settings = NetworkConfig(
            name=self.guid + '-pub-net1',
            subnet_settings=[
                create_network.SubnetConfig(
                    cidr=cidr1, name=self.guid + '-pub-subnet1',
                    gateway_ip=static_gateway_ip1)])
        self.network_creator = OpenStackNetwork(
            self.admin_os_creds, network_settings)
        self.network_creator.create()

        port_settings = [
            create_network.PortConfig(
                name=self.guid + '-port1',
                ip_addrs=[{
                    'subnet_name': network_settings.subnet_settings[0].name,
                    'ip': static_gateway_ip1}],
                network_name=network_settings.name)]

        router_settings = RouterConfig(
            name=self.guid + '-pub-router', external_gateway=self.ext_net_name,
            port_settings=port_settings)
        self.router_creator = create_router.OpenStackRouter(
            self.os_creds, router_settings)

        with self.assertRaises(PortConfigError):
            self.router_creator.create()


class CreateMultipleRouterTests(OSIntegrationTestCase):
    """
    Test for the OpenStackRouter class and how it interacts with routers
    groups within other projects with the same name
    """

    def setUp(self):
        """
        Initializes objects used for router testing
        """
        super(self.__class__, self).__start__()

        self.guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.admin_router_creator = None
        self.proj_router_creator = None
        self.neutron = neutron_utils.neutron_client(
            self.os_creds, self.os_session)

        network_settings = NetworkConfig(
            name=self.guid + '-pub-net', shared=True,
            subnet_settings=[
                create_network.SubnetConfig(
                    cidr=cidr1, name=self.guid + '-pub-subnet',
                    gateway_ip=static_gateway_ip1)])

        self.network_creator = OpenStackNetwork(
            self.admin_os_creds, network_settings)
        self.network_creator.create()

    def tearDown(self):
        """
        Cleans the remote OpenStack objects used for router testing
        """
        if self.admin_router_creator:
            self.admin_router_creator.clean()

        if self.proj_router_creator:
            self.proj_router_creator.clean()

        if self.network_creator:
            self.network_creator.clean()

        super(self.__class__, self).__clean__()

    def test_router_same_name_diff_proj(self):
        """
        Tests the creation of an OpenStackNetwork with the same name
        within a different project/tenant when not configured but implied by
        the OSCreds.
        """
        # Create Router

        router_config = RouterConfig(name=self.guid + '-router')
        self.admin_router_creator = OpenStackRouter(
            self.admin_os_creds, router_config)
        self.admin_router_creator.create()

        self.proj_router_creator = OpenStackRouter(
            self.os_creds, router_config)
        self.proj_router_creator.create()

        self.assertNotEqual(
            self.admin_router_creator.get_router().id,
            self.proj_router_creator.get_router().id)

        admin_creator2 = OpenStackRouter(
            self.admin_os_creds, router_config)
        admin_creator2.create()
        self.assertEqual(
            self.admin_router_creator.get_router(),
            admin_creator2.get_router())

        proj_creator2 = OpenStackRouter(self.os_creds, router_config)
        proj_creator2.create()
        self.assertEqual(self.proj_router_creator.get_router(),
                         proj_creator2.get_router())

    def test_router_create_by_admin_to_different_project(self):
        """
        Tests the creation of an OpenStackRouter by the admin user and
        initialize again with tenant credentials.
        """
        # Create Network

        admin_router_config = RouterConfig(
            name=self.guid + '-router',
            project_name=self.os_creds.project_name)

        self.admin_router_creator = OpenStackRouter(
            self.admin_os_creds, admin_router_config)
        self.admin_router_creator.create()

        proj_router_config = RouterConfig(
            name=self.guid + '-router',
            project_name=self.os_creds.project_name)

        self.proj_router_creator = OpenStackRouter(
            self.os_creds, proj_router_config)
        self.proj_router_creator.create()

        self.assertEqual(
            self.admin_router_creator.get_router().id,
            self.proj_router_creator.get_router().id)


class CreateRouterSecurityGroupTests(OSIntegrationTestCase):
    """
    Class for testing routers with ports containing security groups
    """

    def setUp(self):
        """
        Initializes objects used for router testing
        """
        super(self.__class__, self).__start__()

        self.guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.router_creator = None
        self.network_creator = None

        self.sec_grp_creator = OpenStackSecurityGroup(
            self.os_creds, SecurityGroupConfig(name=self.guid + '-sec_grp'))
        self.sec_grp_creator.create()

        self.neutron = neutron_utils.neutron_client(
            self.os_creds, self.os_session)

    def tearDown(self):
        """
        Cleans the remote OpenStack objects used for router testing
        """
        if self.router_creator:
            self.router_creator.clean()

        if self.network_creator:
            self.network_creator.clean()

        if self.sec_grp_creator:
            self.sec_grp_creator.clean()

        super(self.__class__, self).__clean__()

    def test_create_router_secure_port(self):
        """
        Test creation of a router with a port that has a security group.
        """
        network_settings = NetworkConfig(
            name=self.guid + '-pub-net1',
            subnet_settings=[
                create_network.SubnetConfig(
                    cidr=cidr1, name=self.guid + '-pub-subnet1')])
        self.network_creator = OpenStackNetwork(
            self.os_creds, network_settings)
        self.network_creator.create()

        port_settings = [
            create_network.PortConfig(
                name=self.guid + '-port1',
                ip_addrs=[{
                    'subnet_name': network_settings.subnet_settings[0].name,
                    'ip': static_gateway_ip1}],
                network_name=network_settings.name,
                security_groups=[self.sec_grp_creator.sec_grp_settings.name])]

        router_settings = RouterConfig(
            name=self.guid + '-pub-router', external_gateway=self.ext_net_name,
            port_settings=port_settings)
        self.router_creator = create_router.OpenStackRouter(
            self.os_creds, router_settings)
        self.router_creator.create()
