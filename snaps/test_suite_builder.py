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
import unittest

from snaps.domain.test.flavor_tests import FlavorDomainObjectTests
from snaps.domain.test.image_tests import ImageDomainObjectTests
from snaps.domain.test.keypair_tests import KeypairDomainObjectTests
from snaps.domain.test.network_tests import (
    SecurityGroupDomainObjectTests, SecurityGroupRuleDomainObjectTests,
    PortDomainObjectTests, RouterDomainObjectTests,
    InterfaceRouterDomainObjectTests, NetworkObjectTests, SubnetObjectTests)
from snaps.domain.test.project_tests import ProjectDomainObjectTests
from snaps.domain.test.role_tests import RoleDomainObjectTests
from snaps.domain.test.stack_tests import StackDomainObjectTests
from snaps.domain.test.user_tests import UserDomainObjectTests
from snaps.domain.test.vm_inst_tests import (
    VmInstDomainObjectTests, FloatingIpDomainObjectTests)
from snaps.openstack.tests.conf.os_credentials_tests import (
    ProxySettingsUnitTests, OSCredsUnitTests)
from snaps.openstack.tests.create_flavor_tests import (
    CreateFlavorTests, FlavorSettingsUnitTests)
from snaps.openstack.tests.create_image_tests import (
    CreateImageSuccessTests, CreateImageNegativeTests, ImageSettingsUnitTests,
    CreateMultiPartImageTests)
from snaps.openstack.tests.create_instance_tests import (
    CreateInstanceSingleNetworkTests, CreateInstancePubPrivNetTests,
    CreateInstanceOnComputeHost, CreateInstanceSimpleTests,
    FloatingIpSettingsUnitTests, InstanceSecurityGroupTests,
    VmInstanceSettingsUnitTests, CreateInstancePortManipulationTests,
    SimpleHealthCheck, CreateInstanceFromThreePartImage,
    CreateInstanceMockOfflineTests)
from snaps.openstack.tests.create_keypairs_tests import (
    CreateKeypairsTests, KeypairSettingsUnitTests)
from snaps.openstack.tests.create_network_tests import (
    CreateNetworkSuccessTests, NetworkSettingsUnitTests, PortSettingsUnitTests,
    SubnetSettingsUnitTests, CreateNetworkTypeTests)
from snaps.openstack.tests.create_project_tests import (
    CreateProjectSuccessTests, ProjectSettingsUnitTests,
    CreateProjectUserTests)
from snaps.openstack.tests.create_router_tests import (
    CreateRouterSuccessTests, CreateRouterNegativeTests,
    RouterSettingsUnitTests)
from snaps.openstack.tests.create_security_group_tests import (
    CreateSecurityGroupTests, SecurityGroupRuleSettingsUnitTests,
    SecurityGroupSettingsUnitTests)
from snaps.openstack.tests.create_stack_tests import (
    StackSettingsUnitTests, CreateStackSuccessTests,  CreateStackNegativeTests)
from snaps.openstack.tests.create_user_tests import (
    UserSettingsUnitTests, CreateUserSuccessTests)
from snaps.openstack.tests.os_source_file_test import (
    OSComponentTestCase, OSIntegrationTestCase)
from snaps.openstack.utils.tests.glance_utils_tests import (
    GlanceSmokeTests, GlanceUtilsTests)
from snaps.openstack.utils.tests.heat_utils_tests import (
    HeatUtilsCreateStackTests, HeatSmokeTests)
from snaps.openstack.utils.tests.keystone_utils_tests import (
    KeystoneSmokeTests, KeystoneUtilsTests)
from snaps.openstack.utils.tests.neutron_utils_tests import (
    NeutronSmokeTests, NeutronUtilsNetworkTests, NeutronUtilsSubnetTests,
    NeutronUtilsRouterTests, NeutronUtilsSecurityGroupTests,
    NeutronUtilsFloatingIpTests)
from snaps.openstack.utils.tests.nova_utils_tests import (
    NovaSmokeTests, NovaUtilsKeypairTests, NovaUtilsFlavorTests,
    NovaUtilsInstanceTests)
from snaps.provisioning.tests.ansible_utils_tests import (
    AnsibleProvisioningTests)
from snaps.tests.file_utils_tests import FileUtilsTests

__author__ = 'spisarski'


