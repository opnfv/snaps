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
import logging
import re
import shutil
import time
import unittest
import uuid

import os
from neutronclient.common.exceptions import (
    InvalidIpForSubnetClient, BadRequest)

from snaps import file_utils
from snaps.config.flavor import FlavorConfig
from snaps.config.image import ImageConfig
from snaps.config.keypair import KeypairConfig
from snaps.config.network import PortConfig, NetworkConfig, SubnetConfig
from snaps.config.router import RouterConfig
from snaps.config.security_group import (
    Protocol, SecurityGroupRuleConfig, Direction, SecurityGroupConfig)
from snaps.config.vm_inst import (
    VmInstanceConfig, FloatingIpConfig,  VmInstanceConfigError,
    FloatingIpConfigError)
from snaps.config.volume import VolumeConfig
from snaps.openstack import create_network, create_router, create_instance
from snaps.openstack.create_flavor import OpenStackFlavor
from snaps.openstack.create_image import OpenStackImage
from snaps.openstack.create_instance import (
    VmInstanceSettings, OpenStackVmInstance, FloatingIpSettings)
from snaps.openstack.create_keypairs import OpenStackKeypair
from snaps.openstack.create_network import OpenStackNetwork
from snaps.openstack.create_router import OpenStackRouter
from snaps.openstack.create_security_group import OpenStackSecurityGroup
from snaps.openstack.create_volume import OpenStackVolume
from snaps.openstack.tests import openstack_tests, validation_utils
from snaps.openstack.tests.os_source_file_test import (
    OSIntegrationTestCase, OSComponentTestCase)
from snaps.openstack.utils import nova_utils, keystone_utils, neutron_utils
from snaps.openstack.utils.nova_utils import RebootType
from snaps.openstack.utils import nova_utils, settings_utils, neutron_utils

__author__ = 'spisarski'

VM_BOOT_TIMEOUT = 600

logger = logging.getLogger('create_instance_tests')


class VmInstanceSettingsUnitTests(unittest.TestCase):
    """
    Tests the construction of the VmInstanceSettings class
    """

    def test_no_params(self):
        with self.assertRaises(VmInstanceConfigError):
            VmInstanceSettings()

    def test_empty_config(self):
        with self.assertRaises(VmInstanceConfigError):
            VmInstanceSettings(config=dict())

    def test_name_only(self):
        with self.assertRaises(VmInstanceConfigError):
            VmInstanceSettings(name='foo')

    def test_config_with_name_only(self):
        with self.assertRaises(VmInstanceConfigError):
            VmInstanceSettings(config={'name': 'foo'})

    def test_name_flavor_only(self):
        with self.assertRaises(VmInstanceConfigError):
            VmInstanceSettings(name='foo', flavor='bar')

    def test_config_with_name_flavor_only(self):
        with self.assertRaises(VmInstanceConfigError):
            VmInstanceSettings(config={'name': 'foo', 'flavor': 'bar'})

    def test_name_flavor_port_only(self):
        port_settings = PortConfig(name='foo-port', network_name='bar-net')
        settings = VmInstanceSettings(name='foo', flavor='bar',
                                      port_settings=[port_settings])
        self.assertEqual('foo', settings.name)
        self.assertEqual('bar', settings.flavor)
        self.assertEqual(1, len(settings.port_settings))
        self.assertEqual('foo-port', settings.port_settings[0].name)
        self.assertEqual('bar-net', settings.port_settings[0].network_name)
        self.assertEqual(0, len(settings.security_group_names))
        self.assertEqual(0, len(settings.floating_ip_settings))
        self.assertIsNone(settings.sudo_user)
        self.assertEqual(900, settings.vm_boot_timeout)
        self.assertEqual(300, settings.vm_delete_timeout)
        self.assertEqual(180, settings.ssh_connect_timeout)
        self.assertIsNone(settings.availability_zone)
        self.assertIsNone(settings.volume_names)

    def test_config_with_name_flavor_port_only(self):
        port_settings = PortConfig(name='foo-port', network_name='bar-net')
        settings = VmInstanceSettings(
            **{'name': 'foo', 'flavor': 'bar', 'ports': [port_settings]})
        self.assertEqual('foo', settings.name)
        self.assertEqual('bar', settings.flavor)
        self.assertEqual(1, len(settings.port_settings))
        self.assertEqual('foo-port', settings.port_settings[0].name)
        self.assertEqual('bar-net', settings.port_settings[0].network_name)
        self.assertEqual(0, len(settings.security_group_names))
        self.assertEqual(0, len(settings.floating_ip_settings))
        self.assertIsNone(settings.sudo_user)
        self.assertEqual(900, settings.vm_boot_timeout)
        self.assertEqual(300, settings.vm_delete_timeout)
        self.assertEqual(180, settings.ssh_connect_timeout)
        self.assertIsNone(settings.availability_zone)
        self.assertIsNone(settings.volume_names)

    def test_all(self):
        port_settings = PortConfig(name='foo-port', network_name='bar-net')
        fip_settings = FloatingIpSettings(name='foo-fip', port_name='bar-port',
                                          router_name='foo-bar-router')

        settings = VmInstanceSettings(
            name='foo', flavor='bar', port_settings=[port_settings],
            security_group_names=['sec_grp_1'],
            floating_ip_settings=[fip_settings], sudo_user='joe',
            vm_boot_timeout=999, vm_delete_timeout=333,
            ssh_connect_timeout=111, availability_zone='server name',
            volume_names=['vol1'])
        self.assertEqual('foo', settings.name)
        self.assertEqual('bar', settings.flavor)
        self.assertEqual(1, len(settings.port_settings))
        self.assertEqual('foo-port', settings.port_settings[0].name)
        self.assertEqual('bar-net', settings.port_settings[0].network_name)
        self.assertEqual(1, len(settings.security_group_names))
        self.assertEqual('sec_grp_1', settings.security_group_names[0])
        self.assertEqual(1, len(settings.floating_ip_settings))
        self.assertEqual('foo-fip', settings.floating_ip_settings[0].name)
        self.assertEqual('bar-port',
                         settings.floating_ip_settings[0].port_name)
        self.assertEqual('foo-bar-router',
                         settings.floating_ip_settings[0].router_name)
        self.assertEqual('joe', settings.sudo_user)
        self.assertEqual(999, settings.vm_boot_timeout)
        self.assertEqual(333, settings.vm_delete_timeout)
        self.assertEqual(111, settings.ssh_connect_timeout)
        self.assertEqual('server name', settings.availability_zone)
        self.assertEqual('vol1', settings.volume_names[0])

    def test_config_all(self):
        port_settings = PortConfig(name='foo-port', network_name='bar-net')
        fip_settings = FloatingIpSettings(name='foo-fip', port_name='bar-port',
                                          router_name='foo-bar-router')

        settings = VmInstanceSettings(
            **{'name': 'foo', 'flavor': 'bar', 'ports': [port_settings],
               'security_group_names': ['sec_grp_1'],
               'floating_ips': [fip_settings], 'sudo_user': 'joe',
               'vm_boot_timeout': 999, 'vm_delete_timeout': 333,
               'ssh_connect_timeout': 111, 'availability_zone': 'server name',
               'volume_names': ['vol2']})
        self.assertEqual('foo', settings.name)
        self.assertEqual('bar', settings.flavor)
        self.assertEqual(1, len(settings.port_settings))
        self.assertEqual('foo-port', settings.port_settings[0].name)
        self.assertEqual('bar-net', settings.port_settings[0].network_name)
        self.assertEqual(1, len(settings.security_group_names))
        self.assertEqual(1, len(settings.floating_ip_settings))
        self.assertEqual('foo-fip', settings.floating_ip_settings[0].name)
        self.assertEqual('bar-port',
                         settings.floating_ip_settings[0].port_name)
        self.assertEqual('foo-bar-router',
                         settings.floating_ip_settings[0].router_name)
        self.assertEqual('joe', settings.sudo_user)
        self.assertEqual(999, settings.vm_boot_timeout)
        self.assertEqual(333, settings.vm_delete_timeout)
        self.assertEqual(111, settings.ssh_connect_timeout)
        self.assertEqual('server name', settings.availability_zone)
        self.assertEqual('vol2', settings.volume_names[0])


class FloatingIpSettingsUnitTests(unittest.TestCase):
    """
    Tests the construction of the FloatingIpSettings class
    """

    def test_no_params(self):
        with self.assertRaises(FloatingIpConfigError):
            FloatingIpSettings()

    def test_empty_config(self):
        with self.assertRaises(FloatingIpConfigError):
            FloatingIpSettings(**dict())

    def test_name_only(self):
        with self.assertRaises(FloatingIpConfigError):
            FloatingIpSettings(name='foo')

    def test_config_with_name_only(self):
        with self.assertRaises(FloatingIpConfigError):
            FloatingIpSettings(**{'name': 'foo'})

    def test_name_port_only(self):
        with self.assertRaises(FloatingIpConfigError):
            FloatingIpSettings(name='foo', port_name='bar')

    def test_config_with_name_port_only(self):
        with self.assertRaises(FloatingIpConfigError):
            FloatingIpSettings(**{'name': 'foo', 'port_name': 'bar'})

    def test_name_router_only(self):
        with self.assertRaises(FloatingIpConfigError):
            FloatingIpSettings(name='foo', router_name='bar')

    def test_config_with_name_router_only(self):
        with self.assertRaises(FloatingIpConfigError):
            FloatingIpSettings(**{'name': 'foo', 'router_name': 'bar'})

    def test_name_port_router_name_only(self):
        settings = FloatingIpSettings(name='foo', port_name='foo-port',
                                      router_name='bar-router')
        self.assertEqual('foo', settings.name)
        self.assertEqual('foo-port', settings.port_name)
        self.assertIsNone(settings.port_id)
        self.assertEqual('bar-router', settings.router_name)
        self.assertIsNone(settings.subnet_name)
        self.assertTrue(settings.provisioning)

    def test_name_port_router_id_only(self):
        settings = FloatingIpSettings(name='foo', port_id='foo-port',
                                      router_name='bar-router')
        self.assertEqual('foo', settings.name)
        self.assertEqual('foo-port', settings.port_id)
        self.assertIsNone(settings.port_name)
        self.assertEqual('bar-router', settings.router_name)
        self.assertIsNone(settings.subnet_name)
        self.assertTrue(settings.provisioning)

    def test_config_with_name_port_router_only(self):
        settings = FloatingIpSettings(
            **{'name': 'foo', 'port_name': 'foo-port',
               'router_name': 'bar-router'})
        self.assertEqual('foo', settings.name)
        self.assertEqual('foo-port', settings.port_name)
        self.assertIsNone(settings.port_id)
        self.assertEqual('bar-router', settings.router_name)
        self.assertIsNone(settings.subnet_name)
        self.assertTrue(settings.provisioning)

    def test_all(self):
        settings = FloatingIpSettings(name='foo', port_name='foo-port',
                                      router_name='bar-router',
                                      subnet_name='bar-subnet',
                                      provisioning=False)
        self.assertEqual('foo', settings.name)
        self.assertEqual('foo-port', settings.port_name)
        self.assertIsNone(settings.port_id)
        self.assertEqual('bar-router', settings.router_name)
        self.assertEqual('bar-subnet', settings.subnet_name)
        self.assertFalse(settings.provisioning)

    def test_config_all(self):
        settings = FloatingIpSettings(
            **{'name': 'foo', 'port_name': 'foo-port',
               'router_name': 'bar-router', 'subnet_name': 'bar-subnet',
               'provisioning': False})
        self.assertEqual('foo', settings.name)
        self.assertEqual('foo-port', settings.port_name)
        self.assertIsNone(settings.port_id)
        self.assertEqual('bar-router', settings.router_name)
        self.assertEqual('bar-subnet', settings.subnet_name)
        self.assertFalse(settings.provisioning)


class SimpleHealthCheck(OSIntegrationTestCase):
    """
    Test for the CreateInstance class with a single NIC/Port with Floating IPs
    """

    def setUp(self):
        """
        Instantiates the CreateImage object that is responsible for downloading
        and creating an OS image file
        within OpenStack
        """
        super(self.__class__, self).__start__()

        self.nova = nova_utils.nova_client(self.os_creds, self.os_session)
        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.vm_inst_name = guid + '-inst'
        self.port_1_name = guid + 'port-1'

        # Initialize for tearDown()
        self.image_creator = None
        self.network_creator = None
        self.flavor_creator = None
        self.inst_creator = None

        self.priv_net_config = openstack_tests.get_priv_net_config(
            project_name=self.os_creds.project_name,
            net_name=guid + '-priv-net',
            subnet_name=guid + '-priv-subnet',
            netconf_override=self.netconf_override)
        self.port_settings = PortConfig(
            name=self.port_1_name,
            network_name=self.priv_net_config.network_settings.name)

        # Create Image
        # Set the default image settings, then set any custom parameters sent
        # from the app
        os_image_settings = openstack_tests.cirros_image_settings(
            name=guid + '-image', image_metadata=self.image_metadata)

        try:
            self.image_creator = OpenStackImage(self.os_creds,
                                                os_image_settings)
            self.image_creator.create()

            # Create Network
            self.network_creator = OpenStackNetwork(
                self.os_creds, self.priv_net_config.network_settings)
            self.network_creator.create()

            # Create Flavor
            self.flavor_ram = 256
            if (self.flavor_metadata and
               self.flavor_metadata.get('hw:mem_page_size') == 'large'):
                self.flavor_ram = 1024
            self.flavor_creator = OpenStackFlavor(
                self.admin_os_creds,
                FlavorConfig(name=guid + '-flavor-name', ram=self.flavor_ram,
                             disk=10, vcpus=1, metadata=self.flavor_metadata))
            self.flavor_creator.create()
        except Exception as e:
            self.tearDown()
            raise e

    def tearDown(self):
        """
        Cleans the created object
        """
        if self.inst_creator:
            try:
                self.inst_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning VM instance with message'
                    ' - %s', e)

        if self.network_creator:
            try:
                self.network_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning network with message - %s',
                    e)

        if self.flavor_creator:
            try:
                self.flavor_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning flavor with message - %s',
                    e)

        if self.image_creator and not self.image_creator.image_settings.exists:
            try:
                self.image_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning image with message - %s',
                    e)

        super(self.__class__, self).__clean__()

    def test_check_vm_ip_dhcp(self):
        """
        Tests the creation of an OpenStack instance with a single port and
        ensures that it's assigned IP address is the actual.
        """
        instance_settings = VmInstanceConfig(
            name=self.vm_inst_name,
            flavor=self.flavor_creator.flavor_settings.name,
            port_settings=[self.port_settings])

        self.inst_creator = OpenStackVmInstance(
            self.os_creds, instance_settings,
            self.image_creator.image_settings)
        self.inst_creator.create()

        ip = self.inst_creator.get_port_ip(self.port_settings.name)
        self.assertIsNotNone(ip)

        self.assertTrue(self.inst_creator.vm_active(block=True))

        self.assertTrue(check_dhcp_lease(self.inst_creator, ip))


