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

from snaps.config.user import UserConfig
from snaps.openstack.openstack_creator import OpenStackIdentityObject
from snaps.openstack.os_credentials import OSCreds
from snaps.openstack.utils import keystone_utils

__author__ = 'spisarski'

logger = logging.getLogger('create_user')


class OpenStackUser(OpenStackIdentityObject):
    """
    Class responsible for managing a user in OpenStack
    """

    def __init__(self, os_creds, user_settings):
        """
        Constructor
        :param os_creds: The OpenStack connection credentials
        :param user_settings: The user settings
        :return:
        """
        super(self.__class__, self).__init__(os_creds)

        self.user_settings = user_settings
        self.__user = None

    def initialize(self):
        """
        Creates the user in OpenStack if it does not already exist
        :return: The User domain object
        """
        super(self.__class__, self).initialize()

        self.__user = keystone_utils.get_user(self._keystone,
                                              self.user_settings.name)
        return self.__user

    def create(self, cleanup=False):
        """
        Creates a User if one does not already exist
        :return: The User domain object
        """
        self.initialize()
        if not self.__user:
            self.__user = keystone_utils.create_user(self._keystone,
                                                     self.user_settings)
        return self.__user

    def clean(self):
        """
        Cleanse environment of user
        :return: void
        """
        if self.__user:
            try:
                keystone_utils.delete_user(self._keystone, self.__user)
            except NotFound:
                pass
            self.__user = None

        super(self.__class__, self).clean()

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
        if not project_name:
            project_name = self._os_creds.project_name

        return OSCreds(
            username=self.user_settings.name,
            password=self.user_settings.password,
            auth_url=self._os_creds.auth_url,
            project_name=project_name,
            identity_api_version=self._os_creds.identity_api_version,
            image_api_version=self._os_creds.image_api_version,
            network_api_version=self._os_creds.network_api_version,
            compute_api_version=self._os_creds.compute_api_version,
            heat_api_version=self._os_creds.heat_api_version,
            volume_api_version=self._os_creds.volume_api_version,
            region_name=self._os_creds.region_name,
            user_domain_name=self._os_creds.user_domain_name,
            user_domain_id=self._os_creds.user_domain_id,
            project_domain_name=self._os_creds.project_domain_name,
            project_domain_id=self._os_creds.project_domain_id,
            interface=self._os_creds.interface,
            proxy_settings=self._os_creds.proxy_settings,
            cacert=self._os_creds.cacert)


class UserSettings(UserConfig):
    """
    Class to hold the configuration settings required for creating OpenStack
    user objects
    deprecated
    """

    def __init__(self, **kwargs):
        from warnings import warn
        warn('Use snaps.config.user.UserConfig instead',
             DeprecationWarning)
        super(self.__class__, self).__init__(**kwargs)
