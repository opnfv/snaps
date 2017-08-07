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

from keystoneclient.exceptions import NotFound

from snaps.openstack.utils import keystone_utils, neutron_utils, nova_utils

__author__ = 'spisarski'

logger = logging.getLogger('create_image')


class OpenStackProject:
    """
    Class responsible for creating a project/project in OpenStack
    """

    def __init__(self, os_creds, project_settings):
        """
        Constructor
        :param os_creds: The OpenStack connection credentials
        :param project_settings: The project's settings
        :return:
        """
        self.__os_creds = os_creds
        self.project_settings = project_settings
        self.__project = None
        self.__role = None
        self.__keystone = None

    def create(self, cleanup=False):
        """
        Creates the image in OpenStack if it does not already exist
        :param cleanup: Denotes whether or not this is being called for cleanup
        :return: The OpenStack Image object
        """
        self.__keystone = keystone_utils.keystone_client(self.__os_creds)
        self.__project = keystone_utils.get_project(
            keystone=self.__keystone, project_settings=self.project_settings)
        if self.__project:
            logger.info(
                'Found project with name - ' + self.project_settings.name)
        elif not cleanup:
            self.__project = keystone_utils.create_project(
                self.__keystone, self.project_settings)
        else:
            logger.info('Did not create image due to cleanup mode')

        return self.__project

    def clean(self):
        """
        Cleanse environment of all artifacts
        :return: void
        """
        if self.__project:
            # Delete security group 'default' if exists
            neutron = neutron_utils.neutron_client(self.__os_creds)
            default_sec_grp = neutron_utils.get_security_group(
                neutron, sec_grp_name='default',
                project_id=self.__project.id)
            if default_sec_grp:
                try:
                    neutron_utils.delete_security_group(
                        neutron, default_sec_grp)
                except:
                    pass

            # Delete Project
            try:
                keystone_utils.delete_project(self.__keystone, self.__project)
            except NotFound:
                pass
            self.__project = None

        if self.__role:
            try:
                keystone_utils.delete_role(self.__keystone, self.__role)
            except NotFound:
                pass
            self.__project = None

    def get_project(self):
        """
        Returns the OpenStack project object populated on create()
        :return:
        """
        return self.__project

    def assoc_user(self, user):
        """
        The user object to associate with the project
        :param user: the OpenStack User domain object to associate with project
        :return:
        """
        if not self.__role:
            self.__role = keystone_utils.create_role(
                self.__keystone, self.project_settings.name + '-role')

        keystone_utils.grant_user_role_to_project(self.__keystone, self.__role,
                                                  user, self.__project)

    def get_compute_quotas(self):
        """
        Returns the compute quotas as an instance of the ComputeQuotas class
        :return:
        """
        nova = nova_utils.nova_client(self.__os_creds)
        return nova_utils.get_compute_quotas(nova, self.__project.id)

    def get_network_quotas(self):
        """
        Returns the network quotas as an instance of the NetworkQuotas class
        :return:
        """
        neutron = neutron_utils.neutron_client(self.__os_creds)
        return neutron_utils.get_network_quotas(neutron, self.__project.id)

    def update_compute_quotas(self, compute_quotas):
        """
        Updates the compute quotas for this project
        :param compute_quotas: a ComputeQuotas object.
        """
        nova = nova_utils.nova_client(self.__os_creds)
        nova_utils.update_quotas(nova, self.__project.id, compute_quotas)

    def update_network_quotas(self, network_quotas):
        """
        Updates the network quotas for this project
        :param network_quotas: a NetworkQuotas object.
        """
        neutron = neutron_utils.neutron_client(self.__os_creds)
        neutron_utils.update_quotas(neutron, self.__project.id, network_quotas)


class ProjectSettings:
    """
    Class to hold the configuration settings required for creating OpenStack
    project objects
    """

    def __init__(self, **kwargs):

        """
        Constructor
        :param name: the project's name (required)
        :param domain or domain_name: the project's domain name
                                      (default = 'Default').
                                      Field is used for v3 clients
        :param description: the description (optional)
        :param enabled: denotes whether or not the user is enabled
                        (default True)
        """

        self.name = kwargs.get('name')
        self.domain_name = kwargs.get(
            'domain', kwargs.get('domain', 'Default'))

        self.description = kwargs.get('description')
        if kwargs.get('enabled') is not None:
            self.enabled = kwargs['enabled']
        else:
            self.enabled = True

        if not self.name:
            raise ProjectSettingsError(
                "The attribute name is required for ProjectSettings")


class ProjectSettingsError(Exception):
    """
    Exception to be thrown when project settings attributes are incorrect
    """
