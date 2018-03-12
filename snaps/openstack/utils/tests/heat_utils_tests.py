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

import pkg_resources
import uuid

import time

import snaps.config.stack as stack_config
from snaps.config.flavor import FlavorConfig
from snaps.openstack.create_flavor import OpenStackFlavor

from snaps.openstack.create_image import OpenStackImage
from snaps.openstack.create_instance import OpenStackVmInstance
from snaps.openstack.create_stack import StackConfig
from snaps.openstack.tests import openstack_tests
from snaps.openstack.tests.os_source_file_test import OSComponentTestCase
from snaps.openstack.utils import (
    heat_utils, neutron_utils, nova_utils, settings_utils, glance_utils,
    cinder_utils, keystone_utils)

__author__ = 'spisarski'

logger = logging.getLogger('heat_utils_tests')


class HeatSmokeTests(OSComponentTestCase):
    """
    Tests to ensure that the heat client can communicate with the cloud
    """

    def test_heat_connect_success(self):
        """
        Tests to ensure that the proper credentials can connect.
        """
        heat = heat_utils.heat_client(self.os_creds, self.os_session)

        # This should not throw an exception
        stacks = heat.stacks.list()
        for stack in stacks:
            logger.info('Stack - %s', stack)

    def test_heat_connect_fail(self):
        """
        Tests to ensure that the improper credentials cannot connect.
        """
        from snaps.openstack.os_credentials import OSCreds

        heat = heat_utils.heat_client(
            OSCreds(username='user', password='pass',
                    auth_url=self.os_creds.auth_url,
                    project_name=self.os_creds.project_name,
                    proxy_settings=self.os_creds.proxy_settings))
        stacks = heat.stacks.list()

        # This should throw an exception
        with self.assertRaises(Exception):
            for stack in stacks:
                logger.info('Stack - %s', stack)


