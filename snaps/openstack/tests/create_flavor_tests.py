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
import unittest
import uuid

from snaps.config.flavor import FlavorConfig, FlavorConfigError
from snaps.openstack import create_flavor
from snaps.openstack.create_flavor import OpenStackFlavor, FlavorSettings
from snaps.openstack.tests.os_source_file_test import OSComponentTestCase
from snaps.openstack.utils import nova_utils

__author__ = 'spisarski'


class FlavorSettingsUnitTests(unittest.TestCase):
    """
    Tests the construction of the FlavorSettings class
    """

    def test_no_params(self):
        with self.assertRaises(FlavorConfigError):
            FlavorSettings()

    def test_empty_config(self):
        with self.assertRaises(FlavorConfigError):
            FlavorSettings(config=dict())

    def test_name_only(self):
        with self.assertRaises(FlavorConfigError):
            FlavorSettings(name='foo')

    def test_config_with_name_only(self):
        with self.assertRaises(FlavorConfigError):
            FlavorSettings(config={'name': 'foo'})

    def test_name_ram_only(self):
        with self.assertRaises(FlavorConfigError):
            FlavorSettings(name='foo', ram=1)

    def test_config_with_name_ram_only(self):
        with self.assertRaises(FlavorConfigError):
            FlavorSettings(config={'name': 'foo', 'ram': 1})

    def test_name_ram_disk_only(self):
        with self.assertRaises(FlavorConfigError):
            FlavorSettings(name='foo', ram=1, disk=1)

    def test_config_with_name_ram_disk_only(self):
        with self.assertRaises(FlavorConfigError):
            FlavorSettings(config={'name': 'foo', 'ram': 1, 'disk': 1})

    def test_ram_string(self):
        with self.assertRaises(FlavorConfigError):
            FlavorSettings(name='foo', ram='bar', disk=2, vcpus=3, ephemeral=4,
                           swap=5, rxtx_factor=6.0,
                           is_public=False)

    def test_config_ram_string(self):
        with self.assertRaises(FlavorConfigError):
            FlavorSettings(
                config={'name': 'foo', 'ram': 'bar', 'disk': 2, 'vcpus': 3,
                        'ephemeral': 4, 'swap': 5,
                        'rxtx_factor': 6.0, 'is_public': False})

    def test_ram_float(self):
        with self.assertRaises(FlavorConfigError):
            FlavorSettings(name='foo', ram=1.5, disk=2, vcpus=3, ephemeral=4,
                           swap=5, rxtx_factor=6.0, is_public=False)

    def test_config_ram_float(self):
        with self.assertRaises(FlavorConfigError):
            FlavorSettings(
                config={'name': 'foo', 'ram': 1.5, 'disk': 2, 'vcpus': 3,
                        'ephemeral': 4, 'swap': 5,
                        'rxtx_factor': 6.0, 'is_public': False})

    def test_disk_string(self):
        with self.assertRaises(FlavorConfigError):
            FlavorSettings(name='foo', ram=1, disk='bar', vcpus=3, ephemeral=4,
                           swap=5, rxtx_factor=6.0,
                           is_public=False)

    def test_config_disk_string(self):
        with self.assertRaises(FlavorConfigError):
            FlavorSettings(
                config={'name': 'foo', 'ram': 1, 'disk': 'bar', 'vcpus': 3,
                        'ephemeral': 4, 'swap': 5,
                        'rxtx_factor': 6.0, 'is_public': False})

    def test_disk_float(self):
        with self.assertRaises(FlavorConfigError):
            FlavorSettings(name='foo', ram=1, disk=2.5, vcpus=3, ephemeral=4,
                           swap=5, rxtx_factor=6.0, is_public=False)

    def test_config_disk_float(self):
        with self.assertRaises(FlavorConfigError):
            FlavorSettings(
                config={'name': 'foo', 'ram': 1, 'disk': 2.5, 'vcpus': 3,
                        'ephemeral': 4, 'swap': 5,
                        'rxtx_factor': 6.0, 'is_public': False})

    def test_vcpus_string(self):
        with self.assertRaises(FlavorConfigError):
            FlavorSettings(name='foo', ram=1, disk=2, vcpus='bar', ephemeral=4,
                           swap=5, rxtx_factor=6.0,
                           is_public=False)

    def test_config_vcpus_string(self):
        with self.assertRaises(FlavorConfigError):
            FlavorSettings(
                config={'name': 'foo', 'ram': 1, 'disk': 2, 'vcpus': 'bar',
                        'ephemeral': 4, 'swap': 5,
                        'rxtx_factor': 6.0, 'is_public': False})

    def test_ephemeral_string(self):
        with self.assertRaises(FlavorConfigError):
            FlavorSettings(name='foo', ram=1, disk=2, vcpus=3, ephemeral='bar',
                           swap=5, rxtx_factor=6.0,
                           is_public=False)

    def test_config_ephemeral_string(self):
        with self.assertRaises(FlavorConfigError):
            FlavorSettings(
                config={'name': 'foo', 'ram': 1, 'disk': 2, 'vcpus': 3,
                        'ephemeral': 'bar', 'swap': 5,
                        'rxtx_factor': 6.0, 'is_public': False})

    def test_ephemeral_float(self):
        with self.assertRaises(FlavorConfigError):
            FlavorSettings(name='foo', ram=1, disk=2, vcpus=3, ephemeral=4.5,
                           swap=5, rxtx_factor=6.0, is_public=False)

    def test_config_ephemeral_float(self):
        with self.assertRaises(FlavorConfigError):
            FlavorSettings(
                config={'name': 'foo', 'ram': 1, 'disk': 2, 'vcpus': 3,
                        'ephemeral': 4.5, 'swap': 5,
                        'rxtx_factor': 6.0, 'is_public': False})

    def test_swap_string(self):
        with self.assertRaises(FlavorConfigError):
            FlavorSettings(name='foo', ram=1, disk=2, vcpus=3, ephemeral=4,
                           swap='bar', rxtx_factor=6.0,
                           is_public=False)

    def test_config_swap_string(self):
        with self.assertRaises(FlavorConfigError):
            FlavorSettings(
                config={'name': 'foo', 'ram': 1, 'disk': 2, 'vcpus': 3,
                        'ephemeral': 4, 'swap': 'bar',
                        'rxtx_factor': 6.0, 'is_public': False})

    def test_swap_float(self):
        with self.assertRaises(FlavorConfigError):
            FlavorSettings(name='foo', ram=1, disk=2, vcpus=3, ephemeral=4,
                           swap=5.5, rxtx_factor=6.0, is_public=False)

    def test_config_swap_float(self):
        with self.assertRaises(FlavorConfigError):
            FlavorSettings(
                config={'name': 'foo', 'ram': 1, 'disk': 2, 'vcpus': 3,
                        'ephemeral': 4, 'swap': 5.5,
                        'rxtx_factor': 6.0, 'is_public': False})

    def test_rxtx_string(self):
        with self.assertRaises(FlavorConfigError):
            FlavorSettings(name='foo', ram=1, disk=2, vcpus=3, ephemeral=4,
                           swap=5, rxtx_factor='bar', is_public=False)

    def test_config_rxtx_string(self):
        with self.assertRaises(FlavorConfigError):
            FlavorSettings(
                config={'name': 'foo', 'ram': 1, 'disk': 2, 'vcpus': 3,
                        'ephemeral': 4, 'swap': 5,
                        'rxtx_factor': 'bar', 'is_public': False})

    def test_is_pub_string(self):
        with self.assertRaises(FlavorConfigError):
            FlavorSettings(name='foo', ram=1, disk=2, vcpus=3, ephemeral=4,
                           swap=5, rxtx_factor=6.0, is_public='bar')

    def test_config_is_pub_string(self):
        with self.assertRaises(FlavorConfigError):
            FlavorSettings(
                config={'name': 'foo', 'ram': 1, 'disk': 2, 'vcpus': 3,
                        'ephemeral': 4, 'swap': 5,
                        'rxtx_factor': 6.0, 'is_public': 'bar'})

    def test_name_ram_disk_vcpus_only(self):
        settings = FlavorSettings(name='foo', ram=1, disk=2, vcpus=3)
        self.assertEqual('foo', settings.name)
        self.assertEqual('auto', settings.flavor_id)
        self.assertEqual(1, settings.ram)
        self.assertEqual(2, settings.disk)
        self.assertEqual(3, settings.vcpus)
        self.assertEqual(0, settings.ephemeral)
        self.assertEqual(0, settings.swap)
        self.assertEqual(1.0, settings.rxtx_factor)
        self.assertEqual(True, settings.is_public)
        self.assertEqual(None, settings.metadata)

    def test_config_with_name_ram_disk_vcpus_only(self):
        settings = FlavorSettings(
            **{'name': 'foo', 'ram': 1, 'disk': 2, 'vcpus': 3})
        self.assertEqual('foo', settings.name)
        self.assertEqual('auto', settings.flavor_id)
        self.assertEqual(1, settings.ram)
        self.assertEqual(2, settings.disk)
        self.assertEqual(3, settings.vcpus)
        self.assertEqual(0, settings.ephemeral)
        self.assertEqual(0, settings.swap)
        self.assertEqual(1.0, settings.rxtx_factor)
        self.assertEqual(True, settings.is_public)
        self.assertEqual(None, settings.metadata)

    def test_all(self):
        metadata = {'foo': 'bar'}
        settings = FlavorSettings(
            name='foo', flavor_id='bar', ram=1, disk=2, vcpus=3, ephemeral=4,
            swap=5, rxtx_factor=6.0, is_public=False, metadata=metadata)
        self.assertEqual('foo', settings.name)
        self.assertEqual('bar', settings.flavor_id)
        self.assertEqual(1, settings.ram)
        self.assertEqual(2, settings.disk)
        self.assertEqual(3, settings.vcpus)
        self.assertEqual(4, settings.ephemeral)
        self.assertEqual(5, settings.swap)
        self.assertEqual(6.0, settings.rxtx_factor)
        self.assertEqual(False, settings.is_public)
        self.assertEqual(metadata, settings.metadata)

    def test_config_all(self):
        metadata = {'foo': 'bar'}
        settings = FlavorSettings(
            **{'name': 'foo', 'flavor_id': 'bar', 'ram': 1, 'disk': 2,
               'vcpus': 3,
               'ephemeral': 4, 'swap': 5, 'rxtx_factor': 6.0,
               'is_public': False,
               'metadata': metadata})
        self.assertEqual('foo', settings.name)
        self.assertEqual('bar', settings.flavor_id)
        self.assertEqual(1, settings.ram)
        self.assertEqual(2, settings.disk)
        self.assertEqual(3, settings.vcpus)
        self.assertEqual(4, settings.ephemeral)
        self.assertEqual(5, settings.swap)
        self.assertEqual(6.0, settings.rxtx_factor)
        self.assertEqual(False, settings.is_public)
        self.assertEqual(metadata, settings.metadata)