class CreateInstanceSimpleTests(OSIntegrationTestCase):
    """
    Simple instance creation tests without any other objects
    """

    def setUp(self):
        """
        Setup the objects required for the test
        """
        super(self.__class__, self).__start__()

        self.guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.vm_inst_name = self.guid + '-inst'
        self.nova = nova_utils.nova_client(self.os_creds)
        self.neutron = neutron_utils.neutron_client(self.os_creds)
        os_image_settings = openstack_tests.cirros_image_settings(
            name=self.guid + '-image', image_metadata=self.image_metadata)

        # Initialize for tearDown()
        self.image_creator = None
        self.flavor_creator = None

        self.network_creator = None
        self.inst_creator = None

        try:
            # Create Image
            self.image_creator = OpenStackImage(self.os_creds,
                                                os_image_settings)
            self.image_creator.create()

            # Create Flavor
            self.flavor_creator = OpenStackFlavor(
                self.admin_os_creds,
                FlavorConfig(name=self.guid + '-flavor-name', ram=256, disk=10,
                             vcpus=2, metadata=self.flavor_metadata))
            self.flavor_creator.create()
            self.network_creator = None
        except Exception as e:
            self.tearDown()
            raise e

    def tearDown(self):
        """
        Cleans the created object
        """
        if self.inst_creator:
            try:
                self.inst_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning VM instance with message '
                    '- %s', e)

        if self.flavor_creator:
            try:
                self.flavor_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning flavor with message - %s',
                    e)

        if self.network_creator:
            try:
                self.network_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning network with message - %s',
                    e)

        if self.image_creator and not self.image_creator.image_settings.exists:
            try:
                self.image_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning image with message - %s', e)

        super(self.__class__, self).__clean__()

    def test_create_delete_instance(self):
        """
        Tests the creation of an OpenStack instance with a single port with a
        static IP without a Floating IP.
        """
        # Create Network
        net_config = openstack_tests.get_priv_net_config(
            project_name=self.os_creds.project_name,
            net_name=self.guid + '-pub-net',
            subnet_name=self.guid + '-pub-subnet',
            router_name=self.guid + '-pub-router',
            external_net=self.ext_net_name,
            netconf_override=self.netconf_override)
        self.network_creator = OpenStackNetwork(
            self.os_creds, net_config.network_settings)
        self.network_creator.create()

        self.port_settings = PortConfig(
            name=self.guid + '-port',
            network_name=net_config.network_settings.name)

        instance_settings = VmInstanceConfig(
            name=self.vm_inst_name,
            flavor=self.flavor_creator.flavor_settings.name,
            port_settings=[self.port_settings])

        self.inst_creator = OpenStackVmInstance(
            self.os_creds, instance_settings,
            self.image_creator.image_settings)

        vm_inst = self.inst_creator.create(block=True)
        vm_inst_get = nova_utils.get_server(
            self.nova, self.neutron, self.keystone,
            vm_inst_settings=instance_settings)
        self.assertEqual(vm_inst, vm_inst_get)

        self.assertIsNotNone(self.inst_creator.get_vm_inst().availability_zone)
        self.assertIsNone(self.inst_creator.get_vm_inst().compute_host)

        # Delete instance
        nova_utils.delete_vm_instance(self.nova, vm_inst)

        self.assertTrue(self.inst_creator.vm_deleted(block=True))
        self.assertIsNone(nova_utils.get_server(
            self.nova, self.neutron, self.keystone,
            vm_inst_settings=instance_settings))

        # Exception should not be thrown
        self.inst_creator.clean()

    def test_create_admin_instance(self):
        """
        Tests the creation of an OpenStack instance with a single port with a
        static IP without a Floating IP.
        """
        # Create Network
        net_config = openstack_tests.get_priv_net_config(
            project_name=self.os_creds.project_name,
            net_name=self.guid + '-pub-net',
            subnet_name=self.guid + '-pub-subnet',
            router_name=self.guid + '-pub-router',
            external_net=self.ext_net_name,
            netconf_override=self.netconf_override)
        self.network_creator = OpenStackNetwork(
            self.admin_os_creds, net_config.network_settings)
        self.network_creator.create()

        self.port_settings = PortConfig(
            name=self.guid + '-port',
            network_name=net_config.network_settings.name)

        instance_settings = VmInstanceConfig(
            name=self.vm_inst_name,
            flavor=self.flavor_creator.flavor_settings.name,
            port_settings=[self.port_settings])

        self.inst_creator = OpenStackVmInstance(
            self.admin_os_creds, instance_settings,
            self.image_creator.image_settings)

        admin_nova = nova_utils.nova_client(self.admin_os_creds)
        admin_neutron = neutron_utils.neutron_client(self.admin_os_creds)
        admin_key = keystone_utils.keystone_client(self.admin_os_creds)
        vm_inst = self.inst_creator.create(block=True)

        self.assertIsNotNone(vm_inst)
        vm_inst_get = nova_utils.get_server(
            admin_nova, admin_neutron, admin_key,
            vm_inst_settings=instance_settings)
        self.assertEqual(vm_inst, vm_inst_get)

        self.assertIsNone(nova_utils.get_server(
            self.nova, self.neutron, self.keystone,
            vm_inst_settings=instance_settings))

        self.assertIsNotNone(self.inst_creator.get_vm_inst().availability_zone)
        self.assertIsNotNone(self.inst_creator.get_vm_inst().compute_host)


class CreateInstanceExternalNetTests(OSIntegrationTestCase):
    """
    Simple instance creation tests where the network is external
    """

    def setUp(self):
        """
        Instantiates the CreateImage object that is responsible for downloading
        and creating an OS image file
        within OpenStack
        """
        super(self.__class__, self).__start__()

        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.vm_inst_name = guid + '-inst'
        self.nova = nova_utils.nova_client(self.admin_os_creds)
        self.neutron = neutron_utils.neutron_client(self.admin_os_creds)
        os_image_settings = openstack_tests.cirros_image_settings(
            name=guid + '-image', image_metadata=self.image_metadata)

        # Initialize for tearDown()
        self.image_creator = None
        self.flavor_creator = None
        self.inst_creator = None

        try:
            # Create Image
            self.image_creator = OpenStackImage(self.os_creds,
                                                os_image_settings)
            self.image_creator.create()

            # Create Flavor
            self.flavor_creator = OpenStackFlavor(
                self.admin_os_creds,
                FlavorConfig(name=guid + '-flavor-name', ram=256, disk=10,
                             vcpus=2, metadata=self.flavor_metadata))
            self.flavor_creator.create()

            self.port_settings = PortConfig(
                name=guid + '-port',
                network_name=self.ext_net_name)

        except Exception as e:
            self.tearDown()
            raise e

    def tearDown(self):
        """
        Cleans the created object
        """
        if self.inst_creator:
            try:
                self.inst_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning VM instance with message '
                    '- %s', e)

        if self.flavor_creator:
            try:
                self.flavor_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning flavor with message - %s',
                    e)

        if self.image_creator and not self.image_creator.image_settings.exists:
            try:
                self.image_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning image with message - %s', e)

        super(self.__class__, self).__clean__()

    def test_create_instance_public_net(self):
        """
        Tests the creation of an OpenStack instance with a single port to
        the external network.
        """
        instance_settings = VmInstanceConfig(
            name=self.vm_inst_name,
            flavor=self.flavor_creator.flavor_settings.name,
            port_settings=[self.port_settings])

        self.inst_creator = OpenStackVmInstance(
            self.admin_os_creds, instance_settings,
            self.image_creator.image_settings)

        vm_inst = self.inst_creator.create(block=True)
        vm_inst_get = nova_utils.get_server(
            self.nova, self.neutron, self.keystone,
            vm_inst_settings=instance_settings)
        self.assertEqual(vm_inst, vm_inst_get)
        ip = self.inst_creator.get_port_ip(self.port_settings.name)

        check_dhcp_lease(self.inst_creator, ip)


