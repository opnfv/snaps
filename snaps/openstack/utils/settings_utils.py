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
from snaps.config.keypair import KeypairConfig
from snaps.openstack.create_flavor import FlavorSettings
from snaps.openstack.create_instance import (
    VmInstanceSettings, FloatingIpSettings)
from snaps.openstack.create_network import (
    PortSettings, SubnetSettings, NetworkSettings)
from snaps.openstack.create_security_group import (
    SecurityGroupSettings, SecurityGroupRuleSettings)
from snaps.openstack.create_router import RouterSettings
from snaps.openstack.create_volume import VolumeSettings
from snaps.openstack.create_volume_type import (
    VolumeTypeSettings, VolumeTypeEncryptionSettings, ControlLocation)
from snaps.openstack.utils import (
    neutron_utils, nova_utils, heat_utils, glance_utils)


def create_network_settings(neutron, network):
    """
    Returns a NetworkSettings object
    :param neutron: the neutron client
    :param network: a SNAPS-OO Network domain object
    :return:
    """
    return NetworkSettings(
        name=network.name, network_type=network.type,
        subnet_settings=create_subnet_settings(neutron, network))


def create_security_group_settings(neutron, security_group):
    """
    Returns a NetworkSettings object
    :param neutron: the neutron client
    :param security_group: a SNAPS-OO SecurityGroup domain object
    :return:
    """
    rules = neutron_utils.get_rules_by_security_group(neutron, security_group)

    rule_settings = list()
    for rule in rules:
        rule_settings.append(SecurityGroupRuleSettings(
            sec_grp_name=security_group.name, description=rule.description,
            direction=rule.direction, ethertype=rule.ethertype,
            port_range_min=rule.port_range_min,
            port_range_max=rule.port_range_max, protocol=rule.protocol,
            remote_group_id=rule.remote_group_id,
            remote_ip_prefix=rule.remote_ip_prefix))

    return SecurityGroupSettings(
        name=security_group.name, description=security_group.description,
        rule_settings=rule_settings)


def create_subnet_settings(neutron, network):
    """
    Returns a list of SubnetSettings objects for a given network
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
        out.append(SubnetSettings(**kwargs))
    return out


def create_router_settings(neutron, router):
    """
    Returns a RouterSettings object
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

    ports_tuple_list = list()
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
                    ip_addrs.append(ip)

            ip_list = list()
            if len(ip_addrs) > 0:
                for ip_addr in ip_addrs:
                    if isinstance(ip_addr, dict):
                        ip_list.append(ip_addr['ip_address'])
                    else:
                        ip_list.append(ip_addr)

            ports_tuple_list.append((network, ip_list))

    port_settings = __create_port_settings(neutron, ports_tuple_list)

    filtered_settings = list()
    for port_setting in port_settings:
        if port_setting.network_name != ext_net_name:
            filtered_settings.append(port_setting)

    return RouterSettings(
        name=router.name, external_gateway=ext_net_name,
        admin_state_up=router.admin_state_up,
        port_settings=filtered_settings)


def create_volume_settings(volume):
    """
    Returns a VolumeSettings object
    :param volume: a SNAPS-OO Volume object
    """

    return VolumeSettings(
        name=volume.name, description=volume.description,
        size=volume.size, type_name=volume.type,
        availability_zone=volume.availability_zone,
        multi_attach=volume.multi_attach)


def create_volume_type_settings(volume_type):
    """
    Returns a VolumeTypeSettings object
    :param volume_type: a SNAPS-OO VolumeType object
    """

    control = None
    if volume_type.encryption:
        if (volume_type.encryption.control_location
                == ControlLocation.front_end.value):
            control = ControlLocation.front_end
        else:
            control = ControlLocation.back_end

    encrypt_settings = VolumeTypeEncryptionSettings(
        name=volume_type.encryption.__class__,
        provider_class=volume_type.encryption.provider,
        control_location=control,
        cipher=volume_type.encryption.cipher,
        key_size=volume_type.encryption.key_size)

    qos_spec_name = None
    if volume_type.qos_spec:
        qos_spec_name = volume_type.qos_spec.name

    return VolumeTypeSettings(
        name=volume_type.name, encryption=encrypt_settings,
        qos_spec_name=qos_spec_name, public=volume_type.public)


