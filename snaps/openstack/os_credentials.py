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
from neutronclient.common.utils import str2bool
import numbers
from snaps import file_utils
from snaps.openstack.utils import glance_utils, keystone_utils, cinder_utils

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
        :param heat_api_version: The OpenStack's API version to use for Heat
                                    clients
        :param volume_api_version: The OpenStack's API version to use
                                   for Cinder clients
        :param magnum_api_version: The OpenStack's API version to use
                                   for magnum clients
        :param user_domain_id: Used for v3 APIs (default='default')
        :param user_domain_name: Used for v3 APIs (default='Default')
        :param project_domain_id: Used for v3 APIs (default='default')
        :param project_domain_name: Used for v3 APIs (default='Default')
        :param interface: Used to specify the endpoint type for keystone as
                          public, admin, internal
        :param proxy_settings: instance of os_credentials.ProxySettings class
        :param cacert: True for https or the certification file for https
                       verification (default=False)
        :param region_name: the region (optional default = None)
        """
        self.username = kwargs.get('username')
        self.password = kwargs.get('password')
        self.auth_url = kwargs.get('auth_url')
        self.project_name = kwargs.get('project_name')

        if kwargs.get('identity_api_version') is None:
            self.identity_api_version = keystone_utils.V2_VERSION_NUM
        else:
            self.identity_api_version = float(kwargs['identity_api_version'])

        if kwargs.get('image_api_version') is None:
            self.image_api_version = glance_utils.VERSION_2
        else:
            self.image_api_version = float(kwargs['image_api_version'])

        if kwargs.get('network_api_version') is None:
            self.network_api_version = 2
        else:
            self.network_api_version = float(kwargs['network_api_version'])

        if kwargs.get('compute_api_version') is None:
            self.compute_api_version = 2
        else:
            self.compute_api_version = float(kwargs['compute_api_version'])

        if kwargs.get('heat_api_version') is None:
            self.heat_api_version = 1
        else:
            val = kwargs['heat_api_version']
            ver = float(val)
            self.heat_api_version = int(ver)

        if kwargs.get('volume_api_version') is None:
            self.volume_api_version = cinder_utils.VERSION_2
        else:
            self.volume_api_version = float(kwargs['volume_api_version'])

        if kwargs.get('magnum_api_version') is None:
            self.magnum_api_version = 1
        else:
            self.magnum_api_version = float(kwargs['magnum_api_version'])

        self.user_domain_id = kwargs.get('user_domain_id', 'default')

        if kwargs.get('user_domain_name') is None:
            self.user_domain_name = 'Default'
        else:
            self.user_domain_name = kwargs['user_domain_name']

        self.project_domain_id = kwargs.get('project_domain_id', 'default')

        if kwargs.get('project_domain_name') is None:
            self.project_domain_name = 'Default'
        else:
            self.project_domain_name = kwargs['project_domain_name']

        if kwargs.get('interface') is None:
            self.interface = 'public'
        else:
            self.interface = kwargs['interface']

        self.region_name = kwargs.get('region_name', None)

        self.cacert = False
        if kwargs.get('cacert') is not None:
            if isinstance(kwargs.get('cacert'), str):
                if file_utils.file_exists(kwargs['cacert']):
                    self.cacert = kwargs['cacert']
                else:
                    self.cacert = str2bool(kwargs['cacert'])
            else:
                self.cacert = kwargs['cacert']

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

        self.auth_url = self.__scrub_auth_url()

    def __scrub_auth_url(self):
        """
        As the Python APIs are have more stringent requirements around how the
        auth_url is formed than the CLI, this method will scrub any version
        from the end of
        :return:
        """
        auth_url_tokens = self.auth_url.rstrip('/').split('/')
        last_token = auth_url_tokens[len(auth_url_tokens) - 1]
        token_iters = len(auth_url_tokens)
        if last_token.startswith('v'):
            token_iters -= 1
        if self.identity_api_version == keystone_utils.V2_VERSION_NUM:
            last_token = keystone_utils.V2_VERSION_STR
        else:
            last_token = 'v' + str(int(self.identity_api_version))

        new_url = None
        for ctr in range(0, token_iters):
            if new_url:
                new_url += '/' + auth_url_tokens[ctr]
            else:
                new_url = auth_url_tokens[ctr]
        new_url += '/' + last_token

        return new_url

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
                ', heat_api_version=' + str(self.heat_api_version) +
                ', user_domain_id=' + str(self.user_domain_id) +
                ', user_domain_name=' + str(self.user_domain_name) +
                ', project_domain_id=' + str(self.project_domain_id) +
                ', project_domain_name=' + str(self.project_domain_name) +
                ', interface=' + str(self.interface) +
                ', region_name=' + str(self.region_name) +
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
        :param https_host: the HTTPS proxy host (defaults to host)
        :param https_port: the HTTPS proxy port (defaults to port)
        :param ssh_proxy_cmd: the SSH proxy command string (optional)
        """
        self.host = kwargs.get('host')
        self.port = kwargs.get('port')
        if self.port and isinstance(self.port, numbers.Number):
            self.port = str(self.port)

        self.https_host = kwargs.get('https_host', self.host)
        self.https_port = kwargs.get('https_port', self.port)
        if self.https_port and isinstance(self.https_port, numbers.Number):
            self.https_port = str(self.https_port)

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
