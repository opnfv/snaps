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


class ProjectConfig(object):
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
        :param users: list of users to associate project to (optional)
        :param enabled: denotes whether or not the project is enabled
                        (default True)
        :param quotas: quota values to override (optional)
        """

        self.name = kwargs.get('name')
        self.domain_name = kwargs.get(
            'domain_name', kwargs.get('domain', 'Default'))

        self.description = kwargs.get('description')
        if kwargs.get('enabled') is not None:
            self.enabled = kwargs['enabled']
        else:
            self.enabled = True

        self.users = kwargs.get('users', list())

        self.quotas = kwargs.get('quotas')

        if not self.name:
            raise ProjectConfigError(
                "The attribute name is required for ProjectConfig")


class ProjectConfigError(Exception):
    """
    Exception to be thrown when project settings attributes are incorrect
    """
