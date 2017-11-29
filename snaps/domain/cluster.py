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


class Cluster(object):
    """
    Class for OpenStack cluster domain object
    """

    def __init__(self, **kwargs):
        """
        Constructor
        :param uuid or id: the cluster template's UUID
        :param name: the cluster's name
        :param template_id: the name of the associated cluster template
        :param discovery_url: The custom discovery url for node discovery. This
                              is used by the COE to discover the servers that
                              have been created to host the containers. The
                              actual discovery mechanism varies with the COE.
                              In some cases, Magnum fills in the server info in
                              the discovery service.
                              In other cases, if the discovery_url is not
                              specified, Magnum will use the public discovery
                              service at 'https://discovery.etcd.io'.
                              In this case, Magnum will generate a unique url
                              here for each bay and store the info for the
                              servers.
        :param master_count: The number of servers that will serve as master
                             for the bay/cluster
        :param coe_version: The version of the COE
        :param container_version: The version of the container
        :param node_count: The number of servers that will serve as node in the
                           bay/cluster
        :param node_addresses: list of addresses for each node
        :param faults: dict of faults
        :param stack_id: ID of the associated stack
        :param status: the last known status code value
        :param status_reason: the last known status code reason
        :param create_timeout: The timeout for cluster creation in minutes
        :param created_at: The create timestamp
        :param updated_at: The update timestamp
        """
        self.id = kwargs.get('uuid', kwargs.get('id'))
        self.name = kwargs.get('name')
        self.template_id = kwargs.get('template_id')
        self.discovery_url = kwargs.get('discovery_url')
        self.master_count = kwargs.get('master_count')
        self.coe_version = kwargs.get('coe_version')
        self.node_count = kwargs.get('node_count')
        self.node_addresses = kwargs.get('node_addresses')
        self.faults = kwargs.get('faults')
        self.stack_id = kwargs.get('stack_id')
        self.status = kwargs.get('status')
        self.status_reason = kwargs.get('status_reason')
        self.create_timeout = kwargs.get('create_timeout')
        self.created_at = kwargs.get('created_at')
