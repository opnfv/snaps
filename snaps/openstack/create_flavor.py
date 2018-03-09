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

from snaps.config.flavor import FlavorConfig
from snaps.openstack.openstack_creator import OpenStackComputeObject
from snaps.openstack.utils import nova_utils

__author__ = 'spisarski'

logger = logging.getLogger('create_flavor')

MEM_PAGE_SIZE_ANY = {'hw:mem_page_size': 'any'}
MEM_PAGE_SIZE_LARGE = {'hw:mem_page_size': 'large'}


class OpenStackFlavor(OpenStackComputeObject):
    """
    Class responsible for creating a user in OpenStack
    """

    def __init__(self, os_creds, flavor_settings):
        """
        Constructor
        :param os_creds: The OpenStack connection credentials
        :param flavor_settings: a FlavorConfig instance
        :return:
        """
        super(self.__class__, self).__init__(os_creds)

        self.flavor_settings = flavor_settings
        self.__flavor = None

    def initialize(self):
        """
        Loads the existing OpenStack flavor
        :return: The Flavor domain object or None
        """
        super(self.__class__, self).initialize()

        self.__flavor = nova_utils.get_flavor_by_name(
            self._nova, self.flavor_settings.name)
        if self.__flavor:
            logger.info('Found flavor with name - %s',
                        self.flavor_settings.name)
        return self.__flavor

    def create(self):
        """
        Creates the image in OpenStack if it does not already exist
        :return: The OpenStack flavor object
        """
        self.initialize()
        if not self.__flavor:
            self.__flavor = nova_utils.create_flavor(
                self._nova, self.flavor_settings)
            if self.flavor_settings.metadata:
                nova_utils.set_flavor_keys(self._nova, self.__flavor,
                                           self.flavor_settings.metadata)

        return self.__flavor

    def clean(self):
        """
        Cleanse environment of all artifacts
        :return: void
        """
        if self.__flavor:
            try:
                nova_utils.delete_flavor(self._nova, self.__flavor)
            except NotFound:
                pass

            self.__flavor = None

        super(self.__class__, self).clean()

    def get_flavor(self):
        """
        Returns the OpenStack flavor object
        :return:
        """
        return self.__flavor


class FlavorSettings(FlavorConfig):
    """
    Configuration settings for OpenStack flavor creation
    """

    def __init__(self, **kwargs):
        from warnings import warn
        warn('Use snaps.config.flavor.FlavorConfig instead',
             DeprecationWarning)
        super(self.__class__, self).__init__(**kwargs)
