# Copyright (c) 2016 Cable Television Laboratories, Inc. ("CableLabs")
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
import os
import uuid

from Crypto.PublicKey import RSA

from snaps.openstack.utils import nova_utils
from snaps.openstack.tests.os_source_file_test import OSComponentTestCase
from snaps.openstack.create_flavor import FlavorSettings

__author__ = 'spisarski'

logger = logging.getLogger('nova_utils_tests')


class NovaSmokeTests(OSComponentTestCase):
    """
    Tests to ensure that the nova client can communicate with the cloud
    """

    def test_nova_connect_success(self):
        """
        Tests to ensure that the proper credentials can connect.
        """
        nova = nova_utils.nova_client(self.os_creds)

        # This should not throw an exception
        nova.flavors.list()

    def test_nova_connect_fail(self):
        """
        Tests to ensure that the improper credentials cannot connect.
        """
        from snaps.openstack.os_credentials import OSCreds

        nova = nova_utils.nova_client(
            OSCreds(username='user', password='pass', auth_url=self.os_creds.auth_url,
                    project_name=self.os_creds.project_name, proxy_settings=self.os_creds.proxy_settings))

        # This should throw an exception
        with self.assertRaises(Exception):
            nova.flavors.list()


class NovaUtilsKeypairTests(OSComponentTestCase):
    """
    Test basic nova keypair functionality
    """

    def setUp(self):
        """
        Instantiates the CreateImage object that is responsible for downloading and creating an OS image file
        within OpenStack
        """
        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.priv_key_file_path = 'tmp/' + guid
        self.pub_key_file_path = self.priv_key_file_path + '.pub'

        self.nova = nova_utils.nova_client(self.os_creds)
        self.keys = RSA.generate(1024)
        self.public_key = self.keys.publickey().exportKey('OpenSSH')
        self.keypair_name = guid
        self.keypair = None
        self.floating_ip = None

    def tearDown(self):
        """
        Cleans the image and downloaded image file
        """
        if self.keypair:
            try:
                nova_utils.delete_keypair(self.nova, self.keypair)
            except:
                pass

        try:
            os.remove(self.priv_key_file_path)
        except:
            pass

        try:
            os.remove(self.pub_key_file_path)
        except:
            pass

        if self.floating_ip:
            nova_utils.delete_floating_ip(self.nova, self.floating_ip)

    def test_create_keypair(self):
        """
        Tests the creation of an OpenStack keypair that does not exist.
        """
        self.keypair = nova_utils.upload_keypair(self.nova, self.keypair_name, self.public_key)
        result = nova_utils.keypair_exists(self.nova, self.keypair)
        self.assertEquals(self.keypair, result)
        keypair = nova_utils.get_keypair_by_name(self.nova, self.keypair_name)
        self.assertEquals(self.keypair, keypair)

    def test_create_delete_keypair(self):
        """
        Tests the creation of an OpenStack keypair that does not exist.
        """
        self.keypair = nova_utils.upload_keypair(self.nova, self.keypair_name, self.public_key)
        result = nova_utils.keypair_exists(self.nova, self.keypair)
        self.assertEquals(self.keypair, result)
        nova_utils.delete_keypair(self.nova, self.keypair)
        result2 = nova_utils.keypair_exists(self.nova, self.keypair)
        self.assertIsNone(result2)

    def test_create_key_from_file(self):
        """
        Tests that the generated RSA keys are properly saved to files
        :return:
        """
        nova_utils.save_keys_to_files(self.keys, self.pub_key_file_path, self.priv_key_file_path)
        self.keypair = nova_utils.upload_keypair_file(self.nova, self.keypair_name, self.pub_key_file_path)
        pub_key = open(os.path.expanduser(self.pub_key_file_path)).read()
        self.assertEquals(self.keypair.public_key, pub_key)

    def test_floating_ips(self):
        """
        Tests the creation of a floating IP
        :return:
        """
        ips = nova_utils.get_floating_ips(self.nova)
        self.assertIsNotNone(ips)

        self.floating_ip = nova_utils.create_floating_ip(self.nova, self.ext_net_name)
        returned = nova_utils.get_floating_ip(self.nova, self.floating_ip)
        self.assertEquals(self.floating_ip, returned)


class NovaUtilsFlavorTests(OSComponentTestCase):
    """
    Test basic nova flavor functionality
    """

    def setUp(self):
        """
        Instantiates the CreateImage object that is responsible for downloading and creating an OS image file
        within OpenStack
        """
        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.flavor_settings = FlavorSettings(name=guid + '-name', flavor_id=guid + '-id', ram=1, disk=1, vcpus=1,
                                              ephemeral=1, swap=2, rxtx_factor=3.0, is_public=False)
        self.nova = nova_utils.nova_client(self.os_creds)
        self.flavor = None

    def tearDown(self):
        """
        Cleans the image and downloaded image file
        """
        if self.flavor:
            try:
                nova_utils.delete_flavor(self.nova, self.flavor)
            except:
                pass

    def test_create_flavor(self):
        """
        Tests the creation of an OpenStack keypair that does not exist.
        """
        self.flavor = nova_utils.create_flavor(self.nova, self.flavor_settings)
        self.validate_flavor()

    def test_create_delete_flavor(self):
        """
        Tests the creation of an OpenStack keypair that does not exist.
        """
        self.flavor = nova_utils.create_flavor(self.nova, self.flavor_settings)
        self.validate_flavor()
        nova_utils.delete_flavor(self.nova, self.flavor)
        flavor = nova_utils.get_flavor_by_name(self.nova, self.flavor_settings.name)
        self.assertIsNone(flavor)

    def validate_flavor(self):
        """
        Validates the flavor_settings against the OpenStack flavor object
        """
        self.assertIsNotNone(self.flavor)
        self.assertEquals(self.flavor_settings.name, self.flavor.name)
        self.assertEquals(self.flavor_settings.flavor_id, self.flavor.id)
        self.assertEquals(self.flavor_settings.ram, self.flavor.ram)
        self.assertEquals(self.flavor_settings.disk, self.flavor.disk)
        self.assertEquals(self.flavor_settings.vcpus, self.flavor.vcpus)
        self.assertEquals(self.flavor_settings.ephemeral, self.flavor.ephemeral)

        if self.flavor_settings.swap == 0:
            self.assertEquals('', self.flavor.swap)
        else:
            self.assertEquals(self.flavor_settings.swap, self.flavor.swap)

        self.assertEquals(self.flavor_settings.rxtx_factor, self.flavor.rxtx_factor)
        self.assertEquals(self.flavor_settings.is_public, self.flavor.is_public)
