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

from cinderclient.exceptions import NotFound

from snaps.openstack.create_qos import QoSSettings, Consumer
from snaps.openstack.tests import validation_utils
from snaps.openstack.tests.os_source_file_test import OSComponentTestCase
from snaps.openstack.utils import cinder_utils

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
        cinder = cinder_utils.cinder_client(self.os_creds)
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
        self.cinder = cinder_utils.cinder_client(self.os_creds)

    def tearDown(self):
        """
        Cleans the remote OpenStack objects
        """
        if self.qos:
            try:
                cinder_utils.delete_qos(self.cinder, self.qos)
            except NotFound:
                pass

    def test_create_qos_both(self):
        """
        Tests the cinder_utils.create_qos()
        """
        qos_settings = QoSSettings(name=self.qos_name, specs=self.specs,
                                   consumer=Consumer.both)
        self.qos = cinder_utils.create_qos(
            self.cinder, qos_settings)
        self.assertIsNotNone(self.qos)

        qos1 = cinder_utils.get_qos(self.cinder, qos_settings=qos_settings)
        self.assertIsNotNone(qos1)
        validation_utils.objects_equivalent(self.qos, qos1)

        qos2 = cinder_utils.get_qos(self.cinder, qos_name=qos_settings.name)
        self.assertIsNotNone(qos2)
        validation_utils.objects_equivalent(self.qos, qos2)

    def test_create_qos_front(self):
        """
        Tests the cinder_utils.create_qos()
        """
        qos_settings = QoSSettings(name=self.qos_name, specs=self.specs,
                                   consumer=Consumer.front_end)
        self.qos = cinder_utils.create_qos(
            self.cinder, qos_settings)
        self.assertIsNotNone(self.qos)

        qos1 = cinder_utils.get_qos(self.cinder, qos_settings=qos_settings)
        self.assertIsNotNone(qos1)
        validation_utils.objects_equivalent(self.qos, qos1)

        qos2 = cinder_utils.get_qos(self.cinder, qos_name=qos_settings.name)
        self.assertIsNotNone(qos2)
        validation_utils.objects_equivalent(self.qos, qos2)

    def test_create_qos_back(self):
        """
        Tests the cinder_utils.create_qos()
        """
        qos_settings = QoSSettings(name=self.qos_name, specs=self.specs,
                                   consumer=Consumer.back_end)
        self.qos = cinder_utils.create_qos(
            self.cinder, qos_settings)
        self.assertIsNotNone(self.qos)

        qos1 = cinder_utils.get_qos(self.cinder, qos_settings=qos_settings)
        self.assertIsNotNone(qos1)
        validation_utils.objects_equivalent(self.qos, qos1)

        qos2 = cinder_utils.get_qos(self.cinder, qos_name=qos_settings.name)
        self.assertIsNotNone(qos2)
        validation_utils.objects_equivalent(self.qos, qos2)

    def test_create_delete_qos(self):
        """
        Tests the cinder_utils.create_qos()
        """
        qos_settings = QoSSettings(name=self.qos_name, consumer=Consumer.both)
        self.qos = cinder_utils.create_qos(
            self.cinder, qos_settings)
        self.assertIsNotNone(self.qos)
        self.assertEqual(self.qos_name, self.qos.name)

        qos = cinder_utils.get_qos(
            self.cinder, qos_settings=qos_settings)
        self.assertIsNotNone(qos)
        validation_utils.objects_equivalent(self.qos, qos)

        cinder_utils.delete_qos(self.cinder, self.qos)
        self.assertIsNone(cinder_utils.get_qos(
            self.cinder, qos_settings=qos_settings))
