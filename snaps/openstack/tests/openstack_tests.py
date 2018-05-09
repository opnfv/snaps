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
import re

from snaps import file_utils
from snaps.config.flavor import FlavorConfig
from snaps.config.image import ImageConfig
from snaps.config.network import NetworkConfig, SubnetConfig
from snaps.config.router import RouterConfig
from snaps.openstack.os_credentials import OSCreds, ProxySettings

__author__ = 'spisarski'

logger = logging.getLogger('openstack_tests')

CIRROS_DEFAULT_IMAGE_URL =\
    'http://download.cirros-cloud.net/0.3.4/cirros-0.3.4-x86_64-disk.img'
CIRROS_DEFAULT_KERNEL_IMAGE_URL =\
    'http://download.cirros-cloud.net/0.3.4/cirros-0.3.4-x86_64-kernel'
CIRROS_DEFAULT_RAMDISK_IMAGE_URL =\
    'http://download.cirros-cloud.net/0.3.4/cirros-0.3.4-x86_64-initramfs'
CIRROS_USER = 'cirros'

CENTOS_DEFAULT_IMAGE_URL =\
    'http://cloud.centos.org/centos/7/images/' \
    'CentOS-7-x86_64-GenericCloud.qcow2'
CENTOS_USER = 'centos'

UBUNTU_DEFAULT_IMAGE_URL = \
    'http://uec-images.ubuntu.com/releases/trusty/14.04/' \
    'ubuntu-14.04-server-cloudimg-amd64-disk1.img'
UBUNTU_USER = 'ubuntu'

DEFAULT_IMAGE_FORMAT = 'qcow2'


def get_credentials(os_env_file=None, proxy_settings_str=None,
                    ssh_proxy_cmd=None, dev_os_env_file=None, overrides=None):
    """
    Returns the OpenStack credentials object. It first attempts to retrieve
    them from a standard OpenStack source file. If that file is None, it will
    attempt to retrieve them with a YAML file.
    :param os_env_file: the OpenStack source file
    :param proxy_settings_str: proxy settings string <host>:<port> (optional)
    :param ssh_proxy_cmd: the SSH proxy command for your environment (optional)
    :param dev_os_env_file: the YAML file to retrieve both the OS credentials
                            and proxy settings
    :param overrides: dict() containing values to override the credentials
                      found and passed in.
    :return: the SNAPS credentials object
    """
    if os_env_file:
        logger.debug('Reading RC file - ' + os_env_file)
        config = file_utils.read_os_env_file(os_env_file)
        proj_name = config.get('OS_PROJECT_NAME')
        if not proj_name:
            proj_name = config.get('OS_TENANT_NAME')

        proxy_settings = None
        if proxy_settings_str:
            tokens = re.split(':', proxy_settings_str)
            proxy_settings = ProxySettings(host=tokens[0], port=tokens[1],
                                           ssh_proxy_cmd=ssh_proxy_cmd)

        https_cacert = None
        if config.get('OS_CACERT'):
            https_cacert = config.get('OS_CACERT')
        elif config.get('OS_INSECURE'):
            https_cacert = False

        interface = 'public'
        if config.get('OS_INTERFACE'):
            interface = config.get('OS_INTERFACE')

        creds_dict = {
            'username': config['OS_USERNAME'],
            'password': config['OS_PASSWORD'],
            'auth_url': config['OS_AUTH_URL'],
            'project_name': proj_name,
            'identity_api_version': config.get('OS_IDENTITY_API_VERSION'),
            'image_api_version': config.get('OS_IMAGE_API_VERSION'),
            'network_api_version': config.get('OS_NETWORK_API_VERSION'),
            'compute_api_version': config.get('OS_COMPUTE_API_VERSION'),
            'heat_api_version': config.get('OS_HEAT_API_VERSION'),
            'user_domain_id': config.get('OS_USER_DOMAIN_ID'),
            'user_domain_name': config.get('OS_USER_DOMAIN_NAME'),
            'project_domain_id': config.get('OS_PROJECT_DOMAIN_ID'),
            'project_domain_name': config.get('OS_PROJECT_DOMAIN_NAME'),
            'volume_api_version': config.get('OS_VOLUME_API_VERSION'),
            'interface': interface,
            'proxy_settings': proxy_settings,
            'cacert': https_cacert,
            'region_name': config.get('OS_REGION_NAME')}
    else:
        logger.info('Reading development os_env file - ' + dev_os_env_file)
        config = file_utils.read_yaml(dev_os_env_file)

        proxy_settings = None
        proxy_str = config.get('http_proxy')
        if proxy_str:
            tokens = re.split(':', proxy_str)
            proxy_settings = ProxySettings(
                host=tokens[0], port=tokens[1],
                ssh_proxy_cmd=config.get('ssh_proxy_cmd'))

        creds_dict = {
            'username': config['username'],
            'password': config['password'],
            'auth_url': config['os_auth_url'],
            'project_name': config['project_name'],
            'identity_api_version': config.get('identity_api_version'),
            'image_api_version': config.get('image_api_version'),
            'network_api_version': config.get('network_api_version'),
            'compute_api_version': config.get('compute_api_version'),
            'heat_api_version': config.get('heat_api_version'),
            'user_domain_id': config.get('user_domain_id'),
            'user_domain_name': config.get('user_domain_name'),
            'project_domain_id': config.get('project_domain_id'),
            'project_domain_name': config.get('project_domain_name'),
            'volume_api_version': config.get('volume_api_version'),
            'interface': config.get('interface'),
            'proxy_settings': proxy_settings,
            'cacert': config.get('cacert'),
            'region_name': config.get('region_name')}

    if overrides and isinstance(overrides, dict):
        creds_dict.update(overrides)

    for key, value in creds_dict.items():
        if value is not None and isinstance(value, str):
            creds_dict[key] = value.replace('"', '').replace('\'', '')

    os_creds = OSCreds(**creds_dict)
    logger.info('OS Credentials = %s', os_creds.__str__)
    return os_creds


