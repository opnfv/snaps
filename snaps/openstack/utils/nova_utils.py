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

import enum
import os
import time
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from novaclient.client import Client
from novaclient.exceptions import NotFound, ClientException

from snaps import file_utils
from snaps.domain.flavor import Flavor
from snaps.domain.keypair import Keypair
from snaps.domain.project import ComputeQuotas
from snaps.domain.vm_inst import VmInst
from snaps.openstack.utils import keystone_utils, glance_utils, neutron_utils

__author__ = 'spisarski'

logger = logging.getLogger('nova_utils')

POLL_INTERVAL = 3

"""
Utilities for basic OpenStack Nova API calls
"""


def nova_client(os_creds, session=None):
    """
    Instantiates and returns a client for communications with OpenStack's Nova
    server
    :param os_creds: The connection credentials to the OpenStack API
    :param session: the keystone session object (optional)
    :return: the client object
    """
    logger.debug('Retrieving Nova Client')
    if not session:
        session = keystone_utils.keystone_session(os_creds)

    return Client(os_creds.compute_api_version,
                  session=session,
                  region_name=os_creds.region_name)


def create_server(nova, keystone, neutron, glance, instance_config,
                  image_config, project_name, keypair_config=None):
    """
    Creates a VM instance
    :param nova: the nova client (required)
    :param keystone: the keystone client for retrieving projects (required)
    :param neutron: the neutron client for retrieving ports (required)
    :param glance: the glance client (required)
    :param instance_config: the VMInstConfig object (required)
    :param image_config: the VM's ImageConfig object (required)
    :param project_name: the associated project name (required)
    :param keypair_config: the VM's KeypairConfig object (optional)
    :return: a snaps.domain.VmInst object
    """

    ports = list()

    for port_setting in instance_config.port_settings:
        port = neutron_utils.get_port(
            neutron, keystone, port_settings=port_setting,
            project_name=project_name)
        if port:
            ports.append(port)
        else:
            raise Exception('Cannot find port named - ' + port_setting.name)
    nics = []
    for port in ports:
        kv = dict()
        kv['port-id'] = port.id
        nics.append(kv)

    logger.info('Creating VM with name - ' + instance_config.name)
    keypair_name = None
    if keypair_config:
        keypair_name = keypair_config.name

    flavor = get_flavor_by_name(nova, instance_config.flavor)
    if not flavor:
        raise NovaException(
            'Flavor not found with name - %s', instance_config.flavor)

    image = glance_utils.get_image(glance, image_settings=image_config)
    if image:
        userdata = None
        if instance_config.userdata:
            if isinstance(instance_config.userdata, str):
                userdata = instance_config.userdata + '\n'
            elif (isinstance(instance_config.userdata, dict) and
                  'script_file' in instance_config.userdata):
                try:
                    userdata = file_utils.read_file(
                        instance_config.userdata['script_file'])
                except Exception as e:
                    logger.warn('error reading userdata file %s - %s',
                                instance_config.userdata, e)
        args = {'name': instance_config.name,
                'flavor': flavor,
                'image': image,
                'nics': nics,
                'key_name': keypair_name,
                'security_groups':
                    instance_config.security_group_names,
                'userdata': userdata}

        if instance_config.availability_zone:
            args['availability_zone'] = instance_config.availability_zone

        server = nova.servers.create(**args)

        return __map_os_server_obj_to_vm_inst(
            neutron, keystone, server, project_name)
    else:
        raise NovaException(
            'Cannot create instance, image cannot be located with name %s',
            image_config.name)


def get_server(nova, neutron, keystone, vm_inst_settings=None,
               server_name=None, project_id=None):
    """
    Returns a VmInst object for the first server instance found.
    :param nova: the Nova client
    :param neutron: the Neutron client
    :param keystone: the Keystone client
    :param vm_inst_settings: the VmInstanceConfig object from which to build
                             the query if not None
    :param server_name: the server with this name to return if vm_inst_settings
                        is not None
    :param project_id: the assocaited project ID
    :return: a snaps.domain.VmInst object or None if not found
    """
    search_opts = dict()
    if vm_inst_settings:
        search_opts['name'] = vm_inst_settings.name
    elif server_name:
        search_opts['name'] = server_name

    servers = nova.servers.list(search_opts=search_opts)
    for server in servers:
        return __map_os_server_obj_to_vm_inst(
            neutron, keystone, server, project_id)


