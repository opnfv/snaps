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
import os
import time

import pkg_resources
from heatclient.exc import HTTPBadRequest

import snaps
from snaps import file_utils
from snaps.config.flavor import FlavorConfig
from snaps.config.image import ImageConfig
from snaps.config.stack import StackConfigError, StackConfig
from snaps.openstack.create_flavor import OpenStackFlavor
from snaps.openstack.create_image import OpenStackImage

try:
    from urllib.request import URLError
except ImportError:
    from urllib2 import URLError

import logging
import unittest
import uuid

from snaps.openstack import create_stack
from snaps.openstack.create_stack import (
    StackSettings, StackCreationError, StackError, OpenStackHeatStack)
from snaps.openstack.tests import openstack_tests, create_instance_tests
from snaps.openstack.tests.os_source_file_test import OSIntegrationTestCase
from snaps.openstack.utils import (
    heat_utils, neutron_utils, nova_utils, keystone_utils)

__author__ = 'spisarski'

logger = logging.getLogger('create_stack_tests')


class StackSettingsUnitTests(unittest.TestCase):
    """
    Tests the construction of the StackSettings class
    """

    def test_no_params(self):
        with self.assertRaises(StackConfigError):
            StackSettings()

    def test_empty_config(self):
        with self.assertRaises(StackConfigError):
            StackSettings(**dict())

    def test_name_only(self):
        with self.assertRaises(StackConfigError):
            StackSettings(name='foo')

    def test_config_with_name_only(self):
        with self.assertRaises(StackConfigError):
            StackSettings(**{'name': 'foo'})

    def test_config_minimum_template(self):
        settings = StackSettings(**{'name': 'stack', 'template': 'foo'})
        self.assertEqual('stack', settings.name)
        self.assertEqual('foo', settings.template)
        self.assertIsNone(settings.template_path)
        self.assertIsNone(settings.env_values)
        self.assertEqual(snaps.config.stack.STACK_COMPLETE_TIMEOUT,
                         settings.stack_create_timeout)

    def test_config_minimum_template_path(self):
        settings = StackSettings(**{'name': 'stack', 'template_path': 'foo'})
        self.assertEqual('stack', settings.name)
        self.assertIsNone(settings.template)
        self.assertEqual('foo', settings.template_path)
        self.assertIsNone(settings.env_values)
        self.assertEqual(snaps.config.stack.STACK_COMPLETE_TIMEOUT,
                         settings.stack_create_timeout)

    def test_minimum_template(self):
        settings = StackSettings(name='stack', template='foo')
        self.assertEqual('stack', settings.name)
        self.assertEqual('foo', settings.template)
        self.assertIsNone(settings.template_path)
        self.assertIsNone(settings.env_values)
        self.assertEqual(snaps.config.stack.STACK_COMPLETE_TIMEOUT,
                         settings.stack_create_timeout)

    def test_minimum_template_path(self):
        settings = StackSettings(name='stack', template_path='foo')
        self.assertEqual('stack', settings.name)
        self.assertEqual('foo', settings.template_path)
        self.assertIsNone(settings.template)
        self.assertIsNone(settings.env_values)
        self.assertEqual(snaps.config.stack.STACK_COMPLETE_TIMEOUT,
                         settings.stack_create_timeout)

    def test_all(self):
        env_values = {'foo': 'bar'}
        settings = StackSettings(name='stack', template='bar',
                                 template_path='foo', env_values=env_values,
                                 stack_create_timeout=999)
        self.assertEqual('stack', settings.name)
        self.assertEqual('bar', settings.template)
        self.assertEqual('foo', settings.template_path)
        self.assertEqual(env_values, settings.env_values)
        self.assertEqual(999, settings.stack_create_timeout)

    def test_config_all(self):
        env_values = {'foo': 'bar'}
        settings = StackSettings(
            **{'name': 'stack', 'template': 'bar', 'template_path': 'foo',
               'env_values': env_values, 'stack_create_timeout': 999})
        self.assertEqual('stack', settings.name)
        self.assertEqual('bar', settings.template)
        self.assertEqual('foo', settings.template_path)
        self.assertEqual(env_values, settings.env_values)
        self.assertEqual(999, settings.stack_create_timeout)


