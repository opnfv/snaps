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
import uuid

from snaps import file_utils
from snaps.config.flavor import FlavorConfig
from snaps.config.keypair import KeypairConfig
from snaps.config.network import SubnetConfig, PortConfig, NetworkConfig
from snaps.config.router import RouterConfig
from snaps.config.security_group import (
    SecurityGroupRuleConfig, SecurityGroupConfig)
from snaps.config.vm_inst import VmInstanceConfig, FloatingIpConfig
from snaps.config.volume import VolumeConfig
from snaps.config.volume_type import (
    ControlLocation,  VolumeTypeEncryptionConfig, VolumeTypeConfig)
from snaps.openstack.utils import (
    neutron_utils, nova_utils, heat_utils, glance_utils)


def create_network_config(neutron, network):
    """
    Returns a NetworkConfig object
    :param neutron: the neutron client
    :param network: a SNAPS-OO Network domain object
    :return:
    """
    return NetworkConfig(
        name=network.name, network_type=network.type,
        subnet_settings=create_subnet_config(neutron, network))


def create_security_group_config(neutron, security_group):
    """
    Returns a SecurityGroupConfig object
    :param neutron: the neutron client
    :param security_group: a SNAPS-OO SecurityGroup domain object
    :return:
    """
    rules = neutron_utils.get_rules_by_security_group(neutron, security_group)

    rule_settings = list()
    for rule in rules:
        rule_settings.append(SecurityGroupRuleConfig(
            sec_grp_name=security_group.name, description=rule.description,
            direction=rule.direction, ethertype=rule.ethertype,
            port_range_min=rule.port_range_min,
            port_range_max=rule.port_range_max, protocol=rule.protocol,
            remote_group_id=rule.remote_group_id,
            remote_ip_prefix=rule.remote_ip_prefix))

    return SecurityGroupConfig(
        name=security_group.name, description=security_group.description,
        rule_settings=rule_settings)


def create_subnet_config(neutron, network):
    """
    Returns a list of SubnetConfig objects for a given network
    :param neutron: the OpenStack neutron client
    :param network: the SNAPS-OO Network domain object
    :return: a list
    """
    out = list()

    subnets = neutron_utils.get_subnets_by_network(neutron, network)
    for subnet in subnets:
        kwargs = dict()
        kwargs['cidr'] = subnet.cidr
        kwargs['ip_version'] = subnet.ip_version
        kwargs['name'] = subnet.name
        kwargs['start'] = subnet.start
        kwargs['end'] = subnet.end
        kwargs['gateway_ip'] = subnet.gateway_ip
        kwargs['enable_dhcp'] = subnet.enable_dhcp
        kwargs['dns_nameservers'] = subnet.dns_nameservers
        kwargs['host_routes'] = subnet.host_routes
        kwargs['ipv6_ra_mode'] = subnet.ipv6_ra_mode
        kwargs['ipv6_address_mode'] = subnet.ipv6_address_mode
        out.append(SubnetConfig(**kwargs))
    return out


def create_router_config(neutron, router):
    """
    Returns a RouterConfig object
    :param neutron: the neutron client
    :param router: a SNAPS-OO Router domain object
    :return:
    """
    ext_net_name = None

    if router.external_network_id:
        network = neutron_utils.get_network_by_id(
            neutron, router.external_network_id)
        if network:
            ext_net_name = network.name

    out_ports = list()
    if router.port_subnets:
        for port, subnets in router.port_subnets:
            network = neutron_utils.get_network_by_id(
                neutron, port.network_id)

            ip_addrs = list()
            if network and router.external_fixed_ips:
                for ext_fixed_ips in router.external_fixed_ips:
                    for subnet in subnets:
                        if ext_fixed_ips['subnet_id'] == subnet.id:
                            ip_addrs.append(ext_fixed_ips['ip_address'])
            else:
                for ip in port.ips:
                    ip_addrs.append(ip['ip_address'])

            ports = neutron_utils.get_ports(neutron, network, ip_addrs)
            for out_port in ports:
                out_ports.append(out_port)

    port_settings = __create_port_configs(neutron, out_ports)

    filtered_settings = list()
    for port_setting in port_settings:
        if port_setting.network_name != ext_net_name:
            filtered_settings.append(port_setting)

    return RouterConfig(
        name=router.name, external_gateway=ext_net_name,
        admin_state_up=router.admin_state_up,
        port_settings=filtered_settings)