class CreateInstanceSingleNetworkTests(OSIntegrationTestCase):
    """
    Test for the CreateInstance class with a single NIC/Port with Floating IPs
    """

    def setUp(self):
        """
        Instantiates the CreateImage object that is responsible for downloading
        and creating an OS image file within OpenStack
        """
        super(self.__class__, self).__start__()

        self.nova = nova_utils.nova_client(self.os_creds, self.os_session)
        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.keypair_priv_filepath = 'tmp/' + guid
        self.keypair_pub_filepath = self.keypair_priv_filepath + '.pub'
        self.keypair_name = guid + '-kp'
        self.vm_inst_name = guid + '-inst'
        self.port_1_name = guid + 'port-1'
        self.port_2_name = guid + 'port-2'
        self.floating_ip_name = guid + 'fip1'

        # Initialize for tearDown()
        self.image_creator = None
        self.network_creator = None
        self.router_creator = None
        self.flavor_creator = None
        self.keypair_creator = None
        self.sec_grp_creator = None
        self.inst_creators = list()

        self.pub_net_config = openstack_tests.get_pub_net_config(
            project_name=self.os_creds.project_name,
            net_name=guid + '-pub-net', subnet_name=guid + '-pub-subnet',
            router_name=guid + '-pub-router', external_net=self.ext_net_name,
            netconf_override=self.netconf_override)
        os_image_settings = openstack_tests.cirros_image_settings(
            name=guid + '-image', image_metadata=self.image_metadata)
        try:
            # Create Image
            self.image_creator = OpenStackImage(self.os_creds,
                                                os_image_settings)
            self.image_creator.create()

            # Create Network
            self.network_creator = OpenStackNetwork(
                self.os_creds, self.pub_net_config.network_settings)
            self.network_creator.create()

            # Create Router
            self.router_creator = OpenStackRouter(
                self.os_creds, self.pub_net_config.router_settings)
            self.router_creator.create()

            # Create Flavor
            self.flavor_creator = OpenStackFlavor(
                self.admin_os_creds,
                FlavorConfig(name=guid + '-flavor-name', ram=256, disk=10,
                             vcpus=2, metadata=self.flavor_metadata))
            self.flavor_creator.create()

            self.keypair_creator = OpenStackKeypair(
                self.os_creds, KeypairConfig(
                    name=self.keypair_name,
                    public_filepath=self.keypair_pub_filepath,
                    private_filepath=self.keypair_priv_filepath))
            self.keypair_creator.create()

            sec_grp_name = guid + '-sec-grp'
            rule1 = SecurityGroupRuleConfig(
                sec_grp_name=sec_grp_name, direction=Direction.ingress,
                protocol=Protocol.icmp)
            rule2 = SecurityGroupRuleConfig(
                sec_grp_name=sec_grp_name, direction=Direction.ingress,
                protocol=Protocol.tcp, port_range_min=22, port_range_max=22)
            self.sec_grp_creator = OpenStackSecurityGroup(
                self.os_creds,
                SecurityGroupConfig(
                    name=sec_grp_name, rule_settings=[rule1, rule2]))
            self.sec_grp_creator.create()
        except Exception as e:
            self.tearDown()
            raise e

    def tearDown(self):
        """
        Cleans the created object
        """
        for inst_creator in self.inst_creators:
            try:
                inst_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning VM instance with message '
                    '- %s', e)

        if self.keypair_creator:
            try:
                self.keypair_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning keypair with message - %s',
                    e)

        if self.flavor_creator:
            try:
                self.flavor_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning flavor with message - %s',
                    e)

        if self.sec_grp_creator:
            try:
                self.sec_grp_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning security group with message'
                    ' - %s', e)

        if self.router_creator:
            try:
                self.router_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning router with message - %s',
                    e)

        if self.network_creator:
            try:
                self.network_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning network with message - %s',
                    e)

        if self.image_creator and not self.image_creator.image_settings.exists:
            try:
                self.image_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning image with message - %s', e)

        super(self.__class__, self).__clean__()

    def test_single_port_static(self):
        """
        Tests the creation of an OpenStack instance with a single port with a
        static IP without a Floating IP.
        """
        ip_1 = '10.55.1.100'
        sub_settings = self.pub_net_config.network_settings.subnet_settings
        port_settings = PortConfig(
            name=self.port_1_name,
            network_name=self.pub_net_config.network_settings.name,
            ip_addrs=[
                {'subnet_name': sub_settings[0].name, 'ip': ip_1}])

        instance_settings = VmInstanceConfig(
            name=self.vm_inst_name,
            flavor=self.flavor_creator.flavor_settings.name,
            port_settings=[port_settings],
            floating_ip_settings=[FloatingIpConfig(
                name=self.floating_ip_name, port_name=self.port_1_name,
                router_name=self.pub_net_config.router_settings.name)])

        inst_creator = OpenStackVmInstance(
            self.os_creds, instance_settings,
            self.image_creator.image_settings,
            keypair_settings=self.keypair_creator.keypair_settings)
        self.inst_creators.append(inst_creator)
        vm_inst = inst_creator.create(block=True)

        self.assertEqual(ip_1, inst_creator.get_port_ip(self.port_1_name))
        self.assertTrue(inst_creator.vm_active(block=True))
        self.assertEqual(vm_inst.id, inst_creator.get_vm_inst().id)

    def test_ssh_client_fip_before_active(self):
        """
        Tests the ability to access a VM via SSH and a floating IP when it has
        been assigned prior to being active.
        """
        port_settings = PortConfig(
            name=self.port_1_name,
            network_name=self.pub_net_config.network_settings.name)

        instance_settings = VmInstanceConfig(
            name=self.vm_inst_name,
            flavor=self.flavor_creator.flavor_settings.name,
            port_settings=[port_settings],
            security_group_names=[self.sec_grp_creator.sec_grp_settings.name],
            floating_ip_settings=[FloatingIpConfig(
                name=self.floating_ip_name, port_name=self.port_1_name,
                router_name=self.pub_net_config.router_settings.name)])

        inst_creator = OpenStackVmInstance(
            self.os_creds, instance_settings,
            self.image_creator.image_settings,
            keypair_settings=self.keypair_creator.keypair_settings)
        self.inst_creators.append(inst_creator)
        vm_inst = inst_creator.create()
        self.assertIsNotNone(vm_inst)

        self.assertTrue(inst_creator.vm_active(block=True))

        ip = inst_creator.get_port_ip(port_settings.name)
        self.assertTrue(check_dhcp_lease(inst_creator, ip))

        self.assertEqual(vm_inst.id, inst_creator.get_vm_inst().id)

        self.assertTrue(validate_ssh_client(inst_creator))

    def test_ssh_client_fip_after_active(self):
        """
        Tests the ability to access a VM via SSH and a floating IP when it has
        been assigned prior to being active.
        """
        port_settings = PortConfig(
            name=self.port_1_name,
            network_name=self.pub_net_config.network_settings.name)

        instance_settings = VmInstanceConfig(
            name=self.vm_inst_name,
            flavor=self.flavor_creator.flavor_settings.name,
            port_settings=[port_settings],
            security_group_names=[self.sec_grp_creator.sec_grp_settings.name],
            floating_ip_settings=[FloatingIpConfig(
                name=self.floating_ip_name, port_name=self.port_1_name,
                router_name=self.pub_net_config.router_settings.name)])

        inst_creator = OpenStackVmInstance(
            self.os_creds, instance_settings,
            self.image_creator.image_settings,
            keypair_settings=self.keypair_creator.keypair_settings)
        self.inst_creators.append(inst_creator)

        # block=True will force the create() method to block until the
        vm_inst = inst_creator.create(block=True)
        self.assertIsNotNone(vm_inst)

        self.assertTrue(inst_creator.vm_active(block=True))

        ip = inst_creator.get_port_ip(port_settings.name)
        self.assertTrue(check_dhcp_lease(inst_creator, ip))

        self.assertEqual(vm_inst.id, inst_creator.get_vm_inst().id)

        self.assertTrue(validate_ssh_client(inst_creator))

    def test_ssh_client_fip_after_reboot(self):
        """
        Tests the ability to access a VM via SSH and a floating IP after it has
        been rebooted.
        """
        port_settings = PortConfig(
            name=self.port_1_name,
            network_name=self.pub_net_config.network_settings.name)

        instance_settings = VmInstanceConfig(
            name=self.vm_inst_name,
            flavor=self.flavor_creator.flavor_settings.name,
            port_settings=[port_settings],
            security_group_names=[self.sec_grp_creator.sec_grp_settings.name],
            floating_ip_settings=[FloatingIpConfig(
                name=self.floating_ip_name, port_name=self.port_1_name,
                router_name=self.pub_net_config.router_settings.name)])

        inst_creator = OpenStackVmInstance(
            self.os_creds, instance_settings,
            self.image_creator.image_settings,
            keypair_settings=self.keypair_creator.keypair_settings)
        self.inst_creators.append(inst_creator)

        # block=True will force the create() method to block until the
        vm_inst = inst_creator.create(block=True)
        self.assertIsNotNone(vm_inst)

        self.assertTrue(inst_creator.vm_active(block=True))

        ip = inst_creator.get_port_ip(port_settings.name)
        self.assertTrue(check_dhcp_lease(inst_creator, ip))

        self.assertEqual(vm_inst.id, inst_creator.get_vm_inst().id)

        self.assertTrue(validate_ssh_client(inst_creator))

        # Test default reboot which should be 'SOFT'
        inst_creator.reboot()
        # Lag time to allow for shutdown routine to take effect
        time.sleep(15)
        self.assertTrue(check_dhcp_lease(inst_creator, ip))
        self.assertTrue(validate_ssh_client(inst_creator))

        # Test 'SOFT' reboot
        inst_creator.reboot(reboot_type=RebootType.soft)
        time.sleep(15)
        self.assertTrue(check_dhcp_lease(inst_creator, ip))
        self.assertTrue(validate_ssh_client(inst_creator))

        # Test 'HARD' reboot
        inst_creator.reboot(reboot_type=RebootType.hard)
        time.sleep(15)
        self.assertTrue(check_dhcp_lease(inst_creator, ip))
        self.assertTrue(validate_ssh_client(inst_creator))

    def test_ssh_client_fip_after_init(self):
        """
        Tests the ability to assign a floating IP to an already initialized
        OpenStackVmInstance object. After the floating IP has been allocated
        and assigned, this test will ensure that it can be accessed via SSH.
        """
        port_settings = PortConfig(
            name=self.port_1_name,
            network_name=self.pub_net_config.network_settings.name)

        instance_settings = VmInstanceConfig(
            name=self.vm_inst_name,
            flavor=self.flavor_creator.flavor_settings.name,
            port_settings=[port_settings],
            security_group_names=[self.sec_grp_creator.sec_grp_settings.name])

        inst_creator = OpenStackVmInstance(
            self.os_creds, instance_settings,
            self.image_creator.image_settings,
            keypair_settings=self.keypair_creator.keypair_settings)
        self.inst_creators.append(inst_creator)

        # block=True will force the create() method to block until the
        vm_inst = inst_creator.create(block=True)
        self.assertIsNotNone(vm_inst)

        self.assertTrue(inst_creator.vm_active(block=True))
        ip = inst_creator.get_port_ip(port_settings.name)
        self.assertTrue(check_dhcp_lease(inst_creator, ip))
        self.assertEqual(vm_inst.id, inst_creator.get_vm_inst().id)

        inst_creator.add_floating_ip(FloatingIpConfig(
            name=self.floating_ip_name, port_name=self.port_1_name,
            router_name=self.pub_net_config.router_settings.name))

        self.assertTrue(validate_ssh_client(inst_creator))

    def test_ssh_client_fip_reverse_engineer(self):
        """
        Tests the ability to assign a floating IP to a reverse engineered
        OpenStackVmInstance object. After the floating IP has been allocated
        and assigned, this test will ensure that it can be accessed via SSH.
        """
        port_settings = PortConfig(
            name=self.port_1_name,
            network_name=self.pub_net_config.network_settings.name)

        instance_settings = VmInstanceConfig(
            name=self.vm_inst_name,
            flavor=self.flavor_creator.flavor_settings.name,
            port_settings=[port_settings],
            security_group_names=[self.sec_grp_creator.sec_grp_settings.name])

        inst_creator = OpenStackVmInstance(
            self.os_creds, instance_settings,
            self.image_creator.image_settings,
            keypair_settings=self.keypair_creator.keypair_settings)
        self.inst_creators.append(inst_creator)

        # block=True will force the create() method to block until the
        vm_inst = inst_creator.create(block=True)
        self.assertIsNotNone(vm_inst)

        self.assertTrue(inst_creator.vm_active(block=True))

        derived_inst_creator = create_instance.generate_creator(
            self.os_creds, vm_inst, self.image_creator.image_settings,
            self.os_creds.project_name, self.keypair_creator.keypair_settings)

        derived_inst_creator.add_floating_ip(FloatingIpConfig(
            name=self.floating_ip_name, port_name=self.port_1_name,
            router_name=self.pub_net_config.router_settings.name))
        self.inst_creators.append(derived_inst_creator)

        self.assertTrue(validate_ssh_client(
            derived_inst_creator, fip_name=self.floating_ip_name))

    def test_ssh_client_fip_second_creator(self):
        """
        Tests the ability to access a VM via SSH and a floating IP via a
        creator that is identical to the original creator.
        """
        port_settings = PortConfig(
            name=self.port_1_name,
            network_name=self.pub_net_config.network_settings.name)

        instance_settings = VmInstanceConfig(
            name=self.vm_inst_name,
            flavor=self.flavor_creator.flavor_settings.name,
            port_settings=[port_settings],
            security_group_names=[self.sec_grp_creator.sec_grp_settings.name],
            floating_ip_settings=[FloatingIpConfig(
                name=self.floating_ip_name, port_name=self.port_1_name,
                router_name=self.pub_net_config.router_settings.name)])

        inst_creator = OpenStackVmInstance(
            self.os_creds, instance_settings,
            self.image_creator.image_settings,
            keypair_settings=self.keypair_creator.keypair_settings)
        self.inst_creators.append(inst_creator)

        # block=True will force the create() method to block until the
        vm_inst = inst_creator.create(block=True)
        self.assertIsNotNone(vm_inst)

        self.assertTrue(inst_creator.vm_active(block=True))

        ip = inst_creator.get_port_ip(port_settings.name)
        self.assertTrue(check_dhcp_lease(inst_creator, ip))

        self.assertEqual(vm_inst.id, inst_creator.get_vm_inst().id)

        self.assertTrue(validate_ssh_client(inst_creator))

        inst_creator2 = OpenStackVmInstance(
            self.os_creds, instance_settings,
            self.image_creator.image_settings,
            keypair_settings=self.keypair_creator.keypair_settings)
        inst_creator2.create()
        self.assertTrue(validate_ssh_client(inst_creator2))