class CreateStackSuccessTests(OSIntegrationTestCase):
    """
    Tests for the OpenStackHeatStack class defined in create_stack.py
    """

    def setUp(self):
        self.user_roles = ['heat_stack_owner']

        super(self.__class__, self).__start__()

        self.guid = self.__class__.__name__ + '-' + str(uuid.uuid4())

        self.heat_cli = heat_utils.heat_client(self.os_creds, self.os_session)
        self.stack_creator = None

        self.image_creator = OpenStackImage(
            self.os_creds, openstack_tests.cirros_image_settings(
                name=self.guid + '-image',
                image_metadata=self.image_metadata))
        self.image_creator.create()

        # Create Flavor
        flavor_config = openstack_tests.get_flavor_config(
            name=self.guid + '-flavor-name', ram=256, disk=10,
            vcpus=1, metadata=self.flavor_metadata)
        self.flavor_creator = OpenStackFlavor(
            self.admin_os_creds, flavor_config)
        self.flavor_creator.create()

        self.network_name = self.guid + '-net'
        self.subnet_name = self.guid + '-subnet'
        self.vm_inst_name = self.guid + '-inst'

        self.env_values = {
            'image_name': self.image_creator.image_settings.name,
            'flavor_name': self.flavor_creator.flavor_settings.name,
            'net_name': self.network_name,
            'subnet_name': self.subnet_name,
            'inst_name': self.vm_inst_name}

        self.heat_tmplt_path = pkg_resources.resource_filename(
            'snaps.openstack.tests.heat', 'test_heat_template.yaml')

    def tearDown(self):
        """
        Cleans the stack and downloaded stack file
        """
        if self.stack_creator:
            try:
                self.stack_creator.clean()
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

    def test_create_stack_template_file(self):
        """
        Tests the creation of an OpenStack stack from Heat template file.
        """
        # Create Stack
        # Set the default stack settings, then set any custom parameters sent
        # from the app
        stack_settings = StackConfig(
            name=self.__class__.__name__ + '-' + str(self.guid) + '-stack',
            template_path=self.heat_tmplt_path,
            env_values=self.env_values)
        self.stack_creator = OpenStackHeatStack(
            self.os_creds, stack_settings)
        created_stack = self.stack_creator.create()
        self.assertIsNotNone(created_stack)

        retrieved_stack = heat_utils.get_stack_by_id(self.heat_cli,
                                                     created_stack.id)
        self.assertIsNotNone(retrieved_stack)
        self.assertEqual(created_stack.name, retrieved_stack.name)
        self.assertEqual(created_stack.id, retrieved_stack.id)
        self.assertEqual(0, len(self.stack_creator.get_outputs()))

        derived_creator = create_stack.generate_creator(
            self.os_creds, retrieved_stack,
            [self.image_creator.image_settings])
        derived_stack = derived_creator.get_stack()
        self.assertEqual(retrieved_stack, derived_stack)

    def test_create_stack_short_timeout(self):
        """
        Tests the creation of an OpenStack stack from Heat template file.
        """
        # Create Stack
        # Set the default stack settings, then set any custom parameters sent
        # from the app
        stack_settings = StackConfig(
            name=self.__class__.__name__ + '-' + str(self.guid) + '-stack',
            template_path=self.heat_tmplt_path,
            env_values=self.env_values, stack_create_timeout=0)

        self.stack_creator = OpenStackHeatStack(
            self.os_creds, stack_settings)
        with self.assertRaises(StackCreationError):
            self.stack_creator.create()

    def test_create_stack_template_dict(self):
        """
        Tests the creation of an OpenStack stack from a heat dict() object.
        """
        # Create Stack
        # Set the default stack settings, then set any custom parameters sent
        # from the app
        template_dict = heat_utils.parse_heat_template_str(
            file_utils.read_file(self.heat_tmplt_path))
        stack_settings = StackConfig(
            name=self.__class__.__name__ + '-' + str(self.guid) + '-stack',
            template=template_dict,
            env_values=self.env_values)
        self.stack_creator = OpenStackHeatStack(
            self.os_creds, stack_settings)
        created_stack = self.stack_creator.create()
        self.assertIsNotNone(created_stack)

        retrieved_stack = heat_utils.get_stack_by_id(self.heat_cli,
                                                     created_stack.id)
        self.assertIsNotNone(retrieved_stack)
        self.assertEqual(created_stack.name, retrieved_stack.name)
        self.assertEqual(created_stack.id, retrieved_stack.id)
        self.assertEqual(0, len(self.stack_creator.get_outputs()))

    def test_create_delete_stack(self):
        """
        Tests the creation then deletion of an OpenStack stack to ensure
        clean() does not raise an Exception.
        """
        # Create Stack
        template_dict = heat_utils.parse_heat_template_str(
            file_utils.read_file(self.heat_tmplt_path))
        stack_settings = StackConfig(
            name=self.__class__.__name__ + '-' + str(self.guid) + '-stack',
            template=template_dict,
            env_values=self.env_values)
        self.stack_creator = OpenStackHeatStack(
            self.os_creds, stack_settings)
        created_stack = self.stack_creator.create()
        self.assertIsNotNone(created_stack)

        retrieved_stack = heat_utils.get_stack_by_id(self.heat_cli,
                                                     created_stack.id)
        self.assertIsNotNone(retrieved_stack)
        self.assertEqual(created_stack.name, retrieved_stack.name)
        self.assertEqual(created_stack.id, retrieved_stack.id)
        self.assertEqual(0, len(self.stack_creator.get_outputs()))
        self.assertEqual(snaps.config.stack.STATUS_CREATE_COMPLETE,
                         self.stack_creator.get_status())

        # Delete Stack manually
        heat_utils.delete_stack(self.heat_cli, created_stack)

        end_time = time.time() + 90
        deleted = False
        while time.time() < end_time:
            status = heat_utils.get_stack_status(self.heat_cli,
                                                 retrieved_stack.id)
            if status == snaps.config.stack.STATUS_DELETE_COMPLETE:
                deleted = True
                break

        self.assertTrue(deleted)

        # Must not throw an exception when attempting to cleanup non-existent
        # stack
        self.stack_creator.clean()
        self.assertIsNone(self.stack_creator.get_stack())

    def test_create_same_stack(self):
        """
        Tests the creation of an OpenStack stack when the stack already exists.
        """
        # Create Stack
        template_dict = heat_utils.parse_heat_template_str(
            file_utils.read_file(self.heat_tmplt_path))
        stack_settings = StackConfig(
            name=self.__class__.__name__ + '-' + str(self.guid) + '-stack',
            template=template_dict,
            env_values=self.env_values)
        self.stack_creator = OpenStackHeatStack(
            self.os_creds, stack_settings)
        created_stack1 = self.stack_creator.create()

        retrieved_stack = heat_utils.get_stack_by_id(self.heat_cli,
                                                     created_stack1.id)
        self.assertIsNotNone(retrieved_stack)
        self.assertEqual(created_stack1.name, retrieved_stack.name)
        self.assertEqual(created_stack1.id, retrieved_stack.id)
        self.assertEqual(0, len(self.stack_creator.get_outputs()))

        # Should be retrieving the instance data
        stack_creator2 = OpenStackHeatStack(self.os_creds, stack_settings)
        stack2 = stack_creator2.create()
        self.assertEqual(created_stack1.id, stack2.id)

    def test_retrieve_network_creators(self):
        """
        Tests the creation of an OpenStack stack from Heat template file and
        the retrieval of the network creator.
        """
        stack_settings = StackConfig(
            name=self.__class__.__name__ + '-' + str(self.guid) + '-stack',
            template_path=self.heat_tmplt_path,
            env_values=self.env_values)
        self.stack_creator = OpenStackHeatStack(
            self.os_creds, stack_settings)
        created_stack = self.stack_creator.create()
        self.assertIsNotNone(created_stack)

        net_creators = self.stack_creator.get_network_creators()
        self.assertIsNotNone(net_creators)
        self.assertEqual(1, len(net_creators))
        self.assertEqual(self.network_name, net_creators[0].get_network().name)

        # Need to use 'admin' creds as heat creates objects under it's own
        # project/tenant
        neutron = neutron_utils.neutron_client(
            self.os_creds, self.os_session)
        keystone = keystone_utils.keystone_client(
            self.os_creds, self.os_session)
        net_by_name = neutron_utils.get_network(
            neutron, keystone, network_name=net_creators[0].get_network().name)
        self.assertEqual(net_creators[0].get_network(), net_by_name)
        self.assertIsNotNone(neutron_utils.get_network_by_id(
            neutron, net_creators[0].get_network().id))

        self.assertEqual(1, len(net_creators[0].get_network().subnets))
        subnet = net_creators[0].get_network().subnets[0]
        subnet_by_name = neutron_utils.get_subnet(
            neutron, net_creators[0].get_network(), subnet_name=subnet.name)
        self.assertEqual(subnet, subnet_by_name)

        subnet_by_id = neutron_utils.get_subnet_by_id(neutron, subnet.id)
        self.assertIsNotNone(subnet_by_id)
        self.assertEqual(subnet_by_name, subnet_by_id)

    def test_retrieve_vm_inst_creators(self):
        """
        Tests the creation of an OpenStack stack from Heat template file and
        the retrieval of the network creator.
        """
        stack_settings = StackConfig(
            name=self.__class__.__name__ + '-' + str(self.guid) + '-stack',
            template_path=self.heat_tmplt_path,
            env_values=self.env_values)
        self.stack_creator = OpenStackHeatStack(
            self.os_creds, stack_settings)
        created_stack = self.stack_creator.create()
        self.assertIsNotNone(created_stack)

        vm_inst_creators = self.stack_creator.get_vm_inst_creators()
        self.assertIsNotNone(vm_inst_creators)
        self.assertEqual(1, len(vm_inst_creators))
        self.assertEqual(self.vm_inst_name,
                         vm_inst_creators[0].get_vm_inst().name)

        nova = nova_utils.nova_client(self.os_creds, self.os_session)
        neutron = neutron_utils.neutron_client(self.os_creds, self.os_session)
        keystone = keystone_utils.keystone_client(self.os_creds, self.os_session)
        vm_inst_by_name = nova_utils.get_server(
            nova, neutron, keystone,
            server_name=vm_inst_creators[0].get_vm_inst().name)

        self.assertEqual(vm_inst_creators[0].get_vm_inst(), vm_inst_by_name)
        self.assertIsNotNone(nova_utils.get_server_object_by_id(
            nova, neutron, keystone, vm_inst_creators[0].get_vm_inst().id))


