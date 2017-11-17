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

from snaps.config.volume_type import (
    VolumeTypeConfig,  VolumeTypeEncryptionConfig, ControlLocation,
    VolumeTypeConfigError)


class VolumeTypeConfigUnitTests(unittest.TestCase):
    """
    Tests the construction of the VolumeTypeConfig class
    """

    def test_no_params(self):
        with self.assertRaises(VolumeTypeConfigError):
            VolumeTypeConfig()

    def test_empty_config(self):
        with self.assertRaises(VolumeTypeConfigError):
            VolumeTypeConfig(**dict())

    def test_name_only(self):
        settings = VolumeTypeConfig(name='foo')
        self.assertEqual('foo', settings.name)
        self.assertIsNone(settings.description)
        self.assertIsNone(settings.qos_spec_name)
        self.assertIsNone(settings.encryption)
        self.assertFalse(settings.public)

    def test_config_with_name_only(self):
        settings = VolumeTypeConfig(**{'name': 'foo'})
        self.assertEqual('foo', settings.name)
        self.assertIsNone(settings.description)
        self.assertIsNone(settings.qos_spec_name)
        self.assertIsNone(settings.encryption)
        self.assertFalse(settings.public)

    def test_all(self):
        encryption_settings = VolumeTypeEncryptionConfig(
            name='foo', provider_class='bar',
            control_location=ControlLocation.back_end)
        settings = VolumeTypeConfig(
            name='foo', description='desc', encryption=encryption_settings,
            qos_spec_name='spec_name', public=True)
        self.assertEqual('foo', settings.name)
        self.assertEqual('desc', settings.description)
        self.assertEqual('spec_name', settings.qos_spec_name)
        self.assertEqual(encryption_settings, settings.encryption)
        self.assertTrue(True, settings.public)

    def test_all_string(self):
        encryption_settings = {
            'name': 'foo', 'provider_class': 'bar',
            'control_location': 'back-end'}
        settings = VolumeTypeConfig(
            name='foo', description='desc', encryption=encryption_settings,
            qos_spec_name='spec_name', public='true')
        self.assertEqual('foo', settings.name)
        self.assertEqual('desc', settings.description)
        self.assertEqual('spec_name', settings.qos_spec_name)
        self.assertEqual(VolumeTypeEncryptionConfig(**encryption_settings),
                         settings.encryption)
        self.assertTrue(settings.public)

    def test_config_all(self):
        encryption_settings = {
            'name': 'foo', 'provider_class': 'bar',
            'control_location': 'back-end'}
        settings = VolumeTypeConfig(
            **{'name': 'foo', 'description': 'desc',
               'encryption': encryption_settings,
               'qos_spec_name': 'spec_name', 'public': 'false'})
        self.assertEqual('foo', settings.name)
        self.assertEqual('desc', settings.description)
        self.assertEqual('spec_name', settings.qos_spec_name)
        self.assertEqual(VolumeTypeEncryptionConfig(**encryption_settings),
                         settings.encryption)
        self.assertFalse(settings.public)
