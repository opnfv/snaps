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
import logging
import uuid

import time
from cinderclient.exceptions import NotFound, BadRequest

from snaps.config.volume import VolumeConfig
from snaps.config.volume_type import (
    VolumeTypeConfig, ControlLocation, VolumeTypeEncryptionConfig)
from snaps.config.qos import Consumer, QoSConfig
from snaps.openstack import create_volume
from snaps.openstack.create_qos import Consumer
from snaps.openstack.tests import validation_utils
from snaps.openstack.tests.os_source_file_test import OSComponentTestCase
from snaps.openstack.utils import cinder_utils, keystone_utils

__author__ = 'spisarski'


logger = logging.getLogger('cinder_utils_tests')


class CinderSmokeTests(OSComponentTestCase):
    """
    Tests to ensure that the neutron client can communicate with the cloud
    """

    def test_cinder_connect_success(self):
        """
        Tests to ensure that the proper credentials can connect.
        """
        cinder = cinder_utils.cinder_client(self.os_creds, self.os_session)
        volumes = cinder.volumes.list()
        self.assertIsNotNone(volumes)
        self.assertTrue(isinstance(volumes, list))

    def test_cinder_connect_fail(self):
        """
        Tests to ensure that the improper credentials cannot connect.
        """
        from snaps.openstack.os_credentials import OSCreds

        with self.assertRaises(Exception):
            cinder = cinder_utils.cinder_client(OSCreds(
                username='user', password='pass', auth_url='url',
                project_name='project'))
            cinder.volumes.list()


class CinderUtilsVolumeTests(OSComponentTestCase):
    """
    Test for the CreateVolume class defined in create_volume.py
    """

    def setUp(self):
        """
        Instantiates the CreateVolume object that is responsible for
        downloading and creating an OS volume file within OpenStack
        """
        guid = uuid.uuid4()
        self.volume_name = self.__class__.__name__ + '-' + str(guid)
        self.volume = None
        self.cinder = cinder_utils.cinder_client(
            self.os_creds, self.os_session)
        self.keystone = keystone_utils.keystone_client(
            self.os_creds, self.os_session)

    def tearDown(self):
        """
        Cleans the remote OpenStack objects
        """
        if self.volume:
            try:
                cinder_utils.delete_volume(self.cinder, self.volume)
            except NotFound:
                pass

        self.assertTrue(volume_deleted(self.cinder, self.volume))

    def test_create_simple_volume(self):
        """
        Tests the cinder_utils.create_volume()
        """
        volume_settings = VolumeConfig(name=self.volume_name)
        self.volume = cinder_utils.create_volume(
            self.cinder, self.keystone, volume_settings)
        self.assertIsNotNone(self.volume)
        self.assertEqual(self.volume_name, self.volume.name)

        self.assertTrue(volume_active(self.cinder, self.volume))

        volume = cinder_utils.get_volume(
            self.cinder, self.keystone, volume_settings=volume_settings,
            project_name=self.os_creds.project_name)
        self.assertIsNotNone(volume)
        validation_utils.objects_equivalent(self.volume, volume)

    def test_create_delete_volume(self):
        """
        Tests the cinder_utils.create_volume()
        """
        volume_settings = VolumeConfig(name=self.volume_name)
        self.volume = cinder_utils.create_volume(
            self.cinder, self.keystone, volume_settings)
        self.assertIsNotNone(self.volume)
        self.assertEqual(self.volume_name, self.volume.name)

        self.assertTrue(volume_active(self.cinder, self.volume))

        volume = cinder_utils.get_volume(
            self.cinder, self.keystone, volume_settings=volume_settings,
            project_name=self.os_creds.project_name)
        self.assertIsNotNone(volume)
        validation_utils.objects_equivalent(self.volume, volume)

        cinder_utils.delete_volume(self.cinder, self.volume)
        self.assertTrue(volume_deleted(self.cinder, self.volume))
        self.assertIsNone(
            cinder_utils.get_volume(
                self.cinder, self.keystone, volume_settings,
                project_name=self.os_creds.project_name))


