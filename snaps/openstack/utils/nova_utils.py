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

from snaps.domain.flavor import Flavor
from snaps.domain.keypair import Keypair
from snaps.domain.project import ComputeQuotas
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
                  session=keystone_utils.keystone_session(os_creds),
                  region_name=os_creds.region_name)


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
        ports.append(neutron_utils.get_port(
            neutron, port_settings=port_setting))
    nics = []
    for port in ports:
        kv = dict()
        kv['port-id'] = port.id
        nics.append(kv)

    logger.info('Creating VM with name - ' + instance_settings.name)
    keypair_name = None
    if keypair_settings:
        keypair_name = keypair_settings.name

    flavor = get_flavor_by_name(nova, instance_settings.flavor)
    if not flavor:
        raise NovaException(
            'Flavor not found with name - %s', instance_settings.flavor)

    image = glance_utils.get_image(glance, image_settings=image_settings)
    if image:
        args = {'name': instance_settings.name,
                'flavor': flavor,
                'image': image,
                'nics': nics,
                'key_name': keypair_name,
                'security_groups':
                    instance_settings.security_group_names,
                'userdata': instance_settings.userdata}

        if instance_settings.availability_zone:
            args['availability_zone'] = instance_settings.availability_zone

        server = nova.servers.create(**args)
        return VmInst(name=server.name, inst_id=server.id,
                      networks=server.networks)
    else:
        raise NovaException(
            'Cannot create instance, image cannot be located with name %s',
            image_settings.name)


def get_server(nova, vm_inst_settings=None, server_name=None):
    """
    Returns a VmInst object for the first server instance found.
    :param nova: the Nova client
    :param vm_inst_settings: the VmInstanceSettings object from which to build
                             the query if not None
    :param server_name: the server with this name to return if vm_inst_settings
                        is not None
    :return: a snaps.domain.VmInst object or None if not found
    """
    search_opts = dict()
    if vm_inst_settings:
        search_opts['name'] = vm_inst_settings.name
    elif server_name:
        search_opts['name'] = server_name

    servers = nova.servers.list(search_opts=search_opts)
    for server in servers:
        return VmInst(name=server.name, inst_id=server.id,
                      networks=server.networks)


def __get_latest_server_os_object(nova, server):
    """
    Returns a server with a given id
    :param nova: the Nova client
    :param server: the domain VmInst object
    :return: the list of servers or None if not found
    """
    return nova.servers.get(server.id)


def get_server_status(nova, server):
    """
    Returns the a VM instance's status from OpenStack
    :param nova: the Nova client
    :param server: the domain VmInst object
    :return: the VM's string status or None if not founc
    """
    server = __get_latest_server_os_object(nova, server)
    if server:
        return server.status
    return None


def get_server_console_output(nova, server):
    """
    Returns the console object for parsing VM activity
    :param nova: the Nova client
    :param server: the domain VmInst object
    :return: the console output object or None if server object is not found
    """
    server = __get_latest_server_os_object(nova, server)
    if server:
        return server.get_console_output()
    return None


def get_latest_server_object(nova, server):
    """
    Returns a server with a given id
    :param nova: the Nova client
    :param server: the old server object
    :return: the list of servers or None if not found
    """
    server = __get_latest_server_os_object(nova, server)
    return VmInst(name=server.name, inst_id=server.id,
                  networks=server.networks)


def get_server_security_group_names(nova, server):
    """
    Returns a server with a given id
    :param nova: the Nova client
    :param server: the old server object
    :return: the list of security groups associated with a VM
    """
    out = list()
    os_vm_inst = __get_latest_server_os_object(nova, server)
    for sec_grp_dict in os_vm_inst.security_groups:
        out.append(sec_grp_dict['name'])
    return out


