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
from snaps.domain.flavor import Flavor


class FlavorDomainObjectTests(unittest.TestCase):
    """
    Tests the construction of the snaps.domain.test.Flavor class
    """

    def test_construction_kwargs(self):
        flavor = Flavor(**{'name': 'name', 'id': 'id', 'ram': 10, 'disk': 20,
                           'vcpus': 3, 'ephemeral': 30, 'swap': 100,
                           'rxtx_factor': 5, 'is_public': True})
        self.assertEqual('name', flavor.name)
        self.assertEqual('id', flavor.id)
        self.assertEqual(10, flavor.ram)
        self.assertEqual(20, flavor.disk)
        self.assertEqual(3, flavor.vcpus)
        self.assertEqual(30, flavor.ephemeral)
        self.assertEqual(100, flavor.swap)
        self.assertEqual(5, flavor.rxtx_factor)
        self.assertTrue(flavor.is_public)

    def test_construction_named(self):
        flavor = Flavor(is_public=True, rxtx_factor=5, swap=100, ephemeral=30,
                        vcpus=3, disk=20, ram=10, id='id', name='name')
        self.assertEqual('name', flavor.name)
        self.assertEqual('id', flavor.id)
        self.assertEqual(10, flavor.ram)
        self.assertEqual(20, flavor.disk)
        self.assertEqual(3, flavor.vcpus)
        self.assertEqual(30, flavor.ephemeral)
        self.assertEqual(100, flavor.swap)
        self.assertEqual(5, flavor.rxtx_factor)
        self.assertTrue(flavor.is_public)
