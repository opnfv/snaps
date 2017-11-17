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

from snaps.config.keypair import KeypairConfigError, KeypairConfig


class KeypairConfigUnitTests(unittest.TestCase):
    """
    Tests the construction of the KeypairConfig class
    """

    def test_no_params(self):
        with self.assertRaises(KeypairConfigError):
            KeypairConfig()

    def test_empty_config(self):
        with self.assertRaises(KeypairConfigError):
            KeypairConfig(**dict())

    def test_small_key_size(self):
        with self.assertRaises(KeypairConfigError):
            KeypairConfig(name='foo', key_size=511)

    def test_name_only(self):
        settings = KeypairConfig(name='foo')
        self.assertEqual('foo', settings.name)
        self.assertEqual(1024, settings.key_size)
        self.assertIsNone(settings.public_filepath)
        self.assertIsNone(settings.private_filepath)
        self.assertIsNone(settings.delete_on_clean)

    def test_config_with_name_only(self):
        settings = KeypairConfig(**{'name': 'foo'})
        self.assertEqual('foo', settings.name)
        self.assertEqual(1024, settings.key_size)
        self.assertIsNone(settings.public_filepath)
        self.assertIsNone(settings.private_filepath)
        self.assertIsNone(settings.delete_on_clean)

    def test_name_pub_only(self):
        settings = KeypairConfig(name='foo', public_filepath='/foo/bar.pub')
        self.assertEqual('foo', settings.name)
        self.assertEqual(1024, settings.key_size)
        self.assertEqual('/foo/bar.pub', settings.public_filepath)
        self.assertIsNone(settings.private_filepath)
        self.assertIsNone(settings.delete_on_clean)

    def test_config_with_name_pub_only(self):
        settings = KeypairConfig(
            **{'name': 'foo', 'public_filepath': '/foo/bar.pub'})
        self.assertEqual('foo', settings.name)
        self.assertEqual(1024, settings.key_size)
        self.assertEqual('/foo/bar.pub', settings.public_filepath)
        self.assertIsNone(settings.private_filepath)
        self.assertIsNone(settings.delete_on_clean)

    def test_name_priv_only(self):
        settings = KeypairConfig(name='foo', private_filepath='/foo/bar')
        self.assertEqual('foo', settings.name)
        self.assertEqual(1024, settings.key_size)
        self.assertIsNone(settings.public_filepath)
        self.assertEqual('/foo/bar', settings.private_filepath)
        self.assertIsNone(settings.delete_on_clean)

    def test_config_with_name_priv_only(self):
        settings = KeypairConfig(
            **{'name': 'foo', 'private_filepath': '/foo/bar'})
        self.assertEqual('foo', settings.name)
        self.assertEqual(1024, settings.key_size)
        self.assertIsNone(settings.public_filepath)
        self.assertEqual('/foo/bar', settings.private_filepath)
        self.assertIsNone(settings.delete_on_clean)

    def test_all_delete_bool(self):
        settings = KeypairConfig(
            name='foo', public_filepath='/foo/bar.pub',
            private_filepath='/foo/bar', delete_on_clean=True,
            key_size=999)
        self.assertEqual('foo', settings.name)
        self.assertEqual(999, settings.key_size)
        self.assertEqual('/foo/bar.pub', settings.public_filepath)
        self.assertEqual('/foo/bar', settings.private_filepath)
        self.assertTrue(settings.delete_on_clean)

    def test_all_delete_str_true_cap(self):
        settings = KeypairConfig(
            name='foo', public_filepath='/foo/bar.pub',
            private_filepath='/foo/bar', delete_on_clean='True')
        self.assertEqual('foo', settings.name)
        self.assertEqual(1024, settings.key_size)
        self.assertEqual('/foo/bar.pub', settings.public_filepath)
        self.assertEqual('/foo/bar', settings.private_filepath)
        self.assertTrue(settings.delete_on_clean)

    def test_all_delete_str_true_lc(self):
        settings = KeypairConfig(
            name='foo', public_filepath='/foo/bar.pub',
            private_filepath='/foo/bar', delete_on_clean='true')
        self.assertEqual('foo', settings.name)
        self.assertEqual(1024, settings.key_size)
        self.assertEqual('/foo/bar.pub', settings.public_filepath)
        self.assertEqual('/foo/bar', settings.private_filepath)
        self.assertTrue(settings.delete_on_clean)

    def test_all_delete_str_false_cap(self):
        settings = KeypairConfig(
            name='foo', public_filepath='/foo/bar.pub',
            private_filepath='/foo/bar', delete_on_clean='False')
        self.assertEqual('foo', settings.name)
        self.assertEqual(1024, settings.key_size)
        self.assertEqual('/foo/bar.pub', settings.public_filepath)
        self.assertEqual('/foo/bar', settings.private_filepath)
        self.assertFalse(settings.delete_on_clean)

    def test_all_delete_str_false_lc(self):
        settings = KeypairConfig(
            name='foo', public_filepath='/foo/bar.pub',
            private_filepath='/foo/bar', delete_on_clean='false',
            key_size='999')
        self.assertEqual('foo', settings.name)
        self.assertEqual(999, settings.key_size)
        self.assertEqual('/foo/bar.pub', settings.public_filepath)
        self.assertEqual('/foo/bar', settings.private_filepath)
        self.assertFalse(settings.delete_on_clean)

    def test_config_all_delete_false_bool(self):
        settings = KeypairConfig(
            **{'name': 'foo', 'public_filepath': '/foo/bar.pub',
               'private_filepath': '/foo/bar', 'delete_on_clean': False,
               'key_size': 999})
        self.assertEqual('foo', settings.name)
        self.assertEqual(999, settings.key_size)
        self.assertEqual('/foo/bar.pub', settings.public_filepath)
        self.assertEqual('/foo/bar', settings.private_filepath)
        self.assertFalse(settings.delete_on_clean)

    def test_config_all_delete_false_str_cap(self):
        settings = KeypairConfig(
            **{'name': 'foo', 'public_filepath': '/foo/bar.pub',
               'private_filepath': '/foo/bar', 'delete_on_clean': 'False'})
        self.assertEqual('foo', settings.name)
        self.assertEqual(1024, settings.key_size)
        self.assertEqual('/foo/bar.pub', settings.public_filepath)
        self.assertEqual('/foo/bar', settings.private_filepath)
        self.assertFalse(settings.delete_on_clean)

    def test_config_all_delete_false_str_lc(self):
        settings = KeypairConfig(
            **{'name': 'foo', 'public_filepath': '/foo/bar.pub',
               'private_filepath': '/foo/bar', 'delete_on_clean': 'false'})
        self.assertEqual('foo', settings.name)
        self.assertEqual(1024, settings.key_size)
        self.assertEqual('/foo/bar.pub', settings.public_filepath)
        self.assertEqual('/foo/bar', settings.private_filepath)
        self.assertFalse(settings.delete_on_clean)

    def test_config_all_delete_false_str_foo(self):
        settings = KeypairConfig(
            **{'name': 'foo', 'public_filepath': '/foo/bar.pub',
               'private_filepath': '/foo/bar', 'delete_on_clean': 'foo',
               'key_size': '999'})
        self.assertEqual('foo', settings.name)
        self.assertEqual(999, settings.key_size)
        self.assertEqual('/foo/bar.pub', settings.public_filepath)
        self.assertEqual('/foo/bar', settings.private_filepath)
        self.assertFalse(settings.delete_on_clean)
