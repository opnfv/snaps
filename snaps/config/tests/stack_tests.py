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

import snaps
from snaps.config.stack import StackConfigError, StackConfig


class StackConfigUnitTests(unittest.TestCase):
    """
    Tests the construction of the StackConfig class
    """

    def test_no_params(self):
        with self.assertRaises(StackConfigError):
            StackConfig()

    def test_empty_config(self):
        with self.assertRaises(StackConfigError):
            StackConfig(**dict())

    def test_name_only(self):
        with self.assertRaises(StackConfigError):
            StackConfig(name='foo')

    def test_config_with_name_only(self):
        with self.assertRaises(StackConfigError):
            StackConfig(**{'name': 'foo'})

    def test_resource_not_list(self):
        with self.assertRaises(StackConfigError):
            StackConfig(**{'name': 'foo', 'resource_files': 'bar'})

    def test_config_minimum_template(self):
        settings = StackConfig(**{'name': 'stack', 'template': 'foo'})
        self.assertEqual('stack', settings.name)
        self.assertEqual('foo', settings.template)
        self.assertIsNone(settings.template_path)
        self.assertIsNone(settings.resource_files)
        self.assertIsNone(settings.env_values)
        self.assertEqual(snaps.config.stack.STACK_COMPLETE_TIMEOUT,
                         settings.stack_create_timeout)

    def test_config_minimum_template_path(self):
        settings = StackConfig(**{'name': 'stack', 'template_path': 'foo'})
        self.assertEqual('stack', settings.name)
        self.assertIsNone(settings.template)
        self.assertEqual('foo', settings.template_path)
        self.assertIsNone(settings.resource_files)
        self.assertIsNone(settings.env_values)
        self.assertEqual(snaps.config.stack.STACK_COMPLETE_TIMEOUT,
                         settings.stack_create_timeout)

    def test_minimum_template(self):
        settings = StackConfig(name='stack', template='foo')
        self.assertEqual('stack', settings.name)
        self.assertEqual('foo', settings.template)
        self.assertIsNone(settings.template_path)
        self.assertIsNone(settings.resource_files)
        self.assertIsNone(settings.env_values)
        self.assertEqual(snaps.config.stack.STACK_COMPLETE_TIMEOUT,
                         settings.stack_create_timeout)

    def test_minimum_template_path(self):
        settings = StackConfig(name='stack', template_path='foo')
        self.assertEqual('stack', settings.name)
        self.assertEqual('foo', settings.template_path)
        self.assertIsNone(settings.template)
        self.assertIsNone(settings.resource_files)
        self.assertIsNone(settings.env_values)
        self.assertEqual(snaps.config.stack.STACK_COMPLETE_TIMEOUT,
                         settings.stack_create_timeout)

    def test_resource(self):
        settings = StackConfig(
            name='stack', template_path='foo', resource_files=['foo', 'bar'])
        self.assertEqual('stack', settings.name)
        self.assertEqual('foo', settings.template_path)
        self.assertIsNone(settings.template)
        self.assertEqual(['foo', 'bar'], settings.resource_files)
        self.assertIsNone(settings.env_values)
        self.assertEqual(snaps.config.stack.STACK_COMPLETE_TIMEOUT,
                         settings.stack_create_timeout)

    def test_all(self):
        env_values = {'foo': 'bar'}
        settings = StackConfig(
            name='stack', template='bar', template_path='foo',
            env_values=env_values, stack_create_timeout=999)
        self.assertEqual('stack', settings.name)
        self.assertEqual('bar', settings.template)
        self.assertEqual('foo', settings.template_path)
        self.assertEqual(env_values, settings.env_values)
        self.assertEqual(999, settings.stack_create_timeout)

    def test_config_all(self):
        env_values = {'foo': 'bar'}
        settings = StackConfig(
            **{'name': 'stack', 'template': 'bar', 'template_path': 'foo',
               'env_values': env_values, 'stack_create_timeout': 999})
        self.assertEqual('stack', settings.name)
        self.assertEqual('bar', settings.template)
        self.assertEqual('foo', settings.template_path)
        self.assertEqual(env_values, settings.env_values)
        self.assertEqual(999, settings.stack_create_timeout)