class HeatUtilsCreateSimpleStackTests(OSComponentTestCase):
    """
    Test basic Heat functionality
    """

    def setUp(self):
        """
        Instantiates OpenStack instances that cannot be spawned by Heat
        """
        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        stack_name1 = guid + '-stack1'
        stack_name2 = guid + '-stack2'
        self.network_name = guid + '-net'
        self.subnet_name = guid + '-subnet'
        self.vm_inst_name = guid + '-inst'

        self.image_creator = OpenStackImage(
            self.os_creds, openstack_tests.cirros_image_settings(
                name=guid + '-image', image_metadata=self.image_metadata))
        self.image_creator.create()

        # Create Flavor
        self.flavor_creator = OpenStackFlavor(
            self.os_creds,
            FlavorConfig(name=guid + '-flavor', ram=256, disk=10, vcpus=1))
        self.flavor_creator.create()

        env_values = {'image_name': self.image_creator.image_settings.name,
                      'flavor_name': self.flavor_creator.flavor_settings.name,
                      'net_name': self.network_name,
                      'subnet_name': self.subnet_name,
                      'inst_name': self.vm_inst_name}
        heat_tmplt_path = pkg_resources.resource_filename(
            'snaps.openstack.tests.heat', 'test_heat_template.yaml')
        self.stack_settings1 = StackConfig(
            name=stack_name1, template_path=heat_tmplt_path,
            env_values=env_values)
        self.stack_settings2 = StackConfig(
            name=stack_name2, template_path=heat_tmplt_path,
            env_values=env_values)
        self.stack1 = None
        self.stack2 = None
        self.heat_client = heat_utils.heat_client(
            self.os_creds, self.os_session)

    def tearDown(self):
        """
        Cleans the stack and image
        """
        if self.stack1:
            try:
                heat_utils.delete_stack(self.heat_client, self.stack1)
            except:
                pass

        if self.stack2:
            try:
                heat_utils.delete_stack(self.heat_client, self.stack2)
            except:
                pass

        if self.image_creator:
            try:
                self.image_creator.clean()
            except:
                pass

        if self.flavor_creator:
            try:
                self.flavor_creator.clean()
            except:
                pass

        super(self.__class__, self).__clean__()

    def test_create_stack(self):
        """
        Tests the creation of an OpenStack Heat stack1 that does not exist.
        """
        self.stack1 = heat_utils.create_stack(self.heat_client,
                                              self.stack_settings1)

        stack_query_1 = heat_utils.get_stack(
            self.heat_client, stack_settings=self.stack_settings1)
        self.assertEqual(self.stack1, stack_query_1)

        stack_query_2 = heat_utils.get_stack(
            self.heat_client, stack_name=self.stack_settings1.name)
        self.assertEqual(self.stack1, stack_query_2)

        stack_query_3 = heat_utils.get_stack_by_id(self.heat_client,
                                                   self.stack1.id)
        self.assertEqual(self.stack1, stack_query_3)

        resources = heat_utils.get_resources(self.heat_client, self.stack1.id)
        self.assertIsNotNone(resources)
        self.assertEqual(4, len(resources))

        outputs = heat_utils.get_outputs(self.heat_client, self.stack1)
        self.assertIsNotNone(outputs)
        self.assertEqual(0, len(outputs))

        self.assertTrue(stack_active(self.heat_client, self.stack1))

        neutron = neutron_utils.neutron_client(self.os_creds, self.os_session)
        networks = heat_utils.get_stack_networks(
            self.heat_client, neutron, self.stack1)
        self.assertIsNotNone(networks)
        self.assertEqual(1, len(networks))
        self.assertEqual(self.network_name, networks[0].name)

        subnets = neutron_utils.get_subnets_by_network(neutron, networks[0])
        self.assertEqual(1, len(subnets))
        self.assertEqual(self.subnet_name, subnets[0].name)

        nova = nova_utils.nova_client(self.os_creds, self.os_session)
        keystone = keystone_utils.keystone_client(
            self.os_creds, self.os_session)
        servers = heat_utils.get_stack_servers(
            self.heat_client, nova, neutron, keystone, self.stack1,
            self.os_creds.project_name)
        self.assertIsNotNone(servers)
        self.assertEqual(1, len(servers))
        self.assertEqual(self.vm_inst_name, servers[0].name)

    def test_create_stack_x2(self):
        """
        Tests the creation of an OpenStack keypair that does not exist.
        """
        self.stack1 = heat_utils.create_stack(self.heat_client,
                                              self.stack_settings1)

        stack1_query_1 = heat_utils.get_stack(
            self.heat_client, stack_settings=self.stack_settings1)
        self.assertEqual(self.stack1, stack1_query_1)

        stack1_query_2 = heat_utils.get_stack(
            self.heat_client, stack_name=self.stack_settings1.name)
        self.assertEqual(self.stack1, stack1_query_2)

        stack1_query_3 = heat_utils.get_stack_by_id(self.heat_client,
                                                    self.stack1.id)
        self.assertEqual(self.stack1, stack1_query_3)

        self.assertTrue(stack_active(self.heat_client, self.stack1))

        self.stack2 = heat_utils.create_stack(self.heat_client,
                                              self.stack_settings2)

        stack2_query_1 = heat_utils.get_stack(
            self.heat_client, stack_settings=self.stack_settings2)
        self.assertEqual(self.stack2, stack2_query_1)

        stack2_query_2 = heat_utils.get_stack(
            self.heat_client, stack_name=self.stack_settings2.name)
        self.assertEqual(self.stack2, stack2_query_2)

        stack2_query_3 = heat_utils.get_stack_by_id(self.heat_client,
                                                    self.stack2.id)
        self.assertEqual(self.stack2, stack2_query_3)

        self.assertTrue(stack_active(self.heat_client, self.stack2))


