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

from snaps.openstack.utils import keystone_utils

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
        self.__keystone = keystone_utils.keystone_client(self.__os_creds)

    def create(self, cleanup=False):
        """
        Creates the image in OpenStack if it does not already exist
        :param cleanup: Denotes whether or not this is being called for cleanup or not
        :return: The OpenStack Image object
        """
        self.__project = keystone_utils.get_project(keystone=self.__keystone,
                                                    project_name=self.project_settings.name)
        if self.__project:
            logger.info('Found project with name - ' + self.project_settings.name)
        elif not cleanup:
            self.__project = keystone_utils.create_project(self.__keystone, self.project_settings)
        else:
            logger.info('Did not create image due to cleanup mode')

        return self.__project

    def clean(self):
        """
        Cleanse environment of all artifacts
        :return: void
        """
        if self.__project:
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
        :param user: the OpenStack user object to associate with project
        :return:
        """
        if not self.__role:
            self.__role = keystone_utils.create_role(self.__keystone, self.project_settings.name + '-role')

        keystone_utils.assoc_user_to_project(self.__keystone, self.__role, user, self.__project)


class ProjectSettings:
    """
    Class to hold the configuration settings required for creating OpenStack project objects
    """
    def __init__(self, config=None, name=None, domain='default', description=None, enabled=True):

        """
        Constructor
        :param config: dict() object containing the configuration settings using the attribute names below as each
                       member's the key and overrides any of the other parameters.
        :param name: the project's name (required)
        :param domain: the project's domain name (default 'default'). Field is used for v3 clients
        :param description: the description (optional)
        :param enabled: denotes whether or not the user is enabled (default True)
        """

        if config:
            self.name = config.get('name')
            if config.get('domain'):
                self.domain = config['domain']
            else:
                self.domain = domain

            self.description = config.get('description')
            if config.get('enabled') is not None:
                self.enabled = config['enabled']
            else:
                self.enabled = enabled
        else:
            self.name = name
            self.domain = domain
            self.description = description
            self.enabled = enabled

        if not self.name:
            raise Exception("The attribute name is required for ProjectSettings")
