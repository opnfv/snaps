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

from snaps.config.tests.cluster_template_tests import (
    ClusterTemplateConfigUnitTests)
from snaps.config.tests.network_tests import (
    NetworkConfigUnitTests, SubnetConfigUnitTests, PortConfigUnitTests)
from snaps.config.tests.security_group_tests import (
    SecurityGroupConfigUnitTests, SecurityGroupRuleConfigUnitTests)
from snaps.config.tests.vm_inst_tests import (
    VmInstanceConfigUnitTests, FloatingIpConfigUnitTests)
from snaps.config.tests.volume_tests import VolumeConfigUnitTests
from snaps.config.tests.volume_type_tests import VolumeTypeConfigUnitTests
from snaps.config.tests.qos_tests import QoSConfigUnitTests
from snaps.config.tests.stack_tests import StackConfigUnitTests
from snaps.config.tests.router_tests import RouterConfigUnitTests
from snaps.config.tests.user_tests import UserConfigUnitTests
from snaps.config.tests.project_tests import ProjectConfigUnitTests
from snaps.config.tests.keypair_tests import KeypairConfigUnitTests
from snaps.config.tests.flavor_tests import FlavorConfigUnitTests
import snaps.config.tests.image_tests as image_tests
import snaps.openstack.tests.create_image_tests as creator_tests
from snaps.domain.test.cluster_template_tests import ClusterTemplateUnitTests
from snaps.domain.test.flavor_tests import FlavorDomainObjectTests
from snaps.domain.test.image_tests import ImageDomainObjectTests
from snaps.domain.test.keypair_tests import KeypairDomainObjectTests
from snaps.domain.test.network_tests import (
    SecurityGroupDomainObjectTests, SecurityGroupRuleDomainObjectTests,
    PortDomainObjectTests, RouterDomainObjectTests,
    InterfaceRouterDomainObjectTests, NetworkObjectTests, SubnetObjectTests)
from snaps.domain.test.project_tests import (
    ProjectDomainObjectTests, DomainDomainObjectTests,
    ComputeQuotasDomainObjectTests, NetworkQuotasDomainObjectTests)
from snaps.domain.test.role_tests import RoleDomainObjectTests
from snaps.domain.test.stack_tests import (
    StackDomainObjectTests, ResourceDomainObjectTests)
from snaps.domain.test.user_tests import UserDomainObjectTests
from snaps.domain.test.vm_inst_tests import (
    VmInstDomainObjectTests, FloatingIpDomainObjectTests)
from snaps.domain.test.volume_tests import (
    QoSSpecDomainObjectTests, VolumeTypeDomainObjectTests,
    VolumeTypeEncryptionObjectTests, VolumeDomainObjectTests)
from snaps.openstack.tests.cluster_template_tests import (
    CreateClusterTemplateTests)
from snaps.openstack.tests.conf.os_credentials_tests import (
    ProxySettingsUnitTests, OSCredsUnitTests)
from snaps.openstack.tests.create_flavor_tests import (
    CreateFlavorTests, FlavorSettingsUnitTests)
from snaps.openstack.tests.create_image_tests import (
    CreateImageSuccessTests, CreateImageNegativeTests,
    CreateMultiPartImageTests)
from snaps.openstack.tests.create_instance_tests import (
    CreateInstanceSingleNetworkTests, CreateInstanceOnComputeHost,
    CreateInstanceSimpleTests, FloatingIpSettingsUnitTests,
    InstanceSecurityGroupTests, VmInstanceSettingsUnitTests,
    CreateInstancePortManipulationTests, SimpleHealthCheck,
    CreateInstanceFromThreePartImage, CreateInstanceMockOfflineTests,
    CreateInstanceTwoNetTests, CreateInstanceVolumeTests,
    CreateInstanceIPv6NetworkTests, CreateInstanceExternalNetTests)
from snaps.openstack.tests.create_keypairs_tests import (
    CreateKeypairsTests, KeypairSettingsUnitTests, CreateKeypairsCleanupTests)
from snaps.openstack.tests.create_network_tests import (
    CreateNetworkSuccessTests, NetworkSettingsUnitTests, PortSettingsUnitTests,
    SubnetSettingsUnitTests, CreateNetworkTypeTests, CreateNetworkIPv6Tests,
    CreateMultipleNetworkTests, CreateNetworkGatewayTests)
