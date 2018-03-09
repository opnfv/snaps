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
import os
import shutil
import uuid

from snaps import file_utils
from snaps.openstack.tests import openstack_tests

from snaps.openstack.tests import validation_utils
from snaps.openstack.tests.os_source_file_test import OSComponentTestCase
from snaps.openstack.utils import glance_utils

__author__ = 'spisarski'


logger = logging.getLogger('glance_utils_tests')


class GlanceSmokeTests(OSComponentTestCase):
    """
    Tests to ensure that the neutron client can communicate with the cloud
    """

    def test_glance_connect_success(self):
        """
        Tests to ensure that the proper credentials can connect.
        """
        glance = glance_utils.glance_client(self.os_creds, self.os_session)
        image = glance_utils.get_image(glance, image_name='foo')
        self.assertIsNone(image)

    def test_glance_connect_fail(self):
        """
        Tests to ensure that the improper credentials cannot connect.
        """
        from snaps.openstack.os_credentials import OSCreds

        with self.assertRaises(Exception):
            glance = glance_utils.glance_client(OSCreds(
                username='user', password='pass', auth_url='url',
                project_name='project'))
            glance_utils.get_image(glance, image_name='foo')


class GlanceUtilsTests(OSComponentTestCase):
    """
    Test for the CreateImage class defined in create_image.py
    """

    def setUp(self):
        """
        Instantiates the CreateImage object that is responsible for downloading
        and creating an OS image file within OpenStack
        """
        guid = uuid.uuid4()
        self.image_name = self.__class__.__name__ + '-' + str(guid)
        self.image = None
        self.glance = glance_utils.glance_client(
            self.os_creds, self.os_session)
        if self.image_metadata:
            self.glance_test_meta = self.image_metadata.get('glance_tests')
        else:
            self.glance_test_meta = dict()

        self.tmp_dir = 'tmp/' + str(guid)
        if not os.path.exists(self.tmp_dir):
            os.makedirs(self.tmp_dir)

    def tearDown(self):
        """
        Cleans the remote OpenStack objects
        """
        if self.image:
            glance_utils.delete_image(self.glance, self.image)

        if os.path.exists(self.tmp_dir) and os.path.isdir(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)

        super(self.__class__, self).__clean__()

    def test_create_image_minimal_url(self):
        """
        Tests the glance_utils.create_image() function with a URL unless the
        self.glance_test_meta has configured a file to be used.
        """
        if 'disk_file' not in self.glance_test_meta:
            os_image_settings = openstack_tests.cirros_image_settings(
                name=self.image_name, image_metadata=self.glance_test_meta)

            self.image = glance_utils.create_image(self.glance,
                                                   os_image_settings)
            self.assertIsNotNone(self.image)

            self.assertEqual(self.image_name, self.image.name)

            image = glance_utils.get_image(self.glance,
                                           image_settings=os_image_settings)
            self.assertIsNotNone(image)

            validation_utils.objects_equivalent(self.image, image)
        else:
            logger.warn('Test not executed as the image metadata requires '
                        'image files')

    def test_create_image_minimal_file(self):
        """
        Tests the glance_utils.create_image() function with a file
        """
        if 'disk_file' not in self.glance_test_meta:
            url_image_settings = openstack_tests.cirros_image_settings(
                name='foo', image_metadata=self.glance_test_meta)
            image_file_name = file_utils.download(
                url_image_settings.url, self.tmp_dir).name
        else:
            image_file_name = self.glance_test_meta['disk_file']

        file_image_settings = openstack_tests.file_image_test_settings(
            name=self.image_name, file_path=image_file_name)

        self.image = glance_utils.create_image(self.glance,
                                               file_image_settings)
        self.assertIsNotNone(self.image)
        self.assertEqual(self.image_name, self.image.name)

        image = glance_utils.get_image(
            self.glance, image_settings=file_image_settings)
        self.assertIsNotNone(image)
        validation_utils.objects_equivalent(self.image, image)
