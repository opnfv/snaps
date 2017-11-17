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

from snaps.config.flavor import FlavorConfig, FlavorConfigError


class FlavorConfigUnitTests(unittest.TestCase):
    """
    Tests the construction of the FlavorConfig class
    """

    def test_no_params(self):
        with self.assertRaises(FlavorConfigError):
            FlavorConfig()

    def test_empty_config(self):
        with self.assertRaises(FlavorConfigError):
            FlavorConfig(config=dict())

    def test_name_only(self):
        with self.assertRaises(FlavorConfigError):
            FlavorConfig(name='foo')

    def test_config_with_name_only(self):
        with self.assertRaises(FlavorConfigError):
            FlavorConfig(config={'name': 'foo'})

    def test_name_ram_only(self):
        with self.assertRaises(FlavorConfigError):
            FlavorConfig(name='foo', ram=1)

    def test_config_with_name_ram_only(self):
        with self.assertRaises(FlavorConfigError):
            FlavorConfig(config={'name': 'foo', 'ram': 1})

    def test_name_ram_disk_only(self):
        with self.assertRaises(FlavorConfigError):
            FlavorConfig(name='foo', ram=1, disk=1)

    def test_config_with_name_ram_disk_only(self):
        with self.assertRaises(FlavorConfigError):
            FlavorConfig(config={'name': 'foo', 'ram': 1, 'disk': 1})

    def test_ram_string(self):
        with self.assertRaises(FlavorConfigError):
            FlavorConfig(name='foo', ram='bar', disk=2, vcpus=3, ephemeral=4,
                         swap=5, rxtx_factor=6.0,
                         is_public=False)

    def test_config_ram_string(self):
        with self.assertRaises(FlavorConfigError):
            FlavorConfig(
                config={'name': 'foo', 'ram': 'bar', 'disk': 2, 'vcpus': 3,
                        'ephemeral': 4, 'swap': 5,
                        'rxtx_factor': 6.0, 'is_public': False})

    def test_ram_float(self):
        with self.assertRaises(FlavorConfigError):
            FlavorConfig(name='foo', ram=1.5, disk=2, vcpus=3, ephemeral=4,
                         swap=5, rxtx_factor=6.0, is_public=False)

    def test_config_ram_float(self):
        with self.assertRaises(FlavorConfigError):
            FlavorConfig(
                config={'name': 'foo', 'ram': 1.5, 'disk': 2, 'vcpus': 3,
                        'ephemeral': 4, 'swap': 5,
                        'rxtx_factor': 6.0, 'is_public': False})

    def test_disk_string(self):
        with self.assertRaises(FlavorConfigError):
            FlavorConfig(name='foo', ram=1, disk='bar', vcpus=3, ephemeral=4,
                         swap=5, rxtx_factor=6.0,
                         is_public=False)

    def test_config_disk_string(self):
        with self.assertRaises(FlavorConfigError):
            FlavorConfig(
                config={'name': 'foo', 'ram': 1, 'disk': 'bar', 'vcpus': 3,
                        'ephemeral': 4, 'swap': 5,
                        'rxtx_factor': 6.0, 'is_public': False})

    def test_disk_float(self):
        with self.assertRaises(FlavorConfigError):
            FlavorConfig(name='foo', ram=1, disk=2.5, vcpus=3, ephemeral=4,
                         swap=5, rxtx_factor=6.0, is_public=False)

    def test_config_disk_float(self):
        with self.assertRaises(FlavorConfigError):
            FlavorConfig(
                config={'name': 'foo', 'ram': 1, 'disk': 2.5, 'vcpus': 3,
                        'ephemeral': 4, 'swap': 5,
                        'rxtx_factor': 6.0, 'is_public': False})

    def test_vcpus_string(self):
        with self.assertRaises(FlavorConfigError):
            FlavorConfig(name='foo', ram=1, disk=2, vcpus='bar', ephemeral=4,
                         swap=5, rxtx_factor=6.0,
                         is_public=False)

    def test_config_vcpus_string(self):
        with self.assertRaises(FlavorConfigError):
            FlavorConfig(
                config={'name': 'foo', 'ram': 1, 'disk': 2, 'vcpus': 'bar',
                        'ephemeral': 4, 'swap': 5,
                        'rxtx_factor': 6.0, 'is_public': False})

    def test_ephemeral_string(self):
        with self.assertRaises(FlavorConfigError):
            FlavorConfig(name='foo', ram=1, disk=2, vcpus=3, ephemeral='bar',
                         swap=5, rxtx_factor=6.0,
                         is_public=False)

    def test_config_ephemeral_string(self):
        with self.assertRaises(FlavorConfigError):
            FlavorConfig(
                config={'name': 'foo', 'ram': 1, 'disk': 2, 'vcpus': 3,
                        'ephemeral': 'bar', 'swap': 5,
                        'rxtx_factor': 6.0, 'is_public': False})

    def test_ephemeral_float(self):
        with self.assertRaises(FlavorConfigError):
            FlavorConfig(name='foo', ram=1, disk=2, vcpus=3, ephemeral=4.5,
                         swap=5, rxtx_factor=6.0, is_public=False)

    def test_config_ephemeral_float(self):
        with self.assertRaises(FlavorConfigError):
            FlavorConfig(
                config={'name': 'foo', 'ram': 1, 'disk': 2, 'vcpus': 3,
                        'ephemeral': 4.5, 'swap': 5,
                        'rxtx_factor': 6.0, 'is_public': False})

    def test_swap_string(self):
        with self.assertRaises(FlavorConfigError):
            FlavorConfig(name='foo', ram=1, disk=2, vcpus=3, ephemeral=4,
                         swap='bar', rxtx_factor=6.0,
                         is_public=False)

    def test_config_swap_string(self):
        with self.assertRaises(FlavorConfigError):
            FlavorConfig(
                config={'name': 'foo', 'ram': 1, 'disk': 2, 'vcpus': 3,
                        'ephemeral': 4, 'swap': 'bar',
                        'rxtx_factor': 6.0, 'is_public': False})

    def test_swap_float(self):
        with self.assertRaises(FlavorConfigError):
            FlavorConfig(name='foo', ram=1, disk=2, vcpus=3, ephemeral=4,
                         swap=5.5, rxtx_factor=6.0, is_public=False)

    def test_config_swap_float(self):
        with self.assertRaises(FlavorConfigError):
            FlavorConfig(
                config={'name': 'foo', 'ram': 1, 'disk': 2, 'vcpus': 3,
                        'ephemeral': 4, 'swap': 5.5,
                        'rxtx_factor': 6.0, 'is_public': False})

    def test_rxtx_string(self):
        with self.assertRaises(FlavorConfigError):
            FlavorConfig(name='foo', ram=1, disk=2, vcpus=3, ephemeral=4,
                         swap=5, rxtx_factor='bar', is_public=False)

    def test_config_rxtx_string(self):
        with self.assertRaises(FlavorConfigError):
            FlavorConfig(
                config={'name': 'foo', 'ram': 1, 'disk': 2, 'vcpus': 3,
                        'ephemeral': 4, 'swap': 5,
                        'rxtx_factor': 'bar', 'is_public': False})

    def test_is_pub_string(self):
        with self.assertRaises(FlavorConfigError):
            FlavorConfig(name='foo', ram=1, disk=2, vcpus=3, ephemeral=4,
                         swap=5, rxtx_factor=6.0, is_public='bar')

    def test_config_is_pub_string(self):
        with self.assertRaises(FlavorConfigError):
            FlavorConfig(
                config={'name': 'foo', 'ram': 1, 'disk': 2, 'vcpus': 3,
                        'ephemeral': 4, 'swap': 5,
                        'rxtx_factor': 6.0, 'is_public': 'bar'})

    def test_name_ram_disk_vcpus_only(self):
        settings = FlavorConfig(name='foo', ram=1, disk=2, vcpus=3)
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
        settings = FlavorConfig(
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
        settings = FlavorConfig(
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
        settings = FlavorConfig(
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