class CreateInstanceIPv6NetworkTests(OSIntegrationTestCase):
    """
    Test for the CreateInstance class with a single NIC/Port with Floating IPs
    """

    def setUp(self):
        """
        Instantiates the CreateImage object that is responsible for downloading
        and creating an OS image file within OpenStack
        """
        super(self.__class__, self).__start__()

        self.nova = nova_utils.nova_client(self.os_creds, self.os_session)
        self.guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.keypair_priv_filepath = 'tmp/' + self.guid
        self.keypair_pub_filepath = self.keypair_priv_filepath + '.pub'
        self.keypair_name = self.guid + '-kp'
        self.vm_inst_name = self.guid + '-inst'
        self.port1_name = self.guid + 'port1'
        self.port2_name = self.guid + 'port2'

        # Initialize for tearDown()
        self.image_creator = None
        self.network_creator = None
        self.router_creator = None
        self.flavor_creator = None
        self.keypair_creator = None
        self.sec_grp_creator = None
        self.inst_creator = None

        os_image_settings = openstack_tests.cirros_image_settings(
            name=self.guid + '-image', image_metadata=self.image_metadata)
        try:
            self.image_creator = OpenStackImage(
                self.os_creds, os_image_settings)
            self.image_creator.create()

            self.flavor_creator = OpenStackFlavor(
                self.admin_os_creds,
                FlavorConfig(
                    name=self.guid + '-flavor-name', ram=256, disk=10, vcpus=2,
                    metadata=self.flavor_metadata))
            self.flavor_creator.create()

            self.keypair_creator = OpenStackKeypair(
                self.os_creds, KeypairConfig(
                    name=self.keypair_name,
                    public_filepath=self.keypair_pub_filepath,
                    private_filepath=self.keypair_priv_filepath))
            self.keypair_creator.create()

            sec_grp_name = self.guid + '-sec-grp'
            rule1 = SecurityGroupRuleConfig(
                sec_grp_name=sec_grp_name, direction=Direction.ingress,
                protocol=Protocol.icmp)
            rule2 = SecurityGroupRuleConfig(
                sec_grp_name=sec_grp_name, direction=Direction.ingress,
                protocol=Protocol.tcp, port_range_min=22, port_range_max=22)
            self.sec_grp_creator = OpenStackSecurityGroup(
                self.os_creds,
                SecurityGroupConfig(
                    name=sec_grp_name, rule_settings=[rule1, rule2]))
            self.sec_grp_creator.create()
        except Exception as e:
            self.tearDown()
            raise e

    def tearDown(self):
        """
        Cleans the created object
        """
        if self.inst_creator:
            try:
                self.inst_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning VM instance with message '
                    '- %s', e)

        if self.keypair_creator:
            try:
                self.keypair_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning keypair with message - %s',
                    e)

        if self.flavor_creator:
            try:
                self.flavor_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning flavor with message - %s',
                    e)

        if self.sec_grp_creator:
            try:
                self.sec_grp_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning security group with message'
                    ' - %s', e)

        if self.router_creator:
            try:
                self.router_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning router with message - %s',
                    e)

        if self.network_creator:
            try:
                self.network_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning network with message - %s',
                    e)

        if self.image_creator and not self.image_creator.image_settings.exists:
            try:
                self.image_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning image with message - %s', e)

        super(self.__class__, self).__clean__()

    def test_v4fip_v6overlay(self):
        """
        Tests the ability to assign an IPv4 floating IP to an IPv6 overlay
        network when the external network does not have an IPv6 subnet.
        """
        subnet_settings = SubnetConfig(
            name=self.guid + '-subnet', cidr='1:1:0:0:0:0:0:0/64',
            ip_version=6)
        network_settings = NetworkConfig(
            name=self.guid + '-net', subnet_settings=[subnet_settings])
        router_settings = RouterConfig(
            name=self.guid + '-router', external_gateway=self.ext_net_name,
            internal_subnets=[{'subnet': {
                'project_name': self.os_creds.project_name,
                'network_name': network_settings.name,
                'subnet_name': subnet_settings.name}}])

        # Create Network
        self.network_creator = OpenStackNetwork(
            self.os_creds, network_settings)
        self.network_creator.create()

        # Create Router
        self.router_creator = OpenStackRouter(
            self.os_creds, router_settings)
        self.router_creator.create()

        port_settings = PortConfig(
            name=self.port1_name, network_name=network_settings.name)

        instance_settings = VmInstanceConfig(
            name=self.vm_inst_name,
            flavor=self.flavor_creator.flavor_settings.name,
            port_settings=[port_settings],
            security_group_names=[self.sec_grp_creator.sec_grp_settings.name],
            floating_ip_settings=[FloatingIpConfig(
                name='fip1', port_name=self.port1_name,
                router_name=router_settings.name)])

        self.inst_creator = OpenStackVmInstance(
            self.os_creds, instance_settings,
            self.image_creator.image_settings,
            keypair_settings=self.keypair_creator.keypair_settings)

        with self.assertRaises(BadRequest):
            self.inst_creator.create(block=True)

    def test_fip_v4and6_overlay(self):
        """
        Tests the ability to assign an IPv4 floating IP to an IPv6 overlay
        network when the external network does not have an IPv6 subnet.
        """
        subnet4_settings = SubnetConfig(
            name=self.guid + '-subnet4', cidr='10.0.1.0/24',
            ip_version=4)
        subnet6_settings = SubnetConfig(
            name=self.guid + '-subnet6', cidr='1:1:0:0:0:0:0:0/64',
            ip_version=6)
        network_settings = NetworkConfig(
            name=self.guid + '-net',
            subnet_settings=[subnet4_settings, subnet6_settings])
        router_settings = RouterConfig(
            name=self.guid + '-router', external_gateway=self.ext_net_name,
            internal_subnets=[{'subnet': {
                'project_name': self.os_creds.project_name,
                'network_name': network_settings.name,
                'subnet_name': subnet4_settings.name}}])

        # Create Network
        self.network_creator = OpenStackNetwork(
            self.os_creds, network_settings)
        self.network_creator.create()

        # Create Router
        self.router_creator = OpenStackRouter(
            self.os_creds, router_settings)
        self.router_creator.create()

        port_settings = PortConfig(
            name=self.port1_name, network_name=network_settings.name)

        instance_settings = VmInstanceConfig(
            name=self.vm_inst_name,
            flavor=self.flavor_creator.flavor_settings.name,
            port_settings=[port_settings],
            security_group_names=[self.sec_grp_creator.sec_grp_settings.name],
            floating_ip_settings=[FloatingIpConfig(
                name='fip1', port_name=self.port1_name,
                router_name=router_settings.name)])

        self.inst_creator = OpenStackVmInstance(
            self.os_creds, instance_settings,
            self.image_creator.image_settings,
            keypair_settings=self.keypair_creator.keypair_settings)

        self.inst_creator.create(block=True)
        ssh_client = self.inst_creator.ssh_client()
        self.assertIsNotNone(ssh_client)


class CreateInstancePortManipulationTests(OSIntegrationTestCase):
    """
    Test for the CreateInstance class with a single NIC/Port where mac and IP
    values are manually set
    """

    def setUp(self):
        """
        Instantiates the CreateImage object that is responsible for downloading
        and creating an OS image file within OpenStack
        """
        super(self.__class__, self).__start__()

        self.guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.vm_inst_name = self.guid + '-inst'
        self.port_1_name = self.guid + 'port-1'
        self.port_2_name = self.guid + 'port-2'
        self.floating_ip_name = self.guid + 'fip1'

        # Initialize for tearDown()
        self.image_creator = None
        self.network_creator = None
        self.network_creator2 = None
        self.flavor_creator = None
        self.inst_creator = None

        self.net_config = openstack_tests.get_priv_net_config(
            project_name=self.os_creds.project_name,
            net_name=self.guid + '-pub-net',
            subnet_name=self.guid + '-pub-subnet',
            router_name=self.guid + '-pub-router',
            external_net=self.ext_net_name,
            netconf_override=self.netconf_override)
        os_image_settings = openstack_tests.cirros_image_settings(
            name=self.guid + '-image', image_metadata=self.image_metadata)

        try:
            # Create Image
            self.image_creator = OpenStackImage(self.os_creds,
                                                os_image_settings)
            self.image_creator.create()

            # Create Network
            self.network_creator = OpenStackNetwork(
                self.os_creds, self.net_config.network_settings)
            self.network_creator.create()

            # Create Flavor
            self.flavor_creator = OpenStackFlavor(
                self.admin_os_creds,
                FlavorConfig(name=self.guid + '-flavor-name', ram=256, disk=10,
                             vcpus=2, metadata=self.flavor_metadata))
            self.flavor_creator.create()
        except Exception as e:
            self.tearDown()
            raise e

    def tearDown(self):
        """
        Cleans the created object
        """
        if self.inst_creator:
            try:
                self.inst_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning VM instance with message '
                    '- %s', e)

        if self.flavor_creator:
            try:
                self.flavor_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning flavor with message - %s',
                    e)

        if self.network_creator:
            try:
                self.network_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning network with message - %s',
                    e)

        if self.image_creator and not self.image_creator.image_settings.exists:
            try:
                self.image_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning image with message - %s', e)

        super(self.__class__, self).__clean__()

    def test_set_custom_valid_ip_one_subnet(self):
        """
        Tests the creation of an OpenStack instance with a single port with a
        static IP on a network with one subnet.
        """
        ip = '10.55.0.101'
        sub_settings = self.net_config.network_settings.subnet_settings
        port_settings = PortConfig(
            name=self.port_1_name,
            network_name=self.net_config.network_settings.name,
            ip_addrs=[{'subnet_name': sub_settings[0].name, 'ip': ip}])

        instance_settings = VmInstanceConfig(
            name=self.vm_inst_name,
            flavor=self.flavor_creator.flavor_settings.name,
            port_settings=[port_settings])

        self.inst_creator = OpenStackVmInstance(
            self.os_creds, instance_settings,
            self.image_creator.image_settings)
        self.inst_creator.create(block=True)

        self.assertEqual(ip, self.inst_creator.get_port_ip(
            self.port_1_name,
            subnet_name=self.net_config.network_settings.subnet_settings[
                0].name))

    def test_set_one_port_two_ip_one_subnet(self):
        """
        Tests the creation of an OpenStack instance with a single port with a
        two static IPs on a network with one subnet.
        """
        ip1 = '10.55.0.101'
        ip2 = '10.55.0.102'
        sub_settings = self.net_config.network_settings.subnet_settings
        port_settings = PortConfig(
            name=self.port_1_name,
            network_name=self.net_config.network_settings.name,
            ip_addrs=[{'subnet_name': sub_settings[0].name, 'ip': ip1},
                      {'subnet_name': sub_settings[0].name, 'ip': ip2}])

        instance_settings = VmInstanceConfig(
            name=self.vm_inst_name,
            flavor=self.flavor_creator.flavor_settings.name,
            port_settings=[port_settings])

        self.inst_creator = OpenStackVmInstance(
            self.os_creds, instance_settings,
            self.image_creator.image_settings)
        vm_inst = self.inst_creator.create(block=True)

        self.assertEqual(ip1, vm_inst.ports[0].ips[0]['ip_address'])
        self.assertEqual(self.network_creator.get_network().subnets[0].id,
                         vm_inst.ports[0].ips[0]['subnet_id'])
        self.assertEqual(ip2, vm_inst.ports[0].ips[1]['ip_address'])
        self.assertEqual(self.network_creator.get_network().subnets[0].id,
                         vm_inst.ports[0].ips[1]['subnet_id'])

    def test_set_one_port_two_ip_two_subnets(self):
        """
        Tests the creation of an OpenStack instance with a single port with a
        two static IPs on a network with one subnet.
        """
        net2_config = NetworkConfig(
            name=self.guid + 'net2', subnets=[
                SubnetConfig(name=self.guid + '-subnet1', cidr='10.55.0.0/24'),
                SubnetConfig(name=self.guid + '-subnet2', cidr='10.65.0.0/24'),
            ])

        # Create Network
        self.network_creator2 = OpenStackNetwork(self.os_creds, net2_config)
        net2 = self.network_creator2.create()

        ip1 = '10.55.0.101'
        ip2 = '10.65.0.101'

        port_settings = PortConfig(
            name=self.port_1_name,
            network_name=net2_config.name,
            ip_addrs=[
                {'subnet_name': net2_config.subnet_settings[0].name,
                 'ip': ip1},
                {'subnet_name': net2_config.subnet_settings[1].name,
                 'ip': ip2}])

        instance_settings = VmInstanceConfig(
            name=self.vm_inst_name,
            flavor=self.flavor_creator.flavor_settings.name,
            port_settings=[port_settings])

        self.inst_creator = OpenStackVmInstance(
            self.os_creds, instance_settings,
            self.image_creator.image_settings)
        vm_inst = self.inst_creator.create(block=True)

        subnet1_id = None
        subnet2_id = None
        for subnet in net2.subnets:
            if subnet.name == net2_config.subnet_settings[0].name:
                subnet1_id = subnet.id
            if subnet.name == net2_config.subnet_settings[1].name:
                subnet2_id = subnet.id
        self.assertEqual(ip1, vm_inst.ports[0].ips[0]['ip_address'])
        self.assertEqual(subnet1_id, vm_inst.ports[0].ips[0]['subnet_id'])
        self.assertEqual(ip2, vm_inst.ports[0].ips[1]['ip_address'])
        self.assertEqual(subnet2_id, vm_inst.ports[0].ips[1]['subnet_id'])

    def test_set_custom_invalid_ip_one_subnet(self):
        """
        Tests the creation of an OpenStack instance with a single port with a
        static IP on a network with one subnet.
        """
        ip = '10.66.0.101'
        sub_settings = self.net_config.network_settings.subnet_settings
        port_settings = PortConfig(
            name=self.port_1_name,
            network_name=self.net_config.network_settings.name,
            ip_addrs=[{'subnet_name': sub_settings[0].name, 'ip': ip}])

        instance_settings = VmInstanceConfig(
            name=self.vm_inst_name,
            flavor=self.flavor_creator.flavor_settings.name,
            port_settings=[port_settings])

        self.inst_creator = OpenStackVmInstance(
            self.os_creds, instance_settings,
            self.image_creator.image_settings)

        with self.assertRaises(InvalidIpForSubnetClient):
            self.inst_creator.create()

    def test_set_custom_valid_mac(self):
        """
        Tests the creation of an OpenStack instance with a single port where
        the MAC address is assigned.
        """
        mac_addr = '0a:1b:2c:3d:4e:5f'
        port_settings = PortConfig(
            name=self.port_1_name,
            network_name=self.net_config.network_settings.name,
            mac_address=mac_addr)

        instance_settings = VmInstanceConfig(
            name=self.vm_inst_name,
            flavor=self.flavor_creator.flavor_settings.name,
            port_settings=[port_settings])

        self.inst_creator = OpenStackVmInstance(
            self.os_creds, instance_settings,
            self.image_creator.image_settings)
        self.inst_creator.create(block=True)

        self.assertEqual(mac_addr,
                         self.inst_creator.get_port_mac(self.port_1_name))

    def test_set_custom_invalid_mac(self):
        """
        Tests the creation of an OpenStack instance with a single port where an
        invalid MAC address value is being
        assigned. This should raise an Exception
        """
        port_settings = PortConfig(
            name=self.port_1_name,
            network_name=self.net_config.network_settings.name,
            mac_address='foo')

        instance_settings = VmInstanceConfig(
            name=self.vm_inst_name,
            flavor=self.flavor_creator.flavor_settings.name,
            port_settings=[port_settings])

        self.inst_creator = OpenStackVmInstance(
            self.os_creds, instance_settings,
            self.image_creator.image_settings)

        with self.assertRaises(Exception):
            self.inst_creator.create()

    def test_set_custom_mac_and_ip(self):
        """
        Tests the creation of an OpenStack instance with a single port where
        the IP and MAC address is assigned.
        """
        ip = '10.55.0.101'
        mac_addr = '0a:1b:2c:3d:4e:5f'
        sub_settings = self.net_config.network_settings.subnet_settings
        port_settings = PortConfig(
            name=self.port_1_name,
            network_name=self.net_config.network_settings.name,
            mac_address=mac_addr,
            ip_addrs=[{'subnet_name': sub_settings[0].name, 'ip': ip}])

        instance_settings = VmInstanceConfig(
            name=self.vm_inst_name,
            flavor=self.flavor_creator.flavor_settings.name,
            port_settings=[port_settings])

        self.inst_creator = OpenStackVmInstance(
            self.os_creds, instance_settings,
            self.image_creator.image_settings)
        self.inst_creator.create(block=True)

        self.assertEqual(ip, self.inst_creator.get_port_ip(
            self.port_1_name,
            subnet_name=self.net_config.network_settings.subnet_settings[
                0].name))
        self.assertEqual(mac_addr,
                         self.inst_creator.get_port_mac(self.port_1_name))

    def test_set_allowed_address_pairs(self):
        """
        Tests the creation of an OpenStack instance with a single port where
        max_allowed_address_pair is set.
        """
        ip = '10.55.0.101'
        mac_addr = '0a:1b:2c:3d:4e:5f'
        pair = {'ip_address': ip, 'mac_address': mac_addr}
        port_settings = PortConfig(
            name=self.port_1_name,
            network_name=self.net_config.network_settings.name,
            allowed_address_pairs=[pair])

        instance_settings = VmInstanceConfig(
            name=self.vm_inst_name,
            flavor=self.flavor_creator.flavor_settings.name,
            port_settings=[port_settings])

        self.inst_creator = OpenStackVmInstance(
            self.os_creds, instance_settings,
            self.image_creator.image_settings)
        self.inst_creator.create(block=True)

        port = self.inst_creator.get_port_by_name(port_settings.name)
        self.assertIsNotNone(port)
        self.assertIsNotNone(port.allowed_address_pairs)
        self.assertEqual(1, len(port.allowed_address_pairs))
        validation_utils.objects_equivalent(pair,
                                            port.allowed_address_pairs[0])

    def test_set_allowed_address_pairs_bad_mac(self):
        """
        Tests the creation of an OpenStack instance with a single port where
        max_allowed_address_pair is set with an invalid MAC address.
        """
        ip = '10.55.0.101'
        mac_addr = 'foo'
        pair = {'ip_address': ip, 'mac_address': mac_addr}
        pairs = set()
        pairs.add((ip, mac_addr))
        port_settings = PortConfig(
            name=self.port_1_name,
            network_name=self.net_config.network_settings.name,
            allowed_address_pairs=[pair])

        instance_settings = VmInstanceConfig(
            name=self.vm_inst_name,
            flavor=self.flavor_creator.flavor_settings.name,
            port_settings=[port_settings])

        self.inst_creator = OpenStackVmInstance(
            self.os_creds, instance_settings,
            self.image_creator.image_settings)
        with self.assertRaises(Exception):
            self.inst_creator.create()

    def test_set_allowed_address_pairs_bad_ip(self):
        """
        Tests the creation of an OpenStack instance with a single port where
        max_allowed_address_pair is set with an invalid MAC address.
        """
        ip = 'foo'
        mac_addr = '0a:1b:2c:3d:4e:5f'
        pair = {'ip_address': ip, 'mac_address': mac_addr}
        pairs = set()
        pairs.add((ip, mac_addr))
        port_settings = PortConfig(
            name=self.port_1_name,
            network_name=self.net_config.network_settings.name,
            allowed_address_pairs=[pair])

        instance_settings = VmInstanceConfig(
            name=self.vm_inst_name,
            flavor=self.flavor_creator.flavor_settings.name,
            port_settings=[port_settings])

        self.inst_creator = OpenStackVmInstance(
            self.os_creds, instance_settings,
            self.image_creator.image_settings)
        with self.assertRaises(Exception):
            self.inst_creator.create()


