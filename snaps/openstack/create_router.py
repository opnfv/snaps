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

from neutronclient.common.exceptions import NotFound

from snaps.openstack.create_network import PortSettings
from snaps.openstack.utils import neutron_utils, keystone_utils

__author__ = 'spisarski'

logger = logging.getLogger('OpenStackNetwork')


class OpenStackRouter:
    """
    Class responsible for creating a router in OpenStack
    """

    def __init__(self, os_creds, router_settings):
        """
        Constructor - all parameters are required
        :param os_creds: The credentials to connect with OpenStack
        :param router_settings: The settings used to create a router object (must be an instance of the
                                RouterSettings class)
        """
        self.__os_creds = os_creds

        if not router_settings:
            raise Exception('router_settings is required')

        self.router_settings = router_settings
        self.__neutron = neutron_utils.neutron_client(os_creds)

        # Attributes instantiated on create()
        self.__router = None
        self.__internal_subnets = list()
        self.__internal_router_interface = None

        # Dict where the port object is the key and any newly created router interfaces are the value
        self.__ports = list()

    def create(self, cleanup=False):
        """
        Responsible for creating the router.
        :param cleanup: When true, only perform lookups for OpenStack objects.
        :return: the router object
        """
        logger.debug('Creating Router with name - ' + self.router_settings.name)
        existing = False
        router_inst = neutron_utils.get_router_by_name(self.__neutron, self.router_settings.name)
        if router_inst:
            self.__router = router_inst
            existing = True
        else:
            if not cleanup:
                self.__router = neutron_utils.create_router(self.__neutron, self.__os_creds, self.router_settings)

        for internal_subnet_name in self.router_settings.internal_subnets:
            internal_subnet = neutron_utils.get_subnet_by_name(self.__neutron, internal_subnet_name)
            if internal_subnet:
                self.__internal_subnets.append(internal_subnet)
                if internal_subnet and not cleanup and not existing:
                    logger.debug('Adding router to subnet...')
                    self.__internal_router_interface = neutron_utils.add_interface_router(
                        self.__neutron, self.__router, subnet=internal_subnet)
            else:
                raise Exception('Subnet not found with name ' + internal_subnet_name)

        for port_setting in self.router_settings.port_settings:
            port = neutron_utils.get_port_by_name(self.__neutron, port_setting.name)
            logger.info('Retrieved port ' + port_setting.name + ' for router - ' + self.router_settings.name)
            if port:
                self.__ports.append(port)

            if not port and not cleanup and not existing:
                port = neutron_utils.create_port(self.__neutron, self.__os_creds, port_setting)
                if port:
                    logger.info('Created port ' + port_setting.name + ' for router - ' + self.router_settings.name)
                    self.__ports.append(port)
                    neutron_utils.add_interface_router(self.__neutron, self.__router, port=port)
                else:
                    raise Exception('Error creating port with name - ' + port_setting.name)

        return self.__router

    def clean(self):
        """
        Removes and deletes all items created in reverse order.
        """
        for port in self.__ports:
            logger.info('Removing router interface from router ' + self.router_settings.name +
                        ' and port ' + port['port']['name'])
            try:
                neutron_utils.remove_interface_router(self.__neutron, self.__router, port=port)
            except NotFound:
                pass
        self.__ports = list()

        for internal_subnet in self.__internal_subnets:
            logger.info('Removing router interface from router ' + self.router_settings.name +
                        ' and subnet ' + internal_subnet['subnet']['name'])
            try:
                neutron_utils.remove_interface_router(self.__neutron, self.__router, subnet=internal_subnet)
            except NotFound:
                pass
        self.__internal_subnets = list()

        if self.__router:
            logger.info('Removing router ' + self.router_settings.name)
            try:
                neutron_utils.delete_router(self.__neutron, self.__router)
            except NotFound:
                pass
            self.__router = None

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


class RouterSettings:
    """
    Class representing a router configuration
    """

    def __init__(self, config=None, name=None, project_name=None, external_gateway=None,
                 admin_state_up=True, external_fixed_ips=None, internal_subnets=list(),
                 port_settings=list()):
        """
        Constructor - all parameters are optional
        :param config: Should be a dict object containing the configuration settings using the attribute names below
                       as each member's the key and overrides any of the other parameters.
        :param name: The router name.
        :param project_name: The name of the project who owns the network. Only administrative users can specify a
                             project ID other than their own. You cannot change this value through authorization
                             policies.
        :param external_gateway: Name of the external network to which to route
        :param admin_state_up: The administrative status of the router. True = up / False = down (default True)
        :param external_fixed_ips: Dictionary containing the IP address parameters.
        :param internal_subnets: List of subnet names to which to connect this router for Floating IP purposes
        :param port_settings: List of PortSettings objects
        :return:
        """
        if config:
            self.name = config.get('name')
            self.project_name = config.get('project_name')
            self.external_gateway = config.get('external_gateway')

            self.admin_state_up = config.get('admin_state_up')
            self.enable_snat = config.get('enable_snat')
            self.external_fixed_ips = config.get('external_fixed_ips')
            if config.get('internal_subnets'):
                self.internal_subnets = config['internal_subnets']
            else:
                self.internal_subnets = internal_subnets

            self.port_settings = list()
            if config.get('interfaces'):
                interfaces = config['interfaces']
                for interface in interfaces:
                    if interface.get('port'):
                        self.port_settings.append(PortSettings(config=interface['port']))
        else:
            self.name = name
            self.project_name = project_name
            self.external_gateway = external_gateway
            self.admin_state_up = admin_state_up
            self.external_fixed_ips = external_fixed_ips
            self.internal_subnets = internal_subnets
            self.port_settings = port_settings

        if not self.name:
            raise Exception('Name is required')

    def dict_for_neutron(self, neutron, os_creds):
        """
        Returns a dictionary object representing this object.
        This is meant to be converted into JSON designed for use by the Neutron API

        TODO - expand automated testing to exercise all parameters
        :param neutron: The neutron client to retrieve external network information if necessary
        :param os_creds: The OpenStack credentials
        :return: the dictionary object
        """
        out = dict()
        ext_gw = dict()

        project_id = None

        if self.name:
            out['name'] = self.name
        if self.project_name:
            keystone = keystone_utils.keystone_client(os_creds)
            project = keystone_utils.get_project(keystone, self.project_name)
            project_id = None
            if project:
                project_id = project.id
            if project_id:
                out['project_id'] = project_id
            else:
                raise Exception('Could not find project ID for project named - ' + self.project_name)
        if self.admin_state_up is not None:
            out['admin_state_up'] = self.admin_state_up
        if self.external_gateway:
            ext_net = neutron_utils.get_network(neutron, self.external_gateway, project_id)
            if ext_net:
                ext_gw['network_id'] = ext_net['network']['id']
                out['external_gateway_info'] = ext_gw
            else:
                raise Exception('Could not find the external network named - ' + self.external_gateway)

        # TODO: Enable SNAT option for Router
        # TODO: Add external_fixed_ips Tests

        return {'router': out}