def add_unit_tests(suite):
    """
    Adds tests that do not require external resources
    :param suite: the unittest.TestSuite object to which to add the tests
    :return: None as the tests will be adding to the 'suite' parameter object
    """
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(FileUtilsTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        SecurityGroupRuleSettingsUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        ProxySettingsUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        OSCredsUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        SecurityGroupSettingsUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        SecurityGroupDomainObjectTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        SecurityGroupRuleDomainObjectTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        ImageSettingsUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        ImageDomainObjectTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        FlavorSettingsUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        FlavorDomainObjectTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        KeypairSettingsUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        KeypairDomainObjectTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        UserSettingsUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        UserDomainObjectTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        ProjectSettingsUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        ProjectDomainObjectTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        RoleDomainObjectTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        NetworkSettingsUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        NetworkObjectTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        SubnetSettingsUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        SubnetObjectTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        PortSettingsUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        PortDomainObjectTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        RouterSettingsUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        RouterDomainObjectTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        InterfaceRouterDomainObjectTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        FloatingIpSettingsUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        VmInstanceSettingsUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        StackDomainObjectTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        StackSettingsUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        VmInstDomainObjectTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        FloatingIpDomainObjectTests))


def add_openstack_client_tests(suite, os_creds, ext_net_name,
                               use_keystone=True, log_level=logging.INFO):
    """
    Adds tests written to exercise OpenStack client retrieval
    :param suite: the unittest.TestSuite object to which to add the tests
    :param os_creds: and instance of OSCreds that holds the credentials
                     required by OpenStack
    :param ext_net_name: the name of an external network on the cloud under
                         test
    :param use_keystone: when True, tests requiring direct access to Keystone
                         are added as these need to be running on a host that
                         has access to the cloud's private network
    :param log_level: the logging level
    :return: None as the tests will be adding to the 'suite' parameter object
    """
    # Basic connection tests
    suite.addTest(
        OSComponentTestCase.parameterize(
            GlanceSmokeTests, os_creds=os_creds, ext_net_name=ext_net_name,
            log_level=log_level))

    if use_keystone:
        suite.addTest(
            OSComponentTestCase.parameterize(
                KeystoneSmokeTests, os_creds=os_creds,
                ext_net_name=ext_net_name, log_level=log_level))

    suite.addTest(
        OSComponentTestCase.parameterize(
            NeutronSmokeTests, os_creds=os_creds, ext_net_name=ext_net_name,
            log_level=log_level))
    suite.addTest(
        OSComponentTestCase.parameterize(
            NovaSmokeTests, os_creds=os_creds, ext_net_name=ext_net_name,
            log_level=log_level))
    suite.addTest(
        OSComponentTestCase.parameterize(
            HeatSmokeTests, os_creds=os_creds, ext_net_name=ext_net_name,
            log_level=log_level))