class CreateInstanceOnComputeHost(OSIntegrationTestCase):
    """
    Test for the CreateInstance where one VM is deployed to each compute node
    """

    def setUp(self):
        """
        Instantiates the CreateImage object that is responsible for downloading
        and creating an OS image file within OpenStack
        """
        super(self.__class__, self).__start__()

        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.vm_inst_name = guid + '-inst'
        self.port_base_name = guid + 'port'

        # Initialize for tearDown()
        self.image_creator = None
        self.flavor_creator = None
        self.network_creator = None
        self.inst_creators = list()

        self.priv_net_config = openstack_tests.get_priv_net_config(
            project_name=self.os_creds.project_name,
            net_name=guid + '-priv-net', subnet_name=guid + '-priv-subnet',
            netconf_override=self.netconf_override)

        os_image_settings = openstack_tests.cirros_image_settings(
            name=guid + '-image', image_metadata=self.image_metadata)

        try:
            # Create Network
            self.network_creator = OpenStackNetwork(
                self.admin_os_creds, self.priv_net_config.network_settings)
            self.network_creator.create()

            # Create Flavor
            self.flavor_creator = OpenStackFlavor(
                self.admin_os_creds,
                FlavorConfig(name=guid + '-flavor-name', ram=512, disk=1,
                             vcpus=1, metadata=self.flavor_metadata))
            self.flavor_creator.create()

            # Create Image
            self.image_creator = OpenStackImage(self.os_creds,
                                                os_image_settings)
            self.image_creator.create()

        except Exception as e:
            self.tearDown()
            raise e

    def tearDown(self):
        """
        Cleans the created object
        """
        for inst_creator in self.inst_creators:
            try:
                inst_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning VM instance with message '
                    '- %s', e)

        if self.flavor_creator:
            try:
                self.flavor_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning flavor with message - %s',
                    e)

        if self.network_creator:
            try:
                self.network_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning network with message - %s',
                    e)

        if self.image_creator and not self.image_creator.image_settings.exists:
            try:
                self.image_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning image with message - %s', e)

        super(self.__class__, self).__clean__()

    def test_deploy_vm_to_each_compute_node(self):
        """
        Tests the creation of OpenStack VM instances to each compute node.
        """
        from snaps.openstack.utils import nova_utils
        nova = nova_utils.nova_client(
            self.admin_os_creds, self.admin_os_session)
        zone_hosts = nova_utils.get_availability_zone_hosts(nova)

        # Create Instance on each server/zone
        ctr = 0
        for zone in zone_hosts:
            inst_name = self.vm_inst_name + '-' + zone
            ctr += 1
            port_settings = PortConfig(
                name=self.port_base_name + '-' + str(ctr),
                network_name=self.priv_net_config.network_settings.name)

            instance_settings = VmInstanceConfig(
                name=inst_name,
                flavor=self.flavor_creator.flavor_settings.name,
                availability_zone=zone,
                port_settings=[port_settings])
            inst_creator = OpenStackVmInstance(
                self.admin_os_creds, instance_settings,
                self.image_creator.image_settings)
            self.inst_creators.append(inst_creator)
            inst_creator.create(block=True)
            avail_zone = inst_creator.get_vm_inst().availability_zone
            self.assertTrue(avail_zone in zone)
            compute_host = inst_creator.get_vm_inst().compute_host
            self.assertTrue(compute_host in zone)

        # Validate instances to ensure they've been deployed to the correct
        # server
        index = 0
        for zone in zone_hosts:
            creator = self.inst_creators[index]
            self.assertTrue(creator.vm_active(block=True))
            info = creator.get_vm_info()
            deployed_zone = info['OS-EXT-AZ:availability_zone']
            deployed_host = info['OS-EXT-SRV-ATTR:host']
            self.assertEqual(zone, deployed_zone + ':' + deployed_host)
            index += 1


class InstanceSecurityGroupTests(OSIntegrationTestCase):
    """
    Tests that include, add, and remove security groups from VM instances
    """

    def setUp(self):
        """
        Instantiates the CreateImage object that is responsible for downloading
        and creating an OS image file within OpenStack
        """
        super(self.__class__, self).__start__()

        self.guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.vm_inst_name = self.guid + '-inst'
        self.nova = nova_utils.nova_client(self.os_creds, self.os_session)
        os_image_settings = openstack_tests.cirros_image_settings(
            name=self.guid + '-image', image_metadata=self.image_metadata)

        self.vm_inst_name = self.guid + '-inst'
        self.port_1_name = self.guid + 'port-1'
        self.port_2_name = self.guid + 'port-2'
        self.floating_ip_name = self.guid + 'fip1'

        net_config = openstack_tests.get_priv_net_config(
            project_name=self.os_creds.project_name,
            net_name=self.guid + '-pub-net',
            subnet_name=self.guid + '-pub-subnet',
            router_name=self.guid + '-pub-router',
            external_net=self.ext_net_name,
            netconf_override=self.netconf_override)

        # Initialize for tearDown()
        self.image_creator = None
        self.flavor_creator = None
        self.network_creator = None
        self.router_creator = None
        self.inst_creator = None
        self.sec_grp_creators = list()

        try:
            # Create Image
            self.image_creator = OpenStackImage(self.os_creds,
                                                os_image_settings)
            self.image_creator.create()

            # Create Network
            self.network_creator = OpenStackNetwork(
                self.os_creds, net_config.network_settings)
            self.network_creator.create()

            # Create Flavor
            self.flavor_creator = OpenStackFlavor(
                self.admin_os_creds,
                FlavorConfig(name=self.guid + '-flavor-name', ram=256,
                             disk=10, vcpus=2,
                             metadata=self.flavor_metadata))
            self.flavor_creator.create()

            self.port_settings = PortConfig(
                name=self.guid + '-port',
                network_name=net_config.network_settings.name)
        except Exception as e:
            self.tearDown()
            raise e

    def tearDown(self):
        """
        Cleans the created object
        """
        if self.inst_creator:
            try:
                self.inst_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning VM instance with message -'
                    ' %s', e)

        for sec_grp_creator in self.sec_grp_creators:
            try:
                sec_grp_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning security group with message'
                    ' - %s', e)

        if self.flavor_creator:
            try:
                self.flavor_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning flavor with message - %s',
                    e)

        if self.network_creator:
            try:
                self.network_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning network with message - %s',
                    e)

        if self.image_creator and not self.image_creator.image_settings.exists:
            try:
                self.image_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning image with message - %s', e)

        super(self.__class__, self).__clean__()

    def test_add_security_group(self):
        """
        Tests the addition of a security group created after the instance.
        """
        # Create instance
        instance_settings = VmInstanceConfig(
            name=self.vm_inst_name,
            flavor=self.flavor_creator.flavor_settings.name,
            port_settings=[self.port_settings])
        self.inst_creator = OpenStackVmInstance(
            self.os_creds, instance_settings,
            self.image_creator.image_settings)
        vm_inst = self.inst_creator.create(block=True)
        self.assertIsNotNone(vm_inst)

        # Create security group object to add to instance
        sec_grp_settings = SecurityGroupConfig(
            name=self.guid + '-name', description='hello group')
        sec_grp_creator = OpenStackSecurityGroup(self.os_creds,
                                                 sec_grp_settings)
        sec_grp = sec_grp_creator.create()
        self.sec_grp_creators.append(sec_grp_creator)

        # Check that group has not been added
        self.assertFalse(inst_has_sec_grp(
            self.nova, self.inst_creator.get_vm_inst(), sec_grp_settings.name))

        # Add security group to instance after activated
        self.inst_creator.add_security_group(sec_grp)

        # Validate that security group has been added
        self.assertTrue(inst_has_sec_grp(
            self.nova, self.inst_creator.get_vm_inst(), sec_grp_settings.name))

    def test_add_invalid_security_group(self):
        """
        Tests the addition of a security group that no longer exists.
        """
        # Create instance
        instance_settings = VmInstanceConfig(
            name=self.vm_inst_name,
            flavor=self.flavor_creator.flavor_settings.name,
            port_settings=[self.port_settings])
        self.inst_creator = OpenStackVmInstance(
            self.os_creds, instance_settings,
            self.image_creator.image_settings)
        vm_inst = self.inst_creator.create(block=True)
        self.assertIsNotNone(vm_inst)

        # Create security group object to add to instance
        sec_grp_settings = SecurityGroupConfig(
            name=self.guid + '-name', description='hello group')
        sec_grp_creator = OpenStackSecurityGroup(self.os_creds,
                                                 sec_grp_settings)
        sec_grp = sec_grp_creator.create()
        sec_grp_creator.clean()
        self.sec_grp_creators.append(sec_grp_creator)

        # Check that group has not been added
        self.assertFalse(inst_has_sec_grp(
            self.nova, self.inst_creator.get_vm_inst(), sec_grp_settings.name))

        # Add security group to instance after activated
        self.assertFalse(self.inst_creator.add_security_group(sec_grp))

        # Validate that security group has been added
        self.assertFalse(inst_has_sec_grp(
            self.nova, self.inst_creator.get_vm_inst(), sec_grp_settings.name))

    def test_remove_security_group(self):
        """
        Tests the removal of a security group created before and added to the
        instance.
        """
        # Create security group object to add to instance
        sec_grp_settings = SecurityGroupConfig(
            name=self.guid + '-name', description='hello group')
        sec_grp_creator = OpenStackSecurityGroup(self.os_creds,
                                                 sec_grp_settings)
        sec_grp = sec_grp_creator.create()
        self.sec_grp_creators.append(sec_grp_creator)

        # Create instance
        instance_settings = VmInstanceConfig(
            name=self.vm_inst_name,
            flavor=self.flavor_creator.flavor_settings.name,
            security_group_names=[sec_grp_settings.name],
            port_settings=[self.port_settings])
        self.inst_creator = OpenStackVmInstance(
            self.os_creds, instance_settings,
            self.image_creator.image_settings)
        vm_inst = self.inst_creator.create(block=True)
        self.assertIsNotNone(vm_inst)

        # Check that group has been added
        self.assertTrue(inst_has_sec_grp(
            self.nova, vm_inst, sec_grp_settings.name))

        # Add security group to instance after activated
        self.assertTrue(self.inst_creator.remove_security_group(sec_grp))

        # Validate that security group has been added
        self.assertFalse(inst_has_sec_grp(
            self.nova, self.inst_creator.get_vm_inst(), sec_grp_settings.name))

    def test_remove_security_group_never_added(self):
        """
        Tests the removal of a security group that was never added in the first
        place.
        """
        # Create security group object to add to instance
        sec_grp_settings = SecurityGroupConfig(
            name=self.guid + '-name', description='hello group')
        sec_grp_creator = OpenStackSecurityGroup(self.os_creds,
                                                 sec_grp_settings)
        sec_grp = sec_grp_creator.create()
        self.sec_grp_creators.append(sec_grp_creator)

        # Create instance
        instance_settings = VmInstanceConfig(
            name=self.vm_inst_name,
            flavor=self.flavor_creator.flavor_settings.name,
            port_settings=[self.port_settings])
        self.inst_creator = OpenStackVmInstance(
            self.os_creds, instance_settings,
            self.image_creator.image_settings)
        vm_inst = self.inst_creator.create(block=True)
        self.assertIsNotNone(vm_inst)

        # Check that group has been added
        self.assertFalse(inst_has_sec_grp(
            self.nova, self.inst_creator.get_vm_inst(), sec_grp_settings.name))

        # Add security group to instance after activated
        self.assertFalse(self.inst_creator.remove_security_group(sec_grp))

        # Validate that security group has been added
        self.assertFalse(inst_has_sec_grp(
            self.nova, self.inst_creator.get_vm_inst(), sec_grp_settings.name))

    def test_add_same_security_group(self):
        """
        Tests the addition of a security group created before add added to the
        instance.
        """
        # Create security group object to add to instance
        sec_grp_settings = SecurityGroupConfig(
            name=self.guid + '-name', description='hello group')
        sec_grp_creator = OpenStackSecurityGroup(self.os_creds,
                                                 sec_grp_settings)
        sec_grp = sec_grp_creator.create()
        self.sec_grp_creators.append(sec_grp_creator)

        # Create instance
        instance_settings = VmInstanceConfig(
            name=self.vm_inst_name,
            flavor=self.flavor_creator.flavor_settings.name,
            security_group_names=[sec_grp_settings.name],
            port_settings=[self.port_settings])
        self.inst_creator = OpenStackVmInstance(
            self.os_creds, instance_settings,
            self.image_creator.image_settings)
        vm_inst = self.inst_creator.create(block=True)
        self.assertIsNotNone(vm_inst)

        # Check that group has been added
        self.assertTrue(inst_has_sec_grp(
            self.nova, self.inst_creator.get_vm_inst(), sec_grp_settings.name))

        # Add security group to instance after activated
        self.assertTrue(self.inst_creator.add_security_group(sec_grp))

        # Validate that security group has been added
        self.assertTrue(inst_has_sec_grp(
            self.nova, self.inst_creator.get_vm_inst(), sec_grp_settings.name))