def create_volume_config(volume):
    """
    Returns a VolumeConfig object
    :param volume: a SNAPS-OO Volume object
    """

    return VolumeConfig(
        name=volume.name, description=volume.description,
        size=volume.size, type_name=volume.type,
        availability_zone=volume.availability_zone,
        multi_attach=volume.multi_attach)


def create_volume_type_config(volume_type):
    """
    Returns a VolumeTypeConfig object
    :param volume_type: a SNAPS-OO VolumeType object
    """

    control = None
    if volume_type.encryption:
        if (volume_type.encryption.control_location
                == ControlLocation.front_end.value):
            control = ControlLocation.front_end
        else:
            control = ControlLocation.back_end

    if volume_type and volume_type.encryption:
        encrypt_settings = VolumeTypeEncryptionConfig(
            name=volume_type.encryption.__class__,
            provider_class=volume_type.encryption.provider,
            control_location=control,
            cipher=volume_type.encryption.cipher,
            key_size=volume_type.encryption.key_size)
    else:
        encrypt_settings = None

    qos_spec_name = None
    if volume_type.qos_spec:
        qos_spec_name = volume_type.qos_spec.name

    return VolumeTypeConfig(
        name=volume_type.name, encryption=encrypt_settings,
        qos_spec_name=qos_spec_name, public=volume_type.public)


def create_flavor_config(flavor):
    """
    Returns a FlavorConfig object
    :param flavor: a FlavorConfig object
    """
    return FlavorConfig(
        name=flavor.name, flavor_id=flavor.id, ram=flavor.ram,
        disk=flavor.disk, vcpus=flavor.vcpus, ephemeral=flavor.ephemeral,
        swap=flavor.swap, rxtx_factor=flavor.rxtx_factor,
        is_public=flavor.is_public)


def create_keypair_config(heat_cli, stack, keypair, pk_output_key):
    """
    Instantiates a KeypairConfig object from a Keypair domain objects
    :param heat_cli: the heat client
    :param stack: the Stack domain object
    :param keypair: the Keypair SNAPS domain object
    :param pk_output_key: the key to the heat template's outputs for retrieval
                          of the private key file
    :return: a KeypairConfig object
    """
    if pk_output_key:
        outputs = heat_utils.get_outputs(heat_cli, stack)
        for output in outputs:
            if output.key == pk_output_key:
                # Save to file
                guid = uuid.uuid4()
                key_file = file_utils.save_string_to_file(
                    output.value, str(guid), 0o400)

                # Use outputs, file and resources for the KeypairConfig
                return KeypairConfig(
                    name=keypair.name, private_filepath=key_file.name)

    return KeypairConfig(name=keypair.name)


def create_vm_inst_config(nova, keystone, neutron, server, project_name):
    """
    Returns a VmInstanceConfig object
    note: if the server instance is not active, the PortSettings objects will
    not be generated resulting in an invalid configuration
    :param nova: the nova client
    :param keystone: the keystone client
    :param neutron: the neutron client
    :param server: a SNAPS-OO VmInst domain object
    :param project_name: the associated project name
    :return:
    """

    flavor_name = nova_utils.get_flavor_by_id(nova, server.flavor_id)

    kwargs = dict()
    kwargs['name'] = server.name
    kwargs['flavor'] = flavor_name

    kwargs['port_settings'] = __create_port_configs(neutron, server.ports)
    kwargs['security_group_names'] = server.sec_grp_names
    kwargs['floating_ip_settings'] = __create_floatingip_config(
        neutron, keystone, kwargs['port_settings'], project_name)

    return VmInstanceConfig(**kwargs)


def __create_port_configs(neutron, ports):
    """
    Returns a list of PortConfig objects based on the networks parameter
    :param neutron: the neutron client
    :param ports: a list of SNAPS-OO Port domain objects
    :return:
    """
    out = list()

    for port in ports:
        if port.device_owner != 'network:dhcp':
            ip_addrs = list()
            for ip_dict in port.ips:
                subnet = neutron_utils.get_subnet_by_id(
                    neutron, ip_dict['subnet_id'])
                ip_addrs.append({'subnet_name': subnet.name,
                                 'ip': ip_dict['ip_address']})

            network = neutron_utils.get_network_by_id(neutron, port.network_id)
            kwargs = dict()
            if port.name:
                kwargs['name'] = port.name
            kwargs['network_name'] = network.name
            kwargs['mac_address'] = port.mac_address
            kwargs['allowed_address_pairs'] = port.allowed_address_pairs
            kwargs['admin_state_up'] = port.admin_state_up
            kwargs['ip_addrs'] = ip_addrs
            out.append(PortConfig(**kwargs))

    return out