class CreateStackFloatingIpTests(OSIntegrationTestCase):
    """
    Tests to ensure that floating IPs can be accessed via an
    OpenStackVmInstance object obtained from the OpenStackHeatStack instance
    """

    def setUp(self):
        self.user_roles = ['heat_stack_owner', 'admin']

        super(self.__class__, self).__start__()

        self.guid = self.__class__.__name__ + '-' + str(uuid.uuid4())

        self.heat_cli = heat_utils.heat_client(self.os_creds, self.os_session)
        self.stack_creator = None

        self.image_creator = OpenStackImage(
            self.os_creds, openstack_tests.cirros_image_settings(
                name=self.guid + '-image',
                image_metadata=self.image_metadata))
        self.image_creator.create()

        self.network_name = self.guid + '-net'
        self.subnet_name = self.guid + '-subnet'
        self.flavor1_name = self.guid + '-flavor1'
        self.flavor2_name = self.guid + '-flavor2'
        self.sec_grp_name = self.guid + '-sec_grp'
        self.vm_inst1_name = self.guid + '-inst1'
        self.vm_inst2_name = self.guid + '-inst2'
        self.keypair_name = self.guid + '-kp'

        self.env_values = {
            'image1_name': self.image_creator.image_settings.name,
            'image2_name': self.image_creator.image_settings.name,
            'flavor1_name': self.flavor1_name,
            'flavor2_name': self.flavor2_name,
            'net_name': self.network_name,
            'subnet_name': self.subnet_name,
            'inst1_name': self.vm_inst1_name,
            'inst2_name': self.vm_inst2_name,
            'keypair_name': self.keypair_name,
            'external_net_name': self.ext_net_name,
            'security_group_name': self.sec_grp_name}

        self.heat_tmplt_path = pkg_resources.resource_filename(
            'snaps.openstack.tests.heat', 'floating_ip_heat_template.yaml')

        self.vm_inst_creators = list()

    def tearDown(self):
        """
        Cleans the stack and downloaded stack file
        """
        if self.stack_creator:
            try:
                self.stack_creator.clean()
            except:
                pass

        if self.image_creator:
            try:
                self.image_creator.clean()
            except:
                pass

        for vm_inst_creator in self.vm_inst_creators:
            try:
                keypair_settings = vm_inst_creator.keypair_settings
                if keypair_settings and keypair_settings.private_filepath:
                    expanded_path = os.path.expanduser(
                        keypair_settings.private_filepath)
                    os.chmod(expanded_path, 0o755)
                    os.remove(expanded_path)
            except:
                pass

        super(self.__class__, self).__clean__()

    def test_connect_via_ssh_heat_vm(self):
        """
        Tests the creation of an OpenStack stack from Heat template file and
        the retrieval of two VM instance creators and attempt to connect via
        SSH to the first one with a floating IP.
        """
        stack_settings = StackConfig(
            name=self.__class__.__name__ + '-' + str(self.guid) + '-stack',
            template_path=self.heat_tmplt_path,
            env_values=self.env_values)
        self.stack_creator = OpenStackHeatStack(
            self.os_creds, stack_settings,
            [self.image_creator.image_settings])
        created_stack = self.stack_creator.create()
        self.assertIsNotNone(created_stack)

        self.vm_inst_creators = self.stack_creator.get_vm_inst_creators(
            heat_keypair_option='private_key')
        self.assertIsNotNone(self.vm_inst_creators)
        self.assertEqual(2, len(self.vm_inst_creators))

        for vm_inst_creator in self.vm_inst_creators:
            if vm_inst_creator.get_vm_inst().name == self.vm_inst1_name:
                self.assertTrue(
                    create_instance_tests.validate_ssh_client(vm_inst_creator))
            else:
                vm_settings = vm_inst_creator.instance_settings
                self.assertEqual(0, len(vm_settings.floating_ip_settings))

    def test_connect_via_ssh_heat_vm_derived(self):
        """
        Tests the the retrieval of two VM instance creators from a derived
        OpenStackHeatStack object and attempt to connect via
        SSH to the first one with a floating IP.
        """
        stack_settings = StackConfig(
            name=self.__class__.__name__ + '-' + str(self.guid) + '-stack',
            template_path=self.heat_tmplt_path,
            env_values=self.env_values)
        self.stack_creator = OpenStackHeatStack(
            self.os_creds, stack_settings,
            [self.image_creator.image_settings])
        created_stack = self.stack_creator.create()
        self.assertIsNotNone(created_stack)

        derived_stack = create_stack.generate_creator(
            self.os_creds, created_stack,
            [self.image_creator.image_settings])

        self.vm_inst_creators = derived_stack.get_vm_inst_creators(
            heat_keypair_option='private_key')
        self.assertIsNotNone(self.vm_inst_creators)
        self.assertEqual(2, len(self.vm_inst_creators))

        for vm_inst_creator in self.vm_inst_creators:
            if vm_inst_creator.get_vm_inst().name == self.vm_inst1_name:
                self.assertTrue(
                    create_instance_tests.validate_ssh_client(vm_inst_creator))
            else:
                vm_settings = vm_inst_creator.instance_settings
                self.assertEqual(0, len(vm_settings.floating_ip_settings))