from snaps.openstack.tests.create_project_tests import (
    CreateProjectSuccessTests, ProjectSettingsUnitTests,
    CreateProjectUserTests)
from snaps.openstack.tests.create_qos_tests import (
    QoSSettingsUnitTests, CreateQoSTests)
from snaps.openstack.tests.create_router_tests import (
    CreateRouterSuccessTests, CreateRouterNegativeTests,
    RouterSettingsUnitTests, CreateMultipleRouterTests,
    CreateRouterSecurityGroupTests)
from snaps.openstack.tests.create_security_group_tests import (
    CreateSecurityGroupTests, SecurityGroupRuleSettingsUnitTests,
    SecurityGroupSettingsUnitTests, CreateMultipleSecurityGroupTests)
from snaps.openstack.tests.create_stack_tests import (
    StackSettingsUnitTests, CreateStackSuccessTests, CreateStackNegativeTests,
    CreateStackFlavorTests, CreateStackFloatingIpTests,
    CreateStackNestedResourceTests, CreateStackKeypairTests,
    CreateStackVolumeTests, CreateStackSecurityGroupTests)
from snaps.openstack.tests.create_user_tests import (
    UserSettingsUnitTests, CreateUserSuccessTests)
from snaps.openstack.tests.create_volume_tests import (
    VolumeSettingsUnitTests, CreateSimpleVolumeSuccessTests,
    CreateVolumeWithTypeTests, CreateVolumeWithImageTests,
    CreateSimpleVolumeFailureTests, CreateVolMultipleCredsTests)
from snaps.openstack.tests.create_volume_type_tests import (
    VolumeTypeSettingsUnitTests, CreateSimpleVolumeTypeSuccessTests,
    CreateVolumeTypeComplexTests)
from snaps.openstack.tests.os_source_file_test import (
    OSComponentTestCase, OSIntegrationTestCase)
from snaps.openstack.utils.tests.cinder_utils_tests import (
    CinderSmokeTests, CinderUtilsQoSTests, CinderUtilsSimpleVolumeTypeTests,
    CinderUtilsAddEncryptionTests, CinderUtilsVolumeTypeCompleteTests,
    CinderUtilsVolumeTests)
from snaps.openstack.utils.tests.glance_utils_tests import (
    GlanceSmokeTests, GlanceUtilsTests)
from snaps.openstack.utils.tests.heat_utils_tests import (
    HeatSmokeTests, HeatUtilsCreateSimpleStackTests,
    HeatUtilsCreateComplexStackTests, HeatUtilsFlavorTests,
    HeatUtilsKeypairTests, HeatUtilsVolumeTests, HeatUtilsSecurityGroupTests)
from snaps.openstack.utils.tests.keystone_utils_tests import (
    KeystoneSmokeTests, KeystoneUtilsTests)
from snaps.openstack.utils.tests.neutron_utils_tests import (
    NeutronSmokeTests, NeutronUtilsNetworkTests, NeutronUtilsSubnetTests,
    NeutronUtilsRouterTests, NeutronUtilsSecurityGroupTests,
    NeutronUtilsFloatingIpTests, NeutronUtilsIPv6Tests)
from snaps.openstack.utils.tests.nova_utils_tests import (
    NovaSmokeTests, NovaUtilsKeypairTests, NovaUtilsFlavorTests,
    NovaUtilsInstanceTests, NovaUtilsInstanceVolumeTests)
from snaps.openstack.utils.tests.settings_utils_tests import (
    SettingsUtilsUnitTests)
