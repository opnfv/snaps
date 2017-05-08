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
from snaps.domain.image import Image


class ImageDomainObjectTests(unittest.TestCase):
    """
    Tests the construction of the snaps.domain.test.Image class
    """

    def test_construction_positional(self):
        props = {'foo': 'bar'}
        image = Image('name', 'id', 100, props)
        self.assertEqual('name', image.name)
        self.assertEqual('id', image.id)
        self.assertEqual(100, image.size)
        self.assertEqual(props, image.properties)

    def test_construction_named(self):
        props = {'foo': 'bar'}
        image = Image(image_id='id', properties=props, name='name', size=101)
        self.assertEqual('name', image.name)
        self.assertEqual('id', image.id)
        self.assertEqual(101, image.size)
        self.assertEqual(props, image.properties)
