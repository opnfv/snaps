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
import shutil
import uuid
import unittest

from snaps import file_utils
from snaps.openstack.create_image import ImageSettings

import openstack_tests
from snaps.openstack.utils import glance_utils
from snaps.openstack import create_image
from snaps.openstack import os_credentials
from snaps.openstack.tests.os_source_file_test import OSIntegrationTestCase

__author__ = 'spisarski'


class ImageSettingsUnitTests(unittest.TestCase):
    """
    Tests the construction of the ImageSettings class
    """

    def test_no_params(self):
        with self.assertRaises(Exception):
            ImageSettings()

    def test_empty_config(self):
        with self.assertRaises(Exception):
            ImageSettings(config=dict())

    def test_name_only(self):
        with self.assertRaises(Exception):
            ImageSettings(name='foo')

    def test_config_with_name_only(self):
        with self.assertRaises(Exception):
            ImageSettings(config={'name': 'foo'})

    def test_name_user_only(self):
        with self.assertRaises(Exception):
            ImageSettings(name='foo', image_user='bar')

    def test_config_with_name_user_only(self):
        with self.assertRaises(Exception):
            ImageSettings(config={'name': 'foo', 'image_user': 'bar'})

    def test_name_user_format_only(self):
        with self.assertRaises(Exception):
            ImageSettings(name='foo', image_user='bar', img_format='qcow2')

    def test_config_with_name_user_format_only(self):
        with self.assertRaises(Exception):
            ImageSettings(config={'name': 'foo', 'image_user': 'bar', 'format': 'qcow2'})

    def test_name_user_format_url_file_only(self):
        with self.assertRaises(Exception):
            ImageSettings(name='foo', image_user='bar', img_format='qcow2', url='http://foo.com',
                          image_file='/foo/bar.qcow')

    def test_config_with_name_user_format_url_file_only(self):
        with self.assertRaises(Exception):
            ImageSettings(config={'name': 'foo', 'image_user': 'bar', 'format': 'qcow2',
                                  'download_url': 'http://foo.com', 'image_file': '/foo/bar.qcow'})

    def test_name_user_format_url_only(self):
        settings = ImageSettings(name='foo', image_user='bar', img_format='qcow2', url='http://foo.com')
        self.assertEquals('foo', settings.name)
        self.assertEquals('bar', settings.image_user)
        self.assertEquals('qcow2', settings.format)
        self.assertEquals('http://foo.com', settings.url)
        self.assertIsNone(settings.image_file)
        self.assertIsNone(settings.nic_config_pb_loc)

    def test_name_user_format_url_only_properties(self):
        properties = {'hw_video_model': 'vga'}
        settings = ImageSettings(name='foo', image_user='bar', img_format='qcow2', url='http://foo.com',
                                 extra_properties=properties)
        self.assertEquals('foo', settings.name)
        self.assertEquals('bar', settings.image_user)
        self.assertEquals('qcow2', settings.format)
        self.assertEquals('http://foo.com', settings.url)
        self.assertEquals(properties, settings.extra_properties)
        self.assertIsNone(settings.image_file)
        self.assertIsNone(settings.nic_config_pb_loc)

    def test_config_with_name_user_format_url_only(self):
        settings = ImageSettings(config={'name': 'foo', 'image_user': 'bar', 'format': 'qcow2',
                                         'download_url': 'http://foo.com'})
        self.assertEquals('foo', settings.name)
        self.assertEquals('bar', settings.image_user)
        self.assertEquals('qcow2', settings.format)
        self.assertEquals('http://foo.com', settings.url)
        self.assertIsNone(settings.image_file)
        self.assertIsNone(settings.nic_config_pb_loc)

    def test_name_user_format_file_only(self):
        settings = ImageSettings(name='foo', image_user='bar', img_format='qcow2', image_file='/foo/bar.qcow')
        self.assertEquals('foo', settings.name)
        self.assertEquals('bar', settings.image_user)
        self.assertEquals('qcow2', settings.format)
        self.assertIsNone(settings.url)
        self.assertEquals('/foo/bar.qcow', settings.image_file)
        self.assertIsNone(settings.nic_config_pb_loc)

    def test_config_with_name_user_format_file_only(self):
        settings = ImageSettings(config={'name': 'foo', 'image_user': 'bar', 'format': 'qcow2',
                                         'image_file': '/foo/bar.qcow'})
        self.assertEquals('foo', settings.name)
        self.assertEquals('bar', settings.image_user)
        self.assertEquals('qcow2', settings.format)
        self.assertIsNone(settings.url)
        self.assertEquals('/foo/bar.qcow', settings.image_file)
        self.assertIsNone(settings.nic_config_pb_loc)

    def test_all_url(self):
        properties = {'hw_video_model': 'vga'}
        settings = ImageSettings(name='foo', image_user='bar', img_format='qcow2', url='http://foo.com',
                                 extra_properties=properties, nic_config_pb_loc='/foo/bar')
        self.assertEquals('foo', settings.name)
        self.assertEquals('bar', settings.image_user)
        self.assertEquals('qcow2', settings.format)
        self.assertEquals('http://foo.com', settings.url)
        self.assertEquals(properties, settings.extra_properties)
        self.assertIsNone(settings.image_file)
        self.assertEquals('/foo/bar', settings.nic_config_pb_loc)

    def test_config_all_url(self):
        settings = ImageSettings(config={'name': 'foo', 'image_user': 'bar', 'format': 'qcow2',
                                         'download_url': 'http://foo.com',
                                         'extra_properties': '{\'hw_video_model\': \'vga\'}',
                                         'nic_config_pb_loc': '/foo/bar'})
        self.assertEquals('foo', settings.name)
        self.assertEquals('bar', settings.image_user)
        self.assertEquals('qcow2', settings.format)
        self.assertEquals('http://foo.com', settings.url)
        self.assertEquals('{\'hw_video_model\': \'vga\'}', settings.extra_properties)
        self.assertIsNone(settings.image_file)
        self.assertEquals('/foo/bar', settings.nic_config_pb_loc)

    def test_all_file(self):
        properties = {'hw_video_model': 'vga'}
        settings = ImageSettings(name='foo', image_user='bar', img_format='qcow2', image_file='/foo/bar.qcow',
                                 extra_properties=properties, nic_config_pb_loc='/foo/bar')
        self.assertEquals('foo', settings.name)
        self.assertEquals('bar', settings.image_user)
        self.assertEquals('qcow2', settings.format)
        self.assertIsNone(settings.url)
        self.assertEquals('/foo/bar.qcow', settings.image_file)
        self.assertEquals(properties, settings.extra_properties)
        self.assertEquals('/foo/bar', settings.nic_config_pb_loc)

    def test_config_all_file(self):
        settings = ImageSettings(config={'name': 'foo', 'image_user': 'bar', 'format': 'qcow2',
                                         'image_file': '/foo/bar.qcow',
                                         'extra_properties': '{\'hw_video_model\' : \'vga\'}',
                                         'nic_config_pb_loc': '/foo/bar'})
        self.assertEquals('foo', settings.name)
        self.assertEquals('bar', settings.image_user)
        self.assertEquals('qcow2', settings.format)
        self.assertIsNone(settings.url)
        self.assertEquals('/foo/bar.qcow', settings.image_file)
        self.assertEquals('{\'hw_video_model\' : \'vga\'}', settings.extra_properties)
        self.assertEquals('/foo/bar', settings.nic_config_pb_loc)