class CreateStackNestedResourceTests(OSIntegrationTestCase):
    """
    Tests to ensure that nested heat templates work
    """

    def setUp(self):
        self.user_roles = ['heat_stack_owner']

        super(self.__class__, self).__start__()

        self.guid = self.__class__.__name__ + '-' + str(uuid.uuid4())

        self.heat_cli = heat_utils.heat_client(self.os_creds, self.os_session)
        self.stack_creator = None

        self.image_creator = OpenStackImage(
            self.os_creds, openstack_tests.cirros_image_settings(
                name=self.guid + '-image',
                image_metadata=self.image_metadata))
        self.image_creator.create()

        self.flavor_creator = OpenStackFlavor(
            self.admin_os_creds,
            FlavorConfig(
                name=self.guid + '-flavor-name', ram=256, disk=10, vcpus=1))
        self.flavor_creator.create()

        env_values = {
            'network_name': self.guid + '-network',
            'public_network': self.ext_net_name,
            'agent_image': self.image_creator.image_settings.name,
            'agent_flavor': self.flavor_creator.flavor_settings.name,
            'key_name': self.guid + '-key',
        }

        heat_tmplt_path = pkg_resources.resource_filename(
            'snaps.openstack.tests.heat', 'agent-group.yaml')
        heat_resource_path = pkg_resources.resource_filename(
            'snaps.openstack.tests.heat', 'agent.yaml')

        stack_settings = StackConfig(
            name=self.__class__.__name__ + '-' + str(self.guid) + '-stack',
            template_path=heat_tmplt_path,
            resource_files=[heat_resource_path],
            env_values=env_values)

        self.stack_creator = OpenStackHeatStack(
            self.os_creds, stack_settings,
            [self.image_creator.image_settings])

        self.vm_inst_creators = list()

    def tearDown(self):
        """
        Cleans the stack and downloaded stack file
        """
        if self.stack_creator:
            try:
                self.stack_creator.clean()
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

        for vm_inst_creator in self.vm_inst_creators:
            try:
                keypair_settings = vm_inst_creator.keypair_settings
                if keypair_settings and keypair_settings.private_filepath:
                    expanded_path = os.path.expanduser(
                        keypair_settings.private_filepath)
                    os.chmod(expanded_path, 0o755)
                    os.remove(expanded_path)
            except:
                pass

        super(self.__class__, self).__clean__()

    def test_nested(self):
        """
        Tests the creation of an OpenStack stack from Heat template file and
        the retrieval of two VM instance creators and attempt to connect via
        SSH to the first one with a floating IP.
        """
        created_stack = self.stack_creator.create()
        self.assertIsNotNone(created_stack)

        self.vm_inst_creators = self.stack_creator.get_vm_inst_creators(
            heat_keypair_option='private_key')
        self.assertIsNotNone(self.vm_inst_creators)
        self.assertEqual(1, len(self.vm_inst_creators))

        for vm_inst_creator in self.vm_inst_creators:
            self.assertTrue(
                create_instance_tests.validate_ssh_client(vm_inst_creator))


