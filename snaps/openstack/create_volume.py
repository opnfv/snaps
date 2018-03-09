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
import time

from cinderclient.exceptions import NotFound

from snaps.config.volume import VolumeConfig
from snaps.openstack.openstack_creator import OpenStackVolumeObject
from snaps.openstack.utils import cinder_utils

__author__ = 'spisarski'

logger = logging.getLogger('create_volume')

VOLUME_ACTIVE_TIMEOUT = 300
VOLUME_DELETE_TIMEOUT = 60
POLL_INTERVAL = 3
STATUS_ACTIVE = 'available'
STATUS_IN_USE = 'in-use'
STATUS_FAILED = 'error'
STATUS_DELETED = 'deleted'


class OpenStackVolume(OpenStackVolumeObject):
    """
    Class responsible for managing an volume in OpenStack
    """

    def __init__(self, os_creds, volume_settings):
        """
        Constructor
        :param os_creds: The OpenStack connection credentials
        :param volume_settings: The volume settings
        :return:
        """
        super(self.__class__, self).__init__(os_creds)

        self.volume_settings = volume_settings
        self.__volume = None

    def initialize(self):
        """
        Loads the existing Volume
        :return: The Volume domain object or None
        """
        super(self.__class__, self).initialize()

        self.__volume = cinder_utils.get_volume(
            self._cinder, self._keystone,
            volume_settings=self.volume_settings,
            project_name=self._os_creds.project_name)
        return self.__volume

    def create(self, block=False):
        """
        Creates the volume in OpenStack if it does not already exist and
        returns the domain Volume object
        :return: The Volume domain object or None
        """
        self.initialize()

        if not self.__volume:
            self.__volume = cinder_utils.create_volume(
                self._cinder, self._keystone, self.volume_settings)

            logger.info(
                'Created volume with name - %s', self.volume_settings.name)
            if self.__volume:
                if block:
                    if self.volume_active(block=True):
                        logger.info('Volume is now active with name - %s',
                                    self.volume_settings.name)
                        return self.__volume
                    else:
                        raise VolumeCreationError(
                            'Volume was not created or activated in the '
                            'alloted amount of time')
        else:
            logger.info('Did not create volume due to cleanup mode')

        return self.__volume

    def clean(self):
        """
        Cleanse environment of all artifacts
        :return: void
        """
        if self.__volume:
            try:
                if self.volume_active():
                    cinder_utils.delete_volume(self._cinder, self.__volume)
                else:
                    logger.warn('Timeout waiting to delete volume %s',
                                self.__volume.name)
            except NotFound:
                pass

            try:
                if self.volume_deleted(block=True):
                    logger.info(
                        'Volume has been properly deleted with name - %s',
                        self.volume_settings.name)
                    self.__vm = None
                else:
                    logger.error(
                        'Volume not deleted within the timeout period of %s '
                        'seconds', VOLUME_DELETE_TIMEOUT)
            except Exception as e:
                logger.error(
                    'Unexpected error while checking VM instance status - %s',
                    e)

        self.__volume = None

        super(self.__class__, self).clean()

    def get_volume(self):
        """
        Returns the domain Volume object as it was populated when create() was
        called
        :return: the object
        """
        return self.__volume

    def volume_active(self, block=False, timeout=VOLUME_ACTIVE_TIMEOUT,
                      poll_interval=POLL_INTERVAL):
        """
        Returns true when the volume status returns the value of
        expected_status_code
        :param block: When true, thread will block until active or timeout
                      value in seconds has been exceeded (False)
        :param timeout: The timeout value
        :param poll_interval: The polling interval in seconds
        :return: T/F
        """
        return self._volume_status_check(STATUS_ACTIVE, block, timeout,
                                         poll_interval)

    def volume_in_use(self):
        """
        Returns true when the volume status returns the value of
        expected_status_code
        :return: T/F
        """
        return self._volume_status_check(STATUS_IN_USE, False, 0, 0)

    def volume_deleted(self, block=False, poll_interval=POLL_INTERVAL):
        """
        Returns true when the VM status returns the value of
        expected_status_code or instance retrieval throws a NotFound exception.
        :param block: When true, thread will block until active or timeout
                      value in seconds has been exceeded (False)
        :param poll_interval: The polling interval in seconds
        :return: T/F
        """
        try:
            return self._volume_status_check(
                STATUS_DELETED, block, VOLUME_DELETE_TIMEOUT, poll_interval)
        except NotFound as e:
            logger.debug(
                "Volume not found when querying status for %s with message "
                "%s", STATUS_DELETED, e)
            return True

    def _volume_status_check(self, expected_status_code, block, timeout,
                             poll_interval):
        """
        Returns true when the volume status returns the value of
        expected_status_code
        :param expected_status_code: instance status evaluated with this string
                                     value
        :param block: When true, thread will block until active or timeout
                      value in seconds has been exceeded (False)
        :param timeout: The timeout value
        :param poll_interval: The polling interval in seconds
        :return: T/F
        """
        # sleep and wait for volume status change
        if block:
            start = time.time()
        else:
            start = time.time() - timeout + 1

        while timeout > time.time() - start:
            status = self._status(expected_status_code)
            if status:
                logger.debug('Volume is active with name - %s',
                             self.volume_settings.name)
                return True

            logger.debug('Retry querying volume status in %s seconds',
                         str(poll_interval))
            time.sleep(poll_interval)
            logger.debug('Volume status query timeout in %s',
                         str(timeout - (time.time() - start)))

        logger.error(
            'Timeout checking for volume status for ' + expected_status_code)
        return False

    def _status(self, expected_status_code):
        """
        Returns True when active else False
        :param expected_status_code: instance status evaluated with this string
                                     value
        :return: T/F
        """
        status = cinder_utils.get_volume_status(self._cinder, self.__volume)
        if not status:
            logger.warning(
                'Cannot volume status for volume with ID - %s',
                self.__volume.id)
            return False

        if status == 'ERROR':
            raise VolumeCreationError(
                'Instance had an error during deployment')
        logger.debug('Instance status is - ' + status)
        return status == expected_status_code


class VolumeSettings(VolumeConfig):
    """
    Class to hold the configuration settings required for creating OpenStack
    Volume Type Encryption objects
    deprecated
    """

    def __init__(self, **kwargs):
        from warnings import warn
        warn('Use snaps.config.volume.VolumeConfig instead',
             DeprecationWarning)
        super(self.__class__, self).__init__(**kwargs)


class VolumeCreationError(Exception):
    """
    Exception to be thrown when an volume cannot be created
    """

    def __init__(self, message):
        Exception.__init__(self, message)