class CreateImageSuccessTests(OSIntegrationTestCase):
    """
    Test for the CreateImage class defined in create_image.py
    """

    def setUp(self):
        """
        Instantiates the CreateImage object that is responsible for downloading and creating an OS image file
        within OpenStack
        """
        super(self.__class__, self).__start__()

        guid = uuid.uuid4()
        self.image_name = self.__class__.__name__ + '-' + str(guid)
        self.glance = glance_utils.glance_client(self.os_creds)
        self.image_creators = list()

        self.tmp_dir = 'tmp/' + str(guid)
        if not os.path.exists(self.tmp_dir):
            os.makedirs(self.tmp_dir)

    def tearDown(self):
        """
        Cleans the image and downloaded image file
        """
        if self.image_creators:
            while self.image_creators:
                self.image_creators[-1].clean()
                self.image_creators.pop()

        if os.path.exists(self.tmp_dir) and os.path.isdir(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)

        super(self.__class__, self).__clean__()

    def test_create_image_clean_url(self):
        """
        Tests the creation of an OpenStack image from a URL.
        """
        # Create Image
        # Set the default image settings, then set any custom parameters sent from the app
        os_image_settings = openstack_tests.cirros_url_image(name=self.image_name)
        if self.image_metadata:
            if 'disk_url' in self.image_metadata and self.image_metadata['disk_url']:
                os_image_settings.url = self.image_metadata['disk_url']
            if 'extra_properties' in self.image_metadata and self.image_metadata['extra_properties']:
                os_image_settings.extra_properties = self.image_metadata['extra_properties']

        # If this is a 3-part image create the kernel and ramdisk images first
        if self.image_metadata:
            if 'kernel_url' in self.image_metadata and self.image_metadata['kernel_url']:
                kernel_image_settings = openstack_tests.cirros_url_image(
                    name=self.image_name+'_kernel', url=self.image_metadata['kernel_url'])
                self.image_creators.append(create_image.OpenStackImage(self.os_creds, kernel_image_settings))
                kernel_image = self.image_creators[-1].create()
                self.assertIsNotNone(kernel_image)
                os_image_settings.extra_properties['kernel_id'] = kernel_image.id
                self.assertEquals(get_image_size(kernel_image_settings), kernel_image.size)

            if 'ramdisk_url' in self.image_metadata and self.image_metadata['ramdisk_url']:
                ramdisk_image_settings = openstack_tests.cirros_url_image(
                    name=self.image_name+'_ramdisk', url=self.image_metadata['ramdisk_url'])
                self.image_creators.append(create_image.OpenStackImage(self.os_creds, ramdisk_image_settings))
                ramdisk_image = self.image_creators[-1].create()
                self.assertIsNotNone(ramdisk_image)
                os_image_settings.extra_properties['ramdisk_id'] = ramdisk_image.id
                self.assertEquals(get_image_size(ramdisk_image_settings), ramdisk_image.size)

        self.image_creators.append(create_image.OpenStackImage(self.os_creds, os_image_settings))
        created_image = self.image_creators[-1].create()
        self.assertIsNotNone(created_image)

        retrieved_image = glance_utils.get_image(self.glance, os_image_settings.name)
        self.assertIsNotNone(retrieved_image)
        self.assertEquals(created_image.size, retrieved_image.size)
        self.assertEquals(get_image_size(os_image_settings), retrieved_image.size)
        self.assertEquals(created_image.name, retrieved_image.name)
        self.assertEquals(created_image.id, retrieved_image.id)

    def test_create_image_clean_url_properties(self):
        """
        Tests the creation of an OpenStack image from a URL and set properties.
        """
        # Create Image
        # Set the default image settings, then set any custom parameters sent from the app
        os_image_settings = openstack_tests.cirros_url_image(name=self.image_name)
        # Set properties
        os_image_settings.extra_properties = {'hw_video_model': 'vga'}

        if self.image_metadata:
            if 'disk_url' in self.image_metadata and self.image_metadata['disk_url']:
                os_image_settings.url = self.image_metadata['disk_url']
            if 'extra_properties' in self.image_metadata and self.image_metadata['extra_properties']:
                os_image_settings.extra_properties = dict(
                    os_image_settings.extra_properties.items()
                    + self.image_metadata['extra_properties'].items())

        # If this is a 3-part image create the kernel and ramdisk images first
        if self.image_metadata:
            if 'kernel_url' in self.image_metadata and self.image_metadata['kernel_url']:
                kernel_image_settings = openstack_tests.cirros_url_image(
                    name=self.image_name+'_kernel', url=self.image_metadata['kernel_url'])
                self.image_creators.append(create_image.OpenStackImage(self.os_creds, kernel_image_settings))
                kernel_image = self.image_creators[-1].create()
                self.assertIsNotNone(kernel_image)
                os_image_settings.extra_properties[str('kernel_id')] = kernel_image.id
                self.assertEquals(get_image_size(kernel_image_settings), kernel_image.size)

            if 'ramdisk_url' in self.image_metadata and self.image_metadata['ramdisk_url']:
                ramdisk_image_settings = openstack_tests.cirros_url_image(
                    name=self.image_name+'_ramdisk', url=self.image_metadata['ramdisk_url'])
                self.image_creators.append(create_image.OpenStackImage(self.os_creds, ramdisk_image_settings))
                ramdisk_image = self.image_creators[-1].create()
                self.assertIsNotNone(ramdisk_image)
                os_image_settings.extra_properties[str('ramdisk_id')] = ramdisk_image.id
                self.assertEquals(get_image_size(ramdisk_image_settings), ramdisk_image.size)

        self.image_creators.append(create_image.OpenStackImage(self.os_creds, os_image_settings))
        created_image = self.image_creators[-1].create()
        self.assertIsNotNone(created_image)

        retrieved_image = glance_utils.get_image(self.glance, os_image_settings.name)
        self.assertIsNotNone(retrieved_image)
        self.assertEquals(self.image_creators[-1].get_image().size, retrieved_image.size)
        self.assertEquals(get_image_size(os_image_settings), retrieved_image.size)
        self.assertEquals(created_image.name, retrieved_image.name)
        self.assertEquals(created_image.id, retrieved_image.id)
        # self.assertEquals(created_image.properties, retrieved_image.properties)

    def test_create_image_clean_file(self):
        """
        Tests the creation of an OpenStack image from a file.
        """

        # Create Image
        # Set the default image settings, then set any custom parameters sent from the app
        url_image_settings = openstack_tests.cirros_url_image('foo')
        if self.image_metadata:
            if 'disk_url' in self.image_metadata and self.image_metadata['disk_url']:
                url_image_settings.url = self.image_metadata['disk_url']

        # Download the file of the image
        image_file = file_utils.download(url_image_settings.url, self.tmp_dir)
        file_image_settings = openstack_tests.file_image_test_settings(name=self.image_name, file_path=image_file.name)

        # Set extra properties sent from the app (if any)
        if self.image_metadata:
            if 'extra_properties' in self.image_metadata and self.image_metadata['extra_properties']:
                file_image_settings.extra_properties = self.image_metadata['extra_properties']

        # If this is a 3-part image create the kernel and ramdisk images first
        if self.image_metadata:
            if 'kernel_url' in self.image_metadata and self.image_metadata['kernel_url']:
                kernel_image_file = file_utils.download(self.image_metadata['kernel_url'], self.tmp_dir)
                kernel_image_settings = openstack_tests.file_image_test_settings(
                    name=self.image_name+'_kernel', file_path=kernel_image_file.name)
                self.image_creators.append(create_image.OpenStackImage(self.os_creds, kernel_image_settings))
                kernel_image = self.image_creators[-1].create()
                self.assertIsNotNone(kernel_image)
                file_image_settings.extra_properties['kernel_id'] = kernel_image.id
                self.assertIsNotNone(kernel_image)
                self.assertEquals(get_image_size(kernel_image_settings), kernel_image.size)

            if 'ramdisk_url' in self.image_metadata and self.image_metadata['ramdisk_url']:
                ramdisk_image_file = file_utils.download(self.image_metadata['ramdisk_url'], self.tmp_dir)
                ramdisk_image_settings = openstack_tests.file_image_test_settings(
                    name=self.image_name+'_ramdisk', file_path=ramdisk_image_file.name)
                self.image_creators.append(create_image.OpenStackImage(self.os_creds, ramdisk_image_settings))
                ramdisk_image = self.image_creators[-1].create()
                self.assertIsNotNone(ramdisk_image)
                file_image_settings.extra_properties['ramdisk_id'] = ramdisk_image.id

        self.image_creators.append(create_image.OpenStackImage(self.os_creds, file_image_settings))
        created_image = self.image_creators[-1].create()
        self.assertIsNotNone(created_image)
        self.assertEqual(self.image_name, created_image.name)

        retrieved_image = glance_utils.get_image(self.glance, file_image_settings.name)
        self.assertIsNotNone(retrieved_image)
        self.assertEquals(self.image_creators[-1].get_image().size, retrieved_image.size)
        self.assertEquals(get_image_size(file_image_settings), retrieved_image.size)

        self.assertEquals(created_image.name, retrieved_image.name)
        self.assertEquals(created_image.id, retrieved_image.id)

    def test_create_delete_image(self):
        """
        Tests the creation then deletion of an OpenStack image to ensure clean() does not raise an Exception.
        """
        # Create Image
        # Set the default image settings, then set any custom parameters sent from the app
        os_image_settings = openstack_tests.cirros_url_image(name=self.image_name)
        if self.image_metadata:
            if 'disk_url' in self.image_metadata and self.image_metadata['disk_url']:
                os_image_settings.url = self.image_metadata['disk_url']
            if 'extra_properties' in self.image_metadata and self.image_metadata['extra_properties']:
                os_image_settings.extra_properties = self.image_metadata['extra_properties']

        # If this is a 3-part image create the kernel and ramdisk images first
        if self.image_metadata:
            if 'kernel_url' in self.image_metadata and self.image_metadata['kernel_url']:
                kernel_image_settings = openstack_tests.cirros_url_image(
                    name=self.image_name+'_kernel', url=self.image_metadata['kernel_url'])
                self.image_creators.append(create_image.OpenStackImage(self.os_creds, kernel_image_settings))
                kernel_image = self.image_creators[-1].create()
                self.assertIsNotNone(kernel_image)
                self.assertEquals(get_image_size(kernel_image_settings), kernel_image.size)
                os_image_settings.extra_properties['kernel_id'] = kernel_image.id

            if 'ramdisk_url' in self.image_metadata and self.image_metadata['ramdisk_url']:
                ramdisk_image_settings = openstack_tests.cirros_url_image(
                    name=self.image_name+'_ramdisk', url=self.image_metadata['ramdisk_url'])
                self.image_creators.append(create_image.OpenStackImage(self.os_creds, ramdisk_image_settings))
                ramdisk_image = self.image_creators[-1].create()
                self.assertIsNotNone(ramdisk_image)
                self.assertEquals(get_image_size(ramdisk_image_settings), ramdisk_image.size)
                os_image_settings.extra_properties['ramdisk_id'] = ramdisk_image.id

        self.image_creators.append(create_image.OpenStackImage(self.os_creds, os_image_settings))
        created_image = self.image_creators[-1].create()
        self.assertIsNotNone(created_image)

        retrieved_image = glance_utils.get_image(self.glance, os_image_settings.name)
        self.assertIsNotNone(retrieved_image)
        self.assertEquals(self.image_creators[-1].get_image().size, retrieved_image.size)
        self.assertEquals(get_image_size(os_image_settings), retrieved_image.size)

        # Delete Image manually
        glance_utils.delete_image(self.glance, created_image)

        self.assertIsNone(glance_utils.get_image(self.glance, self.image_creators[-1].image_settings.name))

        # Must not throw an exception when attempting to cleanup non-existent image
        self.image_creators[-1].clean()
        self.assertIsNone(self.image_creators[-1].get_image())
        self.image_creators.pop()

    def test_create_same_image(self):
        """
        Tests the creation of an OpenStack image when the image already exists.
        """
        # Create Image
        # Set the default image settings, then set any custom parameters sent from the app
        os_image_settings = openstack_tests.cirros_url_image(name=self.image_name)
        if self.image_metadata:
            if 'disk_url' in self.image_metadata and self.image_metadata['disk_url']:
                os_image_settings.url = self.image_metadata['disk_url']
            if 'extra_properties' in self.image_metadata and self.image_metadata['extra_properties']:
                os_image_settings.extra_properties = self.image_metadata['extra_properties']

        # If this is a 3-part image create the kernel and ramdisk images first
        if self.image_metadata:
            if 'kernel_url' in self.image_metadata and self.image_metadata['kernel_url']:
                kernel_image_settings = openstack_tests.cirros_url_image(
                    name=self.image_name+'_kernel', url=self.image_metadata['kernel_url'])
                self.image_creators.append(create_image.OpenStackImage(self.os_creds, kernel_image_settings))
                kernel_image = self.image_creators[-1].create()
                self.assertIsNotNone(kernel_image)
                self.assertEquals(get_image_size(kernel_image_settings), kernel_image.size)
                os_image_settings.extra_properties['kernel_id'] = kernel_image.id

            if 'ramdisk_url' in self.image_metadata and self.image_metadata['ramdisk_url']:
                ramdisk_image_settings = openstack_tests.cirros_url_image(
                    name=self.image_name+'_ramdisk', url=self.image_metadata['ramdisk_url'])
                self.image_creators.append(create_image.OpenStackImage(self.os_creds, ramdisk_image_settings))
                ramdisk_image = self.image_creators[-1].create()
                self.assertIsNotNone(ramdisk_image)
                os_image_settings.extra_properties['ramdisk_id'] = ramdisk_image.id

        self.image_creators.append(create_image.OpenStackImage(self.os_creds, os_image_settings))
        image1 = self.image_creators[-1].create()

        retrieved_image = glance_utils.get_image(self.glance, os_image_settings.name)
        self.assertIsNotNone(retrieved_image)
        self.assertEquals(self.image_creators[-1].get_image().size, retrieved_image.size)
        self.assertEquals(get_image_size(os_image_settings), retrieved_image.size)
        self.assertEquals(image1.name, retrieved_image.name)
        self.assertEquals(image1.id, retrieved_image.id)
        self.assertEquals(image1.properties, retrieved_image.properties)

        # Should be retrieving the instance data
        os_image_2 = create_image.OpenStackImage(self.os_creds, os_image_settings)
        image2 = os_image_2.create()
        self.assertEquals(image1.id, image2.id)