def get_server_info(nova, server):
    """
    Returns a dictionary of a VMs info as returned by OpenStack
    :param nova: the Nova client
    :param server: the old server object
    :return: a dict of the info if VM exists else None
    """
    vm = __get_latest_server_os_object(nova, server)
    if vm:
        return vm._info
    return None


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
    """
    if keys:
        if pub_file_path:
            # To support '~'
            pub_expand_file = os.path.expanduser(pub_file_path)
            pub_dir = os.path.dirname(pub_expand_file)

            if not os.path.isdir(pub_dir):
                os.mkdir(pub_dir)

            public_handle = None
            try:
                public_handle = open(pub_expand_file, 'wb')
                public_bytes = keys.public_key().public_bytes(
                    serialization.Encoding.OpenSSH,
                    serialization.PublicFormat.OpenSSH)
                public_handle.write(public_bytes)
            finally:
                if public_handle:
                    public_handle.close()

            os.chmod(pub_expand_file, 0o400)
            logger.info("Saved public key to - " + pub_expand_file)
        if priv_file_path:
            # To support '~'
            priv_expand_file = os.path.expanduser(priv_file_path)
            priv_dir = os.path.dirname(priv_expand_file)
            if not os.path.isdir(priv_dir):
                os.mkdir(priv_dir)

            private_handle = None
            try:
                private_handle = open(priv_expand_file, 'wb')
                private_handle.write(
                    keys.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.TraditionalOpenSSL,
                        encryption_algorithm=serialization.NoEncryption()))
            finally:
                if private_handle:
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
    fpubkey = None
    try:
        with open(os.path.expanduser(file_path), 'rb') as fpubkey:
            logger.info('Saving keypair to - ' + file_path)
            return upload_keypair(nova, name, fpubkey.read())
    finally:
        if fpubkey:
            fpubkey.close()


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
        return Keypair(name=os_kp.name, id=os_kp.id,
                       public_key=os_kp.public_key)
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


def get_availability_zone_hosts(nova, zone_name='nova'):
    """
    Returns the names of all nova active compute servers
    :param nova: the Nova client
    :param zone_name: the Nova client
    :return: a list of compute server names
    """
    out = list()
    zones = nova.availability_zones.list()
    for zone in zones:
        if zone.zoneName == zone_name and zone.hosts:
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


def __get_os_flavor(nova, flavor):
    """
    Returns to OpenStack flavor object by name
    :param nova: the Nova client
    :param flavor: the SNAPS flavor domain object
    :return: the OpenStack Flavor object
    """
    try:
        return nova.flavors.get(flavor.id)
    except NotFound:
        return None


def get_flavor(nova, flavor):
    """
    Returns to OpenStack flavor object by name
    :param nova: the Nova client
    :param flavor: the SNAPS flavor domain object
    :return: the SNAPS Flavor domain object
    """
    os_flavor = __get_os_flavor(nova, flavor)
    if os_flavor:
        return Flavor(
            name=os_flavor.name, id=os_flavor.id, ram=os_flavor.ram,
            disk=os_flavor.disk, vcpus=os_flavor.vcpus,
            ephemeral=os_flavor.ephemeral, swap=os_flavor.swap,
            rxtx_factor=os_flavor.rxtx_factor, is_public=os_flavor.is_public)
    try:
        return nova.flavors.get(flavor.id)
    except NotFound:
        return None


def __get_os_flavor_by_name(nova, name):
    """
    Returns to OpenStack flavor object by name
    :param nova: the Nova client
    :param name: the name of the flavor to query
    :return: OpenStack flavor object
    """
    try:
        return nova.flavors.find(name=name)
    except NotFound:
        return None


def get_flavor_by_name(nova, name):
    """
    Returns a flavor by name
    :param nova: the Nova client
    :param name: the flavor name to return
    :return: the SNAPS flavor domain object or None if not exists
    """
    os_flavor = __get_os_flavor_by_name(nova, name)
    if os_flavor:
        return Flavor(
            name=os_flavor.name, id=os_flavor.id, ram=os_flavor.ram,
            disk=os_flavor.disk, vcpus=os_flavor.vcpus,
            ephemeral=os_flavor.ephemeral, swap=os_flavor.swap,
            rxtx_factor=os_flavor.rxtx_factor, is_public=os_flavor.is_public)


def create_flavor(nova, flavor_settings):
    """
    Creates and returns and OpenStack flavor object
    :param nova: the Nova client
    :param flavor_settings: the flavor settings
    :return: the SNAPS flavor domain object
    """
    os_flavor = nova.flavors.create(
        name=flavor_settings.name, flavorid=flavor_settings.flavor_id,
        ram=flavor_settings.ram, vcpus=flavor_settings.vcpus,
        disk=flavor_settings.disk, ephemeral=flavor_settings.ephemeral,
        swap=flavor_settings.swap, rxtx_factor=flavor_settings.rxtx_factor,
        is_public=flavor_settings.is_public)
    return Flavor(
        name=os_flavor.name, id=os_flavor.id, ram=os_flavor.ram,
        disk=os_flavor.disk, vcpus=os_flavor.vcpus,
        ephemeral=os_flavor.ephemeral, swap=os_flavor.swap,
        rxtx_factor=os_flavor.rxtx_factor, is_public=os_flavor.is_public)


def delete_flavor(nova, flavor):
    """
    Deletes a flavor
    :param nova: the Nova client
    :param flavor: the SNAPS flavor domain object
    """
    nova.flavors.delete(flavor.id)


def set_flavor_keys(nova, flavor, metadata):
    """
    Sets metadata on the flavor
    :param nova: the Nova client
    :param flavor: the SNAPS flavor domain object
    :param metadata: the metadata to set
    """
    os_flavor = __get_os_flavor(nova, flavor)
    if os_flavor:
        os_flavor.set_keys(metadata)


def get_flavor_keys(nova, flavor):
    """
    Sets metadata on the flavor
    :param nova: the Nova client
    :param flavor: the SNAPS flavor domain object
    """
    os_flavor = __get_os_flavor(nova, flavor)
    if os_flavor:
        return os_flavor.get_keys()


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
    :param security_group: the SNAPS SecurityGroup domain object to add
    """
    nova.servers.remove_security_group(str(vm.id), security_group.name)