from snaps.openstack.utils.tests.magnum_utils_tests import (
    MagnumSmokeTests, MagnumUtilsClusterTypeTests)
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
        ProxySettingsUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        OSCredsUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        SecurityGroupConfigUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        SecurityGroupSettingsUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        SecurityGroupRuleConfigUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        SecurityGroupRuleSettingsUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        SecurityGroupDomainObjectTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        SecurityGroupRuleDomainObjectTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        image_tests.ImageConfigUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        creator_tests.ImageSettingsUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        ImageDomainObjectTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        FlavorConfigUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        FlavorSettingsUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        FlavorDomainObjectTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        KeypairConfigUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        KeypairSettingsUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        KeypairDomainObjectTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        UserConfigUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        UserSettingsUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        UserDomainObjectTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        ProjectConfigUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        ProjectSettingsUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        ProjectDomainObjectTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        DomainDomainObjectTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        ComputeQuotasDomainObjectTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        NetworkQuotasDomainObjectTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        RoleDomainObjectTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        NetworkConfigUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        NetworkSettingsUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        NetworkObjectTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        SubnetConfigUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        SubnetSettingsUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        SubnetObjectTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        PortConfigUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        PortSettingsUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        PortDomainObjectTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        RouterConfigUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        RouterSettingsUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        RouterDomainObjectTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        InterfaceRouterDomainObjectTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        FloatingIpConfigUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        FloatingIpSettingsUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        VmInstanceConfigUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        VmInstanceSettingsUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        StackDomainObjectTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        ResourceDomainObjectTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        StackConfigUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        StackSettingsUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        VolumeTypeDomainObjectTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        VolumeTypeEncryptionObjectTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        VolumeDomainObjectTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        QoSSpecDomainObjectTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        VmInstDomainObjectTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        FloatingIpDomainObjectTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        QoSConfigUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        QoSSettingsUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        VolumeTypeConfigUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        VolumeTypeSettingsUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        VolumeConfigUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        VolumeSettingsUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        ClusterTemplateConfigUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        ClusterTemplateUnitTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
        SettingsUtilsUnitTests))


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
    suite.addTest(
        OSComponentTestCase.parameterize(
            CinderSmokeTests, os_creds=os_creds, ext_net_name=ext_net_name,
            log_level=log_level))


