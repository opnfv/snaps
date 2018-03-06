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
from snaps.domain.stack import Stack, Resource, Output


class StackDomainObjectTests(unittest.TestCase):
    """
    Tests the construction of the snaps.domain.Stack class
    """

    def test_construction_positional(self):
        stack = Stack(
            'name', 'id', 'stack_proj_id', 'fine', 'good')
        self.assertEqual('name', stack.name)
        self.assertEqual('id', stack.id)
        self.assertEqual('stack_proj_id', stack.stack_project_id)
        self.assertEqual('fine', stack.status)
        self.assertEqual('good', stack.status_reason)

    def test_construction_named(self):
        stack = Stack(
            stack_id='id', name='name', stack_project_id='stack_proj_id',
            status='fine', status_reason='good')
        self.assertEqual('name', stack.name)
        self.assertEqual('id', stack.id)
        self.assertEqual('stack_proj_id', stack.stack_project_id)
        self.assertEqual('fine', stack.status)
        self.assertEqual('good', stack.status_reason)


class ResourceDomainObjectTests(unittest.TestCase):
    """
    Tests the construction of the snaps.domain.Resource class
    """

    def test_construction_positional(self):
        resource = Resource('res_name', 'foo', 'bar', 'status', 'reason')
        self.assertEqual('res_name', resource.name)
        self.assertEqual('foo', resource.type)
        self.assertEqual('bar', resource.id)
        self.assertEqual('status', resource.status)
        self.assertEqual('reason', resource.status_reason)

    def test_construction_named(self):
        resource = Resource(
            status_reason=None, status=None, resource_id='bar',
            resource_type='foo', name='res_name')
        self.assertEqual('res_name', resource.name)
        self.assertEqual('foo', resource.type)
        self.assertEqual('bar', resource.id)
        self.assertIsNone(resource.status)
        self.assertIsNone(resource.status_reason)


class OutputDomainObjectTests(unittest.TestCase):
    """
    Tests the construction of the snaps.domain.Resource class
    """

    def test_construction_kwargs(self):
        kwargs = {'description': 'foo', 'output_key': 'test_key',
                  'output_value': 'bar'}
        resource = Output(**kwargs)
        self.assertEqual('foo', resource.description)
        self.assertEqual('test_key', resource.key)
        self.assertEqual('bar', resource.value)

    def test_construction_named(self):
        resource = Output(description='foo', output_key='test_key',
                          output_value='bar')
        self.assertEqual('foo', resource.description)
        self.assertEqual('test_key', resource.key)
        self.assertEqual('bar', resource.value)
