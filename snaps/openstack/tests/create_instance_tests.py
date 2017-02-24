# Copyright (c) 2016 Cable Television Laboratories, Inc. ("CableLabs")
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
import os
import time
import unittest
import uuid

from snaps.openstack.create_instance import VmInstanceSettings, OpenStackVmInstance, FloatingIpSettings
from snaps.openstack.create_flavor import OpenStackFlavor, FlavorSettings
from snaps.openstack.create_keypairs import OpenStackKeypair, KeypairSettings
from snaps.openstack.create_network import OpenStackNetwork, PortSettings
from snaps.openstack.create_router import OpenStackRouter
from snaps.openstack.create_image import OpenStackImage
from snaps.openstack.create_security_group import SecurityGroupSettings, OpenStackSecurityGroup
from snaps.openstack.tests import openstack_tests, validation_utils
from snaps.openstack.utils import nova_utils
from snaps.openstack.tests.os_source_file_test import OSComponentTestCase, OSIntegrationTestCase

__author__ = 'spisarski'

VM_BOOT_TIMEOUT = 600

logger = logging.getLogger('create_instance_tests')


class VmInstanceSettingsUnitTests(unittest.TestCase):
    """
    Tests the construction of the VmInstanceSettings class
    """

    def test_no_params(self):
        with self.assertRaises(Exception):
            VmInstanceSettings()

    def test_empty_config(self):
        with self.assertRaises(Exception):
            VmInstanceSettings(config=dict())

    def test_name_only(self):
        with self.assertRaises(Exception):
            VmInstanceSettings(name='foo')

    def test_config_with_name_only(self):
        with self.assertRaises(Exception):
            VmInstanceSettings(config={'name': 'foo'})

    def test_name_flavor_only(self):
        settings = VmInstanceSettings(name='foo', flavor='bar')
        self.assertEquals('foo', settings.name)
        self.assertEquals('bar', settings.flavor)
        self.assertEquals(0, len(settings.port_settings))
        self.assertEquals(0, len(settings.security_group_names))
        self.assertEquals(0, len(settings.floating_ip_settings))
        self.assertIsNone(settings.sudo_user)
        self.assertEquals(900, settings.vm_boot_timeout)
        self.assertEquals(300, settings.vm_delete_timeout)
        self.assertEquals(180, settings.ssh_connect_timeout)
        self.assertIsNone(settings.availability_zone)

    def test_config_with_name_flavor_only(self):
        settings = VmInstanceSettings(config={'name': 'foo', 'flavor': 'bar'})
        self.assertEquals('foo', settings.name)
        self.assertEquals('bar', settings.flavor)
        self.assertEquals(0, len(settings.port_settings))
        self.assertEquals(0, len(settings.security_group_names))
        self.assertEquals(0, len(settings.floating_ip_settings))
        self.assertIsNone(settings.sudo_user)
        self.assertEquals(900, settings.vm_boot_timeout)
        self.assertEquals(300, settings.vm_delete_timeout)
        self.assertEquals(180, settings.ssh_connect_timeout)
        self.assertIsNone(settings.availability_zone)

    def test_all(self):
        port_settings = PortSettings(name='foo-port', network_name='bar-net')
        fip_settings = FloatingIpSettings(name='foo-fip', port_name='bar-port', router_name='foo-bar-router')

        settings = VmInstanceSettings(name='foo', flavor='bar', port_settings=[port_settings],
                                      security_group_names=['sec_grp_1'], floating_ip_settings=[fip_settings],
                                      sudo_user='joe', vm_boot_timeout=999, vm_delete_timeout=333,
                                      ssh_connect_timeout=111, availability_zone='server name')
        self.assertEquals('foo', settings.name)
        self.assertEquals('bar', settings.flavor)
        self.assertEquals(1, len(settings.port_settings))
        self.assertEquals('foo-port', settings.port_settings[0].name)
        self.assertEquals('bar-net', settings.port_settings[0].network_name)
        self.assertEquals(1, len(settings.security_group_names))
        self.assertEquals('sec_grp_1', settings.security_group_names[0])
        self.assertEquals(1, len(settings.floating_ip_settings))
        self.assertEquals('foo-fip', settings.floating_ip_settings[0].name)
        self.assertEquals('bar-port', settings.floating_ip_settings[0].port_name)
        self.assertEquals('foo-bar-router', settings.floating_ip_settings[0].router_name)
        self.assertEquals('joe', settings.sudo_user)
        self.assertEquals(999, settings.vm_boot_timeout)
        self.assertEquals(333, settings.vm_delete_timeout)
        self.assertEquals(111, settings.ssh_connect_timeout)
        self.assertEquals('server name', settings.availability_zone)

    def test_config_all(self):
        port_settings = PortSettings(name='foo-port', network_name='bar-net')
        fip_settings = FloatingIpSettings(name='foo-fip', port_name='bar-port', router_name='foo-bar-router')

        settings = VmInstanceSettings(config={'name': 'foo', 'flavor': 'bar', 'ports': [port_settings],
                                              'security_group_names': ['sec_grp_1'],
                                              'floating_ips': [fip_settings], 'sudo_user': 'joe',
                                              'vm_boot_timeout': 999, 'vm_delete_timeout': 333,
                                              'ssh_connect_timeout': 111, 'availability_zone': 'server name'})
        self.assertEquals('foo', settings.name)
        self.assertEquals('bar', settings.flavor)
        self.assertEquals(1, len(settings.port_settings))
        self.assertEquals('foo-port', settings.port_settings[0].name)
        self.assertEquals('bar-net', settings.port_settings[0].network_name)
        self.assertEquals(1, len(settings.security_group_names))
        self.assertEquals(1, len(settings.floating_ip_settings))
        self.assertEquals('foo-fip', settings.floating_ip_settings[0].name)
        self.assertEquals('bar-port', settings.floating_ip_settings[0].port_name)
        self.assertEquals('foo-bar-router', settings.floating_ip_settings[0].router_name)
        self.assertEquals('joe', settings.sudo_user)
        self.assertEquals(999, settings.vm_boot_timeout)
        self.assertEquals(333, settings.vm_delete_timeout)
        self.assertEquals(111, settings.ssh_connect_timeout)
        self.assertEquals('server name', settings.availability_zone)


