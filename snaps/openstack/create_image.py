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

from glanceclient.exc import HTTPNotFound

from snaps.openstack.utils import glance_utils

__author__ = 'spisarski'

logger = logging.getLogger('create_image')

IMAGE_ACTIVE_TIMEOUT = 600
POLL_INTERVAL = 3
STATUS_ACTIVE = 'active'


class OpenStackImage:
    """
    Class responsible for creating an image in OpenStack
    """

    def __init__(self, os_creds, image_settings):
        """
        Constructor
        :param os_creds: The OpenStack connection credentials
        :param image_settings: The image settings
        :return:
        """
        self.__os_creds = os_creds
        self.image_settings = image_settings
        self.__image = None
        self.__glance = glance_utils.glance_client(os_creds)

    def create(self, cleanup=False):
        """
        Creates the image in OpenStack if it does not already exist and returns the domain Image object
        :param cleanup: Denotes whether or not this is being called for cleanup or not
        :return: The OpenStack Image object
        """
        self.__image = glance_utils.get_image(self.__glance, self.image_settings.name)
        if self.__image:
            logger.info('Found image with name - ' + self.image_settings.name)
            return self.__image
        elif not cleanup:
            self.__image = glance_utils.create_image(self.__glance, self.image_settings)
            logger.info('Creating image')
            if self.__image and self.image_active(block=True):
                logger.info('Image is now active with name - ' + self.image_settings.name)
                return self.__image
            else:
                raise Exception('Image was not created or activated in the alloted amount of time')
        else:
            logger.info('Did not create image due to cleanup mode')

        return self.__image

    def clean(self):
        """
        Cleanse environment of all artifacts
        :return: void
        """
        if self.__image:
            try:
                glance_utils.delete_image(self.__glance, self.__image)
            except HTTPNotFound:
                pass
            self.__image = None

    def get_image(self):
        """
        Returns the domain Image object as it was populated when create() was called
        :return: the object
        """
        return self.__image

    def image_active(self, block=False, timeout=IMAGE_ACTIVE_TIMEOUT, poll_interval=POLL_INTERVAL):
        """
        Returns true when the image status returns the value of expected_status_code
        :param block: When true, thread will block until active or timeout value in seconds has been exceeded (False)
        :param timeout: The timeout value
        :param poll_interval: The polling interval in seconds
        :return: T/F
        """
        return self._image_status_check(STATUS_ACTIVE, block, timeout, poll_interval)

    def _image_status_check(self, expected_status_code, block, timeout, poll_interval):
        """
        Returns true when the image status returns the value of expected_status_code
        :param expected_status_code: instance status evaluated with this string value
        :param block: When true, thread will block until active or timeout value in seconds has been exceeded (False)
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
                logger.info('Image is active with name - ' + self.image_settings.name)
                return True

            logger.debug('Retry querying image status in ' + str(poll_interval) + ' seconds')
            time.sleep(poll_interval)
            logger.debug('Image status query timeout in ' + str(timeout - (time.time() - start)))

        logger.error('Timeout checking for image status for ' + expected_status_code)
        return False

    def _status(self, expected_status_code):
        """
        Returns True when active else False
        :param expected_status_code: instance status evaluated with this string value
        :return: T/F
        """
        # TODO - Place this API call into glance_utils.
        status = glance_utils.get_image_status(self.__glance, self.__image)
        if not status:
            logger.warn('Cannot image status for image with ID - ' + self.__image.id)
            return False

        if status == 'ERROR':
            raise Exception('Instance had an error during deployment')
        logger.debug('Instance status is - ' + status)
        return status == expected_status_code


class ImageSettings:
    def __init__(self, config=None, name=None, image_user=None, img_format=None, url=None, image_file=None,
                 extra_properties=None, nic_config_pb_loc=None):
        """

        :param config: dict() object containing the configuration settings using the attribute names below as each
                       member's the key and overrides any of the other parameters.
        :param name: the image's name (required)
        :param image_user: the image's default sudo user (required)
        :param img_format: the image type (required)
        :param url: the image download location (requires url or img_file)
        :param image_file: the image file location (requires url or img_file)
        :param extra_properties: dict() object containing extra parameters to pass when loading the image;
                                 can be ids of kernel and initramfs images for a 3-part image
        :param nic_config_pb_loc: the file location to the Ansible Playbook that can configure multiple NICs
        """

        if config:
            self.name = config.get('name')
            self.image_user = config.get('image_user')
            self.format = config.get('format')
            self.url = config.get('download_url')
            self.image_file = config.get('image_file')
            self.extra_properties = config.get('extra_properties')
            self.nic_config_pb_loc = config.get('nic_config_pb_loc')
        else:
            self.name = name
            self.image_user = image_user
            self.format = img_format
            self.url = url
            self.image_file = image_file
            self.extra_properties = extra_properties
            self.nic_config_pb_loc = nic_config_pb_loc

        if not self.name or not self.image_user or not self.format:
            raise Exception("The attributes name, image_user, format, and url are required for ImageSettings")

        if not self.url and not self.image_file:
            raise Exception('URL or image file must be set')

        if self.url and self.image_file:
            raise Exception('Please set either URL or image file, not both')
