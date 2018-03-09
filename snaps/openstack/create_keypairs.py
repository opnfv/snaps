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

from snaps import file_utils
from snaps.config.keypair import KeypairConfig
from snaps.openstack.openstack_creator import OpenStackComputeObject
from snaps.openstack.utils import nova_utils

__author__ = 'spisarski'

logger = logging.getLogger('OpenStackKeypair')


class OpenStackKeypair(OpenStackComputeObject):
    """
    Class responsible for managing a keypair in OpenStack
    """

    def __init__(self, os_creds, keypair_settings):
        """
        Constructor - all parameters are required
        :param os_creds: The credentials to connect with OpenStack
        :param keypair_settings: a KeypairConfig object
        """
        super(self.__class__, self).__init__(os_creds)

        self.keypair_settings = keypair_settings
        self.__delete_keys_on_clean = True

        # Attributes instantiated on create()
        self.__keypair = None

    def initialize(self):
        """
        Loads the existing OpenStack Keypair
        :return: The Keypair domain object or None
        """
        super(self.__class__, self).initialize()

        try:
            self.__keypair = nova_utils.get_keypair_by_name(
                self._nova, self.keypair_settings.name)
            return self.__keypair
        except Exception as e:
            logger.warn('Cannot load existing keypair - %s', e)

    def create(self):
        """
        Responsible for creating the keypair object.
        :return: The Keypair domain object or None
        """
        self.initialize()

        if not self.__keypair:
            logger.info('Creating keypair %s...' % self.keypair_settings.name)

            if self.keypair_settings.public_filepath and os.path.isfile(
                    self.keypair_settings.public_filepath):
                logger.info("Uploading existing keypair")
                self.__keypair = nova_utils.upload_keypair_file(
                    self._nova, self.keypair_settings.name,
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
                    self._nova, self.keypair_settings.name,
                    nova_utils.public_key_openssh(keys))
                file_utils.save_keys_to_files(
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
                nova_utils.delete_keypair(self._nova, self.__keypair)
            except NotFound:
                pass
            self.__keypair = None

        if self.__delete_keys_on_clean:
            if (self.keypair_settings.public_filepath and
                    file_utils.file_exists(
                        self.keypair_settings.public_filepath)):
                expanded_path = os.path.expanduser(
                    self.keypair_settings.public_filepath)
                os.chmod(expanded_path, 0o755)
                os.remove(expanded_path)
                logger.info('Deleted public key file [%s]', expanded_path)
            if (self.keypair_settings.private_filepath and
                    file_utils.file_exists(
                        self.keypair_settings.private_filepath)):
                expanded_path = os.path.expanduser(
                    self.keypair_settings.private_filepath)
                os.chmod(expanded_path, 0o755)
                os.remove(expanded_path)
                logger.info('Deleted private key file [%s]', expanded_path)

        super(self.__class__, self).clean()

    def get_keypair(self):
        """
        Returns the OpenStack keypair object
        :return:
        """
        return self.__keypair


class KeypairSettings(KeypairConfig):
    """
    Class representing a keypair configuration
    """

    def __init__(self, **kwargs):
        from warnings import warn
        warn('Use snaps.config.keypair.KeypairConfig instead',
             DeprecationWarning)
        super(self.__class__, self).__init__(**kwargs)