def add_floating_ip_to_server(nova, vm, floating_ip, ip_addr):
    """
    Adds a floating IP to a server instance
    :param nova: the nova client
    :param vm: VmInst domain object
    :param floating_ip: FloatingIp domain object
    :param ip_addr: the IP to which to bind the floating IP to
    """
    vm = __get_latest_server_os_object(nova, vm)
    vm.add_floating_ip(floating_ip.ip, ip_addr)


def get_compute_quotas(nova, project_id):
    """
    Returns a list of all available keypairs
    :param nova: the Nova client
    :param project_id: the project's ID of the quotas to lookup
    :return: an object of type ComputeQuotas or None if not found
    """
    quotas = nova.quotas.get(tenant_id=project_id)
    if quotas:
        return ComputeQuotas(quotas)


def update_quotas(nova, project_id, compute_quotas):
    """
    Updates the compute quotas for a given project
    :param nova: the Nova client
    :param project_id: the project's ID that requires quota updates
    :param compute_quotas: an object of type ComputeQuotas containing the
                           values to update
    :return:
    """
    update_values = dict()
    update_values['metadata_items'] = compute_quotas.metadata_items
    update_values['cores'] = compute_quotas.cores
    update_values['instances'] = compute_quotas.instances
    update_values['injected_files'] = compute_quotas.injected_files
    update_values['injected_file_content_bytes'] = compute_quotas.injected_file_content_bytes
    update_values['ram'] = compute_quotas.ram
    update_values['fixed_ips'] = compute_quotas.fixed_ips
    update_values['key_pairs'] = compute_quotas.key_pairs

    return nova.quotas.update(project_id, **update_values)


class NovaException(Exception):
    """
    Exception when calls to the Keystone client cannot be served properly
    """
