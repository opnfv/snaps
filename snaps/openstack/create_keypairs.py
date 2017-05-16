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

from novaclient.exceptions import NotFound

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

        # Attributes instantiated on create()
        self.__keypair = None

    def create(self, cleanup=False):
        """
        Responsible for creating the keypair object.
        :param cleanup: Denotes whether or not this is being called for cleanup or not
        """
        self.__nova = nova_utils.nova_client(self.__os_creds)

        logger.info('Creating keypair %s...' % self.keypair_settings.name)

        self.__keypair = nova_utils.get_keypair_by_name(self.__nova, self.keypair_settings.name)

        if not self.__keypair and not cleanup:
            if self.keypair_settings.public_filepath and os.path.isfile(self.keypair_settings.public_filepath):
                logger.info("Uploading existing keypair")
                self.__keypair = nova_utils.upload_keypair_file(self.__nova, self.keypair_settings.name,
                                                                self.keypair_settings.public_filepath)
            else:
                logger.info("Creating new keypair")
                # TODO - Make this value configurable
                keys = nova_utils.create_keys(1024)
                self.__keypair = nova_utils.upload_keypair(self.__nova, self.keypair_settings.name,
                                                           nova_utils.public_key_openssh(keys))
                nova_utils.save_keys_to_files(keys, self.keypair_settings.public_filepath,
                                              self.keypair_settings.private_filepath)

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

    def __init__(self, config=None, name=None, public_filepath=None, private_filepath=None):
        """
        Constructor - all parameters are optional
        :param config: Should be a dict object containing the configuration settings using the attribute names below
                       as each member's the key and overrides any of the other parameters.
        :param name: The keypair name.
        :param public_filepath: The path to/from the filesystem where the public key file is or will be stored
        :param private_filepath: The path where the generated private key file will be stored
        :return:
        """

        if config:
            self.name = config.get('name')
            self.public_filepath = config.get('public_filepath')
            self.private_filepath = config.get('private_filepath')
        else:
            self.name = name
            self.public_filepath = public_filepath
            self.private_filepath = private_filepath

        if not self.name:
            raise Exception('The attributes name, public_filepath, and private_filepath are required')
