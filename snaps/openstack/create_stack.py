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

import snaps
from snaps.config.stack import StackConfig
from snaps.openstack.create_flavor import OpenStackFlavor
from snaps.openstack.create_instance import OpenStackVmInstance
from snaps.openstack.create_keypairs import OpenStackKeypair
from snaps.openstack.create_security_group import OpenStackSecurityGroup
from snaps.openstack.create_router import OpenStackRouter
from snaps.openstack.create_volume import OpenStackVolume
from snaps.openstack.create_volume_type import OpenStackVolumeType
from snaps.openstack.openstack_creator import OpenStackCloudObject
from snaps.openstack.utils import (
    nova_utils, settings_utils, glance_utils, cinder_utils)

from snaps.openstack.create_network import OpenStackNetwork
from snaps.openstack.utils import heat_utils, neutron_utils

__author__ = 'spisarski'

logger = logging.getLogger('create_stack')


class OpenStackHeatStack(OpenStackCloudObject, object):
    """
    Class responsible for managing a heat stack in OpenStack
    """

    def __init__(self, os_creds, stack_settings, image_settings=None,
                 keypair_settings=None):
        """
        Constructor
        :param os_creds: The OpenStack connection credentials
        :param stack_settings: The stack settings
        :param image_settings: A list of ImageConfig objects that were used
                               for spawning this stack
        :param keypair_settings: A list of KeypairConfig objects that were
                                 used for spawning this stack
        :return:
        """
        super(self.__class__, self).__init__(os_creds)

        self.stack_settings = stack_settings

        if image_settings:
            self.image_settings = image_settings
        else:
            self.image_settings = None

        if image_settings:
            self.keypair_settings = keypair_settings
        else:
            self.keypair_settings = None

        self.__stack = None
        self.__heat_cli = None

        self.__neutron = None
        self.__nova = None
        self.__glance = None
        self.__cinder = None

    def initialize(self):
        """
        Loads the existing heat stack
        :return: The Stack domain object or None
        """
        super(self.__class__, self).initialize()

        self.__neutron = neutron_utils.neutron_client(
            self._os_creds, self._os_session)
        self.__nova = nova_utils.nova_client(self._os_creds, self._os_session)
        self.__glance = glance_utils.glance_client(
            self._os_creds, self._os_session)
        self.__cinder = cinder_utils.cinder_client(
            self._os_creds, self._os_session)

        self.__heat_cli = heat_utils.heat_client(
            self._os_creds, self._os_session)
        self.__stack = heat_utils.get_stack(
            self.__heat_cli, stack_settings=self.stack_settings)
        if self.__stack:
            logger.info('Found stack with name - ' + self.stack_settings.name)
            return self.__stack

    def create(self):
        """
        Creates the heat stack in OpenStack if it does not already exist and
        returns the domain Stack object
        :return: The Stack domain object or None
        """
        self.initialize()

        if self.__stack:
            logger.info('Found stack with name - %s', self.stack_settings.name)
            return self.__stack
        else:
            self.__stack = heat_utils.create_stack(self.__heat_cli,
                                                   self.stack_settings)
            logger.info(
                'Created stack with name - %s', self.stack_settings.name)
            if self.__stack and self.stack_complete(block=True):
                logger.info('Stack is now active with name - %s',
                            self.stack_settings.name)
                return self.__stack
            else:
                status = heat_utils.get_stack_status_reason(self.__heat_cli,
                                                            self.__stack.id)
                logger.error('ERROR: STACK CREATION FAILED: %s', status)
                raise StackCreationError('Failure while creating stack')

    def clean(self):
        """
        Cleanse environment of all artifacts
        :return: void
        """
        if self.__stack:
            try:
                logger.info('Deleting stack - %s', self.__stack.name)
                heat_utils.delete_stack(self.__heat_cli, self.__stack)

                try:
                    self.stack_deleted(block=True)
                except StackError as e:
                    # Stack deletion seems to fail quite a bit
                    logger.warn('Stack did not delete properly - %s', e)

                    # Delete VMs first
                    for vm_inst_creator in self.get_vm_inst_creators():
                        try:
                            vm_inst_creator.clean()
                            if not vm_inst_creator.vm_deleted(block=True):
                                logger.warn('Unable to deleted VM - %s',
                                            vm_inst_creator.get_vm_inst().name)
                        except:
                            logger.warn('Unexpected error deleting VM - %s ',
                                        vm_inst_creator.get_vm_inst().name)

                logger.info('Attempting to delete again stack - %s',
                            self.__stack.name)

                # Delete Stack again
                heat_utils.delete_stack(self.__heat_cli, self.__stack)
                deleted = self.stack_deleted(block=True)
                if not deleted:
                    raise StackError(
                        'Stack could not be deleted ' + self.__stack.name)
            except HTTPNotFound:
                pass

            self.__stack = None

        self.__neutron.httpclient.session.session.close()
        self.__nova.client.session.session.close()
        self.__glance.http_client.session.session.close()
        self.__cinder.client.session.session.close()

        super(self.__class__, self).clean()

    def get_stack(self):
        """
        Returns the domain Stack object as it was populated when create() was
        called
        :return: the object
        """
        if self.__stack:
            return heat_utils.get_stack_by_id(self.__heat_cli, self.__stack.id)

    def get_outputs(self):
        """
        Returns the list of outputs as contained on the OpenStack Heat Stack
        object
        :return:
        """
        return heat_utils.get_outputs(self.__heat_cli, self.__stack)

    def get_status(self):
        """
        Returns the list of outputs as contained on the OpenStack Heat Stack
        object
        :return:
        """
        stack = self.get_stack()
        if stack:
            return stack.status

    def stack_complete(self, block=False, timeout=None,
                       poll_interval=snaps.config.stack.POLL_INTERVAL):
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
        return self._stack_status_check(
            snaps.config.stack.STATUS_CREATE_COMPLETE, block, timeout,
            poll_interval, snaps.config.stack.STATUS_CREATE_FAILED)

    def stack_deleted(self, block=False,
                      timeout=snaps.config.stack.STACK_DELETE_TIMEOUT,
                      poll_interval=snaps.config.stack.POLL_INTERVAL):
        """
        Returns true when the stack status returns the value of
        expected_status_code
        :param block: When true, thread will block until active or timeout
                      value in seconds has been exceeded (False)
        :param timeout: The timeout value
        :param poll_interval: The polling interval in seconds
        :return: T/F
        """
        return self._stack_status_check(
            snaps.config.stack.STATUS_DELETE_COMPLETE, block, timeout,
            poll_interval, snaps.config.stack.STATUS_DELETE_FAILED)

    def get_network_creators(self):
        """
        Returns a list of network creator objects as configured by the heat
        template
        :return: list() of OpenStackNetwork objects
        """

        out = list()
        stack_networks = heat_utils.get_stack_networks(
            self.__heat_cli, self.__neutron, self.__stack)

        for stack_network in stack_networks:
            net_settings = settings_utils.create_network_config(
                self.__neutron, stack_network)
            net_creator = OpenStackNetwork(self._os_creds, net_settings)
            out.append(net_creator)
            net_creator.initialize()

        return out

    def get_security_group_creators(self):
        """
        Returns a list of security group creator objects as configured by the
        heat template
        :return: list() of OpenStackNetwork objects
        """

        out = list()
        stack_security_groups = heat_utils.get_stack_security_groups(
            self.__heat_cli, self.__neutron, self.__stack)

        for stack_security_group in stack_security_groups:
            settings = settings_utils.create_security_group_config(
                self.__neutron, stack_security_group)
            creator = OpenStackSecurityGroup(self._os_creds, settings)
            out.append(creator)
            creator.initialize()

        return out

    def get_router_creators(self):
        """
        Returns a list of router creator objects as configured by the heat
        template
        :return: list() of OpenStackRouter objects
        """

        out = list()
        stack_routers = heat_utils.get_stack_routers(
            self.__heat_cli, self.__neutron, self.__stack)

        for routers in stack_routers:
            settings = settings_utils.create_router_config(
                self.__neutron, routers)
            creator = OpenStackRouter(self._os_creds, settings)
            out.append(creator)
            creator.initialize()

        return out

    def get_vm_inst_creators(self, heat_keypair_option=None):
        """
        Returns a list of VM Instance creator objects as configured by the heat
        template
        :return: list() of OpenStackVmInstance objects
        """

        out = list()

        stack_servers = heat_utils.get_stack_servers(
            self.__heat_cli, self.__nova, self.__neutron, self._keystone,
            self.__stack, self._os_creds.project_name)

        for stack_server in stack_servers:
            vm_inst_settings = settings_utils.create_vm_inst_config(
                self.__nova, self._keystone, self.__neutron, stack_server,
                self._os_creds.project_name)
            image_settings = settings_utils.determine_image_config(
                self.__glance, stack_server, self.image_settings)
            keypair_settings = settings_utils.determine_keypair_config(
                self.__heat_cli, self.__stack, stack_server,
                keypair_settings=self.keypair_settings,
                priv_key_key=heat_keypair_option)
            vm_inst_creator = OpenStackVmInstance(
                self._os_creds, vm_inst_settings, image_settings,
                keypair_settings)
            out.append(vm_inst_creator)
            vm_inst_creator.initialize()

        return out

    def get_volume_creators(self):
        """
        Returns a list of Volume creator objects as configured by the heat
        template
        :return: list() of OpenStackVolume objects
        """

        out = list()
        volumes = heat_utils.get_stack_volumes(
            self.__heat_cli, self.__cinder, self.__stack)

        for volume in volumes:
            settings = settings_utils.create_volume_config(volume)
            creator = OpenStackVolume(self._os_creds, settings)
            out.append(creator)

            try:
                creator.initialize()
            except Exception as e:
                logger.error(
                    'Unexpected error initializing volume creator - %s', e)

        return out

    def get_volume_type_creators(self):
        """
        Returns a list of VolumeType creator objects as configured by the heat
        template
        :return: list() of OpenStackVolumeType objects
        """

        out = list()
        vol_types = heat_utils.get_stack_volume_types(
            self.__heat_cli, self.__cinder, self.__stack)

        for volume in vol_types:
            settings = settings_utils.create_volume_type_config(volume)
            creator = OpenStackVolumeType(self._os_creds, settings)
            out.append(creator)

            try:
                creator.initialize()
            except Exception as e:
                logger.error(
                    'Unexpected error initializing volume type creator - %s',
                    e)

        return out

    def get_keypair_creators(self, outputs_pk_key=None):
        """
        Returns a list of keypair creator objects as configured by the heat
        template
        :return: list() of OpenStackKeypair objects
        """

        out = list()

        keypairs = heat_utils.get_stack_keypairs(
            self.__heat_cli, self.__nova, self.__stack)

        for keypair in keypairs:
            settings = settings_utils.create_keypair_config(
                self.__heat_cli, self.__stack, keypair, outputs_pk_key)
            creator = OpenStackKeypair(self._os_creds, settings)
            out.append(creator)

            try:
                creator.initialize()
            except Exception as e:
                logger.error(
                    'Unexpected error initializing volume type creator - %s',
                    e)

        return out

    def get_flavor_creators(self):
        """
        Returns a list of Flavor creator objects as configured by the heat
        template
        :return: list() of OpenStackFlavor objects
        """

        out = list()

        flavors = heat_utils.get_stack_flavors(
            self.__heat_cli, self.__nova, self.__stack)

        for flavor in flavors:
            settings = settings_utils.create_flavor_config(flavor)
            creator = OpenStackFlavor(self._os_creds, settings)
            out.append(creator)

            try:
                creator.initialize()
            except Exception as e:
                logger.error(
                    'Unexpected error initializing volume creator - %s', e)

        return out

    def _stack_status_check(self, expected_status_code, block, timeout,
                            poll_interval, fail_status):
        """
        Returns true when the stack status returns the value of
        expected_status_code
        :param expected_status_code: stack status evaluated with this string
                                     value
        :param block: When true, thread will block until active or timeout
                      value in seconds has been exceeded (False)
        :param timeout: The timeout value
        :param poll_interval: The polling interval in seconds
        :param fail_status: Returns false if the fail_status code is found
        :return: T/F
        """
        # sleep and wait for stack status change
        if block:
            start = time.time()
        else:
            start = time.time() - timeout

        while timeout > time.time() - start:
            status = self._status(expected_status_code, fail_status)
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

    def _status(self, expected_status_code,
                fail_status=snaps.config.stack.STATUS_CREATE_FAILED):
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

        if fail_status and status == fail_status:
            resources = heat_utils.get_resources(
                self.__heat_cli, self.__stack.id)
            logger.error('Stack %s failed', self.__stack.name)
            for resource in resources:
                if (resource.status !=
                        snaps.config.stack.STATUS_CREATE_COMPLETE):
                    logger.error(
                        'Resource: [%s] status: [%s] reason: [%s]',
                        resource.name, resource.status, resource.status_reason)
                else:
                    logger.debug(
                        'Resource: [%s] status: [%s] reason: [%s]',
                        resource.name, resource.status, resource.status_reason)

            raise StackError('Stack had an error')
        logger.debug('Stack status is - ' + status)
        return status == expected_status_code


def generate_creator(os_creds, stack_inst, image_settings):
    """
    Initializes an OpenStackHeatStack object
    :param os_creds: the OpenStack credentials
    :param stack_inst: the SNAPS-OO VmInst domain object
    :param image_settings: list of SNAPS-OO ImageConfig objects
    :return: an initialized OpenStackHeatStack object
    """

    heat_config = StackConfig(
        name=stack_inst.name, template={'place': 'holder'})
    heat_creator = OpenStackHeatStack(os_creds, heat_config, image_settings)
    heat_creator.initialize()
    return heat_creator


class StackSettings(StackConfig):
    """
    Class to hold the configuration settings required for creating OpenStack
    stack objects
    deprecated
    """

    def __init__(self, **kwargs):
        from warnings import warn
        warn('Use snaps.config.stack.StackConfig instead',
             DeprecationWarning)
        super(self.__class__, self).__init__(**kwargs)


class StackCreationError(Exception):
    """
    Exception to be thrown when an stack cannot be created
    """


class StackError(Exception):
    """
    General exception
    """
