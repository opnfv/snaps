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
import pkg_resources
import uuid

import time

from snaps.openstack import create_stack
from snaps.openstack.create_flavor import OpenStackFlavor, FlavorSettings

from snaps.openstack.create_image import OpenStackImage
from snaps.openstack.create_instance import OpenStackVmInstance
from snaps.openstack.create_stack import StackSettings
from snaps.openstack.tests import openstack_tests
from snaps.openstack.tests.os_source_file_test import OSComponentTestCase
from snaps.openstack.utils import (
    heat_utils, neutron_utils, nova_utils, settings_utils, glance_utils)

__author__ = 'spisarski'

logger = logging.getLogger('nova_utils_tests')


class HeatSmokeTests(OSComponentTestCase):
    """
    Tests to ensure that the heat client can communicate with the cloud
    """

    def test_heat_connect_success(self):
        """
        Tests to ensure that the proper credentials can connect.
        """
        heat = heat_utils.heat_client(self.os_creds)

        # This should not throw an exception
        stacks = heat.stacks.list()
        for stack in stacks:
            print stack

    def test_heat_connect_fail(self):
        """
        Tests to ensure that the improper credentials cannot connect.
        """
        from snaps.openstack.os_credentials import OSCreds

        heat = heat_utils.heat_client(
            OSCreds(username='user', password='pass',
                    auth_url=self.os_creds.auth_url,
                    project_name=self.os_creds.project_name,
                    proxy_settings=self.os_creds.proxy_settings))
        stacks = heat.stacks.list()

        # This should throw an exception
        with self.assertRaises(Exception):
            for stack in stacks:
                print stack


class HeatUtilsCreateSimpleStackTests(OSComponentTestCase):
    """
    Test basic Heat functionality
    """

    def setUp(self):
        """
        Instantiates OpenStack instances that cannot be spawned by Heat
        """
        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        stack_name1 = guid + '-stack1'
        stack_name2 = guid + '-stack2'
        self.network_name = guid + '-net'
        self.subnet_name = guid + '-subnet'
        self.vm_inst_name = guid + '-inst'

        self.image_creator = OpenStackImage(
            self.os_creds, openstack_tests.cirros_image_settings(
                name=guid + '-image', image_metadata=self.image_metadata))
        self.image_creator.create()

        # Create Flavor
        self.flavor_creator = OpenStackFlavor(
            self.os_creds,
            FlavorSettings(name=guid + '-flavor', ram=256, disk=10, vcpus=1))
        self.flavor_creator.create()

        env_values = {'image_name': self.image_creator.image_settings.name,
                      'flavor_name': self.flavor_creator.flavor_settings.name,
                      'net_name': self.network_name,
                      'subnet_name': self.subnet_name,
                      'inst_name': self.vm_inst_name}
        heat_tmplt_path = pkg_resources.resource_filename(
            'snaps.openstack.tests.heat', 'test_heat_template.yaml')
        self.stack_settings1 = StackSettings(
            name=stack_name1, template_path=heat_tmplt_path,
            env_values=env_values)
        self.stack_settings2 = StackSettings(
            name=stack_name2, template_path=heat_tmplt_path,
            env_values=env_values)
        self.stack1 = None
        self.stack2 = None
        self.heat_client = heat_utils.heat_client(self.os_creds)

    def tearDown(self):
        """
        Cleans the image and downloaded image file
        """
        if self.stack1:
            try:
                heat_utils.delete_stack(self.heat_client, self.stack1)
            except:
                pass

        if self.stack2:
            try:
                heat_utils.delete_stack(self.heat_client, self.stack2)
            except:
                pass

        if self.image_creator:
            try:
                self.image_creator.clean()
            except:
                pass

        if self.flavor_creator:
            try:
                self.flavor_creator.clean()
            except:
                pass

    def test_create_stack(self):
        """
        Tests the creation of an OpenStack Heat stack1 that does not exist.
        """
        self.stack1 = heat_utils.create_stack(self.heat_client,
                                              self.stack_settings1)

        stack_query_1 = heat_utils.get_stack(
            self.heat_client, stack_settings=self.stack_settings1)
        self.assertEqual(self.stack1, stack_query_1)

        stack_query_2 = heat_utils.get_stack(
            self.heat_client, stack_name=self.stack_settings1.name)
        self.assertEqual(self.stack1, stack_query_2)

        stack_query_3 = heat_utils.get_stack_by_id(self.heat_client,
                                                   self.stack1.id)
        self.assertEqual(self.stack1, stack_query_3)

        resources = heat_utils.get_resources(self.heat_client, self.stack1)
        self.assertIsNotNone(resources)
        self.assertEqual(4, len(resources))

        outputs = heat_utils.get_outputs(self.heat_client, self.stack1)
        self.assertIsNotNone(outputs)
        self.assertEqual(0, len(outputs))

        # Wait until stack deployment has completed
        end_time = time.time() + create_stack.STACK_COMPLETE_TIMEOUT
        is_active = False
        while time.time() < end_time:
            status = heat_utils.get_stack_status(self.heat_client,
                                                 self.stack1.id)
            if status == create_stack.STATUS_CREATE_COMPLETE:
                is_active = True
                break
            elif status == create_stack.STATUS_CREATE_FAILED:
                is_active = False
                break

            time.sleep(3)

        self.assertTrue(is_active)

        neutron = neutron_utils.neutron_client(self.os_creds)
        networks = heat_utils.get_stack_networks(
            self.heat_client, neutron, self.stack1)
        self.assertIsNotNone(networks)
        self.assertEqual(1, len(networks))
        self.assertEqual(self.network_name, networks[0].name)

        subnets = neutron_utils.get_subnets_by_network(neutron, networks[0])
        self.assertEqual(1, len(subnets))
        self.assertEqual(self.subnet_name, subnets[0].name)

        nova = nova_utils.nova_client(self.os_creds)
        servers = heat_utils.get_stack_servers(
            self.heat_client, nova, self.stack1)
        self.assertIsNotNone(servers)
        self.assertEqual(1, len(servers))
        self.assertEqual(self.vm_inst_name, servers[0].name)

    def test_create_stack_x2(self):
        """
        Tests the creation of an OpenStack keypair that does not exist.
        """
        self.stack1 = heat_utils.create_stack(self.heat_client,
                                              self.stack_settings1)

        stack1_query_1 = heat_utils.get_stack(
            self.heat_client, stack_settings=self.stack_settings1)
        self.assertEqual(self.stack1, stack1_query_1)

        stack1_query_2 = heat_utils.get_stack(
            self.heat_client, stack_name=self.stack_settings1.name)
        self.assertEqual(self.stack1, stack1_query_2)

        stack1_query_3 = heat_utils.get_stack_by_id(self.heat_client,
                                                    self.stack1.id)
        self.assertEqual(self.stack1, stack1_query_3)

        end_time = time.time() + create_stack.STACK_COMPLETE_TIMEOUT
        is_active = False
        while time.time() < end_time:
            status = heat_utils.get_stack_status(self.heat_client,
                                                 self.stack1.id)
            if status == create_stack.STATUS_CREATE_COMPLETE:
                is_active = True
                break
            elif status == create_stack.STATUS_CREATE_FAILED:
                is_active = False
                break

            time.sleep(3)

        self.assertTrue(is_active)

        self.stack2 = heat_utils.create_stack(self.heat_client,
                                              self.stack_settings2)

        stack2_query_1 = heat_utils.get_stack(
            self.heat_client, stack_settings=self.stack_settings2)
        self.assertEqual(self.stack2, stack2_query_1)

        stack2_query_2 = heat_utils.get_stack(
            self.heat_client, stack_name=self.stack_settings2.name)
        self.assertEqual(self.stack2, stack2_query_2)

        stack2_query_3 = heat_utils.get_stack_by_id(self.heat_client,
                                                    self.stack2.id)
        self.assertEqual(self.stack2, stack2_query_3)

        end_time = time.time() + create_stack.STACK_COMPLETE_TIMEOUT

        is_active = False
        while time.time() < end_time:
            status = heat_utils.get_stack_status(self.heat_client,
                                                 self.stack2.id)
            if status == create_stack.STATUS_CREATE_COMPLETE:
                is_active = True
                break
            elif status == create_stack.STATUS_CREATE_FAILED:
                is_active = False
                break

            time.sleep(3)

        self.assertTrue(is_active)


