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

from snaps.config.volume import VolumeConfigError, VolumeConfig


class VolumeConfigUnitTests(unittest.TestCase):
    """
    Tests the construction of the VolumeConfig class
    """

    def test_no_params(self):
        with self.assertRaises(VolumeConfigError):
            VolumeConfig()

    def test_empty_config(self):
        with self.assertRaises(VolumeConfigError):
            VolumeConfig(**dict())

    def test_name_only(self):
        settings = VolumeConfig(name='foo')
        self.assertEqual('foo', settings.name)
        self.assertIsNone(settings.project_name)
        self.assertIsNone(settings.description)
        self.assertEquals(1, settings.size)
        self.assertIsNone(settings.image_name)
        self.assertIsNone(settings.type_name)
        self.assertIsNone(settings.availability_zone)
        self.assertFalse(settings.multi_attach)

    def test_config_with_name_only(self):
        settings = VolumeConfig(**{'name': 'foo'})
        self.assertEqual('foo', settings.name)
        self.assertIsNone(settings.project_name)
        self.assertIsNone(settings.description)
        self.assertEquals(1, settings.size)
        self.assertIsNone(settings.image_name)
        self.assertIsNone(settings.type_name)
        self.assertIsNone(settings.availability_zone)
        self.assertFalse(settings.multi_attach)

    def test_all_strings(self):
        settings = VolumeConfig(
            name='foo', project_name='proj-foo', description='desc', size='2',
            image_name='image', type_name='type', availability_zone='zone1',
            multi_attach='true')

        self.assertEqual('foo', settings.name)
        self.assertEqual('proj-foo', settings.project_name)
        self.assertEqual('desc', settings.description)
        self.assertEqual(2, settings.size)
        self.assertEqual('image', settings.image_name)
        self.assertEqual('type', settings.type_name)
        self.assertEqual('zone1', settings.availability_zone)
        self.assertTrue(settings.multi_attach)

    def test_all_correct_type(self):
        settings = VolumeConfig(
            name='foo', project_name='proj-foo', description='desc', size=2,
            image_name='image', type_name='bar', availability_zone='zone1',
            multi_attach=True)

        self.assertEqual('foo', settings.name)
        self.assertEqual('proj-foo', settings.project_name)
        self.assertEqual('desc', settings.description)
        self.assertEqual(2, settings.size)
        self.assertEqual('image', settings.image_name)
        self.assertEqual('bar', settings.type_name)
        self.assertEqual('zone1', settings.availability_zone)
        self.assertTrue(settings.multi_attach)

    def test_config_all(self):
        settings = VolumeConfig(
            **{'name': 'foo', 'project_name': 'proj-foo',
               'description': 'desc', 'size': '2',
               'image_name': 'foo', 'type_name': 'bar',
               'availability_zone': 'zone1', 'multi_attach': 'true'})

        self.assertEqual('foo', settings.name)
        self.assertEqual('proj-foo', settings.project_name)
        self.assertEqual('desc', settings.description)
        self.assertEqual(2, settings.size)
        self.assertEqual('foo', settings.image_name)
        self.assertEqual('bar', settings.type_name)
        self.assertEqual('zone1', settings.availability_zone)
        self.assertTrue(settings.multi_attach)
