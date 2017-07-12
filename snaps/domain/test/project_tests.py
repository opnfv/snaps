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
from snaps.domain.project import Project


class ProjectDomainObjectTests(unittest.TestCase):
    """
    Tests the construction of the snaps.domain.test.Project class
    """

    def test_construction_positional(self):
        project = Project('foo', '123-456')
        self.assertEqual('foo', project.name)
        self.assertEqual('123-456', project.id)

    def test_construction_named(self):
        project = Project(project_id='123-456', name='foo')
        self.assertEqual('foo', project.name)
        self.assertEqual('123-456', project.id)
