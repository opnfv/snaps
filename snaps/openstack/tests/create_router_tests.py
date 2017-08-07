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

from snaps.openstack import create_network
from snaps.openstack import create_router
from snaps.openstack.create_network import (
    NetworkSettings, PortSettings)
from snaps.openstack.create_network import OpenStackNetwork
from snaps.openstack.create_router import (
    RouterSettings, RouterSettingsError)
from snaps.openstack.tests.os_source_file_test import OSIntegrationTestCase
from snaps.openstack.utils import neutron_utils

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
        with self.assertRaises(RouterSettingsError):
            RouterSettings()

    def test_empty_config(self):
        with self.assertRaises(RouterSettingsError):
            RouterSettings(**dict())

    def test_name_only(self):
        settings = RouterSettings(name='foo')
        self.assertEqual('foo', settings.name)
        self.assertIsNone(settings.project_name)
        self.assertIsNone(settings.external_gateway)
        self.assertIsNone(settings.admin_state_up)
        self.assertIsNone(settings.enable_snat)
        self.assertIsNone(settings.external_fixed_ips)
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
        self.assertIsNone(settings.admin_state_up)
        self.assertIsNone(settings.enable_snat)
        self.assertIsNone(settings.external_fixed_ips)
        self.assertIsNotNone(settings.internal_subnets)
        self.assertTrue(isinstance(settings.internal_subnets, list))
        self.assertEqual(0, len(settings.internal_subnets))
        self.assertIsNotNone(settings.port_settings)
        self.assertTrue(isinstance(settings.port_settings, list))
        self.assertEqual(0, len(settings.port_settings))

    def test_all(self):
        port_settings = PortSettings(name='foo', network_name='bar')
        settings = RouterSettings(
            name='foo', project_name='bar', external_gateway='foo_gateway',
            admin_state_up=True, enable_snat=False, external_fixed_ips=['ip1'],
            internal_subnets=['10.0.0.1/24'], interfaces=[port_settings])
        self.assertEqual('foo', settings.name)
        self.assertEqual('bar', settings.project_name)
        self.assertEqual('foo_gateway', settings.external_gateway)
        self.assertTrue(settings.admin_state_up)
        self.assertFalse(settings.enable_snat)
        self.assertEqual(['ip1'], settings.external_fixed_ips)
        self.assertIsNotNone(settings.internal_subnets)
        self.assertTrue(isinstance(settings.internal_subnets, list))
        self.assertEqual(1, len(settings.internal_subnets))
        self.assertEqual(['10.0.0.1/24'], settings.internal_subnets)
        self.assertEqual([port_settings], settings.port_settings)

    def test_config_all(self):
        settings = RouterSettings(
            **{'name': 'foo', 'project_name': 'bar',
               'external_gateway': 'foo_gateway', 'admin_state_up': True,
               'enable_snat': False, 'external_fixed_ips': ['ip1'],
               'internal_subnets': ['10.0.0.1/24'],
               'interfaces':
                   [{'port': {'name': 'foo-port',
                              'network_name': 'bar-net'}}]})
        self.assertEqual('foo', settings.name)
        self.assertEqual('bar', settings.project_name)
        self.assertEqual('foo_gateway', settings.external_gateway)
        self.assertTrue(settings.admin_state_up)
        self.assertFalse(settings.enable_snat)
        self.assertEqual(['ip1'], settings.external_fixed_ips)
        self.assertIsNotNone(settings.internal_subnets)
        self.assertTrue(isinstance(settings.internal_subnets, list))
        self.assertEqual(1, len(settings.internal_subnets))
        self.assertEqual(['10.0.0.1/24'], settings.internal_subnets)
        self.assertEqual([PortSettings(**{'name': 'foo-port',
                                          'network_name': 'bar-net'})],
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
        self.neutron = neutron_utils.neutron_client(self.os_creds)

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
        router_settings = RouterSettings(name=self.guid + '-pub-router',
                                         external_gateway=self.ext_net_name)

        self.router_creator = create_router.OpenStackRouter(self.os_creds,
                                                            router_settings)
        self.router_creator.create()

        router = neutron_utils.get_router(self.neutron,
                                          router_settings=router_settings)
        self.assertIsNotNone(router)

        self.assertTrue(verify_router_attributes(
            router, self.router_creator, ext_gateway=self.ext_net_name))

    def test_create_router_admin_user_to_new_project(self):
        """
        Test creation of a most basic router with the admin user pointing
        to the new project.
        """
        router_settings = RouterSettings(
            name=self.guid + '-pub-router', external_gateway=self.ext_net_name,
            project_name=self.os_creds.project_name)

        self.router_creator = create_router.OpenStackRouter(
            self.admin_os_creds, router_settings)
        self.router_creator.create()

        router = neutron_utils.get_router(self.neutron,
                                          router_settings=router_settings)
        self.assertIsNotNone(router)

        self.assertTrue(verify_router_attributes(
            router, self.router_creator, ext_gateway=self.ext_net_name))

    def test_create_router_new_user_to_admin_project(self):
        """
        Test creation of a most basic router with the new user pointing
        to the admin project.
        """
        router_settings = RouterSettings(
            name=self.guid + '-pub-router', external_gateway=self.ext_net_name,
            project_name=self.admin_os_creds.project_name)

        self.router_creator = create_router.OpenStackRouter(
            self.os_creds, router_settings)
        self.router_creator.create()

        router = neutron_utils.get_router(self.neutron,
                                          router_settings=router_settings)
        self.assertIsNotNone(router)

        self.assertTrue(verify_router_attributes(
            router, self.router_creator, ext_gateway=self.ext_net_name))

    def test_create_delete_router(self):
        """
        Test that clean() will not raise an exception if the router is deleted
        by another process.
        """
        self.router_settings = RouterSettings(
            name=self.guid + '-pub-router', external_gateway=self.ext_net_name)

        self.router_creator = create_router.OpenStackRouter(
            self.os_creds, self.router_settings)
        created_router = self.router_creator.create()
        self.assertIsNotNone(created_router)
        retrieved_router = neutron_utils.get_router(
            self.neutron, router_settings=self.router_settings)
        self.assertIsNotNone(retrieved_router)

        neutron_utils.delete_router(self.neutron, created_router)

        retrieved_router = neutron_utils.get_router(
            self.neutron, router_settings=self.router_settings)
        self.assertIsNone(retrieved_router)

        # Should not raise an exception
        self.router_creator.clean()

    def test_create_router_admin_state_false(self):
        """
        Test creation of a basic router with admin state down.
        """
        router_settings = RouterSettings(name=self.guid + '-pub-router',
                                         admin_state_up=False)

        self.router_creator = create_router.OpenStackRouter(self.os_creds,
                                                            router_settings)
        self.router_creator.create()

        router = neutron_utils.get_router(self.neutron,
                                          router_settings=router_settings)
        self.assertIsNotNone(router)

        self.assertTrue(verify_router_attributes(router, self.router_creator,
                                                 admin_state=False))

    def test_create_router_admin_state_True(self):
        """
        Test creation of a basic router with admin state Up.
        """
        router_settings = RouterSettings(name=self.guid + '-pub-router',
                                         admin_state_up=True)

        self.router_creator = create_router.OpenStackRouter(self.os_creds,
                                                            router_settings)
        self.router_creator.create()

        router = neutron_utils.get_router(self.neutron,
                                          router_settings=router_settings)
        self.assertIsNotNone(router)

        self.assertTrue(verify_router_attributes(router, self.router_creator,
                                                 admin_state=True))

    def test_create_router_private_network(self):
        """
        Test creation of a router connected with two private networks and no
        external gateway
        """
        network_settings1 = NetworkSettings(
            name=self.guid + '-pub-net1',
            subnet_settings=[
                create_network.SubnetSettings(
                    cidr=cidr1, name=self.guid + '-pub-subnet1',
                    gateway_ip=static_gateway_ip1)])
        network_settings2 = NetworkSettings(
            name=self.guid + '-pub-net2',
            subnet_settings=[
                create_network.SubnetSettings(
                    cidr=cidr2, name=self.guid + '-pub-subnet2',
                    gateway_ip=static_gateway_ip2)])

        self.network_creator1 = OpenStackNetwork(self.os_creds,
                                                 network_settings1)
        self.network_creator2 = OpenStackNetwork(self.os_creds,
                                                 network_settings2)

        self.network_creator1.create()
        self.network_creator2.create()

        port_settings = [
            create_network.PortSettings(
                name=self.guid + '-port1',
                ip_addrs=[{
                    'subnet_name':
                        network_settings1.subnet_settings[0].name,
                    'ip': static_gateway_ip1
                }],
                network_name=network_settings1.name,
                project_name=self.os_creds.project_name),
            create_network.PortSettings(
                name=self.guid + '-port2',
                ip_addrs=[{
                    'subnet_name': network_settings2.subnet_settings[0].name,
                    'ip': static_gateway_ip2
                }],
                network_name=network_settings2.name,
                project_name=self.os_creds.project_name)]

        router_settings = RouterSettings(name=self.guid + '-pub-router',
                                         port_settings=port_settings)
        self.router_creator = create_router.OpenStackRouter(self.os_creds,
                                                            router_settings)
        self.router_creator.create()

        router = neutron_utils.get_router(self.neutron,
                                          router_settings=router_settings)

        self.assertTrue(verify_router_attributes(router, self.router_creator))

        # Instantiate second identical creator to ensure a second router
        # has not been created
        router_creator2 = create_router.OpenStackRouter(
            self.os_creds, router_settings)
        router2 = router_creator2.create()
        self.assertIsNotNone(self.router_creator.get_router(), router2)

    def test_create_router_external_network(self):
        """
        Test creation of a router connected to an external network and a
        private network.
        """
        network_settings = NetworkSettings(
            name=self.guid + '-pub-net1',
            subnet_settings=[
                create_network.SubnetSettings(
                    cidr=cidr1, name=self.guid + '-pub-subnet1',
                    gateway_ip=static_gateway_ip1)])
        self.network_creator1 = OpenStackNetwork(self.os_creds,
                                                 network_settings)
        self.network_creator1.create()

        port_settings = [
            create_network.PortSettings(
                name=self.guid + '-port1',
                ip_addrs=[{
                    'subnet_name': network_settings.subnet_settings[0].name,
                    'ip': static_gateway_ip1}],
                network_name=network_settings.name,
                project_name=self.os_creds.project_name)]

        router_settings = RouterSettings(
            name=self.guid + '-pub-router', external_gateway=self.ext_net_name,
            port_settings=port_settings)
        self.router_creator = create_router.OpenStackRouter(self.os_creds,
                                                            router_settings)
        self.router_creator.create()

        router = neutron_utils.get_router(self.neutron,
                                          router_settings=router_settings)

        self.assertTrue(verify_router_attributes(
            router, self.router_creator, ext_gateway=self.ext_net_name))


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
        self.router_creator = None

    def tearDown(self):
        """
        Cleans the remote OpenStack objects used for router testing
        """
        if self.router_creator:
            self.router_creator.clean()

        super(self.__class__, self).__clean__()

    def test_create_router_noname(self):
        """
        Test creating a router without a name.
        """
        with self.assertRaises(RouterSettingsError):
            router_settings = RouterSettings(
                name=None, external_gateway=self.ext_net_name)
            self.router_creator = create_router.OpenStackRouter(
                self.os_creds, router_settings)
            self.router_creator.create()

    def test_create_router_invalid_gateway_name(self):
        """
        Test creating a router without a valid network gateway name.
        """
        with self.assertRaises(RouterSettingsError):
            router_settings = RouterSettings(name=self.guid + '-pub-router',
                                             external_gateway="Invalid_name")
            self.router_creator = create_router.OpenStackRouter(
                self.os_creds, router_settings)
            self.router_creator.create()


def verify_router_attributes(router_operational, router_creator,
                             admin_state=True, ext_gateway=None):
    """
    Helper function to validate the attributes of router created with the one
    operational
    :param router_operational: Operational Router object returned from neutron
                               utils of type snaps.domain.Router
    :param router_creator: router_creator object returned from creating a
                           router in the router test functions
    :param admin_state: True if router is expected to be Up, else False
    :param ext_gateway: None if router is not connected to external gateway
    :return:
    """

    router = router_creator.get_router()

    if not router_operational:
        return False
    elif not router_creator:
        return False
    elif not (router_operational.name == router_creator.router_settings.name):
        return False
    elif not (router_operational.id == router.id):
        return False
    elif not (router_operational.status == router.status):
        return False
    elif not (router_operational.tenant_id == router.tenant_id):
        return False
    elif not (admin_state == router_operational.admin_state_up):
        return False
    elif (ext_gateway is None) and \
            (router_operational.external_gateway_info is not None):
        return False
    elif ext_gateway is not None:
        if router_operational.external_gateway_info is None:
            return False
    return True