def add_openstack_api_tests(suite, os_creds, ext_net_name, use_keystone=True,
                            image_metadata=None, log_level=logging.INFO):
    """
    Adds tests written to exercise all existing OpenStack APIs
    :param suite: the unittest.TestSuite object to which to add the tests
    :param os_creds: Instance of OSCreds that holds the credentials
                     required by OpenStack
    :param ext_net_name: the name of an external network on the cloud under
                         test
    :param use_keystone: when True, tests requiring direct access to Keystone
                         are added as these need to be running on a host that
                         has access to the cloud's private network
    :param image_metadata: dict() object containing metadata for creating an
                           image with custom config
                           (see YAML files in examples/image-metadata)
    :param log_level: the logging level
    :return: None as the tests will be adding to the 'suite' parameter object
    """
    # Tests the OpenStack API calls
    if use_keystone:
        suite.addTest(OSComponentTestCase.parameterize(
            KeystoneUtilsTests, os_creds=os_creds, ext_net_name=ext_net_name,
            log_level=log_level))
        suite.addTest(OSComponentTestCase.parameterize(
            CreateUserSuccessTests, os_creds=os_creds,
            ext_net_name=ext_net_name, log_level=log_level))
        suite.addTest(OSComponentTestCase.parameterize(
            CreateProjectSuccessTests, os_creds=os_creds,
            ext_net_name=ext_net_name, log_level=log_level))
        suite.addTest(OSComponentTestCase.parameterize(
            CreateProjectUserTests, os_creds=os_creds,
            ext_net_name=ext_net_name, log_level=log_level))

    suite.addTest(OSComponentTestCase.parameterize(
        GlanceUtilsTests, os_creds=os_creds, ext_net_name=ext_net_name,
        image_metadata=image_metadata,
        log_level=log_level))
    suite.addTest(OSComponentTestCase.parameterize(
        NeutronUtilsNetworkTests, os_creds=os_creds, ext_net_name=ext_net_name,
        log_level=log_level))
    suite.addTest(OSComponentTestCase.parameterize(
        NeutronUtilsSubnetTests, os_creds=os_creds, ext_net_name=ext_net_name,
        log_level=log_level))
    suite.addTest(OSComponentTestCase.parameterize(
        NeutronUtilsRouterTests, os_creds=os_creds, ext_net_name=ext_net_name,
        log_level=log_level))
    suite.addTest(OSComponentTestCase.parameterize(
        NeutronUtilsSecurityGroupTests, os_creds=os_creds,
        ext_net_name=ext_net_name, log_level=log_level))
    suite.addTest(OSComponentTestCase.parameterize(
        NeutronUtilsFloatingIpTests, os_creds=os_creds,
        ext_net_name=ext_net_name, log_level=log_level))
    suite.addTest(OSComponentTestCase.parameterize(
        NovaUtilsKeypairTests, os_creds=os_creds, ext_net_name=ext_net_name,
        log_level=log_level))
    suite.addTest(OSComponentTestCase.parameterize(
        NovaUtilsFlavorTests, os_creds=os_creds, ext_net_name=ext_net_name,
        log_level=log_level))
    suite.addTest(OSComponentTestCase.parameterize(
        NovaUtilsInstanceTests, os_creds=os_creds, ext_net_name=ext_net_name,
        log_level=log_level, image_metadata=image_metadata))
    suite.addTest(OSComponentTestCase.parameterize(
        CreateFlavorTests, os_creds=os_creds, ext_net_name=ext_net_name,
        log_level=log_level))
    suite.addTest(OSComponentTestCase.parameterize(
        HeatUtilsCreateStackTests, os_creds=os_creds,
        ext_net_name=ext_net_name, log_level=log_level,
        image_metadata=image_metadata))


