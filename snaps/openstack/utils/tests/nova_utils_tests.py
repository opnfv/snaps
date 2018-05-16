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
import time
import uuid

import os

from snaps import file_utils
from snaps.config.flavor import FlavorConfig
from snaps.config.network import PortConfig
from snaps.config.vm_inst import VmInstanceConfig
from snaps.config.volume import VolumeConfig
from snaps.openstack import create_instance
from snaps.openstack.create_flavor import OpenStackFlavor
from snaps.openstack.create_image import OpenStackImage
from snaps.openstack.create_instance import OpenStackVmInstance
from snaps.openstack.create_network import OpenStackNetwork
from snaps.openstack.create_volume import OpenStackVolume
from snaps.openstack.tests import openstack_tests
from snaps.openstack.tests.os_source_file_test import OSComponentTestCase
from snaps.openstack.utils import (
    nova_utils, neutron_utils, glance_utils, cinder_utils, keystone_utils)
from snaps.openstack.utils.nova_utils import NovaException

__author__ = 'spisarski'

logger = logging.getLogger('nova_utils_tests')


class NovaSmokeTests(OSComponentTestCase):
    """
    Tests to ensure that the nova client can communicate with the cloud
    """

    def test_nova_connect_success(self):
        """
        Tests to ensure that the proper credentials can connect.
        """
        nova = nova_utils.nova_client(self.os_creds, self.os_session)

        # This should not throw an exception
        nova.flavors.list()

    def test_nova_get_hypervisor_hosts(self):
        """
        Tests to ensure that get_hypervisors() function works.
        """
        nova = nova_utils.nova_client(self.os_creds, self.os_session)

        hosts = nova_utils.get_hypervisor_hosts(nova)
        # This should not throw an exception
        self.assertGreaterEqual(len(hosts), 1)

    def test_nova_connect_fail(self):
        """
        Tests to ensure that the improper credentials cannot connect.
        """
        from snaps.openstack.os_credentials import OSCreds

        nova = nova_utils.nova_client(
            OSCreds(username='user', password='pass',
                    auth_url=self.os_creds.auth_url,
                    project_name=self.os_creds.project_name,
                    proxy_settings=self.os_creds.proxy_settings))

        # This should throw an exception
        with self.assertRaises(Exception):
            nova.flavors.list()


class NovaUtilsKeypairTests(OSComponentTestCase):
    """
    Test basic nova keypair functionality
    """

    def setUp(self):
        """
        Instantiates the CreateImage object that is responsible for downloading
        and creating an OS image file within OpenStack
        """
        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.priv_key_file_path = 'tmp/' + guid
        self.pub_key_file_path = self.priv_key_file_path + '.pub'

        self.nova = nova_utils.nova_client(self.os_creds, self.os_session)
        self.keys = nova_utils.create_keys()
        self.public_key = nova_utils.public_key_openssh(self.keys)
        self.keypair_name = guid
        self.keypair = None

    def tearDown(self):
        """
        Cleans the image and downloaded image file
        """
        if self.keypair:
            try:
                nova_utils.delete_keypair(self.nova, self.keypair)
            except:
                pass

        try:
            os.chmod(self.priv_key_file_path, 0o777)
            os.remove(self.priv_key_file_path)
        except:
            pass

        try:
            os.chmod(self.pub_key_file_path, 0o777)
            os.remove(self.pub_key_file_path)
        except:
            pass

        super(self.__class__, self).__clean__()

    def test_create_keypair(self):
        """
        Tests the creation of an OpenStack keypair that does not exist.
        """
        self.keypair = nova_utils.upload_keypair(self.nova, self.keypair_name,
                                                 self.public_key)
        result = nova_utils.keypair_exists(self.nova, self.keypair)
        self.assertEqual(self.keypair, result)
        keypair = nova_utils.get_keypair_by_name(self.nova, self.keypair_name)
        self.assertEqual(self.keypair, keypair)

    def test_create_delete_keypair(self):
        """
        Tests the creation of an OpenStack keypair that does not exist.
        """
        self.keypair = nova_utils.upload_keypair(self.nova, self.keypair_name,
                                                 self.public_key)
        result = nova_utils.keypair_exists(self.nova, self.keypair)
        self.assertEqual(self.keypair, result)
        nova_utils.delete_keypair(self.nova, self.keypair)
        result2 = nova_utils.keypair_exists(self.nova, self.keypair)
        self.assertIsNone(result2)

    def test_create_key_from_file(self):
        """
        Tests that the generated RSA keys are properly saved to files
        :return:
        """
        file_utils.save_keys_to_files(self.keys, self.pub_key_file_path,
                                      self.priv_key_file_path)
        self.keypair = nova_utils.upload_keypair_file(self.nova,
                                                      self.keypair_name,
                                                      self.pub_key_file_path)
        pub_key_file = open(os.path.expanduser(self.pub_key_file_path))
        pub_key = pub_key_file.read()
        pub_key_file.close()
        self.assertEqual(self.keypair.public_key, pub_key)


