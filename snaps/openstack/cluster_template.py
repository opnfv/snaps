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

from magnumclient.common.apiclient.exceptions import NotFound

from snaps.openstack.openstack_creator import OpenStackMagnumObject
from snaps.openstack.utils import magnum_utils

__author__ = 'spisarski'

logger = logging.getLogger('cluster_template')


class OpenStackClusterTemplate(OpenStackMagnumObject):
    """
    Class responsible for managing an volume in OpenStack
    """

    def __init__(self, os_creds, cluster_template_config):
        """
        Constructor
        :param os_creds: The OpenStack connection credentials
        :param cluster_template_config: The volume type settings
        :return:
        """
        super(self.__class__, self).__init__(os_creds)

        self.cluster_template_config = cluster_template_config
        self.__cluster_template = None

    def initialize(self):
        """
        Loads the existing Volume
        :return: The Volume domain object or None
        """
        super(self.__class__, self).initialize()

        self.__cluster_template = magnum_utils.get_cluster_template(
            self._magnum, template_config=self.cluster_template_config)

        return self.__cluster_template

    def create(self):
        """
        Creates the volume in OpenStack if it does not already exist and
        returns the domain Volume object
        :return: The Volume domain object or None
        """
        self.initialize()

        if not self.__cluster_template:
            self.__cluster_template = magnum_utils.create_cluster_template(
                self._magnum, self.cluster_template_config)
            logger.info(
                'Created volume type with name - %s',
                self.cluster_template_config.name)

        return self.__cluster_template

    def clean(self):
        """
        Cleanse environment of all artifacts
        :return: void
        """
        if self.__cluster_template:
            try:
                magnum_utils.delete_cluster_template(
                    self._magnum, self.__cluster_template.id)
            except NotFound:
                pass

        self.__cluster_template = None

        super(self.__class__, self).clean()

    def get_cluster_template(self):
        """
        Returns the domain Volume object as it was populated when create() was
        called
        :return: the object
        """
        return self.__cluster_template
