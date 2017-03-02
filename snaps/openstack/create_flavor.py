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

logger = logging.getLogger('create_image')

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
        self.__nova = nova_utils.nova_client(self.__os_creds)

    def create(self, cleanup=False):
        """
        Creates the image in OpenStack if it does not already exist
        :param cleanup: Denotes whether or not this is being called for cleanup or not
        :return: The OpenStack flavor object
        """
        self.__flavor = nova_utils.get_flavor_by_name(self.__nova, self.flavor_settings.name)
        if self.__flavor:
            logger.info('Found flavor with name - ' + self.flavor_settings.name)
        elif not cleanup:
            self.__flavor = nova_utils.create_flavor(self.__nova, self.flavor_settings)
            if self.flavor_settings.metadata:
                self.__flavor.set_keys(self.flavor_settings.metadata)
            self.__flavor = nova_utils.get_flavor_by_name(self.__nova, self.flavor_settings.name)
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

    def __init__(self, config=None, name=None, flavor_id='auto', ram=None, disk=None, vcpus=None, ephemeral=0, swap=0,
                 rxtx_factor=1.0, is_public=True, metadata=None):
        """
        Constructor
        :param config: dict() object containing the configuration settings using the attribute names below as each
                       member's the key and overrides any of the other parameters.
        :param name: the flavor's name (required)
        :param flavor_id: the string ID (default 'auto')
        :param ram: the required RAM in MB (required)
        :param disk: the size of the root disk in GB (required)
        :param vcpus: the number of virtual CPUs (required)
        :param ephemeral: the size of the ephemeral disk in GB (default 0)
        :param swap: the size of the dedicated swap disk in GB (default 0)
        :param rxtx_factor: the receive/transmit factor to be set on ports if backend supports
                            QoS extension (default 1.0)
        :param is_public: denotes whether or not the flavor is public (default True)
        :param metadata: freeform dict() for special metadata (default hw:mem_page_size=any)
        """

        if config:
            self.name = config.get('name')

            if config.get('flavor_id'):
                self.flavor_id = config['flavor_id']
            else:
                self.flavor_id = flavor_id

            self.ram = config.get('ram')
            self.disk = config.get('disk')
            self.vcpus = config.get('vcpus')

            if config.get('ephemeral'):
                self.ephemeral = config['ephemeral']
            else:
                self.ephemeral = ephemeral

            if config.get('swap'):
                self.swap = config['swap']
            else:
                self.swap = swap

            if config.get('rxtx_factor'):
                self.rxtx_factor = config['rxtx_factor']
            else:
                self.rxtx_factor = rxtx_factor

            if config.get('is_public') is not None:
                self.is_public = config['is_public']
            else:
                self.is_public = is_public

            if config.get('metadata'):
                self.metadata = config['metadata']
            else:
                self.metadata = metadata
        else:
            self.name = name
            self.flavor_id = flavor_id
            self.ram = ram
            self.disk = disk
            self.vcpus = vcpus
            self.ephemeral = ephemeral
            self.swap = swap
            self.rxtx_factor = rxtx_factor
            self.is_public = is_public
            self.metadata = metadata

        if not self.name or not self.ram or not self.disk or not self.vcpus:
            raise Exception('The attributes name, ram, disk, and vcpus are required for FlavorSettings')

        if not isinstance(self.ram, int):
            raise Exception('The ram attribute must be a integer')

        if not isinstance(self.disk, int):
            raise Exception('The ram attribute must be a integer')

        if not isinstance(self.vcpus, int):
            raise Exception('The vcpus attribute must be a integer')

        if self.ephemeral and not isinstance(self.ephemeral, int):
            raise Exception('The ephemeral attribute must be an integer')

        if self.swap and not isinstance(self.swap, int):
            raise Exception('The swap attribute must be an integer')

        if self.rxtx_factor and not isinstance(self.rxtx_factor, (int, float)):
            raise Exception('The is_public attribute must be an integer or float')

        if self.is_public and not isinstance(self.is_public, bool):
            raise Exception('The is_public attribute must be a boolean')