class HeatUtilsCreateComplexStackTests(OSComponentTestCase):
    """
    Test basic Heat functionality
    """

    def setUp(self):
        """
        Instantiates OpenStack instances that cannot be spawned by Heat
        """
        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        stack_name = guid + '-stack'
        self.network_name = guid + '-net'
        self.subnet_name = guid + '-subnet'
        self.vm_inst1_name = guid + '-inst1'
        self.vm_inst2_name = guid + '-inst2'
        self.flavor1_name = guid + '-flavor1'
        self.flavor2_name = guid + '-flavor2'
        self.keypair_name = guid + '-keypair'

        self.image_creator1 = OpenStackImage(
            self.os_creds, openstack_tests.cirros_image_settings(
                name=guid + '-image1', image_metadata=self.image_metadata))
        self.image_creator1.create()

        self.image_creator2 = OpenStackImage(
            self.os_creds, openstack_tests.cirros_image_settings(
                name=guid + '-image2', image_metadata=self.image_metadata))
        self.image_creator2.create()

        env_values = {'image1_name': self.image_creator1.image_settings.name,
                      'image2_name': self.image_creator2.image_settings.name,
                      'flavor1_name': self.flavor1_name,
                      'flavor2_name': self.flavor2_name,
                      'net_name': self.network_name,
                      'subnet_name': self.subnet_name,
                      'keypair_name': self.keypair_name,
                      'inst1_name': self.vm_inst1_name,
                      'inst2_name': self.vm_inst2_name,
                      'external_net_name': self.ext_net_name}
        heat_tmplt_path = pkg_resources.resource_filename(
            'snaps.openstack.tests.heat', 'floating_ip_heat_template.yaml')
        stack_settings = StackConfig(
            name=stack_name, template_path=heat_tmplt_path,
            env_values=env_values)
        self.heat_client = heat_utils.heat_client(
            self.os_creds, self.os_session)
        self.stack = heat_utils.create_stack(self.heat_client, stack_settings)

        self.assertTrue(stack_active(self.heat_client, self.stack))

        self.keypair1_settings = None
        self.keypair2_settings = None

    def tearDown(self):
        """
        Cleans the stack and image
        """
        if self.stack:
            try:
                heat_utils.delete_stack(self.heat_client, self.stack)
                # Wait until stack deployment has completed
                end_time = (time.time() +
                            stack_config.STACK_COMPLETE_TIMEOUT)
                is_deleted = False
                while time.time() < end_time:
                    status = heat_utils.get_stack_status(self.heat_client,
                                                         self.stack.id)
                    if status == stack_config.STATUS_DELETE_COMPLETE:
                        is_deleted = True
                        break
                    elif status == stack_config.STATUS_DELETE_FAILED:
                        is_deleted = False
                        break

                    time.sleep(3)

                if not is_deleted:
                    nova = nova_utils.nova_client(
                        self.os_creds, self.os_session)
                    keystone = keystone_utils.keystone_client(
                        self.os_creds, self.os_session)
                    neutron = neutron_utils.neutron_client(
                        self.os_creds, self.os_session)
                    glance = glance_utils.glance_client(
                        self.os_creds, self.os_session)

                    servers = heat_utils.get_stack_servers(
                        self.heat_client, nova, neutron, keystone, self.stack,
                        self.os_creds.project_name)
                    for server in servers:
                        vm_settings = settings_utils.create_vm_inst_config(
                            nova, keystone, neutron, server,
                            self.os_creds.project_name)
                        img_settings = settings_utils.determine_image_config(
                            glance, server,
                            [self.image_creator1.image_settings,
                             self.image_creator2.image_settings])
                        vm_creator = OpenStackVmInstance(
                            self.os_creds, vm_settings, img_settings)
                        vm_creator.initialize()
                        vm_creator.clean()
                        vm_creator.vm_deleted(block=True)

                    heat_utils.delete_stack(self.heat_client, self.stack)
                    time.sleep(20)
            except:
                    raise

        if self.image_creator1:
            try:
                self.image_creator1.clean()
            except:
                pass

        if self.image_creator2:
            try:
                self.image_creator2.clean()
            except:
                pass

        if self.keypair1_settings:
            expanded_path = os.path.expanduser(
                self.keypair1_settings.private_filepath)
            os.chmod(expanded_path, 0o755)
            os.remove(expanded_path)

        if self.keypair2_settings:
            expanded_path = os.path.expanduser(
                self.keypair2_settings.private_filepath)
            os.chmod(expanded_path, 0o755)
            os.remove(expanded_path)

        super(self.__class__, self).__clean__()

    def test_get_settings_from_stack(self):
        """
        Tests that a heat template with floating IPs and can have the proper
        settings derived from settings_utils.py.
        """
        resources = heat_utils.get_resources(self.heat_client, self.stack.id)
        self.assertIsNotNone(resources)
        self.assertEqual(12, len(resources))

        options = heat_utils.get_outputs(self.heat_client, self.stack)
        self.assertIsNotNone(options)
        self.assertEqual(1, len(options))

        neutron = neutron_utils.neutron_client(self.os_creds, self.os_session)
        networks = heat_utils.get_stack_networks(
            self.heat_client, neutron, self.stack)
        self.assertIsNotNone(networks)
        self.assertEqual(1, len(networks))
        self.assertEqual(self.network_name, networks[0].name)

        network_settings = settings_utils.create_network_config(
            neutron, networks[0])
        self.assertIsNotNone(network_settings)
        self.assertEqual(self.network_name, network_settings.name)

        nova = nova_utils.nova_client(self.os_creds, self.os_session)
        glance = glance_utils.glance_client(self.os_creds, self.os_session)
        keystone = keystone_utils.keystone_client(
            self.os_creds, self.os_session)
        servers = heat_utils.get_stack_servers(
            self.heat_client, nova, neutron, keystone, self.stack,
            self.os_creds.project_name)
        self.assertIsNotNone(servers)
        self.assertEqual(2, len(servers))

        image_settings = settings_utils.determine_image_config(
            glance, servers[0],
            [self.image_creator1.image_settings,
             self.image_creator2.image_settings])

        self.assertIsNotNone(image_settings)
        if image_settings.name.endswith('1'):
            self.assertEqual(
                self.image_creator1.image_settings.name, image_settings.name)
        else:
            self.assertEqual(
                self.image_creator2.image_settings.name, image_settings.name)

        image_settings = settings_utils.determine_image_config(
            glance, servers[1],
            [self.image_creator1.image_settings,
             self.image_creator2.image_settings])
        if image_settings.name.endswith('1'):
            self.assertEqual(
                self.image_creator1.image_settings.name, image_settings.name)
        else:
            self.assertEqual(
                self.image_creator2.image_settings.name, image_settings.name)

        self.keypair1_settings = settings_utils.determine_keypair_config(
            self.heat_client, self.stack, servers[0],
            priv_key_key='private_key')
        self.assertIsNotNone(self.keypair1_settings)
        self.assertEqual(self.keypair_name, self.keypair1_settings.name)

        self.keypair2_settings = settings_utils.determine_keypair_config(
            self.heat_client, self.stack, servers[1],
            priv_key_key='private_key')
        self.assertIsNotNone(self.keypair2_settings)
        self.assertEqual(self.keypair_name, self.keypair2_settings.name)


