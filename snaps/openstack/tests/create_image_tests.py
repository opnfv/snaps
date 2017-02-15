# Copyright (c) 2016 Cable Television Laboratories, Inc. ("CableLabs")
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
from snaps.openstack.utils import glance_utils, nova_utils
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
        settings = ImageSettings(name='foo', image_user='bar', img_format='qcow2', url='http://foo.com',
                                 nic_config_pb_loc='/foo/bar')
        self.assertEquals('foo', settings.name)
        self.assertEquals('bar', settings.image_user)
        self.assertEquals('qcow2', settings.format)
        self.assertEquals('http://foo.com', settings.url)
        self.assertIsNone(settings.image_file)
        self.assertEquals('/foo/bar', settings.nic_config_pb_loc)

    def test_config_all_url(self):
        settings = ImageSettings(config={'name': 'foo', 'image_user': 'bar', 'format': 'qcow2',
                                         'download_url': 'http://foo.com', 'nic_config_pb_loc': '/foo/bar'})
        self.assertEquals('foo', settings.name)
        self.assertEquals('bar', settings.image_user)
        self.assertEquals('qcow2', settings.format)
        self.assertEquals('http://foo.com', settings.url)
        self.assertIsNone(settings.image_file)
        self.assertEquals('/foo/bar', settings.nic_config_pb_loc)

    def test_all_file(self):
        settings = ImageSettings(name='foo', image_user='bar', img_format='qcow2', image_file='/foo/bar.qcow',
                                 nic_config_pb_loc='/foo/bar')
        self.assertEquals('foo', settings.name)
        self.assertEquals('bar', settings.image_user)
        self.assertEquals('qcow2', settings.format)
        self.assertIsNone(settings.url)
        self.assertEquals('/foo/bar.qcow', settings.image_file)
        self.assertEquals('/foo/bar', settings.nic_config_pb_loc)

    def test_config_all_file(self):
        settings = ImageSettings(config={'name': 'foo', 'image_user': 'bar', 'format': 'qcow2',
                                         'image_file': '/foo/bar.qcow', 'nic_config_pb_loc': '/foo/bar'})
        self.assertEquals('foo', settings.name)
        self.assertEquals('bar', settings.image_user)
        self.assertEquals('qcow2', settings.format)
        self.assertIsNone(settings.url)
        self.assertEquals('/foo/bar.qcow', settings.image_file)
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

        self.nova = nova_utils.nova_client(self.os_creds)
        self.glance = glance_utils.glance_client(self.os_creds)

        self.tmp_dir = 'tmp/' + str(guid)
        if not os.path.exists(self.tmp_dir):
            os.makedirs(self.tmp_dir)

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
        os_image_settings = openstack_tests.cirros_url_image(name=self.image_name)
        self.image_creator = create_image.OpenStackImage(self.os_creds, os_image_settings)

        created_image = self.image_creator.create()
        self.assertIsNotNone(created_image)

        retrieved_image = glance_utils.get_image(self.nova, self.glance, os_image_settings.name)
        self.assertIsNotNone(retrieved_image)

        self.assertEquals(created_image.name, retrieved_image.name)
        self.assertEquals(created_image.id, retrieved_image.id)

    def test_create_image_clean_file(self):
        """
        Tests the creation of an OpenStack image from a file.
        """
        url_image_settings = openstack_tests.cirros_url_image('foo')
        image_file = file_utils.download(url_image_settings.url, self.tmp_dir)
        file_image_settings = openstack_tests.file_image_test_settings(name=self.image_name, file_path=image_file.name)
        self.image_creator = create_image.OpenStackImage(self.os_creds, file_image_settings)

        self.image = self.image_creator.create()
        self.assertIsNotNone(self.image)
        self.assertEqual(self.image_name, self.image.name)

        created_image = self.image_creator.create()
        self.assertIsNotNone(created_image)

        retrieved_image = glance_utils.get_image(self.nova, self.glance, file_image_settings.name)
        self.assertIsNotNone(retrieved_image)

        self.assertEquals(created_image.name, retrieved_image.name)
        self.assertEquals(created_image.id, retrieved_image.id)

    def test_create_delete_image(self):
        """
        Tests the creation then deletion of an OpenStack image to ensure clean() does not raise an Exception.
        """
        # Create Image
        os_image_settings = openstack_tests.cirros_url_image(name=self.image_name)
        self.image_creator = create_image.OpenStackImage(self.os_creds, os_image_settings)
        created_image = self.image_creator.create()
        self.assertIsNotNone(created_image)

        # Delete Image manually
        glance_utils.delete_image(self.glance, created_image)

        self.assertIsNone(glance_utils.get_image(self.nova, self.glance, self.image_creator.image_settings.name))

        # Must not throw an exception when attempting to cleanup non-existent image
        self.image_creator.clean()
        self.assertIsNone(self.image_creator.get_image())

    def test_create_same_image(self):
        """
        Tests the creation of an OpenStack image when the image already exists.
        """
        # Create Image
        os_image_settings = openstack_tests.cirros_url_image(name=self.image_name)
        self.image_creator = create_image.OpenStackImage(self.os_creds, os_image_settings)
        image1 = self.image_creator.create()
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
