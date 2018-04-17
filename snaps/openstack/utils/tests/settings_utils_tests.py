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

import os
import uuid

from snaps.config.network import SubnetConfig, NetworkConfig, PortConfig
from snaps.config.flavor import FlavorConfig
from snaps.config.keypair import KeypairConfig
from snaps.config.qos import Consumer
from snaps.config.security_group import (
    SecurityGroupRuleConfig, Direction, Protocol, SecurityGroupConfig)
from snaps.config.vm_inst import VmInstanceConfig, FloatingIpConfig
from snaps.domain.flavor import Flavor
from snaps.domain.volume import (
    Volume, VolumeType, VolumeTypeEncryption, QoSSpec)
from snaps.openstack import (
    create_image, create_network, create_router, create_flavor,
    create_keypairs, create_instance)
from snaps.openstack.create_qos import Consumer
from snaps.openstack.create_network import OpenStackNetwork
from snaps.openstack.create_security_group import OpenStackSecurityGroup
from snaps.openstack.tests import openstack_tests
from snaps.openstack.tests.os_source_file_test import OSComponentTestCase
from snaps.openstack.utils import (
    neutron_utils, settings_utils, nova_utils, glance_utils, keystone_utils)

__author__ = 'spisarski'

logger = logging.getLogger('nova_utils_tests')


class SettingsUtilsNetworkingTests(OSComponentTestCase):
    """
    Tests the ability to reverse engineer NetworkConfig objects from existing
    networks deployed to OpenStack
    """

    def setUp(self):
        """
        Instantiates OpenStack instances that cannot be spawned by Heat
        """
        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.network_name = guid + '-net'
        self.subnet_name = guid + '-subnet'
        self.net_creator = None
        self.neutron = neutron_utils.neutron_client(
            self.os_creds, self.os_session)

    def tearDown(self):
        """
        Cleans the image and downloaded image file
        """
        if self.net_creator:
            try:
                self.net_creator.clean()
            except:
                pass

        super(self.__class__, self).__clean__()

    def test_derive_net_settings_no_subnet(self):
        """
        Validates the utility function settings_utils#create_network_config
        returns an acceptable NetworkConfig object and ensures that the
        new settings object will not cause the new OpenStackNetwork instance
        to create another network
        """
        net_settings = NetworkConfig(name=self.network_name)
        self.net_creator = OpenStackNetwork(self.os_creds, net_settings)
        network = self.net_creator.create()

        derived_settings = settings_utils.create_network_config(
            self.neutron, network)

        self.assertIsNotNone(derived_settings)
        self.assertEqual(net_settings.name, derived_settings.name)
        self.assertEqual(net_settings.admin_state_up,
                         derived_settings.admin_state_up)
        self.assertEqual(net_settings.external, derived_settings.external)
        self.assertEqual(len(net_settings.subnet_settings),
                         len(derived_settings.subnet_settings))

        net_creator = OpenStackNetwork(self.os_creds, derived_settings)
        derived_network = net_creator.create()

        self.assertEqual(network, derived_network)

    def test_derive_net_settings_two_subnets(self):
        """
        Validates the utility function settings_utils#create_network_config
        returns an acceptable NetworkConfig object
        """
        subnet_settings = list()
        subnet_settings.append(SubnetConfig(name='sub1', cidr='10.0.0.0/24'))
        subnet_settings.append(SubnetConfig(name='sub2', cidr='10.0.1.0/24'))
        net_settings = NetworkConfig(
            name=self.network_name, subnet_settings=subnet_settings)
        self.net_creator = OpenStackNetwork(self.os_creds, net_settings)
        network = self.net_creator.create()

        derived_settings = settings_utils.create_network_config(
            self.neutron, network)

        self.assertIsNotNone(derived_settings)
        self.assertEqual(net_settings.name, derived_settings.name)
        self.assertEqual(net_settings.admin_state_up,
                         derived_settings.admin_state_up)
        self.assertEqual(net_settings.external, derived_settings.external)
        self.assertEqual(len(net_settings.subnet_settings),
                         len(derived_settings.subnet_settings))

        # Validate the first subnet
        orig_sub1 = net_settings.subnet_settings[0]
        found = False
        for derived_sub in derived_settings.subnet_settings:
            if orig_sub1.name == derived_sub.name:
                self.assertEqual(orig_sub1.cidr, derived_sub.cidr)
                found = True

        self.assertTrue(found)

        # Validate the second subnet
        orig_sub2 = net_settings.subnet_settings[1]
        found = False
        for derived_sub in derived_settings.subnet_settings:
            if orig_sub2.name == derived_sub.name:
                self.assertEqual(orig_sub2.cidr, derived_sub.cidr)
                self.assertEqual(orig_sub2.ip_version, derived_sub.ip_version)
                found = True

        self.assertTrue(found)


