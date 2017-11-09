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

from snaps.openstack.os_credentials import OSCreds
from snaps.openstack.tests.os_source_file_test import OSComponentTestCase
from snaps.openstack.utils import magnum_utils

__author__ = 'spisarski'

logger = logging.getLogger('nova_utils_tests')


class MagnumSmokeTests(OSComponentTestCase):
    """
    Tests to ensure that the magnum client can communicate with the cloud
    """

    def test_connect_success(self):
        """
        Tests to ensure that the proper credentials can connect.
        """
        magnum = magnum_utils.magnum_client(self.os_creds)

        # This should not throw an exception
        magnum.clusters.list()

    def test_nova_connect_fail(self):
        """
        Tests to ensure that the improper credentials cannot connect.
        """

        with self.assertRaises(RuntimeError):
            magnum_utils.magnum_client(
                OSCreds(username='user', password='pass',
                        auth_url=self.os_creds.auth_url,
                        project_name=self.os_creds.project_name,
                        proxy_settings=self.os_creds.proxy_settings))
