# Copyright (c) 2016 Cable Television Laboratories, Inc. ("CableLabs")
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


class FlavorConfig(object):
    """
    Configuration settings for OpenStack flavor creation
    """

    def __init__(self, **kwargs):
        """
        Constructor
        :param name: the flavor's name (required)
        :param flavor_id: the string ID (default 'auto')
        :param ram: the required RAM in MB (required)
        :param disk: the size of the root disk in GB (required)
        :param vcpus: the number of virtual CPUs (required)
        :param ephemeral: the size of the ephemeral disk in GB (default 0)
        :param swap: the size of the dedicated swap disk in GB (default 0)
        :param rxtx_factor: the receive/transmit factor to be set on ports if
                            backend supports QoS extension (default 1.0)
        :param is_public: denotes whether or not the flavor is public
                          (default True)
        :param metadata: freeform dict() for special metadata
        """
        self.name = kwargs.get('name')

        if kwargs.get('flavor_id'):
            self.flavor_id = kwargs['flavor_id']
        else:
            self.flavor_id = 'auto'

        self.ram = kwargs.get('ram')
        self.disk = kwargs.get('disk')
        self.vcpus = kwargs.get('vcpus')

        if kwargs.get('ephemeral'):
            self.ephemeral = kwargs['ephemeral']
        else:
            self.ephemeral = 0

        if kwargs.get('swap'):
            self.swap = kwargs['swap']
        else:
            self.swap = 0

        if kwargs.get('rxtx_factor'):
            self.rxtx_factor = kwargs['rxtx_factor']
        else:
            self.rxtx_factor = 1.0

        if kwargs.get('is_public') is not None:
            self.is_public = kwargs['is_public']
        else:
            self.is_public = True

        if kwargs.get('metadata'):
            self.metadata = kwargs['metadata']
        else:
            self.metadata = None

        if not self.name or not self.ram or not self.disk or not self.vcpus:
            raise FlavorConfigError(
                'The attributes name, ram, disk, and vcpus are required for'
                'FlavorConfig')

        if not isinstance(self.ram, int):
            raise FlavorConfigError('The ram attribute must be a integer')

        if not isinstance(self.disk, int):
            raise FlavorConfigError('The ram attribute must be a integer')

        if not isinstance(self.vcpus, int):
            raise FlavorConfigError('The vcpus attribute must be a integer')

        if self.ephemeral and not isinstance(self.ephemeral, int):
            raise FlavorConfigError(
                'The ephemeral attribute must be an integer')

        if self.swap and not isinstance(self.swap, int):
            raise FlavorConfigError('The swap attribute must be an integer')

        if self.rxtx_factor and not isinstance(self.rxtx_factor, (int, float)):
            raise FlavorConfigError(
                'The is_public attribute must be an integer or float')

        if self.is_public and not isinstance(self.is_public, bool):
            raise FlavorConfigError(
                'The is_public attribute must be a boolean')


class FlavorConfigError(Exception):
    """
    Exception to be thrown when a flavor configuration is incorrect
    """
