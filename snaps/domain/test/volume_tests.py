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
from snaps.domain.volume import QoSSpec


class QoSSpecDomainObjectTests(unittest.TestCase):
    """
    Tests the construction of the snaps.domain.volume.QoSSpec class
    """

    def test_construction_positional(self):
        qos_spec = QoSSpec('name', 'id', 'consumer')
        self.assertEqual('name', qos_spec.name)
        self.assertEqual('id', qos_spec.id)
        self.assertEqual('consumer', qos_spec.consumer)

    def test_construction_named(self):
        qos_spec = QoSSpec(consumer='consumer', spec_id='id', name='name')
        self.assertEqual('name', qos_spec.name)
        self.assertEqual('id', qos_spec.id)
        self.assertEqual('consumer', qos_spec.consumer)
