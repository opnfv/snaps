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
from snaps.config.qos import Consumer, QoSConfigError, QoSConfig
from snaps.openstack.create_qos import Consumer as Consumer_old

try:
    from urllib.request import URLError
except ImportError:
    from urllib2 import URLError

import logging
import unittest
import uuid

from snaps.openstack import create_qos
from snaps.openstack.create_qos import QoSSettings
from snaps.openstack.tests.os_source_file_test import OSIntegrationTestCase
from snaps.openstack.utils import cinder_utils

__author__ = 'spisarski'

logger = logging.getLogger('create_qos_tests')


class QoSSettingsUnitTests(unittest.TestCase):
    """
    Tests the construction of the QoSSettings class
    """

    def test_no_params(self):
        with self.assertRaises(QoSConfigError):
            QoSSettings()

    def test_empty_config(self):
        with self.assertRaises(QoSConfigError):
            QoSSettings(**dict())

    def test_name_only(self):
        with self.assertRaises(QoSConfigError):
            QoSSettings(name='foo')

    def test_config_with_name_only(self):
        with self.assertRaises(QoSConfigError):
            QoSSettings(**{'name': 'foo'})

    def test_invalid_consumer(self):
        with self.assertRaises(QoSConfigError):
            QoSSettings(name='foo', consumer='bar')

    def test_config_with_invalid_consumer(self):
        with self.assertRaises(QoSConfigError):
            QoSSettings(**{'name': 'foo', 'consumer': 'bar'})

    def test_name_consumer(self):
        settings = QoSSettings(name='foo', consumer=Consumer_old.front_end)

        self.assertEqual('foo', settings.name)
        self.assertEqual(Consumer_old.front_end.value, settings.consumer.value)
        self.assertEqual(dict(), settings.specs)

    def test_name_consumer_front_end_strings(self):
        settings = QoSSettings(name='foo', consumer='front-end')

        self.assertEqual('foo', settings.name)
        self.assertEqual(Consumer_old.front_end.value, settings.consumer.value)
        self.assertEqual(dict(), settings.specs)

    def test_name_consumer_back_end_strings(self):
        settings = QoSSettings(name='foo', consumer='back-end')

        self.assertEqual('foo', settings.name)
        self.assertEqual(Consumer_old.back_end.value, settings.consumer.value)
        self.assertEqual(dict(), settings.specs)

    def test_name_consumer_both_strings(self):
        settings = QoSSettings(name='foo', consumer='both')

        self.assertEqual('foo', settings.name)
        self.assertEqual(Consumer_old.both.value, settings.consumer.value)
        self.assertEqual(dict(), settings.specs)

    def test_all(self):
        specs = {'spec1': 'val1', 'spec2': 'val2'}
        settings = QoSSettings(name='foo', consumer=Consumer_old.both,
                               specs=specs)

        self.assertEqual('foo', settings.name)
        self.assertEqual(Consumer_old.both.value, settings.consumer.value)
        self.assertEqual(specs, settings.specs)

    def test_config_all(self):
        settings = QoSSettings(
            **{'name': 'foo', 'consumer': 'both', 'specs': {'spec1': 'val1'}})

        self.assertEqual('foo', settings.name)
        self.assertEqual(Consumer.both, settings.consumer)
        self.assertEqual({'spec1': 'val1'}, settings.specs)


class CreateQoSTests(OSIntegrationTestCase):
    """
    Test for the CreateQoS class defined in create_qos.py
    """

    def setUp(self):
        """
        Instantiates the CreateQoS object that is responsible for
        downloading and creating an OS QoS Spec file within OpenStack
        """
        super(self.__class__, self).__start__()

        guid = uuid.uuid4()
        qos_settings = QoSConfig(
            name=self.__class__.__name__ + '-' + str(guid),
            consumer=Consumer.both)

        self.cinder = cinder_utils.cinder_client(
            self.admin_os_creds, self.admin_os_session)
        self.qos_creator = create_qos.OpenStackQoS(
            self.admin_os_creds, qos_settings)

    def tearDown(self):
        """
        Cleans the Qos Spec
        """
        if self.qos_creator:
            self.qos_creator.clean()

        super(self.__class__, self).__clean__()

    def test_create_qos(self):
        """
        Tests the creation of an OpenStack qos.
        """
        # Create QoS
        created_qos = self.qos_creator.create()
        self.assertIsNotNone(created_qos)

        retrieved_qos = cinder_utils.get_qos(
            self.cinder, qos_settings=self.qos_creator.qos_settings)

        self.assertIsNotNone(retrieved_qos)
        self.assertEqual(created_qos, retrieved_qos)

    def test_create_delete_qos(self):
        """
        Tests the creation then deletion of an OpenStack QoS Spec to ensure
        clean() does not raise an Exception.
        """
        # Create QoS
        created_qos = self.qos_creator.create()
        self.assertIsNotNone(created_qos)

        retrieved_qos = cinder_utils.get_qos(
            self.cinder, qos_settings=self.qos_creator.qos_settings)
        self.assertIsNotNone(retrieved_qos)
        self.assertEqual(created_qos, retrieved_qos)

        # Delete QoS manually
        cinder_utils.delete_qos(self.cinder, created_qos)

        self.assertIsNone(cinder_utils.get_qos(
            self.cinder, qos_settings=self.qos_creator.qos_settings))

        # Must not raise an exception when attempting to cleanup non-existent
        # qos
        self.qos_creator.clean()
        self.assertIsNone(self.qos_creator.get_qos())

    def test_create_same_qos(self):
        """
        Tests the creation of an OpenStack qos when one already exists.
        """
        # Create QoS
        qos1 = self.qos_creator.create()

        retrieved_qos = cinder_utils.get_qos(
            self.cinder, qos_settings=self.qos_creator.qos_settings)
        self.assertEqual(qos1, retrieved_qos)

        # Should be retrieving the instance data
        os_qos_2 = create_qos.OpenStackQoS(
            self.admin_os_creds, self.qos_creator.qos_settings)
        qos2 = os_qos_2.create()
        self.assertEqual(qos1, qos2)
