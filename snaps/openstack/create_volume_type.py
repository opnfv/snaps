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

from cinderclient.exceptions import NotFound

from snaps.config.volume_type import (
    VolumeTypeConfig,  VolumeTypeEncryptionConfig)
from snaps.openstack.openstack_creator import OpenStackVolumeObject
from snaps.openstack.utils import cinder_utils

__author__ = 'spisarski'

logger = logging.getLogger('create_volume_type')


class OpenStackVolumeType(OpenStackVolumeObject):
    """
    Class responsible for managing an volume in OpenStack
    """

    def __init__(self, os_creds, volume_type_settings):
        """
        Constructor
        :param os_creds: The OpenStack connection credentials
        :param volume_type_settings: The volume type settings
        :return:
        """
        super(self.__class__, self).__init__(os_creds)

        self.volume_type_settings = volume_type_settings
        self.__volume_type = None

    def initialize(self):
        """
        Loads the existing Volume
        :return: The Volume domain object or None
        """
        super(self.__class__, self).initialize()

        self.__volume_type = cinder_utils.get_volume_type(
            self._cinder, volume_type_settings=self.volume_type_settings)

        return self.__volume_type

    def create(self):
        """
        Creates the volume in OpenStack if it does not already exist and
        returns the domain Volume object
        :return: The Volume domain object or None
        """
        self.initialize()

        if not self.__volume_type:
            self.__volume_type = cinder_utils.create_volume_type(
                self._cinder, self.volume_type_settings)
            logger.info(
                'Created volume type with name - %s',
                self.volume_type_settings.name)

        return self.__volume_type

    def clean(self):
        """
        Cleanse environment of all artifacts
        :return: void
        """
        if self.__volume_type:
            try:
                cinder_utils.delete_volume_type(self._cinder,
                                                self.__volume_type)
            except NotFound:
                pass

        self.__volume_type = None

        super(self.__class__, self).clean()

    def get_volume_type(self):
        """
        Returns the domain Volume object as it was populated when create() was
        called
        :return: the object
        """
        return self.__volume_type


class VolumeTypeSettings(VolumeTypeConfig):
    """
    Class to hold the configuration settings required for creating OpenStack
    Volume Type objects
    deprecated
    """

    def __init__(self, **kwargs):
        from warnings import warn
        warn('Use snaps.config.volume_type.VolumeTypeConfig instead',
             DeprecationWarning)
        super(self.__class__, self).__init__(**kwargs)


class VolumeTypeEncryptionSettings(VolumeTypeEncryptionConfig):
    """
    Class to hold the configuration settings required for creating OpenStack
    Volume Type Encryption objects
    deprecated
    """

    def __init__(self, **kwargs):
        from warnings import warn
        warn('Use snaps.config.volume_type.VolumeTypeEncryptionConfig instead',
             DeprecationWarning)
        super(self.__class__, self).__init__(**kwargs)


class VolumeTypeCreationError(Exception):
    """
    Exception to be thrown when an volume cannot be created
    """

    def __init__(self, message):
        Exception.__init__(self, message)
