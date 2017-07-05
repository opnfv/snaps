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
__author__ = 'spisarski'


class OSCreds:
    """
    Represents the credentials required to connect with OpenStack servers
    """

    def __init__(self, **kwargs):
        """
        Constructor
        :param username: The user (required)
        :param password: The user's password (required)
        :param auth_url: The OpenStack cloud's authorization URL (required)
        :param project_name: The project/tenant name
        :param identity_api_version: The OpenStack's API version to use for
                                     Keystone clients
        :param image_api_version: The OpenStack's API version to use for Glance
                                  clients
        :param network_api_version: The OpenStack's API version to use for
                                    Neutron clients
        :param compute_api_version: The OpenStack's API version to use for Nova
                                    clients
        :param user_domain_id: Used for v3 APIs
        :param project_domain_id: Used for v3 APIs
        :param interface: Used to specify the endpoint type for keystone as
                          public, admin, internal
        :param proxy_settings: instance of os_credentials.ProxySettings class
        :param cacert: Default to be True for http, or the certification file
                       is specified for https verification, or set to be False
                       to disable server certificate verification without cert
                       file
        """
        self.username = kwargs.get('username')
        self.password = kwargs.get('password')
        self.auth_url = kwargs.get('auth_url')
        self.project_name = kwargs.get('project_name')
        self.identity_api_version = kwargs.get('identity_api_version', 2)
        self.image_api_version = kwargs.get('image_api_version', 2)
        self.network_api_version = kwargs.get('network_api_version', 2)
        self.compute_api_version = kwargs.get('compute_api_version', 2)
        self.user_domain_id = kwargs.get('user_domain_id', 'default')
        self.project_domain_id = kwargs.get('project_domain_id', 'default')
        self.interface = kwargs.get('interface', 'admin')
        self.cacert = kwargs.get('cacert', True)

        if isinstance(kwargs.get('proxy_settings'), ProxySettings):
            self.proxy_settings = kwargs.get('proxy_settings')
        elif isinstance(kwargs.get('proxy_settings'), dict):
            self.proxy_settings = ProxySettings(**kwargs.get('proxy_settings'))
        else:
            self.proxy_settings = None

        if (not self.username or not self.password or not self.auth_url
                or not self.project_name):
            raise OSCredsError('username, password, auth_url, and project_name'
                               ' are required')

        auth_url_tokens = self.auth_url.split('/')
        last_token = auth_url_tokens[len(auth_url_tokens) - 1]
        if len(last_token) == 0:
            last_token = auth_url_tokens[len(auth_url_tokens) - 2]

        if not last_token.startswith('v'):
            raise OSCredsError('auth_url last toke must start with \'v\'')

    @property
    def __str__(self):
        """Converts object to a string"""
        return ('OSCreds - username=' + str(self.username) +
                ', password=' + str(self.password) +
                ', auth_url=' + str(self.auth_url) +
                ', project_name=' + str(self.project_name) +
                ', identity_api_version=' + str(self.identity_api_version) +
                ', image_api_version=' + str(self.image_api_version) +
                ', network_api_version=' + str(self.network_api_version) +
                ', compute_api_version=' + str(self.compute_api_version) +
                ', user_domain_id=' + str(self.user_domain_id) +
                ', interface=' + str(self.interface) +
                ', proxy_settings=' + str(self.proxy_settings) +
                ', cacert=' + str(self.cacert))


class ProxySettings:
    """
    Represents the information required for sending traffic (HTTP & SSH)
    through a proxy
    """

    def __init__(self, **kwargs):
        """
        Constructor
        :param host: the HTTP proxy host
        :param port: the HTTP proxy port
        :param ssh_proxy_cmd: the SSH proxy command string (optional)
        """
        self.host = kwargs.get('host')
        self.port = kwargs.get('port')
        self.ssh_proxy_cmd = kwargs.get('ssh_proxy_cmd')

        if not self.host or not self.port:
            raise ProxySettingsError('host & port are required')

    def __str__(self):
        """Converts object to a string"""
        return 'ProxySettings - host=' + str(self.host) + \
               ', port=' + str(self.port) + \
               ', ssh_proxy_cmd=' + str(self.ssh_proxy_cmd)


class ProxySettingsError(Exception):
    """
    Exception to be thrown when an OSCred are invalid
    """


class OSCredsError(Exception):
    """
    Exception to be thrown when an OSCred are invalid
    """