def add_openstack_integration_tests(suite, os_creds, ext_net_name,
                                    use_keystone=True, flavor_metadata=None,
                                    image_metadata=None, use_floating_ips=True,
                                    log_level=logging.INFO):
    """
    Adds tests written to exercise all long-running OpenStack integration tests
    meaning they will be creating VM instances and potentially performing some
    SSH functions through floatingIPs
    :param suite: the unittest.TestSuite object to which to add the tests
    :param os_creds: and instance of OSCreds that holds the credentials
                     required by OpenStack
    :param ext_net_name: the name of an external network on the cloud under
                         test
    :param use_keystone: when True, tests requiring direct access to Keystone
                         are added as these need to be running on a host that
                         has access to the cloud's private network
    :param image_metadata: dict() object containing metadata for creating an
                           image with custom config
                           (see YAML files in examples/image-metadata)
    :param flavor_metadata: dict() object containing the metadata required by
                            your flavor based on your configuration:
                            (i.e. {'hw:mem_page_size': 'large'})
    :param use_floating_ips: when true, all tests requiring Floating IPs will
                             be added to the suite
    :param log_level: the logging level
    :return: None as the tests will be adding to the 'suite' parameter object
    """
    # Tests the OpenStack API calls via a creator. If use_keystone, objects
    # will be created with a custom user and project

    # Creator Object tests
    suite.addTest(OSIntegrationTestCase.parameterize(
        CreateSecurityGroupTests, os_creds=os_creds, ext_net_name=ext_net_name,
        use_keystone=use_keystone,
        flavor_metadata=flavor_metadata, image_metadata=image_metadata,
        log_level=log_level))
    suite.addTest(OSIntegrationTestCase.parameterize(
        CreateImageSuccessTests, os_creds=os_creds, ext_net_name=ext_net_name,
        use_keystone=use_keystone,
        flavor_metadata=flavor_metadata, image_metadata=image_metadata,
        log_level=log_level))
    suite.addTest(OSIntegrationTestCase.parameterize(
        CreateImageNegativeTests, os_creds=os_creds, ext_net_name=ext_net_name,
        use_keystone=use_keystone,
        flavor_metadata=flavor_metadata, image_metadata=image_metadata,
        log_level=log_level))
    suite.addTest(OSIntegrationTestCase.parameterize(
        CreateMultiPartImageTests, os_creds=os_creds,
        ext_net_name=ext_net_name, use_keystone=use_keystone,
        flavor_metadata=flavor_metadata, image_metadata=image_metadata,
        log_level=log_level))
    suite.addTest(OSIntegrationTestCase.parameterize(
        CreateKeypairsTests, os_creds=os_creds, ext_net_name=ext_net_name,
        use_keystone=use_keystone,
        flavor_metadata=flavor_metadata, image_metadata=image_metadata,
        log_level=log_level))
    suite.addTest(OSIntegrationTestCase.parameterize(
        CreateNetworkSuccessTests, os_creds=os_creds,
        ext_net_name=ext_net_name, use_keystone=use_keystone,
        flavor_metadata=flavor_metadata, image_metadata=image_metadata,
        log_level=log_level))
    suite.addTest(OSIntegrationTestCase.parameterize(
        CreateRouterSuccessTests, os_creds=os_creds, ext_net_name=ext_net_name,
        use_keystone=use_keystone,
        flavor_metadata=flavor_metadata, image_metadata=image_metadata,
        log_level=log_level))
    suite.addTest(OSIntegrationTestCase.parameterize(
        CreateRouterNegativeTests, os_creds=os_creds,
        ext_net_name=ext_net_name, use_keystone=use_keystone,
        flavor_metadata=flavor_metadata, image_metadata=image_metadata,
        log_level=log_level))

    # VM Instances
    suite.addTest(OSIntegrationTestCase.parameterize(
        SimpleHealthCheck, os_creds=os_creds, ext_net_name=ext_net_name,
        use_keystone=use_keystone,
        flavor_metadata=flavor_metadata, image_metadata=image_metadata,
        log_level=log_level))
    suite.addTest(OSIntegrationTestCase.parameterize(
        CreateInstanceSimpleTests, os_creds=os_creds,
        ext_net_name=ext_net_name, use_keystone=use_keystone,
        flavor_metadata=flavor_metadata, image_metadata=image_metadata,
        log_level=log_level))
    suite.addTest(OSIntegrationTestCase.parameterize(
        CreateInstancePortManipulationTests, os_creds=os_creds,
        ext_net_name=ext_net_name, use_keystone=use_keystone,
        flavor_metadata=flavor_metadata, image_metadata=image_metadata,
        log_level=log_level))
    suite.addTest(OSIntegrationTestCase.parameterize(
        InstanceSecurityGroupTests, os_creds=os_creds,
        ext_net_name=ext_net_name, use_keystone=use_keystone,
        flavor_metadata=flavor_metadata, image_metadata=image_metadata,
        log_level=log_level))
    suite.addTest(OSIntegrationTestCase.parameterize(
        CreateInstanceOnComputeHost, os_creds=os_creds,
        ext_net_name=ext_net_name, use_keystone=use_keystone,
        flavor_metadata=flavor_metadata, image_metadata=image_metadata,
        log_level=log_level))
    suite.addTest(OSIntegrationTestCase.parameterize(
        CreateInstanceFromThreePartImage, os_creds=os_creds,
        ext_net_name=ext_net_name, use_keystone=use_keystone,
        flavor_metadata=flavor_metadata, image_metadata=image_metadata,
        log_level=log_level))
    suite.addTest(OSIntegrationTestCase.parameterize(
        CreateStackSuccessTests, os_creds=os_creds, ext_net_name=ext_net_name,
        use_keystone=use_keystone,
        flavor_metadata=flavor_metadata, image_metadata=image_metadata,
        log_level=log_level))
    suite.addTest(OSIntegrationTestCase.parameterize(
        CreateStackNegativeTests, os_creds=os_creds, ext_net_name=ext_net_name,
        use_keystone=use_keystone,
        flavor_metadata=flavor_metadata, image_metadata=image_metadata,
        log_level=log_level))

    if use_floating_ips:
        suite.addTest(OSIntegrationTestCase.parameterize(
            CreateInstanceSingleNetworkTests, os_creds=os_creds,
            ext_net_name=ext_net_name, use_keystone=use_keystone,
            flavor_metadata=flavor_metadata, image_metadata=image_metadata,
            log_level=log_level))
        suite.addTest(OSIntegrationTestCase.parameterize(
            CreateInstancePubPrivNetTests, os_creds=os_creds,
            ext_net_name=ext_net_name, use_keystone=use_keystone,
            flavor_metadata=flavor_metadata, image_metadata=image_metadata,
            log_level=log_level))
        suite.addTest(OSIntegrationTestCase.parameterize(
            AnsibleProvisioningTests, os_creds=os_creds,
            ext_net_name=ext_net_name, use_keystone=use_keystone,
            flavor_metadata=flavor_metadata, image_metadata=image_metadata,
            log_level=log_level))