class FloatingIpSettingsUnitTests(unittest.TestCase):
    """
    Tests the construction of the FloatingIpSettings class
    """

    def test_no_params(self):
        with self.assertRaises(Exception):
            FloatingIpSettings()

    def test_empty_config(self):
        with self.assertRaises(Exception):
            FloatingIpSettings(config=dict())

    def test_name_only(self):
        with self.assertRaises(Exception):
            FloatingIpSettings(name='foo')

    def test_config_with_name_only(self):
        with self.assertRaises(Exception):
            FloatingIpSettings(config={'name': 'foo'})

    def test_name_port_only(self):
        with self.assertRaises(Exception):
            FloatingIpSettings(name='foo', port_name='bar')

    def test_config_with_name_port_only(self):
        with self.assertRaises(Exception):
            FloatingIpSettings(config={'name': 'foo', 'port_name': 'bar'})

    def test_name_router_only(self):
        with self.assertRaises(Exception):
            FloatingIpSettings(name='foo', router_name='bar')

    def test_config_with_name_router_only(self):
        with self.assertRaises(Exception):
            FloatingIpSettings(config={'name': 'foo', 'router_name': 'bar'})

    def test_name_port_router_only(self):
        settings = FloatingIpSettings(name='foo', port_name='foo-port', router_name='bar-router')
        self.assertEquals('foo', settings.name)
        self.assertEquals('foo-port', settings.port_name)
        self.assertEquals('bar-router', settings.router_name)
        self.assertIsNone(settings.subnet_name)
        self.assertTrue(settings.provisioning)

    def test_config_with_name_port_router_only(self):
        settings = FloatingIpSettings(config={'name': 'foo', 'port_name': 'foo-port', 'router_name': 'bar-router'})
        self.assertEquals('foo', settings.name)
        self.assertEquals('foo-port', settings.port_name)
        self.assertEquals('bar-router', settings.router_name)
        self.assertIsNone(settings.subnet_name)
        self.assertTrue(settings.provisioning)

    def test_all(self):
        settings = FloatingIpSettings(name='foo', port_name='foo-port', router_name='bar-router',
                                      subnet_name='bar-subnet', provisioning=False)
        self.assertEquals('foo', settings.name)
        self.assertEquals('foo-port', settings.port_name)
        self.assertEquals('bar-router', settings.router_name)
        self.assertEquals('bar-subnet', settings.subnet_name)
        self.assertFalse(settings.provisioning)

    def test_config_all(self):
        settings = FloatingIpSettings(config={'name': 'foo', 'port_name': 'foo-port', 'router_name': 'bar-router',
                                              'subnet_name': 'bar-subnet', 'provisioning': False})
        self.assertEquals('foo', settings.name)
        self.assertEquals('foo-port', settings.port_name)
        self.assertEquals('bar-router', settings.router_name)
        self.assertEquals('bar-subnet', settings.subnet_name)
        self.assertFalse(settings.provisioning)


class SimpleHealthCheck(OSIntegrationTestCase):
    """
    Test for the CreateInstance class with a single NIC/Port with Floating IPs
    """

    def setUp(self):
        """
        Instantiates the CreateImage object that is responsible for downloading and creating an OS image file
        within OpenStack
        """
        super(self.__class__, self).__start__()

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
        self.flavor_creator = None
        self.inst_creator = None

        self.priv_net_config = openstack_tests.get_priv_net_config(
            net_name=guid + '-priv-net', subnet_name=guid + '-priv-subnet')
        self.port_settings = PortSettings(
            name=self.port_1_name, network_name=self.priv_net_config.network_settings.name)

        self.os_image_settings = openstack_tests.cirros_url_image(name=guid + '-image')

        try:
            # Create Image
            self.image_creator = OpenStackImage(self.os_creds, self.os_image_settings)
            self.image_creator.create()

            # Create Network
            self.network_creator = OpenStackNetwork(self.os_creds, self.priv_net_config.network_settings)
            self.network_creator.create()

            # Create Flavor
            self.flavor_creator = OpenStackFlavor(
                self.admin_os_creds,
                FlavorSettings(name=guid + '-flavor-name', ram=1024, disk=10, vcpus=1))
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
                logger.error('Unexpected exception cleaning VM instance with message - ' + e.message)

        if os.path.isfile(self.keypair_pub_filepath):
            os.remove(self.keypair_pub_filepath)

        if os.path.isfile(self.keypair_priv_filepath):
            os.remove(self.keypair_priv_filepath)

        if self.flavor_creator:
            try:
                self.flavor_creator.clean()
            except Exception as e:
                logger.error('Unexpected exception cleaning flavor with message - ' + e.message)

        if self.network_creator:
            try:
                self.network_creator.clean()
            except Exception as e:
                logger.error('Unexpected exception cleaning network with message - ' + e.message)

        if self.image_creator:
            try:
                self.image_creator.clean()
            except Exception as e:
                logger.error('Unexpected exception cleaning image with message - ' + e.message)

        super(self.__class__, self).__clean__()

    def test_check_vm_ip_dhcp(self):
        """
        Tests the creation of an OpenStack instance with a single port and ensures that it's assigned IP address is
        the actual.
        """
        instance_settings = VmInstanceSettings(
            name=self.vm_inst_name, flavor=self.flavor_creator.flavor_settings.name, port_settings=[self.port_settings])

        self.inst_creator = OpenStackVmInstance(self.os_creds, instance_settings, self.image_creator.image_settings)
        vm = self.inst_creator.create()

        ip = self.inst_creator.get_port_ip(self.port_settings.name)
        self.assertIsNotNone(ip)

        self.assertTrue(self.inst_creator.vm_active(block=True))

        found = False
        timeout = 100
        start_time = time.time()
        match_value = 'Lease of ' + ip + ' obtained,'

        while timeout > time.time() - start_time:
            output = vm.get_console_output()
            if match_value in output:
                found = True
                break
        self.assertTrue(found)


class CreateInstanceSimpleTests(OSIntegrationTestCase):
    """
    Simple instance creation tests without any other objects
    """
    def setUp(self):
        """
        Instantiates the CreateImage object that is responsible for downloading and creating an OS image file
        within OpenStack
        """
        super(self.__class__, self).__start__()

        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.vm_inst_name = guid + '-inst'
        self.nova = nova_utils.nova_client(self.os_creds)
        self.os_image_settings = openstack_tests.cirros_url_image(name=guid + '-image')

        # Initialize for tearDown()
        self.image_creator = None
        self.flavor_creator = None
        self.inst_creator = None

        try:
            # Create Image
            self.image_creator = OpenStackImage(self.os_creds, self.os_image_settings)
            self.image_creator.create()
            # Create Flavor
            self.flavor_creator = OpenStackFlavor(
                self.admin_os_creds,
                FlavorSettings(name=guid + '-flavor-name', ram=2048, disk=10, vcpus=2))
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
                logger.error('Unexpected exception cleaning VM instance with message - ' + e.message)

        if self.flavor_creator:
            try:
                self.flavor_creator.clean()
            except Exception as e:
                logger.error('Unexpected exception cleaning flavor with message - ' + e.message)

        if self.image_creator:
            try:
                self.image_creator.clean()
            except Exception as e:
                logger.error('Unexpected exception cleaning image with message - ' + e.message)

        super(self.__class__, self).__clean__()

    def test_create_delete_instance(self):
        """
        Tests the creation of an OpenStack instance with a single port with a static IP without a Floating IP.
        """
        instance_settings = VmInstanceSettings(name=self.vm_inst_name, flavor=self.flavor_creator.flavor_settings.name)

        self.inst_creator = OpenStackVmInstance(
            self.os_creds, instance_settings, self.image_creator.image_settings)

        vm_inst = self.inst_creator.create()
        self.assertEquals(1, len(nova_utils.get_servers_by_name(self.nova, instance_settings.name)))

        # Delete instance
        nova_utils.delete_vm_instance(self.nova, vm_inst)

        self.assertTrue(self.inst_creator.vm_deleted(block=True))
        self.assertEquals(0, len(nova_utils.get_servers_by_name(self.nova, instance_settings.name)))

        # Exception should not be thrown
        self.inst_creator.clean()