class CreateStackRouterTests(OSIntegrationTestCase):
    """
    Tests for the CreateStack class defined in create_stack.py where the
    target is a Network, Subnet, and Router
    """

    def setUp(self):
        """
        Instantiates the CreateStack object that is responsible for downloading
        and creating an OS stack file within OpenStack
        """
        self.user_roles = ['heat_stack_owner']

        super(self.__class__, self).__start__()

        self.guid = self.__class__.__name__ + '-' + str(uuid.uuid4())

        self.heat_cli = heat_utils.heat_client(self.os_creds, self.os_session)
        self.neutron = neutron_utils.neutron_client(
            self.os_creds, self.os_session)
        self.stack_creator = None

        self.net_name = self.guid + '-net'
        self.subnet_name = self.guid + '-subnet'
        self.router_name = self.guid + '-router'

        self.env_values = {
            'net_name': self.net_name,
            'subnet_name': self.subnet_name,
            'router_name': self.router_name,
            'external_net_name': self.ext_net_name}

        self.heat_tmplt_path = pkg_resources.resource_filename(
            'snaps.openstack.tests.heat', 'router_heat_template.yaml')

        stack_settings = StackConfig(
            name=self.__class__.__name__ + '-' + str(self.guid) + '-stack',
            template_path=self.heat_tmplt_path,
            env_values=self.env_values)
        self.stack_creator = OpenStackHeatStack(
            self.os_creds, stack_settings)
        self.created_stack = self.stack_creator.create()
        self.assertIsNotNone(self.created_stack)

    def tearDown(self):
        """
        Cleans the stack and downloaded stack file
        """
        if self.stack_creator:
            try:
                self.stack_creator.clean()
            except:
                pass

        super(self.__class__, self).__clean__()

    def test_retrieve_router_creator(self):
        """
        Tests the creation of an OpenStack stack from Heat template file and
        the retrieval of an OpenStackRouter creator/state machine instance
        """
        router_creators = self.stack_creator.get_router_creators()
        self.assertEqual(1, len(router_creators))

        creator = router_creators[0]
        self.assertEqual(self.router_name, creator.router_settings.name)

        router = creator.get_router()

        ext_net = neutron_utils.get_network(
            self.neutron, self.keystone, network_name=self.ext_net_name)
        self.assertEqual(ext_net.id, router.external_network_id)


