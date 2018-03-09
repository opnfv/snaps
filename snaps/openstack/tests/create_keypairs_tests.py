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
import uuid

import os

from snaps import file_utils
from snaps.config.keypair import KeypairConfig, KeypairConfigError
from snaps.openstack.create_keypairs import (
    KeypairSettings, OpenStackKeypair)
from snaps.openstack.tests.os_source_file_test import OSIntegrationTestCase
from snaps.openstack.utils import nova_utils

__author__ = 'spisarski'


class KeypairSettingsUnitTests(unittest.TestCase):
    """
    Tests the construction of the KeypairSettings class
    """

    def test_no_params(self):
        with self.assertRaises(KeypairConfigError):
            KeypairSettings()

    def test_empty_config(self):
        with self.assertRaises(KeypairConfigError):
            KeypairSettings(**dict())

    def test_small_key_size(self):
        with self.assertRaises(KeypairConfigError):
            KeypairSettings(name='foo', key_size=511)

    def test_name_only(self):
        settings = KeypairSettings(name='foo')
        self.assertEqual('foo', settings.name)
        self.assertEqual(1024, settings.key_size)
        self.assertIsNone(settings.public_filepath)
        self.assertIsNone(settings.private_filepath)
        self.assertIsNone(settings.delete_on_clean)

    def test_config_with_name_only(self):
        settings = KeypairSettings(**{'name': 'foo'})
        self.assertEqual('foo', settings.name)
        self.assertEqual(1024, settings.key_size)
        self.assertIsNone(settings.public_filepath)
        self.assertIsNone(settings.private_filepath)
        self.assertIsNone(settings.delete_on_clean)

    def test_name_pub_only(self):
        settings = KeypairSettings(name='foo', public_filepath='/foo/bar.pub')
        self.assertEqual('foo', settings.name)
        self.assertEqual(1024, settings.key_size)
        self.assertEqual('/foo/bar.pub', settings.public_filepath)
        self.assertIsNone(settings.private_filepath)
        self.assertIsNone(settings.delete_on_clean)

    def test_config_with_name_pub_only(self):
        settings = KeypairSettings(
            **{'name': 'foo', 'public_filepath': '/foo/bar.pub'})
        self.assertEqual('foo', settings.name)
        self.assertEqual(1024, settings.key_size)
        self.assertEqual('/foo/bar.pub', settings.public_filepath)
        self.assertIsNone(settings.private_filepath)
        self.assertIsNone(settings.delete_on_clean)

    def test_name_priv_only(self):
        settings = KeypairSettings(name='foo', private_filepath='/foo/bar')
        self.assertEqual('foo', settings.name)
        self.assertEqual(1024, settings.key_size)
        self.assertIsNone(settings.public_filepath)
        self.assertEqual('/foo/bar', settings.private_filepath)
        self.assertIsNone(settings.delete_on_clean)

    def test_config_with_name_priv_only(self):
        settings = KeypairSettings(
            **{'name': 'foo', 'private_filepath': '/foo/bar'})
        self.assertEqual('foo', settings.name)
        self.assertEqual(1024, settings.key_size)
        self.assertIsNone(settings.public_filepath)
        self.assertEqual('/foo/bar', settings.private_filepath)
        self.assertIsNone(settings.delete_on_clean)

    def test_all_delete_bool(self):
        settings = KeypairSettings(
            name='foo', public_filepath='/foo/bar.pub',
            private_filepath='/foo/bar', delete_on_clean=True,
            key_size=999)
        self.assertEqual('foo', settings.name)
        self.assertEqual(999, settings.key_size)
        self.assertEqual('/foo/bar.pub', settings.public_filepath)
        self.assertEqual('/foo/bar', settings.private_filepath)
        self.assertTrue(settings.delete_on_clean)

    def test_all_delete_str_true_cap(self):
        settings = KeypairSettings(
            name='foo', public_filepath='/foo/bar.pub',
            private_filepath='/foo/bar', delete_on_clean='True')
        self.assertEqual('foo', settings.name)
        self.assertEqual(1024, settings.key_size)
        self.assertEqual('/foo/bar.pub', settings.public_filepath)
        self.assertEqual('/foo/bar', settings.private_filepath)
        self.assertTrue(settings.delete_on_clean)

    def test_all_delete_str_true_lc(self):
        settings = KeypairSettings(
            name='foo', public_filepath='/foo/bar.pub',
            private_filepath='/foo/bar', delete_on_clean='true')
        self.assertEqual('foo', settings.name)
        self.assertEqual(1024, settings.key_size)
        self.assertEqual('/foo/bar.pub', settings.public_filepath)
        self.assertEqual('/foo/bar', settings.private_filepath)
        self.assertTrue(settings.delete_on_clean)

    def test_all_delete_str_false_cap(self):
        settings = KeypairSettings(
            name='foo', public_filepath='/foo/bar.pub',
            private_filepath='/foo/bar', delete_on_clean='False')
        self.assertEqual('foo', settings.name)
        self.assertEqual(1024, settings.key_size)
        self.assertEqual('/foo/bar.pub', settings.public_filepath)
        self.assertEqual('/foo/bar', settings.private_filepath)
        self.assertFalse(settings.delete_on_clean)

    def test_all_delete_str_false_lc(self):
        settings = KeypairSettings(
            name='foo', public_filepath='/foo/bar.pub',
            private_filepath='/foo/bar', delete_on_clean='false',
            key_size='999')
        self.assertEqual('foo', settings.name)
        self.assertEqual(999, settings.key_size)
        self.assertEqual('/foo/bar.pub', settings.public_filepath)
        self.assertEqual('/foo/bar', settings.private_filepath)
        self.assertFalse(settings.delete_on_clean)

    def test_config_all_delete_false_bool(self):
        settings = KeypairSettings(
            **{'name': 'foo', 'public_filepath': '/foo/bar.pub',
               'private_filepath': '/foo/bar', 'delete_on_clean': False,
               'key_size': 999})
        self.assertEqual('foo', settings.name)
        self.assertEqual(999, settings.key_size)
        self.assertEqual('/foo/bar.pub', settings.public_filepath)
        self.assertEqual('/foo/bar', settings.private_filepath)
        self.assertFalse(settings.delete_on_clean)

    def test_config_all_delete_false_str_cap(self):
        settings = KeypairSettings(
            **{'name': 'foo', 'public_filepath': '/foo/bar.pub',
               'private_filepath': '/foo/bar', 'delete_on_clean': 'False'})
        self.assertEqual('foo', settings.name)
        self.assertEqual(1024, settings.key_size)
        self.assertEqual('/foo/bar.pub', settings.public_filepath)
        self.assertEqual('/foo/bar', settings.private_filepath)
        self.assertFalse(settings.delete_on_clean)

    def test_config_all_delete_false_str_lc(self):
        settings = KeypairSettings(
            **{'name': 'foo', 'public_filepath': '/foo/bar.pub',
               'private_filepath': '/foo/bar', 'delete_on_clean': 'false'})
        self.assertEqual('foo', settings.name)
        self.assertEqual(1024, settings.key_size)
        self.assertEqual('/foo/bar.pub', settings.public_filepath)
        self.assertEqual('/foo/bar', settings.private_filepath)
        self.assertFalse(settings.delete_on_clean)

    def test_config_all_delete_false_str_foo(self):
        settings = KeypairSettings(
            **{'name': 'foo', 'public_filepath': '/foo/bar.pub',
               'private_filepath': '/foo/bar', 'delete_on_clean': 'foo',
               'key_size': '999'})
        self.assertEqual('foo', settings.name)
        self.assertEqual(999, settings.key_size)
        self.assertEqual('/foo/bar.pub', settings.public_filepath)
        self.assertEqual('/foo/bar', settings.private_filepath)
        self.assertFalse(settings.delete_on_clean)