def create_image_settings(image_name, image_user, image_format, metadata,
                          disk_url=None, default_url=None,
                          kernel_settings=None, ramdisk_settings=None,
                          public=False, nic_config_pb_loc=None):
    """
    Returns the image settings object
    :param image_name: the name of the image
    :param image_user: the image's sudo user
    :param image_format: the image's format string
    :param metadata: custom metadata for overriding default behavior for test
                     image settings
    :param disk_url: the disk image's URL
    :param default_url: the default URL for the disk image
    :param kernel_settings: override to the kernel settings from the
                            image_metadata
    :param ramdisk_settings: override to the ramdisk settings from the
                             image_metadata
    :param public: True denotes image can be used by other projects where False
                   indicates the converse (default: False)
    :param nic_config_pb_loc: The location of the playbook used for configuring
                              multiple NICs
    :return:
    """

    logger.debug('Image metadata - ' + str(metadata))

    if metadata and 'config' in metadata:
        return ImageConfig(**metadata['config'])

    disk_file = None
    if metadata and ('disk_url' in metadata or 'disk_file' in metadata):
        disk_url = metadata.get('disk_url')
        disk_file = metadata.get('disk_file')
    elif not disk_url:
        disk_url = default_url

    if (metadata
            and ('kernel_file' in metadata or 'kernel_url' in metadata)
            and kernel_settings is None):
        kernel_image_settings = ImageConfig(
            name=image_name + '-kernel', image_user=image_user,
            img_format=image_format, image_file=metadata.get('kernel_file'),
            url=metadata.get('kernel_url'), public=public)
    else:
        kernel_image_settings = kernel_settings

    if (metadata
            and ('ramdisk_file' in metadata or 'ramdisk_url' in metadata)
            and ramdisk_settings is None):
        ramdisk_image_settings = ImageConfig(
            name=image_name + '-ramdisk', image_user=image_user,
            img_format=image_format,
            image_file=metadata.get('ramdisk_file'),
            url=metadata.get('ramdisk_url'), public=public)
    else:
        ramdisk_image_settings = ramdisk_settings

    extra_properties = None
    if metadata and 'extra_properties' in metadata:
        extra_properties = metadata['extra_properties']

    return ImageConfig(name=image_name, image_user=image_user,
                       img_format=image_format, image_file=disk_file,
                       url=disk_url, extra_properties=extra_properties,
                       kernel_image_settings=kernel_image_settings,
                       ramdisk_image_settings=ramdisk_image_settings,
                       public=public,
                       nic_config_pb_loc=nic_config_pb_loc)


def cirros_image_settings(name=None, url=None, image_metadata=None,
                          kernel_settings=None, ramdisk_settings=None,
                          public=False):
    """
    Returns the image settings for a Cirros QCOW2 image
    :param name: the name of the image
    :param url: the image's URL
    :param image_metadata: dict() values to override URLs for disk, kernel, and
                           ramdisk
    :param kernel_settings: override to the kernel settings from the
                            image_metadata
    :param ramdisk_settings: override to the ramdisk settings from the
                             image_metadata
    :param public: True denotes image can be used by other projects where False
                   indicates the converse
    :return:
    """
    if image_metadata and 'cirros' in image_metadata:
        metadata = image_metadata['cirros']
    else:
        metadata = image_metadata

    return create_image_settings(
        image_name=name, image_user=CIRROS_USER,
        image_format=DEFAULT_IMAGE_FORMAT, metadata=metadata, disk_url=url,
        default_url=CIRROS_DEFAULT_IMAGE_URL,
        kernel_settings=kernel_settings, ramdisk_settings=ramdisk_settings,
        public=public)


def file_image_test_settings(name, file_path, image_user=CIRROS_USER):
    return ImageConfig(name=name, image_user=image_user,
                       img_format=DEFAULT_IMAGE_FORMAT, image_file=file_path)