def volume_active(cinder, volume):
    """
    Returns true if volume becomes active
    :param cinder:
    :param volume:
    :return:
    """
    end_time = time.time() + create_volume.VOLUME_ACTIVE_TIMEOUT
    while time.time() < end_time:
        status = cinder_utils.get_volume_status(cinder, volume)
        if status == create_volume.STATUS_ACTIVE:
            return True
        elif status == create_volume.STATUS_FAILED:
            return False
        time.sleep(3)

    return False


def volume_deleted(cinder, volume):
    """
    Returns true if volume becomes active
    :param cinder:
    :param volume:
    :return:
    """
    end_time = time.time() + create_volume.VOLUME_ACTIVE_TIMEOUT
    while time.time() < end_time:
        try:
            status = cinder_utils.get_volume_status(cinder, volume)
            if status == create_volume.STATUS_DELETED:
                return True
        except NotFound:
            return True

        time.sleep(3)

    return False


class CinderUtilsQoSTests(OSComponentTestCase):
    """
    Test for the CreateQos class defined in create_qos.py
    """

    def setUp(self):
        """
        Creates objects for testing cinder_utils.py
        """
        guid = uuid.uuid4()
        self.qos_name = self.__class__.__name__ + '-' + str(guid)
        self.specs = {'foo': 'bar '}
        self.qos = None
        self.cinder = cinder_utils.cinder_client(
            self.os_creds, self.os_session)

    def tearDown(self):
        """
        Cleans the remote OpenStack objects
        """
        if self.qos:
            try:
                cinder_utils.delete_qos(self.cinder, self.qos)
            except NotFound:
                pass

        super(self.__class__, self).__clean__()

    def test_create_qos_both(self):
        """
        Tests the cinder_utils.create_qos()
        """
        qos_settings = QoSConfig(
            name=self.qos_name, specs=self.specs, consumer=Consumer.both)
        self.qos = cinder_utils.create_qos(self.cinder, qos_settings)
        self.assertIsNotNone(self.qos)

        qos1 = cinder_utils.get_qos(self.cinder, qos_settings=qos_settings)
        self.assertIsNotNone(qos1)
        validation_utils.objects_equivalent(self.qos, qos1)

        qos2 = cinder_utils.get_qos_by_id(self.cinder, qos1.id)
        self.assertIsNotNone(qos2)
        validation_utils.objects_equivalent(self.qos, qos2)

    def test_create_qos_front(self):
        """
        Tests the cinder_utils.create_qos()
        """
        qos_settings = QoSConfig(
            name=self.qos_name, specs=self.specs, consumer=Consumer.front_end)
        self.qos = cinder_utils.create_qos(self.cinder, qos_settings)
        self.assertIsNotNone(self.qos)

        qos1 = cinder_utils.get_qos(self.cinder, qos_settings=qos_settings)
        self.assertIsNotNone(qos1)
        validation_utils.objects_equivalent(self.qos, qos1)

        qos2 = cinder_utils.get_qos_by_id(self.cinder, qos1.id)
        self.assertIsNotNone(qos2)
        validation_utils.objects_equivalent(self.qos, qos2)

    def test_create_qos_back(self):
        """
        Tests the cinder_utils.create_qos()
        """
        qos_settings = QoSConfig(
            name=self.qos_name, specs=self.specs, consumer=Consumer.back_end)
        self.qos = cinder_utils.create_qos(self.cinder, qos_settings)
        self.assertIsNotNone(self.qos)

        qos1 = cinder_utils.get_qos(self.cinder, qos_settings=qos_settings)
        self.assertIsNotNone(qos1)
        validation_utils.objects_equivalent(self.qos, qos1)

        qos2 = cinder_utils.get_qos_by_id(self.cinder, qos1.id)
        self.assertIsNotNone(qos2)
        validation_utils.objects_equivalent(self.qos, qos2)

    def test_create_delete_qos(self):
        """
        Tests the cinder_utils.create_qos()
        """
        qos_settings = QoSConfig(name=self.qos_name, consumer=Consumer.both)
        self.qos = cinder_utils.create_qos(self.cinder, qos_settings)
        self.assertIsNotNone(self.qos)
        self.assertEqual(self.qos_name, self.qos.name)

        qos = cinder_utils.get_qos(
            self.cinder, qos_settings=qos_settings)
        self.assertIsNotNone(qos)
        validation_utils.objects_equivalent(self.qos, qos)

        cinder_utils.delete_qos(self.cinder, self.qos)
        self.assertIsNone(cinder_utils.get_qos(
            self.cinder, qos_settings=qos_settings))


