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
from snaps.config.volume_type import (
    VolumeTypeConfig, VolumeTypeEncryptionConfig, VolumeTypeConfigError,
    ControlLocation)
from snaps.config.qos import QoSConfig, Consumer
from snaps.openstack.create_qos import OpenStackQoS

try:
    from urllib.request import URLError
except ImportError:
    from urllib2 import URLError

import logging
import unittest
import uuid

from snaps.openstack import create_volume_type
from snaps.openstack.create_volume_type import (
    VolumeTypeSettings, VolumeTypeEncryptionSettings, OpenStackVolumeType)
from snaps.openstack.tests.os_source_file_test import OSIntegrationTestCase
from snaps.openstack.utils import cinder_utils

__author__ = 'spisarski'

logger = logging.getLogger('create_volume_type_tests')


class VolumeTypeSettingsUnitTests(unittest.TestCase):
    """
    Tests the construction of the VolumeTypeSettings class
    """

    def test_no_params(self):
        with self.assertRaises(VolumeTypeConfigError):
            VolumeTypeSettings()

    def test_empty_config(self):
        with self.assertRaises(VolumeTypeConfigError):
            VolumeTypeSettings(**dict())

    def test_name_only(self):
        settings = VolumeTypeSettings(name='foo')
        self.assertEqual('foo', settings.name)
        self.assertIsNone(settings.description)
        self.assertIsNone(settings.qos_spec_name)
        self.assertIsNone(settings.encryption)
        self.assertFalse(settings.public)

    def test_config_with_name_only(self):
        settings = VolumeTypeSettings(**{'name': 'foo'})
        self.assertEqual('foo', settings.name)
        self.assertIsNone(settings.description)
        self.assertIsNone(settings.qos_spec_name)
        self.assertIsNone(settings.encryption)
        self.assertFalse(settings.public)

    def test_all(self):
        encryption_settings = VolumeTypeEncryptionSettings(
            name='foo', provider_class='bar',
            control_location=ControlLocation.back_end)
        settings = VolumeTypeSettings(
            name='foo', description='desc', encryption=encryption_settings,
            qos_spec_name='spec_name', public=True)
        self.assertEqual('foo', settings.name)
        self.assertEqual('desc', settings.description)
        self.assertEqual('spec_name', settings.qos_spec_name)
        self.assertEqual(encryption_settings, settings.encryption)
        self.assertTrue(True, settings.public)

    def test_all_string(self):
        encryption_settings = {
            'name': 'foo', 'provider_class': 'bar',
            'control_location': 'back-end'}
        settings = VolumeTypeSettings(
            name='foo', description='desc', encryption=encryption_settings,
            qos_spec_name='spec_name', public='true')
        self.assertEqual('foo', settings.name)
        self.assertEqual('desc', settings.description)
        self.assertEqual('spec_name', settings.qos_spec_name)
        self.assertEqual(VolumeTypeEncryptionSettings(**encryption_settings),
                         settings.encryption)
        self.assertTrue(settings.public)

    def test_config_all(self):
        encryption_settings = {
            'name': 'foo', 'provider_class': 'bar',
            'control_location': 'back-end'}
        settings = VolumeTypeSettings(
            **{'name': 'foo', 'description': 'desc',
               'encryption': encryption_settings,
               'qos_spec_name': 'spec_name', 'public': 'false'})
        self.assertEqual('foo', settings.name)
        self.assertEqual('desc', settings.description)
        self.assertEqual('spec_name', settings.qos_spec_name)
        self.assertEqual(VolumeTypeEncryptionSettings(**encryption_settings),
                         settings.encryption)
        self.assertFalse(settings.public)


class CreateSimpleVolumeTypeSuccessTests(OSIntegrationTestCase):
    """
    Test for the OpenStackVolumeType class defined in py
    without any QoS Specs or Encryption
    """

    def setUp(self):
        """
        Instantiates the CreateVolumeType object that is responsible for
        downloading and creating an OS volume type file within OpenStack
        """
        super(self.__class__, self).__start__()

        guid = uuid.uuid4()
        self.volume_type_settings = VolumeTypeConfig(
            name=self.__class__.__name__ + '-' + str(guid))

        self.cinder = cinder_utils.cinder_client(
            self.admin_os_creds, self.admin_os_session)
        self.volume_type_creator = OpenStackVolumeType(
            self.admin_os_creds, self.volume_type_settings)

    def tearDown(self):
        """
        Cleans the volume type
        """
        if self.volume_type_creator:
            self.volume_type_creator.clean()

        super(self.__class__, self).__clean__()

    def test_create_volume_type(self):
        """
        Tests the creation of an OpenStack volume.
        """
        # Create VolumeType
        created_volume_type = self.volume_type_creator.create()
        self.assertIsNotNone(created_volume_type)
        self.assertEqual(self.volume_type_settings.name,
                         created_volume_type.name)

        retrieved_volume_type1 = cinder_utils.get_volume_type(
            self.cinder, volume_type_settings=self.volume_type_settings)
        self.assertIsNotNone(retrieved_volume_type1)
        self.assertEqual(created_volume_type, retrieved_volume_type1)

        retrieved_volume_type2 = cinder_utils.get_volume_type_by_id(
            self.cinder, created_volume_type.id)
        self.assertEqual(created_volume_type, retrieved_volume_type2)

    def test_create_delete_volume_type(self):
        """
        Tests the creation then deletion of an OpenStack volume type to ensure
        clean() does not raise an Exception.
        """
        # Create VolumeType
        created_volume_type = self.volume_type_creator.create()
        self.assertIsNotNone(created_volume_type)

        retrieved_volume_type = cinder_utils.get_volume_type(
            self.cinder, volume_type_settings=self.volume_type_settings)
        self.assertIsNotNone(retrieved_volume_type)
        self.assertEqual(created_volume_type, retrieved_volume_type)

        # Delete VolumeType manually
        cinder_utils.delete_volume_type(self.cinder, created_volume_type)

        self.assertIsNone(cinder_utils.get_volume_type(
            self.cinder, volume_type_settings=self.volume_type_settings))

        # Must not throw an exception when attempting to cleanup non-existent
        # volume_type
        self.volume_type_creator.clean()
        self.assertIsNone(self.volume_type_creator.get_volume_type())

    def test_create_same_volume_type(self):
        """
        Tests the creation of an OpenStack volume_type when one already exists.
        """
        # Create VolumeType
        volume_type1 = self.volume_type_creator.create()

        retrieved_volume_type = cinder_utils.get_volume_type(
            self.cinder, volume_type_settings=self.volume_type_settings)
        self.assertEqual(volume_type1, retrieved_volume_type)

        # Should be retrieving the instance data
        os_volume_type_2 = create_volume_type.OpenStackVolumeType(
            self.admin_os_creds, self.volume_type_settings)
        volume_type2 = os_volume_type_2.create()
        self.assertEqual(volume_type2, volume_type2)


