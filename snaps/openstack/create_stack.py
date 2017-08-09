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

from snaps.openstack.create_network import (
    OpenStackNetwork, NetworkSettings, SubnetSettings)
from snaps.openstack.utils import heat_utils, neutron_utils

__author__ = 'spisarski'

logger = logging.getLogger('create_stack')

STACK_COMPLETE_TIMEOUT = 1200
POLL_INTERVAL = 3
STATUS_CREATE_FAILED = 'CREATE_FAILED'
STATUS_CREATE_COMPLETE = 'CREATE_COMPLETE'
STATUS_DELETE_COMPLETE = 'DELETE_COMPLETE'


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
        Creates the heat stack in OpenStack if it does not already exist and
        returns the domain Stack object
        :param cleanup: When true, this object is initialized only via queries,
                        else objects will be created when the queries return
                        None. The name of this parameter should be changed to
                        something like 'readonly' as the same goes with all of
                        the other creator classes.
        :return: The OpenStack Stack object
        """
        self.__heat_cli = heat_utils.heat_client(self.__os_creds)
        self.__stack = heat_utils.get_stack(
            self.__heat_cli, stack_settings=self.stack_settings)
        if self.__stack:
            logger.info('Found stack with name - ' + self.stack_settings.name)
            return self.__stack
        elif not cleanup:
            self.__stack = heat_utils.create_stack(self.__heat_cli,
                                                   self.stack_settings)
            logger.info(
                'Created stack with name - ' + self.stack_settings.name)
            if self.__stack and self.stack_complete(block=True):
                logger.info(
                    'Stack is now active with name - ' +
                    self.stack_settings.name)
                return self.__stack
            else:
                raise StackCreationError(
                    'Stack was not created or activated in the alloted amount '
                    'of time')
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
        Returns the domain Stack object as it was populated when create() was
        called
        :return: the object
        """
        return self.__stack

    def get_outputs(self):
        """
        Returns the list of outputs as contained on the OpenStack Heat Stack
        object
        :return:
        """
        return heat_utils.get_stack_outputs(self.__heat_cli, self.__stack.id)

    def get_status(self):
        """
        Returns the list of outputs as contained on the OpenStack Heat Stack
        object
        :return:
        """
        return heat_utils.get_stack_status(self.__heat_cli, self.__stack.id)

    def stack_complete(self, block=False, timeout=None,
                       poll_interval=POLL_INTERVAL):
        """
        Returns true when the stack status returns the value of
        expected_status_code
        :param block: When true, thread will block until active or timeout
                      value in seconds has been exceeded (False)
        :param timeout: The timeout value
        :param poll_interval: The polling interval in seconds
        :return: T/F
        """
        if not timeout:
            timeout = self.stack_settings.stack_create_timeout
        return self._stack_status_check(STATUS_CREATE_COMPLETE, block, timeout,
                                        poll_interval)

    def get_network_creators(self):
        """
        Returns a list of network creator objects as configured by the heat
        template
        :return: list() of OpenStackNetwork objects
        """

        neutron = neutron_utils.neutron_client(self.__os_creds)

        out = list()
        stack_networks = heat_utils.get_stack_networks(
            self.__heat_cli, neutron, self.__stack)

        for stack_network in stack_networks:
            net_settings = self.__create_network_settings(
                neutron, stack_network)
            net_creator = OpenStackNetwork(self.__os_creds, net_settings)
            out.append(net_creator)
            net_creator.create(cleanup=True)

        return out

    def __create_network_settings(self, neutron, network):
        """
        Returns a NetworkSettings object
        :param neutron: the neutron client
        :param network: a SNAPS-OO Network domain object
        :return:
        """
        return NetworkSettings(
            name=network.name, network_type=network.type,
            subnet_settings=self.__create_subnet_settings(neutron, network))

    def __create_subnet_settings(self, neutron, network):
        """
        Returns a list of SubnetSettings objects for a given network
        :param neutron: the OpenStack neutron client
        :param network: the SNAPS-OO Network domain object
        :return: a list
        """
        out = list()

        subnets = neutron_utils.get_subnets_by_network(neutron, network)
        for subnet in subnets:
            kwargs = dict()
            kwargs['cidr'] = subnet.cidr
            kwargs['ip_version'] = subnet.ip_version
            kwargs['name'] = subnet.name
            kwargs['start'] = subnet.start
            kwargs['end'] = subnet.end
            kwargs['gateway_ip'] = subnet.gateway_ip
            kwargs['enable_dhcp'] = subnet.enable_dhcp
            kwargs['dns_nameservers'] = subnet.dns_nameservers
            kwargs['host_routes'] = subnet.host_routes
            kwargs['ipv6_ra_mode'] = subnet.ipv6_ra_mode
            kwargs['ipv6_address_mode'] = subnet.ipv6_address_mode
            out.append(SubnetSettings(**kwargs))
        return out

    def _stack_status_check(self, expected_status_code, block, timeout,
                            poll_interval):
        """
        Returns true when the stack status returns the value of
        expected_status_code
        :param expected_status_code: stack status evaluated with this string
                                     value
        :param block: When true, thread will block until active or timeout
                      value in seconds has been exceeded (False)
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
                logger.debug(
                    'Stack is active with name - ' + self.stack_settings.name)
                return True

            logger.debug('Retry querying stack status in ' + str(
                poll_interval) + ' seconds')
            time.sleep(poll_interval)
            logger.debug('Stack status query timeout in ' + str(
                timeout - (time.time() - start)))

        logger.error(
            'Timeout checking for stack status for ' + expected_status_code)
        return False

    def _status(self, expected_status_code):
        """
        Returns True when active else False
        :param expected_status_code: stack status evaluated with this string
        value
        :return: T/F
        """
        status = self.get_status()
        if not status:
            logger.warning(
                'Cannot stack status for stack with ID - ' + self.__stack.id)
            return False

        if status == STATUS_CREATE_FAILED:
            raise StackCreationError('Stack had an error during deployment')
        logger.debug('Stack status is - ' + status)
        return status == expected_status_code


class StackSettings:
    def __init__(self, **kwargs):
        """
        Constructor
        :param name: the stack's name (required)
        :param template: the heat template in dict() format (required if
                         template_path attribute is None)
        :param template_path: the location of the heat template file (required
                              if template attribute is None)
        :param env_values: k/v pairs of strings for substitution of template
                           default values (optional)
        """

        self.name = kwargs.get('name')
        self.template = kwargs.get('template')
        self.template_path = kwargs.get('template_path')
        self.env_values = kwargs.get('env_values')
        if 'stack_create_timeout' in kwargs:
            self.stack_create_timeout = kwargs['stack_create_timeout']
        else:
            self.stack_create_timeout = STACK_COMPLETE_TIMEOUT

        if not self.name:
            raise StackSettingsError('name is required')

        if not self.template and not self.template_path:
            raise StackSettingsError('A Heat template is required')

    def __eq__(self, other):
        return (self.name == other.name and
                self.template == other.template and
                self.template_path == other.template_path and
                self.env_values == other.env_values and
                self.stack_create_timeout == other.stack_create_timeout)


class StackSettingsError(Exception):
    """
    Exception to be thrown when an stack settings are incorrect
    """


class StackCreationError(Exception):
    """
    Exception to be thrown when an stack cannot be created
    """
