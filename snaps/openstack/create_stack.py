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

from heatclient.exc import HTTPNotFound

from snaps.openstack.utils import heat_utils

__author__ = 'spisarski'

logger = logging.getLogger('create_stack')

STACK_COMPLETE_TIMEOUT = 1200
POLL_INTERVAL = 3
STATUS_COMPLETE = 'CREATE_COMPLETE'


class OpenStackHeatStack:
    """
    Class responsible for creating an heat stack in OpenStack
    """

    def __init__(self, os_creds, stack_settings):
        """
        Constructor
        :param os_creds: The OpenStack connection credentials
        :param stack_settings: The stack settings
        :return:
        """
        self.__os_creds = os_creds
        self.stack_settings = stack_settings
        self.__stack = None
        self.__heat_cli = None

    def create(self, cleanup=False):
        """
        Creates the heat stack in OpenStack if it does not already exist and returns the domain Stack object
        :param cleanup: Denotes whether or not this is being called for cleanup or not
        :return: The OpenStack Stack object
        """
        self.__heat_cli = heat_utils.heat_client(self.__os_creds)
        self.__stack = heat_utils.get_stack_by_name(self.__heat_cli, self.stack_settings.name)
        if self.__stack:
            logger.info('Found stack with name - ' + self.stack_settings.name)
            return self.__stack
        elif not cleanup:
            self.__stack = heat_utils.create_stack(self.__heat_cli, self.stack_settings)
            logger.info('Created stack with name - ' + self.stack_settings.name)
            if self.__stack and self.stack_complete(block=True):
                logger.info('Stack is now active with name - ' + self.stack_settings.name)
                return self.__stack
            else:
                raise StackCreationError('Stack was not created or activated in the alloted amount of time')
        else:
            logger.info('Did not create stack due to cleanup mode')

        return self.__stack

    def clean(self):
        """
        Cleanse environment of all artifacts
        :return: void
        """
        if self.__stack:
            try:
                heat_utils.delete_stack(self.__heat_cli, self.__stack)
            except HTTPNotFound:
                pass

        self.__stack = None

    def get_stack(self):
        """
        Returns the domain Stack object as it was populated when create() was called
        :return: the object
        """
        return self.__stack

    def stack_complete(self, block=False, timeout=None, poll_interval=POLL_INTERVAL):
        """
        Returns true when the stack status returns the value of expected_status_code
        :param block: When true, thread will block until active or timeout value in seconds has been exceeded (False)
        :param timeout: The timeout value
        :param poll_interval: The polling interval in seconds
        :return: T/F
        """
        if not timeout:
            timeout = self.stack_settings.stack_create_timeout
        return self._stack_status_check(STATUS_COMPLETE, block, timeout, poll_interval)

    def _stack_status_check(self, expected_status_code, block, timeout, poll_interval):
        """
        Returns true when the stack status returns the value of expected_status_code
        :param expected_status_code: stack status evaluated with this string value
        :param block: When true, thread will block until active or timeout value in seconds has been exceeded (False)
        :param timeout: The timeout value
        :param poll_interval: The polling interval in seconds
        :return: T/F
        """
        # sleep and wait for stack status change
        if block:
            start = time.time()
        else:
            start = time.time() - timeout

        while timeout > time.time() - start:
            status = self._status(expected_status_code)
            if status:
                logger.debug('Stack is active with name - ' + self.stack_settings.name)
                return True

            logger.debug('Retry querying stack status in ' + str(poll_interval) + ' seconds')
            time.sleep(poll_interval)
            logger.debug('Stack status query timeout in ' + str(timeout - (time.time() - start)))

        logger.error('Timeout checking for stack status for ' + expected_status_code)
        return False

    def _status(self, expected_status_code):
        """
        Returns True when active else False
        :param expected_status_code: stack status evaluated with this string value
        :return: T/F
        """
        status = heat_utils.get_stack_status(self.__heat_cli, self.__stack.id)
        if not status:
            logger.warning('Cannot stack status for stack with ID - ' + self.__stack.id)
            return False

        if status == 'ERROR':
            raise StackCreationError('Stack had an error during deployment')
        logger.debug('Stack status is - ' + status)
        return status == expected_status_code


class StackSettings:
    def __init__(self, config=None, name=None, template_path=None, env_values=None,
                 stack_create_timeout=STACK_COMPLETE_TIMEOUT):
        """
        Constructor
        :param config: dict() object containing the configuration settings using the attribute names below as each
                       member's the key and overrides any of the other parameters.
        :param name: the stack's name (required)
        :param template_path: the location of the heat template file (required)
        :param env_values: k/v pairs of strings for substitution of template default values (optional)
        """

        if config:
            self.name = config.get('name')
            self.template_path = config.get('template_path')
            self.env_values = config.get('env_values')
            if 'stack_create_timeout' in config:
                self.stack_create_timeout = config['stack_create_timeout']
            else:
                self.stack_create_timeout = stack_create_timeout
        else:
            self.name = name
            self.template_path = template_path
            self.env_values = env_values
            self.stack_create_timeout = stack_create_timeout

        if not self.name or not self.template_path:
            raise StackSettingsError('name and template_path attributes are required')


class StackSettingsError(Exception):
    """
    Exception to be thrown when an stack settings are incorrect
    """
    def __init__(self, message):
        Exception.__init__(self, message)


class StackCreationError(Exception):
    """
    Exception to be thrown when an stack cannot be created
    """
    def __init__(self, message):
        Exception.__init__(self, message)