class HeatUtilsCreateComplexStackTests(OSComponentTestCase):
    """
    Test basic Heat functionality
    """

    def setUp(self):
        """
        Instantiates OpenStack instances that cannot be spawned by Heat
        """
        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        stack_name = guid + '-stack'
        self.network_name = guid + '-net'
        self.subnet_name = guid + '-subnet'
        self.vm_inst1_name = guid + '-inst1'
        self.vm_inst2_name = guid + '-inst2'
        self.flavor1_name = guid + '-flavor1'
        self.flavor2_name = guid + '-flavor2'
        self.keypair_name = guid + '-keypair'

        self.image_creator1 = OpenStackImage(
            self.os_creds, openstack_tests.cirros_image_settings(
                name=guid + '-image1', image_metadata=self.image_metadata))
        self.image_creator1.create()

        self.image_creator2 = OpenStackImage(
            self.os_creds, openstack_tests.cirros_image_settings(
                name=guid + '-image2', image_metadata=self.image_metadata))
        self.image_creator2.create()

        env_values = {'image1_name': self.image_creator1.image_settings.name,
                      'image2_name': self.image_creator2.image_settings.name,
                      'flavor1_name': self.flavor1_name,
                      'flavor2_name': self.flavor2_name,
                      'net_name': self.network_name,
                      'subnet_name': self.subnet_name,
                      'keypair_name': self.keypair_name,
                      'inst1_name': self.vm_inst1_name,
                      'inst2_name': self.vm_inst2_name,
                      'external_net_name': self.ext_net_name}
        heat_tmplt_path = pkg_resources.resource_filename(
            'snaps.openstack.tests.heat', 'floating_ip_heat_template.yaml')
        stack_settings = StackSettings(
            name=stack_name, template_path=heat_tmplt_path,
            env_values=env_values)
        self.heat_client = heat_utils.heat_client(self.os_creds)
        self.stack = heat_utils.create_stack(self.heat_client, stack_settings)

        # Wait until stack deployment has completed
        end_time = time.time() + create_stack.STACK_COMPLETE_TIMEOUT
        is_active = False
        while time.time() < end_time:
            status = heat_utils.get_stack_status(self.heat_client,
                                                 self.stack.id)
            if status == create_stack.STATUS_CREATE_COMPLETE:
                is_active = True
                break
            elif status == create_stack.STATUS_CREATE_FAILED:
                is_active = False
                break

            time.sleep(3)
        self.assertTrue(is_active)

    def tearDown(self):
        """
        Cleans the image and downloaded image file
        """
        if self.stack:
            try:
                heat_utils.delete_stack(self.heat_client, self.stack)
                # Wait until stack deployment has completed
                end_time = time.time() + create_stack.STACK_COMPLETE_TIMEOUT
                is_deleted = False
                while time.time() < end_time:
                    status = heat_utils.get_stack_status(self.heat_client,
                                                         self.stack.id)
                    if status == create_stack.STATUS_DELETE_COMPLETE:
                        is_deleted = True
                        break
                    elif status == create_stack.STATUS_DELETE_FAILED:
                        is_deleted = False
                        break

                    time.sleep(3)

                if not is_deleted:
                    nova = nova_utils.nova_client(self.os_creds)
                    neutron = neutron_utils.neutron_client(self.os_creds)
                    glance = glance_utils.glance_client(self.os_creds)
                    servers = heat_utils.get_stack_servers(
                        self.heat_client, nova, self.stack)
                    for server in servers:
                        vm_settings = settings_utils.create_vm_inst_settings(
                            nova, neutron, server)
                        img_settings = settings_utils.determine_image_settings(
                            glance, server,
                            [self.image_creator1.image_settings,
                             self.image_creator2.image_settings])
                        vm_creator = OpenStackVmInstance(
                            self.os_creds, vm_settings, img_settings)
                        vm_creator.create(cleanup=False)
                        vm_creator.clean()
                        vm_creator.vm_deleted(block=True)

                    heat_utils.delete_stack(self.heat_client, self.stack)
                    time.sleep(20)
            except:
                    raise

        if self.image_creator1:
            try:
                self.image_creator1.clean()
            except:
                pass

        if self.image_creator2:
            try:
                self.image_creator2.clean()
            except:
                pass

    def test_get_settings_from_stack(self):
        """
        Tests that a heat template with floating IPs and can have the proper
        settings derived from settings_utils.py.
        """
        resources = heat_utils.get_resources(self.heat_client, self.stack)
        self.assertIsNotNone(resources)
        self.assertEqual(11, len(resources))

        options = heat_utils.get_outputs(self.heat_client, self.stack)
        self.assertIsNotNone(options)
        self.assertEqual(1, len(options))

        neutron = neutron_utils.neutron_client(self.os_creds)
        networks = heat_utils.get_stack_networks(
            self.heat_client, neutron, self.stack)
        self.assertIsNotNone(networks)
        self.assertEqual(1, len(networks))
        self.assertEqual(self.network_name, networks[0].name)

        network_settings = settings_utils.create_network_settings(
            neutron, networks[0])
        self.assertIsNotNone(network_settings)
        self.assertEqual(self.network_name, network_settings.name)

        nova = nova_utils.nova_client(self.os_creds)
        glance = glance_utils.glance_client(self.os_creds)

        servers = heat_utils.get_stack_servers(
            self.heat_client, nova, self.stack)
        self.assertIsNotNone(servers)
        self.assertEqual(2, len(servers))

        image_settings = settings_utils.determine_image_settings(
            glance, servers[0],
            [self.image_creator1.image_settings,
             self.image_creator2.image_settings])

        self.assertIsNotNone(image_settings)
        if image_settings.name.endswith('1'):
            self.assertEqual(
                self.image_creator1.image_settings.name, image_settings.name)
        else:
            self.assertEqual(
                self.image_creator2.image_settings.name, image_settings.name)

        image_settings = settings_utils.determine_image_settings(
            glance, servers[1],
            [self.image_creator1.image_settings,
             self.image_creator2.image_settings])
        if image_settings.name.endswith('1'):
            self.assertEqual(
                self.image_creator1.image_settings.name, image_settings.name)
        else:
            self.assertEqual(
                self.image_creator2.image_settings.name, image_settings.name)

        keypair1_settings = settings_utils.determine_keypair_settings(
            self.heat_client, self.stack, servers[0],
            priv_key_key='private_key')
        self.assertIsNotNone(keypair1_settings)
        self.assertEqual(self.keypair_name, keypair1_settings.name)

        keypair2_settings = settings_utils.determine_keypair_settings(
            self.heat_client, self.stack, servers[1],
            priv_key_key='private_key')
        self.assertIsNotNone(keypair2_settings)
        self.assertEqual(self.keypair_name, keypair2_settings.name)
