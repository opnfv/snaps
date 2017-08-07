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


class Project:
    """
    SNAPS domain class for Projects. Should contain attributes that
    are shared amongst cloud providers
    """
    def __init__(self, name, project_id, domain_id=None):
        """
        Constructor
        :param name: the project's name
        :param project_id: the project's id
        :param domain_id: the project's domain id
        """
        self.name = name
        self.id = project_id
        self.domain_id = domain_id

    def __eq__(self, other):
        return self.name == other.name and self.id == other.id


class Domain:
    """
    SNAPS domain class for OpenStack Keystone v3+ domains.
    """
    def __init__(self, name, domain_id=None):
        """
        Constructor
        :param name: the project's name
        :param domain_id: the project's domain id
        """
        self.name = name
        self.id = domain_id

    def __eq__(self, other):
        return self.name == other.name and self.id == other.id


class ComputeQuotas:
    """
    SNAPS domain class for holding project quotas for compute services
    """
    def __init__(self, nova_quotas=None, **kwargs):
        """
        Constructor
        :param nova_quotas: the OS nova quota object
        """
        if nova_quotas:
            self.metadata_items = nova_quotas.metadata_items
            self.cores = nova_quotas.cores  # aka. VCPUs
            self.instances = nova_quotas.instances
            self.injected_files = nova_quotas.injected_files
            self.injected_file_content_bytes = nova_quotas.injected_file_content_bytes
            self.ram = nova_quotas.ram
            self.fixed_ips = nova_quotas.fixed_ips
            self.key_pairs = nova_quotas.key_pairs
        else:
            self.metadata_items = kwargs.get('metadata_items')
            self.cores = kwargs.get('cores')  # aka. VCPUs
            self.instances = kwargs.get('instances')
            self.injected_files = kwargs.get('injected_files')
            self.injected_file_content_bytes = kwargs.get(
                'injected_file_content_bytes')
            self.ram = kwargs.get('ram')
            self.fixed_ips = kwargs.get('fixed_ips')
            self.key_pairs = kwargs.get('key_pairs')

    def __eq__(self, other):
        return (self.metadata_items == other.metadata_items and
                self.cores == other.cores and
                self.instances == other.instances and
                self.injected_files == other.injected_files and
                self.injected_file_content_bytes == other.injected_file_content_bytes and
                self.fixed_ips == other.fixed_ips and
                self.key_pairs == other.key_pairs)


class NetworkQuotas:
    """
    SNAPS domain class for holding project quotas for networking services
    """
    def __init__(self, **neutron_quotas):
        """
        Constructor
        :param neutron_quotas: the OS network quota object
        """

        # Networks settings here
        self.security_group = neutron_quotas['security_group']
        self.security_group_rule = neutron_quotas['security_group_rule']
        self.floatingip = neutron_quotas['floatingip']
        self.network = neutron_quotas['network']
        self.port = neutron_quotas['port']
        self.router = neutron_quotas['router']
        self.subnet = neutron_quotas['subnet']

    def __eq__(self, other):
        return (self.security_group == other.security_group and
                self.security_group_rule == other.security_group_rule and
                self.floatingip == other.floatingip and
                self.network == other.network and
                self.port == other.port and
                self.router == other.router and
                self.subnet == other.subnet)