class CreateFlavorTests(OSComponentTestCase):
    """
    Test for the CreateSecurityGroup class defined in create_security_group.py
    """

    def setUp(self):
        """
        Instantiates the CreateSecurityGroup object that is responsible for
        downloading and creating an OS image file within OpenStack
        """
        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.flavor_name = guid + 'name'

        self.nova = nova_utils.nova_client(self.os_creds, self.os_session)

        # Initialize for cleanup
        self.flavor_creator = None

    def tearDown(self):
        """
        Cleans the image and downloaded image file
        """
        if self.flavor_creator:
            self.flavor_creator.clean()

        super(self.__class__, self).__clean__()

    def test_create_flavor(self):
        """
        Tests the creation of an OpenStack flavor.
        """
        # Create Flavor
        flavor_settings = FlavorConfig(
            name=self.flavor_name, ram=1, disk=1, vcpus=1)
        self.flavor_creator = OpenStackFlavor(self.os_creds, flavor_settings)
        flavor = self.flavor_creator.create()
        self.assertTrue(validate_flavor(self.nova, flavor_settings, flavor))

    def test_create_flavor_existing(self):
        """
        Tests the creation of an OpenStack flavor then starts another creator
        to ensure it has not been done twice.
        """
        # Create Flavor
        flavor_settings = FlavorConfig(
            name=self.flavor_name, ram=1, disk=1, vcpus=1)
        self.flavor_creator = OpenStackFlavor(self.os_creds, flavor_settings)
        flavor = self.flavor_creator.create()
        self.assertTrue(validate_flavor(self.nova, flavor_settings, flavor))

        flavor_creator_2 = OpenStackFlavor(self.os_creds, flavor_settings)
        flavor2 = flavor_creator_2.create()

        self.assertEqual(flavor.id, flavor2.id)

    def test_create_clean_flavor(self):
        """
        Tests the creation and cleanup of an OpenStack flavor.
        """
        # Create Flavor
        flavor_settings = FlavorConfig(
            name=self.flavor_name, ram=1, disk=1, vcpus=1)
        self.flavor_creator = OpenStackFlavor(self.os_creds, flavor_settings)
        flavor = self.flavor_creator.create()
        self.assertTrue(validate_flavor(self.nova, flavor_settings, flavor))

        # Clean Flavor
        self.flavor_creator.clean()

        self.assertIsNone(self.flavor_creator.get_flavor())
        self.assertIsNone(
            nova_utils.get_flavor_by_name(self.nova, flavor_settings.name))

    def test_create_delete_flavor(self):
        """
        Tests the creation of an OpenStack Flavor, the deletion, then
        cleanup to ensure clean() does not
        raise any exceptions.
        """
        # Create Flavor
        flavor_settings = FlavorConfig(
            name=self.flavor_name, ram=1, disk=1, vcpus=1)
        self.flavor_creator = OpenStackFlavor(self.os_creds, flavor_settings)
        flavor = self.flavor_creator.create()
        self.assertTrue(validate_flavor(self.nova, flavor_settings, flavor))

        # Delete Flavor
        nova_utils.delete_flavor(self.nova, flavor)
        self.assertIsNone(
            nova_utils.get_flavor_by_name(self.nova, flavor_settings.name))

        # Attempt to cleanup
        self.flavor_creator.clean()

        self.assertIsNone(self.flavor_creator.get_flavor())

    def test_create_flavor_all_settings(self):
        """
        Tests the creation of an OpenStack Flavor, the deletion, then
        cleanup to ensure clean() does not
        raise any exceptions.
        """
        # Create Flavor
        flavor_settings = FlavorConfig(
            name=self.flavor_name, ram=1, disk=1, vcpus=1, ephemeral=2, swap=3,
            rxtx_factor=2.2, is_public=False,
            metadata=create_flavor.MEM_PAGE_SIZE_ANY)
        self.flavor_creator = OpenStackFlavor(self.os_creds, flavor_settings)
        flavor = self.flavor_creator.create()
        self.assertTrue(validate_flavor(self.nova, flavor_settings, flavor))

        # Delete Flavor
        nova_utils.delete_flavor(self.nova, flavor)
        self.assertIsNone(
            nova_utils.get_flavor_by_name(self.nova, flavor_settings.name))

        # Attempt to cleanup
        self.flavor_creator.clean()

        self.assertIsNone(self.flavor_creator.get_flavor())


def validate_flavor(nova, flavor_settings, flavor):
    """
    Validates the flavor_settings against the OpenStack flavor object
    :param nova: the nova client
    :param flavor_settings: the settings used to create the flavor
    :param flavor: the OpenStack flavor object
    """
    setting_meta = dict()
    if flavor_settings.metadata:
        setting_meta = flavor_settings.metadata
    metadata = nova_utils.get_flavor_keys(nova, flavor)

    equals = True
    for key, value in setting_meta.items():
        if metadata[key] != value:
            equals = False
            break

    swap = None
    if flavor_settings.swap != 0:
        swap = flavor_settings.swap

    return (
        flavor is not None and
        flavor_settings.name == flavor.name and
        flavor_settings.ram == flavor.ram and
        flavor_settings.disk == flavor.disk and
        flavor_settings.vcpus == flavor.vcpus and
        flavor_settings.ephemeral == flavor.ephemeral and
        swap == flavor.swap and
        flavor_settings.rxtx_factor == flavor.rxtx_factor and
        flavor_settings.is_public == flavor.is_public and
        equals)
