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
from glanceclient.exc import HTTPBadRequest

try:
    from urllib.request import URLError
except ImportError:
    from urllib2 import URLError

import logging
import shutil
import unittest
import uuid

import os

from snaps import file_utils
from snaps.config.image import ImageConfigError
from snaps.openstack import create_image
from snaps.openstack.create_image import ImageSettings, ImageCreationError
from snaps.config.image import ImageConfig
from snaps.openstack.tests import openstack_tests
from snaps.openstack.tests.os_source_file_test import OSIntegrationTestCase
from snaps.openstack.utils import glance_utils

__author__ = 'spisarski'

logger = logging.getLogger('create_image_tests')


class ImageSettingsUnitTests(unittest.TestCase):
    """
    Tests the construction of the ImageSettings class
    To be removed once the deprecated class ImageSettings is finally removed
    from the source tree
    """

    def test_no_params(self):
        with self.assertRaises(ImageConfigError):
            ImageSettings()

    def test_empty_config(self):
        with self.assertRaises(ImageConfigError):
            ImageSettings(**dict())

    def test_name_only(self):
        with self.assertRaises(ImageConfigError):
            ImageSettings(name='foo')

    def test_config_with_name_only(self):
        with self.assertRaises(ImageConfigError):
            ImageSettings(**{'name': 'foo'})

    def test_name_user_only(self):
        with self.assertRaises(ImageConfigError):
            ImageSettings(name='foo', image_user='bar')

    def test_config_with_name_user_only(self):
        with self.assertRaises(ImageConfigError):
            ImageSettings(**{'name': 'foo', 'image_user': 'bar'})

    def test_name_user_format_only(self):
        with self.assertRaises(ImageConfigError):
            ImageSettings(name='foo', image_user='bar', img_format='qcow2')

    def test_config_with_name_user_format_only(self):
        with self.assertRaises(ImageConfigError):
            ImageSettings(
                **{'name': 'foo', 'image_user': 'bar', 'format': 'qcow2'})

    def test_name_user_format_url_only(self):
        settings = ImageSettings(name='foo', image_user='bar',
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
        settings = ImageSettings(name='foo', image_user='bar',
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
        settings = ImageSettings(
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
        settings = ImageSettings(name='foo', image_user='bar',
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
        settings = ImageSettings(
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
        kernel_settings = ImageSettings(name='kernel', url='http://kernel.com',
                                        image_user='bar', img_format='qcow2')
        ramdisk_settings = ImageSettings(name='ramdisk',
                                         url='http://ramdisk.com',
                                         image_user='bar', img_format='qcow2')
        settings = ImageSettings(name='foo', image_user='bar',
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
        settings = ImageSettings(
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
        settings = ImageSettings(name='foo', image_user='bar',
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
        settings = ImageSettings(
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


class CreateImageSuccessTests(OSIntegrationTestCase):
    """
    Test for the CreateImage class defined in create_image.py
    """

    def setUp(self):
        """
        Instantiates the CreateImage object that is responsible for downloading
        and creating an OS image file within OpenStack
        """
        super(self.__class__, self).__start__()

        guid = uuid.uuid4()
        self.image_name = self.__class__.__name__ + '-' + str(guid)
        self.glance = glance_utils.glance_client(
            self.os_creds, self.os_session)
        self.image_creator = None

        if self.image_metadata and 'glance_tests' in self.image_metadata:
            glance_test_meta = self.image_metadata['glance_tests']
        else:
            glance_test_meta = None

        self.tmp_dir = 'tmp/' + str(guid)
        if not os.path.exists(self.tmp_dir):
            os.makedirs(self.tmp_dir)

        self.image_settings = openstack_tests.cirros_image_settings(
            name=self.image_name,
            image_metadata=glance_test_meta)

    def tearDown(self):
        """
        Cleans the image and downloaded image file
        """
        if self.image_creator:
            self.image_creator.clean()

        if os.path.exists(self.tmp_dir) and os.path.isdir(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)

        super(self.__class__, self).__clean__()

    def test_create_image_clean_url(self):
        """
        Tests the creation of an OpenStack image from a URL.
        """
        # Create Image
        # Set the default image settings, then set any custom parameters sent
        # from the app

        self.image_creator = create_image.OpenStackImage(self.os_creds,
                                                         self.image_settings)
        created_image = self.image_creator.create()
        self.assertIsNotNone(created_image)

        retrieved_image = glance_utils.get_image(
            self.glance, image_settings=self.image_settings)
        self.assertIsNotNone(retrieved_image)
        self.assertEqual(created_image.size, retrieved_image.size)
        self.assertEqual(get_image_size(self.image_settings),
                         retrieved_image.size)
        self.assertEqual(created_image.name, retrieved_image.name)
        self.assertEqual(created_image.id, retrieved_image.id)

    def test_create_image_clean_url_properties(self):
        """
        Tests the creation of an OpenStack image from a URL and set properties.
        """
        # Create Image
        # Set the default image settings, then set any custom parameters sent
        # from the app
        self.image_creator = create_image.OpenStackImage(self.os_creds,
                                                         self.image_settings)
        created_image = self.image_creator.create()
        self.assertIsNotNone(created_image)

        retrieved_image = glance_utils.get_image(
            self.glance, image_settings=self.image_settings)
        self.assertIsNotNone(retrieved_image)
        self.assertEqual(self.image_creator.get_image().size,
                         retrieved_image.size)
        self.assertEqual(get_image_size(self.image_settings),
                         retrieved_image.size)
        self.assertEqual(created_image.name, retrieved_image.name)
        self.assertEqual(created_image.id, retrieved_image.id)
        self.assertEqual(created_image.properties, retrieved_image.properties)

    def test_create_image_clean_file(self):
        """
        Tests the creation of an OpenStack image from a file.
        """
        if not self.image_settings.image_file and self.image_settings.url:
            # Download the file of the image
            image_file_name = file_utils.download(self.image_settings.url,
                                                  self.tmp_dir).name
        else:
            image_file_name = self.image_settings.image_file

        if image_file_name:
            file_image_settings = openstack_tests.file_image_test_settings(
                name=self.image_name, file_path=image_file_name)

            self.image_creator = create_image.OpenStackImage(
                self.os_creds, file_image_settings)
            created_image = self.image_creator.create()
            self.assertIsNotNone(created_image)
            self.assertEqual(self.image_name, created_image.name)

            retrieved_image = glance_utils.get_image(
                self.glance, image_settings=file_image_settings)
            self.assertIsNotNone(retrieved_image)
            self.assertEqual(self.image_creator.get_image().size,
                             retrieved_image.size)
            self.assertEqual(get_image_size(file_image_settings),
                             retrieved_image.size)

            self.assertEqual(created_image.name, retrieved_image.name)
            self.assertEqual(created_image.id, retrieved_image.id)
        else:
            logger.warn(
                'Test not executed as the image metadata requires image files')

    def test_create_delete_image(self):
        """
        Tests the creation then deletion of an OpenStack image to ensure
        clean() does not raise an Exception.
        """
        # Create Image
        self.image_creator = create_image.OpenStackImage(
            self.os_creds, self.image_settings)
        created_image = self.image_creator.create()
        self.assertIsNotNone(created_image)

        retrieved_image = glance_utils.get_image(
            self.glance, image_settings=self.image_settings)
        self.assertIsNotNone(retrieved_image)
        self.assertEqual(self.image_creator.get_image().size,
                         retrieved_image.size)
        self.assertEqual(get_image_size(self.image_settings),
                         retrieved_image.size)

        # Delete Image manually
        glance_utils.delete_image(self.glance, created_image)

        self.assertIsNone(glance_utils.get_image(
            self.glance, image_settings=self.image_creator.image_settings))

        # Must not throw an exception when attempting to cleanup non-existent
        # image
        self.image_creator.clean()
        self.assertIsNone(self.image_creator.get_image())

    def test_create_same_image(self):
        """
        Tests the creation of an OpenStack image when the image already exists.
        """
        # Create Image
        self.image_creator = create_image.OpenStackImage(self.os_creds,
                                                         self.image_settings)
        image1 = self.image_creator.create()

        retrieved_image = glance_utils.get_image(
            self.glance, image_settings=self.image_settings)
        self.assertIsNotNone(retrieved_image)
        self.assertEqual(self.image_creator.get_image().size,
                         retrieved_image.size)
        self.assertEqual(get_image_size(self.image_settings),
                         retrieved_image.size)
        self.assertEqual(image1.name, retrieved_image.name)
        self.assertEqual(image1.id, retrieved_image.id)
        self.assertEqual(image1.properties, retrieved_image.properties)

        # Should be retrieving the instance data
        os_image_2 = create_image.OpenStackImage(self.os_creds,
                                                 self.image_settings)
        image2 = os_image_2.create()
        self.assertEqual(image1.id, image2.id)

    def test_create_same_image_new_settings(self):
        """
        Tests the creation of an OpenStack image when the image already exists
        and the configuration only contains the name.
        """
        # Create Image
        self.image_creator = create_image.OpenStackImage(self.os_creds,
                                                         self.image_settings)
        image1 = self.image_creator.create()

        retrieved_image = glance_utils.get_image(
            self.glance, image_settings=self.image_settings)
        self.assertIsNotNone(retrieved_image)
        self.assertEqual(self.image_creator.get_image().size,
                         retrieved_image.size)
        self.assertEqual(get_image_size(self.image_settings),
                         retrieved_image.size)
        self.assertEqual(image1.name, retrieved_image.name)
        self.assertEqual(image1.id, retrieved_image.id)
        self.assertEqual(image1.properties, retrieved_image.properties)

        # Should be retrieving the instance data
        image_2_settings = ImageConfig(name=self.image_settings.name,
                                       image_user='foo', exists=True)
        os_image_2 = create_image.OpenStackImage(self.os_creds,
                                                 image_2_settings)
        image2 = os_image_2.create()
        self.assertEqual(image1.id, image2.id)


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

    def test_bad_image_name(self):
        """
        Expect an ImageCreationError when the image name does not exist when a
        file or URL has not been configured
        """
        os_image_settings = ImageConfig(name='foo', image_user='bar',
                                        exists=True)
        self.image_creator = create_image.OpenStackImage(self.os_creds,
                                                         os_image_settings)

        with self.assertRaises(ImageCreationError):
            self.image_creator.create()

            self.fail('ImageCreationError should have been raised prior to'
                      'this line')

    def test_bad_image_url(self):
        """
        Expect an ImageCreationError when the image download url is bad
        """
        os_image_settings = openstack_tests.cirros_image_settings(
            name=self.image_name)
        self.image_creator = create_image.OpenStackImage(
            self.os_creds,
            ImageConfig(
                name=os_image_settings.name,
                image_user=os_image_settings.image_user,
                img_format=os_image_settings.format,
                url="http://foo.bar"))

        try:
            self.image_creator.create()
        except HTTPBadRequest:
            pass
        except URLError:
            pass
        except Exception as e:
            self.fail('Invalid Exception ' + str(e))

    def test_bad_image_image_type(self):
        """
        Expect an ImageCreationError when the image type bad
        """
        os_image_settings = openstack_tests.cirros_image_settings(
            name=self.image_name)
        self.image_creator = create_image.OpenStackImage(
            self.os_creds,
            ImageConfig(
                name=os_image_settings.name,
                image_user=os_image_settings.image_user,
                img_format='foo', url=os_image_settings.url))

        with self.assertRaises(Exception):
            self.image_creator.create()

    def test_bad_image_file(self):
        """
        Expect an ImageCreationError when the image file does not exist
        """
        os_image_settings = openstack_tests.cirros_image_settings(
            name=self.image_name)
        self.image_creator = create_image.OpenStackImage(
            self.os_creds,
            ImageConfig(
                name=os_image_settings.name,
                image_user=os_image_settings.image_user,
                img_format=os_image_settings.format, image_file="/foo/bar.qcow"))
        with self.assertRaises(IOError):
            self.image_creator.create()


class CreateMultiPartImageTests(OSIntegrationTestCase):
    """
    Test different means for creating a 3-part images
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
        self.glance = glance_utils.glance_client(
            self.os_creds, self.os_session)

        self.tmp_dir = 'tmp/' + str(guid)
        if not os.path.exists(self.tmp_dir):
            os.makedirs(self.tmp_dir)

        if self.image_metadata and 'glance_tests' in self.image_metadata:
            self.glance_test_meta = self.image_metadata['glance_tests']
        else:
            self.glance_test_meta = dict()

    def tearDown(self):
        """
        Cleans the images and downloaded image file
        """
        for image_creator in self.image_creators:
            image_creator.clean()

        if os.path.exists(self.tmp_dir) and os.path.isdir(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)

        super(self.__class__, self).__clean__()

    def test_create_three_part_image_from_url(self):
        """
        Tests the creation of a 3-part OpenStack image from a URL.
        """
        # Create the kernel image
        if 'disk_file' not in self.glance_test_meta:
            image_settings = openstack_tests.cirros_image_settings(
                name=self.image_name,
                image_metadata={
                    'disk_url':
                        openstack_tests.CIRROS_DEFAULT_IMAGE_URL,
                    'kernel_url':
                        openstack_tests.CIRROS_DEFAULT_KERNEL_IMAGE_URL,
                    'ramdisk_url':
                        openstack_tests.CIRROS_DEFAULT_RAMDISK_IMAGE_URL})

            image_creator = create_image.OpenStackImage(self.os_creds,
                                                        image_settings)
            self.image_creators.append(image_creator)
            image_creator.create()

            main_image = glance_utils.get_image(self.glance,
                                                image_settings=image_settings)
            self.assertIsNotNone(main_image)
            self.assertIsNotNone(image_creator.get_image())
            self.assertEqual(image_creator.get_image().id, main_image.id)

            kernel_image = glance_utils.get_image(
                self.glance,
                image_settings=image_settings.kernel_image_settings)
            self.assertIsNotNone(kernel_image)
            self.assertIsNotNone(image_creator.get_kernel_image())
            self.assertEqual(kernel_image.id,
                             image_creator.get_kernel_image().id)

            ramdisk_image = glance_utils.get_image(
                self.glance,
                image_settings=image_settings.ramdisk_image_settings)
            self.assertIsNotNone(ramdisk_image)
            self.assertIsNotNone(image_creator.get_ramdisk_image())
            self.assertEqual(ramdisk_image.id,
                             image_creator.get_ramdisk_image().id)
        else:
            logger.warn(
                'Test not executed as the image metadata requires image files')

    def test_create_three_part_image_from_file_3_creators(self):
        """
        Tests the creation of a 3-part OpenStack image from files.
        """
        file_only = False

        # Set properties
        properties = {}
        if self.glance_test_meta:
            if 'extra_properties' in self.glance_test_meta:
                properties = self.glance_test_meta['extra_properties']
            if 'disk_file' in self.glance_test_meta:
                file_only = True

        # Create the kernel image
        kernel_file_name = None
        kernel_url = openstack_tests.CIRROS_DEFAULT_KERNEL_IMAGE_URL
        if 'kernel_file' in self.glance_test_meta:
            kernel_file_name = self.glance_test_meta['kernel_file']
        elif 'kernel_url' in self.glance_test_meta:
            kernel_url = self.glance_test_meta['kernel_url']
        else:
            kernel_url = openstack_tests.CIRROS_DEFAULT_KERNEL_IMAGE_URL

        if not kernel_file_name and not file_only:
            kernel_file_name = file_utils.download(kernel_url,
                                                   self.tmp_dir).name
        else:
            logger.warn('Will not download the kernel image.'
                        ' Cannot execute test')
            return

        kernel_file_image_settings = openstack_tests.file_image_test_settings(
            name=self.image_name + '_kernel', file_path=kernel_file_name)

        self.image_creators.append(create_image.OpenStackImage(
            self.os_creds, kernel_file_image_settings))
        kernel_image = self.image_creators[-1].create()
        self.assertIsNotNone(kernel_image)
        self.assertEqual(get_image_size(kernel_file_image_settings),
                         kernel_image.size)

        # Create the ramdisk image
        ramdisk_file_name = None
        ramdisk_url = openstack_tests.CIRROS_DEFAULT_RAMDISK_IMAGE_URL
        if 'ramdisk_file' in self.glance_test_meta:
            ramdisk_file_name = self.glance_test_meta['ramdisk_file']
        elif 'ramdisk_url' in self.glance_test_meta:
            ramdisk_url = self.glance_test_meta['ramdisk_url']

        if not ramdisk_file_name and not file_only:
            ramdisk_file_name = file_utils.download(ramdisk_url,
                                                    self.tmp_dir).name
        else:
            logger.warn('Will not download the ramdisk image.'
                        ' Cannot execute test')
            return

        ramdisk_file_image_settings = openstack_tests.file_image_test_settings(
            name=self.image_name + '_ramdisk', file_path=ramdisk_file_name)
        self.image_creators.append(create_image.OpenStackImage(
            self.os_creds, ramdisk_file_image_settings))
        ramdisk_image = self.image_creators[-1].create()
        self.assertIsNotNone(ramdisk_image)
        self.assertEqual(get_image_size(ramdisk_file_image_settings),
                         ramdisk_image.size)

        # Create the main disk image
        disk_file_name = None
        disk_url = openstack_tests.CIRROS_DEFAULT_IMAGE_URL
        if 'disk_file' in self.glance_test_meta:
            disk_file_name = self.glance_test_meta['disk_file']
        elif 'disk_url' in self.glance_test_meta:
            disk_url = self.glance_test_meta['disk_url']

        if not disk_file_name and not file_only:
            disk_file_name = file_utils.download(disk_url, self.tmp_dir).name
        else:
            logger.warn('Will not download the disk file image.'
                        ' Cannot execute test')
            return

        file_image_settings = openstack_tests.file_image_test_settings(
            name=self.image_name, file_path=disk_file_name)
        properties['kernel_id'] = kernel_image.id
        properties['ramdisk_id'] = ramdisk_image.id
        file_image_settings.extra_properties = properties
        self.image_creators.append(
            create_image.OpenStackImage(self.os_creds, file_image_settings))
        created_image = self.image_creators[-1].create()

        self.assertIsNotNone(created_image)
        self.assertEqual(self.image_name, created_image.name)

        retrieved_image = glance_utils.get_image(
            self.glance, image_settings=file_image_settings)
        self.assertIsNotNone(retrieved_image)
        self.assertEqual(self.image_creators[-1].get_image().size,
                         retrieved_image.size)
        self.assertEqual(get_image_size(file_image_settings),
                         retrieved_image.size)
        self.assertEqual(created_image.name, retrieved_image.name)
        self.assertEqual(created_image.id, retrieved_image.id)
        self.assertEqual(created_image.properties, retrieved_image.properties)

    def test_create_three_part_image_from_url_3_creators(self):
        """
        Tests the creation of a 3-part OpenStack image from a URL.
        """
        if 'disk_file' not in self.glance_test_meta:
            # Set properties
            properties = {}
            if self.glance_test_meta and \
                    'extra_properties' in self.glance_test_meta:
                properties = self.glance_test_meta['extra_properties']

            # Create the kernel image
            kernel_image_settings = openstack_tests.cirros_image_settings(
                name=self.image_name + '_kernel',
                url=openstack_tests.CIRROS_DEFAULT_KERNEL_IMAGE_URL)

            if self.glance_test_meta:
                if 'kernel_url' in self.glance_test_meta:
                    kernel_image_settings.url = self.glance_test_meta[
                        'kernel_url']
            self.image_creators.append(
                create_image.OpenStackImage(self.os_creds,
                                            kernel_image_settings))
            kernel_image = self.image_creators[-1].create()
            self.assertIsNotNone(kernel_image)
            self.assertEqual(get_image_size(kernel_image_settings),
                             kernel_image.size)

            # Create the ramdisk image
            ramdisk_image_settings = openstack_tests.cirros_image_settings(
                name=self.image_name + '_ramdisk',
                url=openstack_tests.CIRROS_DEFAULT_RAMDISK_IMAGE_URL)
            if self.glance_test_meta:
                if 'ramdisk_url' in self.glance_test_meta:
                    ramdisk_image_settings.url = self.glance_test_meta[
                        'ramdisk_url']
            self.image_creators.append(
                create_image.OpenStackImage(self.os_creds,
                                            ramdisk_image_settings))
            ramdisk_image = self.image_creators[-1].create()
            self.assertIsNotNone(ramdisk_image)
            self.assertEqual(get_image_size(ramdisk_image_settings),
                             ramdisk_image.size)

            # Create the main image
            os_image_settings = openstack_tests.cirros_image_settings(
                name=self.image_name,
                url=openstack_tests.CIRROS_DEFAULT_IMAGE_URL)
            if self.glance_test_meta:
                if 'disk_url' in self.glance_test_meta:
                    os_image_settings.url = self.glance_test_meta['disk_url']

            properties['kernel_id'] = kernel_image.id
            properties['ramdisk_id'] = ramdisk_image.id
            os_image_settings.extra_properties = properties

            self.image_creators.append(
                create_image.OpenStackImage(self.os_creds, os_image_settings))
            created_image = self.image_creators[-1].create()
            self.assertIsNotNone(created_image)
            self.assertEqual(self.image_name, created_image.name)

            retrieved_image = glance_utils.get_image(
                self.glance, image_settings=os_image_settings)
            self.assertIsNotNone(retrieved_image)

            self.assertEqual(self.image_creators[-1].get_image().size,
                             retrieved_image.size)
            self.assertEqual(get_image_size(os_image_settings),
                             retrieved_image.size)

            self.assertEqual(created_image.name, retrieved_image.name)
            self.assertEqual(created_image.id, retrieved_image.id)
            self.assertEqual(created_image.properties,
                             retrieved_image.properties)
        else:
            logger.warn(
                'Test not executed as the image metadata requires image files')


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
        raise Exception(
            'Cannot retrieve expected image size. Image filename or URL has '
            'not been configured')