class CreateImageNegativeTests(OSIntegrationTestCase):
    """
    Negative test cases for the CreateImage class
    """

    def setUp(self):
        super(self.__class__, self).__start__()

        self.image_name = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.image_creator = None

    def tearDown(self):
        if self.image_creator:
            self.image_creator.clean()

        super(self.__class__, self).__clean__()

    def test_none_image_name(self):
        """
        Expect an exception when the image name is None
        """
        os_image_settings = openstack_tests.cirros_url_image(name=self.image_name)
        with self.assertRaises(Exception):
            self.image_creator = create_image.OpenStackImage(
                self.os_creds, create_image.ImageSettings(
                    name=None, image_user=os_image_settings.image_user, img_format=os_image_settings.format,
                    url=os_image_settings.url))

            self.fail('Exception should have been thrown prior to this line')

    def test_bad_image_url(self):
        """
        Expect an exception when the image download url is bad
        """
        os_image_settings = openstack_tests.cirros_url_image(name=self.image_name)
        self.image_creator = create_image.OpenStackImage(self.os_creds, create_image.ImageSettings(
            name=os_image_settings.name, image_user=os_image_settings.image_user,
            img_format=os_image_settings.format, url="http://foo.bar"))
        with self.assertRaises(Exception):
            self.image_creator.create()

    def test_bad_image_file(self):
        """
        Expect an exception when the image file does not exist
        """
        os_image_settings = openstack_tests.cirros_url_image(name=self.image_name)
        self.image_creator = create_image.OpenStackImage(
            self.os_creds,
            create_image.ImageSettings(name=os_image_settings.name, image_user=os_image_settings.image_user,
                                       img_format=os_image_settings.format, image_file="/foo/bar.qcow"))
        with self.assertRaises(Exception):
            self.image_creator.create()

    def test_none_proj_name(self):
        """
        Expect an exception when the project name is None
        """
        os_image_settings = openstack_tests.cirros_url_image(name=self.image_name)
        with self.assertRaises(Exception):
            self.image_creator = create_image.OpenStackImage(
                os_credentials.OSCreds(self.os_creds.username, self.os_creds.password, self.os_creds.auth_url, None,
                                       proxy_settings=self.os_creds.proxy_settings),
                os_image_settings)
            self.image_creator.create()

    def test_none_auth_url(self):
        """
        Expect an exception when the project name is None
        """
        os_image_settings = openstack_tests.cirros_url_image(name=self.image_name)
        with self.assertRaises(Exception):
            self.image_creator = create_image.OpenStackImage(
                os_credentials.OSCreds(self.os_creds.username, self.os_creds.password, None,
                                       self.os_creds.project_name, proxy_settings=self.os_creds.proxy_settings),
                os_image_settings)
            self.image_creator.create()

    def test_none_password(self):
        """
        Expect an exception when the project name is None
        """
        os_image_settings = openstack_tests.cirros_url_image(name=self.image_name)
        with self.assertRaises(Exception):
            self.image_creator = create_image.OpenStackImage(
                os_credentials.OSCreds(self.os_creds.username, None, self.os_creds.os_auth_url,
                                       self.os_creds.project_name, proxy_settings=self.os_creds.proxy_settings),
                os_image_settings)

    def test_none_user(self):
        """
        Expect an exception when the project name is None
        """
        os_image_settings = openstack_tests.cirros_url_image(name=self.image_name)
        with self.assertRaises(Exception):
            self.image_creator = create_image.OpenStackImage(
                os_credentials.OSCreds(None, self.os_creds.password, self.os_creds.os_auth_url,
                                       self.os_creds.project_name,
                                       proxy_settings=self.os_creds.proxy_settings),
                os_image_settings)