class CreateInstanceSingleNetworkTests(OSIntegrationTestCase):
    """
    Test for the CreateInstance class with a single NIC/Port with Floating IPs
    """

    def setUp(self):
        """
        Instantiates the CreateImage object that is responsible for downloading and creating an OS image file
        within OpenStack
        """
        super(self.__class__, self).__start__()

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
        self.inst_creators = list()

        self.pub_net_config = openstack_tests.get_pub_net_config(
            net_name=guid + '-pub-net', subnet_name=guid + '-pub-subnet',
            router_name=guid + '-pub-router', external_net=self.ext_net_name)
        self.os_image_settings = openstack_tests.cirros_url_image(name=guid + '-image')

        try:
            # Create Image
            self.image_creator = OpenStackImage(self.os_creds, self.os_image_settings)
            self.image_creator.create()

            # Create Network
            self.network_creator = OpenStackNetwork(self.os_creds, self.pub_net_config.network_settings)
            self.network_creator.create()

            # Create Router
            self.router_creator = OpenStackRouter(self.os_creds, self.pub_net_config.router_settings)
            self.router_creator.create()

            # Create Flavor
            self.flavor_creator = OpenStackFlavor(
                self.admin_os_creds,
                FlavorSettings(name=guid + '-flavor-name', ram=2048, disk=10, vcpus=2))
            self.flavor_creator.create()

            self.keypair_creator = OpenStackKeypair(
                self.os_creds, KeypairSettings(
                    name=self.keypair_name, public_filepath=self.keypair_pub_filepath,
                    private_filepath=self.keypair_priv_filepath))
            self.keypair_creator.create()
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
                logger.error('Unexpected exception cleaning VM instance with message - ' + e.message)

        if self.keypair_creator:
            try:
                self.keypair_creator.clean()
            except Exception as e:
                logger.error('Unexpected exception cleaning keypair with message - ' + e.message)

        if os.path.isfile(self.keypair_pub_filepath):
            os.remove(self.keypair_pub_filepath)

        if os.path.isfile(self.keypair_priv_filepath):
            os.remove(self.keypair_priv_filepath)

        if self.flavor_creator:
            try:
                self.flavor_creator.clean()
            except Exception as e:
                logger.error('Unexpected exception cleaning flavor with message - ' + e.message)

        if self.router_creator:
            try:
                self.router_creator.clean()
            except Exception as e:
                logger.error('Unexpected exception cleaning router with message - ' + e.message)

        if self.network_creator:
            try:
                self.network_creator.clean()
            except Exception as e:
                logger.error('Unexpected exception cleaning network with message - ' + e.message)

        if self.image_creator:
            try:
                self.image_creator.clean()
            except Exception as e:
                logger.error('Unexpected exception cleaning image with message - ' + e.message)

        super(self.__class__, self).__clean__()

    def test_single_port_static(self):
        """
        Tests the creation of an OpenStack instance with a single port with a static IP without a Floating IP.
        """
        ip_1 = '10.55.1.100'

        port_settings = PortSettings(
            name=self.port_1_name, network_name=self.pub_net_config.network_settings.name,
            ip_addrs=[{'subnet_name': self.pub_net_config.network_settings.subnet_settings[0].name, 'ip': ip_1}])

        instance_settings = VmInstanceSettings(
            name=self.vm_inst_name, flavor=self.flavor_creator.flavor_settings.name, port_settings=[port_settings],
            floating_ip_settings=[FloatingIpSettings(
                name=self.floating_ip_name, port_name=self.port_1_name,
                router_name=self.pub_net_config.router_settings.name)])

        inst_creator = OpenStackVmInstance(
            self.os_creds, instance_settings, self.image_creator.image_settings,
            keypair_settings=self.keypair_creator.keypair_settings)
        self.inst_creators.append(inst_creator)
        vm_inst = inst_creator.create()

        self.assertEquals(ip_1, inst_creator.get_port_ip(self.port_1_name))
        self.assertTrue(inst_creator.vm_active(block=True))
        self.assertEquals(vm_inst, inst_creator.get_vm_inst())

    def test_ssh_client_fip_before_active(self):
        """
        Tests the ability to access a VM via SSH and a floating IP when it has been assigned prior to being active.
        """
        port_settings = PortSettings(
            name=self.port_1_name, network_name=self.pub_net_config.network_settings.name)

        instance_settings = VmInstanceSettings(
            name=self.vm_inst_name, flavor=self.flavor_creator.flavor_settings.name, port_settings=[port_settings],
            floating_ip_settings=[FloatingIpSettings(
                name=self.floating_ip_name, port_name=self.port_1_name,
                router_name=self.pub_net_config.router_settings.name)])

        inst_creator = OpenStackVmInstance(
            self.os_creds, instance_settings, self.image_creator.image_settings,
            keypair_settings=self.keypair_creator.keypair_settings)
        self.inst_creators.append(inst_creator)
        vm_inst = inst_creator.create()
        self.assertIsNotNone(vm_inst)

        self.assertTrue(inst_creator.vm_active(block=True))
        self.assertEquals(vm_inst, inst_creator.get_vm_inst())

        validate_ssh_client(inst_creator)

    def test_ssh_client_fip_after_active(self):
        """
        Tests the ability to access a VM via SSH and a floating IP when it has been assigned prior to being active.
        """
        port_settings = PortSettings(
            name=self.port_1_name, network_name=self.pub_net_config.network_settings.name)

        instance_settings = VmInstanceSettings(
            name=self.vm_inst_name, flavor=self.flavor_creator.flavor_settings.name, port_settings=[port_settings],
            floating_ip_settings=[FloatingIpSettings(
                name=self.floating_ip_name, port_name=self.port_1_name,
                router_name=self.pub_net_config.router_settings.name)])

        inst_creator = OpenStackVmInstance(
            self.os_creds, instance_settings, self.image_creator.image_settings,
            keypair_settings=self.keypair_creator.keypair_settings)
        self.inst_creators.append(inst_creator)

        # block=True will force the create() method to block until the
        vm_inst = inst_creator.create(block=True)
        self.assertIsNotNone(vm_inst)

        self.assertTrue(inst_creator.vm_active(block=True))
        self.assertEquals(vm_inst, inst_creator.get_vm_inst())

        validate_ssh_client(inst_creator)

    # TODO - Determine how allowed_address_pairs is supposed to operate before continuing this test
    # see http://docs.openstack.org/developer/dragonflow/specs/allowed_address_pairs.html for a functional description
    # def test_allowed_address_port_access(self):
    #     """
    #     Tests to ensure that setting allowed_address_pairs on a port functions as designed
    #     """
    #     port_settings_1 = PortSettings(
    #         name=self.port_1_name + '-1', network_name=self.pub_net_config.network_settings.name)
    #
    #     instance_settings_1 = VmInstanceSettings(
    #         name=self.vm_inst_name + '-1', flavor=self.flavor_creator.flavor_settings.name, port_settings=[port_settings_1],
    #         floating_ip_settings=[FloatingIpSettings(
    #             name=self.floating_ip_name + '-1', port_name=port_settings_1.name,
    #             router_name=self.pub_net_config.router_settings.name)])
    #
    #     inst_creator_1 = OpenStackVmInstance(
    #         self.os_creds, instance_settings_1, self.image_creator.image_settings,
    #         keypair_settings=self.keypair_creator.keypair_settings)
    #     self.inst_creators.append(inst_creator_1)
    #
    #     # block=True will force the create() method to block until the
    #     vm_inst_1 = inst_creator_1.create(block=True)
    #     self.assertIsNotNone(vm_inst_1)
    #
    #     port_settings_1 = PortSettings(
    #         name=self.port_1_name + '-1', network_name=self.pub_net_config.network_settings.name)
    #
    #     instance_settings_1 = VmInstanceSettings(
    #         name=self.vm_inst_name + '-1', flavor=self.flavor_creator.flavor_settings.name, port_settings=[port_settings_1],
    #         floating_ip_settings=[FloatingIpSettings(
    #             name=self.floating_ip_name + '-1', port_name=port_settings_1.name,
    #             router_name=self.pub_net_config.router_settings.name)])
    #
    #     inst_creator_1 = OpenStackVmInstance(
    #         self.os_creds, instance_settings_1, self.image_creator.image_settings,
    #         keypair_settings=self.keypair_creator.keypair_settings)
    #     self.inst_creators.append(inst_creator_1)
    #     inst_creator_1.create(block=True)
    #
    #     ip = inst_creator_1.get_port_ip(port_settings_1.name,
    #                                     subnet_name=self.pub_net_config.network_settings.subnet_settings[0].name)
    #     self.assertIsNotNone(ip)
    #     mac_addr = inst_creator_1.get_port_mac(port_settings_1.name)
    #     self.assertIsNotNone(mac_addr)
    #
    #     allowed_address_pairs = [{'ip_address': ip, 'mac_address': mac_addr}]
    #
    #     # Create VM that can be accessed by vm_inst_1
    #     port_settings_2 = PortSettings(
    #         name=self.port_1_name + '-2', network_name=self.pub_net_config.network_settings.name,
    #         allowed_address_pairs=allowed_address_pairs)
    #
    #     instance_settings_2 = VmInstanceSettings(
    #         name=self.vm_inst_name + '-2', flavor=self.flavor_creator.flavor_settings.name,
    #         port_settings=[port_settings_2])
    #
    #     inst_creator_2 = OpenStackVmInstance(
    #         self.os_creds, instance_settings_2, self.image_creator.image_settings)
    #     self.inst_creators.append(inst_creator_2)
    #     inst_creator_2.create(block=True)
    #
    #     # Create VM that cannot be accessed by vm_inst_1
    #     ip = '10.55.0.101'
    #     mac_addr = '0a:1b:2c:3d:4e:5f'
    #     invalid_address_pairs = [{'ip_address': ip, 'mac_address': mac_addr}]
    #
    #     port_settings_3 = PortSettings(
    #         name=self.port_1_name + '-3', network_name=self.pub_net_config.network_settings.name,
    #         allowed_address_pairs=invalid_address_pairs)
    #
    #     instance_settings_3 = VmInstanceSettings(
    #         name=self.vm_inst_name + '-3', flavor=self.flavor_creator.flavor_settings.name,
    #         port_settings=[port_settings_3])
    #
    #     inst_creator_3 = OpenStackVmInstance(
    #         self.os_creds, instance_settings_3, self.image_creator.image_settings)
    #     self.inst_creators.append(inst_creator_3)
    #     inst_creator_3.create(block=True)
    #
    #     print 'foo'
    # I expected that this feature would block/allow traffic from specific endpoints (VMs). In this case, I would expect
    # inst_1 to be able to access inst_2 but not inst_3; however, they all can access each other.
    # TODO - Add validation


