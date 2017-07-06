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

import os
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from novaclient.client import Client
from novaclient.exceptions import NotFound

from snaps.domain.keypair import Keypair
from snaps.domain.vm_inst import VmInst
from snaps.openstack.utils import keystone_utils, glance_utils, neutron_utils

__author__ = 'spisarski'

logger = logging.getLogger('nova_utils')

"""
Utilities for basic OpenStack Nova API calls
"""


def nova_client(os_creds):
    """
    Instantiates and returns a client for communications with OpenStack's Nova
    server
    :param os_creds: The connection credentials to the OpenStack API
    :return: the client object
    """
    logger.debug('Retrieving Nova Client')
    return Client(os_creds.compute_api_version,
                  session=keystone_utils.keystone_session(os_creds))


def create_server(nova, neutron, glance, instance_settings, image_settings,
                  keypair_settings=None):
    """
    Creates a VM instance
    :param nova: the nova client (required)
    :param neutron: the neutron client for retrieving ports (required)
    :param glance: the glance client (required)
    :param instance_settings: the VM instance settings object (required)
    :param image_settings: the VM's image settings object (required)
    :param keypair_settings: the VM's keypair settings object (optional)
    :return: a snaps.domain.VmInst object
    """

    ports = list()

    for port_setting in instance_settings.port_settings:
        ports.append(neutron_utils.get_port_by_name(
            neutron, port_setting.name))
    nics = []
    for port in ports:
        kv = dict()
        kv['port-id'] = port['port']['id']
        nics.append(kv)

    logger.info('Creating VM with name - ' + instance_settings.name)
    keypair_name = None
    if keypair_settings:
        keypair_name = keypair_settings.name

    flavor = get_flavor_by_name(nova, instance_settings.flavor)
    if not flavor:
        raise Exception(
            'Flavor not found with name - %s',
            instance_settings.flavor)

    image = glance_utils.get_image(glance, image_settings.name)
    if image:
        args = {'name': instance_settings.name,
                'flavor': flavor,
                'image': image,
                'nics': nics,
                'key_name': keypair_name,
                'security_groups':
                    instance_settings.security_group_names,
                'userdata': instance_settings.userdata,
                'availability_zone':
                    instance_settings.availability_zone}
        server = nova.servers.create(**args)
        return VmInst(name=server.name, inst_id=server.id,
                      networks=server.networks)
    else:
        raise Exception(
            'Cannot create instance, image cannot be located with name %s',
            image_settings.name)


def get_servers_by_name(nova, name):
    """
    Returns a list of servers with a given name
    :param nova: the Nova client
    :param name: the server name
    :return: the list of servers
    """
    out = list()
    servers = nova.servers.list(search_opts={'name': name})
    for server in servers:
        out.append(VmInst(name=server.name, inst_id=server.id,
                          networks=server.networks))
    return out


def get_latest_server_os_object(nova, server):
    """
    Returns a server with a given id
    :param nova: the Nova client
    :param server: the domain VmInst object
    :return: the list of servers or None if not found
    """
    return nova.servers.get(server.id)


def get_latest_server_object(nova, server):
    """
    Returns a server with a given id
    :param nova: the Nova client
    :param server: the old server object
    :return: the list of servers or None if not found
    """
    server = get_latest_server_os_object(nova, server)
    return VmInst(name=server.name, inst_id=server.id,
                  networks=server.networks)


def create_keys(key_size=2048):
    """
    Generates public and private keys
    :param key_size: the number of bytes for the key size
    :return: the cryptography keys
    """
    return rsa.generate_private_key(backend=default_backend(),
                                    public_exponent=65537,
                                    key_size=key_size)


def public_key_openssh(keys):
    """
    Returns the public key for OpenSSH
    :param keys: the keys generated by create_keys() from cryptography
    :return: the OpenSSH public key
    """
    return keys.public_key().public_bytes(serialization.Encoding.OpenSSH,
                                          serialization.PublicFormat.OpenSSH)


def save_keys_to_files(keys=None, pub_file_path=None, priv_file_path=None):
    """
    Saves the generated RSA generated keys to the filesystem
    :param keys: the keys to save generated by cryptography
    :param pub_file_path: the path to the public keys
    :param priv_file_path: the path to the private keys
    :return: None
    """
    if keys:
        if pub_file_path:
            # To support '~'
            pub_expand_file = os.path.expanduser(pub_file_path)
            pub_dir = os.path.dirname(pub_expand_file)

            if not os.path.isdir(pub_dir):
                os.mkdir(pub_dir)
            public_handle = open(pub_expand_file, 'wb')
            public_bytes = keys.public_key().public_bytes(
                serialization.Encoding.OpenSSH,
                serialization.PublicFormat.OpenSSH)
            public_handle.write(public_bytes)
            public_handle.close()
            os.chmod(pub_expand_file, 0o400)
            logger.info("Saved public key to - " + pub_expand_file)
        if priv_file_path:
            # To support '~'
            priv_expand_file = os.path.expanduser(priv_file_path)
            priv_dir = os.path.dirname(priv_expand_file)
            if not os.path.isdir(priv_dir):
                os.mkdir(priv_dir)
            private_handle = open(priv_expand_file, 'wb')
            private_handle.write(
                keys.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption()))
            private_handle.close()
            os.chmod(priv_expand_file, 0o400)
            logger.info("Saved private key to - " + priv_expand_file)


