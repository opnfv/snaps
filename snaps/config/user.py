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


class UserConfig(object):
    """
    Class for holding user configurations
    """
    def __init__(self, **kwargs):

        """
        Constructor
        :param name: the user's name (required)
        :param password: the user's password (required)
        :param project_name: the user's primary project name (optional)
        :param domain_name: the user's domain name (default='Default'). For v3
                            APIs
        :param email: the user's email address (optional)
        :param enabled: denotes whether or not the user is enabled
                        (default True)
        :param roles: dict where key is the role's name and value is the name
                      of the project to associate with the role (optional)
        """

        self.name = kwargs.get('name')
        self.password = kwargs.get('password')
        self.project_name = kwargs.get('project_name')
        self.email = kwargs.get('email')
        self.domain_name = kwargs.get('domain_name', 'Default')
        self.enabled = kwargs.get('enabled', True)
        self.roles = kwargs.get('roles', dict())

        if not self.name or not self.password:
            raise UserConfigException(
                'The attributes name and password are required for '
                'UserConfig')

        if not isinstance(self.enabled, bool):
            raise UserConfigException(
                'The attribute enabled must be of type boolean')


class UserConfigException(Exception):
    """
    Raised when there is a problem with the values set in the UserConfig
    class
    """
