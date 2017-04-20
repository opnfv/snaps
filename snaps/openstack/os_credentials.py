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
__author__ = 'spisarski'


class OSCreds:
    """
    Represents the credentials required to connect with OpenStack servers
    """

    def __init__(self, username, password, auth_url, project_name, identity_api_version=2, image_api_version=2,
                 network_api_version=2, compute_api_version=2, user_domain_id='default', project_domain_id='default',
                 proxy_settings=None):
        """
        Constructor
        :param username: The user (required)
        :param password: The user's password (required)
        :param auth_url: The OpenStack cloud's authorization URL (required)
        :param project_name: The project/tenant name
        :param identity_api_version: The OpenStack's API version to use for Keystone clients
        :param image_api_version: The OpenStack's API version to use for Glance clients
        :param network_api_version: The OpenStack's API version to use for Neutron clients
        :param compute_api_version: The OpenStack's API version to use for Nova clients
        :param user_domain_id: Used for v3 APIs
        :param project_domain_id: Used for v3 APIs
        :param proxy_settings: instance of os_credentials.ProxySettings class
        """
        self.username = username
        self.password = password
        self.auth_url = auth_url
        self.project_name = project_name
        self.identity_api_version = identity_api_version
        self.image_api_version = image_api_version
        self.network_api_version = network_api_version
        self.compute_api_version = compute_api_version
        self.user_domain_id = user_domain_id
        self.project_domain_id = project_domain_id
        self.proxy_settings = proxy_settings

        if self.proxy_settings and not isinstance(self.proxy_settings, ProxySettings):
            raise Exception('proxy_settings must be an instance of the class ProxySettings')

        if self.auth_url:
            auth_url_tokens = self.auth_url.split('/')
            last_token = auth_url_tokens[len(auth_url_tokens) - 1]
            if len(last_token) == 0:
                last_token = auth_url_tokens[len(auth_url_tokens) - 2]

            if not last_token.startswith('v'):
                raise Exception('auth_url last toke must start with \'v\'')

    def __str__(self):
        """Converts object to a string"""
        return 'OSCreds - username=' + str(self.username) + \
               ', password=' + str(self.password) + \
               ', auth_url=' + str(self.auth_url) + \
               ', project_name=' + str(self.project_name) + \
               ', identity_api_version=' + str(self.identity_api_version) + \
               ', image_api_version=' + str(self.image_api_version) + \
               ', network_api_version=' + str(self.network_api_version) + \
               ', compute_api_version=' + str(self.compute_api_version) + \
               ', user_domain_id=' + str(self.user_domain_id) + \
               ', proxy_settings=' + str(self.proxy_settings)


class ProxySettings:
    """
    Represents the information required for sending traffic (HTTP & SSH) through a proxy
    """

    def __init__(self, host, port, ssh_proxy_cmd=None):
        """
        Constructor
        :param host: the HTTP proxy host
        :param port: the HTTP proxy port
        :param ssh_proxy_cmd: the SSH proxy command string (optional)
        """
        # TODO - Add necessary fields here when adding support for secure proxies

        self.host = host
        self.port = port
        self.ssh_proxy_cmd = ssh_proxy_cmd

        if not self.host and not self.port:
            raise Exception('host & port are required')

    def __str__(self):
        """Converts object to a string"""
        return 'ProxySettings - host=' + str(self.host) + \
               ', port=' + str(self.port) + \
               ', ssh_proxy_cmd=' + str(self.ssh_proxy_cmd)
