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

from snaps.config.user import UserConfig


class UserConfigUnitTests(unittest.TestCase):
    """
    Tests the construction of the UserConfig class
    """

    def test_no_params(self):
        with self.assertRaises(Exception):
            UserConfig()

    def test_empty_config(self):
        with self.assertRaises(Exception):
            UserConfig(**dict())

    def test_name_only(self):
        with self.assertRaises(Exception):
            UserConfig(name='foo')

    def test_config_with_name_only(self):
        with self.assertRaises(Exception):
            UserConfig(**{'name': 'foo'})

    def test_name_pass_enabled_str(self):
        with self.assertRaises(Exception):
            UserConfig(name='foo', password='bar', enabled='true')

    def test_config_with_name_pass_enabled_str(self):
        with self.assertRaises(Exception):
            UserConfig(
                **{'name': 'foo', 'password': 'bar', 'enabled': 'true'})

    def test_name_pass_only(self):
        settings = UserConfig(name='foo', password='bar')
        self.assertEqual('foo', settings.name)
        self.assertEqual('bar', settings.password)
        self.assertIsNone(settings.project_name)
        self.assertIsNone(settings.email)
        self.assertTrue(settings.enabled)

    def test_config_with_name_pass_only(self):
        settings = UserConfig(**{'name': 'foo', 'password': 'bar'})
        self.assertEqual('foo', settings.name)
        self.assertEqual('bar', settings.password)
        self.assertIsNone(settings.project_name)
        self.assertIsNone(settings.email)
        self.assertTrue(settings.enabled)

    def test_all(self):
        settings = UserConfig(
            name='foo', password='bar', project_name='proj-foo',
            email='foo@bar.com', enabled=False)
        self.assertEqual('foo', settings.name)
        self.assertEqual('bar', settings.password)
        self.assertEqual('proj-foo', settings.project_name)
        self.assertEqual('foo@bar.com', settings.email)
        self.assertFalse(settings.enabled)

    def test_config_all(self):
        settings = UserConfig(
            **{'name': 'foo', 'password': 'bar', 'project_name': 'proj-foo',
               'email': 'foo@bar.com', 'enabled': False})
        self.assertEqual('foo', settings.name)
        self.assertEqual('bar', settings.password)
        self.assertEqual('proj-foo', settings.project_name)
        self.assertEqual('foo@bar.com', settings.email)
        self.assertFalse(settings.enabled)