class CinderUtilsSimpleVolumeTypeTests(OSComponentTestCase):
    """
    Tests the creation of a Volume Type without any external settings such as
    QoS Specs or encryption
    """

    def setUp(self):
        """
        Instantiates the CreateVolume object that is responsible for
        downloading and creating an OS volume file within OpenStack
        """
        guid = uuid.uuid4()
        volume_type_name = self.__class__.__name__ + '-' + str(guid)
        self.volume_type_settings = VolumeTypeConfig(name=volume_type_name)
        self.volume_type = None
        self.cinder = cinder_utils.cinder_client(
            self.os_creds, self.os_session)

    def tearDown(self):
        """
        Cleans the remote OpenStack objects
        """
        if self.volume_type:
            try:
                cinder_utils.delete_volume_type(self.cinder, self.volume_type)
            except NotFound:
                pass

        super(self.__class__, self).__clean__()

    def test_create_simple_volume_type(self):
        """
        Tests the cinder_utils.create_volume_type(), get_volume_type(), and
        get_volume_type_by_id()
        """
        self.volume_type = cinder_utils.create_volume_type(
            self.cinder, self.volume_type_settings)
        self.assertIsNotNone(self.volume_type)
        self.assertEqual(self.volume_type_settings.name, self.volume_type.name)

        volume_type1 = cinder_utils.get_volume_type(
            self.cinder, volume_type_settings=self.volume_type_settings)
        self.assertEquals(self.volume_type, volume_type1)
        self.assertEquals(self.volume_type_settings.public,
                          volume_type1.public)

        volume_type2 = cinder_utils.get_volume_type_by_id(
            self.cinder, volume_type1.id)
        self.assertEquals(self.volume_type, volume_type2)
        self.assertIsNone(self.volume_type.encryption)

    def test_create_delete_volume_type(self):
        """
        Primarily tests the cinder_utils.delete_volume()
        """
        self.volume_type = cinder_utils.create_volume_type(
            self.cinder, self.volume_type_settings)
        self.assertIsNotNone(self.volume_type)
        self.assertEqual(self.volume_type_settings.name, self.volume_type.name)

        volume_type = cinder_utils.get_volume_type(
            self.cinder, volume_type_settings=self.volume_type_settings)
        self.assertIsNotNone(volume_type)
        validation_utils.objects_equivalent(self.volume_type, volume_type)
        self.assertIsNone(self.volume_type.encryption)

        cinder_utils.delete_volume_type(self.cinder, self.volume_type)
        self.assertIsNone(cinder_utils.get_volume_type_by_id(
            self.cinder, self.volume_type.id))


