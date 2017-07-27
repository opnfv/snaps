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

import os
from neutronclient.common.utils import str2bool
from novaclient.exceptions import NotFound

from snaps import file_utils
from snaps.openstack.utils import nova_utils

__author__ = 'spisarski'

logger = logging.getLogger('OpenStackKeypair')


class OpenStackKeypair:
    """
    Class responsible for creating a keypair in OpenStack
    """

    def __init__(self, os_creds, keypair_settings):
        """
        Constructor - all parameters are required
        :param os_creds: The credentials to connect with OpenStack
        :param keypair_settings: The settings used to create a keypair
        """
        self.__nova = None
        self.__os_creds = os_creds
        self.keypair_settings = keypair_settings
        self.__nova = nova_utils.nova_client(os_creds)
        self.__delete_keys_on_clean = True

        # Attributes instantiated on create()
        self.__keypair = None

    def create(self, cleanup=False):
        """
        Responsible for creating the keypair object.
        :param cleanup: Denotes whether or not this is being called for cleanup
                        or not
        """
        self.__nova = nova_utils.nova_client(self.__os_creds)

        logger.info('Creating keypair %s...' % self.keypair_settings.name)

        self.__keypair = nova_utils.get_keypair_by_name(
            self.__nova, self.keypair_settings.name)

        if not self.__keypair and not cleanup:
            if self.keypair_settings.public_filepath and os.path.isfile(
                    self.keypair_settings.public_filepath):
                logger.info("Uploading existing keypair")
                self.__keypair = nova_utils.upload_keypair_file(
                    self.__nova, self.keypair_settings.name,
                    self.keypair_settings.public_filepath)

                if self.keypair_settings.delete_on_clean is not None:
                    delete_on_clean = self.keypair_settings.delete_on_clean
                    self.__delete_keys_on_clean = delete_on_clean
                else:
                    self.__delete_keys_on_clean = False
            else:
                logger.info("Creating new keypair")
                keys = nova_utils.create_keys(self.keypair_settings.key_size)
                self.__keypair = nova_utils.upload_keypair(
                    self.__nova, self.keypair_settings.name,
                    nova_utils.public_key_openssh(keys))
                nova_utils.save_keys_to_files(
                    keys, self.keypair_settings.public_filepath,
                    self.keypair_settings.private_filepath)

                if self.keypair_settings.delete_on_clean is not None:
                    delete_on_clean = self.keypair_settings.delete_on_clean
                    self.__delete_keys_on_clean = delete_on_clean
                else:
                    self.__delete_keys_on_clean = True
        elif self.__keypair and not os.path.isfile(
                self.keypair_settings.private_filepath):
            logger.warn("The public key already exist in OpenStack \
                        but the private key file is not found ..")

        return self.__keypair

    def clean(self):
        """
        Removes and deletes the keypair.
        """
        if self.__keypair:
            try:
                nova_utils.delete_keypair(self.__nova, self.__keypair)
            except NotFound:
                pass
            self.__keypair = None

        if self.__delete_keys_on_clean:
            if (self.keypair_settings.public_filepath and
                    file_utils.file_exists(
                        self.keypair_settings.public_filepath)):
                os.chmod(self.keypair_settings.public_filepath, 0o777)
                os.remove(self.keypair_settings.public_filepath)
            if (self.keypair_settings.private_filepath and
                    file_utils.file_exists(
                        self.keypair_settings.private_filepath)):
                os.chmod(self.keypair_settings.private_filepath, 0o777)
                os.remove(self.keypair_settings.private_filepath)

    def get_keypair(self):
        """
        Returns the OpenStack keypair object
        :return:
        """
        return self.__keypair


class KeypairSettings:
    """
    Class representing a keypair configuration
    """

    def __init__(self, **kwargs):
        """
        Constructor - all parameters are optional
        :param name: The keypair name.
        :param public_filepath: The path to/from the filesystem where the
                                public key file is or will be stored
        :param private_filepath: The path where the generated private key file
                                 will be stored
        :param key_size: The number of bytes for the key size when it needs to
                         be generated (Must be >=512 default 1024)
        :param delete_on_clean: when True, the key files will be deleted when
                                OpenStackKeypair#clean() is called
        :return:
        """

        self.name = kwargs.get('name')
        self.public_filepath = kwargs.get('public_filepath')
        self.private_filepath = kwargs.get('private_filepath')
        self.key_size = int(kwargs.get('key_size', 1024))

        if kwargs.get('delete_on_clean') is not None:
            if isinstance(kwargs.get('delete_on_clean'), bool):
                self.delete_on_clean = kwargs.get('delete_on_clean')
            else:
                self.delete_on_clean = str2bool(kwargs.get('delete_on_clean'))
        else:
            self.delete_on_clean = None

        if not self.name:
            raise KeypairSettingsError('Name is a required attribute')

        if self.key_size < 512:
            raise KeypairSettingsError('key_size must be >=512')


class KeypairSettingsError(Exception):
    """
    Exception to be thrown when keypair settings are incorrect
    """