def inst_has_sec_grp(nova, vm_inst, sec_grp_name):
    """
    Returns true if instance has a security group of a given name
    :param nova: the nova client
    :param vm_inst: the VmInst domain object
    :param sec_grp_name: the name of the security group to validate
    :return: T/F
    """
    sec_grp_names = nova_utils.get_server_security_group_names(nova, vm_inst)
    for name in sec_grp_names:
        if sec_grp_name == name:
            return True
    return False


def validate_ssh_client(instance_creator, fip_name=None):
    """
    Returns True if instance_creator returns an SSH client that is valid
    :param instance_creator: the object responsible for creating the VM
                             instance
    :param fip_name: the name of the floating IP to use
    :return: T/F
    """
    ssh_active = instance_creator.vm_ssh_active(block=True)

    if ssh_active:
        ssh_client = instance_creator.ssh_client(fip_name=fip_name)
        if ssh_client:
            try:
                out = ssh_client.exec_command('pwd')[1]
                channel = out.channel
                in_buffer = channel.in_buffer
                pwd_out = in_buffer.read(1024)
                if not pwd_out or len(pwd_out) < 10:
                    return False
                return True
            finally:
                ssh_client.close()
        else:
            return False

    return False


class CreateInstanceFromThreePartImage(OSIntegrationTestCase):
    """
    Test for the CreateInstance class for creating an image from a 3-part image
    """

    def setUp(self):
        """
        Instantiates the CreateImage object that is responsible for downloading
        and creating an OS image file within OpenStack
        """
        super(self.__class__, self).__start__()

        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.image_name = guid
        self.vm_inst_name = guid + '-inst'
        self.nova = nova_utils.nova_client(self.os_creds, self.os_session)

        net_config = openstack_tests.get_priv_net_config(
            project_name=self.os_creds.project_name,
            net_name=guid + '-pub-net', subnet_name=guid + '-pub-subnet',
            router_name=guid + '-pub-router', external_net=self.ext_net_name,
            netconf_override=self.netconf_override)

        # Initialize for tearDown()
        self.image_creator = None
        self.network_creator = None
        self.flavor_creator = None
        self.inst_creator = None

        try:
            if self.image_metadata and 'disk_file' in self.image_metadata:
                metadata = self.image_metadata
            elif self.image_metadata and 'cirros' in self.image_metadata \
                    and 'disk_file' in self.image_metadata['cirros']:
                metadata = self.image_metadata['cirros']
            else:
                metadata = {
                    'disk_url': openstack_tests.CIRROS_DEFAULT_IMAGE_URL,
                    'kernel_url':
                        openstack_tests.CIRROS_DEFAULT_KERNEL_IMAGE_URL,
                    'ramdisk_url':
                        openstack_tests.CIRROS_DEFAULT_RAMDISK_IMAGE_URL}

            image_settings = openstack_tests.cirros_image_settings(
                name=self.image_name,
                image_metadata=metadata)

            if not image_settings.ramdisk_image_settings or not \
                    image_settings.kernel_image_settings:
                logger.warn(
                    '3 Part image will not be tested. Image metadata has '
                    'overridden this functionality')

            self.image_creator = OpenStackImage(self.os_creds, image_settings)
            self.image_creator.create()

            # Create Flavor
            self.flavor_creator = OpenStackFlavor(
                self.admin_os_creds,
                FlavorConfig(name=guid + '-flavor-name', ram=256, disk=10,
                             vcpus=2, metadata=self.flavor_metadata))
            self.flavor_creator.create()

            # Create Network
            self.network_creator = OpenStackNetwork(
                self.os_creds, net_config.network_settings)
            self.network_creator.create()

            self.port_settings = PortConfig(
                name=guid + '-port',
                network_name=net_config.network_settings.name)
        except Exception as e:
            self.tearDown()
            raise e

    def tearDown(self):
        """
        Cleans the created object
        """
        if self.inst_creator:
            try:
                self.inst_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning VM instance with message -'
                    ' %s', e)

        if self.flavor_creator:
            try:
                self.flavor_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning flavor with message - %s',
                    e)

        if self.network_creator:
            try:
                self.network_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning network with message - %s',
                    e)

        if self.image_creator and not self.image_creator.image_settings.exists:
            try:
                self.image_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning image with message - %s', e)

        super(self.__class__, self).__clean__()

    def test_create_instance_from_three_part_image(self):
        """
        Tests the creation of an OpenStack instance from a 3-part image.
        """
        instance_settings = VmInstanceConfig(
            name=self.vm_inst_name,
            flavor=self.flavor_creator.flavor_settings.name,
            port_settings=[self.port_settings])

        # The last created image is the main image from which we create the
        # instance
        self.inst_creator = OpenStackVmInstance(
            self.os_creds, instance_settings,
            self.image_creator.image_settings)

        vm_inst = self.inst_creator.create()
        self.assertIsNotNone(vm_inst)
        self.assertTrue(self.inst_creator.vm_active(block=True))