class NovaUtilsFlavorTests(OSComponentTestCase):
    """
    Test basic nova flavor functionality
    """

    def setUp(self):
        """
        Instantiates the CreateImage object that is responsible for downloading
        and creating an OS image file within OpenStack
        """
        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.flavor_settings = FlavorConfig(
            name=guid + '-name', flavor_id=guid + '-id', ram=1, disk=1,
            vcpus=1, ephemeral=1, swap=2, rxtx_factor=3.0, is_public=False)
        self.nova = nova_utils.nova_client(self.os_creds, self.os_session)
        self.flavor = None

    def tearDown(self):
        """
        Cleans the image and downloaded image file
        """
        if self.flavor:
            try:
                nova_utils.delete_flavor(self.nova, self.flavor)
            except:
                pass

        super(self.__class__, self).__clean__()

    def test_create_flavor(self):
        """
        Tests the creation of an OpenStack keypair that does not exist.
        """
        self.flavor = nova_utils.create_flavor(self.nova, self.flavor_settings)
        self.validate_flavor()

    def test_create_delete_flavor(self):
        """
        Tests the creation of an OpenStack keypair that does not exist.
        """
        self.flavor = nova_utils.create_flavor(self.nova, self.flavor_settings)
        self.validate_flavor()
        nova_utils.delete_flavor(self.nova, self.flavor)
        flavor = nova_utils.get_flavor_by_name(self.nova,
                                               self.flavor_settings.name)
        self.assertIsNone(flavor)

    def validate_flavor(self):
        """
        Validates the flavor_settings against the OpenStack flavor object
        """
        self.assertIsNotNone(self.flavor)
        self.assertEqual(self.flavor_settings.name, self.flavor.name)
        self.assertEqual(self.flavor_settings.flavor_id, self.flavor.id)
        self.assertEqual(self.flavor_settings.ram, self.flavor.ram)
        self.assertEqual(self.flavor_settings.disk, self.flavor.disk)
        self.assertEqual(self.flavor_settings.vcpus, self.flavor.vcpus)
        self.assertEqual(self.flavor_settings.ephemeral, self.flavor.ephemeral)

        if self.flavor_settings.swap == 0:
            self.assertEqual('', self.flavor.swap)
        else:
            self.assertEqual(self.flavor_settings.swap, self.flavor.swap)

        self.assertEqual(self.flavor_settings.rxtx_factor,
                         self.flavor.rxtx_factor)
        self.assertEqual(self.flavor_settings.is_public, self.flavor.is_public)


class NovaUtilsInstanceTests(OSComponentTestCase):
    """
    Tests the creation of VM instances via nova_utils.py
    """

    def setUp(self):
        """
        Setup objects required by VM instances
        :return:
        """

        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())

        self.nova = nova_utils.nova_client(
            self.os_creds, self.os_session)
        self.keystone = keystone_utils.keystone_client(
            self.os_creds, self.os_session)
        self.neutron = neutron_utils.neutron_client(
            self.os_creds, self.os_session)
        self.glance = glance_utils.glance_client(
            self.os_creds, self.os_session)

        self.image_creator = None
        self.network_creator = None
        self.flavor_creator = None
        self.port = None
        self.vm_inst = None

        try:
            image_settings = openstack_tests.cirros_image_settings(
                name=guid + '-image', image_metadata=self.image_metadata)
            self.image_creator = OpenStackImage(
                self.os_creds, image_settings=image_settings)
            self.image_creator.create()

            network_settings = openstack_tests.get_priv_net_config(
                self.os_creds.project_name, guid + '-net',
                guid + '-subnet').network_settings
            self.network_creator = OpenStackNetwork(
                self.os_creds, network_settings)
            self.network_creator.create()

            self.flavor_creator = OpenStackFlavor(
                self.os_creds,
                FlavorConfig(
                    name=guid + '-flavor-name', ram=256, disk=10, vcpus=1))
            self.flavor_creator.create()

            port_settings = PortConfig(
                name=guid + '-port', network_name=network_settings.name)
            self.port = neutron_utils.create_port(
                self.neutron, self.os_creds, port_settings)

            self.instance_settings = VmInstanceConfig(
                name=guid + '-vm_inst',
                flavor=self.flavor_creator.flavor_settings.name,
                port_settings=[port_settings])
        except:
            self.tearDown()
            raise

    def tearDown(self):
        """
        Cleanup deployed resources
        :return:
        """
        if self.vm_inst:
            try:
                nova_utils.delete_vm_instance(self.nova, self.vm_inst)
            except:
                pass
        if self.port:
            try:
                neutron_utils.delete_port(self.neutron, self.port)
            except:
                pass
        if self.flavor_creator:
            try:
                self.flavor_creator.clean()
            except:
                pass
        if self.network_creator:
            try:
                self.network_creator.clean()
            except:
                pass
        if self.image_creator:
            try:
                self.image_creator.clean()
            except:
                pass

        super(self.__class__, self).__clean__()

    def test_create_instance(self):
        """
        Tests the nova_utils.create_server() method
        :return:
        """

        self.vm_inst = nova_utils.create_server(
            self.nova, self.keystone, self.neutron, self.glance,
            self.instance_settings, self.image_creator.image_settings,
            self.os_creds.project_name)

        self.assertIsNotNone(self.vm_inst)

        # Wait until instance is ACTIVE
        iters = 0
        active = False
        status = None
        while iters < 60:
            status = nova_utils.get_server_status(self.nova, self.vm_inst)
            if create_instance.STATUS_ACTIVE == status:
                active = True
                break

            time.sleep(3)
            iters += 1

        self.assertTrue(active, msg='VM {} status {} is not {}'.format(
            self.vm_inst.name, status, create_instance.STATUS_ACTIVE))
        vm_inst = nova_utils.get_latest_server_object(
            self.nova, self.neutron, self.keystone, self.vm_inst,
            self.os_creds.project_name)

        self.assertEqual(self.vm_inst.name, vm_inst.name)
        self.assertEqual(self.vm_inst.id, vm_inst.id)