class HeatUtilsRouterTests(OSComponentTestCase):
    """
    Test Heat volume functionality
    """

    def setUp(self):
        """
        Instantiates OpenStack instances that cannot be spawned by Heat
        """
        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        stack_name = guid + '-stack'

        self.net_name = guid + '-net'
        self.subnet_name = guid + '-subnet'
        self.router_name = guid + '-router'

        env_values = {
            'net_name': self.net_name,
            'subnet_name': self.subnet_name,
            'router_name': self.router_name,
            'external_net_name': self.ext_net_name}

        heat_tmplt_path = pkg_resources.resource_filename(
            'snaps.openstack.tests.heat', 'router_heat_template.yaml')
        self.stack_settings = StackConfig(
            name=stack_name, template_path=heat_tmplt_path,
            env_values=env_values)
        self.stack = None
        self.heat_client = heat_utils.heat_client(
            self.os_creds, self.os_session)
        self.neutron = neutron_utils.neutron_client(
            self.os_creds, self.os_session)

    def tearDown(self):
        """
        Cleans the image and downloaded image file
        """
        if self.stack:
            try:
                heat_utils.delete_stack(self.heat_client, self.stack)
            except:
                pass

        super(self.__class__, self).__clean__()

    def test_create_router_with_stack(self):
        """
        Tests the creation of an OpenStack router with Heat and the retrieval
        of the Router Domain objects from heat_utils#get_stack_routers().
        """
        self.stack = heat_utils.create_stack(
            self.heat_client, self.stack_settings)

        # Wait until stack deployment has completed
        end_time = time.time() + stack_config.STACK_COMPLETE_TIMEOUT
        is_active = False
        while time.time() < end_time:
            status = heat_utils.get_stack_status(self.heat_client,
                                                 self.stack.id)
            if status == stack_config.STATUS_CREATE_COMPLETE:
                is_active = True
                break
            elif status == stack_config.STATUS_CREATE_FAILED:
                is_active = False
                break

            time.sleep(3)

        self.assertTrue(is_active)

        routers = heat_utils.get_stack_routers(
            self.heat_client, self.neutron, self.stack)

        self.assertEqual(1, len(routers))

        router = routers[0]
        self.assertEqual(self.router_name, router.name)

        keystone = keystone_utils.keystone_client(
            self.os_creds, self.os_session)
        ext_net = neutron_utils.get_network(
            self.neutron, keystone, network_name=self.ext_net_name)
        self.assertEqual(ext_net.id, router.external_network_id)


