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

from snaps.openstack.create_project import OpenStackProject, ProjectSettings
from snaps.openstack.create_security_group import OpenStackSecurityGroup
from snaps.openstack.create_security_group import SecurityGroupSettings
from snaps.openstack.create_user import OpenStackUser
from snaps.openstack.create_user import UserSettings
from snaps.openstack.tests.os_source_file_test import OSComponentTestCase
from snaps.openstack.utils import keystone_utils

__author__ = 'spisarski'


class ProjectSettingsUnitTests(unittest.TestCase):
    """
    Tests the construction of the ProjectSettings class
    """

    def test_no_params(self):
        with self.assertRaises(Exception):
            ProjectSettings()

    def test_empty_config(self):
        with self.assertRaises(Exception):
            ProjectSettings(**dict())

    def test_name_only(self):
        settings = ProjectSettings(name='foo')
        self.assertEqual('foo', settings.name)
        self.assertEqual('default', settings.domain)
        self.assertIsNone(settings.description)
        self.assertTrue(settings.enabled)

    def test_config_with_name_only(self):
        settings = ProjectSettings(**{'name': 'foo'})
        self.assertEqual('foo', settings.name)
        self.assertEqual('default', settings.domain)
        self.assertIsNone(settings.description)
        self.assertTrue(settings.enabled)

    def test_all(self):
        settings = ProjectSettings(name='foo', domain='bar',
                                   description='foobar', enabled=False)
        self.assertEqual('foo', settings.name)
        self.assertEqual('bar', settings.domain)
        self.assertEqual('foobar', settings.description)
        self.assertFalse(settings.enabled)

    def test_config_all(self):
        settings = ProjectSettings(
            **{'name': 'foo', 'domain': 'bar', 'description': 'foobar',
               'enabled': False})
        self.assertEqual('foo', settings.name)
        self.assertEqual('bar', settings.domain)
        self.assertEqual('foobar', settings.description)
        self.assertFalse(settings.enabled)


class CreateProjectSuccessTests(OSComponentTestCase):
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
        self.project_settings = ProjectSettings(name=guid + '-name')

        self.keystone = keystone_utils.keystone_client(self.os_creds)

        # Initialize for cleanup
        self.project_creator = None

    def tearDown(self):
        """
        Cleans the image and downloaded image file
        """
        if self.project_creator:
            self.project_creator.clean()

    def test_create_project(self):
        """
        Tests the creation of an OpenStack project.
        """
        self.project_creator = OpenStackProject(self.os_creds,
                                                self.project_settings)
        created_project = self.project_creator.create()
        self.assertIsNotNone(created_project)

        retrieved_project = keystone_utils.get_project(
            keystone=self.keystone, project_name=self.project_settings.name)
        self.assertIsNotNone(retrieved_project)
        self.assertEqual(created_project, retrieved_project)

    def test_create_project_2x(self):
        """
        Tests the creation of an OpenStack project twice to ensure it only
        creates one.
        """
        self.project_creator = OpenStackProject(self.os_creds,
                                                self.project_settings)
        created_project = self.project_creator.create()
        self.assertIsNotNone(created_project)

        retrieved_project = keystone_utils.get_project(
            keystone=self.keystone, project_name=self.project_settings.name)
        self.assertIsNotNone(retrieved_project)
        self.assertEqual(created_project, retrieved_project)

        project2 = OpenStackProject(self.os_creds,
                                    self.project_settings).create()
        self.assertEqual(retrieved_project, project2)

    def test_create_delete_project(self):
        """
        Tests the creation of an OpenStack project, it's deletion, then cleanup
        """
        # Create Image
        self.project_creator = OpenStackProject(self.os_creds,
                                                self.project_settings)
        created_project = self.project_creator.create()
        self.assertIsNotNone(created_project)

        keystone_utils.delete_project(self.keystone, created_project)

        self.project_creator.clean()

        self.assertIsNone(self.project_creator.get_project())

        # TODO - Expand tests


