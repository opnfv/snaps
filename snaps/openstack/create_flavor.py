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

from novaclient.exceptions import NotFound

from snaps.openstack.utils import nova_utils

__author__ = 'spisarski'

logger = logging.getLogger('create_flavor')

MEM_PAGE_SIZE_ANY = {'hw:mem_page_size': 'any'}
MEM_PAGE_SIZE_LARGE = {'hw:mem_page_size': 'large'}


class OpenStackFlavor:
    """
    Class responsible for creating a user in OpenStack
    """

    def __init__(self, os_creds, flavor_settings):
        """
        Constructor
        :param os_creds: The OpenStack connection credentials
        :param flavor_settings: The flavor settings
        :return:
        """
        self.__os_creds = os_creds
        self.flavor_settings = flavor_settings
        self.__flavor = None
        self.__nova = None

    def create(self, cleanup=False):
        """
        Creates the image in OpenStack if it does not already exist
        :param cleanup: Denotes whether or not this is being called for cleanup
                        or not
        :return: The OpenStack flavor object
        """
        self.__nova = nova_utils.nova_client(self.__os_creds)
        self.__flavor = nova_utils.get_flavor_by_name(
            self.__nova, self.flavor_settings.name)
        if self.__flavor:
            logger.info(
                'Found flavor with name - ' + self.flavor_settings.name)
        elif not cleanup:
            self.__flavor = nova_utils.create_flavor(
                self.__nova, self.flavor_settings)
            if self.flavor_settings.metadata:
                nova_utils.set_flavor_keys(self.__nova, self.__flavor,
                                           self.flavor_settings.metadata)
        else:
            logger.info('Did not create flavor due to cleanup mode')

        return self.__flavor

    def clean(self):
        """
        Cleanse environment of all artifacts
        :return: void
        """
        if self.__flavor:
            try:
                nova_utils.delete_flavor(self.__nova, self.__flavor)
            except NotFound:
                pass

            self.__flavor = None

    def get_flavor(self):
        """
        Returns the OpenStack flavor object
        :return:
        """
        return self.__flavor


class FlavorSettings:
    """
    Configuration settings for OpenStack flavor creation
    """

    def __init__(self, **kwargs):
        """
        Constructor
        :param config: dict() object containing the configuration settings
                       using the attribute names below as each member's the
                       key and overrides any of the other parameters.
        :param name: the flavor's name (required)
        :param flavor_id: the string ID (default 'auto')
        :param ram: the required RAM in MB (required)
        :param disk: the size of the root disk in GB (required)
        :param vcpus: the number of virtual CPUs (required)
        :param ephemeral: the size of the ephemeral disk in GB (default 0)
        :param swap: the size of the dedicated swap disk in GB (default 0)
        :param rxtx_factor: the receive/transmit factor to be set on ports if
                            backend supports QoS extension (default 1.0)
        :param is_public: denotes whether or not the flavor is public
                          (default True)
        :param metadata: freeform dict() for special metadata
        """
        self.name = kwargs.get('name')

        if kwargs.get('flavor_id'):
            self.flavor_id = kwargs['flavor_id']
        else:
            self.flavor_id = 'auto'

        self.ram = kwargs.get('ram')
        self.disk = kwargs.get('disk')
        self.vcpus = kwargs.get('vcpus')

        if kwargs.get('ephemeral'):
            self.ephemeral = kwargs['ephemeral']
        else:
            self.ephemeral = 0

        if kwargs.get('swap'):
            self.swap = kwargs['swap']
        else:
            self.swap = 0

        if kwargs.get('rxtx_factor'):
            self.rxtx_factor = kwargs['rxtx_factor']
        else:
            self.rxtx_factor = 1.0

        if kwargs.get('is_public') is not None:
            self.is_public = kwargs['is_public']
        else:
            self.is_public = True

        if kwargs.get('metadata'):
            self.metadata = kwargs['metadata']
        else:
            self.metadata = None

        if not self.name or not self.ram or not self.disk or not self.vcpus:
            raise FlavorSettingsError(
                'The attributes name, ram, disk, and vcpus are required for'
                'FlavorSettings')

        if not isinstance(self.ram, int):
            raise FlavorSettingsError('The ram attribute must be a integer')

        if not isinstance(self.disk, int):
            raise FlavorSettingsError('The ram attribute must be a integer')

        if not isinstance(self.vcpus, int):
            raise FlavorSettingsError('The vcpus attribute must be a integer')

        if self.ephemeral and not isinstance(self.ephemeral, int):
            raise FlavorSettingsError(
                'The ephemeral attribute must be an integer')

        if self.swap and not isinstance(self.swap, int):
            raise FlavorSettingsError('The swap attribute must be an integer')

        if self.rxtx_factor and not isinstance(self.rxtx_factor, (int, float)):
            raise FlavorSettingsError(
                'The is_public attribute must be an integer or float')

        if self.is_public and not isinstance(self.is_public, bool):
            raise FlavorSettingsError(
                'The is_public attribute must be a boolean')


class FlavorSettingsError(Exception):
    """
    Exception to be thrown when an flavor settings are incorrect
    """