class HeatUtilsVolumeTests(OSComponentTestCase):
    """
    Test Heat volume functionality
    """

    def setUp(self):
        """
        Instantiates OpenStack instances that cannot be spawned by Heat
        """
        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        stack_name = guid + '-stack'
        self.volume_name = guid + '-vol'
        self.volume_type_name = guid + '-vol-type'

        env_values = {
            'volume_name': self.volume_name,
            'volume_type_name': self.volume_type_name}

        heat_tmplt_path = pkg_resources.resource_filename(
            'snaps.openstack.tests.heat', 'volume_heat_template.yaml')
        self.stack_settings = StackConfig(
            name=stack_name, template_path=heat_tmplt_path,
            env_values=env_values)
        self.stack = None
        self.heat_client = heat_utils.heat_client(
            self.os_creds, self.os_session)
        self.cinder = cinder_utils.cinder_client(
            self.os_creds, self.os_session)

    def tearDown(self):
        """
        Cleans the stack
        """
        if self.stack:
            try:
                heat_utils.delete_stack(self.heat_client, self.stack)
            except:
                pass

        super(self.__class__, self).__clean__()

    def test_create_vol_with_stack(self):
        """
        Tests the creation of an OpenStack volume with Heat.
        """
        self.stack = heat_utils.create_stack(
            self.heat_client, self.stack_settings)
        self.assertTrue(stack_active(self.heat_client, self.stack))

        volumes = heat_utils.get_stack_volumes(
            self.heat_client, self.cinder, self.stack)

        self.assertEqual(1, len(volumes))

        volume = volumes[0]
        self.assertEqual(self.volume_name, volume.name)
        self.assertEqual(self.volume_type_name, volume.type)
        self.assertEqual(1, volume.size)
        self.assertEqual(False, volume.multi_attach)

    def test_create_vol_types_with_stack(self):
        """
        Tests the creation of an OpenStack volume with Heat.
        """
        self.stack = heat_utils.create_stack(
            self.heat_client, self.stack_settings)
        self.assertTrue(stack_active(self.heat_client, self.stack))

        volume_types = heat_utils.get_stack_volume_types(
            self.heat_client, self.cinder, self.stack)

        self.assertEqual(1, len(volume_types))

        volume_type = volume_types[0]

        self.assertEqual(self.volume_type_name, volume_type.name)
        self.assertTrue(volume_type.public)
        self.assertIsNone(volume_type.qos_spec)

        # TODO - Add encryption back and find out why it broke in Pike
        # encryption = volume_type.encryption
        # self.assertIsNotNone(encryption)
        # self.assertIsNone(encryption.cipher)
        # self.assertEqual('front-end', encryption.control_location)
        # self.assertIsNone(encryption.key_size)
        # self.assertEqual(u'nova.volume.encryptors.luks.LuksEncryptor',
        #                  encryption.provider)
        # self.assertEqual(volume_type.id, encryption.volume_type_id)


