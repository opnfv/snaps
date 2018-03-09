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

import enum
from neutronclient.common.exceptions import NetworkNotFoundClient, Unauthorized

from snaps.config.network import NetworkConfig, SubnetConfig, PortConfig
from snaps.openstack.openstack_creator import OpenStackNetworkObject
from snaps.openstack.utils import neutron_utils

__author__ = 'spisarski'

logger = logging.getLogger('OpenStackNetwork')


class OpenStackNetwork(OpenStackNetworkObject):
    """
    Class responsible for managing a network in OpenStack
    """

    def __init__(self, os_creds, network_settings):
        """
        Constructor - all parameters are required
        :param os_creds: The credentials to connect with OpenStack
        :param network_settings: The settings used to create a network
        """
        super(self.__class__, self).__init__(os_creds)

        self.network_settings = network_settings

        # Attributes instantiated on create()
        self.__network = None

    def initialize(self):
        """
        Loads the existing OpenStack network/subnet
        :return: The Network domain object or None
        """
        super(self.__class__, self).initialize()

        try:
            self.__network = neutron_utils.get_network(
                self._neutron, self._keystone,
                network_settings=self.network_settings,
                project_name=self._os_creds.project_name)
        except Unauthorized as e:
            logger.warn('Unable to lookup network with name %s - %s',
                        self.network_settings.name, e)

        return self.__network

    def create(self):
        """
        Responsible for creating not only the network but then a private
        subnet, router, and an interface to the router.
        :return: the Network domain object
        """
        self.initialize()

        if not self.__network:
            self.__network = neutron_utils.create_network(
                self._neutron, self._os_creds, self.network_settings)
            logger.debug(
                'Network [%s] created successfully' % self.__network.id)

        return self.__network

    def clean(self):
        """
        Removes and deletes all items created in reverse order.
        """
        try:
            neutron_utils.delete_network(self._neutron, self.__network)
        except NetworkNotFoundClient:
            pass
        self.__network = None

        super(self.__class__, self).clean()

    def get_network(self):
        """
        Returns the created OpenStack network object
        :return: the OpenStack network object
        """
        return self.__network


class NetworkSettings(NetworkConfig):
    """
    Class to hold the configuration settings required for creating OpenStack
    Network objects
    deprecated
    """

    def __init__(self, **kwargs):
        from warnings import warn
        warn('Use snaps.config.network.NetworkConfig instead',
             DeprecationWarning)
        super(self.__class__, self).__init__(**kwargs)


class IPv6Mode(enum.Enum):
    """
    A rule's direction
    deprecated - use snaps.config.network.IPv6Mode
    """
    slaac = 'slaac'
    stateful = 'dhcpv6-stateful'
    stateless = 'dhcpv6-stateless'


class SubnetSettings(SubnetConfig):
    """
    Class to hold the configuration settings required for creating OpenStack
    Subnet objects
    deprecated
    """

    def __init__(self, **kwargs):
        from warnings import warn
        warn('Use snaps.config.network.SubnetConfig instead',
             DeprecationWarning)
        super(self.__class__, self).__init__(**kwargs)


class PortSettings(PortConfig):
    """
    Class to hold the configuration settings required for creating OpenStack
    Subnet objects
    deprecated
    """

    def __init__(self, **kwargs):
        from warnings import warn
        warn('Use snaps.config.network.PortConfig instead',
             DeprecationWarning)
        super(self.__class__, self).__init__(**kwargs)
