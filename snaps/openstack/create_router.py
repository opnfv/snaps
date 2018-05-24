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

from neutronclient.common.exceptions import NotFound, Unauthorized

from snaps.config.router import RouterConfig
from snaps.openstack.openstack_creator import OpenStackNetworkObject
from snaps.openstack.utils import neutron_utils

__author__ = 'spisarski'

logger = logging.getLogger('OpenStackNetwork')


class OpenStackRouter(OpenStackNetworkObject):
    """
    Class responsible for managing a router in OpenStack
    """

    def __init__(self, os_creds, router_settings):
        """
        Constructor - all parameters are required
        :param os_creds: The credentials to connect with OpenStack
        :param router_settings: The settings used to create a router object
                                (must be an instance of the RouterConfig
                                class)
        """
        super(self.__class__, self).__init__(os_creds)

        if not router_settings:
            raise RouterCreationError('router_settings is required')

        self.router_settings = router_settings

        # Attributes instantiated on create()
        self.__router = None
        self.__internal_subnets = list()
        self.__internal_router_interface = None

        # Dict where the port object is the key and any newly created router
        # interfaces are the value
        self.__ports = list()

    def initialize(self):
        """
        Loads the existing router.
        :return: the Router domain object
        """
        super(self.__class__, self).initialize()

        try:
            self.__router = neutron_utils.get_router(
                self._neutron, self._keystone,
                router_settings=self.router_settings,
                project_name=self._os_creds.project_name)
        except Unauthorized as e:
            logger.warn('Unable to lookup router with name %s - %s',
                        self.router_settings.name, e)

        if self.__router:
            for sub_config in self.router_settings.internal_subnets:
                internal_subnet = self.__get_internal_subnet(sub_config)
                if internal_subnet:
                    self.__internal_subnets.append(internal_subnet)
                else:
                    raise RouterCreationError(
                        'Subnet not found with name ' + internal_subnet.name)

            for port_setting in self.router_settings.port_settings:
                port = neutron_utils.get_port(
                    self._neutron, self._keystone, port_settings=port_setting,
                    project_name=self._os_creds.project_name)
                if port:
                    self.__ports.append(port)

        return self.__router

    def create(self):
        """
        Responsible for creating the router.
        :return: the Router domain object
        """
        self.initialize()

        if not self.__router:
            self.__router = neutron_utils.create_router(
                self._neutron, self._os_creds, self.router_settings)

            for sub_config in self.router_settings.internal_subnets:
                internal_subnet = self.__get_internal_subnet(sub_config)
                if internal_subnet:
                    self.__internal_subnets.append(internal_subnet)
                    if internal_subnet:
                        logger.debug('Adding router to subnet...')
                        router_intf = neutron_utils.add_interface_router(
                            self._neutron, self.__router,
                            subnet=internal_subnet)
                        self.__internal_router_interface = router_intf
                else:
                    raise RouterCreationError(
                        'Subnet not found with name ' + internal_subnet.name)

            for port_setting in self.router_settings.port_settings:
                port = neutron_utils.get_port(
                    self._neutron, self._keystone, port_settings=port_setting,
                    project_name=self._os_creds.project_name)
                logger.info(
                    'Retrieved port %s for router - %s', port_setting.name,
                    self.router_settings.name)
                if port:
                    self.__ports.append(port)

                if not port:
                    port = neutron_utils.create_port(
                        self._neutron, self._os_creds, port_setting)
                    if port:
                        logger.info(
                            'Created port %s for router - %s',
                            port_setting.name,
                            self.router_settings.name)
                        self.__ports.append(port)
                        neutron_utils.add_interface_router(
                            self._neutron, self.__router, port=port)
                    else:
                        raise RouterCreationError(
                            'Error creating port with name - '
                            + port_setting.name)

        self.__router = neutron_utils.get_router_by_id(
            self._neutron, self.__router.id)
        return self.__router

    def __get_internal_subnet(self, sub_config):
        """
        returns the Subnet domain object from the subnet configurator
        :param sub_config:
        :return:
        """
        if isinstance(sub_config, dict):
            sub_dict = sub_config['subnet']
            network = neutron_utils.get_network(
                self._neutron, self._keystone,
                network_name=sub_dict['network_name'],
                project_name=sub_dict['project_name'])
            if network:
                return neutron_utils.get_subnet(
                    self._neutron, network,
                    subnet_name=sub_dict['subnet_name'])
        else:
            return neutron_utils.get_subnet_by_name(
                self._neutron, self._keystone,
                subnet_name=sub_config,
                project_name=self._os_creds.project_name)

    def clean(self):
        """
        Removes and deletes all items created in reverse order.
        """
        for port in self.__ports:
            logger.info(
                'Removing router interface from router %s and port %s',
                self.router_settings.name, port.name)
            try:
                neutron_utils.remove_interface_router(self._neutron,
                                                      self.__router, port=port)
            except NotFound:
                pass
        self.__ports = list()

        for internal_subnet in self.__internal_subnets:
            logger.info(
                'Removing router interface from router %s and subnet %s',
                self.router_settings.name, internal_subnet.name)
            try:
                neutron_utils.remove_interface_router(self._neutron,
                                                      self.__router,
                                                      subnet=internal_subnet)
            except NotFound:
                pass
        self.__internal_subnets = list()

        if self.__router:
            logger.info('Removing router ' + self.router_settings.name)
            try:
                neutron_utils.delete_router(self._neutron, self.__router)
            except NotFound:
                pass
            self.__router = None

        super(self.__class__, self).clean()

    def get_router(self):
        """
        Returns the OpenStack router object
        :return:
        """
        return self.__router

    def get_internal_router_interface(self):
        """
        Returns the OpenStack internal router interface object
        :return:
        """
        return self.__internal_router_interface


class RouterCreationError(Exception):
    """
    Exception to be thrown when an router instance cannot be created
    """


class RouterSettings(RouterConfig):
    """
    Class to hold the configuration settings required for creating OpenStack
    router objects
    deprecated
    """

    def __init__(self, **kwargs):
        from warnings import warn
        warn('Use snaps.config.router.RouterConfig instead',
             DeprecationWarning)
        super(self.__class__, self).__init__(**kwargs)