def add_openstack_api_tests(suite, os_creds, ext_net_name, use_keystone=True,
                            flavor_metadata=None, image_metadata=None,
                            log_level=logging.INFO):
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
    :param flavor_metadata: dict() object containing the metadata required by
                            your flavor based on your configuration:
                            (i.e. {'hw:mem_page_size': 'any'})
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
        NeutronUtilsIPv6Tests, os_creds=os_creds, ext_net_name=ext_net_name,
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
        NovaUtilsInstanceVolumeTests, os_creds=os_creds,
        ext_net_name=ext_net_name, log_level=log_level,
        flavor_metadata=flavor_metadata, image_metadata=image_metadata))
    suite.addTest(OSComponentTestCase.parameterize(
        CreateFlavorTests, os_creds=os_creds, ext_net_name=ext_net_name,
        log_level=log_level))
    suite.addTest(OSComponentTestCase.parameterize(
        HeatUtilsCreateSimpleStackTests, os_creds=os_creds,
        ext_net_name=ext_net_name, log_level=log_level,
        image_metadata=image_metadata))
    suite.addTest(OSComponentTestCase.parameterize(
        HeatUtilsCreateComplexStackTests, os_creds=os_creds,
        ext_net_name=ext_net_name, log_level=log_level,
        image_metadata=image_metadata))
    suite.addTest(OSComponentTestCase.parameterize(
        HeatUtilsFlavorTests, os_creds=os_creds,
        ext_net_name=ext_net_name, log_level=log_level,
        image_metadata=image_metadata))
    suite.addTest(OSComponentTestCase.parameterize(
        HeatUtilsKeypairTests, os_creds=os_creds,
        ext_net_name=ext_net_name, log_level=log_level,
        image_metadata=image_metadata))
    suite.addTest(OSComponentTestCase.parameterize(
        HeatUtilsSecurityGroupTests, os_creds=os_creds,
        ext_net_name=ext_net_name, log_level=log_level,
        image_metadata=image_metadata))
    suite.addTest(OSComponentTestCase.parameterize(
        HeatUtilsVolumeTests, os_creds=os_creds,
        ext_net_name=ext_net_name, log_level=log_level,
        image_metadata=image_metadata))
    suite.addTest(OSComponentTestCase.parameterize(
        CinderUtilsQoSTests, os_creds=os_creds,
        ext_net_name=ext_net_name, log_level=log_level,
        image_metadata=image_metadata))
    suite.addTest(OSComponentTestCase.parameterize(
        CinderUtilsVolumeTests, os_creds=os_creds,
        ext_net_name=ext_net_name, log_level=log_level,
        image_metadata=image_metadata))
    suite.addTest(OSComponentTestCase.parameterize(
        CinderUtilsSimpleVolumeTypeTests, os_creds=os_creds,
        ext_net_name=ext_net_name, log_level=log_level,
        image_metadata=image_metadata))
    suite.addTest(OSComponentTestCase.parameterize(
        CinderUtilsAddEncryptionTests, os_creds=os_creds,
        ext_net_name=ext_net_name, log_level=log_level,
        image_metadata=image_metadata))
    suite.addTest(OSComponentTestCase.parameterize(
        CinderUtilsVolumeTypeCompleteTests, os_creds=os_creds,
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
        CreateMultipleSecurityGroupTests, os_creds=os_creds,
        ext_net_name=ext_net_name, use_keystone=use_keystone,
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
        CreateKeypairsCleanupTests, os_creds=os_creds,
        ext_net_name=ext_net_name,
        use_keystone=use_keystone,
        flavor_metadata=flavor_metadata, image_metadata=image_metadata,
        log_level=log_level))
    suite.addTest(OSIntegrationTestCase.parameterize(
        CreateNetworkSuccessTests, os_creds=os_creds,
        ext_net_name=ext_net_name, use_keystone=use_keystone,
        flavor_metadata=flavor_metadata, image_metadata=image_metadata,
        log_level=log_level))
    suite.addTest(OSIntegrationTestCase.parameterize(
        CreateNetworkGatewayTests, os_creds=os_creds,
        ext_net_name=ext_net_name, use_keystone=use_keystone,
        flavor_metadata=flavor_metadata, image_metadata=image_metadata,
        log_level=log_level))
    suite.addTest(OSIntegrationTestCase.parameterize(
        CreateNetworkIPv6Tests, os_creds=os_creds,
        ext_net_name=ext_net_name, use_keystone=use_keystone,
        flavor_metadata=flavor_metadata, image_metadata=image_metadata,
        log_level=log_level))
    suite.addTest(OSIntegrationTestCase.parameterize(
        CreateMultipleNetworkTests, os_creds=os_creds,
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
    suite.addTest(OSIntegrationTestCase.parameterize(
        CreateMultipleRouterTests, os_creds=os_creds,
        ext_net_name=ext_net_name, use_keystone=use_keystone,
        flavor_metadata=flavor_metadata, image_metadata=image_metadata,
        log_level=log_level))
    suite.addTest(OSIntegrationTestCase.parameterize(
        CreateRouterSecurityGroupTests, os_creds=os_creds,
        ext_net_name=ext_net_name, use_keystone=use_keystone,
        flavor_metadata=flavor_metadata, image_metadata=image_metadata,
        log_level=log_level))
    suite.addTest(OSIntegrationTestCase.parameterize(
        CreateQoSTests, os_creds=os_creds,
        ext_net_name=ext_net_name, use_keystone=use_keystone,
        flavor_metadata=flavor_metadata, image_metadata=image_metadata,
        log_level=log_level))
    suite.addTest(OSIntegrationTestCase.parameterize(
        CreateSimpleVolumeTypeSuccessTests, os_creds=os_creds,
        ext_net_name=ext_net_name, use_keystone=use_keystone,
        flavor_metadata=flavor_metadata, image_metadata=image_metadata,
        log_level=log_level))
    suite.addTest(OSIntegrationTestCase.parameterize(
        CreateVolumeTypeComplexTests, os_creds=os_creds,
        ext_net_name=ext_net_name, use_keystone=use_keystone,
        flavor_metadata=flavor_metadata, image_metadata=image_metadata,
        log_level=log_level))
    suite.addTest(OSIntegrationTestCase.parameterize(
        CreateSimpleVolumeSuccessTests, os_creds=os_creds,
        ext_net_name=ext_net_name, use_keystone=use_keystone,
        flavor_metadata=flavor_metadata, image_metadata=image_metadata,
        log_level=log_level))
    suite.addTest(OSIntegrationTestCase.parameterize(
        CreateSimpleVolumeFailureTests, os_creds=os_creds,
        ext_net_name=ext_net_name, use_keystone=use_keystone,
        flavor_metadata=flavor_metadata, image_metadata=image_metadata,
        log_level=log_level))
    suite.addTest(OSIntegrationTestCase.parameterize(
        CreateVolumeWithTypeTests, os_creds=os_creds,
        ext_net_name=ext_net_name, use_keystone=use_keystone,
        flavor_metadata=flavor_metadata, image_metadata=image_metadata,
        log_level=log_level))
    suite.addTest(OSIntegrationTestCase.parameterize(
        CreateVolumeWithImageTests, os_creds=os_creds,
        ext_net_name=ext_net_name, use_keystone=use_keystone,
        flavor_metadata=flavor_metadata, image_metadata=image_metadata,
        log_level=log_level))
    suite.addTest(OSIntegrationTestCase.parameterize(
        CreateVolMultipleCredsTests, os_creds=os_creds,
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
        CreateInstanceTwoNetTests, os_creds=os_creds,
        ext_net_name=ext_net_name, use_keystone=use_keystone,
        flavor_metadata=flavor_metadata, image_metadata=image_metadata,
        log_level=log_level))
    suite.addTest(OSIntegrationTestCase.parameterize(
        CreateInstanceSimpleTests, os_creds=os_creds,
        ext_net_name=ext_net_name, use_keystone=use_keystone,
        flavor_metadata=flavor_metadata, image_metadata=image_metadata,
        log_level=log_level))
    suite.addTest(OSIntegrationTestCase.parameterize(
        CreateInstanceExternalNetTests, os_creds=os_creds,
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
        CreateInstanceVolumeTests, os_creds=os_creds,
        ext_net_name=ext_net_name, use_keystone=use_keystone,
        flavor_metadata=flavor_metadata, image_metadata=image_metadata,
        log_level=log_level))
    suite.addTest(OSIntegrationTestCase.parameterize(
        CreateInstanceIPv6NetworkTests, os_creds=os_creds,
        ext_net_name=ext_net_name, use_keystone=use_keystone,
        flavor_metadata=flavor_metadata, image_metadata=image_metadata,
        log_level=log_level))
    suite.addTest(OSIntegrationTestCase.parameterize(
        CreateStackSuccessTests, os_creds=os_creds, ext_net_name=ext_net_name,
        use_keystone=use_keystone,
        flavor_metadata=flavor_metadata, image_metadata=image_metadata,
        log_level=log_level))
    suite.addTest(OSIntegrationTestCase.parameterize(
        CreateStackVolumeTests, os_creds=os_creds, ext_net_name=ext_net_name,
        use_keystone=use_keystone,
        flavor_metadata=flavor_metadata, image_metadata=image_metadata,
        log_level=log_level))
    suite.addTest(OSIntegrationTestCase.parameterize(
        CreateStackFlavorTests, os_creds=os_creds, ext_net_name=ext_net_name,
        use_keystone=use_keystone,
        flavor_metadata=flavor_metadata, image_metadata=image_metadata,
        log_level=log_level))
    suite.addTest(OSIntegrationTestCase.parameterize(
        CreateStackKeypairTests, os_creds=os_creds, ext_net_name=ext_net_name,
        use_keystone=use_keystone,
        flavor_metadata=flavor_metadata, image_metadata=image_metadata,
        log_level=log_level))
    suite.addTest(OSIntegrationTestCase.parameterize(
        CreateStackSecurityGroupTests, os_creds=os_creds,
        ext_net_name=ext_net_name, use_keystone=use_keystone,
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
            CreateStackFloatingIpTests, os_creds=os_creds,
            ext_net_name=ext_net_name, use_keystone=use_keystone,
            flavor_metadata=flavor_metadata, image_metadata=image_metadata,
            log_level=log_level))
        suite.addTest(OSIntegrationTestCase.parameterize(
            CreateStackNestedResourceTests, os_creds=os_creds,
            ext_net_name=ext_net_name, use_keystone=use_keystone,
            flavor_metadata=flavor_metadata, image_metadata=image_metadata,
            log_level=log_level))


def add_ansible_integration_tests(suite, os_creds, ext_net_name,
                                  use_keystone=True, flavor_metadata=None,
                                  image_metadata=None, log_level=logging.INFO):
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
    :param log_level: the logging level
    :return: None as the tests will be adding to the 'suite' parameter object
    """
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
        CreateNetworkTypeTests, os_creds=os_creds,
        ext_net_name=ext_net_name, log_level=log_level))
    suite.addTest(OSComponentTestCase.parameterize(
        CreateInstanceMockOfflineTests, os_creds=os_creds,
        ext_net_name=ext_net_name, log_level=log_level))
    suite.addTest(OSComponentTestCase.parameterize(
        MagnumSmokeTests, os_creds=os_creds,
        ext_net_name=ext_net_name, log_level=log_level))
    suite.addTest(OSComponentTestCase.parameterize(
        MagnumUtilsClusterTypeTests, os_creds=os_creds,
        ext_net_name=ext_net_name, log_level=log_level))
    suite.addTest(OSComponentTestCase.parameterize(
        CreateClusterTemplateTests, os_creds=os_creds,
        ext_net_name=ext_net_name, log_level=log_level))
