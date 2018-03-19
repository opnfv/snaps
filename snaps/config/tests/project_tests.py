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

from snaps.config.project import ProjectConfig, ProjectConfigError


class ProjectConfigUnitTests(unittest.TestCase):
    """
    Tests the construction of the ProjectConfig class
    """

    def test_no_params(self):
        with self.assertRaises(ProjectConfigError):
            ProjectConfig()

    def test_empty_config(self):
        with self.assertRaises(ProjectConfigError):
            ProjectConfig(**dict())

    def test_name_only(self):
        settings = ProjectConfig(name='foo')
        self.assertEqual('foo', settings.name)
        self.assertEqual('Default', settings.domain_name)
        self.assertIsNone(settings.description)
        self.assertTrue(settings.enabled)
        self.assertEqual(list(), settings.users)
        self.assertIsNone(settings.quotas)

    def test_config_with_name_only(self):
        settings = ProjectConfig(**{'name': 'foo'})
        self.assertEqual('foo', settings.name)
        self.assertEqual('Default', settings.domain_name)
        self.assertIsNone(settings.description)
        self.assertTrue(settings.enabled)
        self.assertEqual(list(), settings.users)
        self.assertIsNone(settings.quotas)

    def test_all(self):
        users = ['test1', 'test2']
        quotas = {
            'cores': 4, 'instances': 5, 'injected_files': 6,
            'injected_file_content_bytes': 60000, 'ram': 70000, 'fixed_ips': 7,
            'key_pairs': 8}
        settings = ProjectConfig(
            name='foo', domain='bar', description='foobar', enabled=False,
            users=users, quotas=quotas)
        self.assertEqual('foo', settings.name)
        self.assertEqual('bar', settings.domain_name)
        self.assertEqual('foobar', settings.description)
        self.assertFalse(settings.enabled)
        self.assertEqual(users, settings.users)
        self.assertIsNotNone(settings.quotas)
        self.assertEquals(4, settings.quotas.get('cores'))
        self.assertEquals(5, settings.quotas.get('instances'))
        self.assertEquals(6, settings.quotas.get('injected_files'))
        self.assertEquals(
            60000, settings.quotas.get('injected_file_content_bytes'))
        self.assertEquals(70000, settings.quotas.get('ram'))
        self.assertEquals(7, settings.quotas.get('fixed_ips'))
        self.assertEquals(8, settings.quotas.get('key_pairs'))

    def test_config_all(self):
        users = ['test1', 'test2']
        settings = ProjectConfig(
            **{'name': 'foo', 'domain': 'bar', 'description': 'foobar',
               'enabled': False, 'users': users,
               'quotas': {
                   'cores': 4, 'instances': 5, 'injected_files': 6,
                   'injected_file_content_bytes': 60000, 'ram': 70000,
                   'fixed_ips': 7, 'key_pairs': 8}})
        self.assertEqual('foo', settings.name)
        self.assertEqual('bar', settings.domain_name)
        self.assertEqual('foobar', settings.description)
        self.assertFalse(settings.enabled)
        self.assertEqual(users, settings.users)
        self.assertIsNotNone(settings.quotas)
        self.assertEquals(4, settings.quotas.get('cores'))
        self.assertEquals(5, settings.quotas.get('instances'))
        self.assertEquals(6, settings.quotas.get('injected_files'))
        self.assertEquals(
            60000, settings.quotas.get('injected_file_content_bytes'))
        self.assertEquals(70000, settings.quotas.get('ram'))
        self.assertEquals(7, settings.quotas.get('fixed_ips'))
        self.assertEquals(8, settings.quotas.get('key_pairs'))
