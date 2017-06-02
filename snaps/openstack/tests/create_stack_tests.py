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
import time

from heatclient.exc import HTTPBadRequest

from snaps.openstack.create_flavor import OpenStackFlavor, FlavorSettings

from snaps.openstack.create_image import OpenStackImage

try:
    from urllib.request import URLError
except ImportError:
    from urllib2 import URLError

import logging
import unittest
import uuid

from snaps.openstack import create_stack
from snaps.openstack.create_stack import StackSettings, StackSettingsError
from snaps.openstack.tests import openstack_tests
from snaps.openstack.tests.os_source_file_test import OSIntegrationTestCase
from snaps.openstack.utils import heat_utils

__author__ = 'spisarski'

logger = logging.getLogger('create_stack_tests')


class StackSettingsUnitTests(unittest.TestCase):
    """
    Tests the construction of the StackSettings class
    """
    def test_no_params(self):
        with self.assertRaises(StackSettingsError):
            StackSettings()

    def test_empty_config(self):
        with self.assertRaises(StackSettingsError):
            StackSettings(config=dict())

    def test_name_only(self):
        with self.assertRaises(StackSettingsError):
            StackSettings(name='foo')

    def test_config_with_name_only(self):
        with self.assertRaises(StackSettingsError):
            StackSettings(config={'name': 'foo'})

    def test_config_minimum(self):
        settings = StackSettings(config={'name': 'stack', 'template_path': 'foo'})
        self.assertEqual('stack', settings.name)
        self.assertEqual('foo', settings.template_path)
        self.assertIsNone(settings.env_values)
        self.assertEqual(create_stack.STACK_COMPLETE_TIMEOUT, settings.stack_create_timeout)

    def test_minimum(self):
        settings = StackSettings(name='stack', template_path='foo')
        self.assertEqual('stack', settings.name)
        self.assertEqual('foo', settings.template_path)
        self.assertIsNone(settings.env_values)
        self.assertEqual(create_stack.STACK_COMPLETE_TIMEOUT, settings.stack_create_timeout)

    def test_all(self):
        env_values = {'foo': 'bar'}
        settings = StackSettings(name='stack', template_path='foo', env_values=env_values, stack_create_timeout=999)
        self.assertEqual('stack', settings.name)
        self.assertEqual('foo', settings.template_path)
        self.assertEqual(env_values, settings.env_values)
        self.assertEqual(999, settings.stack_create_timeout)

    def test_config_all(self):
        env_values = {'foo': 'bar'}
        settings = StackSettings(
            config={'name': 'stack', 'template_path': 'foo',
                    'env_values': env_values, 'stack_create_timeout': 999})
        self.assertEqual('stack', settings.name)
        self.assertEqual('foo', settings.template_path)
        self.assertEqual(env_values, settings.env_values)
        self.assertEqual(999, settings.stack_create_timeout)