class HeatUtilsFlavorTests(OSComponentTestCase):
    """
    Test Heat volume functionality
    """

    def setUp(self):
        """
        Instantiates OpenStack instances that cannot be spawned by Heat
        """
        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.name_prefix = guid
        stack_name = guid + '-stack'

        heat_tmplt_path = pkg_resources.resource_filename(
            'snaps.openstack.tests.heat', 'flavor_heat_template.yaml')
        self.stack_settings = StackConfig(
            name=stack_name, template_path=heat_tmplt_path)
        self.stack = None
        self.heat_client = heat_utils.heat_client(
            self.os_creds, self.os_session)
        self.nova = nova_utils.nova_client(
            self.os_creds, self.os_session)

    def tearDown(self):
        """
        Cleans the stack
        """
        if self.stack:
            try:
                heat_utils.delete_stack(self.heat_client, self.stack)
            except:
                pass

        super(self.__class__, self).__clean__()

    def test_create_flavor_with_stack(self):
        """
        Tests the creation of an OpenStack volume with Heat.
        """
        self.stack = heat_utils.create_stack(
            self.heat_client, self.stack_settings)

        self.assertTrue(stack_active(self.heat_client, self.stack))

        flavors = heat_utils.get_stack_flavors(
            self.heat_client, self.nova, self.stack)

        self.assertEqual(1, len(flavors))

        flavor = flavors[0]
        self.assertTrue(flavor.name.startswith(self.name_prefix))
        self.assertEqual(1024, flavor.ram)
        self.assertEqual(200, flavor.disk)
        self.assertEqual(8, flavor.vcpus)
        self.assertEqual(0, flavor.ephemeral)
        self.assertIsNone(flavor.swap)
        self.assertEqual(1.0, flavor.rxtx_factor)
        self.assertTrue(flavor.is_public)


class HeatUtilsKeypairTests(OSComponentTestCase):
    """
    Test Heat volume functionality
    """

    def setUp(self):
        """
        Instantiates OpenStack instances that cannot be spawned by Heat
        """
        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        stack_name = guid + '-stack'
        self.keypair_name = guid + '-kp'

        env_values = {'keypair_name': self.keypair_name}

        heat_tmplt_path = pkg_resources.resource_filename(
            'snaps.openstack.tests.heat', 'keypair_heat_template.yaml')
        self.stack_settings = StackConfig(
            name=stack_name, template_path=heat_tmplt_path,
            env_values=env_values)
        self.stack = None
        self.heat_client = heat_utils.heat_client(
            self.os_creds, self.os_session)
        self.nova = nova_utils.nova_client(
            self.os_creds, self.os_session)

    def tearDown(self):
        """
        Cleans the stack
        """
        if self.stack:
            try:
                heat_utils.delete_stack(self.heat_client, self.stack)
            except:
                pass

        super(self.__class__, self).__clean__()

    def test_create_keypair_with_stack(self):
        """
        Tests the creation of an OpenStack keypair with Heat.
        """
        self.stack = heat_utils.create_stack(
            self.heat_client, self.stack_settings)
        self.assertTrue(stack_active(self.heat_client, self.stack))

        keypairs = heat_utils.get_stack_keypairs(
            self.heat_client, self.nova, self.stack)

        self.assertEqual(1, len(keypairs))
        keypair = keypairs[0]

        self.assertEqual(self.keypair_name, keypair.name)

        outputs = heat_utils.get_outputs(self.heat_client, self.stack)

        for output in outputs:
            if output.key == 'private_key':
                self.assertTrue(output.value.startswith(
                    '-----BEGIN RSA PRIVATE KEY-----'))

        keypair = nova_utils.get_keypair_by_id(self.nova, keypair.id)
        self.assertIsNotNone(keypair)

        self.assertEqual(self.keypair_name, keypair.name)


