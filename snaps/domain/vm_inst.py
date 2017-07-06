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


class VmInst:
    """
    SNAPS domain object for Images. Should contain attributes that
    are shared amongst cloud providers
    """
    def __init__(self, name, inst_id, networks):
        """
        Constructor
        :param name: the image's name
        :param inst_id: the instance's id
        :param networks: dict of networks where the key is the subnet name and
                         value is a list of associated IPs
        """
        self.name = name
        self.id = inst_id
        self.networks = networks


class FloatingIp:
    """
    SNAPS domain object for Images. Should contain attributes that
    are shared amongst cloud providers
    """
    def __init__(self, inst_id, ip):
        """
        Constructor
        :param inst_id: the floating ip's id
        :param ip: the IP address
        """
        self.id = inst_id
        self.ip = ip