class CreateInstancePortManipulationTests(OSIntegrationTestCase):
    """
    Test for the CreateInstance class with a single NIC/Port where mac and IP values are manually set
    """

    def setUp(self):
        """
        Instantiates the CreateImage object that is responsible for downloading and creating an OS image file
        within OpenStack
        """
        super(self.__class__, self).__start__()

        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.vm_inst_name = guid + '-inst'
        self.port_1_name = guid + 'port-1'
        self.port_2_name = guid + 'port-2'
        self.floating_ip_name = guid + 'fip1'

        # Initialize for tearDown()
        self.image_creator = None
        self.network_creator = None
        self.flavor_creator = None
        self.inst_creator = None

        self.net_config = openstack_tests.get_priv_net_config(
            net_name=guid + '-pub-net', subnet_name=guid + '-pub-subnet',
            router_name=guid + '-pub-router', external_net=self.ext_net_name)
        self.os_image_settings = openstack_tests.cirros_url_image(name=guid + '-image')

        try:
            # Create Image
            self.image_creator = OpenStackImage(self.os_creds, self.os_image_settings)
            self.image_creator.create()

            # Create Network
            self.network_creator = OpenStackNetwork(self.os_creds, self.net_config.network_settings)
            self.network_creator.create()

            # Create Flavor
            self.flavor_creator = OpenStackFlavor(
                self.admin_os_creds,
                FlavorSettings(name=guid + '-flavor-name', ram=2048, disk=10, vcpus=2))
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
                logger.error('Unexpected exception cleaning VM instance with message - ' + e.message)

        if self.flavor_creator:
            try:
                self.flavor_creator.clean()
            except Exception as e:
                logger.error('Unexpected exception cleaning flavor with message - ' + e.message)

        if self.network_creator:
            try:
                self.network_creator.clean()
            except Exception as e:
                logger.error('Unexpected exception cleaning network with message - ' + e.message)

        if self.image_creator:
            try:
                self.image_creator.clean()
            except Exception as e:
                logger.error('Unexpected exception cleaning image with message - ' + e.message)

        super(self.__class__, self).__clean__()

    def test_set_custom_valid_ip_one_subnet(self):
        """
        Tests the creation of an OpenStack instance with a single port with a static IP on a network with one subnet.
        """
        ip = '10.55.0.101'
        port_settings = PortSettings(
            name=self.port_1_name, network_name=self.net_config.network_settings.name,
            ip_addrs=[{'subnet_name': self.net_config.network_settings.subnet_settings[0].name, 'ip': ip}])

        instance_settings = VmInstanceSettings(
            name=self.vm_inst_name, flavor=self.flavor_creator.flavor_settings.name, port_settings=[port_settings])

        self.inst_creator = OpenStackVmInstance(self.os_creds, instance_settings, self.image_creator.image_settings)
        self.inst_creator.create()

        self.assertEquals(ip, self.inst_creator.get_port_ip(
            self.port_1_name, subnet_name=self.net_config.network_settings.subnet_settings[0].name))

    def test_set_custom_invalid_ip_one_subnet(self):
        """
        Tests the creation of an OpenStack instance with a single port with a static IP on a network with one subnet.
        """
        ip = '10.66.0.101'
        port_settings = PortSettings(
            name=self.port_1_name, network_name=self.net_config.network_settings.name,
            ip_addrs=[{'subnet_name': self.net_config.network_settings.subnet_settings[0].name, 'ip': ip}])

        instance_settings = VmInstanceSettings(
            name=self.vm_inst_name, flavor=self.flavor_creator.flavor_settings.name, port_settings=[port_settings])

        self.inst_creator = OpenStackVmInstance(self.os_creds, instance_settings, self.image_creator.image_settings)

        with self.assertRaises(Exception):
            self.inst_creator.create()

    def test_set_custom_valid_mac(self):
        """
        Tests the creation of an OpenStack instance with a single port where the MAC address is assigned.
        """
        mac_addr = '0a:1b:2c:3d:4e:5f'
        port_settings = PortSettings(
            name=self.port_1_name, network_name=self.net_config.network_settings.name, mac_address=mac_addr)

        instance_settings = VmInstanceSettings(
            name=self.vm_inst_name, flavor=self.flavor_creator.flavor_settings.name, port_settings=[port_settings])

        self.inst_creator = OpenStackVmInstance(self.os_creds, instance_settings, self.image_creator.image_settings)
        self.inst_creator.create()

        self.assertEquals(mac_addr, self.inst_creator.get_port_mac(self.port_1_name))

    def test_set_custom_invalid_mac(self):
        """
        Tests the creation of an OpenStack instance with a single port where an invalid MAC address value is being
        assigned. This should raise an Exception
        """
        port_settings = PortSettings(
            name=self.port_1_name, network_name=self.net_config.network_settings.name, mac_address='foo')

        instance_settings = VmInstanceSettings(
            name=self.vm_inst_name, flavor=self.flavor_creator.flavor_settings.name, port_settings=[port_settings])

        self.inst_creator = OpenStackVmInstance(
            self.os_creds, instance_settings, self.image_creator.image_settings)

        with self.assertRaises(Exception):
            self.inst_creator.create()

    def test_set_custom_mac_and_ip(self):
        """
        Tests the creation of an OpenStack instance with a single port where the IP and MAC address is assigned.
        """
        ip = '10.55.0.101'
        mac_addr = '0a:1b:2c:3d:4e:5f'
        port_settings = PortSettings(
            name=self.port_1_name, network_name=self.net_config.network_settings.name, mac_address=mac_addr,
            ip_addrs=[{'subnet_name': self.net_config.network_settings.subnet_settings[0].name, 'ip': ip}])

        instance_settings = VmInstanceSettings(
            name=self.vm_inst_name, flavor=self.flavor_creator.flavor_settings.name, port_settings=[port_settings])

        self.inst_creator = OpenStackVmInstance(self.os_creds, instance_settings, self.image_creator.image_settings)
        self.inst_creator.create()

        self.assertEquals(ip, self.inst_creator.get_port_ip(
            self.port_1_name, subnet_name=self.net_config.network_settings.subnet_settings[0].name))
        self.assertEquals(mac_addr, self.inst_creator.get_port_mac(self.port_1_name))

    def test_set_allowed_address_pairs(self):
        """
        Tests the creation of an OpenStack instance with a single port where max_allowed_address_pair is set.
        """
        ip = '10.55.0.101'
        mac_addr = '0a:1b:2c:3d:4e:5f'
        pair = {'ip_address': ip, 'mac_address': mac_addr}
        port_settings = PortSettings(
            name=self.port_1_name, network_name=self.net_config.network_settings.name, allowed_address_pairs=[pair])

        instance_settings = VmInstanceSettings(
            name=self.vm_inst_name, flavor=self.flavor_creator.flavor_settings.name, port_settings=[port_settings])

        self.inst_creator = OpenStackVmInstance(self.os_creds, instance_settings, self.image_creator.image_settings)
        self.inst_creator.create()

        port = self.inst_creator.get_port_by_name(port_settings.name)
        self.assertIsNotNone(port)
        self.assertIsNotNone(port['port'].get('allowed_address_pairs'))
        self.assertEquals(1, len(port['port']['allowed_address_pairs']))
        validation_utils.objects_equivalent(pair, port['port']['allowed_address_pairs'][0])

    def test_set_allowed_address_pairs_bad_mac(self):
        """
        Tests the creation of an OpenStack instance with a single port where max_allowed_address_pair is set with an
        invalid MAC address.
        """
        ip = '10.55.0.101'
        mac_addr = 'foo'
        pair = {'ip_address': ip, 'mac_address': mac_addr}
        pairs = set()
        pairs.add((ip, mac_addr))
        port_settings = PortSettings(
            name=self.port_1_name, network_name=self.net_config.network_settings.name, allowed_address_pairs=[pair])

        instance_settings = VmInstanceSettings(
            name=self.vm_inst_name, flavor=self.flavor_creator.flavor_settings.name, port_settings=[port_settings])

        self.inst_creator = OpenStackVmInstance(self.os_creds, instance_settings, self.image_creator.image_settings)
        with self.assertRaises(Exception):
            self.inst_creator.create()

    def test_set_allowed_address_pairs_bad_ip(self):
        """
        Tests the creation of an OpenStack instance with a single port where max_allowed_address_pair is set with an
        invalid MAC address.
        """
        ip = 'foo'
        mac_addr = '0a:1b:2c:3d:4e:5f'
        pair = {'ip_address': ip, 'mac_address': mac_addr}
        pairs = set()
        pairs.add((ip, mac_addr))
        port_settings = PortSettings(
            name=self.port_1_name, network_name=self.net_config.network_settings.name, allowed_address_pairs=[pair])

        instance_settings = VmInstanceSettings(
            name=self.vm_inst_name, flavor=self.flavor_creator.flavor_settings.name, port_settings=[port_settings])

        self.inst_creator = OpenStackVmInstance(self.os_creds, instance_settings, self.image_creator.image_settings)
        with self.assertRaises(Exception):
            self.inst_creator.create()