class CreateMultiPartImageTests(OSIntegrationTestCase):
    """
    Test for creating a 3-part image
    """
    def setUp(self):
        """
        Instantiates the CreateImage object that is responsible for
        downloading and creating an OS image file within OpenStack
        """
        super(self.__class__, self).__start__()

        guid = uuid.uuid4()
        self.image_creators = list()
        self.image_name = self.__class__.__name__ + '-' + str(guid)
        self.glance = glance_utils.glance_client(self.os_creds)

        self.tmp_dir = 'tmp/' + str(guid)
        if not os.path.exists(self.tmp_dir):
            os.makedirs(self.tmp_dir)

    def tearDown(self):
        """
        Cleans the images and downloaded image file
        """
        while self.image_creators:
            self.image_creators[-1].clean()
            self.image_creators.pop()

        if os.path.exists(self.tmp_dir) and os.path.isdir(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)

        super(self.__class__, self).__clean__()

    def test_create_three_part_image_from_url(self):
        """
        Tests the creation of a 3-part OpenStack image from a URL.
        """
        # Set properties
        properties = {}
        if self.image_metadata:
            if 'extra_properties' in self.image_metadata and self.image_metadata['extra_properties']:
                properties = self.image_metadata['extra_properties']

        # Create the kernel image
        kernel_image_settings = openstack_tests.cirros_url_image(
            name=self.image_name+'_kernel',
            url='http://download.cirros-cloud.net/0.3.4/cirros-0.3.4-x86_64-kernel')

        if self.image_metadata:
            if 'kernel_url' in self.image_metadata and self.image_metadata['kernel_url']:
                kernel_image_settings.url = self.image_metadata['kernel_url']
        self.image_creators.append(create_image.OpenStackImage(self.os_creds, kernel_image_settings))
        kernel_image = self.image_creators[-1].create()
        self.assertIsNotNone(kernel_image)
        self.assertEquals(get_image_size(kernel_image_settings), kernel_image.size)

        # Create the ramdisk image
        ramdisk_image_settings = openstack_tests.cirros_url_image(
            name=self.image_name+'_ramdisk',
            url='http://download.cirros-cloud.net/0.3.4/cirros-0.3.4-x86_64-initramfs')
        if self.image_metadata:
            if 'ramdisk_url' in self.image_metadata and self.image_metadata['ramdisk_url']:
                ramdisk_image_settings.url = self.image_metadata['ramdisk_url']
        self.image_creators.append(create_image.OpenStackImage(self.os_creds, ramdisk_image_settings))
        ramdisk_image = self.image_creators[-1].create()
        self.assertIsNotNone(ramdisk_image)
        self.assertEquals(get_image_size(ramdisk_image_settings), ramdisk_image.size)

        # Create the main image
        os_image_settings = openstack_tests.cirros_url_image(
            name=self.image_name,
            url='http://download.cirros-cloud.net/0.3.4/cirros-0.3.4-x86_64-disk.img')
        if self.image_metadata:
            if 'disk_url' in self.image_metadata and self.image_metadata['disk_url']:
                os_image_settings.url = self.image_metadata['disk_url']

        properties['kernel_id'] = kernel_image.id
        properties['ramdisk_id'] = ramdisk_image.id
        os_image_settings.extra_properties = properties

        self.image_creators.append(create_image.OpenStackImage(self.os_creds, os_image_settings))
        created_image = self.image_creators[-1].create()
        self.assertIsNotNone(created_image)
        self.assertEqual(self.image_name, created_image.name)

        retrieved_image = glance_utils.get_image(self.glance, os_image_settings.name)
        self.assertIsNotNone(retrieved_image)
        self.assertEquals(self.image_creators[-1].get_image().size, retrieved_image.size)
        self.assertEquals(get_image_size(os_image_settings), retrieved_image.size)
        self.assertEquals(created_image.name, retrieved_image.name)
        self.assertEquals(created_image.id, retrieved_image.id)
        self.assertEquals(created_image.properties, retrieved_image.properties)

    def test_create_three_part_image_from_file(self):
        """
        Tests the creation of a 3-part OpenStack image from files.
        """
        # Set properties
        properties = {}
        if self.image_metadata:
            if 'extra_properties' in self.image_metadata and self.image_metadata['extra_properties']:
                properties = self.image_metadata['extra_properties']
        # Create the kernel image
        kernel_url = 'http://download.cirros-cloud.net/0.3.4/cirros-0.3.4-x86_64-kernel'
        if self.image_metadata:
            if 'kernel_url' in self.image_metadata and self.image_metadata['kernel_url']:
                kernel_url = self.image_metadata['kernel_url']
        kernel_image_file = file_utils.download(kernel_url, self.tmp_dir)
        kernel_file_image_settings = openstack_tests.file_image_test_settings(
            name=self.image_name+'_kernel', file_path=kernel_image_file.name)
        self.image_creators.append(create_image.OpenStackImage(self.os_creds, kernel_file_image_settings))
        kernel_image = self.image_creators[-1].create()
        self.assertIsNotNone(kernel_image)
        self.assertEquals(get_image_size(kernel_file_image_settings), kernel_image.size)

        # Create the ramdisk image
        ramdisk_url = 'http://download.cirros-cloud.net/0.3.4/cirros-0.3.4-x86_64-initramfs'
        if self.image_metadata:
            if 'ramdisk_url' in self.image_metadata and self.image_metadata['ramdisk_url']:
                ramdisk_url = self.image_metadata['ramdisk_url']
        ramdisk_image_file = file_utils.download(ramdisk_url, self.tmp_dir)
        ramdisk_file_image_settings = openstack_tests.file_image_test_settings(
            name=self.image_name+'_ramdisk', file_path=ramdisk_image_file.name)
        self.image_creators.append(create_image.OpenStackImage(self.os_creds, ramdisk_file_image_settings))
        ramdisk_image = self.image_creators[-1].create()
        self.assertIsNotNone(ramdisk_image)
        self.assertEquals(get_image_size(ramdisk_file_image_settings), ramdisk_image.size)

        # Create the main image
        image_url = 'http://download.cirros-cloud.net/0.3.4/cirros-0.3.4-x86_64-disk.img'
        image_file = file_utils.download(image_url, self.tmp_dir)
        file_image_settings = openstack_tests.file_image_test_settings(name=self.image_name, file_path=image_file.name)
        properties['kernel_id'] = kernel_image.id
        properties['ramdisk_id'] = ramdisk_image.id
        file_image_settings.extra_properties = properties
        self.image_creators.append(create_image.OpenStackImage(self.os_creds, file_image_settings))
        created_image = self.image_creators[-1].create()

        self.assertIsNotNone(created_image)
        self.assertEqual(self.image_name, created_image.name)

        retrieved_image = glance_utils.get_image(self.glance, file_image_settings.name)
        self.assertIsNotNone(retrieved_image)

        self.assertEquals(self.image_creators[-1].get_image().size, retrieved_image.size)
        self.assertEquals(get_image_size(file_image_settings), retrieved_image.size)

        self.assertEquals(created_image.name, retrieved_image.name)
        self.assertEquals(created_image.id, retrieved_image.id)
        self.assertEquals(created_image.properties, retrieved_image.properties)


def get_image_size(image_settings):
    """
    Returns the expected image size
    :return:
    """
    if image_settings.image_file:
        return os.path.getsize(image_settings.image_file)
    elif image_settings.url:
        return int(file_utils.get_content_length(image_settings.url))
    else:
        raise Exception('Cannot retrieve expected image size. Image filename or URL has not been configured')
