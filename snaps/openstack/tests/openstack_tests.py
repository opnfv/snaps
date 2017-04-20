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
import re

from snaps import file_utils
from snaps.openstack.utils import glance_utils
from snaps.openstack.create_network import NetworkSettings, SubnetSettings
from snaps.openstack.create_router import RouterSettings
from snaps.openstack.os_credentials import OSCreds, ProxySettings
from snaps.openstack.create_image import ImageSettings
import logging

__author__ = 'spisarski'


logger = logging.getLogger('openstack_tests')


def get_credentials(os_env_file=None, proxy_settings_str=None, ssh_proxy_cmd=None, dev_os_env_file=None):
    """
    Returns the OpenStack credentials object. It first attempts to retrieve them from a standard OpenStack source file.
    If that file is None, it will attempt to retrieve them with a YAML file.
    it will retrieve them from a
    :param os_env_file: the OpenStack source file
    :param proxy_settings_str: proxy settings string <host>:<port> (optional)
    :param ssh_proxy_cmd: the SSH proxy command for your environment (optional)
    :param dev_os_env_file: the YAML file to retrieve both the OS credentials and proxy settings
    :return: the SNAPS credentials object
    """
    if os_env_file:
        logger.debug('Reading RC file - ' + os_env_file)
        config = file_utils.read_os_env_file(os_env_file)
        proj_name = config.get('OS_PROJECT_NAME')
        if not proj_name:
            proj_name = config.get('OS_TENANT_NAME')

        proj_domain_id = 'default'
        user_domain_id = 'default'

        if config.get('OS_PROJECT_DOMAIN_ID'):
            proj_domain_id = config['OS_PROJECT_DOMAIN_ID']
        if config.get('OS_USER_DOMAIN_ID'):
            user_domain_id = config['OS_USER_DOMAIN_ID']
        if config.get('OS_IDENTITY_API_VERSION'):
            version = int(config['OS_IDENTITY_API_VERSION'])
        else:
            version = 2

        proxy_settings = None
        if proxy_settings_str:
            tokens = re.split(':', proxy_settings_str)
            proxy_settings = ProxySettings(tokens[0], tokens[1], ssh_proxy_cmd)

        os_creds = OSCreds(username=config['OS_USERNAME'],
                           password=config['OS_PASSWORD'],
                           auth_url=config['OS_AUTH_URL'],
                           project_name=proj_name,
                           identity_api_version=version,
                           user_domain_id=user_domain_id,
                           project_domain_id=proj_domain_id,
                           proxy_settings=proxy_settings)
    else:
        logger.info('Reading development os_env file - ' + dev_os_env_file)
        config = file_utils.read_yaml(dev_os_env_file)
        identity_api_version = config.get('identity_api_version')
        if not identity_api_version:
            identity_api_version = 2

        image_api_version = config.get('image_api_version')
        if not image_api_version:
            image_api_version = glance_utils.VERSION_2

        proxy_settings = None
        proxy_str = config.get('http_proxy')
        if proxy_str:
            tokens = re.split(':', proxy_str)
            proxy_settings = ProxySettings(tokens[0], tokens[1], config.get('ssh_proxy_cmd'))

        os_creds = OSCreds(username=config['username'], password=config['password'],
                           auth_url=config['os_auth_url'], project_name=config['project_name'],
                           identity_api_version=identity_api_version, image_api_version=image_api_version,
                           proxy_settings=proxy_settings)

    logger.info('OS Credentials = ' + str(os_creds))
    return os_creds


def cirros_url_image(name, url=None):
    if not url:
        url = 'http://download.cirros-cloud.net/0.3.4/cirros-0.3.4-x86_64-disk.img'
    return ImageSettings(name=name, image_user='cirros', img_format='qcow2', url=url)


def file_image_test_settings(name, file_path):
    return ImageSettings(name=name, image_user='cirros', img_format='qcow2',
                         image_file=file_path)


def centos_url_image(name, url=None):
    if not url:
        url = 'http://cloud.centos.org/centos/7/images/CentOS-7-x86_64-GenericCloud.qcow2'
    return ImageSettings(
        name=name, image_user='centos', img_format='qcow2', url=url,
        nic_config_pb_loc='./provisioning/ansible/centos-network-setup/playbooks/configure_host.yml')


def ubuntu_url_image(name, url=None):
    if not url:
        url = 'http://uec-images.ubuntu.com/releases/trusty/14.04/ubuntu-14.04-server-cloudimg-amd64-disk1.img'
    return ImageSettings(
        name=name, image_user='ubuntu', img_format='qcow2', url=url,
        nic_config_pb_loc='./provisioning/ansible/ubuntu-network-setup/playbooks/configure_host.yml')


def get_priv_net_config(net_name, subnet_name, router_name=None, cidr='10.55.0.0/24', external_net=None):
    return OSNetworkConfig(net_name, subnet_name, cidr, router_name, external_gateway=external_net)


def get_pub_net_config(net_name, subnet_name=None, router_name=None, cidr='10.55.1.0/24', external_net=None):
    return OSNetworkConfig(net_name, subnet_name, cidr, router_name, external_gateway=external_net)


class OSNetworkConfig:
    """
    Represents the settings required for the creation of a network in OpenStack
    """

    def __init__(self, net_name, subnet_name=None, subnet_cidr=None, router_name=None, external_gateway=None):

        if subnet_name and subnet_cidr:
            self.network_settings = NetworkSettings(
                name=net_name, subnet_settings=[SubnetSettings(cidr=subnet_cidr, name=subnet_name)])
        else:
            self.network_settings = NetworkSettings(name=net_name)

        if router_name:
            if subnet_name:
                self.router_settings = RouterSettings(name=router_name, external_gateway=external_gateway,
                                                      internal_subnets=[subnet_name])
            else:
                self.router_settings = RouterSettings(name=router_name, external_gateway=external_gateway)