class CreateInstanceOnComputeHost(OSComponentTestCase):
    """
    Test for the CreateInstance where one VM is deployed to each compute node
    """

    def setUp(self):
        """
        Instantiates the CreateImage object that is responsible for downloading and creating an OS image file
        within OpenStack
        """
        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.vm_inst_name = guid + '-inst'
        self.port_base_name = guid + 'port'

        # Initialize for tearDown()
        self.image_creator = None
        self.flavor_creator = None
        self.network_creator = None
        self.inst_creators = list()

        self.priv_net_config = openstack_tests.get_priv_net_config(
            net_name=guid + '-priv-net', subnet_name=guid + '-priv-subnet')

        self.os_image_settings = openstack_tests.cirros_url_image(name=guid + '-image')

        try:
            # Create Network
            self.network_creator = OpenStackNetwork(self.os_creds, self.priv_net_config.network_settings)
            self.network_creator.create()

            # Create Flavor
            self.flavor_creator = OpenStackFlavor(
                self.os_creds,
                FlavorSettings(name=guid + '-flavor-name', ram=512, disk=1, vcpus=1))
            self.flavor_creator.create()

            # Create Image
            self.image_creator = OpenStackImage(self.os_creds, self.os_image_settings)
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
                logger.error('Unexpected exception cleaning VM instance with message - ' + e.message)

        if self.flavor_creator:
            try:
                self.flavor_creator.clean()
            except Exception as e:
                logger.error('Unexpected exception cleaning flavor with message - ' + e.message)

        if self.network_creator:
            try:
                self.network_creator.clean()
            except Exception as e:
                logger.error('Unexpected exception cleaning network with message - ' + e.message)

        if self.image_creator:
            try:
                self.image_creator.clean()
            except Exception as e:
                logger.error('Unexpected exception cleaning image with message - ' + e.message)

    def test_deploy_vm_to_each_compute_node(self):
        """
        Tests the creation of OpenStack VM instances to each compute node.
        """
        from snaps.openstack.utils import nova_utils
        nova = nova_utils.nova_client(self.os_creds)
        zones = nova_utils.get_nova_availability_zones(nova)

        # Create Instance on each server/zone
        ctr = 0
        for zone in zones:
            inst_name = self.vm_inst_name + '-' + zone
            ctr += 1
            port_settings = PortSettings(name=self.port_base_name + '-' + str(ctr),
                                         network_name=self.priv_net_config.network_settings.name)

            instance_settings = VmInstanceSettings(
                name=inst_name, flavor=self.flavor_creator.flavor_settings.name, availability_zone=zone,
                port_settings=[port_settings])
            inst_creator = OpenStackVmInstance(
                self.os_creds, instance_settings, self.image_creator.image_settings)
            self.inst_creators.append(inst_creator)
            inst_creator.create()

        # Validate instances to ensure they've been deployed to the correct server
        index = 0
        for zone in zones:
            creator = self.inst_creators[index]
            self.assertTrue(creator.vm_active(block=True))
            vm = creator.get_vm_inst()
            deployed_zone = vm._info['OS-EXT-AZ:availability_zone']
            deployed_host = vm._info['OS-EXT-SRV-ATTR:host']
            self.assertEquals(zone, deployed_zone + ':' + deployed_host)
            index += 1


