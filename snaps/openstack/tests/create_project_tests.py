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

from keystoneclient.exceptions import BadRequest

from snaps.config.security_group import SecurityGroupConfig
from snaps.config.user import UserConfig
from snaps.config.project import ProjectConfigError, ProjectConfig
from snaps.domain.project import ComputeQuotas, NetworkQuotas
from snaps.openstack.create_project import (
    OpenStackProject, ProjectSettings)
from snaps.openstack.create_security_group import OpenStackSecurityGroup
from snaps.openstack.create_user import OpenStackUser
from snaps.openstack.tests.os_source_file_test import OSComponentTestCase
from snaps.openstack.utils import keystone_utils, nova_utils, neutron_utils

__author__ = 'spisarski'


class ProjectSettingsUnitTests(unittest.TestCase):
    """
    Tests the construction of the ProjectSettings class
    """

    def test_no_params(self):
        with self.assertRaises(ProjectConfigError):
            ProjectSettings()

    def test_empty_config(self):
        with self.assertRaises(ProjectConfigError):
            ProjectSettings(**dict())

    def test_name_only(self):
        settings = ProjectSettings(name='foo')
        self.assertEqual('foo', settings.name)
        self.assertEqual('Default', settings.domain_name)
        self.assertIsNone(settings.description)
        self.assertTrue(settings.enabled)
        self.assertEqual(list(), settings.users)

    def test_config_with_name_only(self):
        settings = ProjectSettings(**{'name': 'foo'})
        self.assertEqual('foo', settings.name)
        self.assertEqual('Default', settings.domain_name)
        self.assertIsNone(settings.description)
        self.assertTrue(settings.enabled)
        self.assertEqual(list(), settings.users)

    def test_all(self):
        users = ['test1', 'test2']
        settings = ProjectSettings(
            name='foo', domain='bar', description='foobar', enabled=False,
            users=users)
        self.assertEqual('foo', settings.name)
        self.assertEqual('bar', settings.domain_name)
        self.assertEqual('foobar', settings.description)
        self.assertFalse(settings.enabled)
        self.assertEqual(users, settings.users)

    def test_config_all(self):
        users = ['test1', 'test2']
        settings = ProjectSettings(
            **{'name': 'foo', 'domain': 'bar', 'description': 'foobar',
               'enabled': False, 'users': users})
        self.assertEqual('foo', settings.name)
        self.assertEqual('bar', settings.domain_name)
        self.assertEqual('foobar', settings.description)
        self.assertFalse(settings.enabled)
        self.assertEqual(users, settings.users)


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
        self.project_settings = ProjectConfig(
            name=guid + '-name',
            domain=self.os_creds.project_domain_name)

        self.keystone = keystone_utils.keystone_client(
            self.os_creds, self.os_session)

        # Initialize for cleanup
        self.project_creator = None

    def tearDown(self):
        """
        Cleans the image and downloaded image file
        """
        if self.project_creator:
            self.project_creator.clean()

        super(self.__class__, self).__clean__()

    def test_create_project_bad_domain(self):
        """
        Tests the creation of an OpenStack project with an invalid domain
        value. This test will not do anything with a keystone v2.0 client.
        """
        if self.keystone.version != keystone_utils.V2_VERSION_STR:
            self.project_settings.domain_name = 'foo'
            self.project_creator = OpenStackProject(self.os_creds,
                                                    self.project_settings)

            with self.assertRaises(BadRequest):
                self.project_creator.create()

    def test_create_project(self):
        """
        Tests the creation of an OpenStack project.
        """
        self.project_creator = OpenStackProject(self.os_creds,
                                                self.project_settings)
        created_project = self.project_creator.create()
        self.assertIsNotNone(created_project)

        retrieved_project = keystone_utils.get_project(
            keystone=self.keystone, project_settings=self.project_settings)
        self.assertIsNotNone(retrieved_project)
        self.assertEqual(created_project, retrieved_project)
        self.assertTrue(validate_project(self.keystone, self.project_settings,
                                         created_project))

    def test_create_project_quota_override(self):
        """
        Tests the creation of an OpenStack project with new quotas.
        """
        quotas = {
            'cores': 4, 'instances': 5, 'injected_files': 6,
            'injected_file_content_bytes': 60000, 'ram': 70000, 'fixed_ips': 7,
            'key_pairs': 8}
        self.project_settings.quotas = quotas
        self.project_creator = OpenStackProject(self.os_creds,
                                                self.project_settings)
        created_project = self.project_creator.create()
        self.assertIsNotNone(created_project)

        retrieved_project = keystone_utils.get_project(
            keystone=self.keystone, project_settings=self.project_settings)
        self.assertIsNotNone(retrieved_project)
        self.assertEqual(created_project, retrieved_project)
        self.assertTrue(validate_project(self.keystone, self.project_settings,
                                         created_project))

        nova = nova_utils.nova_client(self.os_creds, self.os_session)
        new_quotas = nova_utils.get_compute_quotas(nova, created_project.id)

        self.assertEqual(4, new_quotas.cores)
        self.assertEqual(5, new_quotas.instances)
        self.assertEqual(6, new_quotas.injected_files)
        self.assertEqual(60000, new_quotas.injected_file_content_bytes)
        self.assertEqual(70000, new_quotas.ram)
        self.assertEqual(7, new_quotas.fixed_ips)
        self.assertEqual(8, new_quotas.key_pairs)

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
            keystone=self.keystone, project_settings=self.project_settings)
        self.assertIsNotNone(retrieved_project)
        self.assertEqual(created_project, retrieved_project)

        project2 = OpenStackProject(self.os_creds,
                                    self.project_settings).create()
        self.assertEqual(retrieved_project, project2)
        self.assertTrue(validate_project(self.keystone, self.project_settings,
                                         created_project))

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

        self.assertTrue(validate_project(self.keystone, self.project_settings,
                                         created_project))

    def test_update_quotas(self):
        """
        Tests the creation of an OpenStack project where the quotas get
        updated.
        """
        self.project_creator = OpenStackProject(self.os_creds,
                                                self.project_settings)
        created_project = self.project_creator.create()
        self.assertIsNotNone(created_project)

        retrieved_project = keystone_utils.get_project(
            keystone=self.keystone, project_settings=self.project_settings)
        self.assertIsNotNone(retrieved_project)
        self.assertEqual(created_project, retrieved_project)
        self.assertTrue(validate_project(self.keystone, self.project_settings,
                                         created_project))

        update_compute_quotas = ComputeQuotas(
            **{'metadata_items': 64, 'cores': 5, 'instances': 5,
               'injected_files': 3, 'injected_file_content_bytes': 5120,
               'ram': 25600, 'fixed_ips': 100, 'key_pairs': 50})
        self.project_creator.update_compute_quotas(update_compute_quotas)

        update_network_quotas = NetworkQuotas(
            **{'security_group': 5, 'security_group_rule': 50,
               'floatingip': 25, 'network': 5, 'port': 25, 'router': 6,
               'subnet': 7})
        self.project_creator.update_network_quotas(update_network_quotas)

        self.assertEqual(update_compute_quotas,
                         self.project_creator.get_compute_quotas())
        self.assertEqual(update_network_quotas,
                         self.project_creator.get_network_quotas())

        nova = nova_utils.nova_client(self.os_creds, self.os_session)
        new_compute_quotas = nova_utils.get_compute_quotas(
            nova, self.project_creator.get_project().id)
        self.assertEqual(update_compute_quotas, new_compute_quotas)

        neutron = neutron_utils.neutron_client(self.os_creds, self.os_session)
        new_network_quotas = neutron_utils.get_network_quotas(
            neutron, self.project_creator.get_project().id)
        self.assertEqual(update_network_quotas, new_network_quotas)


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
        self.project_settings = ProjectConfig(
            name=self.guid + '-name',
            domain=self.os_creds.project_domain_name)

        self.keystone = keystone_utils.keystone_client(
            self.os_creds, self.os_session)

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

        super(self.__class__, self).__clean__()

    def test_create_project_sec_grp_one_user(self):
        """
        Tests the creation of an OpenStack object to a project with a new users
        and to create a security group
        """
        self.project_creator = OpenStackProject(self.os_creds,
                                                self.project_settings)
        created_project = self.project_creator.create()
        self.assertIsNotNone(created_project)

        user_creator = OpenStackUser(
            self.os_creds, UserConfig(
                name=self.guid + '-user',
                password=self.guid,
                roles={'admin':  self.project_settings.name},
                domain_name=self.os_creds.user_domain_name))
        self.project_creator.assoc_user(user_creator.create())
        self.user_creators.append(user_creator)

        sec_grp_os_creds = user_creator.get_os_creds(
            self.project_creator.get_project().name)
        sec_grp_creator = OpenStackSecurityGroup(
            sec_grp_os_creds, SecurityGroupConfig(
                name=self.guid + '-name', description='hello group'))
        sec_grp = sec_grp_creator.create()
        self.assertIsNotNone(sec_grp)
        self.sec_grp_creators.append(sec_grp_creator)

        self.assertEqual(self.project_creator.get_project().id,
                         sec_grp.project_id)

    def test_create_project_sec_grp_two_users(self):
        """
        Tests the creation of an OpenStack object to a project with two new
        users and use each user to create a security group
        """
        self.project_creator = OpenStackProject(self.os_creds,
                                                self.project_settings)
        created_project = self.project_creator.create()
        self.assertIsNotNone(created_project)

        user_creator_1 = OpenStackUser(
            self.os_creds, UserConfig(
                name=self.guid + '-user1', password=self.guid,
                roles={'admin': self.project_settings.name},
                domain_name=self.os_creds.user_domain_name))
        self.project_creator.assoc_user(user_creator_1.create())
        self.user_creators.append(user_creator_1)

        user_creator_2 = OpenStackUser(
            self.os_creds, UserConfig(
                name=self.guid + '-user2', password=self.guid,
                roles={'admin': self.project_settings.name},
                domain_name=self.os_creds.user_domain_name))
        self.project_creator.assoc_user(user_creator_2.create())
        self.user_creators.append(user_creator_2)

        ctr = 0
        for user_creator in self.user_creators:
            ctr += 1
            sec_grp_os_creds = user_creator.get_os_creds(
                self.project_creator.get_project().name)

            sec_grp_creator = OpenStackSecurityGroup(
                sec_grp_os_creds,
                SecurityGroupConfig(
                    name=self.guid + '-name', description='hello group'))
            sec_grp = sec_grp_creator.create()
            self.assertIsNotNone(sec_grp)
            self.sec_grp_creators.append(sec_grp_creator)

            self.assertEqual(self.project_creator.get_project().id,
                             sec_grp.project_id)


def validate_project(keystone, project_settings, project):
    """
    Validates that the project_settings used to create the project have been
    properly set
    :param keystone: the keystone client for version checking
    :param project_settings: the settings used to create the project
    :param project: the SNAPS-OO Project domain object
    :return: T/F
    """
    if keystone.version == keystone_utils.V2_VERSION_STR:
        return project_settings.name == project.name
    else:
        domain = keystone_utils.get_domain_by_id(keystone, project.domain_id)
        return (project_settings.name == project.name and
                project_settings.domain_name == domain.name)
