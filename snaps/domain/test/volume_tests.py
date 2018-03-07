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
from snaps.domain.volume import (
    QoSSpec, VolumeType, VolumeTypeEncryption, Volume)


class VolumeDomainObjectTests(unittest.TestCase):
    """
    Tests the construction of the snaps.domain.volume.Volume class
    """

    def test_construction_positional(self):
        volume = Volume('name1', 'id1', 'proj_id1', 'desc_val1', 2,
                        'type_val1', 'avail_zone1', False,
                        [{'attached_at': 'foo'}])
        self.assertEqual('name1', volume.name)
        self.assertEqual('id1', volume.id)
        self.assertEqual('proj_id1', volume.project_id)
        self.assertEqual('desc_val1', volume.description)
        self.assertEqual(2, volume.size)
        self.assertEqual('type_val1', volume.type)
        self.assertEqual('avail_zone1', volume.availability_zone)
        self.assertFalse(volume.multi_attach)
        self.assertIsNotNone(volume.attachments)
        self.assertTrue(isinstance(volume.attachments[0], dict))
        self.assertEqual(1, len(volume.attachments))

    def test_construction_named(self):
        volume = Volume(attachments=[{'attached_at': 'foo'}],
                        multi_attach=True, availability_zone='avail_zone2',
                        vol_type='type_val2', size=3, description='desc_val2',
                        volume_id='id2', name='name2', project_id='proj_id1')
        self.assertEqual('name2', volume.name)
        self.assertEqual('id2', volume.id)
        self.assertEqual('proj_id1', volume.project_id)
        self.assertEqual('desc_val2', volume.description)
        self.assertEqual(3, volume.size)
        self.assertEqual('type_val2', volume.type)
        self.assertEqual('avail_zone2', volume.availability_zone)
        self.assertTrue(volume.multi_attach)
        self.assertIsNotNone(volume.attachments)
        self.assertTrue(isinstance(volume.attachments[0], dict))
        self.assertEqual(1, len(volume.attachments))


class VolumeTypeDomainObjectTests(unittest.TestCase):
    """
    Tests the construction of the snaps.domain.volume.VolumeType class
    """

    def test_construction_positional(self):
        encryption = VolumeTypeEncryption(
            'id-encrypt1', 'id-vol-type1', 'loc1', 'provider1', 'cipher1', 99)
        qos_spec = QoSSpec('name', 'id', 'consumer')

        volume_type = VolumeType('name', 'id', True, encryption, qos_spec)
        self.assertEqual('name', volume_type.name)
        self.assertEqual('id', volume_type.id)
        self.assertTrue(volume_type.public)
        self.assertEqual(encryption, volume_type.encryption)
        self.assertEqual(qos_spec, volume_type.qos_spec)

    def test_construction_named(self):
        encryption = VolumeTypeEncryption(
            'id-encrypt1', 'id-vol-type1', 'loc1', 'provider1', 'cipher1', 99)
        qos_spec = QoSSpec('name', 'id', 'consumer')

        volume_type = VolumeType(
            qos_spec=qos_spec, encryption=encryption, volume_type_id='id',
            name='name', public='true')
        self.assertEqual('name', volume_type.name)
        self.assertEqual('id', volume_type.id)
        self.assertTrue(volume_type.public)
        self.assertEqual(encryption, volume_type.encryption)
        self.assertEqual(qos_spec, volume_type.qos_spec)


class VolumeTypeEncryptionObjectTests(unittest.TestCase):
    """
    Tests the construction of the snaps.domain.volume.VolumeTypeEncryption
    class
    """

    def test_construction_positional(self):
        encryption = VolumeTypeEncryption(
            'id-encrypt1', 'id-vol-type1', 'loc1', 'provider1', 'cipher1', 99)
        self.assertEqual('id-encrypt1', encryption.id)
        self.assertEqual('id-vol-type1', encryption.volume_type_id)
        self.assertEqual('loc1', encryption.control_location)
        self.assertEqual('provider1', encryption.provider)
        self.assertEqual('cipher1', encryption.cipher)
        self.assertEqual(99, encryption.key_size)

    def test_construction_named(self):
        encryption = VolumeTypeEncryption(
            key_size=89, cipher='cipher2', provider='provider2',
            control_location='loc2', volume_type_id='id-vol-type2',
            volume_encryption_id='id-encrypt2')
        self.assertEqual('id-encrypt2', encryption.id)
        self.assertEqual('id-vol-type2', encryption.volume_type_id)
        self.assertEqual('loc2', encryption.control_location)
        self.assertEqual('provider2', encryption.provider)
        self.assertEqual('cipher2', encryption.cipher)
        self.assertEqual(89, encryption.key_size)


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