class CreateInstancePubPrivNetTests(OSIntegrationTestCase):
    """
    Test for the CreateInstance class with two NIC/Ports, eth0 with floating IP and eth1 w/o
    These tests require a Centos image
    """

    def setUp(self):
        """
        Instantiates the CreateImage object that is responsible for downloading and creating an OS image file
        within OpenStack
        """
        super(self.__class__, self).__start__()

        # Initialize for tearDown()
        self.image_creator = None
        self.network_creators = list()
        self.router_creators = list()
        self.flavor_creator = None
        self.keypair_creator = None
        self.inst_creator = None

        self.guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.keypair_priv_filepath = 'tmp/' + self.guid
        self.keypair_pub_filepath = self.keypair_priv_filepath + '.pub'
        self.keypair_name = self.guid + '-kp'
        self.vm_inst_name = self.guid + '-inst'
        self.port_1_name = self.guid + '-port-1'
        self.port_2_name = self.guid + '-port-2'
        self.floating_ip_name = self.guid + 'fip1'
        self.priv_net_config = openstack_tests.get_priv_net_config(
            net_name=self.guid + '-priv-net', subnet_name=self.guid + '-priv-subnet',
            router_name=self.guid + '-priv-router', external_net=self.ext_net_name)
        self.pub_net_config = openstack_tests.get_pub_net_config(
            net_name=self.guid + '-pub-net', subnet_name=self.guid + '-pub-subnet',
            router_name=self.guid + '-pub-router', external_net=self.ext_net_name)
        image_name = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.os_image_settings = openstack_tests.centos_url_image(name=image_name)

        try:
            # Create Image
            self.image_creator = OpenStackImage(self.os_creds, self.os_image_settings)
            self.image_creator.create()

            # First network is public
            self.network_creators.append(OpenStackNetwork(self.os_creds, self.pub_net_config.network_settings))
            # Second network is private
            self.network_creators.append(OpenStackNetwork(self.os_creds, self.priv_net_config.network_settings))
            for network_creator in self.network_creators:
                network_creator.create()

            self.router_creators.append(OpenStackRouter(self.os_creds, self.pub_net_config.router_settings))
            self.router_creators.append(OpenStackRouter(self.os_creds, self.priv_net_config.router_settings))

            # Create Routers
            for router_creator in self.router_creators:
                router_creator.create()

            # Create Flavor
            self.flavor_creator = OpenStackFlavor(
                self.admin_os_creds,
                FlavorSettings(name=self.guid + '-flavor-name', ram=2048, disk=10, vcpus=2))
            self.flavor_creator.create()

            # Create Keypair
            self.keypair_creator = OpenStackKeypair(
                self.os_creds, KeypairSettings(
                    name=self.keypair_name, public_filepath=self.keypair_pub_filepath,
                    private_filepath=self.keypair_priv_filepath))
            self.keypair_creator.create()
        except Exception as e:
            self.tearDown()
            raise Exception(e.message)

    def tearDown(self):
        """
        Cleans the created objects
        """
        if self.inst_creator:
            try:
                self.inst_creator.clean()
            except Exception as e:
                logger.error('Unexpected exception cleaning VM instance with message - ' + e.message)

        if self.keypair_creator:
            try:
                self.keypair_creator.clean()
            except Exception as e:
                logger.error('Unexpected exception cleaning keypair with message - ' + e.message)

        if os.path.isfile(self.keypair_pub_filepath):
            os.remove(self.keypair_pub_filepath)

        if os.path.isfile(self.keypair_priv_filepath):
            os.remove(self.keypair_priv_filepath)

        if self.flavor_creator:
            try:
                self.flavor_creator.clean()
            except Exception as e:
                logger.error('Unexpected exception cleaning flavor with message - ' + e.message)

        for router_creator in self.router_creators:
            try:
                router_creator.clean()
            except Exception as e:
                logger.error('Unexpected exception cleaning router with message - ' + e.message)

        for network_creator in self.network_creators:
            try:
                network_creator.clean()
            except Exception as e:
                logger.error('Unexpected exception cleaning network with message - ' + e.message)

        if self.image_creator:
            try:
                self.image_creator.clean()
            except Exception as e:
                logger.error('Unexpected exception cleaning image with message - ' + e.message)

        super(self.__class__, self).__clean__()

    def test_dual_ports_dhcp(self):
        """
        Tests the creation of an OpenStack instance with a dual ports/NICs with a DHCP assigned IP.
        NOTE: This test and any others that call ansible will most likely fail unless you do one of
        two things:
        1. Have a ~/.ansible.cfg (or alternate means) to set host_key_checking = False
        2. Set the following environment variable in your executing shell: ANSIBLE_HOST_KEY_CHECKING=False
        Should this not be performed, the creation of the host ssh key will cause your ansible calls to fail.
        """
        # Create ports/NICs for instance
        ports_settings = []
        ctr = 1
        for network_creator in self.network_creators:
            ports_settings.append(PortSettings(
                name=self.guid + '-port-' + str(ctr),
                network_name=network_creator.network_settings.name))
            ctr += 1

        # Create instance
        instance_settings = VmInstanceSettings(
            name=self.vm_inst_name, flavor=self.flavor_creator.flavor_settings.name, port_settings=ports_settings,
            floating_ip_settings=[FloatingIpSettings(
                name=self.floating_ip_name, port_name=self.port_1_name,
                router_name=self.pub_net_config.router_settings.name)])

        self.inst_creator = OpenStackVmInstance(
            self.os_creds, instance_settings, self.image_creator.image_settings,
            keypair_settings=self.keypair_creator.keypair_settings)

        vm_inst = self.inst_creator.create(block=True)

        self.assertEquals(vm_inst, self.inst_creator.get_vm_inst())

        # Effectively blocks until VM has been properly activated
        self.assertTrue(self.inst_creator.vm_active(block=True))

        # Effectively blocks until VM's ssh port has been opened
        self.assertTrue(self.inst_creator.vm_ssh_active(block=True))

        self.inst_creator.config_nics()

        # TODO - *** ADD VALIDATION HERE ***
        # TODO - Add validation that both floating IPs work
        # TODO - Add tests where only one NIC has a floating IP
        # TODO - Add tests where one attempts to place a floating IP on a network/router without an external gateway


