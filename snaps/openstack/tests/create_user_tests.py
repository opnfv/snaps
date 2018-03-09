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

from snaps.config.user import UserConfig
from snaps.openstack.create_user import OpenStackUser, UserSettings
from snaps.openstack.tests.os_source_file_test import OSComponentTestCase
from snaps.openstack.utils import keystone_utils

__author__ = 'spisarski'


class UserSettingsUnitTests(unittest.TestCase):
    """
    Tests the construction of the UserSettings class
    """

    def test_no_params(self):
        with self.assertRaises(Exception):
            UserSettings()

    def test_empty_config(self):
        with self.assertRaises(Exception):
            UserSettings(**dict())

    def test_name_only(self):
        with self.assertRaises(Exception):
            UserSettings(name='foo')

    def test_config_with_name_only(self):
        with self.assertRaises(Exception):
            UserSettings(**{'name': 'foo'})

    def test_name_pass_enabled_str(self):
        with self.assertRaises(Exception):
            UserSettings(name='foo', password='bar', enabled='true')

    def test_config_with_name_pass_enabled_str(self):
        with self.assertRaises(Exception):
            UserSettings(
                **{'name': 'foo', 'password': 'bar', 'enabled': 'true'})

    def test_name_pass_only(self):
        settings = UserSettings(name='foo', password='bar')
        self.assertEqual('foo', settings.name)
        self.assertEqual('bar', settings.password)
        self.assertIsNone(settings.project_name)
        self.assertIsNone(settings.email)
        self.assertTrue(settings.enabled)

    def test_config_with_name_pass_only(self):
        settings = UserSettings(**{'name': 'foo', 'password': 'bar'})
        self.assertEqual('foo', settings.name)
        self.assertEqual('bar', settings.password)
        self.assertIsNone(settings.project_name)
        self.assertIsNone(settings.email)
        self.assertTrue(settings.enabled)

    def test_all(self):
        settings = UserSettings(name='foo', password='bar',
                                project_name='proj-foo', email='foo@bar.com',
                                enabled=False)
        self.assertEqual('foo', settings.name)
        self.assertEqual('bar', settings.password)
        self.assertEqual('proj-foo', settings.project_name)
        self.assertEqual('foo@bar.com', settings.email)
        self.assertFalse(settings.enabled)

    def test_config_all(self):
        settings = UserSettings(**{'name': 'foo', 'password': 'bar',
                                   'project_name': 'proj-foo',
                                   'email': 'foo@bar.com',
                                   'enabled': False})
        self.assertEqual('foo', settings.name)
        self.assertEqual('bar', settings.password)
        self.assertEqual('proj-foo', settings.project_name)
        self.assertEqual('foo@bar.com', settings.email)
        self.assertFalse(settings.enabled)


class CreateUserSuccessTests(OSComponentTestCase):
    """
    Test for the CreateImage class defined in create_image.py
    """

    def setUp(self):
        """
        Instantiates the CreateImage object that is responsible for downloading
        and creating an OS image file within OpenStack
        """
        guid = str(uuid.uuid4())[:-19]
        guid = self.__class__.__name__ + '-' + guid
        self.user_settings = UserConfig(
            name=guid + '-name',
            password=guid + '-password',
            roles={'admin': self.os_creds.project_name},
            domain_name=self.os_creds.user_domain_name)

        self.keystone = keystone_utils.keystone_client(self.os_creds, self.os_session)

        # Initialize for cleanup
        self.user_creator = None

    def tearDown(self):
        """
        Cleans the image and downloaded image file
        """
        if self.user_creator:
            self.user_creator.clean()

        super(self.__class__, self).__clean__()

    def test_create_user(self):
        """
        Tests the creation of an OpenStack user.
        """
        self.user_creator = OpenStackUser(self.os_creds, self.user_settings)
        created_user = self.user_creator.create()
        self.assertIsNotNone(created_user)

        retrieved_user = keystone_utils.get_user(self.keystone,
                                                 self.user_settings.name)
        self.assertIsNotNone(retrieved_user)
        self.assertEqual(created_user, retrieved_user)

    def test_create_user_2x(self):
        """
        Tests the creation of an OpenStack user twice to ensure it only creates
        one.
        """
        self.user_creator = OpenStackUser(self.os_creds, self.user_settings)
        created_user = self.user_creator.create()
        self.assertIsNotNone(created_user)

        retrieved_user = keystone_utils.get_user(self.keystone,
                                                 self.user_settings.name)
        self.assertIsNotNone(retrieved_user)
        self.assertEqual(created_user, retrieved_user)

        # Create user for the second time to ensure it is the same
        user2 = OpenStackUser(self.os_creds, self.user_settings).create()
        self.assertEqual(retrieved_user, user2)

    def test_create_delete_user(self):
        """
        Tests the creation of an OpenStack user then delete.
        """
        # Create Image
        self.user_creator = OpenStackUser(self.os_creds, self.user_settings)
        created_user = self.user_creator.create()
        self.assertIsNotNone(created_user)

        keystone_utils.delete_user(self.keystone, created_user)

        # Delete user
        self.user_creator.clean()
        self.assertIsNone(self.user_creator.get_user())

    def test_create_admin_user(self):
        """
        Tests the creation of an OpenStack user.
        """
        self.user_creator = OpenStackUser(self.os_creds, self.user_settings)
        created_user = self.user_creator.create()
        self.assertIsNotNone(created_user)

        retrieved_user = keystone_utils.get_user(self.keystone,
                                                 self.user_settings.name)
        self.assertIsNotNone(retrieved_user)
        self.assertEqual(created_user, retrieved_user)

        role = keystone_utils.get_role_by_name(self.keystone, 'admin')
        self.assertIsNotNone(role)

        os_proj = keystone_utils.get_project(
            keystone=self.keystone, project_name=self.os_creds.project_name)
        user_roles = keystone_utils.get_roles_by_user(
            self.keystone, retrieved_user, os_proj)
        self.assertIsNotNone(user_roles)
        self.assertEqual(1, len(user_roles))
        self.assertEqual(role.id, user_roles[0].id)
