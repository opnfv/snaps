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
    def __init__(self, name, inst_id, image_id, flavor_id, networks,
                 keypair_name, sec_grp_names):
        """
        Constructor
        :param name: the image's name
        :param inst_id: the instance's id
        :param image_id: the instance's image id
        :param flavor_id: the ID used to spawn this instance
        :param networks: dict of networks where the key is the network name and
                         value is a list of associated IPs
        :param keypair_name: the name of the associated keypair
        :param sec_grp_names: list of security group names
        """
        self.name = name
        self.id = inst_id
        self.image_id = image_id
        self.flavor_id = flavor_id
        self.networks = networks
        self.keypair_name = keypair_name
        self.sec_grp_names = sec_grp_names

    def __eq__(self, other):
        return (self.name == other.name and
                self.id == other.id and
                self.image_id == other.image_id and
                self.flavor_id == other.flavor_id and
                self.networks == other.networks and
                self.keypair_name == other.keypair_name and
                self.sec_grp_names == other.sec_grp_names)


class FloatingIp:
    """
    SNAPS domain object for Images. Should contain attributes that
    are shared amongst cloud providers
    """
    def __init__(self, **kwargs):
        """
        Constructor
        :param id: the floating ip's id
        :param description: the description
        :param ip|floating_ip_address: the Floating IP address mapped to the
                                       'ip' attribute
        :param fixed_ip_address: the IP address of the tenant network
        :param floating_network_id: the ID of the external network
        :param port_id: the ID of the associated port
        :param router_id: the ID of the associated router
        :param project_id|tenant_id: the ID of the associated project mapped to
                                     the attribute 'project_id'
        :param
        """
        self.id = kwargs.get('id')
        self.description = kwargs.get('description')
        self.ip = kwargs.get('ip', kwargs.get('floating_ip_address'))
        self.fixed_ip_address = kwargs.get('fixed_ip_address')
        self.floating_network_id = kwargs.get('floating_network_id')
        self.port_id = kwargs.get('port_id')
        self.router_id = kwargs.get('router_id')
        self.project_id = kwargs.get('project_id', kwargs.get('tenant_id'))