class CreateKeypairsTests(OSIntegrationTestCase):
    """
    Tests for the OpenStackKeypair class
    """

    def setUp(self):
        super(self.__class__, self).__start__()

        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.priv_file_path = 'tmp/' + guid
        self.pub_file_path = self.priv_file_path + '.pub'
        self.nova = nova_utils.nova_client(self.os_creds, self.os_session)
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
        self.keypair_creator = OpenStackKeypair(self.os_creds, KeypairConfig(
            name=self.keypair_name))
        self.keypair_creator.create()

        keypair = nova_utils.keypair_exists(self.nova,
                                            self.keypair_creator.get_keypair())
        self.assertEqual(self.keypair_creator.get_keypair(), keypair)

    def test_create_keypair_large_key(self):
        """
        Tests the creation of a generated keypair without saving to file
        :return:
        """
        self.keypair_creator = OpenStackKeypair(self.os_creds, KeypairConfig(
            name=self.keypair_name, key_size=10000))
        self.keypair_creator.create()

        keypair = nova_utils.keypair_exists(self.nova,
                                            self.keypair_creator.get_keypair())
        self.assertEqual(self.keypair_creator.get_keypair(), keypair)

    def test_create_delete_keypair(self):
        """
        Tests the creation then deletion of an OpenStack keypair to ensure
        clean() does not raise an Exception.
        """
        # Create Image
        self.keypair_creator = OpenStackKeypair(self.os_creds, KeypairConfig(
            name=self.keypair_name))
        created_keypair = self.keypair_creator.create()
        self.assertIsNotNone(created_keypair)

        # Delete Image manually
        nova_utils.delete_keypair(self.nova, created_keypair)

        self.assertIsNone(
            nova_utils.get_keypair_by_name(self.nova, self.keypair_name))

        # Must not throw an exception when attempting to cleanup non-existent
        # image
        self.keypair_creator.clean()
        self.assertIsNone(self.keypair_creator.get_keypair())

    def test_create_keypair_save_pub_only(self):
        """
        Tests the creation of a generated keypair and saves the public key only
        :return:
        """
        self.keypair_creator = OpenStackKeypair(
            self.os_creds, KeypairConfig(
                name=self.keypair_name, public_filepath=self.pub_file_path))
        self.keypair_creator.create()

        keypair = nova_utils.keypair_exists(self.nova,
                                            self.keypair_creator.get_keypair())
        self.assertEqual(self.keypair_creator.get_keypair(), keypair)

        pub_file = None
        try:
            pub_file = open(os.path.expanduser(self.pub_file_path))
            file_key = pub_file.read()
            self.assertEqual(self.keypair_creator.get_keypair().public_key,
                             file_key)
        finally:
            if pub_file:
                pub_file.close()

    def test_create_keypair_save_both(self):
        """
        Tests the creation of a generated keypair and saves both private and
        public key files[
        :return:
        """
        self.keypair_creator = OpenStackKeypair(
            self.os_creds, KeypairConfig(
                name=self.keypair_name, public_filepath=self.pub_file_path,
                private_filepath=self.priv_file_path))
        self.keypair_creator.create()

        keypair = nova_utils.keypair_exists(self.nova,
                                            self.keypair_creator.get_keypair())
        self.assertEqual(self.keypair_creator.get_keypair(), keypair)

        pub_file = None
        try:
            pub_file = open(os.path.expanduser(self.pub_file_path))
            file_key = pub_file.read()
            self.assertEqual(self.keypair_creator.get_keypair().public_key,
                             file_key)
        finally:
            if pub_file:
                pub_file.close()

        self.assertEqual(self.keypair_creator.get_keypair().public_key,
                         file_key)

        self.assertTrue(os.path.isfile(self.priv_file_path))

    def test_create_keypair_from_file(self):
        """
        Tests the creation of an existing public keypair from a file
        :return:
        """
        keys = nova_utils.create_keys()
        file_utils.save_keys_to_files(keys=keys,
                                      pub_file_path=self.pub_file_path)
        self.keypair_creator = OpenStackKeypair(
            self.os_creds, KeypairConfig(
                name=self.keypair_name, public_filepath=self.pub_file_path))
        self.keypair_creator.create()

        keypair = nova_utils.keypair_exists(self.nova,
                                            self.keypair_creator.get_keypair())
        self.assertEqual(self.keypair_creator.get_keypair(), keypair)

        pub_file = None
        try:
            pub_file = open(os.path.expanduser(self.pub_file_path))
            file_key = pub_file.read()
            self.assertEqual(self.keypair_creator.get_keypair().public_key,
                             file_key)
        finally:
            if pub_file:
                pub_file.close()

        self.assertEqual(self.keypair_creator.get_keypair().public_key,
                         file_key)