class CreateProjectUserTests(OSComponentTestCase):
    """
    Test for the CreateImage class defined in create_image.py
    """

    def setUp(self):
        """
        Instantiates the CreateImage object that is responsible for downloading
        and creating an OS image file within OpenStack
        """
        guid = str(uuid.uuid4())[:-19]
        self.guid = self.__class__.__name__ + '-' + guid
        self.project_settings = ProjectSettings(name=self.guid + '-name')

        self.keystone = keystone_utils.keystone_client(self.os_creds)

        # Initialize for cleanup
        self.project_creator = None
        self.user_creators = list()

        self.sec_grp_creators = list()

    def tearDown(self):
        """
        Cleans the image and downloaded image file
        """
        for sec_grp_creator in self.sec_grp_creators:
            sec_grp_creator.clean()

        for user_creator in self.user_creators:
            user_creator.clean()

        if self.project_creator:
            self.project_creator.clean()

    def test_create_project_sec_grp_one_user(self):
        """
        Tests the creation of an OpenStack object to a project with a new users
        and to create a security group
        """
        self.project_creator = OpenStackProject(self.os_creds,
                                                self.project_settings)
        created_project = self.project_creator.create()
        self.assertIsNotNone(created_project)

        user_creator = OpenStackUser(self.os_creds,
                                     UserSettings(name=self.guid + '-user',
                                                  password=self.guid))
        self.project_creator.assoc_user(user_creator.create())
        self.user_creators.append(user_creator)

        sec_grp_os_creds = user_creator.get_os_creds(
            self.project_creator.get_project().name)
        sec_grp_creator = OpenStackSecurityGroup(
            sec_grp_os_creds, SecurityGroupSettings(name=self.guid + '-name',
                                                    description='hello group'))
        sec_grp = sec_grp_creator.create()
        self.assertIsNotNone(sec_grp)
        self.sec_grp_creators.append(sec_grp_creator)

        if 'tenant_id' in sec_grp['security_group']:
            self.assertEqual(self.project_creator.get_project().id,
                             sec_grp['security_group']['tenant_id'])
        elif 'project_id' in sec_grp['security_group']:
            self.assertEqual(self.project_creator.get_project().id,
                             sec_grp['security_group']['project_id'])
        else:
            self.fail('Cannot locate the project or tenant ID')

    def test_create_project_sec_grp_two_users(self):
        """
        Tests the creation of an OpenStack object to a project with two new
        users and use each user to create a security group
        """
        self.project_creator = OpenStackProject(self.os_creds,
                                                self.project_settings)
        created_project = self.project_creator.create()
        self.assertIsNotNone(created_project)

        user_creator_1 = OpenStackUser(self.os_creds,
                                       UserSettings(name=self.guid + '-user1',
                                                    password=self.guid))
        self.project_creator.assoc_user(user_creator_1.create())
        self.user_creators.append(user_creator_1)

        user_creator_2 = OpenStackUser(self.os_creds,
                                       UserSettings(name=self.guid + '-user2',
                                                    password=self.guid))
        self.project_creator.assoc_user(user_creator_2.create())
        self.user_creators.append(user_creator_2)

        ctr = 0
        for user_creator in self.user_creators:
            ctr += 1
            sec_grp_os_creds = user_creator.get_os_creds(
                self.project_creator.get_project().name)

            sec_grp_creator = OpenStackSecurityGroup(
                sec_grp_os_creds,
                SecurityGroupSettings(name=self.guid + '-name',
                                      description='hello group'))
            sec_grp = sec_grp_creator.create()
            self.assertIsNotNone(sec_grp)
            self.sec_grp_creators.append(sec_grp_creator)

            if 'tenant_id' in sec_grp['security_group']:
                self.assertEqual(self.project_creator.get_project().id,
                                 sec_grp['security_group']['tenant_id'])
            elif 'project_id' in sec_grp['security_group']:
                self.assertEqual(self.project_creator.get_project().id,
                                 sec_grp['security_group']['project_id'])
            else:
                self.fail('Cannot locate the project or tenant ID')