class CreateStackVolumeTests(OSIntegrationTestCase):
    """
    Tests to ensure that floating IPs can be accessed via an
    OpenStackVolume object obtained from the OpenStackHeatStack instance
    """

    def setUp(self):

        self.user_roles = ['heat_stack_owner', 'admin']

        super(self.__class__, self).__start__()

        self.guid = self.__class__.__name__ + '-' + str(uuid.uuid4())

        self.heat_cli = heat_utils.heat_client(self.os_creds, self.os_session)
        self.stack_creator = None

        self.volume_name = self.guid + '-volume'
        self.volume_type_name = self.guid + '-volume-type'

        self.env_values = {
            'volume_name': self.volume_name,
            'volume_type_name': self.volume_type_name}

        self.heat_tmplt_path = pkg_resources.resource_filename(
            'snaps.openstack.tests.heat', 'volume_heat_template.yaml')

        stack_settings = StackConfig(
            name=self.__class__.__name__ + '-' + str(self.guid) + '-stack',
            template_path=self.heat_tmplt_path,
            env_values=self.env_values)
        self.stack_creator = OpenStackHeatStack(
            self.os_creds, stack_settings)
        self.created_stack = self.stack_creator.create()
        self.assertIsNotNone(self.created_stack)

    def tearDown(self):
        """
        Cleans the stack and downloaded stack file
        """
        if self.stack_creator:
            try:
                self.stack_creator.clean()
            except:
                pass

        super(self.__class__, self).__clean__()

    def test_retrieve_volume_creator(self):
        """
        Tests the creation of an OpenStack stack from Heat template file and
        the retrieval of an OpenStackVolume creator/state machine instance
        """
        volume_creators = self.stack_creator.get_volume_creators()
        self.assertEqual(1, len(volume_creators))

        creator = volume_creators[0]
        self.assertEqual(self.volume_name, creator.volume_settings.name)
        self.assertEqual(self.volume_name, creator.get_volume().name)
        self.assertEqual(self.volume_type_name,
                         creator.volume_settings.type_name)
        self.assertEqual(self.volume_type_name, creator.get_volume().type)
        self.assertEqual(1, creator.volume_settings.size)
        self.assertEqual(1, creator.get_volume().size)

    def test_retrieve_volume_type_creator(self):
        """
        Tests the creation of an OpenStack stack from Heat template file and
        the retrieval of an OpenStackVolume creator/state machine instance
        """
        volume_type_creators = self.stack_creator.get_volume_type_creators()
        self.assertEqual(1, len(volume_type_creators))

        creator = volume_type_creators[0]
        self.assertIsNotNone(creator)

        volume_type = creator.get_volume_type()
        self.assertIsNotNone(volume_type)

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


class CreateStackFlavorTests(OSIntegrationTestCase):
    """
    Tests to ensure that floating IPs can be accessed via an
    OpenStackFlavor object obtained from the OpenStackHeatStack instance
    """

    def setUp(self):

        self.user_roles = ['heat_stack_owner', 'admin']

        super(self.__class__, self).__start__()

        self.guid = self.__class__.__name__ + '-' + str(uuid.uuid4())

        self.heat_cli = heat_utils.heat_client(self.os_creds, self.os_session)
        self.stack_creator = None

        self.heat_tmplt_path = pkg_resources.resource_filename(
            'snaps.openstack.tests.heat', 'flavor_heat_template.yaml')

        stack_settings = StackConfig(
            name=self.guid + '-stack',
            template_path=self.heat_tmplt_path)
        self.stack_creator = OpenStackHeatStack(
            self.os_creds, stack_settings)
        self.created_stack = self.stack_creator.create()
        self.assertIsNotNone(self.created_stack)

    def tearDown(self):
        """
        Cleans the stack and downloaded stack file
        """
        if self.stack_creator:
            try:
                self.stack_creator.clean()
            except:
                pass

        super(self.__class__, self).__clean__()

    def test_retrieve_flavor_creator(self):
        """
        Tests the creation of an OpenStack stack from Heat template file and
        the retrieval of an OpenStackVolume creator/state machine instance
        """
        flavor_creators = self.stack_creator.get_flavor_creators()
        self.assertEqual(1, len(flavor_creators))

        creator = flavor_creators[0]
        self.assertTrue(creator.get_flavor().name.startswith(self.guid))
        self.assertEqual(1024, creator.get_flavor().ram)
        self.assertEqual(200, creator.get_flavor().disk)
        self.assertEqual(8, creator.get_flavor().vcpus)
        self.assertEqual(0, creator.get_flavor().ephemeral)
        self.assertIsNone(creator.get_flavor().swap)
        self.assertEqual(1.0, creator.get_flavor().rxtx_factor)
        self.assertTrue(creator.get_flavor().is_public)