class CinderUtilsAddEncryptionTests(OSComponentTestCase):
    """
    Tests the creation of an encryption and association to and existing
    VolumeType object
    """

    def setUp(self):
        """
        Instantiates the CreateVolume object that is responsible for
        downloading and creating an OS volume file within OpenStack
        """
        guid = uuid.uuid4()
        self.encryption_name = self.__class__.__name__ + '-' + str(guid)
        self.encryption = None

        self.cinder = cinder_utils.cinder_client(
            self.os_creds, self.os_session)

        volume_type_name = self.__class__.__name__ + '-' + str(guid) + '-type'
        self.volume_type = cinder_utils.create_volume_type(
            self.cinder, VolumeTypeConfig(name=volume_type_name))

    def tearDown(self):
        """
        Cleans the remote OpenStack objects
        """
        if self.encryption:
            try:
                cinder_utils.delete_volume_type_encryption(
                    self.cinder, self.volume_type)
            except NotFound:
                pass

        if self.volume_type:
            try:
                cinder_utils.delete_volume_type(self.cinder, self.volume_type)
            except NotFound:
                pass

        super(self.__class__, self).__clean__()

    def test_create_simple_encryption(self):
        """
        Tests the cinder_utils.create_volume_encryption(),
        get_volume_encryption(), and get_volume_encryption_by_id()
        """
        encryption_settings = VolumeTypeEncryptionConfig(
            name=self.encryption_name, provider_class='foo',
            control_location=ControlLocation.front_end)
        self.encryption = cinder_utils.create_volume_encryption(
            self.cinder, self.volume_type, encryption_settings)
        self.assertIsNotNone(self.encryption)
        self.assertEqual('foo', self.encryption.provider)
        self.assertEqual(ControlLocation.front_end.value,
                         self.encryption.control_location)

        encryption1 = cinder_utils.get_volume_encryption_by_type(
            self.cinder, self.volume_type)
        self.assertEquals(self.encryption, encryption1)

    def test_create_delete_encryption(self):
        """
        Primarily tests the cinder_utils.delete_volume_type_encryption()
        """
        encryption_settings = VolumeTypeEncryptionConfig(
            name=self.encryption_name, provider_class='LuksEncryptor',
            control_location=ControlLocation.back_end)
        self.encryption = cinder_utils.create_volume_encryption(
            self.cinder, self.volume_type, encryption_settings)
        self.assertIsNotNone(self.encryption)
        self.assertEqual('LuksEncryptor', self.encryption.provider)
        self.assertEqual(ControlLocation.back_end.value,
                         self.encryption.control_location)

        encryption1 = cinder_utils.get_volume_encryption_by_type(
            self.cinder, self.volume_type)
        self.assertEquals(self.encryption, encryption1)

        cinder_utils.delete_volume_type_encryption(
            self.cinder, self.volume_type)

        encryption2 = cinder_utils.get_volume_encryption_by_type(
            self.cinder, self.volume_type)
        self.assertIsNone(encryption2)

    def test_create_with_all_attrs(self):
        """
        Tests the cinder_utils.create_volume_encryption() with all valid
        settings
        """
        encryption_settings = VolumeTypeEncryptionConfig(
            name=self.encryption_name, provider_class='foo',
            cipher='bar', control_location=ControlLocation.back_end,
            key_size=1)
        self.encryption = cinder_utils.create_volume_encryption(
            self.cinder, self.volume_type, encryption_settings)
        self.assertIsNotNone(self.encryption)
        self.assertEqual('foo', self.encryption.provider)
        self.assertEqual('bar', self.encryption.cipher)
        self.assertEqual(1, self.encryption.key_size)
        self.assertEqual(ControlLocation.back_end.value,
                         self.encryption.control_location)

        encryption1 = cinder_utils.get_volume_encryption_by_type(
            self.cinder, self.volume_type)
        self.assertEquals(self.encryption, encryption1)

    def test_create_bad_key_size(self):
        """
        Tests the cinder_utils.create_volume_encryption() raises an exception
        when the provider class does not exist
        """
        encryption_settings = VolumeTypeEncryptionConfig(
            name=self.encryption_name, provider_class='foo',
            cipher='bar', control_location=ControlLocation.back_end,
            key_size=-1)

        with self.assertRaises(BadRequest):
            self.encryption = cinder_utils.create_volume_encryption(
                self.cinder, self.volume_type, encryption_settings)