def __create_floatingip_config(neutron, keystone, port_settings, project_name):
    """
    Returns a list of FloatingIpConfig objects as they pertain to an
    existing deployed server instance
    :param neutron: the neutron client
    :param keystone: the keystone client
    :param port_settings: list of SNAPS-OO PortConfig objects
    :return: a list of FloatingIpConfig objects or an empty list if no
             floating IPs have been created
    """
    base_fip_name = 'fip-'
    fip_ctr = 1
    out = list()

    fip_ports = list()
    for port_setting in port_settings:
        setting_port = neutron_utils.get_port(
            neutron, keystone, port_setting, project_name=project_name)
        if setting_port:
            network = neutron_utils.get_network(
                neutron, keystone, network_name=port_setting.network_name)
            network_ports = neutron_utils.get_ports(neutron, network)
            if network_ports:
                for setting_port in network_ports:
                    if port_setting.mac_address == setting_port.mac_address:
                        fip_ports.append((port_setting.name, setting_port))
                        break

    floating_ips = neutron_utils.get_port_floating_ips(neutron, fip_ports)

    for port_id, floating_ip in floating_ips:
        router = neutron_utils.get_router_by_id(neutron, floating_ip.router_id)
        setting_port = neutron_utils.get_port_by_id(
            neutron, floating_ip.port_id)
        kwargs = dict()
        kwargs['name'] = base_fip_name + str(fip_ctr)
        kwargs['port_name'] = setting_port.name
        kwargs['port_id'] = setting_port.id
        kwargs['router_name'] = router.name

        if setting_port:
            for ip_dict in setting_port.ips:
                if ('ip_address' in ip_dict and
                        'subnet_id' in ip_dict and
                        ip_dict['ip_address'] == floating_ip.fixed_ip_address):
                    subnet = neutron_utils.get_subnet_by_id(
                        neutron, ip_dict['subnet_id'])
                    if subnet:
                        kwargs['subnet_name'] = subnet.name

        out.append(FloatingIpConfig(**kwargs))

        fip_ctr += 1

    return out


def determine_image_config(glance, server, image_settings):
    """
    Returns a ImageConfig object from the list that matches the name in one
    of the image_settings parameter
    :param glance: the glance client
    :param server: a SNAPS-OO VmInst domain object
    :param image_settings: list of ImageConfig objects
    :return: ImageConfig or None
    """
    if image_settings:
        for image_setting in image_settings:
            image = glance_utils.get_image_by_id(glance, server.image_id)
            if image and image.name == image_setting.name:
                return image_setting


def determine_keypair_config(heat_cli, stack, server, keypair_settings=None,
                             priv_key_key=None):
    """
    Returns a KeypairConfig object from the list that matches the
    server.keypair_name value in the keypair_settings parameter if not None,
    else if the output_key is not None, the output's value when contains the
    string 'BEGIN RSA PRIVATE KEY', this value will be stored into a file and
    encoded into the KeypairConfig object returned
    :param heat_cli: the OpenStack heat client
    :param stack: a SNAPS-OO Stack domain object
    :param server: a SNAPS-OO VmInst domain object
    :param keypair_settings: list of KeypairConfig objects
    :param priv_key_key: the stack options that holds the private key value
    :return: KeypairConfig or None
    """
    # Existing keypair being used by Heat Template
    if keypair_settings:
        for keypair_setting in keypair_settings:
            if server.keypair_name == keypair_setting.name:
                return keypair_setting

    # Keypair created by Heat template
    if priv_key_key:
        outputs = heat_utils.get_outputs(heat_cli, stack)
        for output in outputs:
            if output.key == priv_key_key:
                # Save to file
                guid = uuid.uuid4()
                key_file = file_utils.save_string_to_file(
                    output.value, str(guid), 0o400)

                # Use outputs, file and resources for the KeypairConfig
                return KeypairConfig(
                    name=server.keypair_name, private_filepath=key_file.name)