class InstanceSecurityGroupTests(OSIntegrationTestCase):
    """
    Tests that include, add, and remove security groups from VM instances
    """
    def setUp(self):
        """
        Instantiates the CreateImage object that is responsible for downloading and creating an OS image file
        within OpenStack
        """
        super(self.__class__, self).__start__()

        self.guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.vm_inst_name = self.guid + '-inst'
        self.nova = nova_utils.nova_client(self.os_creds)
        self.os_image_settings = openstack_tests.cirros_url_image(name=self.guid + '-image')

        self.keypair_priv_filepath = 'tmp/' + self.guid
        self.keypair_pub_filepath = self.keypair_priv_filepath + '.pub'
        self.keypair_name = self.guid + '-kp'
        self.vm_inst_name = self.guid + '-inst'
        self.port_1_name = self.guid + 'port-1'
        self.port_2_name = self.guid + 'port-2'
        self.floating_ip_name = self.guid + 'fip1'

        self.pub_net_config = openstack_tests.get_pub_net_config(
            net_name=self.guid + '-pub-net', subnet_name=self.guid + '-pub-subnet',
            router_name=self.guid + '-pub-router', external_net=self.ext_net_name)

        # Initialize for tearDown()
        self.image_creator = None
        self.keypair_creator = None
        self.flavor_creator = None
        self.network_creator = None
        self.router_creator = None
        self.inst_creator = None
        self.sec_grp_creators = list()

        try:
            # Create Image
            self.image_creator = OpenStackImage(self.os_creds, self.os_image_settings)
            self.image_creator.create()

            # Create Network
            self.network_creator = OpenStackNetwork(self.os_creds, self.pub_net_config.network_settings)
            self.network_creator.create()

            # Create Router
            self.router_creator = OpenStackRouter(self.os_creds, self.pub_net_config.router_settings)
            self.router_creator.create()

            # Create Flavor
            self.flavor_creator = OpenStackFlavor(
                self.admin_os_creds,
                FlavorSettings(name=self.guid + '-flavor-name', ram=2048, disk=10, vcpus=2))
            self.flavor_creator.create()

            self.keypair_creator = OpenStackKeypair(
                self.os_creds, KeypairSettings(
                    name=self.keypair_name, public_filepath=self.keypair_pub_filepath,
                    private_filepath=self.keypair_priv_filepath))
            self.keypair_creator.create()
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
                logger.error('Unexpected exception cleaning VM instance with message - ' + e.message)

        for sec_grp_creator in self.sec_grp_creators:
            try:
                sec_grp_creator.clean()
            except Exception as e:
                logger.error('Unexpected exception cleaning security group with message - ' + e.message)

        if self.keypair_creator:
            try:
                self.keypair_creator.clean()
            except Exception as e:
                logger.error('Unexpected exception cleaning keypair with message - ' + e.message)

        if os.path.isfile(self.keypair_pub_filepath):
            os.remove(self.keypair_pub_filepath)

        if os.path.isfile(self.keypair_priv_filepath):
            os.remove(self.keypair_priv_filepath)

        if self.flavor_creator:
            try:
                self.flavor_creator.clean()
            except Exception as e:
                logger.error('Unexpected exception cleaning flavor with message - ' + e.message)

        if self.router_creator:
            try:
                self.router_creator.clean()
            except Exception as e:
                logger.error('Unexpected exception cleaning router with message - ' + e.message)

        if self.network_creator:
            try:
                self.network_creator.clean()
            except Exception as e:
                logger.error('Unexpected exception cleaning network with message - ' + e.message)

        if self.image_creator:
            try:
                self.image_creator.clean()
            except Exception as e:
                logger.error('Unexpected exception cleaning image with message - ' + e.message)

        super(self.__class__, self).__clean__()

    def test_add_security_group(self):
        """
        Tests the addition of a security group created after the instance.
        """
        # Create instance
        instance_settings = VmInstanceSettings(
            name=self.vm_inst_name, flavor=self.flavor_creator.flavor_settings.name)
        self.inst_creator = OpenStackVmInstance(self.os_creds, instance_settings, self.image_creator.image_settings)
        vm_inst = self.inst_creator.create()
        self.assertIsNotNone(vm_inst)

        # Create security group object to add to instance
        sec_grp_settings = SecurityGroupSettings(name=self.guid + '-name', description='hello group')
        sec_grp_creator = OpenStackSecurityGroup(self.os_creds, sec_grp_settings)
        sec_grp = sec_grp_creator.create()
        self.sec_grp_creators.append(sec_grp_creator)

        # Check that group has not been added
        self.assertFalse(inst_has_sec_grp(self.inst_creator.get_vm_inst(), sec_grp_settings.name))

        # Add security group to instance after activated
        self.inst_creator.add_security_group(sec_grp)

        # Validate that security group has been added
        self.assertTrue(inst_has_sec_grp(self.inst_creator.get_vm_inst(), sec_grp_settings.name))

    def test_add_invalid_security_group(self):
        """
        Tests the addition of a security group that no longer exists.
        """
        # Create instance
        instance_settings = VmInstanceSettings(
            name=self.vm_inst_name, flavor=self.flavor_creator.flavor_settings.name)
        self.inst_creator = OpenStackVmInstance(self.os_creds, instance_settings, self.image_creator.image_settings)
        vm_inst = self.inst_creator.create()
        self.assertIsNotNone(vm_inst)

        # Create security group object to add to instance
        sec_grp_settings = SecurityGroupSettings(name=self.guid + '-name', description='hello group')
        sec_grp_creator = OpenStackSecurityGroup(self.os_creds, sec_grp_settings)
        sec_grp = sec_grp_creator.create()
        sec_grp_creator.clean()
        self.sec_grp_creators.append(sec_grp_creator)

        # Check that group has not been added
        self.assertFalse(inst_has_sec_grp(self.inst_creator.get_vm_inst(), sec_grp_settings.name))

        # Add security group to instance after activated
        self.assertFalse(self.inst_creator.add_security_group(sec_grp))

        # Validate that security group has been added
        self.assertFalse(inst_has_sec_grp(self.inst_creator.get_vm_inst(), sec_grp_settings.name))

    def test_remove_security_group(self):
        """
        Tests the removal of a security group created before and added to the instance.
        """
        # Create security group object to add to instance
        sec_grp_settings = SecurityGroupSettings(name=self.guid + '-name', description='hello group')
        sec_grp_creator = OpenStackSecurityGroup(self.os_creds, sec_grp_settings)
        sec_grp = sec_grp_creator.create()
        self.sec_grp_creators.append(sec_grp_creator)

        # Create instance
        instance_settings = VmInstanceSettings(
            name=self.vm_inst_name, flavor=self.flavor_creator.flavor_settings.name,
            security_group_names=[sec_grp_settings.name])
        self.inst_creator = OpenStackVmInstance(self.os_creds, instance_settings, self.image_creator.image_settings)
        vm_inst = self.inst_creator.create()
        self.assertIsNotNone(vm_inst)

        # Check that group has been added
        self.assertTrue(inst_has_sec_grp(vm_inst, sec_grp_settings.name))

        # Add security group to instance after activated
        self.assertTrue(self.inst_creator.remove_security_group(sec_grp))

        # Validate that security group has been added
        self.assertFalse(inst_has_sec_grp(self.inst_creator.get_vm_inst(), sec_grp_settings.name))

    def test_remove_security_group_never_added(self):
        """
        Tests the removal of a security group that was never added in the first place.
        """
        # Create security group object to add to instance
        sec_grp_settings = SecurityGroupSettings(name=self.guid + '-name', description='hello group')
        sec_grp_creator = OpenStackSecurityGroup(self.os_creds, sec_grp_settings)
        sec_grp = sec_grp_creator.create()
        self.sec_grp_creators.append(sec_grp_creator)

        # Create instance
        instance_settings = VmInstanceSettings(
            name=self.vm_inst_name, flavor=self.flavor_creator.flavor_settings.name)
        self.inst_creator = OpenStackVmInstance(self.os_creds, instance_settings, self.image_creator.image_settings)
        vm_inst = self.inst_creator.create()
        self.assertIsNotNone(vm_inst)

        # Check that group has been added
        self.assertFalse(inst_has_sec_grp(vm_inst, sec_grp_settings.name))

        # Add security group to instance after activated
        self.assertFalse(self.inst_creator.remove_security_group(sec_grp))

        # Validate that security group has been added
        self.assertFalse(inst_has_sec_grp(self.inst_creator.get_vm_inst(), sec_grp_settings.name))

    def test_add_same_security_group(self):
        """
        Tests the addition of a security group created before add added to the instance.
        """
        # Create security group object to add to instance
        sec_grp_settings = SecurityGroupSettings(name=self.guid + '-name', description='hello group')
        sec_grp_creator = OpenStackSecurityGroup(self.os_creds, sec_grp_settings)
        sec_grp = sec_grp_creator.create()
        self.sec_grp_creators.append(sec_grp_creator)

        # Create instance
        instance_settings = VmInstanceSettings(
            name=self.vm_inst_name, flavor=self.flavor_creator.flavor_settings.name,
            security_group_names=[sec_grp_settings.name])
        self.inst_creator = OpenStackVmInstance(self.os_creds, instance_settings, self.image_creator.image_settings)
        vm_inst = self.inst_creator.create()
        self.assertIsNotNone(vm_inst)

        # Check that group has been added
        self.assertTrue(inst_has_sec_grp(vm_inst, sec_grp_settings.name))

        # Add security group to instance after activated
        self.assertTrue(self.inst_creator.add_security_group(sec_grp))

        # Validate that security group has been added
        self.assertTrue(inst_has_sec_grp(self.inst_creator.get_vm_inst(), sec_grp_settings.name))


