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

from keystoneclient.exceptions import NotFound, Conflict

from snaps.config.project import ProjectConfig
from snaps.openstack.openstack_creator import OpenStackIdentityObject
from snaps.openstack.utils import keystone_utils, neutron_utils, nova_utils

__author__ = 'spisarski'

logger = logging.getLogger('create_image')


class OpenStackProject(OpenStackIdentityObject):
    """
    Class responsible for managing a project/project in OpenStack
    """

    def __init__(self, os_creds, project_settings):
        """
        Constructor
        :param os_creds: The OpenStack connection credentials
        :param project_settings: The project's settings
        :return:
        """
        super(self.__class__, self).__init__(os_creds)

        self.project_settings = project_settings
        self.__project = None
        self.__role = None
        self.__role_name = self.project_settings.name + '-role'

    def initialize(self):
        """
        Loads the existing Project object if it exists
        :return: The Project domain object
        """
        super(self.__class__, self).initialize()

        self.__project = keystone_utils.get_project(
            keystone=self._keystone, project_settings=self.project_settings)
        return self.__project

    def create(self):
        """
        Creates a Project/Tenant in OpenStack if it does not already exist
        :return: The Project domain object
        """
        self.initialize()

        if not self.__project:
            self.__project = keystone_utils.create_project(
                self._keystone, self.project_settings)
            for username in self.project_settings.users:
                user = keystone_utils.get_user(self._keystone, username)
                if user:
                    try:
                        self.assoc_user(user)
                    except Conflict as e:
                        logger.warn('Unable to associate user %s due to %s',
                                    user.name, e)

            if self.project_settings.quotas:
                quota_dict = self.project_settings.quotas
                nova = nova_utils.nova_client(self._os_creds, self._os_session)
                quotas = nova_utils.get_compute_quotas(nova, self.__project.id)
                if quotas:
                    if 'cores' in quota_dict:
                        quotas.cores = quota_dict['cores']
                    if 'instances' in quota_dict:
                        quotas.instances = quota_dict['instances']
                    if 'injected_files' in quota_dict:
                        quotas.injected_files = quota_dict['injected_files']
                    if 'injected_file_content_bytes' in quota_dict:
                        quotas.injected_file_content_bytes = \
                            quota_dict['injected_file_content_bytes']
                    if 'ram' in quota_dict:
                        quotas.ram = quota_dict['ram']
                    if 'fixed_ips' in quota_dict:
                        quotas.fixed_ips = quota_dict['fixed_ips']
                    if 'key_pairs' in quota_dict:
                        quotas.key_pairs = quota_dict['key_pairs']

                    nova_utils.update_quotas(nova, self.__project.id, quotas)

        return self.__project

    def clean(self):
        """
        Cleanse environment of all artifacts
        :return: void
        """
        if self.__project:
            # Delete security group 'default' if exists
            neutron = neutron_utils.neutron_client(
                self._os_creds, self._os_session)
            try:
                default_sec_grp = neutron_utils.get_security_group(
                    neutron, self._keystone, sec_grp_name='default',
                    project_name=self.__project.name)
                if default_sec_grp:
                    try:
                        neutron_utils.delete_security_group(
                            neutron, default_sec_grp)
                    except:
                        pass
            finally:
                neutron.httpclient.session.session.close()

            # Delete Project
            try:
                keystone_utils.delete_project(self._keystone, self.__project)
            except NotFound:
                pass
            self.__project = None

        if self.__role:
            try:
                keystone_utils.delete_role(self._keystone, self.__role)
            except NotFound:
                pass
            self.__project = None

        # Final role check in case init was done from an existing instance
        role = keystone_utils.get_role_by_name(
            self._keystone, self.__role_name)
        if role:
            keystone_utils.delete_role(self._keystone, role)

        super(self.__class__, self).clean()

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
            self.__role = keystone_utils.get_role_by_name(
                self._keystone, self.__role_name)
            if not self.__role:
                self.__role = keystone_utils.create_role(
                    self._keystone, self.__role_name)

        keystone_utils.grant_user_role_to_project(self._keystone, self.__role,
                                                  user, self.__project)

    def get_compute_quotas(self):
        """
        Returns the compute quotas as an instance of the ComputeQuotas class
        :return:
        """
        nova = nova_utils.nova_client(self._os_creds, self._os_session)

        try:
            return nova_utils.get_compute_quotas(nova, self.__project.id)
        finally:
            nova.client.session.session.close()

    def get_network_quotas(self):
        """
        Returns the network quotas as an instance of the NetworkQuotas class
        :return:
        """
        neutron = neutron_utils.neutron_client(
            self._os_creds, self._os_session)
        try:
            return neutron_utils.get_network_quotas(neutron, self.__project.id)
        finally:
            neutron.httpclient.session.session.close()

    def update_compute_quotas(self, compute_quotas):
        """
        Updates the compute quotas for this project
        :param compute_quotas: a ComputeQuotas object.
        """
        nova = nova_utils.nova_client(self._os_creds, self._os_session)
        try:
            nova_utils.update_quotas(nova, self.__project.id, compute_quotas)
        finally:
            nova.client.session.session.close()

    def update_network_quotas(self, network_quotas):
        """
        Updates the network quotas for this project
        :param network_quotas: a NetworkQuotas object.
        """
        neutron = neutron_utils.neutron_client(
            self._os_creds, self._os_session)
        try:
            neutron_utils.update_quotas(
                neutron, self.__project.id, network_quotas)
        finally:
            neutron.httpclient.session.session.close()


class ProjectSettings(ProjectConfig):
    """
    Class to hold the configuration settings required for creating OpenStack
    project objects
    deprecated
    """

    def __init__(self, **kwargs):
        from warnings import warn
        warn('Use snaps.config.project.ProjectConfig instead',
             DeprecationWarning)
        super(self.__class__, self).__init__(**kwargs)
