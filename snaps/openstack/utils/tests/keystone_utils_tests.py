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

from snaps.openstack.create_project import ProjectSettings
from snaps.openstack.create_user import UserSettings
from snaps.openstack.tests.os_source_file_test import OSComponentTestCase
from snaps.openstack.utils import keystone_utils

__author__ = 'spisarski'


class KeystoneSmokeTests(OSComponentTestCase):
    """
    Tests to ensure that the neutron client can communicate with the cloud
    """

    def test_keystone_connect_success(self):
        """
        Tests to ensure that the proper credentials can connect.
        """
        keystone = keystone_utils.keystone_client(self.os_creds)

        users = keystone.users.list()
        self.assertIsNotNone(users)

    def test_keystone_connect_fail(self):
        """
        Tests to ensure that the improper credentials cannot connect.
        """
        from snaps.openstack.os_credentials import OSCreds

        with self.assertRaises(Exception):
            keystone = keystone_utils.keystone_client(OSCreds(
                username='user', password='pass', auth_url='url',
                project_name='project'))
            keystone.users.list()


class KeystoneUtilsTests(OSComponentTestCase):
    """
    Test for the CreateImage class defined in create_image.py
    """

    def setUp(self):
        """
        Instantiates the CreateImage object that is responsible for downloading
        and creating an OS image file within OpenStack
        """
        self.guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.username = self.guid + '-username'
        self.user = None

        self.project_name = self.guid + '-projName'
        self.project = None
        self.role = None
        self.keystone = keystone_utils.keystone_client(self.os_creds)

    def tearDown(self):
        """
        Cleans the remote OpenStack objects
        """
        if self.project:
                keystone_utils.delete_project(self.keystone, self.project)

        if self.user:
            keystone_utils.delete_user(self.keystone, self.user)

        if self.role:
            keystone_utils.delete_role(self.keystone, self.role)

    def test_create_user_minimal(self):
        """
        Tests the keystone_utils.create_user() function
        """
        user_settings = UserSettings(name=self.username,
                                     password=str(uuid.uuid4()))
        self.user = keystone_utils.create_user(self.keystone, user_settings)
        self.assertEqual(self.username, self.user.name)

        user = keystone_utils.get_user(self.keystone, self.username)
        self.assertIsNotNone(user)
        self.assertEqual(self.user, user)

    def test_create_project_minimal(self):
        """
        Tests the keyston_utils.create_project() funtion
        """
        project_settings = ProjectSettings(name=self.project_name)
        self.project = keystone_utils.create_project(self.keystone,
                                                     project_settings)
        self.assertEqual(self.project_name, self.project.name)

        project = keystone_utils.get_project(
            keystone=self.keystone, project_name=project_settings.name)
        self.assertIsNotNone(project)
        self.assertEqual(self.project_name, self.project.name)

    def test_get_endpoint_success(self):
        """
        Tests to ensure that proper credentials and proper service type can
        succeed.
        """
        endpoint = keystone_utils.get_endpoint(self.os_creds,
                                               service_type='identity')
        self.assertIsNotNone(endpoint)

    def test_get_endpoint_fail_without_proper_service(self):
        """
        Tests to ensure that proper credentials and improper service type
        cannot succeed.
        """
        with self.assertRaises(Exception):
            keystone_utils.get_endpoint(self.os_creds, service_type='glance')

    def test_get_endpoint_fail_without_proper_credentials(self):
        """
        Tests to ensure that improper credentials and proper service type
        cannot succeed.
        """
        from snaps.openstack.os_credentials import OSCreds

        with self.assertRaises(Exception):
            keystone_utils.get_endpoint(
                OSCreds(username='user', password='pass', auth_url='url',
                        project_name='project'),
                service_type='image')

    def test_get_endpoint_with_each_interface(self):
        """
        Tests to ensure that endpoint urls are obtained with
        'public', 'internal' and 'admin' interface
        """
        endpoint_public = keystone_utils.get_endpoint(self.os_creds,
                                                      service_type='image',
                                                      interface='public')
        endpoint_internal = keystone_utils.get_endpoint(self.os_creds,
                                                        service_type='image',
                                                        interface='internal')
        endpoint_admin = keystone_utils.get_endpoint(self.os_creds,
                                                     service_type='image',
                                                     interface='admin')
        self.assertIsNotNone(endpoint_public)
        self.assertIsNotNone(endpoint_internal)
        self.assertIsNotNone(endpoint_admin)

    def test_grant_user_role_to_project(self):
        """
        Tests the keystone_utils function grant_user_role_to_project()
        :return:
        """
        user_settings = UserSettings(name=self.username,
                                     password=str(uuid.uuid4()))
        self.user = keystone_utils.create_user(self.keystone, user_settings)
        self.assertEqual(self.username, self.user.name)

        project_settings = ProjectSettings(name=self.project_name)
        self.project = keystone_utils.create_project(self.keystone,
                                                     project_settings)
        self.assertEqual(self.project_name, self.project.name)

        role_name = self.guid + '-role'
        self.role = keystone_utils.create_role(self.keystone, role_name)
        self.assertEqual(role_name, self.role.name)

        keystone_utils.grant_user_role_to_project(
            self.keystone, self.role, self.user, self.project)

        user_roles = keystone_utils.get_roles_by_user(
            self.keystone, self.user, self.project)
        self.assertIsNotNone(user_roles)
        self.assertEqual(1, len(user_roles))
        self.assertEqual(self.role.id, user_roles[0].id)