class SettingsUtilsVmInstTests(OSComponentTestCase):
    """
    Tests the ability to reverse engineer VmInstanceConfig objects from
    existing VMs/servers deployed to OpenStack
    """

    def setUp(self):
        """
        Instantiates the CreateImage object that is responsible for downloading
        and creating an OS image file within OpenStack
        """
        self.nova = nova_utils.nova_client(
            self.os_creds, self.os_session)
        self.keystone = keystone_utils.keystone_client(
            self.os_creds, self.os_session)
        self.glance = glance_utils.glance_client(
            self.os_creds, self.os_session)
        self.neutron = neutron_utils.neutron_client(
            self.os_creds, self.os_session)

        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.keypair_priv_filepath = 'tmp/' + guid
        self.keypair_pub_filepath = self.keypair_priv_filepath + '.pub'
        self.keypair_name = guid + '-kp'
        self.vm_inst_name = guid + '-inst'
        self.test_file_local_path = 'tmp/' + guid + '-hello.txt'
        self.port_1_name = guid + '-port-1'
        self.port_2_name = guid + '-port-2'
        self.floating_ip_name = guid + 'fip1'

        # Setup members to cleanup just in case they don't get created
        self.inst_creator = None
        self.keypair_creator = None
        self.sec_grp_creator = None
        self.flavor_creator = None
        self.router_creator = None
        self.network_creator = None
        self.image_creator = None

        try:
            # Create Image
            os_image_settings = openstack_tests.cirros_image_settings(
                name=guid + '-' + '-image',
                image_metadata=self.image_metadata)
            self.image_creator = create_image.OpenStackImage(self.os_creds,
                                                             os_image_settings)
            self.image_creator.create()

            # First network is public
            self.pub_net_config = openstack_tests.get_pub_net_config(
                project_name=self.os_creds.project_name,
                net_name=guid + '-pub-net', subnet_name=guid + '-pub-subnet',
                router_name=guid + '-pub-router',
                external_net=self.ext_net_name)

            self.network_creator = create_network.OpenStackNetwork(
                self.os_creds, self.pub_net_config.network_settings)
            self.network_creator.create()

            # Create routers
            self.router_creator = create_router.OpenStackRouter(
                self.os_creds, self.pub_net_config.router_settings)
            self.router_creator.create()

            # Create Flavor
            self.flavor_creator = create_flavor.OpenStackFlavor(
                self.os_creds,
                FlavorConfig(
                    name=guid + '-flavor-name', ram=256, disk=1, vcpus=1))
            self.flavor_creator.create()

            # Create Key/Pair
            self.keypair_creator = create_keypairs.OpenStackKeypair(
                self.os_creds, KeypairConfig(
                    name=self.keypair_name,
                    public_filepath=self.keypair_pub_filepath,
                    private_filepath=self.keypair_priv_filepath))
            self.keypair_creator.create()

            # Create Security Group
            sec_grp_name = guid + '-sec-grp'
            rule1 = SecurityGroupRuleConfig(
                sec_grp_name=sec_grp_name, direction=Direction.ingress,
                protocol=Protocol.icmp)
            rule2 = SecurityGroupRuleConfig(
                sec_grp_name=sec_grp_name, direction=Direction.ingress,
                protocol=Protocol.tcp, port_range_min=22, port_range_max=22)
            self.sec_grp_creator = OpenStackSecurityGroup(
                self.os_creds,
                SecurityGroupConfig(
                    name=sec_grp_name, rule_settings=[rule1, rule2]))
            self.sec_grp_creator.create()

            # Create instance
            ports_settings = list()
            ports_settings.append(
                PortConfig(
                    name=self.port_1_name,
                    network_name=self.pub_net_config.network_settings.name))

            instance_settings = VmInstanceConfig(
                name=self.vm_inst_name,
                flavor=self.flavor_creator.flavor_settings.name,
                port_settings=ports_settings,
                floating_ip_settings=[FloatingIpConfig(
                    name=self.floating_ip_name, port_name=self.port_1_name,
                    router_name=self.pub_net_config.router_settings.name)])

            self.inst_creator = create_instance.OpenStackVmInstance(
                self.os_creds, instance_settings,
                self.image_creator.image_settings,
                keypair_settings=self.keypair_creator.keypair_settings)
        except:
            self.tearDown()
            raise

    def tearDown(self):
        """
        Cleans the created objects
        """
        if self.inst_creator:
            try:
                self.inst_creator.clean()
            except:
                pass

        if self.sec_grp_creator:
            try:
                self.sec_grp_creator.clean()
            except:
                pass

        if self.keypair_creator:
            try:
                self.keypair_creator.clean()
            except:
                pass

        if self.flavor_creator:
            try:
                self.flavor_creator.clean()
            except:
                pass

        if os.path.isfile(self.keypair_pub_filepath):
            try:
                os.remove(self.keypair_pub_filepath)
            except:
                pass

        if os.path.isfile(self.keypair_priv_filepath):
            try:
                os.remove(self.keypair_priv_filepath)
            except:
                pass

        if self.router_creator:
            try:
                self.router_creator.clean()
            except:
                pass

        if self.network_creator:
            try:
                self.network_creator.clean()
            except:
                pass

        if self.image_creator and not self.image_creator.image_settings.exists:
            try:
                self.image_creator.clean()
            except:
                pass

        if os.path.isfile(self.test_file_local_path):
            os.remove(self.test_file_local_path)

        super(self.__class__, self).__clean__()

    def test_derive_vm_inst_config(self):
        """
        Validates the utility function settings_utils#create_vm_inst_config
        returns an acceptable VmInstanceConfig object
        """
        self.inst_creator.create(block=True)

        server = nova_utils.get_server(
            self.nova, self.neutron, self.keystone,
            vm_inst_settings=self.inst_creator.instance_settings)
        derived_vm_settings = settings_utils.create_vm_inst_config(
            self.nova, self.keystone, self.neutron, server,
            self.os_creds.project_name)
        self.assertIsNotNone(derived_vm_settings)
        self.assertIsNotNone(derived_vm_settings.port_settings)
        self.assertIsNotNone(derived_vm_settings.floating_ip_settings)

    def test_derive_image_settings(self):
        """
        Validates the utility function settings_utils#create_image_settings
        returns an acceptable ImageConfig object
        """
        self.inst_creator.create(block=True)

        server = nova_utils.get_server(
            self.nova, self.neutron, self.keystone,
            vm_inst_settings=self.inst_creator.instance_settings)
        derived_image_settings = settings_utils.determine_image_config(
            self.glance, server, [self.image_creator.image_settings])
        self.assertIsNotNone(derived_image_settings)
        self.assertEqual(self.image_creator.image_settings.name,
                         derived_image_settings.name)


