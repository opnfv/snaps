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
import os
import uuid

from snaps.openstack import (
    create_image, create_network, create_router, create_flavor,
    create_keypairs, create_instance)
from snaps.openstack.create_network import (
    NetworkSettings, OpenStackNetwork, SubnetSettings)
from snaps.openstack.create_security_group import (
    SecurityGroupRuleSettings,  Direction, Protocol, OpenStackSecurityGroup,
    SecurityGroupSettings)
from snaps.openstack.tests import openstack_tests
from snaps.openstack.tests.os_source_file_test import OSComponentTestCase
from snaps.openstack.utils import (
    neutron_utils, settings_utils, nova_utils, glance_utils)

__author__ = 'spisarski'

logger = logging.getLogger('nova_utils_tests')


class SettingsUtilsNetworkingTests(OSComponentTestCase):
    """
    Tests the ability to reverse engineer NetworkSettings objects from existing
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
        self.neutron = neutron_utils.neutron_client(self.os_creds)

    def tearDown(self):
        """
        Cleans the image and downloaded image file
        """
        if self.net_creator:
            try:
                self.net_creator.clean()
            except:
                pass

    def test_derive_net_settings_no_subnet(self):
        """
        Validates the utility function settings_utils#create_network_settings
        returns an acceptable NetworkSettings object and ensures that the
        new settings object will not cause the new OpenStackNetwork instance
        to create another network
        """
        net_settings = NetworkSettings(name=self.network_name)
        self.net_creator = OpenStackNetwork(self.os_creds, net_settings)
        network = self.net_creator.create()

        derived_settings = settings_utils.create_network_settings(
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
        Validates the utility function settings_utils#create_network_settings
        returns an acceptable NetworkSettings object
        """
        subnet_settings = list()
        subnet_settings.append(SubnetSettings(name='sub1', cidr='10.0.0.0/24'))
        subnet_settings.append(SubnetSettings(name='sub2', cidr='10.0.1.0/24'))
        net_settings = NetworkSettings(name=self.network_name,
                                       subnet_settings=subnet_settings)
        self.net_creator = OpenStackNetwork(self.os_creds, net_settings)
        network = self.net_creator.create()

        derived_settings = settings_utils.create_network_settings(
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
    Tests the ability to reverse engineer VmInstanceSettings objects from
    existing VMs/servers deployed to OpenStack
    """

    def setUp(self):
        """
        Instantiates the CreateImage object that is responsible for downloading
        and creating an OS image file within OpenStack
        """
        # super(self.__class__, self).__start__()

        self.nova = nova_utils.nova_client(self.os_creds)
        self.glance = glance_utils.glance_client(self.os_creds)
        self.neutron = neutron_utils.neutron_client(self.os_creds)

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
                create_flavor.FlavorSettings(name=guid + '-flavor-name',
                                             ram=256, disk=1, vcpus=1))
            self.flavor_creator.create()

            # Create Key/Pair
            self.keypair_creator = create_keypairs.OpenStackKeypair(
                self.os_creds, create_keypairs.KeypairSettings(
                    name=self.keypair_name,
                    public_filepath=self.keypair_pub_filepath,
                    private_filepath=self.keypair_priv_filepath))
            self.keypair_creator.create()

            # Create Security Group
            sec_grp_name = guid + '-sec-grp'
            rule1 = SecurityGroupRuleSettings(sec_grp_name=sec_grp_name,
                                              direction=Direction.ingress,
                                              protocol=Protocol.icmp)
            rule2 = SecurityGroupRuleSettings(sec_grp_name=sec_grp_name,
                                              direction=Direction.ingress,
                                              protocol=Protocol.tcp,
                                              port_range_min=22,
                                              port_range_max=22)
            self.sec_grp_creator = OpenStackSecurityGroup(
                self.os_creds,
                SecurityGroupSettings(name=sec_grp_name,
                                      rule_settings=[rule1, rule2]))
            self.sec_grp_creator.create()

            # Create instance
            ports_settings = list()
            ports_settings.append(
                create_network.PortSettings(
                    name=self.port_1_name,
                    network_name=self.pub_net_config.network_settings.name))

            instance_settings = create_instance.VmInstanceSettings(
                name=self.vm_inst_name,
                flavor=self.flavor_creator.flavor_settings.name,
                port_settings=ports_settings,
                floating_ip_settings=[create_instance.FloatingIpSettings(
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

        # super(self.__class__, self).__clean__()

    def test_derive_vm_inst_settings(self):
        """
        Validates the utility function settings_utils#create_vm_inst_settings
        returns an acceptable VmInstanceSettings object
        """
        self.inst_creator.create(block=True)

        server = nova_utils.get_server(
            self.nova, vm_inst_settings=self.inst_creator.instance_settings)
        derived_vm_settings = settings_utils.create_vm_inst_settings(
            self.nova, self.neutron, server)
        self.assertIsNotNone(derived_vm_settings)
        self.assertIsNotNone(derived_vm_settings.port_settings)
        self.assertIsNotNone(derived_vm_settings.floating_ip_settings)

    def test_derive_image_settings(self):
        """
        Validates the utility function settings_utils#create_image_settings
        returns an acceptable ImageSettings object
        """
        self.inst_creator.create(block=True)

        server = nova_utils.get_server(
            self.nova, vm_inst_settings=self.inst_creator.instance_settings)
        derived_image_settings = settings_utils.determine_image_settings(
            self.glance, server, [self.image_creator.image_settings])
        self.assertIsNotNone(derived_image_settings)
        self.assertEqual(self.image_creator.image_settings.name,
                         derived_image_settings.name)