class CinderUtilsVolumeTypeCompleteTests(OSComponentTestCase):
    """
    Tests to ensure that a volume type can have a QoS Spec added to it
    """

    def setUp(self):
        """
        Creates objects for testing cinder_utils.py
        """
        guid = uuid.uuid4()
        self.qos_name = self.__class__.__name__ + '-' + str(guid) + '-qos'
        self.vol_type_name = self.__class__.__name__ + '-' + str(guid)
        self.specs = {'foo': 'bar'}
        self.cinder = cinder_utils.cinder_client(
            self.os_creds, self.os_session)
        qos_settings = QoSConfig(
            name=self.qos_name, specs=self.specs, consumer=Consumer.both)
        self.qos = cinder_utils.create_qos(self.cinder, qos_settings)
        self.volume_type = None

    def tearDown(self):
        """
        Cleans the remote OpenStack objects
        """
        if self.volume_type:
            if self.volume_type.encryption:
                try:
                    cinder_utils.delete_volume_type_encryption(
                        self.cinder, self.volume_type)
                except NotFound:
                    pass
            try:
                cinder_utils.delete_volume_type(self.cinder, self.volume_type)
            except NotFound:
                pass

        if self.qos:
            try:
                cinder_utils.delete_qos(self.cinder, self.qos)
            except NotFound:
                pass

        super(self.__class__, self).__clean__()

    def test_create_with_encryption(self):
        """
        Tests the cinder_utils.create_volume_type() where encryption has been
        configured
        """
        encryption_settings = VolumeTypeEncryptionConfig(
            name='foo', provider_class='bar',
            control_location=ControlLocation.back_end)
        volume_type_settings = VolumeTypeConfig(
            name=self.vol_type_name, encryption=encryption_settings)
        self.volume_type = cinder_utils.create_volume_type(
            self.cinder, volume_type_settings)

        vol_encrypt = cinder_utils.get_volume_encryption_by_type(
            self.cinder, self.volume_type)
        self.assertIsNotNone(vol_encrypt)
        self.assertIsNone(self.volume_type.qos_spec)
        self.assertEqual(self.volume_type.encryption, vol_encrypt)
        self.assertEqual(self.volume_type.id, vol_encrypt.volume_type_id)

    def test_create_with_qos(self):
        """
        Tests the cinder_utils.create_volume_type() with an associated QoS Spec
        """
        volume_type_settings = VolumeTypeConfig(
            name=self.vol_type_name, qos_spec_name=self.qos_name)
        self.volume_type = cinder_utils.create_volume_type(
            self.cinder, volume_type_settings)

        self.assertIsNotNone(self.volume_type)
        self.assertIsNone(self.volume_type.encryption)
        self.assertIsNotNone(self.volume_type.qos_spec)
        self.assertEqual(self.qos.id, self.volume_type.qos_spec.id)

    def test_create_with_invalid_qos(self):
        """
        Tests the cinder_utils.create_volume_type() when the QoS Spec name
        does not exist
        """
        volume_type_settings = VolumeTypeConfig(
            name=self.vol_type_name, qos_spec_name='foo')

        self.volume_type = cinder_utils.create_volume_type(
            self.cinder, volume_type_settings)

        self.assertIsNone(self.volume_type.qos_spec)

    def test_create_with_qos_and_encryption(self):
        """
        Tests the cinder_utils.create_volume_type() with encryption and an
        associated QoS Spec
        """
        encryption_settings = VolumeTypeEncryptionConfig(
            name='foo', provider_class='bar',
            control_location=ControlLocation.back_end)
        volume_type_settings = VolumeTypeConfig(
            name=self.vol_type_name, qos_spec_name=self.qos_name,
            encryption=encryption_settings)
        self.volume_type = cinder_utils.create_volume_type(
            self.cinder, volume_type_settings)

        self.assertIsNotNone(self.volume_type)
        vol_encrypt = cinder_utils.get_volume_encryption_by_type(
            self.cinder, self.volume_type)
        self.assertIsNotNone(vol_encrypt)
        self.assertEqual(self.volume_type.id, vol_encrypt.volume_type_id)
        self.assertIsNotNone(self.volume_type.qos_spec)
        self.assertEqual(self.qos.id, self.volume_type.qos_spec.id)