class SettingsUtilsUnitTests(unittest.TestCase):
    """
    Exercises the settings_utils.py functions around volumes
    """

    def test_vol_settings_from_vol(self):
        volume = Volume(
            name='vol-name', volume_id='vol-id', project_id='proj-id',
            description='desc', size=99, vol_type='vol-type',
            availability_zone='zone1', multi_attach=True)
        settings = settings_utils.create_volume_config(volume)
        self.assertEqual(volume.name, settings.name)
        self.assertEqual(volume.description, settings.description)
        self.assertEqual(volume.size, settings.size)
        self.assertEqual(volume.type, settings.type_name)
        self.assertEqual(volume.availability_zone, settings.availability_zone)
        self.assertEqual(volume.multi_attach, settings.multi_attach)

    def test_vol_type_settings_from_vol(self):
        encryption = VolumeTypeEncryption(
            volume_encryption_id='vol-encrypt-id', volume_type_id='vol-typ-id',
            control_location='front-end', provider='FooClass', cipher='1',
            key_size=1)
        qos_spec = QoSSpec(name='qos-spec-name', spec_id='qos-spec-id',
                           consumer=Consumer.back_end)
        volume_type = VolumeType(
            name='vol-type-name', volume_type_id='vol-type-id', public=True,
            encryption=encryption, qos_spec=qos_spec)

        settings = settings_utils.create_volume_type_config(volume_type)
        self.assertEqual(volume_type.name, settings.name)
        self.assertEqual(volume_type.public, settings.public)

        encrypt_settings = settings.encryption
        self.assertIsNotNone(encrypt_settings)
        self.assertEqual(encryption.control_location,
                         encrypt_settings.control_location.value)
        self.assertEqual(encryption.cipher, encrypt_settings.cipher)
        self.assertEqual(encryption.key_size, encrypt_settings.key_size)

        self.assertEqual(qos_spec.name, settings.qos_spec_name)

    def test_flavor_settings_from_flavor(self):
        flavor = Flavor(
            name='flavor-name', flavor_id='flavor-id', ram=99, disk=101,
            vcpus=9, ephemeral=3, swap=5, rxtx_factor=7, is_public=False)
        settings = settings_utils.create_flavor_config(flavor)
        self.assertEqual(flavor.name, settings.name)
        self.assertEqual(flavor.id, settings.flavor_id)
        self.assertEqual(flavor.ram, settings.ram)
        self.assertEqual(flavor.disk, settings.disk)
        self.assertEqual(flavor.vcpus, settings.vcpus)
        self.assertEqual(flavor.ephemeral, settings.ephemeral)
        self.assertEqual(flavor.swap, settings.swap)
        self.assertEqual(flavor.rxtx_factor, settings.rxtx_factor)
        self.assertEqual(flavor.is_public, settings.is_public)