class CreateStackSuccessTests(OSIntegrationTestCase):
    """
    Test for the CreateStack class defined in create_stack.py
    """

    def setUp(self):
        """
        Instantiates the CreateStack object that is responsible for downloading and creating an OS stack file
        within OpenStack
        """
        super(self.__class__, self).__start__()

        guid = str(uuid.uuid4())
        self.heat_cli = heat_utils.heat_client(self.os_creds)
        self.stack_creator = None

        self.image_creator = OpenStackImage(
            self.os_creds, openstack_tests.cirros_image_settings(
                name=self.__class__.__name__ + '-' + str(guid) + '-image'))
        self.image_creator.create()

        # Create Flavor
        self.flavor_creator = OpenStackFlavor(
            self.admin_os_creds,
            FlavorSettings(name=guid + '-flavor-name', ram=128, disk=10, vcpus=1))
        self.flavor_creator.create()

        env_values = {'image_name': self.image_creator.image_settings.name,
                      'flavor_name': self.flavor_creator.flavor_settings.name}
        self.stack_settings = StackSettings(name=self.__class__.__name__ + '-' + str(guid) + '-stack',
                                            template_path='../examples/heat/test_heat_template.yaml',
                                            env_values=env_values)

    def tearDown(self):
        """
        Cleans the stack and downloaded stack file
        """
        if self.stack_creator:
            self.stack_creator.clean()

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

        super(self.__class__, self).__clean__()

    def test_create_stack(self):
        """
        Tests the creation of an OpenStack stack from a URL.
        """
        # Create Stack
        # Set the default stack settings, then set any custom parameters sent from the app

        self.stack_creator = create_stack.OpenStackHeatStack(self.os_creds, self.stack_settings)
        created_stack = self.stack_creator.create()
        self.assertIsNotNone(created_stack)

        retrieved_stack = heat_utils.get_stack_by_id(self.heat_cli, created_stack.id)
        self.assertIsNotNone(retrieved_stack)
        self.assertEqual(created_stack.name, retrieved_stack.name)
        self.assertEqual(created_stack.id, retrieved_stack.id)

    def test_create_delete_stack(self):
        """
        Tests the creation then deletion of an OpenStack stack to ensure clean() does not raise an Exception.
        """
        # Create Stack
        self.stack_creator = create_stack.OpenStackHeatStack(self.os_creds, self.stack_settings)
        created_stack = self.stack_creator.create()
        self.assertIsNotNone(created_stack)

        retrieved_stack = heat_utils.get_stack_by_id(self.heat_cli, created_stack.id)
        self.assertIsNotNone(retrieved_stack)
        self.assertEqual(created_stack.name, retrieved_stack.name)
        self.assertEqual(created_stack.id, retrieved_stack.id)

        # Delete Stack manually
        heat_utils.delete_stack(self.heat_cli, created_stack)

        end_time = time.time() + 60
        deleted = False
        while time.time() < end_time:
            deleted_stack = heat_utils.get_stack_by_id(self.heat_cli, retrieved_stack.id)
            if not deleted_stack:
                deleted = True
                break

        self.assertTrue(deleted)

        # Must not throw an exception when attempting to cleanup non-existent stack
        self.stack_creator.clean()
        self.assertIsNone(self.stack_creator.get_stack())

    def test_create_same_stack(self):
        """
        Tests the creation of an OpenStack stack when the stack already exists.
        """
        # Create Stack
        self.stack_creator = create_stack.OpenStackHeatStack(self.os_creds, self.stack_settings)
        created_stack1 = self.stack_creator.create()

        retrieved_stack = heat_utils.get_stack_by_id(self.heat_cli, created_stack1.id)
        self.assertIsNotNone(retrieved_stack)
        self.assertEqual(created_stack1.name, retrieved_stack.name)
        self.assertEqual(created_stack1.id, retrieved_stack.id)

        # Should be retrieving the instance data
        stack_creator2 = create_stack.OpenStackHeatStack(self.os_creds, self.stack_settings)
        stack2 = stack_creator2.create()
        self.assertEqual(created_stack1.id, stack2.id)


class CreateStackNegativeTests(OSIntegrationTestCase):
    """
    Negative test cases for the CreateStack class
    """

    def setUp(self):
        super(self.__class__, self).__start__()

        self.stack_name = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.stack_creator = None

    def tearDown(self):
        if self.stack_creator:
            self.stack_creator.clean()
        super(self.__class__, self).__clean__()

    def test_missing_dependencies(self):
        """
        Expect an StackCreationError when the stack file does not exist
        """
        stack_settings = StackSettings(name=self.stack_name, template_path='../examples/heat/test_heat_template.yaml')
        self.stack_creator = create_stack.OpenStackHeatStack(self.os_creds, stack_settings)
        with self.assertRaises(HTTPBadRequest):
            self.stack_creator.create()

    def test_bad_stack_file(self):
        """
        Expect an StackCreationError when the stack file does not exist
        """
        stack_settings = StackSettings(name=self.stack_name, template_path='foo')
        self.stack_creator = create_stack.OpenStackHeatStack(self.os_creds, stack_settings)
        with self.assertRaises(IOError):
            self.stack_creator.create()