class CreateInstanceMockOfflineTests(OSComponentTestCase):
    """
    Tests the custom image_metadata that can be set by clients for handling
    images differently than the default behavior of the existing tests
    primarily for offline testing
    """

    def setUp(self):
        """
        Instantiates the CreateImage object that is responsible for downloading
        and creating an OS image file within OpenStack
        """
        self.guid = self.__class__.__name__ + '-' + str(uuid.uuid4())

        self.tmpDir = 'tmp/' + str(self.guid)
        if not os.path.exists(self.tmpDir):
            os.makedirs(self.tmpDir)

        self.image_name = self.guid + '-image'
        self.vm_inst_name = self.guid + '-inst'
        self.port_1_name = self.guid + 'port-1'

        # Initialize for tearDown()
        self.image_creator = None
        self.network_creator = None
        self.flavor_creator = None
        self.inst_creator = None

        self.priv_net_config = openstack_tests.get_priv_net_config(
            project_name=self.os_creds.project_name,
            net_name=self.guid + '-priv-net',
            subnet_name=self.guid + '-priv-subnet')
        self.port_settings = PortConfig(
            name=self.port_1_name,
            network_name=self.priv_net_config.network_settings.name)

        try:
            # Download image file
            self.image_file = file_utils.download(
                openstack_tests.CIRROS_DEFAULT_IMAGE_URL, self.tmpDir)

            # Create Network
            self.network_creator = OpenStackNetwork(
                self.os_creds, self.priv_net_config.network_settings)
            self.network_creator.create()

            # Create Flavor
            self.flavor_creator = OpenStackFlavor(
                self.os_creds,
                FlavorConfig(
                    name=self.guid + '-flavor-name', ram=256, disk=10,
                    vcpus=1))
            self.flavor_creator.create()
        except Exception as e:
            self.tearDown()
            raise e

    def tearDown(self):
        """
        Cleans the created object
        """
        if self.inst_creator:
            try:
                self.inst_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning VM instance with message - '
                    '%s', e)

        if self.network_creator:
            try:
                self.network_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning network with message - %s',
                    e)

        if self.flavor_creator:
            try:
                self.flavor_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning flavor with message - %s',
                    e)

        if self.image_creator:
            try:
                self.image_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning image with message - %s', e)

        if os.path.exists(self.tmpDir) and os.path.isdir(self.tmpDir):
            shutil.rmtree(self.tmpDir)

        super(self.__class__, self).__clean__()

    def test_inst_from_file_image_simple_flat(self):
        """
        Creates a VM instance from a locally sourced file image using simply
        the 'disk_file' attribute vs. using the 'config' option which
        completely overrides all image settings
        :return: 
        """
        metadata = {'disk_file': self.image_file.name}

        os_image_settings = openstack_tests.cirros_image_settings(
            name=self.image_name, image_metadata=metadata)
        self.assertEqual(self.image_file.name, os_image_settings.image_file)
        self.assertEqual(openstack_tests.CIRROS_USER,
                         os_image_settings.image_user)
        self.assertIsNone(os_image_settings.url)
        self.assertFalse(os_image_settings.exists)
        self.assertEqual(openstack_tests.DEFAULT_IMAGE_FORMAT,
                         os_image_settings.format)

        self.assertIsNone(os_image_settings.kernel_image_settings)
        self.assertIsNone(os_image_settings.ramdisk_image_settings)

        self.image_creator = OpenStackImage(self.os_creds, os_image_settings)
        self.image_creator.create()

        instance_settings = VmInstanceConfig(
            name=self.vm_inst_name,
            flavor=self.flavor_creator.flavor_settings.name,
            port_settings=[self.port_settings])
        self.inst_creator = OpenStackVmInstance(
            self.os_creds, instance_settings,
            self.image_creator.image_settings)
        self.inst_creator.create()

        self.assertTrue(self.inst_creator.vm_active(block=True))

    def test_inst_from_file_image_simple_nested(self):
        """
        Creates a VM instance from a locally sourced file image using simply
        the 'disk_file' attribute under 'cirros' vs. using the 'config' option
        which completely overrides all image settings
        :return: 
        """
        metadata = {'cirros': {'disk_file': self.image_file.name}}

        os_image_settings = openstack_tests.cirros_image_settings(
            name=self.image_name, image_metadata=metadata)
        self.assertEqual(self.image_file.name, os_image_settings.image_file)
        self.assertEqual(openstack_tests.CIRROS_USER,
                         os_image_settings.image_user)
        self.assertIsNone(os_image_settings.url)
        self.assertFalse(os_image_settings.exists)
        self.assertEqual(openstack_tests.DEFAULT_IMAGE_FORMAT,
                         os_image_settings.format)

        self.assertIsNone(os_image_settings.kernel_image_settings)
        self.assertIsNone(os_image_settings.ramdisk_image_settings)

        self.image_creator = OpenStackImage(self.os_creds, os_image_settings)
        self.image_creator.create()

        instance_settings = VmInstanceConfig(
            name=self.vm_inst_name,
            flavor=self.flavor_creator.flavor_settings.name,
            port_settings=[self.port_settings])
        self.inst_creator = OpenStackVmInstance(
            self.os_creds, instance_settings,
            self.image_creator.image_settings)
        self.inst_creator.create()

        self.assertTrue(self.inst_creator.vm_active(block=True))

    def test_inst_from_existing(self):
        """
        Creates a VM instance from a image creator that has been configured to
        use an existing image
        :return: 
        """
        os_image_settings = openstack_tests.cirros_image_settings(
            name=self.image_name)
        self.image_creator = OpenStackImage(self.os_creds, os_image_settings)
        self.image_creator.create()

        image_settings = self.image_creator.image_settings
        test_image_creator = OpenStackImage(
            self.os_creds,
            ImageConfig(
                name=image_settings.name, image_user=image_settings.image_user,
                exists=True))
        test_image_creator.create()
        self.assertEqual(self.image_creator.get_image().id,
                         test_image_creator.get_image().id)

        instance_settings = VmInstanceConfig(
            name=self.vm_inst_name,
            flavor=self.flavor_creator.flavor_settings.name,
            port_settings=[self.port_settings])
        self.inst_creator = OpenStackVmInstance(
            self.os_creds, instance_settings,
            test_image_creator.image_settings)
        self.inst_creator.create()

        self.assertTrue(self.inst_creator.vm_active(block=True))

    def test_inst_from_file_image_complex(self):
        """
        Creates a VM instance from a locally sourced file image by overriding
        the default settings by using a dict() that can be read in by
        ImageSettings
        :return: 
        """

        os_image_settings = openstack_tests.cirros_image_settings(
            name=self.image_name)
        self.image_creator = OpenStackImage(self.os_creds, os_image_settings)
        self.image_creator.create()

        metadata = {
            'cirros': {
                'config': {
                    'name': os_image_settings.name,
                    'image_user': os_image_settings.image_user,
                    'exists': True}}}
        test_image_settings = openstack_tests.cirros_image_settings(
            image_metadata=metadata)
        test_image = OpenStackImage(self.os_creds, test_image_settings)
        test_image.create()

        instance_settings = VmInstanceConfig(
            name=self.vm_inst_name,
            flavor=self.flavor_creator.flavor_settings.name,
            port_settings=[self.port_settings])
        self.inst_creator = OpenStackVmInstance(self.os_creds,
                                                instance_settings,
                                                test_image_settings)
        self.inst_creator.create()

        self.assertTrue(self.inst_creator.vm_active(block=True))

    def test_inst_from_file_3part_image_complex(self):
        """
        Creates a VM instance from a locally sourced file image by overriding
        the default settings by using a dict() that can be read in by
        ImageSettings
        :return: 
        """

        kernel_file = file_utils.download(
            openstack_tests.CIRROS_DEFAULT_KERNEL_IMAGE_URL, self.tmpDir)
        ramdisk_file = file_utils.download(
            openstack_tests.CIRROS_DEFAULT_RAMDISK_IMAGE_URL, self.tmpDir)

        metadata = {
            'cirros': {
                'config': {
                    'name': self.image_name,
                    'image_user': openstack_tests.CIRROS_USER,
                    'image_file': self.image_file.name,
                    'format': openstack_tests.DEFAULT_IMAGE_FORMAT,
                    'kernel_image_settings': {
                        'name': self.image_name + '-kernel',
                        'image_user': openstack_tests.CIRROS_USER,
                        'image_file': kernel_file.name,
                        'format': openstack_tests.DEFAULT_IMAGE_FORMAT},
                    'ramdisk_image_settings': {
                        'name': self.image_name + '-ramdisk',
                        'image_user': openstack_tests.CIRROS_USER,
                        'image_file': ramdisk_file.name,
                        'format': openstack_tests.DEFAULT_IMAGE_FORMAT}}}}

        os_image_settings = openstack_tests.cirros_image_settings(
            name=self.image_name, image_metadata=metadata)
        self.assertEqual(self.image_name, os_image_settings.name)
        self.assertEqual(self.image_file.name, os_image_settings.image_file)
        self.assertEqual(openstack_tests.CIRROS_USER,
                         os_image_settings.image_user)
        self.assertIsNone(os_image_settings.url)
        self.assertFalse(os_image_settings.exists)
        self.assertEqual(openstack_tests.DEFAULT_IMAGE_FORMAT,
                         os_image_settings.format)

        self.assertIsNotNone(os_image_settings.kernel_image_settings)
        self.assertEqual(self.image_name + '-kernel',
                         os_image_settings.kernel_image_settings.name)
        self.assertEqual(kernel_file.name,
                         os_image_settings.kernel_image_settings.image_file)
        self.assertEqual(openstack_tests.CIRROS_USER,
                         os_image_settings.kernel_image_settings.image_user)
        self.assertIsNone(os_image_settings.kernel_image_settings.url)
        self.assertFalse(os_image_settings.kernel_image_settings.exists)
        self.assertEqual(openstack_tests.DEFAULT_IMAGE_FORMAT,
                         os_image_settings.kernel_image_settings.format)

        self.assertIsNotNone(os_image_settings.ramdisk_image_settings)
        self.assertEqual(self.image_name + '-ramdisk',
                         os_image_settings.ramdisk_image_settings.name)
        self.assertEqual(ramdisk_file.name,
                         os_image_settings.ramdisk_image_settings.image_file)
        self.assertEqual(openstack_tests.CIRROS_USER,
                         os_image_settings.ramdisk_image_settings.image_user)
        self.assertIsNone(os_image_settings.ramdisk_image_settings.url)
        self.assertFalse(os_image_settings.ramdisk_image_settings.exists)
        self.assertEqual(openstack_tests.DEFAULT_IMAGE_FORMAT,
                         os_image_settings.ramdisk_image_settings.format)

        self.image_creator = OpenStackImage(self.os_creds, os_image_settings)
        self.image_creator.create()

        instance_settings = VmInstanceConfig(
            name=self.vm_inst_name,
            flavor=self.flavor_creator.flavor_settings.name,
            port_settings=[self.port_settings])
        self.inst_creator = OpenStackVmInstance(
            self.os_creds, instance_settings,
            self.image_creator.image_settings)
        self.inst_creator.create()

        self.assertTrue(self.inst_creator.vm_active(block=True))

    def test_inst_from_file_3part_image_simple_flat(self):
        """
        Creates a VM instance from a 3-part image locally sourced from file
        images using simply the 'disk_file', 'kernel_file', and 'ramdisk_file'
        attributes vs. using the 'config' option which completely overrides all
        image settings
        :return: 
        """
        kernel_file = file_utils.download(
            openstack_tests.CIRROS_DEFAULT_KERNEL_IMAGE_URL, self.tmpDir)
        ramdisk_file = file_utils.download(
            openstack_tests.CIRROS_DEFAULT_RAMDISK_IMAGE_URL, self.tmpDir)

        metadata = {'disk_file': self.image_file.name,
                    'kernel_file': kernel_file.name,
                    'ramdisk_file': ramdisk_file.name}

        os_image_settings = openstack_tests.cirros_image_settings(
            name=self.image_name, image_metadata=metadata)

        self.assertEqual(self.image_name, os_image_settings.name)
        self.assertEqual(self.image_file.name, os_image_settings.image_file)
        self.assertEqual(openstack_tests.CIRROS_USER,
                         os_image_settings.image_user)
        self.assertIsNone(os_image_settings.url)
        self.assertFalse(os_image_settings.exists)
        self.assertEqual(openstack_tests.DEFAULT_IMAGE_FORMAT,
                         os_image_settings.format)

        self.assertIsNotNone(os_image_settings.kernel_image_settings)
        self.assertEqual(self.image_name + '-kernel',
                         os_image_settings.kernel_image_settings.name)
        self.assertEqual(kernel_file.name,
                         os_image_settings.kernel_image_settings.image_file)
        self.assertEqual(openstack_tests.CIRROS_USER,
                         os_image_settings.kernel_image_settings.image_user)
        self.assertIsNone(os_image_settings.kernel_image_settings.url)
        self.assertFalse(os_image_settings.kernel_image_settings.exists)
        self.assertEqual(openstack_tests.DEFAULT_IMAGE_FORMAT,
                         os_image_settings.kernel_image_settings.format)

        self.assertIsNotNone(os_image_settings.ramdisk_image_settings)
        self.assertEqual(self.image_name + '-ramdisk',
                         os_image_settings.ramdisk_image_settings.name)
        self.assertEqual(ramdisk_file.name,
                         os_image_settings.ramdisk_image_settings.image_file)
        self.assertEqual(openstack_tests.CIRROS_USER,
                         os_image_settings.ramdisk_image_settings.image_user)
        self.assertIsNone(os_image_settings.ramdisk_image_settings.url)
        self.assertFalse(os_image_settings.ramdisk_image_settings.exists)
        self.assertEqual(openstack_tests.DEFAULT_IMAGE_FORMAT,
                         os_image_settings.ramdisk_image_settings.format)

        self.image_creator = OpenStackImage(self.os_creds, os_image_settings)
        self.image_creator.create()

        self.assertIsNotNone(self.image_creator.get_kernel_image())
        self.assertIsNotNone(self.image_creator.get_ramdisk_image())

        instance_settings = VmInstanceConfig(
            name=self.vm_inst_name,
            flavor=self.flavor_creator.flavor_settings.name,
            port_settings=[self.port_settings])
        self.inst_creator = OpenStackVmInstance(
            self.os_creds, instance_settings,
            self.image_creator.image_settings)
        self.inst_creator.create()

        self.assertTrue(self.inst_creator.vm_active(block=True))

    def test_inst_from_file_3part_image_simple_nested(self):
        """
        Creates a VM instance from a 3-part image locally sourced from file
        images using simply the 'disk_file', 'kernel_file', and 'ramdisk_file'
        attributes under 'cirros' vs. using the 'config' option which
        completely overrides all image settings
        :return: 
        """
        kernel_file = file_utils.download(
            openstack_tests.CIRROS_DEFAULT_KERNEL_IMAGE_URL, self.tmpDir)
        ramdisk_file = file_utils.download(
            openstack_tests.CIRROS_DEFAULT_RAMDISK_IMAGE_URL, self.tmpDir)

        metadata = {'cirros': {'disk_file': self.image_file.name,
                               'kernel_file': kernel_file.name,
                               'ramdisk_file': ramdisk_file.name}}

        os_image_settings = openstack_tests.cirros_image_settings(
            name=self.image_name, image_metadata=metadata)

        self.assertEqual(self.image_name, os_image_settings.name)
        self.assertEqual(self.image_file.name, os_image_settings.image_file)
        self.assertEqual(openstack_tests.CIRROS_USER,
                         os_image_settings.image_user)
        self.assertIsNone(os_image_settings.url)
        self.assertFalse(os_image_settings.exists)
        self.assertEqual(openstack_tests.DEFAULT_IMAGE_FORMAT,
                         os_image_settings.format)

        self.assertIsNotNone(os_image_settings.kernel_image_settings)
        self.assertEqual(self.image_name + '-kernel',
                         os_image_settings.kernel_image_settings.name)
        self.assertEqual(kernel_file.name,
                         os_image_settings.kernel_image_settings.image_file)
        self.assertEqual(openstack_tests.CIRROS_USER,
                         os_image_settings.kernel_image_settings.image_user)
        self.assertIsNone(os_image_settings.kernel_image_settings.url)
        self.assertFalse(os_image_settings.kernel_image_settings.exists)
        self.assertEqual(openstack_tests.DEFAULT_IMAGE_FORMAT,
                         os_image_settings.kernel_image_settings.format)

        self.assertIsNotNone(os_image_settings.ramdisk_image_settings)
        self.assertEqual(self.image_name + '-ramdisk',
                         os_image_settings.ramdisk_image_settings.name)
        self.assertEqual(ramdisk_file.name,
                         os_image_settings.ramdisk_image_settings.image_file)
        self.assertEqual(openstack_tests.CIRROS_USER,
                         os_image_settings.ramdisk_image_settings.image_user)
        self.assertIsNone(os_image_settings.ramdisk_image_settings.url)
        self.assertFalse(os_image_settings.ramdisk_image_settings.exists)
        self.assertEqual(openstack_tests.DEFAULT_IMAGE_FORMAT,
                         os_image_settings.ramdisk_image_settings.format)

        self.image_creator = OpenStackImage(self.os_creds, os_image_settings)
        self.image_creator.create()

        self.assertIsNotNone(self.image_creator.get_kernel_image())
        self.assertIsNotNone(self.image_creator.get_ramdisk_image())

        instance_settings = VmInstanceConfig(
            name=self.vm_inst_name,
            flavor=self.flavor_creator.flavor_settings.name,
            port_settings=[self.port_settings])
        self.inst_creator = OpenStackVmInstance(
            self.os_creds, instance_settings,
            self.image_creator.image_settings)
        self.inst_creator.create()

        self.assertTrue(self.inst_creator.vm_active(block=True))

    def test_inst_from_file_3part_image_existing(self):
        """
        Creates a VM instance from a 3-part image that is existing
        :return: 
        """
        kernel_file = file_utils.download(
            openstack_tests.CIRROS_DEFAULT_KERNEL_IMAGE_URL, self.tmpDir)
        ramdisk_file = file_utils.download(
            openstack_tests.CIRROS_DEFAULT_RAMDISK_IMAGE_URL, self.tmpDir)

        metadata = {'cirros': {'disk_file': self.image_file.name,
                               'kernel_file': kernel_file.name,
                               'ramdisk_file': ramdisk_file.name}}

        os_image_settings = openstack_tests.cirros_image_settings(
            name=self.image_name, image_metadata=metadata)
        self.image_creator = OpenStackImage(self.os_creds, os_image_settings)
        self.image_creator.create()

        image_settings = self.image_creator.image_settings
        test_image_creator = OpenStackImage(
            self.os_creds,
            ImageConfig(
                name=image_settings.name, image_user=image_settings.image_user,
                exists=True))
        test_image_creator.create()
        self.assertEqual(self.image_creator.get_image().id,
                         test_image_creator.get_image().id)

        instance_settings = VmInstanceConfig(
            name=self.vm_inst_name,
            flavor=self.flavor_creator.flavor_settings.name,
            port_settings=[self.port_settings])
        self.inst_creator = OpenStackVmInstance(
            self.os_creds, instance_settings,
            test_image_creator.image_settings)
        self.inst_creator.create()

        self.assertTrue(self.inst_creator.vm_active(block=True))


