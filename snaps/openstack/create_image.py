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

from glanceclient.exc import HTTPNotFound
import logging
import time

from snaps.openstack.openstack_creator import OpenStackCloudObject
from snaps.openstack.utils import glance_utils
from snaps.config import image

__author__ = 'spisarski'

logger = logging.getLogger('create_image')

IMAGE_ACTIVE_TIMEOUT = 600
POLL_INTERVAL = 3
STATUS_ACTIVE = 'active'


class OpenStackImage(OpenStackCloudObject):
    """
    Class responsible for managing an image in OpenStack
    """

    def __init__(self, os_creds, image_settings):
        """
        Constructor
        :param os_creds: The OpenStack connection credentials
        :param image_settings: An snaps.config.image.ImageConfig object
        """
        super(self.__class__, self).__init__(os_creds)

        self.image_settings = image_settings
        self.__image = None
        self.__kernel_image = None
        self.__ramdisk_image = None
        self.__glance = None

    def initialize(self):
        """
        Loads the existing Image
        :return: The Image domain object or None
        """
        super(self.__class__, self).initialize()

        self.__glance = glance_utils.glance_client(
            self._os_creds, self._os_session)
        self.__image = glance_utils.get_image(
            self.__glance, image_settings=self.image_settings)

        if self.__image:
            logger.info('Found image with name - ' + self.image_settings.name)
            return self.__image
        elif (self.image_settings.exists and not self.image_settings.url
                and not self.image_settings.image_file):
            raise ImageCreationError(
                'Image with does not exist with name - ' +
                self.image_settings.name)

        if self.image_settings.kernel_image_settings:
            self.__kernel_image = glance_utils.get_image(
                self.__glance,
                image_settings=self.image_settings.kernel_image_settings)

        if self.image_settings.ramdisk_image_settings:
            self.__ramdisk_image = glance_utils.get_image(
                self.__glance,
                image_settings=self.image_settings.ramdisk_image_settings)

        return self.__image

    def create(self):
        """
        Creates the image in OpenStack if it does not already exist and returns
        the domain Image object
        :return: The Image domain object or None
        """
        self.initialize()

        if not self.__image:
            extra_properties = self.image_settings.extra_properties or dict()

            if self.image_settings.kernel_image_settings:
                if not self.__kernel_image:
                    logger.info(
                        'Creating associated kernel image with name - %s',
                        self.image_settings.kernel_image_settings.name)
                    self.__kernel_image = glance_utils.create_image(
                        self.__glance,
                        self.image_settings.kernel_image_settings)
                extra_properties['kernel_id'] = self.__kernel_image.id

            if self.image_settings.ramdisk_image_settings:
                if not self.__ramdisk_image:
                    logger.info(
                        'Creating associated ramdisk image with name - %s',
                        self.image_settings.ramdisk_image_settings.name)
                    self.__ramdisk_image = glance_utils.create_image(
                        self.__glance,
                        self.image_settings.ramdisk_image_settings)
                extra_properties['ramdisk_id'] = self.__ramdisk_image.id

            self.image_settings.extra_properties = extra_properties
            self.__image = glance_utils.create_image(self.__glance,
                                                     self.image_settings)

            logger.info(
                'Created image with name - %s', self.image_settings.name)

            if self.__image and self.image_active(block=True):
                logger.info(
                    'Image is now active with name - %s',
                    self.image_settings.name)
                return self.__image
            else:
                raise ImageCreationError(
                    'Image was not created or activated in the alloted amount'
                    'of time')

        return self.__image

    def clean(self):
        """
        Cleanse environment of all artifacts
        :return: void
        """
        for img in [self.__image, self.__kernel_image, self.__ramdisk_image]:
            if img:
                try:
                    glance_utils.delete_image(self.__glance, img)
                except HTTPNotFound:
                    pass

        self.__image = None
        self.__kernel_image = None
        self.__ramdisk_image = None

        if self.__glance:
            self.__glance.http_client.session.session.close()

        super(self.__class__, self).clean()

    def get_image(self):
        """
        Returns the domain Image object as it was populated when create() was
        called
        :return: the object
        """
        return self.__image

    def get_kernel_image(self):
        """
        Returns the OpenStack kernel image object as it was populated when
        create() was called
        :return: the object
        """
        return self.__kernel_image

    def get_ramdisk_image(self):
        """
        Returns the OpenStack ramdisk image object as it was populated when
        create() was called
        :return: the object
        """
        return self.__ramdisk_image

    def image_active(self, block=False, timeout=IMAGE_ACTIVE_TIMEOUT,
                     poll_interval=POLL_INTERVAL):
        """
        Returns true when the image status returns the value of
        expected_status_code
        :param block: When true, thread will block until active or timeout
                      value in seconds has been exceeded (False)
        :param timeout: The timeout value
        :param poll_interval: The polling interval in seconds
        :return: T/F
        """
        return self._image_status_check(STATUS_ACTIVE, block, timeout,
                                        poll_interval)

    def _image_status_check(self, expected_status_code, block, timeout,
                            poll_interval):
        """
        Returns true when the image status returns the value of
        expected_status_code
        :param expected_status_code: instance status evaluated with this string
                                     value
        :param block: When true, thread will block until active or timeout
                      value in seconds has been exceeded (False)
        :param timeout: The timeout value
        :param poll_interval: The polling interval in seconds
        :return: T/F
        """
        # sleep and wait for image status change
        if block:
            start = time.time()
        else:
            start = time.time() - timeout

        while timeout > time.time() - start:
            status = self._status(expected_status_code)
            if status:
                logger.debug(
                    'Image is active with name - ' + self.image_settings.name)
                return True

            logger.debug('Retry querying image status in ' + str(
                poll_interval) + ' seconds')
            time.sleep(poll_interval)
            logger.debug('Image status query timeout in ' + str(
                timeout - (time.time() - start)))

        logger.error(
            'Timeout checking for image status for ' + expected_status_code)
        return False

    def _status(self, expected_status_code):
        """
        Returns True when active else False
        :param expected_status_code: instance status evaluated with this string
                                     value
        :return: T/F
        """
        status = glance_utils.get_image_status(self.__glance, self.__image)
        if not status:
            logger.warning(
                'Cannot image status for image with ID - ' + self.__image.id)
            return False

        if status == 'ERROR':
            raise ImageCreationError('Instance had an error during deployment')
        logger.debug('Instance status is - ' + status)
        return status == expected_status_code


class ImageSettings(image.ImageConfig):
    """
    Deprecated, use snaps.config.image.ImageSettings instead
    """
    def __init__(self, **kwargs):
        from warnings import warn
        warn('Use snaps.config.image.ImageConfig instead', DeprecationWarning)
        super(ImageSettings, self).__init__(**kwargs)


class ImageCreationError(Exception):
    """
    Exception to be thrown when an image cannot be created
    """

    def __init__(self, message):
        Exception.__init__(self, message)
