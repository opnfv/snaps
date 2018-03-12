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
import pkg_resources
import unittest
import shutil
import uuid

from snaps import file_utils
from snaps.openstack.tests import openstack_tests

__author__ = 'spisarski'


class FileUtilsTests(unittest.TestCase):
    """
    Tests the methods in file_utils.py
    """

    def setUp(self):
        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.tmp_dir = 'tmp/'
        self.test_dir = self.tmp_dir + str(guid)
        if not os.path.exists(self.test_dir):
            os.makedirs(self.test_dir)

        self.tmpFile = self.test_dir + '/bar.txt'
        self.tmp_file_opened = None

    def tearDown(self):
        if self.tmp_file_opened:
            self.tmp_file_opened.close()

        if os.path.exists(self.test_dir) and os.path.isdir(self.test_dir):
            shutil.rmtree(self.test_dir)

    def testFileIsDirectory(self):
        """
        Ensure the file_utils.fileExists() method returns false with a
        directory
        """
        result = file_utils.file_exists(self.test_dir)
        self.assertFalse(result)

    def testFileNotExist(self):
        """
        Ensure the file_utils.fileExists() method returns false with a bogus
        file
        """
        result = file_utils.file_exists('/foo/bar.txt')
        self.assertFalse(result)

    def testFileExists(self):
        """
        Ensure the file_utils.fileExists() method returns false with a
        directory
        """
        if not os.path.exists(self.tmpFile):
            self.tmp_file_opened = open(self.tmpFile, 'wb')

        if not os.path.exists(self.tmpFile):
            os.makedirs(self.tmpFile)

        result = file_utils.file_exists(self.tmpFile)
        self.assertTrue(result)

    def testDownloadBadUrl(self):
        """
        Tests the file_utils.download() method when given a bad URL
        """
        with self.assertRaises(Exception):
            file_utils.download('http://bunkUrl.com/foo/bar.iso',
                                self.test_dir)

    def testDownloadBadDir(self):
        """
        Tests the file_utils.download() method when given a bad URL
        """
        with self.assertRaises(Exception):
            file_utils.download(openstack_tests.CIRROS_DEFAULT_IMAGE_URL,
                                '/foo/bar')

    def testCirrosImageDownload(self):
        """
        Tests the file_utils.download() method when given a good Cirros QCOW2
        URL
        """
        image_file = file_utils.download(
            openstack_tests.CIRROS_DEFAULT_IMAGE_URL, self.test_dir)
        self.assertIsNotNone(image_file)
        self.assertTrue(
            image_file.name.endswith("cirros-0.3.4-x86_64-disk.img"))
        self.assertTrue(image_file.name.startswith(self.test_dir))

    def testReadOSEnvFile(self):
        """
        Tests that the OS Environment file is correctly parsed
        :return:
        """
        rc_file_path = pkg_resources.resource_filename(
            'snaps.openstack.tests.conf', 'overcloudrc_test')
        os_env_dict = file_utils.read_os_env_file(rc_file_path)
        self.assertEqual('test_pw', os_env_dict['OS_PASSWORD'])
        self.assertEqual('http://foo:5000/v2.0/', os_env_dict['OS_AUTH_URL'])
        self.assertEqual('admin', os_env_dict['OS_USERNAME'])
        self.assertEqual('admin', os_env_dict['OS_TENANT_NAME'])

    def test_write_str_to_file(self):
        """
        Ensure the file_utils.fileExists() method returns false with a
        directory
        """
        test_val = 'test string'

        test_file = file_utils.save_string_to_file(
            test_val, self.tmpFile)
        result1 = file_utils.file_exists(self.tmpFile)
        self.assertTrue(result1)
        result2 = file_utils.file_exists(test_file.name)
        self.assertTrue(result2)

        file_contents = file_utils.read_file(self.tmpFile)
        self.assertEqual(test_val, file_contents)
