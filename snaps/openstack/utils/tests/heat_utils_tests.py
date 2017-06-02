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
import uuid

import time

from snaps.openstack import create_stack
from snaps.openstack.create_flavor import OpenStackFlavor, FlavorSettings

from snaps.openstack.create_image import OpenStackImage
from snaps.openstack.create_stack import StackSettings
from snaps.openstack.tests import openstack_tests
from snaps.openstack.tests.os_source_file_test import OSComponentTestCase
from snaps.openstack.utils import heat_utils

__author__ = 'spisarski'

logger = logging.getLogger('nova_utils_tests')


class HeatSmokeTests(OSComponentTestCase):
    """
    Tests to ensure that the nova client can communicate with the cloud
    """

    def test_nova_connect_success(self):
        """
        Tests to ensure that the proper credentials can connect.
        """
        heat = heat_utils.heat_client(self.os_creds)

        # This should not throw an exception
        heat.stacks.list()

    def test_nova_connect_fail(self):
        """
        Tests to ensure that the improper credentials cannot connect.
        """
        from snaps.openstack.os_credentials import OSCreds

        nova = heat_utils.heat_client(
            OSCreds(username='user', password='pass', auth_url=self.os_creds.auth_url,
                    project_name=self.os_creds.project_name, proxy_settings=self.os_creds.proxy_settings))

        # This should throw an exception
        with self.assertRaises(Exception):
            nova.flavors.list()


class HeatUtilsCreateStackTests(OSComponentTestCase):
    """
    Test basic nova keypair functionality
    """

    def setUp(self):
        """
        Instantiates the CreateImage object that is responsible for downloading and creating an OS image file
        within OpenStack
        """
        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        stack_name = self.__class__.__name__ + '-' + str(guid) + '-stack'

        self.image_creator = OpenStackImage(
            self.os_creds, openstack_tests.cirros_image_settings(
                name=self.__class__.__name__ + '-' + str(guid) + '-image'))
        self.image_creator.create()

        # Create Flavor
        self.flavor_creator = OpenStackFlavor(
            self.os_creds,
            FlavorSettings(name=guid + '-flavor', ram=128, disk=10, vcpus=1))
        self.flavor_creator.create()

        env_values = {'image_name': self.image_creator.image_settings.name,
                      'flavor_name': self.flavor_creator.flavor_settings.name}
        self.stack_settings = StackSettings(name=stack_name, template_path='../examples/heat/test_heat_template.yaml',
                                            env_values=env_values)
        self.stack = None
        self.heat_client = heat_utils.heat_client(self.os_creds)

    def tearDown(self):
        """
        Cleans the image and downloaded image file
        """
        if self.stack:
            try:
                heat_utils.delete_stack(self.heat_client, self.stack)
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
        Tests the creation of an OpenStack keypair that does not exist.
        """
        self.stack = heat_utils.create_stack(self.heat_client, self.stack_settings)

        stack_query_1 = heat_utils.get_stack_by_name(self.heat_client, self.stack_settings.name)
        self.assertEqual(self.stack.id, stack_query_1.id)

        stack_query_2 = heat_utils.get_stack_by_id(self.heat_client, self.stack.id)
        self.assertEqual(self.stack.id, stack_query_2.id)

        outputs = heat_utils.get_stack_outputs(self.heat_client, self.stack.id)
        self.assertIsNotNone(outputs)
        self.assertEqual(0, len(outputs))

        end_time = time.time() + create_stack.STACK_COMPLETE_TIMEOUT

        is_active = False
        while time.time() < end_time:
            status = heat_utils.get_stack_status(self.heat_client, self.stack.id)
            if status == create_stack.STATUS_CREATE_COMPLETE:
                is_active = True
                break

            time.sleep(3)

        self.assertTrue(is_active)
