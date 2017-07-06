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
from snaps.domain.vm_inst import VmInst, FloatingIp


class VmInstDomainObjectTests(unittest.TestCase):
    """
    Tests the construction of the snaps.domain.test.Image class
    """

    def test_construction_positional(self):
        vm_inst = VmInst('name', 'id', dict())
        self.assertEqual('name', vm_inst.name)
        self.assertEqual('id', vm_inst.id)
        self.assertEqual(dict(), vm_inst.networks)

    def test_construction_named(self):
        vm_inst = VmInst(networks=dict(), inst_id='id', name='name')
        self.assertEqual('name', vm_inst.name)
        self.assertEqual('id', vm_inst.id)
        self.assertEqual(dict(), vm_inst.networks)


class FloatingIpDomainObjectTests(unittest.TestCase):
    """
    Tests the construction of the snaps.domain.test.Image class
    """

    def test_construction_positional(self):
        vm_inst = FloatingIp('id-123', '10.0.0.1')
        self.assertEqual('id-123', vm_inst.id)
        self.assertEqual('10.0.0.1', vm_inst.ip)

    def test_construction_named(self):
        vm_inst = FloatingIp(ip='10.0.0.1', inst_id='id-123')
        self.assertEqual('id-123', vm_inst.id)
        self.assertEqual('10.0.0.1', vm_inst.ip)
