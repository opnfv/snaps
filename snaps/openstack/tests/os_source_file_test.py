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
import unittest
import uuid

from snaps import file_utils
import openstack_tests
import logging

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# To run these tests from an IDE, the CWD must be set to the python directory of this project
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
from snaps.openstack import create_flavor
from snaps.openstack.create_project import ProjectSettings
from snaps.openstack.create_user import UserSettings
from snaps.openstack.utils import deploy_utils, keystone_utils

dev_os_env_file = 'openstack/tests/conf/os_env.yaml'


class OSComponentTestCase(unittest.TestCase):

    """
    Super for test classes requiring a connection to OpenStack
    """
    def __init__(self, method_name='runTest', os_env_file=None, ext_net_name=None, http_proxy_str=None,
                 ssh_proxy_cmd=None, log_level=logging.DEBUG):
        super(OSComponentTestCase, self).__init__(method_name)

        logging.basicConfig(level=log_level)

        self.os_creds = openstack_tests.get_credentials(os_env_file=os_env_file, proxy_settings_str=http_proxy_str,
                                                        ssh_proxy_cmd=ssh_proxy_cmd, dev_os_env_file=dev_os_env_file)
        self.ext_net_name = ext_net_name

        if not self.ext_net_name and file_utils.file_exists(dev_os_env_file):
            test_conf = file_utils.read_yaml(dev_os_env_file)
            self.ext_net_name = test_conf.get('ext_net')

    @staticmethod
    def parameterize(testcase_klass, os_env_file, ext_net_name, http_proxy_str=None, ssh_proxy_cmd=None,
                     log_level=logging.DEBUG):
        """ Create a suite containing all tests taken from the given
            subclass, passing them the parameter 'param'.
        """
        test_loader = unittest.TestLoader()
        test_names = test_loader.getTestCaseNames(testcase_klass)
        suite = unittest.TestSuite()
        for name in test_names:
            suite.addTest(testcase_klass(name, os_env_file, ext_net_name, http_proxy_str, ssh_proxy_cmd, log_level))
        return suite


class OSIntegrationTestCase(OSComponentTestCase):

    """
    Super for test classes requiring a connection to OpenStack
    """
    def __init__(self, method_name='runTest', os_env_file=None, ext_net_name=None, http_proxy_str=None,
                 ssh_proxy_cmd=None, use_keystone=False, flavor_metadata=create_flavor.DEFAULT_METADATA,
                 log_level=logging.DEBUG):
        super(OSIntegrationTestCase, self).__init__(method_name=method_name, os_env_file=os_env_file,
                                                    ext_net_name=ext_net_name, http_proxy_str=http_proxy_str,
                                                    ssh_proxy_cmd=ssh_proxy_cmd, log_level=log_level)
        self.use_keystone = use_keystone
        self.keystone = None
        self.flavor_metadata = flavor_metadata

    @staticmethod
    def parameterize(testcase_klass, os_env_file, ext_net_name, http_proxy_str=None, ssh_proxy_cmd=None,
                     use_keystone=False, flavor_metadata=create_flavor.DEFAULT_METADATA,
                     log_level=logging.DEBUG):
        """ Create a suite containing all tests taken from the given
            subclass, passing them the parameter 'param'.
        """
        test_loader = unittest.TestLoader()
        test_names = test_loader.getTestCaseNames(testcase_klass)
        suite = unittest.TestSuite()
        for name in test_names:
            suite.addTest(testcase_klass(name, os_env_file, ext_net_name, http_proxy_str, ssh_proxy_cmd, use_keystone,
                                         flavor_metadata, log_level))
        return suite

    """
    Super for test classes that should be run within their own project/tenant as they can run for quite some time
    """
    def __start__(self):
        """
        Creates a project and user to be leveraged by subclass test methods. If implementing class uses this method,
        it must call __clean__() else you will be left with unwanted users and tenants
        """
        self.project_creator = None
        self.user_creator = None
        self.admin_os_creds = self.os_creds
        self.role = None

        if self.use_keystone:
            self.keystone = keystone_utils.keystone_client(self.os_creds)
            guid = self.__class__.__name__ + '-' + str(uuid.uuid4())[:-19]
            project_name = guid + '-proj'
            self.project_creator = deploy_utils.create_project(self.admin_os_creds, ProjectSettings(name=project_name))

            self.user_creator = deploy_utils.create_user(
                self.admin_os_creds, UserSettings(name=guid + '-user', password=guid, project_name=project_name))
            self.os_creds = self.user_creator.get_os_creds(self.project_creator.project_settings.name)

            # add user to project
            self.project_creator.assoc_user(self.user_creator.get_user())

    def __clean__(self):
        """
        Cleans up test user and project.
        Must be called at the end of child classes tearDown() if __start__() is called during setUp() else these
        objects will persist after the test is run
        """
        if self.role:
            keystone_utils.delete_role(self.keystone, self.role)

        if self.project_creator:
            self.project_creator.clean()

        if self.user_creator:
            self.user_creator.clean()