class CreateKeypairsCleanupTests(OSIntegrationTestCase):
    """
    Tests for the OpenStackKeypair#clean method to ensure key files are deleted
    when required
    """

    def setUp(self):
        super(self.__class__, self).__start__()

        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.priv_file_path = 'tmp/' + guid
        self.pub_file_path = self.priv_file_path + '.pub'
        self.nova = nova_utils.nova_client(self.os_creds, self.os_session)
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

    def test_create_keypair_gen_files_delete_1(self):
        """
        Tests the creation of a generated keypair and ensures that the files
        are deleted on clean()
        :return:
        """
        self.keypair_creator = OpenStackKeypair(
            self.os_creds, KeypairConfig(
                name=self.keypair_name, public_filepath=self.pub_file_path,
                private_filepath=self.priv_file_path))
        self.keypair_creator.create()
        self.keypair_creator.clean()

        self.assertFalse(file_utils.file_exists(self.pub_file_path))
        self.assertFalse(file_utils.file_exists(self.priv_file_path))

    def test_create_keypair_gen_files_delete_2(self):
        """
        Tests the creation of a generated keypair and ensures that the files
        are deleted on clean()
        :return:
        """
        self.keypair_creator = OpenStackKeypair(
            self.os_creds, KeypairConfig(
                name=self.keypair_name, public_filepath=self.pub_file_path,
                private_filepath=self.priv_file_path, delete_on_clean=True))
        self.keypair_creator.create()
        self.keypair_creator.clean()

        self.assertFalse(file_utils.file_exists(self.pub_file_path))
        self.assertFalse(file_utils.file_exists(self.priv_file_path))

    def test_create_keypair_gen_files_keep(self):
        """
        Tests the creation of a generated keypair and ensures that the files
        are not deleted on clean()
        :return:
        """
        self.keypair_creator = OpenStackKeypair(
            self.os_creds, KeypairConfig(
                name=self.keypair_name, public_filepath=self.pub_file_path,
                private_filepath=self.priv_file_path, delete_on_clean=False))
        self.keypair_creator.create()
        self.keypair_creator.clean()

        self.assertTrue(file_utils.file_exists(self.pub_file_path))
        self.assertTrue(file_utils.file_exists(self.priv_file_path))

    def test_create_keypair_exist_files_keep(self):
        """
        Tests the creation of an existing public keypair and ensures the files
        are not deleted on clean
        :return:
        """
        keys = nova_utils.create_keys()
        file_utils.save_keys_to_files(
            keys=keys, pub_file_path=self.pub_file_path,
            priv_file_path=self.priv_file_path)
        self.keypair_creator = OpenStackKeypair(
            self.os_creds, KeypairConfig(
                name=self.keypair_name, public_filepath=self.pub_file_path,
                private_filepath=self.priv_file_path, delete_on_clean=False))
        self.keypair_creator.create()
        self.keypair_creator.clean()

        self.assertTrue(file_utils.file_exists(self.pub_file_path))
        self.assertTrue(file_utils.file_exists(self.priv_file_path))

    def test_create_keypair_exist_files_delete(self):
        """
        Tests the creation of an existing public keypair and ensures the files
        are deleted on clean
        :return:
        """
        keys = nova_utils.create_keys()
        file_utils.save_keys_to_files(
            keys=keys, pub_file_path=self.pub_file_path,
            priv_file_path=self.priv_file_path)
        self.keypair_creator = OpenStackKeypair(
            self.os_creds, KeypairConfig(
                name=self.keypair_name, public_filepath=self.pub_file_path,
                private_filepath=self.priv_file_path, delete_on_clean=True))
        self.keypair_creator.create()
        self.keypair_creator.clean()

        self.assertFalse(file_utils.file_exists(self.pub_file_path))
        self.assertFalse(file_utils.file_exists(self.priv_file_path))