class NovaUtilsInstanceVolumeTests(OSComponentTestCase):
    """
    Tests the creation of VM instances via nova_utils.py
    """

    def setUp(self):
        """
        Setup objects required by VM instances
        :return:
        """

        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())

        self.nova = nova_utils.nova_client(self.os_creds, self.os_session)
        self.cinder = cinder_utils.cinder_client(
            self.os_creds, self.os_session)

        self.image_creator = None
        self.network_creator = None
        self.flavor_creator = None
        self.volume_creator = None
        self.instance_creator = None

        try:
            image_settings = openstack_tests.cirros_image_settings(
                name=guid + '-image', image_metadata=self.image_metadata)
            self.image_creator = OpenStackImage(
                self.os_creds, image_settings=image_settings)
            self.image_creator.create()

            network_settings = openstack_tests.get_priv_net_config(
                self.os_creds.project_name, guid + '-net',
                guid + '-subnet').network_settings
            self.network_creator = OpenStackNetwork(
                self.os_creds, network_settings)
            self.network_creator.create()

            flavor_settings = FlavorConfig(
                name=guid + '-flavor', ram=256, disk=10, vcpus=1,
                metadata=self.flavor_metadata)
            self.flavor_creator = OpenStackFlavor(
                self.os_creds, flavor_settings)
            self.flavor_creator.create()

            # Create Volume
            volume_settings = VolumeConfig(
                name=self.__class__.__name__ + '-' + str(guid))
            self.volume_creator = OpenStackVolume(
                self.os_creds, volume_settings)
            self.volume_creator.create(block=True)

            port_settings = PortConfig(
                name=guid + '-port', network_name=network_settings.name)
            instance_settings = VmInstanceConfig(
                name=guid + '-vm_inst',
                flavor=self.flavor_creator.flavor_settings.name,
                port_settings=[port_settings])
            self.instance_creator = OpenStackVmInstance(
                self.os_creds, instance_settings, image_settings)
            self.instance_creator.create(block=True)
        except:
            self.tearDown()
            raise

    def tearDown(self):
        """
        Cleanup deployed resources
        :return:
        """
        if self.instance_creator:
            try:
                self.instance_creator.clean()
            except:
                pass
        if self.volume_creator:
            try:
                self.volume_creator.clean()
            except:
                pass
        if self.flavor_creator:
            try:
                self.flavor_creator.clean()
            except:
                pass
        if self.network_creator:
            try:
                self.network_creator.clean()
            except:
                pass
        if self.image_creator:
            try:
                self.image_creator.clean()
            except:
                pass

        super(self.__class__, self).__clean__()

    def test_add_remove_volume(self):
        """
        Tests the nova_utils.attach_volume() and detach_volume functions with
        a timeout value
        :return:
        """

        self.assertIsNotNone(self.volume_creator.get_volume())
        self.assertEqual(0, len(self.volume_creator.get_volume().attachments))

        # Attach volume to VM
        neutron = neutron_utils.neutron_client(
            self.os_creds, self.os_session)
        keystone = keystone_utils.keystone_client(
            self.os_creds, self.os_session)
        self.assertIsNotNone(nova_utils.attach_volume(
            self.nova, neutron, keystone, self.instance_creator.get_vm_inst(),
            self.volume_creator.get_volume(), self.os_creds.project_name))

        vol_attach = None
        vol_detach = None
        attached = False
        start_time = time.time()
        while time.time() < start_time + 120:
            vol_attach = cinder_utils.get_volume_by_id(
                self.cinder, self.volume_creator.get_volume().id)

            if len(vol_attach.attachments) > 0:
                attached = True
                break

            time.sleep(3)

        self.assertTrue(attached)
        self.assertIsNotNone(vol_attach)

        keystone = keystone_utils.keystone_client(
            self.os_creds, self.os_session)
        vm_attach = nova_utils.get_server_object_by_id(
            self.nova, neutron, keystone,
            self.instance_creator.get_vm_inst().id, self.os_creds.project_name)

        # Validate Attachment
        self.assertIsNotNone(vol_attach)
        self.assertEqual(self.volume_creator.get_volume().id, vol_attach.id)
        self.assertEqual(1, len(vol_attach.attachments))
        self.assertEqual(vm_attach.volume_ids[0]['id'],
                         vol_attach.attachments[0]['volume_id'])

        # Detach volume to VM
        self.assertIsNotNone(nova_utils.detach_volume(
            self.nova, neutron, keystone, self.instance_creator.get_vm_inst(),
            self.volume_creator.get_volume(), self.os_creds.project_name))

        start_time = time.time()
        while time.time() < start_time + 120:
            vol_detach = cinder_utils.get_volume_by_id(
                self.cinder, self.volume_creator.get_volume().id)
            if len(vol_detach.attachments) == 0:
                attached = False
                break

            time.sleep(3)

        self.assertFalse(attached)
        self.assertIsNotNone(vol_detach)

        vm_detach = nova_utils.get_server_object_by_id(
            self.nova, neutron, keystone,
            self.instance_creator.get_vm_inst().id, self.os_creds.project_name)

        # Validate Detachment
        self.assertIsNotNone(vol_detach)
        self.assertEqual(self.volume_creator.get_volume().id, vol_detach.id)

        self.assertEqual(0, len(vol_detach.attachments))
        self.assertEqual(0, len(vm_detach.volume_ids))

    def test_attach_volume_nowait(self):
        """
        Tests the nova_utils.attach_volume() with a timeout value that is too
        small to have the volume attachment data to be included on the VmInst
        object that was supposed to be returned
        """

        self.assertIsNotNone(self.volume_creator.get_volume())
        self.assertEqual(0, len(self.volume_creator.get_volume().attachments))

        # Attach volume to VM
        neutron = neutron_utils.neutron_client(self.os_creds, self.os_session)
        keystone = keystone_utils.keystone_client(
            self.os_creds, self.os_session)
        with self.assertRaises(NovaException):
            nova_utils.attach_volume(
                self.nova, neutron, keystone,
                self.instance_creator.get_vm_inst(),
                self.volume_creator.get_volume(), self.os_creds.project_name,
                0)

    def test_detach_volume_nowait(self):
        """
        Tests the nova_utils.detach_volume() with a timeout value that is too
        small to have the volume attachment data to be included on the VmInst
        object that was supposed to be returned
        """

        self.assertIsNotNone(self.volume_creator.get_volume())
        self.assertEqual(0, len(self.volume_creator.get_volume().attachments))

        # Attach volume to VM
        neutron = neutron_utils.neutron_client(self.os_creds, self.os_session)
        keystone = keystone_utils.keystone_client(
            self.os_creds, self.os_session)
        nova_utils.attach_volume(
            self.nova, neutron, keystone, self.instance_creator.get_vm_inst(),
            self.volume_creator.get_volume(), self.os_creds.project_name)

        # Check VmInst for attachment
        keystone = keystone_utils.keystone_client(
            self.os_creds, self.os_session)
        latest_vm = nova_utils.get_server_object_by_id(
            self.nova, neutron, keystone,
            self.instance_creator.get_vm_inst().id, self.os_creds.project_name)
        self.assertEqual(1, len(latest_vm.volume_ids))

        # Check Volume for attachment
        vol_attach = None
        attached = False
        start_time = time.time()
        while time.time() < start_time + 120:
            vol_attach = cinder_utils.get_volume_by_id(
                self.cinder, self.volume_creator.get_volume().id)

            if len(vol_attach.attachments) > 0:
                attached = True
                break

            time.sleep(3)

        self.assertTrue(attached)
        self.assertIsNotNone(vol_attach)

        # Detach volume
        with self.assertRaises(NovaException):
            nova_utils.detach_volume(
                self.nova, neutron, keystone,
                self.instance_creator.get_vm_inst(),
                self.volume_creator.get_volume(), self.os_creds.project_name,
                0)