class CreateInstanceTwoNetTests(OSIntegrationTestCase):
    """
    Tests the ability of two VMs to communicate when attached to separate
    private networks that are tied together with a router.
    """

    def setUp(self):
        """
        Instantiates the CreateImage object that is responsible for downloading
        and creating an OS image file within OpenStack
        """
        super(self.__class__, self).__start__()

        cidr1 = '10.200.201.0/24'
        cidr2 = '10.200.202.0/24'
        static_gateway_ip1 = '10.200.201.1'
        static_gateway_ip2 = '10.200.202.1'
        self.ip1 = '10.200.201.5'
        self.ip2 = '10.200.202.5'

        self.nova = nova_utils.nova_client(self.os_creds, self.os_session)

        # Initialize for tearDown()
        self.image_creator = None
        self.network_creators = list()
        self.router_creator = None
        self.flavor_creator = None
        self.sec_grp_creator = None
        self.inst_creators = list()

        self.guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.vm_inst1_name = self.guid + '-inst1'
        self.vm_inst2_name = self.guid + '-inst2'
        self.port_1_name = self.guid + '-vm1-port'
        self.port_2_name = self.guid + '-vm2-port'
        self.net_config_1 = NetworkConfig(
            name=self.guid + '-net1',
            subnet_settings=[
                create_network.SubnetConfig(
                    cidr=cidr1, name=self.guid + '-subnet1',
                    gateway_ip=static_gateway_ip1)])
        self.net_config_2 = NetworkConfig(
            name=self.guid + '-net2',
            subnet_settings=[
                create_network.SubnetConfig(
                    cidr=cidr2, name=self.guid + '-subnet2',
                    gateway_ip=static_gateway_ip2)])

        image_name = self.__class__.__name__ + '-' + str(uuid.uuid4())
        os_image_settings = openstack_tests.cirros_image_settings(
            name=image_name, image_metadata=self.image_metadata)

        try:
            # Create Image
            self.image_creator = OpenStackImage(
                self.os_creds, os_image_settings)
            self.image_creator.create()

            # First network is public
            self.network_creators.append(OpenStackNetwork(
                self.os_creds, self.net_config_1))

            # Second network is private
            self.network_creators.append(OpenStackNetwork(
                self.os_creds, self.net_config_2))
            for network_creator in self.network_creators:
                network_creator.create()

            port_settings = [
                PortConfig(
                    name=self.guid + '-router-port1',
                    ip_addrs=[{
                        'subnet_name':
                            self.net_config_1.subnet_settings[0].name,
                        'ip': static_gateway_ip1
                    }],
                    network_name=self.net_config_1.name),
                PortConfig(
                    name=self.guid + '-router-port2',
                    ip_addrs=[{
                        'subnet_name':
                            self.net_config_2.subnet_settings[0].name,
                        'ip': static_gateway_ip2
                    }],
                    network_name=self.net_config_2.name)]

            router_settings = RouterConfig(
                name=self.guid + '-pub-router', port_settings=port_settings)
            self.router_creator = OpenStackRouter(
                self.os_creds, router_settings)
            self.router_creator.create()

            self.flavor_creator = OpenStackFlavor(
                self.admin_os_creds,
                FlavorConfig(name=self.guid + '-flavor-name', ram=512,
                             disk=10, vcpus=2,
                             metadata=self.flavor_metadata))
            self.flavor_creator.create()

            sec_grp_name = self.guid + '-sec-grp'
            rule1 = SecurityGroupRuleConfig(
                sec_grp_name=sec_grp_name, direction=Direction.ingress,
                protocol=Protocol.icmp)
            self.sec_grp_creator = OpenStackSecurityGroup(
                self.os_creds,
                SecurityGroupConfig(
                    name=sec_grp_name, rule_settings=[rule1]))
            self.sec_grp_creator.create()
        except:
            self.tearDown()
            raise

    def tearDown(self):
        """
        Cleans the created objects
        """
        for inst_creator in self.inst_creators:
            try:
                inst_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning VM instance with message '
                    '- %s', e)

        if self.flavor_creator:
            try:
                self.flavor_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning flavor with message - %s',
                    e)

        if self.router_creator:
            try:
                self.router_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning router with message - %s',
                    e)

        for network_creator in self.network_creators:
            try:
                network_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning network with message - %s',
                    e)

        if self.sec_grp_creator:
            try:
                self.sec_grp_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning security group with message'
                    ' - %s', e)

        if self.image_creator and not self.image_creator.image_settings.exists:
            try:
                self.image_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning image with message - %s', e)

        super(self.__class__, self).__clean__()

    def test_ping_via_router(self):
        """
        Tests the creation of two OpenStack instances with one port on
        different private networks wit a router in between to ensure that they
        can ping
        through
        """
        # Create ports/NICs for instance
        ports_settings = []
        ctr = 1
        for network_creator in self.network_creators:
            ports_settings.append(PortConfig(
                name=self.guid + '-port-' + str(ctr),
                network_name=network_creator.network_settings.name))
            ctr += 1

        # Configure instances
        instance1_settings = VmInstanceConfig(
            name=self.vm_inst1_name,
            flavor=self.flavor_creator.flavor_settings.name,
            userdata=_get_ping_userdata(self.ip2),
            port_settings=[PortConfig(
                name=self.port_1_name,
                ip_addrs=[{
                    'subnet_name':
                        self.net_config_1.subnet_settings[0].name,
                    'ip': self.ip1
                }],
                network_name=self.network_creators[0].network_settings.name)])
        instance2_settings = VmInstanceConfig(
            name=self.vm_inst2_name,
            flavor=self.flavor_creator.flavor_settings.name,
            userdata=_get_ping_userdata(self.ip1),
            port_settings=[PortConfig(
                name=self.port_2_name,
                ip_addrs=[{
                    'subnet_name':
                        self.net_config_2.subnet_settings[0].name,
                    'ip': self.ip2
                }],
                network_name=self.network_creators[1].network_settings.name)])

        # Create instances
        self.inst_creators.append(OpenStackVmInstance(
            self.os_creds, instance1_settings,
            self.image_creator.image_settings))
        self.inst_creators.append(OpenStackVmInstance(
            self.os_creds, instance2_settings,
            self.image_creator.image_settings))

        for inst_creator in self.inst_creators:
            inst_creator.create(block=True)

        # Check for DHCP lease
        self.assertTrue(check_dhcp_lease(self.inst_creators[0], self.ip1))
        self.assertTrue(check_dhcp_lease(self.inst_creators[1], self.ip2))

        # Effectively blocks until VM has been properly activated
        self.assertTrue(check_ping(self.inst_creators[0]))
        self.assertTrue(check_ping(self.inst_creators[1]))


class CreateInstanceVolumeTests(OSIntegrationTestCase):
    """
    Simple instance creation with an attached volume
    """

    def setUp(self):
        """
        Instantiates the CreateImage object that is responsible for downloading
        and creating an OS image file
        within OpenStack
        """
        super(self.__class__, self).__start__()

        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.vm_inst_name = guid + '-inst'
        self.nova = nova_utils.nova_client(
            self.os_creds, self.os_session)
        self.neutron = neutron_utils.neutron_client(
            self.os_creds, self.os_session)
        os_image_settings = openstack_tests.cirros_image_settings(
            name=guid + '-image', image_metadata=self.image_metadata)

        net_config = openstack_tests.get_priv_net_config(
            project_name=self.os_creds.project_name,
            net_name=guid + '-pub-net', subnet_name=guid + '-pub-subnet',
            router_name=guid + '-pub-router', external_net=self.ext_net_name,
            netconf_override=self.netconf_override)

        self.volume_settings1 = VolumeConfig(
            name=self.__class__.__name__ + '-' + str(guid) + '-1')
        self.volume_settings2 = VolumeConfig(
            name=self.__class__.__name__ + '-' + str(guid) + '-2')

        # Initialize for tearDown()
        self.image_creator = None
        self.flavor_creator = None

        self.network_creator = None
        self.inst_creator = None
        self.volume_creator1 = None
        self.volume_creator2 = None

        try:
            # Create Image
            self.image_creator = OpenStackImage(self.os_creds,
                                                os_image_settings)
            self.image_creator.create()

            # Create Flavor
            self.flavor_creator = OpenStackFlavor(
                self.admin_os_creds,
                FlavorConfig(name=guid + '-flavor-name', ram=256, disk=1,
                             vcpus=2, metadata=self.flavor_metadata))
            self.flavor_creator.create()

            # Create Network
            self.network_creator = OpenStackNetwork(
                self.os_creds, net_config.network_settings)
            self.network_creator.create()

            self.port_settings = PortConfig(
                name=guid + '-port',
                network_name=net_config.network_settings.name)

            self.volume_creator1 = OpenStackVolume(
                self.os_creds, self.volume_settings1)
            self.volume_creator1.create(block=True)

            self.volume_creator2 = OpenStackVolume(
                self.os_creds, self.volume_settings2)
            self.volume_creator2.create(block=True)

        except Exception as e:
            self.tearDown()
            raise e

    def tearDown(self):
        """
        Cleans the created object
        """
        if self.inst_creator:
            try:
                self.inst_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning VM instance with message '
                    '- %s', e)

        if self.flavor_creator:
            try:
                self.flavor_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning flavor with message - %s',
                    e)

        if self.network_creator:
            try:
                self.network_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning network with message - %s',
                    e)

        if self.volume_creator2:
            try:
                self.volume_creator2.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning volume with message - %s',
                    e)

        if self.volume_creator1:
            try:
                self.volume_creator1.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning volume with message - %s',
                    e)

        if self.image_creator and not self.image_creator.image_settings.exists:
            try:
                self.image_creator.clean()
            except Exception as e:
                logger.error(
                    'Unexpected exception cleaning image with message - %s', e)

        super(self.__class__, self).__clean__()

    def test_create_instance_with_one_volume(self):
        """
        Tests the creation of an OpenStack instance with a single volume.
        """
        instance_settings = VmInstanceConfig(
            name=self.vm_inst_name,
            flavor=self.flavor_creator.flavor_settings.name,
            port_settings=[self.port_settings],
            volume_names=[self.volume_settings1.name])

        self.inst_creator = OpenStackVmInstance(
            self.os_creds, instance_settings,
            self.image_creator.image_settings)

        vm_inst = self.inst_creator.create(block=True)
        self.assertIsNotNone(nova_utils.get_server(
            self.nova, self.neutron, self.keystone,
            vm_inst_settings=instance_settings))

        self.assertIsNotNone(vm_inst)
        self.assertEqual(1, len(vm_inst.volume_ids))
        self.assertEqual(self.volume_creator1.get_volume().id,
                         vm_inst.volume_ids[0]['id'])

    def test_create_instance_with_two_volumes(self):
        """
        Tests the creation of an OpenStack instance with a single volume.
        """
        instance_settings = VmInstanceConfig(
            name=self.vm_inst_name,
            flavor=self.flavor_creator.flavor_settings.name,
            port_settings=[self.port_settings],
            volume_names=[self.volume_settings1.name,
                          self.volume_settings2.name])

        self.inst_creator = OpenStackVmInstance(
            self.os_creds, instance_settings,
            self.image_creator.image_settings)

        vm_inst = self.inst_creator.create(block=True)
        self.assertIsNotNone(nova_utils.get_server(
            self.nova, self.neutron, self.keystone,
            vm_inst_settings=instance_settings))

        self.assertIsNotNone(vm_inst)
        self.assertEqual(2, len(vm_inst.volume_ids))
        self.assertEqual(self.volume_creator1.get_volume().id,
                         vm_inst.volume_ids[0]['id'])
        self.assertEqual(self.volume_creator2.get_volume().id,
                         vm_inst.volume_ids[1]['id'])


def check_dhcp_lease(inst_creator, ip, timeout=160):
    """
    Returns true if the expected DHCP lease has been acquired
    :param inst_creator: the SNAPS OpenStackVmInstance object
    :param ip: the IP address to look for
    :param timeout: how long to query for IP address
    :return:
    """
    found = False
    start_time = time.time()

    logger.info("Looking for IP %s in the console log" % ip)
    full_log = ''
    while timeout > time.time() - start_time:
        output = inst_creator.get_console_output()
        full_log = full_log + output
        if re.search(ip, output):
            logger.info('DHCP lease obtained logged in console')
            found = True
            break

    if not found:
        logger.error('Full console output -\n' + full_log)
    else:
        logger.debug('Full console output -\n' + full_log)

    return found


def _get_ping_userdata(test_ip):
    """
    Returns the post VM creation script to be added into the VM's userdata
    :param test_ip: the IP value to substitute into the script
    :return: the bash script contents
    """
    if test_ip:
        return ("#!/bin/sh\n\n"
                "while true; do\n"
                " ping -c 1 %s 2>&1 >/dev/null\n"
                " RES=$?\n"
                " if [ \"Z$RES\" = \"Z0\" ] ; then\n"
                "  echo 'vPing OK'\n"
                "  break\n"
                " else\n"
                "  echo 'vPing KO'\n"
                " fi\n"
                " sleep 1\n"
                "done\n" % test_ip)
    return None


def check_ping(vm_creator, timeout=160):
    """
    Check for VM for ping result
    """
    tries = 0

    while tries < timeout:
        time.sleep(1)
        p_console = vm_creator.get_console_output()
        if "vPing OK" in p_console:
            return True
        elif "failed to read iid from metadata" in p_console or tries > 5:
            return False
        tries += 1

    return False
