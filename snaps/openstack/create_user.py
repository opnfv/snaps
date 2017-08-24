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
from snaps.openstack.os_credentials import OSCreds
from snaps.openstack.utils import keystone_utils

__author__ = 'spisarski'

logger = logging.getLogger('create_user')


class OpenStackUser:
    """
    Class responsible for creating a user in OpenStack
    """

    def __init__(self, os_creds, user_settings):
        """
        Constructor
        :param os_creds: The OpenStack connection credentials
        :param user_settings: The user settings
        :return:
        """
        self.__os_creds = os_creds
        self.user_settings = user_settings
        self.__user = None
        self.__keystone = None

    def create(self, cleanup=False):
        """
        Creates the user in OpenStack if it does not already exist
        :param cleanup: Denotes whether or not this is being called for cleanup
        :return: The OpenStack user object
        """
        self.__keystone = keystone_utils.keystone_client(self.__os_creds)
        self.__user = keystone_utils.get_user(self.__keystone,
                                              self.user_settings.name)
        if not self.__user and not cleanup:
            self.__user = keystone_utils.create_user(self.__keystone,
                                                     self.user_settings)

        return self.__user

    def clean(self):
        """
        Cleanse environment of user
        :return: void
        """
        if self.__user:
            try:
                keystone_utils.delete_user(self.__keystone, self.__user)
            except NotFound:
                pass
            self.__user = None

    def get_user(self):
        """
        Returns the OpenStack user object populated in create()
        :return: the Object or None if not created
        """
        return self.__user

    def get_os_creds(self, project_name=None):
        """
        Returns an OSCreds object based on this user account and a project
        :param project_name: the name of the project to leverage in the
                             credentials
        :return:
        """
        return OSCreds(
            username=self.user_settings.name,
            password=self.user_settings.password,
            auth_url=self.__os_creds.auth_url,
            project_name=project_name,
            identity_api_version=self.__os_creds.identity_api_version,
            user_domain_name=self.__os_creds.user_domain_name,
            user_domain_id=self.__os_creds.user_domain_id,
            project_domain_name=self.__os_creds.project_domain_name,
            project_domain_id=self.__os_creds.project_domain_id,
            interface=self.__os_creds.interface,
            proxy_settings=self.__os_creds.proxy_settings,
            cacert=self.__os_creds.cacert)


class UserSettings:
    def __init__(self, **kwargs):

        """
        Constructor
        :param name: the user's name (required)
        :param password: the user's password (required)
        :param project_name: the user's primary project name (optional)
        :param domain_name: the user's domain name (default='default'). For v3
                            APIs
        :param email: the user's email address (optional)
        :param enabled: denotes whether or not the user is enabled
                        (default True)
        :param roles: dict where key is the role's name and value is the name
                      the project to associate with the role
        """

        self.name = kwargs.get('name')
        self.password = kwargs.get('password')
        self.project_name = kwargs.get('project_name')
        self.email = kwargs.get('email')
        self.domain_name = kwargs.get('domain_name', 'Default')
        self.enabled = kwargs.get('enabled', True)
        self.roles = kwargs.get('roles', dict())

        if not self.name or not self.password:
            raise UserSettingsException(
                'The attributes name and password are required for '
                'UserSettings')

        if not isinstance(self.enabled, bool):
            raise UserSettingsException('The attribute enabled must be of type'
                                        ' boolean')


class UserSettingsException(Exception):
    """
    Raised when there is a problem with the values set in the UserSettings
    class
    """
