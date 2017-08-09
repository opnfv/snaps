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
from snaps.openstack.create_stack import StackSettings
from snaps.openstack.tests import openstack_tests
from snaps.openstack.tests.os_source_file_test import OSComponentTestCase
from snaps.openstack.utils import heat_utils, neutron_utils

__author__ = 'spisarski'

logger = logging.getLogger('nova_utils_tests')


class HeatSmokeTests(OSComponentTestCase):
    """
    Tests to ensure that the heat client can communicate with the cloud
    """

    def test_nova_connect_success(self):
        """
        Tests to ensure that the proper credentials can connect.
        """
        heat = heat_utils.heat_client(self.os_creds)

        # This should not throw an exception
        stacks = heat.stacks.list()
        for stack in stacks:
            print stack

    def test_nova_connect_fail(self):
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


class HeatUtilsCreateStackTests(OSComponentTestCase):
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
                      'subnet_name': self.subnet_name}
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

        outputs = heat_utils.get_stack_outputs(
            self.heat_client, self.stack1.id)
        self.assertIsNotNone(outputs)
        self.assertEqual(0, len(outputs))

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

        resources = heat_utils.get_resources(self.heat_client, self.stack1)
        self.assertIsNotNone(resources)
        self.assertEqual(4, len(resources))

        neutron = neutron_utils.neutron_client(self.os_creds)
        networks = heat_utils.get_stack_networks(
            self.heat_client, neutron, self.stack1)
        self.assertIsNotNone(networks)
        self.assertEqual(1, len(networks))
        self.assertEqual(self.network_name, networks[0].name)

        subnets = neutron_utils.get_subnets_by_network(neutron, networks[0])
        self.assertEqual(1, len(subnets))
        self.assertEqual(self.subnet_name, subnets[0].name)

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

        outputs = heat_utils.get_stack_outputs(self.heat_client,
                                               self.stack1.id)
        self.assertIsNotNone(outputs)
        self.assertEqual(0, len(outputs))

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

        outputs = heat_utils.get_stack_outputs(self.heat_client,
                                               self.stack2.id)
        self.assertIsNotNone(outputs)
        self.assertEqual(0, len(outputs))

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