class CreateStackKeypairTests(OSIntegrationTestCase):
    """
    Tests to ensure that floating IPs can be accessed via an
    OpenStackKeypair object obtained from the OpenStackHeatStack instance
    """

    def setUp(self):

        self.user_roles = ['heat_stack_owner']

        super(self.__class__, self).__start__()

        self.guid = self.__class__.__name__ + '-' + str(uuid.uuid4())

        self.heat_cli = heat_utils.heat_client(self.os_creds, self.os_session)
        self.nova = nova_utils.nova_client(self.os_creds, self.os_session)
        self.stack_creator = None

        self.keypair_name = self.guid + '-kp'

        self.env_values = {
            'keypair_name': self.keypair_name}

        self.heat_tmplt_path = pkg_resources.resource_filename(
            'snaps.openstack.tests.heat', 'keypair_heat_template.yaml')

        stack_settings = StackConfig(
            name=self.__class__.__name__ + '-' + str(self.guid) + '-stack',
            template_path=self.heat_tmplt_path,
            env_values=self.env_values)
        self.stack_creator = OpenStackHeatStack(
            self.os_creds, stack_settings)
        self.created_stack = self.stack_creator.create()
        self.assertIsNotNone(self.created_stack)

        self.keypair_creators = list()

    def tearDown(self):
        """
        Cleans the stack and downloaded stack file
        """
        if self.stack_creator:
            try:
                self.stack_creator.clean()
            except:
                pass
        for keypair_creator in self.keypair_creators:
            try:
                keypair_creator.clean()
            except:
                pass

        super(self.__class__, self).__clean__()

    def test_retrieve_keypair_creator(self):
        """
        Tests the creation of an OpenStack stack from Heat template file and
        the retrieval of an OpenStackKeypair creator/state machine instance
        """
        self.kp_creators = self.stack_creator.get_keypair_creators(
            'private_key')
        self.assertEqual(1, len(self.kp_creators))

        self.keypair_creator = self.kp_creators[0]

        self.assertEqual(self.keypair_name,
                         self.keypair_creator.get_keypair().name)
        self.assertIsNotNone(
            self.keypair_creator.keypair_settings.private_filepath)

        private_file_contents = file_utils.read_file(
            self.keypair_creator.keypair_settings.private_filepath)
        self.assertTrue(private_file_contents.startswith(
            '-----BEGIN RSA PRIVATE KEY-----'))

        keypair = nova_utils.get_keypair_by_id(
            self.nova, self.keypair_creator.get_keypair().id)
        self.assertIsNotNone(keypair)
        self.assertEqual(self.keypair_creator.get_keypair(), keypair)


class CreateStackSecurityGroupTests(OSIntegrationTestCase):
    """
    Tests for the OpenStackHeatStack class to ensure it returns an
    OpenStackSecurityGroup object
    """

    def setUp(self):
        """
        Instantiates the CreateStack object that is responsible for downloading
        and creating an OS stack file within OpenStack
        """
        self.user_roles = ['heat_stack_owner']

        super(self.__class__, self).__start__()

        self.guid = self.__class__.__name__ + '-' + str(uuid.uuid4())

        self.heat_cli = heat_utils.heat_client(self.os_creds, self.os_session)
        self.nova = nova_utils.nova_client(self.os_creds, self.os_session)
        self.stack_creator = None

        self.security_group_name = self.guid + '-sec-grp'

        self.env_values = {
            'security_group_name': self.security_group_name}

        self.heat_tmplt_path = pkg_resources.resource_filename(
            'snaps.openstack.tests.heat', 'security_group_heat_template.yaml')

        stack_settings = StackConfig(
            name=self.__class__.__name__ + '-' + str(self.guid) + '-stack',
            template_path=self.heat_tmplt_path,
            env_values=self.env_values)
        self.stack_creator = OpenStackHeatStack(
            self.os_creds, stack_settings)
        self.created_stack = self.stack_creator.create()
        self.assertIsNotNone(self.created_stack)

    def tearDown(self):
        """
        Cleans the stack and downloaded stack file
        """
        if self.stack_creator:
            try:
                self.stack_creator.clean()
            except:
                pass

        super(self.__class__, self).__clean__()

    def test_retrieve_security_group_creator(self):
        """
        Tests the creation of an OpenStack stack from Heat template file and
        the retrieval of an OpenStackSecurityGroup creator/state machine
        instance
        """
        sec_grp_creators = self.stack_creator.get_security_group_creators()
        self.assertEqual(1, len(sec_grp_creators))

        creator = sec_grp_creators[0]
        sec_grp = creator.get_security_group()

        self.assertEqual(self.security_group_name, sec_grp.name)
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


