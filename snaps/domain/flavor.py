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


class Flavor:
    """
    SNAPS domain object for Flavors. Should contain attributes that
    are shared amongst cloud providers
    """
    def __init__(self, **kwargs):
        """
        Constructor
        :param name: the flavor's name
        :param flavor_id or id: the flavor's id
        :param ram: the flavor's RAM in MB
        :param disk: the flavor's disk size in GB
        :param vcpus: the flavor's number of virtual CPUs
        :param ephemeral: the flavor's ephemeral disk in GB
        :param swap: the flavor's swap space in MB
        :param rxtx_factor: the flavor's RX/TX factor integer value
        :param is_public: denotes if flavor can be used by other projects
        """
        self.name = kwargs.get('name')
        self.id = kwargs.get('flavor_id', kwargs.get('id'))
        self.ram = kwargs.get('ram')
        self.disk = kwargs.get('disk')
        self.vcpus = kwargs.get('vcpus')
        self.ephemeral = kwargs.get('ephemeral')

        if kwargs.get('swap'):
            self.swap = int(kwargs.get('swap'))
        else:
            self.swap = None

        self.rxtx_factor = kwargs.get('rxtx_factor')
        self.is_public = kwargs.get('is_public')
