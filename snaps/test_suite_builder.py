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
import unittest

from snaps.openstack.utils.tests.glance_utils_tests import GlanceSmokeTests, GlanceUtilsTests
from snaps.openstack.tests.create_flavor_tests import CreateFlavorTests
from snaps.tests.file_utils_tests import FileUtilsTests
from snaps.openstack.tests.create_security_group_tests import CreateSecurityGroupTests, \
    SecurityGroupRuleSettingsUnitTests, SecurityGroupSettingsUnitTests
from snaps.openstack.tests.create_project_tests import CreateProjectSuccessTests, ProjectSettingsUnitTests, \
    CreateProjectUserTests
from snaps.openstack.tests.create_user_tests import UserSettingsUnitTests, CreateUserSuccessTests
from snaps.openstack.utils.tests.keystone_utils_tests import KeystoneSmokeTests, KeystoneUtilsTests
from snaps.openstack.utils.tests.neutron_utils_tests import NeutronSmokeTests, NeutronUtilsNetworkTests, \
    NeutronUtilsSubnetTests, NeutronUtilsRouterTests, NeutronUtilsSecurityGroupTests
from snaps.openstack.tests.create_image_tests import CreateImageSuccessTests, CreateImageNegativeTests, \
    ImageSettingsUnitTests, CreateMultiPartImageTests
from snaps.openstack.tests.create_keypairs_tests import CreateKeypairsTests, KeypairSettingsUnitTests
from snaps.openstack.tests.create_network_tests import CreateNetworkSuccessTests, NetworkSettingsUnitTests, \
    PortSettingsUnitTests, SubnetSettingsUnitTests, CreateNetworkTypeTests
from snaps.openstack.tests.create_router_tests import CreateRouterSuccessTests, CreateRouterNegativeTests
from snaps.openstack.tests.create_instance_tests import CreateInstanceSingleNetworkTests, \
    CreateInstancePubPrivNetTests, CreateInstanceOnComputeHost, CreateInstanceSimpleTests, \
    FloatingIpSettingsUnitTests, InstanceSecurityGroupTests, VmInstanceSettingsUnitTests, \
    CreateInstancePortManipulationTests, SimpleHealthCheck, CreateInstanceFromThreePartImage
from snaps.provisioning.tests.ansible_utils_tests import AnsibleProvisioningTests
from snaps.openstack.tests.os_source_file_test import OSComponentTestCase, OSIntegrationTestCase
from snaps.openstack.utils.tests.nova_utils_tests import NovaSmokeTests, NovaUtilsKeypairTests, NovaUtilsFlavorTests

__author__ = 'spisarski'