def upload_keypair_file(nova, name, file_path):
    """
    Uploads a public key from a file
    :param nova: the Nova client
    :param name: the keypair name
    :param file_path: the path to the public key file
    :return: the keypair object
    """
    with open(os.path.expanduser(file_path), 'rb') as fpubkey:
        logger.info('Saving keypair to - ' + file_path)
        return upload_keypair(nova, name, fpubkey.read())


def upload_keypair(nova, name, key):
    """
    Uploads a public key from a file
    :param nova: the Nova client
    :param name: the keypair name
    :param key: the public key object
    :return: the keypair object
    """
    logger.info('Creating keypair with name - ' + name)
    os_kp = nova.keypairs.create(name=name, public_key=key.decode('utf-8'))
    return Keypair(name=os_kp.name, id=os_kp.id, public_key=os_kp.public_key)


def keypair_exists(nova, keypair_obj):
    """
    Returns a copy of the keypair object if found
    :param nova: the Nova client
    :param keypair_obj: the keypair object
    :return: the keypair object or None if not found
    """
    try:
        os_kp = nova.keypairs.get(keypair_obj)
        return Keypair(name=os_kp.name, id=os_kp.id, public_key=os_kp.public_key)
    except:
        return None


def get_keypair_by_name(nova, name):
    """
    Returns a list of all available keypairs
    :param nova: the Nova client
    :param name: the name of the keypair to lookup
    :return: the keypair object or None if not found
    """
    keypairs = nova.keypairs.list()

    for keypair in keypairs:
        if keypair.name == name:
            return Keypair(name=keypair.name, id=keypair.id,
                           public_key=keypair.public_key)

    return None


def delete_keypair(nova, key):
    """
    Deletes a keypair object from OpenStack
    :param nova: the Nova client
    :param key: the SNAPS-OO keypair domain object to delete
    """
    logger.debug('Deleting keypair - ' + key.name)
    nova.keypairs.delete(key.id)


def get_nova_availability_zones(nova):
    """
    Returns the names of all nova active compute servers
    :param nova: the Nova client
    :return: a list of compute server names
    """
    out = list()
    zones = nova.availability_zones.list()
    for zone in zones:
        if zone.zoneName == 'nova':
            for key, host in zone.hosts.items():
                if host['nova-compute']['available']:
                    out.append(zone.zoneName + ':' + key)

    return out


def delete_vm_instance(nova, vm_inst):
    """
    Deletes a VM instance
    :param nova: the nova client
    :param vm_inst: the snaps.domain.VmInst object
    """
    nova.servers.delete(vm_inst.id)


def get_flavor_by_name(nova, name):
    """
    Returns a flavor by name
    :param nova: the Nova client
    :param name: the flavor name to return
    :return: the OpenStack flavor object or None if not exists
    """
    try:
        return nova.flavors.find(name=name)
    except NotFound:
        return None


def create_flavor(nova, flavor_settings):
    """
    Creates and returns and OpenStack flavor object
    :param nova: the Nova client
    :param flavor_settings: the flavor settings
    :return: the Flavor
    """
    return nova.flavors.create(name=flavor_settings.name,
                               flavorid=flavor_settings.flavor_id,
                               ram=flavor_settings.ram,
                               vcpus=flavor_settings.vcpus,
                               disk=flavor_settings.disk,
                               ephemeral=flavor_settings.ephemeral,
                               swap=flavor_settings.swap,
                               rxtx_factor=flavor_settings.rxtx_factor,
                               is_public=flavor_settings.is_public)


def delete_flavor(nova, flavor):
    """
    Deletes a flavor
    :param nova: the Nova client
    :param flavor: the OpenStack flavor object
    """
    nova.flavors.delete(flavor)


def add_security_group(nova, vm, security_group_name):
    """
    Adds a security group to an existing VM
    :param nova: the nova client
    :param vm: the OpenStack server object (VM) to alter
    :param security_group_name: the name of the security group to add
    """
    nova.servers.add_security_group(str(vm.id), security_group_name)


def remove_security_group(nova, vm, security_group):
    """
    Removes a security group from an existing VM
    :param nova: the nova client
    :param vm: the OpenStack server object (VM) to alter
    :param security_group: the OpenStack security group object to add
    """
    nova.servers.remove_security_group(
        str(vm.id), security_group['security_group']['name'])


def add_floating_ip_to_server(nova, vm, floating_ip, ip_addr):
    """
    Adds a floating IP to a server instance
    :param nova: the nova client
    :param vm: VmInst domain object
    :param floating_ip: FloatingIp domain object
    :param ip_addr: the IP to which to bind the floating IP to
    """
    vm = get_latest_server_os_object(nova, vm)
    vm.add_floating_ip(floating_ip.ip, ip_addr)