def centos_image_settings(name, url=None, image_metadata=None,
                          kernel_settings=None, ramdisk_settings=None,
                          public=False):
    """
    Returns the image settings for a Centos QCOW2 image
    :param name: the name of the image
    :param url: the image's URL
    :param image_metadata: dict() values to override URLs for disk, kernel, and
                           ramdisk
    :param kernel_settings: override to the kernel settings from the
                            image_metadata
    :param ramdisk_settings: override to the ramdisk settings from the
                             image_metadata
    :param public: True denotes image can be used by other projects where False
                   indicates the converse
    :return:
    """
    if image_metadata and 'centos' in image_metadata:
        metadata = image_metadata['centos']
    else:
        metadata = image_metadata

    return create_image_settings(
        image_name=name, image_user=CENTOS_USER,
        image_format=DEFAULT_IMAGE_FORMAT, metadata=metadata, disk_url=url,
        default_url=CENTOS_DEFAULT_IMAGE_URL,
        kernel_settings=kernel_settings, ramdisk_settings=ramdisk_settings,
        public=public)


def ubuntu_image_settings(name, url=None, image_metadata=None,
                          kernel_settings=None, ramdisk_settings=None,
                          public=False):
    """
    Returns the image settings for a Ubuntu QCOW2 image
    :param name: the name of the image
    :param url: the image's URL
    :param image_metadata: dict() values to override URLs for disk, kernel, and
                           ramdisk
    :param kernel_settings: override to the kernel settings from the
                            image_metadata
    :param ramdisk_settings: override to the ramdisk settings from the
                             image_metadata
    :param public: True denotes image can be used by other projects where False
                   indicates the converse
    :return:
    """
    if image_metadata and 'ubuntu' in image_metadata:
        metadata = image_metadata['ubuntu']
    else:
        metadata = image_metadata

    return create_image_settings(
        image_name=name, image_user=UBUNTU_USER,
        image_format=DEFAULT_IMAGE_FORMAT, metadata=metadata, disk_url=url,
        default_url=UBUNTU_DEFAULT_IMAGE_URL,
        kernel_settings=kernel_settings, ramdisk_settings=ramdisk_settings,
        public=public)


def get_priv_net_config(project_name, net_name, subnet_name, router_name=None,
                        cidr='10.55.0.0/24', external_net=None,
                        netconf_override=None):
    return OSNetworkConfig(
        project_name, net_name, subnet_name, cidr, router_name,
        external_gateway=external_net, netconf_override=netconf_override)


def get_pub_net_config(
        project_name, net_name, subnet_name=None, router_name=None,
        cidr='10.55.1.0/24', external_net=None, netconf_override=None):
    return OSNetworkConfig(project_name, net_name, subnet_name, cidr,
                           router_name, external_gateway=external_net,
                           netconf_override=netconf_override)


def get_flavor_config(name, ram, disk, vcpus, ephemeral=None, swap=None,
                      rxtx_factor=None, is_public=None, metadata=None):
    if metadata:
        if 'ram' in metadata:
            ram = metadata['ram']
        if 'disk' in metadata:
            disk = metadata['disk']
        if 'vcpus' in metadata:
            vcpus = metadata['vcpus']
        if 'ephemeral' in metadata:
            ephemeral = metadata['ephemeral']
        if 'swap' in metadata:
            swap = metadata['swap']
        if 'rxtx_factor' in metadata:
            rxtx_factor = metadata['rxtx_factor']
        if 'is_public' in metadata:
            is_public = metadata['is_public']
        if 'metadata' in metadata:
            metadata = metadata['metadata']

    return FlavorConfig(
        name=name, ram=ram, disk=disk, vcpus=vcpus, ephemeral=ephemeral,
        swap=swap, rxtx_factor=rxtx_factor, is_public=is_public,
        metadata=metadata)


class OSNetworkConfig:
    """
    Represents the settings required for the creation of a network in OpenStack
    where netconf_override is used to reconfigure the network_type,
    physical_network and segmentation_id
    """

    def __init__(self, project_name, net_name, subnet_name=None,
                 subnet_cidr=None, router_name=None, external_gateway=None,
                 netconf_override=None):
        """
        :param netconf_override: dict() containing the reconfigured
                                 network_type, physical_network and
                                 segmentation_id
        """
        if subnet_name and subnet_cidr:
            network_conf = NetworkConfig(
                name=net_name, subnet_settings=[
                    SubnetConfig(cidr=subnet_cidr, name=subnet_name)])
        else:
            network_conf = NetworkConfig(name=net_name)
        if netconf_override:
            network_conf.network_type = netconf_override.get('network_type')
            network_conf.physical_network = netconf_override.get(
                'physical_network')
            network_conf.segmentation_id = netconf_override.get(
                'segmentation_id')
        self.network_settings = network_conf

        if router_name:
            if subnet_name:
                self.router_settings = RouterConfig(
                    name=router_name, external_gateway=external_gateway,
                    internal_subnets=[{'subnet': {
                        'project_name': project_name,
                        'network_name': net_name,
                        'subnet_name': subnet_name}}])
            else:
                self.router_settings = RouterConfig(
                    name=router_name, external_gateway=external_gateway)
