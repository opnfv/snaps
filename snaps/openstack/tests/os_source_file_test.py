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
import pkg_resources
import uuid
import unittest

from snaps import file_utils
from snaps.config.project import ProjectConfig
from snaps.config.user import UserConfig
from snaps.openstack.tests import openstack_tests
from snaps.openstack.utils import deploy_utils, keystone_utils


dev_os_env_file = pkg_resources.resource_filename(
    'snaps.openstack.tests.conf', 'os_env.yaml')


class OSComponentTestCase(unittest.TestCase):

    def __init__(self, method_name='runTest', os_creds=None, ext_net_name=None,
                 image_metadata=None, log_level=logging.DEBUG):
        """
        Super for test classes requiring a connection to OpenStack
        :param method_name: default 'runTest'
        :param os_creds: the OSCreds object, when null it searches for the file
                         in the package snaps.openstack.tests.conf.os_env.yaml
        :param ext_net_name: the name of the external network that is used for
                             creating routers for floating IPs
        :param image_metadata: ability to override images being used in the
                               tests (see examples/image-metadata)
        :param log_level: the logging level of your test run (default DEBUG)
        """
        super(OSComponentTestCase, self).__init__(method_name)

        logging.basicConfig(level=log_level)

        if os_creds:
            self.os_creds = os_creds
        else:
            self.os_creds = openstack_tests.get_credentials(
                dev_os_env_file=dev_os_env_file)

        self.os_session = keystone_utils.keystone_session(self.os_creds)
        self.ext_net_name = ext_net_name

        if not self.ext_net_name and file_utils.file_exists(dev_os_env_file):
            test_conf = file_utils.read_yaml(dev_os_env_file)
            self.ext_net_name = test_conf.get('ext_net')

        self.image_metadata = image_metadata

    @staticmethod
    def parameterize(testcase_klass, os_creds, ext_net_name,
                     image_metadata=None, log_level=logging.DEBUG):
        """ Create a suite containing all tests taken from the given
            subclass, passing them the parameter 'param'.
        """
        test_loader = unittest.TestLoader()
        test_names = test_loader.getTestCaseNames(testcase_klass)
        suite = unittest.TestSuite()
        for name in test_names:
            suite.addTest(testcase_klass(name, os_creds, ext_net_name,
                                         image_metadata, log_level))
        return suite

    def __clean__(self):
        """
        Cleans up keystone session.
        """
        if self.os_session:
            keystone_utils.close_session(self.os_session)


class OSIntegrationTestCase(OSComponentTestCase):

    def __init__(self, method_name='runTest', os_creds=None, ext_net_name=None,
                 use_keystone=True, flavor_metadata=None, image_metadata=None,
                 netconf_override=None, log_level=logging.DEBUG):
        """
        Super for integration tests requiring a connection to OpenStack
        :param method_name: default 'runTest'
        :param os_creds: the OSCreds object, when null it searches for the file
                         in the package snaps.openstack.tests.conf.os_env.yaml
        :param ext_net_name: the name of the external network that is used for
                             creating routers for floating IPs
        :param use_keystone: when true, these tests will create a new
                             user/project under which to run the test
        :param image_metadata: dict() containing the URLs for the disk, kernel,
                               and ramdisk images when multi-part images are
                               required. See below for a simple example
        image_metadata={'disk_url': '{URI}/cirros-0.3.4-x86_64-disk.img',
                        'kernel_url': '{URI}/cirros-0.3.4-x86_64-kernel',
                        'ramdisk_url': '{URI}/cirros-0.3.4-x86_64-initramfs'})
        :param flavor_metadata: dict() to be sent directly into the Nova client
                                generally used for page sizes
        :param netconf_override: dict() containing the configured network_type,
                               physical_network and segmentation_id
        :param log_level: the logging level of your test run (default DEBUG)
        """
        super(OSIntegrationTestCase, self).__init__(
            method_name=method_name, os_creds=os_creds,
            ext_net_name=ext_net_name, image_metadata=image_metadata,
            log_level=log_level)
        self.netconf_override = netconf_override
        self.use_keystone = use_keystone
        self.keystone = None
        self.flavor_metadata = flavor_metadata
        self.user_roles = None

    @staticmethod
    def parameterize(testcase_klass, os_creds, ext_net_name,
                     use_keystone=True, flavor_metadata=None,
                     image_metadata=None, netconf_override=None,
                     log_level=logging.DEBUG):
        """
        Create a suite containing all tests taken from the given
        subclass, passing them the parameter 'param'.
        """
        test_loader = unittest.TestLoader()
        test_names = test_loader.getTestCaseNames(testcase_klass)
        suite = unittest.TestSuite()
        for name in test_names:
            suite.addTest(testcase_klass(name, os_creds, ext_net_name,
                                         use_keystone, flavor_metadata,
                                         image_metadata, netconf_override,
                                         log_level))
        return suite

    """
    Super for test classes that should be run within their own project/tenant
    as they can run for quite some time
    """
    def __start__(self):
        """
        Creates a project and user to be leveraged by subclass test methods. If
        implementing class uses this method, it must call __clean__() else you
        will be left with unwanted users and tenants
        """
        self.project_creator = None
        self.user_creator = None
        self.admin_os_creds = self.os_creds
        self.admin_os_session = self.os_session
        self.keystone = keystone_utils.keystone_client(
            self.admin_os_creds, self.admin_os_session)

        if self.use_keystone:
            guid = self.__class__.__name__ + '-' + str(uuid.uuid4())[:-19]
            project_name = guid + '-proj'
            self.project_creator = deploy_utils.create_project(
                self.admin_os_creds, ProjectConfig(
                    name=project_name,
                    domain=self.admin_os_creds.project_domain_name))

            # Set by implementing class for setting the user's roles
            roles = dict()
            if self.user_roles:
                for user_role in self.user_roles:
                    roles[user_role] = project_name

            self.user_creator = deploy_utils.create_user(
                self.admin_os_creds, UserConfig(
                    name=guid + '-user', password=guid,
                    project_name=project_name, roles=roles,
                    domain_name=self.admin_os_creds.user_domain_name))

            self.os_creds = self.user_creator.get_os_creds(
                self.project_creator.project_settings.name)
            self.os_session = keystone_utils.keystone_session(self.os_creds)

            # add user to project
            self.project_creator.assoc_user(self.user_creator.get_user())

    def __clean__(self):
        """
        Cleans up test user and project.
        Must be called at the end of child classes tearDown() if __start__() is
        called during setUp() else these objects will persist after the test is
        run
        """
        if self.project_creator:
            self.project_creator.clean()

        if self.user_creator:
            self.user_creator.clean()

        if self.admin_os_session:
            keystone_utils.close_session(self.admin_os_session)

        super(OSIntegrationTestCase, self).__clean__()