def inst_has_sec_grp(vm_inst, sec_grp_name):
    """
    Returns true if instance has a security group of a given name
    :return:
    """
    if not hasattr(vm_inst, 'security_groups'):
        return False

    found = False
    for sec_grp_dict in vm_inst.security_groups:
        if sec_grp_name in sec_grp_dict['name']:
            found = True
            break
    return found


def validate_ssh_client(instance_creator):
    """
    Returns True if instance_creator returns an SSH client that is valid
    :param instance_creator: the object responsible for creating the VM instance
    :return: T/F
    """
    ssh_active = instance_creator.vm_ssh_active(block=True)

    if ssh_active:
        ssh_client = instance_creator.ssh_client()
        if ssh_client:
            out = ssh_client.exec_command('pwd')[1]
        else:
            return False

        channel = out.channel
        in_buffer = channel.in_buffer
        pwd_out = in_buffer.read(1024)
        if not pwd_out or len(pwd_out) < 10:
            return False
        return True

    return False


class CreateInstanceFromThreePartImage(OSIntegrationTestCase):
    """
    Test for the CreateInstance class for creating an image from a 3-part image
    """

    def setUp(self):
        """
        Instantiates the CreateImage object that is responsible for downloading and creating an OS image file
        within OpenStack
        """
        super(self.__class__, self).__start__()

        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.image_name = guid
        self.vm_inst_name = guid + '-inst'
        self.nova = nova_utils.nova_client(self.os_creds)

        net_config = openstack_tests.get_priv_net_config(
            net_name=guid + '-pub-net', subnet_name=guid + '-pub-subnet',
            router_name=guid + '-pub-router', external_net=self.ext_net_name)

        # Initialize for tearDown()
        self.image_creators = list()
        self.network_creator = None
        self.flavor_creator = None
        self.inst_creator = None

        try:
            # Create Images
            # Create the kernel image
            kernel_image_settings = openstack_tests.cirros_url_image(name=self.image_name+'_kernel',
                url='http://download.cirros-cloud.net/0.3.4/cirros-0.3.4-x86_64-kernel')
            self.image_creators.append(OpenStackImage(self.os_creds, kernel_image_settings))
            kernel_image = self.image_creators[-1].create()

            # Create the ramdisk image
            ramdisk_image_settings = openstack_tests.cirros_url_image(name=self.image_name+'_ramdisk',
                url='http://download.cirros-cloud.net/0.3.4/cirros-0.3.4-x86_64-initramfs')
            self.image_creators.append(OpenStackImage(self.os_creds, ramdisk_image_settings))
            ramdisk_image = self.image_creators[-1].create()
            self.assertIsNotNone(ramdisk_image)

            # Create the main image
            os_image_settings = openstack_tests.cirros_url_image(name=self.image_name,
                url='http://download.cirros-cloud.net/0.3.4/cirros-0.3.4-x86_64-disk.img')
            properties = {}
            properties['kernel_id'] = kernel_image.id
            properties['ramdisk_id'] = ramdisk_image.id
            os_image_settings.extra_properties = properties
            self.image_creators.append(OpenStackImage(self.os_creds, os_image_settings))
            created_image = self.image_creators[-1].create()

            # Create Flavor
            self.flavor_creator = OpenStackFlavor(
                self.admin_os_creds,
                FlavorSettings(name=guid + '-flavor-name', ram=2048, disk=10, vcpus=2))
            self.flavor_creator.create()

            # Create Network
            self.network_creator = OpenStackNetwork(self.os_creds, net_config.network_settings)
            self.network_creator.create()

            self.port_settings = PortSettings(name=guid + '-port',
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
                logger.error('Unexpected exception cleaning VM instance with message - ' + e.message)

        if self.flavor_creator:
            try:
                self.flavor_creator.clean()
            except Exception as e:
                logger.error('Unexpected exception cleaning flavor with message - ' + e.message)

        if self.network_creator:
            try:
                self.network_creator.clean()
            except Exception as e:
                logger.error('Unexpected exception cleaning network with message - ' + e.message)

        if self.image_creators:
            try:
                while self.image_creators:
                    self.image_creators[0].clean()
                    self.image_creators.pop(0)
            except Exception as e:
                logger.error('Unexpected exception cleaning image with message - ' + e.message)

        super(self.__class__, self).__clean__()

    def test_create_delete_instance_from_three_part_image(self):
        """
        Tests the creation of an OpenStack instance from a 3-part image.
        """
        instance_settings = VmInstanceSettings(name=self.vm_inst_name, flavor=self.flavor_creator.flavor_settings.name,
                                               port_settings=[self.port_settings])

        # The last created image is the main image from which we create the instance
        self.inst_creator = OpenStackVmInstance(
            self.os_creds, instance_settings, self.image_creators[-1].image_settings)

        vm_inst = self.inst_creator.create()
        self.assertEquals(1, len(nova_utils.get_servers_by_name(self.nova, instance_settings.name)))

        # Delete instance
        nova_utils.delete_vm_instance(self.nova, vm_inst)

        self.assertTrue(self.inst_creator.vm_deleted(block=True))
        self.assertEquals(0, len(nova_utils.get_servers_by_name(self.nova, instance_settings.name)))

        # Exception should not be thrown
        self.inst_creator.clean()