def add_unit_tests(suite):
    """
    Adds tests that do not require external resources
    :param suite: the unittest.TestSuite object to which to add the tests
    :return: None as the tests will be adding to the 'suite' parameter object
    """
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(FileUtilsTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(SecurityGroupRuleSettingsUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(SecurityGroupSettingsUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(ImageSettingsUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(KeypairSettingsUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(UserSettingsUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(ProjectSettingsUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(NetworkSettingsUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(SubnetSettingsUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(PortSettingsUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(FloatingIpSettingsUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(VmInstanceSettingsUnitTests))


def add_openstack_client_tests(suite, source_filename, ext_net_name, use_keystone=True, http_proxy_str=None,
                               log_level=logging.INFO):
    """
    Adds tests written to exercise OpenStack client retrieval
    :param suite: the unittest.TestSuite object to which to add the tests
    :param source_filename: the OpenStack credentials filename
    :param ext_net_name: the name of an external network on the cloud under test
    :param http_proxy_str: <host>:<port> of the proxy server (optional)
    :param use_keystone: when True, tests requiring direct access to Keystone are added as these need to be running on
                         a host that has access to the cloud's private network
    :param log_level: the logging level
    :return: None as the tests will be adding to the 'suite' parameter object
    """
    # Basic connection tests
    suite.addTest(OSComponentTestCase.parameterize(GlanceSmokeTests, source_filename, ext_net_name,
                                                   http_proxy_str=http_proxy_str, log_level=log_level))

    if use_keystone:
        suite.addTest(OSComponentTestCase.parameterize(KeystoneSmokeTests, source_filename, ext_net_name,
                                                       http_proxy_str=http_proxy_str, log_level=log_level))

    suite.addTest(OSComponentTestCase.parameterize(NeutronSmokeTests, source_filename, ext_net_name,
                                                   http_proxy_str=http_proxy_str, log_level=log_level))
    suite.addTest(OSComponentTestCase.parameterize(NovaSmokeTests, source_filename, ext_net_name,
                                                   http_proxy_str=http_proxy_str, log_level=log_level))


def add_openstack_api_tests(suite, source_filename, ext_net_name, http_proxy_str=None, use_keystone=True,
                            log_level=logging.INFO):
    """
    Adds tests written to exercise all existing OpenStack APIs
    :param suite: the unittest.TestSuite object to which to add the tests
    :param source_filename: the OpenStack credentials filename
    :param ext_net_name: the name of an external network on the cloud under test
    :param http_proxy_str: <host>:<port> of the proxy server (optional)
    :param use_keystone: when True, tests requiring direct access to Keystone are added as these need to be running on
                         a host that has access to the cloud's private network
    :param log_level: the logging level
    :return: None as the tests will be adding to the 'suite' parameter object
    """
    # Tests the OpenStack API calls
    if use_keystone:
        suite.addTest(OSComponentTestCase.parameterize(KeystoneUtilsTests, source_filename, ext_net_name,
                                                       http_proxy_str=http_proxy_str, log_level=log_level))
        suite.addTest(OSComponentTestCase.parameterize(CreateUserSuccessTests, source_filename, ext_net_name,
                                                       http_proxy_str=http_proxy_str, log_level=log_level))
        suite.addTest(OSComponentTestCase.parameterize(CreateProjectSuccessTests, source_filename, ext_net_name,
                                                       http_proxy_str=http_proxy_str, log_level=log_level))
        suite.addTest(OSComponentTestCase.parameterize(CreateProjectUserTests, source_filename, ext_net_name,
                                                       http_proxy_str=http_proxy_str, log_level=log_level))

    suite.addTest(OSComponentTestCase.parameterize(GlanceUtilsTests, source_filename, ext_net_name,
                                                   http_proxy_str=http_proxy_str, log_level=log_level))
    suite.addTest(OSComponentTestCase.parameterize(NeutronUtilsNetworkTests, source_filename, ext_net_name,
                                                   http_proxy_str=http_proxy_str, log_level=log_level))
    suite.addTest(OSComponentTestCase.parameterize(NeutronUtilsSubnetTests, source_filename, ext_net_name,
                                                   http_proxy_str=http_proxy_str, log_level=log_level))
    suite.addTest(OSComponentTestCase.parameterize(NeutronUtilsRouterTests, source_filename, ext_net_name,
                                                   http_proxy_str=http_proxy_str, log_level=log_level))
    suite.addTest(OSComponentTestCase.parameterize(NeutronUtilsSecurityGroupTests, source_filename, ext_net_name,
                                                   http_proxy_str=http_proxy_str, log_level=log_level))
    suite.addTest(OSComponentTestCase.parameterize(NovaUtilsKeypairTests, source_filename, ext_net_name,
                                                   http_proxy_str=http_proxy_str, log_level=log_level))
    suite.addTest(OSComponentTestCase.parameterize(NovaUtilsFlavorTests, source_filename, ext_net_name,
                                                   http_proxy_str=http_proxy_str, log_level=log_level))
    suite.addTest(OSComponentTestCase.parameterize(CreateFlavorTests, source_filename, ext_net_name,
                                                   http_proxy_str=http_proxy_str, log_level=log_level))


def add_openstack_integration_tests(suite, source_filename, ext_net_name, proxy_settings=None, ssh_proxy_cmd=None,
                                    use_keystone=True, use_floating_ips=True, log_level=logging.INFO):
    """
    Adds tests written to exercise all long-running OpenStack integration tests meaning they will be creating VM
    instances and potentially performing some SSH functions through floating IPs
    :param suite: the unittest.TestSuite object to which to add the tests
    :param source_filename: the OpenStack credentials filename
    :param ext_net_name: the name of an external network on the cloud under test
    :param proxy_settings: <host>:<port> of the proxy server (optional)
    :param ssh_proxy_cmd: the command your environment requires for creating ssh connections through a proxy
    :param use_keystone: when True, tests requiring direct access to Keystone are added as these need to be running on
                         a host that has access to the cloud's private network
    :param use_floating_ips: when true, all tests requiring Floating IPs will be added to the suite
    :param log_level: the logging level
    :return: None as the tests will be adding to the 'suite' parameter object
    """
    # Tests the OpenStack API calls via a creator. If use_keystone, objects will be created with a custom user
    # and project

    # Creator Object tests
    suite.addTest(OSIntegrationTestCase.parameterize(CreateSecurityGroupTests, source_filename, ext_net_name,
                                                     http_proxy_str=proxy_settings, use_keystone=use_keystone,
                                                     log_level=log_level))
    suite.addTest(OSIntegrationTestCase.parameterize(CreateImageSuccessTests, source_filename, ext_net_name,
                                                     http_proxy_str=proxy_settings, use_keystone=use_keystone,
                                                     log_level=log_level))
    suite.addTest(OSIntegrationTestCase.parameterize(CreateImageNegativeTests, source_filename, ext_net_name,
                                                     http_proxy_str=proxy_settings, use_keystone=use_keystone,
                                                     log_level=log_level))
    suite.addTest(OSIntegrationTestCase.parameterize(CreateMultiPartImageTests, source_filename, ext_net_name,
                                                     http_proxy_str=proxy_settings, use_keystone=use_keystone,
                                                     log_level=log_level))
    suite.addTest(OSIntegrationTestCase.parameterize(CreateKeypairsTests, source_filename, ext_net_name,
                                                     http_proxy_str=proxy_settings, use_keystone=use_keystone,
                                                     log_level=log_level))
    suite.addTest(OSIntegrationTestCase.parameterize(CreateNetworkSuccessTests, source_filename, ext_net_name,
                                                     http_proxy_str=proxy_settings, use_keystone=use_keystone,
                                                     log_level=log_level))
    suite.addTest(OSComponentTestCase.parameterize(CreateNetworkTypeTests, source_filename, ext_net_name,
                                                   http_proxy_str=proxy_settings, log_level=log_level))
    suite.addTest(OSIntegrationTestCase.parameterize(CreateRouterSuccessTests, source_filename, ext_net_name,
                                                     http_proxy_str=proxy_settings, use_keystone=use_keystone,
                                                     log_level=log_level))
    suite.addTest(OSIntegrationTestCase.parameterize(CreateRouterNegativeTests, source_filename, ext_net_name,
                                                     http_proxy_str=proxy_settings, use_keystone=use_keystone,
                                                     log_level=log_level))

    # VM Instances
    suite.addTest(OSIntegrationTestCase.parameterize(SimpleHealthCheck, source_filename, ext_net_name,
                                                     http_proxy_str=proxy_settings, use_keystone=use_keystone,
                                                     log_level=log_level))
    suite.addTest(OSIntegrationTestCase.parameterize(CreateInstanceSimpleTests, source_filename, ext_net_name,
                                                     http_proxy_str=proxy_settings, use_keystone=use_keystone,
                                                     log_level=log_level))
    suite.addTest(OSIntegrationTestCase.parameterize(CreateInstancePortManipulationTests, source_filename, ext_net_name,
                                                     http_proxy_str=proxy_settings, use_keystone=use_keystone,
                                                     log_level=log_level))
    suite.addTest(OSIntegrationTestCase.parameterize(InstanceSecurityGroupTests, source_filename, ext_net_name,
                                                     http_proxy_str=proxy_settings, use_keystone=use_keystone,
                                                     log_level=log_level))
    suite.addTest(OSComponentTestCase.parameterize(CreateInstanceOnComputeHost, source_filename, ext_net_name,
                                                   http_proxy_str=proxy_settings, log_level=log_level))
    suite.addTest(OSComponentTestCase.parameterize(CreateInstanceFromThreePartImage, source_filename, ext_net_name,
                                                   http_proxy_str=proxy_settings, log_level=log_level))

    if use_floating_ips:
        suite.addTest(OSIntegrationTestCase.parameterize(CreateInstanceSingleNetworkTests, source_filename,
                                                         ext_net_name, http_proxy_str=proxy_settings,
                                                         ssh_proxy_cmd=ssh_proxy_cmd, use_keystone=use_keystone,
                                                         log_level=log_level))
        suite.addTest(OSIntegrationTestCase.parameterize(CreateInstancePubPrivNetTests, source_filename,
                                                         ext_net_name, http_proxy_str=proxy_settings,
                                                         ssh_proxy_cmd=ssh_proxy_cmd, use_keystone=use_keystone,
                                                         log_level=log_level))
        suite.addTest(OSIntegrationTestCase.parameterize(AnsibleProvisioningTests, source_filename,
                                                         ext_net_name, http_proxy_str=proxy_settings,
                                                         ssh_proxy_cmd=ssh_proxy_cmd, use_keystone=use_keystone,
                                                         log_level=log_level))
