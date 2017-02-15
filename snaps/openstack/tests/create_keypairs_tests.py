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
import uuid
import unittest

from Crypto.PublicKey import RSA

from snaps.openstack.create_keypairs import KeypairSettings, OpenStackKeypair
from snaps.openstack.utils import nova_utils
from snaps.openstack.tests.os_source_file_test import OSIntegrationTestCase

__author__ = 'spisarski'


class KeypairSettingsUnitTests(unittest.TestCase):
    """
    Tests the construction of the KeypairSettings class
    """

    def test_no_params(self):
        with self.assertRaises(Exception):
            KeypairSettings()

    def test_empty_config(self):
        with self.assertRaises(Exception):
            KeypairSettings(config=dict())

    def test_name_only(self):
        settings = KeypairSettings(name='foo')
        self.assertEquals('foo', settings.name)
        self.assertIsNone(settings.public_filepath)
        self.assertIsNone(settings.private_filepath)

    def test_config_with_name_only(self):
        settings = KeypairSettings(config={'name': 'foo'})
        self.assertEquals('foo', settings.name)
        self.assertIsNone(settings.public_filepath)
        self.assertIsNone(settings.private_filepath)

    def test_name_pub_only(self):
        settings = KeypairSettings(name='foo', public_filepath='/foo/bar.pub')
        self.assertEquals('foo', settings.name)
        self.assertEquals('/foo/bar.pub', settings.public_filepath)
        self.assertIsNone(settings.private_filepath)

    def test_config_with_name_pub_only(self):
        settings = KeypairSettings(config={'name': 'foo', 'public_filepath': '/foo/bar.pub'})
        self.assertEquals('foo', settings.name)
        self.assertEquals('/foo/bar.pub', settings.public_filepath)
        self.assertIsNone(settings.private_filepath)

    def test_name_priv_only(self):
        settings = KeypairSettings(name='foo', private_filepath='/foo/bar')
        self.assertEquals('foo', settings.name)
        self.assertIsNone(settings.public_filepath)
        self.assertEquals('/foo/bar', settings.private_filepath)

    def test_config_with_name_priv_only(self):
        settings = KeypairSettings(config={'name': 'foo', 'private_filepath': '/foo/bar'})
        self.assertEquals('foo', settings.name)
        self.assertIsNone(settings.public_filepath)
        self.assertEquals('/foo/bar', settings.private_filepath)

    def test_all(self):
        settings = KeypairSettings(name='foo', public_filepath='/foo/bar.pub', private_filepath='/foo/bar')
        self.assertEquals('foo', settings.name)
        self.assertEquals('/foo/bar.pub', settings.public_filepath)
        self.assertEquals('/foo/bar', settings.private_filepath)

    def test_config_all(self):
        settings = KeypairSettings(config={'name': 'foo', 'public_filepath': '/foo/bar.pub',
                                           'private_filepath': '/foo/bar'})
        self.assertEquals('foo', settings.name)
        self.assertEquals('/foo/bar.pub', settings.public_filepath)
        self.assertEquals('/foo/bar', settings.private_filepath)


class CreateKeypairsTests(OSIntegrationTestCase):
    """
    Tests for the OpenStackKeypair class
    """

    def setUp(self):
        super(self.__class__, self).__start__()

        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.priv_file_path = 'tmp/' + guid
        self.pub_file_path = self.priv_file_path + '.pub'
        self.nova = nova_utils.nova_client(self.os_creds)
        self.keypair_name = guid

        self.keypair_creator = None

    def tearDown(self):
        """
        Cleanup of created keypair
        """
        if self.keypair_creator:
            self.keypair_creator.clean()

        try:
            os.remove(self.pub_file_path)
        except:
            pass

        try:
            os.remove(self.priv_file_path)
        except:
            pass

        super(self.__class__, self).__clean__()

    def test_create_keypair_only(self):
        """
        Tests the creation of a generated keypair without saving to file
        :return:
        """
        self.keypair_creator = OpenStackKeypair(self.os_creds, KeypairSettings(name=self.keypair_name))
        self.keypair_creator.create()

        keypair = nova_utils.keypair_exists(self.nova, self.keypair_creator.get_keypair())
        self.assertEquals(self.keypair_creator.get_keypair(), keypair)

    def test_create_delete_keypair(self):
        """
        Tests the creation then deletion of an OpenStack keypair to ensure clean() does not raise an Exception.
        """
        # Create Image
        self.keypair_creator = OpenStackKeypair(self.os_creds, KeypairSettings(name=self.keypair_name))
        created_keypair = self.keypair_creator.create()
        self.assertIsNotNone(created_keypair)

        # Delete Image manually
        nova_utils.delete_keypair(self.nova, created_keypair)

        self.assertIsNone(nova_utils.get_keypair_by_name(self.nova, self.keypair_name))

        # Must not throw an exception when attempting to cleanup non-existent image
        self.keypair_creator.clean()
        self.assertIsNone(self.keypair_creator.get_keypair())

    def test_create_keypair_save_pub_only(self):
        """
        Tests the creation of a generated keypair and saves the public key only
        :return:
        """
        self.keypair_creator = OpenStackKeypair(
            self.os_creds, KeypairSettings(name=self.keypair_name, public_filepath=self.pub_file_path))
        self.keypair_creator.create()

        keypair = nova_utils.keypair_exists(self.nova, self.keypair_creator.get_keypair())
        self.assertEquals(self.keypair_creator.get_keypair(), keypair)

        file_key = open(os.path.expanduser(self.pub_file_path)).read()
        self.assertEquals(self.keypair_creator.get_keypair().public_key, file_key)

    def test_create_keypair_save_both(self):
        """
        Tests the creation of a generated keypair and saves both private and public key files[
        :return:
        """
        self.keypair_creator = OpenStackKeypair(
            self.os_creds, KeypairSettings(name=self.keypair_name, public_filepath=self.pub_file_path,
                                           private_filepath=self.priv_file_path))
        self.keypair_creator.create()

        keypair = nova_utils.keypair_exists(self.nova, self.keypair_creator.get_keypair())
        self.assertEquals(self.keypair_creator.get_keypair(), keypair)

        file_key = open(os.path.expanduser(self.pub_file_path)).read()
        self.assertEquals(self.keypair_creator.get_keypair().public_key, file_key)

        self.assertTrue(os.path.isfile(self.priv_file_path))

    def test_create_keypair_from_file(self):
        """
        Tests the creation of an existing public keypair from a file
        :return:
        """
        keys = RSA.generate(1024)
        nova_utils.save_keys_to_files(keys=keys, pub_file_path=self.pub_file_path)
        self.keypair_creator = OpenStackKeypair(
            self.os_creds, KeypairSettings(name=self.keypair_name, public_filepath=self.pub_file_path))
        self.keypair_creator.create()

        keypair = nova_utils.keypair_exists(self.nova, self.keypair_creator.get_keypair())
        self.assertEquals(self.keypair_creator.get_keypair(), keypair)

        file_key = open(os.path.expanduser(self.pub_file_path)).read()
        self.assertEquals(self.keypair_creator.get_keypair().public_key, file_key)
