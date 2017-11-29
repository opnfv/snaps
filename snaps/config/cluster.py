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
import enum
from neutronclient.common.utils import str2bool

from snaps.openstack.utils import magnum_utils


class ClusterConfig(object):
    """
    Configuration settings for OpenStack cluster creation
    see https://developer.openstack.org/api-ref/
    """

    def __init__(self, **kwargs):
        """
        Constructor
        :param name: the cluster's name (required)
        :param cluster_template_name: the name of the associated cluster
                                      template (required)
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
                              servers. (optional)
        :param master_count: The number of servers that will serve as master
                             for the bay/cluster (default = 1)
        :param node_count: The number of servers that will serve as node in the
                           bay/cluster (default = 1)
        :param docker_volume_size: The size in GB for the local storage on each
                                   server for the Docker daemon to cache the
                                   images and host the containers. Cinder
                                   volumes provide the storage. The default is
                                   25 GB. For the devicemapper storage driver,
                                   the minimum value is 3GB. For the overlay
                                   storage driver, the minimum value is 1GB
        :param create_timeout: The timeout for cluster creation in minutes. The
                               value expected is a positive integer and the
                               default is 60 minutes. If the timeout is reached
                               during cluster creation process, the operation
                               will be aborted and the cluster status will be
                               set to CREATE_FAILED (???)
        """
        self.name = kwargs.get('name')
        self.cluster_template_name = kwargs.get('cluster_template_name')
        self.discovery_url = kwargs.get('discovery_url')
        self.master_count = kwargs.get('master_count')
        self.node_count = kwargs.get('node_count')
        self.docker_volume_size = kwargs.get('docker_volume_size')
        self.create_timeout = kwargs.get('create_timeout')

        if not self.name or not self.cluster_template_name:
            raise ClusterConfigError(
                'The attributes name, cluster_template_name are required for '
                'ClusterConfig')

    def magnum_dict(self, magnum):
        """
        Returns a dictionary object representing this object.
        This is meant to be sent into as kwargs into the Magnum client
        :param magnum: the magnum client
        :return: the dictionary object
        """
        out = dict()

        if self.name:
            out['name'] = self.name
        if self.cluster_template_name:
            cluster_tmplt = magnum_utils.get_cluster_template(
                magnum, template_name=self.cluster_template_name)
            out['cluster_template_id'] = cluster_tmplt.id
        if self.discovery_url:
            out['discovery_url'] = self.discovery_url
        if self.master_count:
            out['master_count'] = self.master_count
        if self.node_count:
            out['node_count'] = self.node_count
        if self.docker_volume_size:
            out['docker_volume_size'] = self.docker_volume_size
        if self.create_timeout:
            out['create_timeout'] = self.create_timeout
        return out


class ClusterConfigError(Exception):
    """
    Exception to be thrown when a cluster configuration is incorrect
    """