class CreateVolumeTypeComplexTests(OSIntegrationTestCase):
    """
    Test cases for the CreateVolumeType class that include QoS Specs and/or
    encryption
    """

    def setUp(self):
        super(self.__class__, self).__start__()

        self.cinder = cinder_utils.cinder_client(
            self.admin_os_creds, self.admin_os_session)

        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())

        self.volume_type_name = guid + '-vol_type'
        self.volume_type_creator = None

        qos_settings = QoSConfig(
            name=guid + '-qos-spec', consumer=Consumer.both)
        self.qos_creator = OpenStackQoS(self.admin_os_creds, qos_settings)
        self.qos_creator.create()

    def tearDown(self):
        if self.volume_type_creator:
            self.volume_type_creator.clean()

        if self.qos_creator:
            self.qos_creator.clean()

        super(self.__class__, self).__clean__()

    def test_volume_type_with_qos(self):
        """
        Creates a Volume Type object with an associated QoS Spec
        """
        self.volume_type_creator = OpenStackVolumeType(
            self.admin_os_creds,
            VolumeTypeConfig(
                name=self.volume_type_name,
                qos_spec_name=self.qos_creator.qos_settings.name))

        vol_type = self.volume_type_creator.create()
        self.assertEqual(self.volume_type_creator.volume_type_settings.name,
                         vol_type.name)
        self.assertEqual(self.volume_type_creator.volume_type_settings.name,
                         vol_type.name)
        self.assertIsNotNone(vol_type.qos_spec)
        self.assertEqual(
            self.volume_type_creator.volume_type_settings.qos_spec_name,
            vol_type.qos_spec.name)
        self.assertIsNone(vol_type.encryption)

        vol_type_query = cinder_utils.get_volume_type_by_id(
            self.cinder, vol_type.id)
        self.assertIsNotNone(vol_type_query)
        self.assertEqual(vol_type, vol_type_query)

    def test_volume_type_with_encryption(self):
        """
        Creates a Volume Type object with encryption
        """
        encryption_settings = VolumeTypeEncryptionConfig(
            name='foo', provider_class='bar',
            control_location=ControlLocation.back_end)
        self.volume_type_creator = OpenStackVolumeType(
            self.admin_os_creds,
            VolumeTypeConfig(
                name=self.volume_type_name,
                encryption=encryption_settings))

        vol_type = self.volume_type_creator.create()
        self.assertEqual(self.volume_type_creator.volume_type_settings.name,
                         vol_type.name)
        self.assertEqual(self.volume_type_creator.volume_type_settings.name,
                         vol_type.name)
        self.assertIsNone(vol_type.qos_spec)
        self.assertIsNotNone(vol_type.encryption)

        self.assertEqual(encryption_settings.control_location.value,
                         vol_type.encryption.control_location)

        vol_type_query = cinder_utils.get_volume_type_by_id(
            self.cinder, vol_type.id)
        self.assertIsNotNone(vol_type_query)
        self.assertEqual(vol_type, vol_type_query)

    def test_volume_type_with_qos_and_encryption(self):
        """
        Creates a Volume Type object with encryption and an associated QoS Spec
        """
        encryption_settings = VolumeTypeEncryptionConfig(
            name='foo', provider_class='bar',
            control_location=ControlLocation.back_end)
        self.volume_type_creator = OpenStackVolumeType(
            self.admin_os_creds,
            VolumeTypeConfig(
                name=self.volume_type_name,
                encryption=encryption_settings,
                qos_spec_name=self.qos_creator.qos_settings.name))

        vol_type = self.volume_type_creator.create()
        self.assertEqual(self.volume_type_creator.volume_type_settings.name,
                         vol_type.name)
        self.assertEqual(self.volume_type_creator.volume_type_settings.name,
                         vol_type.name)
        self.assertIsNotNone(vol_type.qos_spec)
        self.assertEqual(
            self.volume_type_creator.volume_type_settings.qos_spec_name,
            vol_type.qos_spec.name)
        self.assertIsNotNone(vol_type.encryption)

        self.assertEqual(encryption_settings.control_location.value,
                         vol_type.encryption.control_location)

        vol_type_query = cinder_utils.get_volume_type_by_id(
            self.cinder, vol_type.id)
        self.assertIsNotNone(vol_type_query)
        self.assertEqual(vol_type, vol_type_query)
