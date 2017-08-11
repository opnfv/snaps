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
from snaps.domain.stack import Stack, Resource


class StackDomainObjectTests(unittest.TestCase):
    """
    Tests the construction of the snaps.domain.Stack class
    """

    def test_construction_positional(self):
        stack = Stack('name', 'id')
        self.assertEqual('name', stack.name)
        self.assertEqual('id', stack.id)

    def test_construction_named(self):
        stack = Stack(stack_id='id', name='name')
        self.assertEqual('name', stack.name)
        self.assertEqual('id', stack.id)


class ResourceDomainObjectTests(unittest.TestCase):
    """
    Tests the construction of the snaps.domain.Resource class
    """

    def test_construction_positional(self):
        resource = Resource('foo', 'bar')
        self.assertEqual('foo', resource.type)
        self.assertEqual('bar', resource.id)

    def test_construction_named(self):
        resource = Resource(resource_id='bar', resource_type='foo')
        self.assertEqual('foo', resource.type)
        self.assertEqual('bar', resource.id)
