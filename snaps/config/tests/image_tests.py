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

from snaps.config.image import ImageConfigError, ImageConfig


class ImageConfigUnitTests(unittest.TestCase):
    """
    Tests the construction of the ImageConfig class
    """

    def test_no_params(self):
        with self.assertRaises(ImageConfigError):
            ImageConfig()

    def test_empty_config(self):
        with self.assertRaises(ImageConfigError):
            ImageConfig(**dict())

    def test_name_only(self):
        with self.assertRaises(ImageConfigError):
            ImageConfig(name='foo')

    def test_config_with_name_only(self):
        with self.assertRaises(ImageConfigError):
            ImageConfig(**{'name': 'foo'})

    def test_name_user_only(self):
        with self.assertRaises(ImageConfigError):
            ImageConfig(name='foo', image_user='bar')

    def test_config_with_name_user_only(self):
        with self.assertRaises(ImageConfigError):
            ImageConfig(**{'name': 'foo', 'image_user': 'bar'})

    def test_name_user_format_only(self):
        with self.assertRaises(ImageConfigError):
            ImageConfig(name='foo', image_user='bar', img_format='qcow2')

    def test_config_with_name_user_format_only(self):
        with self.assertRaises(ImageConfigError):
            ImageConfig(
                **{'name': 'foo', 'image_user': 'bar', 'format': 'qcow2'})

    def test_name_user_format_url_only(self):
        settings = ImageConfig(name='foo', image_user='bar',
                               img_format='qcow2', url='http://foo.com')
        self.assertEqual('foo', settings.name)
        self.assertEqual('bar', settings.image_user)
        self.assertEqual('qcow2', settings.format)
        self.assertEqual('http://foo.com', settings.url)
        self.assertIsNone(settings.image_file)
        self.assertFalse(settings.exists)
        self.assertFalse(settings.public)
        self.assertIsNone(settings.nic_config_pb_loc)

    def test_name_user_format_url_only_properties(self):
        properties = {'hw_video_model': 'vga'}
        settings = ImageConfig(name='foo', image_user='bar',
                               img_format='qcow2', url='http://foo.com',
                               extra_properties=properties)
        self.assertEqual('foo', settings.name)
        self.assertEqual('bar', settings.image_user)
        self.assertEqual('qcow2', settings.format)
        self.assertEqual('http://foo.com', settings.url)
        self.assertEqual(properties, settings.extra_properties)
        self.assertIsNone(settings.image_file)
        self.assertFalse(settings.exists)
        self.assertFalse(settings.public)
        self.assertIsNone(settings.nic_config_pb_loc)

    def test_config_with_name_user_format_url_only(self):
        settings = ImageConfig(
            **{'name': 'foo', 'image_user': 'bar', 'format': 'qcow2',
               'download_url': 'http://foo.com'})
        self.assertEqual('foo', settings.name)
        self.assertEqual('bar', settings.image_user)
        self.assertEqual('qcow2', settings.format)
        self.assertEqual('http://foo.com', settings.url)
        self.assertIsNone(settings.image_file)
        self.assertFalse(settings.exists)
        self.assertFalse(settings.public)
        self.assertIsNone(settings.nic_config_pb_loc)

    def test_name_user_format_file_only(self):
        settings = ImageConfig(name='foo', image_user='bar',
                               img_format='qcow2',
                               image_file='/foo/bar.qcow')
        self.assertEqual('foo', settings.name)
        self.assertEqual('bar', settings.image_user)
        self.assertEqual('qcow2', settings.format)
        self.assertIsNone(settings.url)
        self.assertEqual('/foo/bar.qcow', settings.image_file)
        self.assertFalse(settings.exists)
        self.assertFalse(settings.public)
        self.assertIsNone(settings.nic_config_pb_loc)

    def test_config_with_name_user_format_file_only(self):
        settings = ImageConfig(
            **{'name': 'foo', 'image_user': 'bar', 'format': 'qcow2',
               'image_file': '/foo/bar.qcow'})
        self.assertEqual('foo', settings.name)
        self.assertEqual('bar', settings.image_user)
        self.assertEqual('qcow2', settings.format)
        self.assertIsNone(settings.url)
        self.assertEqual('/foo/bar.qcow', settings.image_file)
        self.assertFalse(settings.exists)
        self.assertFalse(settings.public)
        self.assertIsNone(settings.nic_config_pb_loc)

    def test_all_url(self):
        properties = {'hw_video_model': 'vga'}
        kernel_settings = ImageConfig(name='kernel', url='http://kernel.com',
                                      image_user='bar', img_format='qcow2')
        ramdisk_settings = ImageConfig(name='ramdisk',
                                       url='http://ramdisk.com',
                                       image_user='bar', img_format='qcow2')
        settings = ImageConfig(name='foo', image_user='bar',
                               img_format='qcow2', url='http://foo.com',
                               extra_properties=properties,
                               nic_config_pb_loc='/foo/bar',
                               kernel_image_settings=kernel_settings,
                               ramdisk_image_settings=ramdisk_settings,
                               exists=True, public=True)
        self.assertEqual('foo', settings.name)
        self.assertEqual('bar', settings.image_user)
        self.assertEqual('qcow2', settings.format)
        self.assertEqual('http://foo.com', settings.url)
        self.assertEqual(properties, settings.extra_properties)
        self.assertIsNone(settings.image_file)
        self.assertEqual('/foo/bar', settings.nic_config_pb_loc)
        self.assertEqual('kernel', settings.kernel_image_settings.name)
        self.assertEqual('http://kernel.com',
                         settings.kernel_image_settings.url)
        self.assertEqual('bar', settings.kernel_image_settings.image_user)
        self.assertEqual('qcow2', settings.kernel_image_settings.format)
        self.assertEqual('ramdisk', settings.ramdisk_image_settings.name)
        self.assertEqual('http://ramdisk.com',
                         settings.ramdisk_image_settings.url)
        self.assertEqual('bar', settings.ramdisk_image_settings.image_user)
        self.assertEqual('qcow2', settings.ramdisk_image_settings.format)
        self.assertTrue(settings.exists)
        self.assertTrue(settings.public)

    def test_config_all_url(self):
        settings = ImageConfig(
            **{'name': 'foo', 'image_user': 'bar', 'format': 'qcow2',
               'download_url': 'http://foo.com',
               'extra_properties': '{\'hw_video_model\': \'vga\'}',
               'nic_config_pb_loc': '/foo/bar',
               'kernel_image_settings': {
                   'name': 'kernel',
                   'download_url': 'http://kernel.com',
                   'image_user': 'bar',
                   'format': 'qcow2'},
               'ramdisk_image_settings': {
                   'name': 'ramdisk',
                   'download_url': 'http://ramdisk.com',
                   'image_user': 'bar',
                   'format': 'qcow2'},
               'exists': True, 'public': True})
        self.assertEqual('foo', settings.name)
        self.assertEqual('bar', settings.image_user)
        self.assertEqual('qcow2', settings.format)
        self.assertEqual('http://foo.com', settings.url)
        self.assertEqual('{\'hw_video_model\': \'vga\'}',
                         settings.extra_properties)
        self.assertIsNone(settings.image_file)
        self.assertEqual('/foo/bar', settings.nic_config_pb_loc)
        self.assertEqual('kernel', settings.kernel_image_settings.name)
        self.assertEqual('http://kernel.com',
                         settings.kernel_image_settings.url)
        self.assertEqual('ramdisk', settings.ramdisk_image_settings.name)
        self.assertEqual('http://ramdisk.com',
                         settings.ramdisk_image_settings.url)
        self.assertTrue(settings.exists)
        self.assertTrue(settings.public)

    def test_all_file(self):
        properties = {'hw_video_model': 'vga'}
        settings = ImageConfig(name='foo', image_user='bar',
                               img_format='qcow2',
                               image_file='/foo/bar.qcow',
                               extra_properties=properties,
                               nic_config_pb_loc='/foo/bar', exists=True,
                               public=True)
        self.assertEqual('foo', settings.name)
        self.assertEqual('bar', settings.image_user)
        self.assertEqual('qcow2', settings.format)
        self.assertIsNone(settings.url)
        self.assertEqual('/foo/bar.qcow', settings.image_file)
        self.assertEqual(properties, settings.extra_properties)
        self.assertEqual('/foo/bar', settings.nic_config_pb_loc)
        self.assertTrue(settings.exists)
        self.assertTrue(settings.public)

    def test_config_all_file(self):
        settings = ImageConfig(
            **{'name': 'foo', 'image_user': 'bar', 'format': 'qcow2',
               'image_file': '/foo/bar.qcow',
               'extra_properties': '{\'hw_video_model\' : \'vga\'}',
               'nic_config_pb_loc': '/foo/bar', 'exists': True,
               'public': True})
        self.assertEqual('foo', settings.name)
        self.assertEqual('bar', settings.image_user)
        self.assertEqual('qcow2', settings.format)
        self.assertIsNone(settings.url)
        self.assertEqual('/foo/bar.qcow', settings.image_file)
        self.assertEqual('{\'hw_video_model\' : \'vga\'}',
                         settings.extra_properties)
        self.assertEqual('/foo/bar', settings.nic_config_pb_loc)
        self.assertTrue(settings.exists)
        self.assertTrue(settings.public)