def get_server_connection(nova, vm_inst_settings=None, server_name=None):
    """
    Returns a VmInst object for the first server instance found.
    :param nova: the Nova client
    :param vm_inst_settings: the VmInstanceConfig object from which to build
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
        return server.links[0]


def __map_os_server_obj_to_vm_inst(neutron, keystone, os_server,
                                   project_name=None):
    """
    Returns a VmInst object for an OpenStack Server object
    :param neutron: the Neutron client
    :param keystone: the Keystone client
    :param os_server: the OpenStack server object
    :param project_name: the associated project name
    :return: an equivalent SNAPS-OO VmInst domain object
    """
    sec_grp_names = list()
    # VM must be active for 'security_groups' attr to be initialized
    if hasattr(os_server, 'security_groups'):
        for sec_group in os_server.security_groups:
            if sec_group.get('name'):
                sec_grp_names.append(sec_group.get('name'))

    out_ports = list()
    if len(os_server.networks) > 0:
        for net_name, ips in os_server.networks.items():
            network = neutron_utils.get_network(
                neutron, keystone, network_name=net_name,
                project_name=project_name)
            ports = neutron_utils.get_ports(neutron, network, ips)
            for port in ports:
                out_ports.append(port)

    volumes = None
    if hasattr(os_server, 'os-extended-volumes:volumes_attached'):
        volumes = getattr(os_server, 'os-extended-volumes:volumes_attached')

    return VmInst(
        name=os_server.name, inst_id=os_server.id,
        image_id=os_server.image['id'], flavor_id=os_server.flavor['id'],
        ports=out_ports, keypair_name=os_server.key_name,
        sec_grp_names=sec_grp_names, volume_ids=volumes,
        compute_host=os_server._info.get('OS-EXT-SRV-ATTR:host'),
        availability_zone=os_server._info.get('OS-EXT-AZ:availability_zone'))


def __get_latest_server_os_object(nova, server):
    """
    Returns a server with a given id
    :param nova: the Nova client
    :param server: the domain VmInst object
    :return: the list of servers or None if not found
    """
    return __get_latest_server_os_object_by_id(nova, server.id)


def __get_latest_server_os_object_by_id(nova, server_id):
    """
    Returns a server with a given id
    :param nova: the Nova client
    :param server_id: the server's ID
    :return: the list of servers or None if not found
    """
    return nova.servers.get(server_id)


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


def get_latest_server_object(nova, neutron, keystone, server, project_name):
    """
    Returns a server with a given id
    :param nova: the Nova client
    :param neutron: the Neutron client
    :param keystone: the Keystone client
    :param server: the old server object
    :param project_name: the associated project name
    :return: the list of servers or None if not found
    """
    server = __get_latest_server_os_object(nova, server)
    return __map_os_server_obj_to_vm_inst(
        neutron, keystone, server, project_name)


def get_server_object_by_id(nova, neutron, keystone, server_id,
                            project_name=None):
    """
    Returns a server with a given id
    :param nova: the Nova client
    :param neutron: the Neutron client
    :param keystone: the Keystone client
    :param server_id: the server's id
    :param project_name: the associated project name
    :return: an SNAPS-OO VmInst object or None if not found
    """
    server = __get_latest_server_os_object_by_id(nova, server_id)
    return __map_os_server_obj_to_vm_inst(
        neutron, keystone, server, project_name)


def get_server_security_group_names(nova, server):
    """
    Returns a server with a given id
    :param nova: the Nova client
    :param server: the old server object
    :return: the list of security groups associated with a VM
    """
    out = list()
    os_vm_inst = __get_latest_server_os_object(nova, server)
    if hasattr(os_vm_inst, 'security_groups'):
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


def reboot_server(nova, server, reboot_type=None):
    """
    Returns a dictionary of a VMs info as returned by OpenStack
    :param nova: the Nova client
    :param server: the old server object
    :param reboot_type: Acceptable values 'SOFT', 'HARD'
                        (api uses SOFT as the default)
    :return: a dict of the info if VM exists else None
    """
    vm = __get_latest_server_os_object(nova, server)
    if vm:
        vm.reboot(reboot_type=reboot_type.value)
    else:
        raise ServerNotFoundError('Cannot locate server')


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

            os.chmod(pub_expand_file, 0o600)
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

            os.chmod(priv_expand_file, 0o600)
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
    return Keypair(name=os_kp.name, kp_id=os_kp.id,
                   public_key=os_kp.public_key, fingerprint=os_kp.fingerprint)


def keypair_exists(nova, keypair_obj):
    """
    Returns a copy of the keypair object if found
    :param nova: the Nova client
    :param keypair_obj: the keypair object
    :return: the keypair object or None if not found
    """
    try:
        os_kp = nova.keypairs.get(keypair_obj)
        return Keypair(name=os_kp.name, kp_id=os_kp.id,
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
            return Keypair(name=keypair.name, kp_id=keypair.id,
                           public_key=keypair.public_key)

    return None


def get_keypair_by_id(nova, kp_id):
    """
    Returns a list of all available keypairs
    :param nova: the Nova client
    :param kp_id: the ID of the keypair to return
    :return: the keypair object
    """
    keypair = nova.keypairs.get(kp_id)
    return Keypair(name=keypair.name, kp_id=keypair.id,
                   public_key=keypair.public_key)


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


def get_hypervisor_hosts(nova):
    """
    Returns the host names of all nova nodes with active hypervisors
    :param nova: the Nova client
    :return: a list of hypervisor host names
    """
    out = list()
    hypervisors = nova.hypervisors.list()
    for hypervisor in hypervisors:
        if hypervisor.state == "up":
            out.append(hypervisor.hypervisor_hostname)

    return out


def delete_vm_instance(nova, vm_inst):
    """
    Deletes a VM instance
    :param nova: the nova client
    :param vm_inst: the snaps.domain.VmInst object
    """
    nova.servers.delete(vm_inst.id)


def __get_os_flavor(nova, flavor_id):
    """
    Returns to OpenStack flavor object by name
    :param nova: the Nova client
    :param flavor_id: the flavor's ID value
    :return: the OpenStack Flavor object
    """
    try:
        return nova.flavors.get(flavor_id)
    except NotFound:
        return None


def get_flavor(nova, flavor):
    """
    Returns to OpenStack flavor object by name
    :param nova: the Nova client
    :param flavor: the SNAPS flavor domain object
    :return: the SNAPS Flavor domain object
    """
    os_flavor = __get_os_flavor(nova, flavor.id)
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


def get_flavor_by_id(nova, flavor_id):
    """
    Returns to OpenStack flavor object by name
    :param nova: the Nova client
    :param flavor_id: the flavor ID value
    :return: the SNAPS Flavor domain object
    """
    os_flavor = __get_os_flavor(nova, flavor_id)
    if os_flavor:
        return Flavor(
            name=os_flavor.name, id=os_flavor.id, ram=os_flavor.ram,
            disk=os_flavor.disk, vcpus=os_flavor.vcpus,
            ephemeral=os_flavor.ephemeral, swap=os_flavor.swap,
            rxtx_factor=os_flavor.rxtx_factor, is_public=os_flavor.is_public)


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
    os_flavor = __get_os_flavor(nova, flavor.id)
    if os_flavor:
        os_flavor.set_keys(metadata)


def get_flavor_keys(nova, flavor):
    """
    Sets metadata on the flavor
    :param nova: the Nova client
    :param flavor: the SNAPS flavor domain object
    """
    os_flavor = __get_os_flavor(nova, flavor.id)
    if os_flavor:
        return os_flavor.get_keys()


def add_security_group(nova, vm, security_group_name):
    """
    Adds a security group to an existing VM
    :param nova: the nova client
    :param vm: the OpenStack server object (VM) to alter
    :param security_group_name: the name of the security group to add
    """
    try:
        nova.servers.add_security_group(str(vm.id), security_group_name)
    except ClientException as e:
        sec_grp_names = get_server_security_group_names(nova, vm)
        if security_group_name in sec_grp_names:
            logger.warn('Security group [%s] already added to VM [%s]',
                        security_group_name, vm.name)
            return

        logger.error('Unexpected error while adding security group [%s] - %s',
                     security_group_name, e)
        raise


def remove_security_group(nova, vm, security_group):
    """
    Removes a security group from an existing VM
    :param nova: the nova client
    :param vm: the OpenStack server object (VM) to alter
    :param security_group: the SNAPS SecurityGroup domain object to add
    """
    nova.servers.remove_security_group(str(vm.id), security_group.name)


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
    update_values['injected_file_content_bytes'] = (
        compute_quotas.injected_file_content_bytes)
    update_values['ram'] = compute_quotas.ram
    update_values['fixed_ips'] = compute_quotas.fixed_ips
    update_values['key_pairs'] = compute_quotas.key_pairs

    return nova.quotas.update(project_id, **update_values)


def attach_volume(nova, neutron, keystone, server, volume, project_name,
                  timeout=120):
    """
    Attaches a volume to a server. When the timeout parameter is used, a VmInst
    object with the proper volume updates is returned unless it has not been
    updated in the allotted amount of time then an Exception will be raised.
    :param nova: the nova client
    :param neutron: the neutron client
    :param keystone: the neutron client
    :param server: the VMInst domain object
    :param volume: the Volume domain object
    :param project_name: the associated project name
    :param timeout: denotes the amount of time to block to determine if the
                    has been properly attached.
    :return: updated VmInst object
    """
    nova.volumes.create_server_volume(server.id, volume.id)

    start_time = time.time()
    while time.time() < start_time + timeout:
        vm = get_server_object_by_id(
            nova, neutron, keystone, server.id, project_name)
        for vol_dict in vm.volume_ids:
            if volume.id == vol_dict['id']:
                return vm
        time.sleep(POLL_INTERVAL)

    raise NovaException(
        'Attach failed on volume - {} and server - {}'.format(
            volume.id, server.id))


def detach_volume(nova, neutron, keystone, server, volume, project_name,
                  timeout=120):
    """
    Detaches a volume to a server. When the timeout parameter is used, a VmInst
    object with the proper volume updates is returned unless it has not been
    updated in the allotted amount of time then an Exception will be raised.
    :param nova: the nova client
    :param neutron: the neutron client
    :param keystone: the keystone client
    :param server: the VMInst domain object
    :param volume: the Volume domain object
    :param project_name: the associated project name
    :param timeout: denotes the amount of time to block to determine if the
                    has been properly detached.
    :return: updated VmInst object
    """
    nova.volumes.delete_server_volume(server.id, volume.id)

    start_time = time.time()
    while time.time() < start_time + timeout:
        vm = get_server_object_by_id(
            nova, neutron, keystone, server.id, project_name)
        if len(vm.volume_ids) == 0:
            return vm
        else:
            ids = list()
            for vol_dict in vm.volume_ids:
                ids.append(vol_dict['id'])
            if volume.id not in ids:
                return vm
        time.sleep(POLL_INTERVAL)

    raise NovaException(
        'Detach failed on volume - {} server - {}'.format(
            volume.id, server.id))


class RebootType(enum.Enum):
    """
    A rule's direction
    """
    soft = 'SOFT'
    hard = 'HARD'


class NovaException(Exception):
    """
    Exception when calls to the Keystone client cannot be served properly
    """


class ServerNotFoundError(Exception):
    """
    Exception when operations to a VM/Server is requested and the OpenStack
    Server instance cannot be located
    """
