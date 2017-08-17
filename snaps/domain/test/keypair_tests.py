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
from snaps.domain.keypair import Keypair


class KeypairDomainObjectTests(unittest.TestCase):
    """
    Tests the construction of the snaps.domain.test.Keypair class
    """

    def test_construction_positional(self):
        keypair = Keypair('foo', '123-456', 'foo-bar', '01:02:03')
        self.assertEqual('foo', keypair.name)
        self.assertEqual('123-456', keypair.id)
        self.assertEqual('foo-bar', keypair.public_key)
        self.assertEqual('01:02:03', keypair.fingerprint)

    def test_construction_named(self):
        keypair = Keypair(fingerprint='01:02:03', public_key='foo-bar',
                          kp_id='123-456', name='foo')
        self.assertEqual('foo', keypair.name)
        self.assertEqual('123-456', keypair.id)
        self.assertEqual('foo-bar', keypair.public_key)
        self.assertEqual('01:02:03', keypair.fingerprint)