def create_flavor_settings(flavor):
    """
    Returns a VolumeSettings object
    :param flavor: a SNAPS-OO Volume object
    """
    return FlavorSettings(
        name=flavor.name, flavor_id=flavor.id, ram=flavor.ram,
        disk=flavor.disk, vcpus=flavor.vcpus, ephemeral=flavor.ephemeral,
        swap=flavor.swap, rxtx_factor=flavor.rxtx_factor,
        is_public=flavor.is_public)


def create_keypair_settings(heat_cli, stack, keypair, pk_output_key):
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


def create_vm_inst_settings(nova, neutron, server):
    """
    Returns a NetworkSettings object
    :param nova: the nova client
    :param neutron: the neutron client
    :param server: a SNAPS-OO VmInst domain object
    :return:
    """

    flavor_name = nova_utils.get_flavor_by_id(nova, server.flavor_id)

    kwargs = dict()
    kwargs['name'] = server.name
    kwargs['flavor'] = flavor_name

    net_tuples = list()
    for net_name, ips in server.networks.items():
        network = neutron_utils.get_network(neutron, network_name=net_name)
        if network:
            net_tuples.append((network, ips))

    kwargs['port_settings'] = __create_port_settings(
        neutron, net_tuples)
    kwargs['security_group_names'] = server.sec_grp_names
    kwargs['floating_ip_settings'] = __create_floatingip_settings(
        neutron, kwargs['port_settings'])

    return VmInstanceSettings(**kwargs)


def __create_port_settings(neutron, networks):
    """
    Returns a list of port settings based on the networks parameter
    :param neutron: the neutron client
    :param networks: a list of tuples where #1 is the SNAPS Network domain
                     object and #2 is a list of IP addresses
    :return:
    """
    out = list()

    for network, ips in networks:
        ports = neutron_utils.get_ports(neutron, network, ips)
        for port in ports:
            if port.device_owner != 'network:dhcp':
                ip_addrs = list()
                for ip_dict in port.ips:
                    subnet = neutron_utils.get_subnet_by_id(
                        neutron, ip_dict['subnet_id'])
                    ip_addrs.append({'subnet_name': subnet.name,
                                     'ip': ip_dict['ip_address']})

                kwargs = dict()
                if port.name:
                    kwargs['name'] = port.name
                kwargs['network_name'] = network.name
                kwargs['mac_address'] = port.mac_address
                kwargs['allowed_address_pairs'] = port.allowed_address_pairs
                kwargs['admin_state_up'] = port.admin_state_up
                kwargs['ip_addrs'] = ip_addrs
                out.append(PortSettings(**kwargs))

    return out


def __create_floatingip_settings(neutron, port_settings):
    """
    Returns a list of FloatingIPSettings objects as they pertain to an
    existing deployed server instance
    :param neutron: the neutron client
    :param port_settings: list of SNAPS-OO PortSettings objects
    :return: a list of FloatingIPSettings objects or an empty list if no
             floating IPs have been created
    """
    base_fip_name = 'fip-'
    fip_ctr = 1
    out = list()

    fip_ports = list()
    for port_setting in port_settings:
        setting_port = neutron_utils.get_port(neutron, port_setting)
        if setting_port:
            network = neutron_utils.get_network(
                neutron, network_name=port_setting.network_name)
            network_ports = neutron_utils.get_ports(neutron, network)
            if network_ports:
                for setting_port in network_ports:
                    if port_setting.mac_address == setting_port.mac_address:
                        fip_ports.append((port_setting.name, setting_port))
                        break

    floating_ips = neutron_utils.get_floating_ips(neutron, fip_ports)

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

        out.append(FloatingIpSettings(**kwargs))

        fip_ctr += 1

    return out


def determine_image_settings(glance, server, image_settings):
    """
    Returns a ImageSettings object from the list that matches the name in one
    of the image_settings parameter
    :param glance: the glance client
    :param server: a SNAPS-OO VmInst domain object
    :param image_settings: list of ImageSettings objects
    :return: ImageSettings or None
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