def add_openstack_ci_tests(
        suite, os_creds, ext_net_name, use_keystone=True, flavor_metadata=None,
        image_metadata=None, use_floating_ips=True, log_level=logging.INFO):
    """
    Adds tests written for a CI server to run the tests to validate code
    changes
    :param suite: the unittest.TestSuite object to which to add the tests
    :param os_creds: and instance of OSCreds that holds the credentials
                     required by OpenStack
    :param ext_net_name: the name of an external network on the cloud under
                         test
    :param use_keystone: when True, tests requiring direct access to Keystone
                         are added as these need to be running on a host that
                         has access to the cloud's private network
    :param image_metadata: dict() object containing metadata for creating an
                           image with custom config
                           (see YAML files in examples/image-metadata)
    :param flavor_metadata: dict() object containing the metadata required by
                            your flavor based on your configuration:
                            (i.e. {'hw:mem_page_size': 'large'})
    :param use_floating_ips: when true, all tests requiring Floating IPs will
                             be added to the suite
    :param log_level: the logging level
    :return: None as the tests will be adding to the 'suite' parameter object
    """

    add_unit_tests(suite)

    add_openstack_client_tests(suite, os_creds, ext_net_name, use_keystone,
                               log_level)

    add_openstack_api_tests(suite, os_creds, ext_net_name, use_keystone,
                            image_metadata, log_level)

    suite.addTest(OSIntegrationTestCase.parameterize(
        SimpleHealthCheck, os_creds=os_creds, ext_net_name=ext_net_name,
        use_keystone=use_keystone,
        flavor_metadata=flavor_metadata, image_metadata=image_metadata,
        log_level=log_level))

    if use_floating_ips:
        suite.addTest(OSIntegrationTestCase.parameterize(
            CreateInstanceSingleNetworkTests, os_creds=os_creds,
            ext_net_name=ext_net_name, use_keystone=use_keystone,
            flavor_metadata=flavor_metadata, image_metadata=image_metadata,
            log_level=log_level))

    suite.addTest(OSIntegrationTestCase.parameterize(
        CreateStackSuccessTests, os_creds=os_creds, ext_net_name=ext_net_name,
        use_keystone=use_keystone,
        flavor_metadata=flavor_metadata, image_metadata=image_metadata,
        log_level=log_level))
    suite.addTest(OSIntegrationTestCase.parameterize(
        CreateStackNegativeTests, os_creds=os_creds, ext_net_name=ext_net_name,
        use_keystone=use_keystone,
        flavor_metadata=flavor_metadata, image_metadata=image_metadata,
        log_level=log_level))


def add_openstack_staging_tests(suite, os_creds, ext_net_name,
                                log_level=logging.INFO):
    """
    Adds tests that are still in development have not been designed to run
    successfully against all OpenStack pods
    :param suite: the unittest.TestSuite object to which to add the tests
    :param os_creds: Instance of OSCreds that holds the credentials
                    required by OpenStack
    :param ext_net_name: the name of an external network on the cloud under
                         test
    :param log_level: the logging level
    :return: None as the tests will be adding to the 'suite' parameter object
    """
    suite.addTest(OSComponentTestCase.parameterize(
        CreateNetworkTypeTests, os_creds=os_creds, ext_net_name=ext_net_name,
        log_level=log_level))
    suite.addTest(OSComponentTestCase.parameterize(
        CreateInstanceMockOfflineTests, os_creds=os_creds,
        ext_net_name=ext_net_name, log_level=log_level))
