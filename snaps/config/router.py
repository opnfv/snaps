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
from snaps.config.network import PortConfig
from snaps.openstack.utils import neutron_utils, keystone_utils


class RouterConfig(object):
    """
    Class representing a router configuration
    """

    def __init__(self, **kwargs):
        """
        Constructor - all parameters are optional
        :param name: The router name.
        :param project_name: The name of the project who owns the network. Only
                             administrative users can specify a project ID
                             other than their own. You cannot change this value
                             through authorization policies.
        :param external_gateway: Name of the external network to which to route
        :param admin_state_up: The administrative status of the router.
                               True = up / False = down (default True)
        :param internal_subnets: List of subnet names to which to connect this
                                 router (this way is deprecated).
                                 *** NEW WAY ***
                                 List of dict where the key is 'subnet' that
                                 contains members with the following keys:
                                 project_name, network_name, and subnet_name
        :param port_settings: List of PortConfig objects
        :return:
        """
        self.name = kwargs.get('name')
        self.project_name = kwargs.get('project_name')
        self.external_gateway = kwargs.get('external_gateway')

        self.admin_state_up = kwargs.get('admin_state_up', True)
        self.enable_snat = kwargs.get('enable_snat')
        if kwargs.get('internal_subnets'):
            self.internal_subnets = kwargs['internal_subnets']
            if isinstance(self.internal_subnets, dict):
                if 'subnet' not in self.internal_subnets:
                    raise RouterConfigError(
                        'subnet is a required key to internal_subnets')
                if 'project_name' not in self.internal_subnets['subnet']:
                    raise RouterConfigError(
                        'subnet.project is a required key to subnet')
                if 'network_name' not in self.internal_subnets['subnet']:
                    raise RouterConfigError(
                        'network_name is a required key to subnet')
                if 'subnet_name' not in self.internal_subnets['subnet']:
                    raise RouterConfigError(
                        'subnet_name is a required key to subnet')
        else:
            self.internal_subnets = list()

        self.port_settings = list()
        if kwargs.get('interfaces', kwargs.get('port_settings')):
            interfaces = kwargs.get('interfaces', kwargs.get('port_settings'))
            for interface in interfaces:
                if isinstance(interface, PortConfig):
                    self.port_settings.append(interface)
                else:
                    self.port_settings.append(
                        PortConfig(**interface['port']))

        if not self.name:
            raise RouterConfigError('Name is required')

    def dict_for_neutron(self, neutron, os_creds):
        """
        Returns a dictionary object representing this object.
        This is meant to be converted into JSON designed for use by the Neutron
        API

        TODO - expand automated testing to exercise all parameters
        :param neutron: The neutron client to retrieve external network
                        information if necessary
        :param os_creds: The OpenStack credentials for retrieving the keystone
                         client for looking up the project ID when the
                         self.project_name is not None
        :return: the dictionary object
        """
        out = dict()
        ext_gw = dict()

        session = keystone_utils.keystone_session(os_creds)
        keystone = keystone_utils.keystone_client(os_creds, session)
        try:
            if self.name:
                out['name'] = self.name
            if self.project_name:
                project = keystone_utils.get_project(
                    keystone=keystone, project_name=self.project_name)
                if project:
                        out['tenant_id'] = project.id
                else:
                    raise RouterConfigError(
                        'Could not find project ID for project named - ' +
                        self.project_name)
            if self.admin_state_up is not None:
                out['admin_state_up'] = self.admin_state_up
            if self.external_gateway:
                ext_net = neutron_utils.get_network(
                    neutron, keystone, network_name=self.external_gateway)
                if ext_net:
                    ext_gw['network_id'] = ext_net.id
                    out['external_gateway_info'] = ext_gw
                else:
                    raise RouterConfigError(
                        'Could not find the external network named - ' +
                        self.external_gateway)
        finally:
            keystone_utils.close_session(session)

        return {'router': out}


class RouterConfigError(Exception):
    """
    Exception to be thrown when router settings attributes are incorrect
    """