class CreateStackNegativeTests(OSIntegrationTestCase):
    """
    Negative test cases for the OpenStackHeatStack class with poor
    configuration
    """

    def setUp(self):
        self.user_roles = ['heat_stack_owner']

        super(self.__class__, self).__start__()

        self.stack_name = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.stack_creator = None
        self.heat_tmplt_path = pkg_resources.resource_filename(
            'snaps.openstack.tests.heat', 'test_heat_template.yaml')

    def tearDown(self):
        if self.stack_creator:
            self.stack_creator.clean()

        super(self.__class__, self).__clean__()

    def test_missing_dependencies(self):
        """
        Expect an StackCreationError when the stack file does not exist
        """
        stack_settings = StackConfig(name=self.stack_name,
                                     template_path=self.heat_tmplt_path)
        self.stack_creator = OpenStackHeatStack(
            self.os_creds, stack_settings)
        with self.assertRaises(HTTPBadRequest):
            self.stack_creator.create()

    def test_bad_stack_file(self):
        """
        Expect an StackCreationError when the stack file does not exist
        """
        stack_settings = StackConfig(
            name=self.stack_name, template_path='foo')
        self.stack_creator = OpenStackHeatStack(
            self.os_creds, stack_settings)
        with self.assertRaises(IOError):
            self.stack_creator.create()


class CreateStackFailureTests(OSIntegrationTestCase):
    """
    Tests for the OpenStackHeatStack class defined in create_stack.py for
    when failures occur. Failures are being triggered by allocating 1 million
    CPUs.
    """

    def setUp(self):
        self.user_roles = ['heat_stack_owner']

        super(self.__class__, self).__start__()

        self.guid = self.__class__.__name__ + '-' + str(uuid.uuid4())

        self.heat_cli = heat_utils.heat_client(self.os_creds, self.os_session)
        self.stack_creator = None

        self.tmp_file = file_utils.save_string_to_file(
            ' ', str(uuid.uuid4()) + '-bad-image')
        self.image_creator = OpenStackImage(
            self.os_creds, ImageConfig(
                name=self.guid + 'image', image_file=self.tmp_file.name,
                image_user='foo', img_format='qcow2'))
        self.image_creator.create()

        # Create Flavor
        self.flavor_creator = OpenStackFlavor(
            self.admin_os_creds,
            FlavorConfig(
                name=self.guid + '-flavor-name', ram=256, disk=10,
                vcpus=1000000))
        self.flavor_creator.create()

        self.network_name = self.guid + '-net'
        self.subnet_name = self.guid + '-subnet'
        self.vm_inst_name = self.guid + '-inst'

        self.env_values = {
            'image_name': self.image_creator.image_settings.name,
            'flavor_name': self.flavor_creator.flavor_settings.name,
            'net_name': self.network_name,
            'subnet_name': self.subnet_name,
            'inst_name': self.vm_inst_name}

        self.heat_tmplt_path = pkg_resources.resource_filename(
            'snaps.openstack.tests.heat', 'test_heat_template.yaml')

    def tearDown(self):
        """
        Cleans the stack and downloaded stack file
        """
        if self.stack_creator:
            try:
                self.stack_creator.clean()
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

        if self.tmp_file:
            try:
                os.remove(self.tmp_file.name)
            except:
                pass

        super(self.__class__, self).__clean__()

    def test_stack_failure(self):
        """
        Tests the creation of an OpenStack stack from Heat template file that
        should always fail due to too many CPU cores
        """
        # Create Stack
        # Set the default stack settings, then set any custom parameters sent
        # from the app
        stack_settings = StackConfig(
            name=self.__class__.__name__ + '-' + str(self.guid) + '-stack',
            template_path=self.heat_tmplt_path,
            env_values=self.env_values)
        self.stack_creator = OpenStackHeatStack(
            self.os_creds, stack_settings)

        with self.assertRaises(StackError):
            try:
                self.stack_creator.create()
            except StackError:
                resources = heat_utils.get_resources(
                    self.heat_cli, self.stack_creator.get_stack().id)

                found = False
                for resource in resources:
                    if (resource.status ==
                            snaps.config.stack.STATUS_CREATE_COMPLETE):
                        found = True
                self.assertTrue(found)
                raise