class HeatUtilsSecurityGroupTests(OSComponentTestCase):
    """
    Test Heat volume functionality
    """

    def setUp(self):
        """
        Instantiates OpenStack instances that cannot be spawned by Heat
        """
        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        stack_name = guid + '-stack'
        self.sec_grp_name = guid + '-sec-grp'

        env_values = {'security_group_name': self.sec_grp_name}

        heat_tmplt_path = pkg_resources.resource_filename(
            'snaps.openstack.tests.heat', 'security_group_heat_template.yaml')
        self.stack_settings = StackConfig(
            name=stack_name, template_path=heat_tmplt_path,
            env_values=env_values)
        self.stack = None
        self.heat_client = heat_utils.heat_client(
            self.os_creds, self.os_session)
        self.neutron = neutron_utils.neutron_client(
            self.os_creds, self.os_session)

    def tearDown(self):
        """
        Cleans the stack
        """
        if self.stack:
            try:
                heat_utils.delete_stack(self.heat_client, self.stack)
            except:
                pass

        super(self.__class__, self).__clean__()

    def test_create_security_group_with_stack(self):
        """
        Tests the creation of an OpenStack SecurityGroup with Heat.
        """
        self.stack = heat_utils.create_stack(
            self.heat_client, self.stack_settings)
        self.assertTrue(stack_active(self.heat_client, self.stack))

        sec_grp = heat_utils.get_stack_security_groups(
            self.heat_client, self.neutron, self.stack)[0]

        self.assertEqual(self.sec_grp_name, sec_grp.name)
        self.assertEqual('Test description', sec_grp.description)
        self.assertEqual(2, len(sec_grp.rules))

        has_ssh_rule = False
        has_icmp_rule = False

        for rule in sec_grp.rules:
            if (rule.security_group_id == sec_grp.id
                    and rule.direction == 'egress'
                    and rule.ethertype == 'IPv4'
                    and rule.port_range_min == 22
                    and rule.port_range_max == 22
                    and rule.protocol == 'tcp'
                    and rule.remote_group_id is None
                    and rule.remote_ip_prefix == '0.0.0.0/0'):
                has_ssh_rule = True
            if (rule.security_group_id == sec_grp.id
                    and rule.direction == 'ingress'
                    and rule.ethertype == 'IPv4'
                    and rule.port_range_min is None
                    and rule.port_range_max is None
                    and rule.protocol == 'icmp'
                    and rule.remote_group_id is None
                    and rule.remote_ip_prefix == '0.0.0.0/0'):
                has_icmp_rule = True

        self.assertTrue(has_ssh_rule)
        self.assertTrue(has_icmp_rule)


def stack_active(heat_cli, stack):
    """
    Blocks until stack application has successfully completed or failed
    :param heat_cli: the Heat client
    :param stack: the Stack domain object
    :return: T/F
    """
    # Wait until stack deployment has completed
    end_time = time.time() + stack_config.STACK_COMPLETE_TIMEOUT
    is_active = False
    while time.time() < end_time:
        status = heat_utils.get_stack_status(heat_cli, stack.id)
        if status == stack_config.STATUS_CREATE_COMPLETE:
            is_active = True
            break
        elif status == stack_config.STATUS_CREATE_FAILED:
            is_active = False
            break

        time.sleep(3)

    return is_active
