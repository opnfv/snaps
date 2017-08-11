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

from neutronclient.common.exceptions import NotFound
from neutronclient.neutron.client import Client

from snaps.domain.network import (
    Port, SecurityGroup, SecurityGroupRule, Router, InterfaceRouter, Subnet,
    Network)
from snaps.domain.project import NetworkQuotas
from snaps.domain.vm_inst import FloatingIp
from snaps.openstack.utils import keystone_utils

__author__ = 'spisarski'

logger = logging.getLogger('neutron_utils')

"""
Utilities for basic neutron API calls
"""


def neutron_client(os_creds):
    """
    Instantiates and returns a client for communications with OpenStack's
    Neutron server
    :param os_creds: the credentials for connecting to the OpenStack remote API
    :return: the client object
    """
    return Client(api_version=os_creds.network_api_version,
                  session=keystone_utils.keystone_session(os_creds),
                  region_name=os_creds.region_name)


def create_network(neutron, os_creds, network_settings):
    """
    Creates a network for OpenStack
    :param neutron: the client
    :param os_creds: the OpenStack credentials
    :param network_settings: A dictionary containing the network configuration
                             and is responsible for creating the network
                            request JSON body
    :return: a SNAPS-OO Network domain object
    """
    if neutron and network_settings:
        logger.info('Creating network with name ' + network_settings.name)
        json_body = network_settings.dict_for_neutron(os_creds)
        os_network = neutron.create_network(body=json_body)
        return Network(**os_network['network'])
    else:
        raise NeutronException('Failded to create network')


def delete_network(neutron, network):
    """
    Deletes a network for OpenStack
    :param neutron: the client
    :param network: a SNAPS-OO Network domain object
    """
    if neutron and network:
        logger.info('Deleting network with name ' + network.name)
        neutron.delete_network(network.id)


def get_network(neutron, network_settings=None, network_name=None,
                project_id=None):
    """
    Returns Network SNAPS-OO domain object the first network found with
    either the given attributes from the network_settings object if not None,
    else the query will use just the name from the network_name parameter.
    When the project_id is included, that will be added to the query filter.
    :param neutron: the client
    :param network_settings: the NetworkSettings object used to create filter
    :param network_name: the name of the network to retrieve
    :param project_id: the id of the network's project
    :return: a SNAPS-OO Network domain object
    """
    net_filter = dict()
    if network_settings:
        net_filter['name'] = network_settings.name
    elif network_name:
        net_filter['name'] = network_name

    if project_id:
        net_filter['project_id'] = project_id

    networks = neutron.list_networks(**net_filter)
    for network, netInsts in networks.items():
        for inst in netInsts:
            return Network(**inst)


def get_network_by_id(neutron, network_id):
    """
    Returns the network object (dictionary) with the given ID else None
    :param neutron: the client
    :param network_id: the id of the network to retrieve
    :return: a SNAPS-OO Network domain object
    """
    networks = neutron.list_networks(**{'id': network_id})
    for network in networks['networks']:
        if network['id'] == network_id:
            return Network(**network)


def create_subnet(neutron, subnet_settings, os_creds, network=None):
    """
    Creates a network subnet for OpenStack
    :param neutron: the client
    :param network: the network object
    :param subnet_settings: A dictionary containing the subnet configuration
                            and is responsible for creating the subnet request
                            JSON body
    :param os_creds: the OpenStack credentials
    :return: a SNAPS-OO Subnet domain object
    """
    if neutron and network and subnet_settings:
        json_body = {'subnets': [subnet_settings.dict_for_neutron(
            os_creds, network=network)]}
        logger.info('Creating subnet with name ' + subnet_settings.name)
        subnets = neutron.create_subnet(body=json_body)
        return Subnet(**subnets['subnets'][0])
    else:
        raise NeutronException('Failed to create subnet')


def delete_subnet(neutron, subnet):
    """
    Deletes a network subnet for OpenStack
    :param neutron: the client
    :param subnet: a SNAPS-OO Subnet domain object
    """
    if neutron and subnet:
        logger.info('Deleting subnet with name ' + subnet.name)
        neutron.delete_subnet(subnet.id)


def get_subnet(neutron, subnet_settings=None, subnet_name=None):
    """
    Returns the first subnet object that fits the query else None including
    if subnet_settings or subnet_name parameters are None.
    :param neutron: the client
    :param subnet_settings: the subnet settings of the object to retrieve
    :param subnet_name: the name of the subnet to retrieve
    :return: a SNAPS-OO Subnet domain object or None
    """
    sub_filter = dict()
    if subnet_settings:
        sub_filter['name'] = subnet_settings.name
        sub_filter['cidr'] = subnet_settings.cidr
        if subnet_settings.gateway_ip:
            sub_filter['gateway_ip'] = subnet_settings.gateway_ip

        if subnet_settings.enable_dhcp is not None:
            sub_filter['enable_dhcp'] = subnet_settings.enable_dhcp

        if subnet_settings.destination:
            sub_filter['destination'] = subnet_settings.destination

        if subnet_settings.nexthop:
            sub_filter['nexthop'] = subnet_settings.nexthop

        if subnet_settings.ipv6_ra_mode:
            sub_filter['ipv6_ra_mode'] = subnet_settings.ipv6_ra_mode

        if subnet_settings.ipv6_address_mode:
            sub_filter['ipv6_address_mode'] = subnet_settings.ipv6_address_mode
    elif subnet_name:
        sub_filter['name'] = subnet_name
    else:
        return None

    subnets = neutron.list_subnets(**sub_filter)
    for subnet in subnets['subnets']:
        return Subnet(**subnet)


def get_subnet_by_id(neutron, subnet_id):
    """
    Returns a SNAPS-OO Subnet domain object for a given ID
    :param neutron: the OpenStack neutron client
    :param subnet_id: the subnet ID
    :return: a Subnet object
    """
    os_subnet = neutron.show_subnet(subnet_id)
    if os_subnet and 'subnet' in os_subnet:
        return Subnet(**os_subnet['subnet'])


def get_subnets_by_network(neutron, network):
    """
    Returns a list of SNAPS-OO Subnet domain objects
    :param neutron: the OpenStack neutron client
    :param network: the SNAPS-OO Network domain object
    :return: a list of Subnet objects
    """
    out = list()

    os_subnets = neutron.list_subnets(network_id=network.id)

    for os_subnet in os_subnets['subnets']:
        out.append(Subnet(**os_subnet))

    return out


def create_router(neutron, os_creds, router_settings):
    """
    Creates a router for OpenStack
    :param neutron: the client
    :param os_creds: the OpenStack credentials
    :param router_settings: A dictionary containing the router configuration
                            and is responsible for creating the subnet request
                            JSON body
    :return: a SNAPS-OO Router domain object
    """
    if neutron:
        json_body = router_settings.dict_for_neutron(neutron, os_creds)
        logger.info('Creating router with name - ' + router_settings.name)
        os_router = neutron.create_router(json_body)
        return Router(**os_router['router'])
    else:
        logger.error("Failed to create router.")
        raise NeutronException('Failed to create router')


def delete_router(neutron, router):
    """
    Deletes a router for OpenStack
    :param neutron: the client
    :param router: a SNAPS-OO Router domain object
    """
    if neutron and router:
        logger.info('Deleting router with name - ' + router.name)
        neutron.delete_router(router=router.id)


def get_router(neutron, router_settings=None, router_name=None):
    """
    Returns the first router object (dictionary) found the given the settings
    values if not None, else finds the first with the value of the router_name
    parameter, else None
    :param neutron: the client
    :param router_settings: the RouterSettings object
    :param router_name: the name of the network to retrieve
    :return: a SNAPS-OO Router domain object
    """
    router_filter = dict()
    if router_settings:
        router_filter['name'] = router_settings.name
        if router_settings.admin_state_up is not None:
            router_filter['admin_state_up'] = router_settings.admin_state_up
    elif router_name:
        router_filter['name'] = router_name
    else:
        return None

    routers = neutron.list_routers(**router_filter)
    for routerInst in routers['routers']:
        return Router(**routerInst)
    return None


def add_interface_router(neutron, router, subnet=None, port=None):
    """
    Adds an interface router for OpenStack for either a subnet or port.
    Exception will be raised if requesting for both.
    :param neutron: the client
    :param router: the router object
    :param subnet: the subnet object
    :param port: the port object
    :return: the interface router object
    """
    if subnet and port:
        raise NeutronException(
            'Cannot add interface to the router. Both subnet and '
            'port were sent in. Either or please.')

    if neutron and router and (router or subnet):
        logger.info('Adding interface to router with name ' + router.name)
        os_intf_router = neutron.add_interface_router(
            router=router.id, body=__create_port_json_body(subnet, port))
        return InterfaceRouter(**os_intf_router)
    else:
        raise NeutronException(
            'Unable to create interface router as neutron client,'
            ' router or subnet were not created')


def remove_interface_router(neutron, router, subnet=None, port=None):
    """
    Removes an interface router for OpenStack
    :param neutron: the client
    :param router: the SNAPS-OO Router domain object
    :param subnet: the subnet object (either subnet or port, not both)
    :param port: the port object
    """
    if router:
        try:
            logger.info('Removing router interface from router named ' +
                        router.name)
            neutron.remove_interface_router(
                router=router.id,
                body=__create_port_json_body(subnet, port))
        except NotFound as e:
            logger.warning('Could not remove router interface. NotFound - %s',
                           e)
            pass
    else:
        logger.warning('Could not remove router interface, No router object')


def __create_port_json_body(subnet=None, port=None):
    """
    Returns the dictionary required for creating and deleting router
    interfaces. Will only work on a subnet or port object. Will throw and
    exception if parameters contain both or neither
    :param subnet: the subnet object
    :param port: the port object
    :return: the dict
    """
    if subnet and port:
        raise NeutronException(
            'Cannot create JSON body with both subnet and port')
    if not subnet and not port:
        raise NeutronException(
            'Cannot create JSON body without subnet or port')

    if subnet:
        return {"subnet_id": subnet.id}
    else:
        return {"port_id": port.id}


def create_port(neutron, os_creds, port_settings):
    """
    Creates a port for OpenStack
    :param neutron: the client
    :param os_creds: the OpenStack credentials
    :param port_settings: the settings object for port configuration
    :return: the SNAPS-OO Port domain object
    """
    json_body = port_settings.dict_for_neutron(neutron, os_creds)
    logger.info('Creating port for network with name - %s',
                port_settings.network_name)
    os_port = neutron.create_port(body=json_body)['port']
    return Port(name=os_port['name'], id=os_port['id'],
                ips=os_port['fixed_ips'],
                mac_address=os_port['mac_address'],
                allowed_address_pairs=os_port['allowed_address_pairs'])


def delete_port(neutron, port):
    """
    Removes an OpenStack port
    :param neutron: the client
    :param port: the SNAPS-OO Port domain object
    """
    logger.info('Deleting port with name ' + port.name)
    neutron.delete_port(port.id)


def get_port(neutron, port_settings=None, port_name=None):
    """
    Returns the first port object (dictionary) found for the given query
    :param neutron: the client
    :param port_settings: the PortSettings object used for generating the query
    :param port_name: if port_settings is None, this name is the value to place
                      into the query
    :return: a SNAPS-OO Port domain object
    """
    port_filter = dict()

    if port_settings:
        port_filter['name'] = port_settings.name
        if port_settings.admin_state_up:
            port_filter['admin_state_up'] = port_settings.admin_state_up
        if port_settings.device_id:
            port_filter['device_id'] = port_settings.device_id
        if port_settings.mac_address:
            port_filter['mac_address'] = port_settings.mac_address
    elif port_name:
        port_filter['name'] = port_name

    ports = neutron.list_ports(**port_filter)
    for port in ports['ports']:
        return Port(name=port['name'], id=port['id'],
                    ips=port['fixed_ips'], mac_address=port['mac_address'])
    return None


def create_security_group(neutron, keystone, sec_grp_settings):
    """
    Creates a security group object in OpenStack
    :param neutron: the Neutron client
    :param keystone: the Keystone client
    :param sec_grp_settings: the security group settings
    :return: a SNAPS-OO SecurityGroup domain object
    """
    logger.info('Creating security group with name - %s',
                sec_grp_settings.name)
    os_group = neutron.create_security_group(
        sec_grp_settings.dict_for_neutron(keystone))
    return SecurityGroup(**os_group['security_group'])


def delete_security_group(neutron, sec_grp):
    """
    Deletes a security group object from OpenStack
    :param neutron: the client
    :param sec_grp: the SNAPS SecurityGroup object to delete
    """
    logger.info('Deleting security group with name - %s', sec_grp.name)
    neutron.delete_security_group(sec_grp.id)


def get_security_group(neutron, sec_grp_settings=None, sec_grp_name=None,
                       project_id=None):
    """
    Returns the first security group for a given query. The query gets built
    from the sec_grp_settings parameter if not None, else only the name of
    the security group will be used, else if the query parameters are None then
    None will be returned
    :param neutron: the client
    :param sec_grp_settings: an instance of SecurityGroupSettings config object
    :param sec_grp_name: the name of security group object to retrieve
    :param project_id: the ID of the project/tentant object that owns the
                       secuity group to retrieve
    :return: a SNAPS-OO SecurityGroup domain object or None if not found
    """

    sec_grp_filter = dict()
    if project_id:
        sec_grp_filter['tenant_id'] = project_id

    if sec_grp_settings:
        sec_grp_filter['name'] = sec_grp_settings.name

        if sec_grp_settings.description:
            sec_grp_filter['description'] = sec_grp_settings.description
    elif sec_grp_name:
        sec_grp_filter['name'] = sec_grp_name
    else:
        return None

    groups = neutron.list_security_groups(**sec_grp_filter)
    for group in groups['security_groups']:
        return SecurityGroup(**group)


def get_security_group_by_id(neutron, sec_grp_id):
    """
    Returns the first security group object of the given name else None
    :param neutron: the client
    :param sec_grp_id: the id of the security group to retrieve
    :return: a SNAPS-OO SecurityGroup domain object or None if not found
    """
    logger.info('Retrieving security group with ID - ' + sec_grp_id)

    groups = neutron.list_security_groups(**{'id': sec_grp_id})
    for group in groups['security_groups']:
        if group['id'] == sec_grp_id:
            return SecurityGroup(**group)
    return None


def create_security_group_rule(neutron, sec_grp_rule_settings):
    """
    Creates a security group object in OpenStack
    :param neutron: the client
    :param sec_grp_rule_settings: the security group rule settings
    :return: a SNAPS-OO SecurityGroupRule domain object
    """
    logger.info('Creating security group to security group - %s',
                sec_grp_rule_settings.sec_grp_name)
    os_rule = neutron.create_security_group_rule(
        sec_grp_rule_settings.dict_for_neutron(neutron))
    return SecurityGroupRule(**os_rule['security_group_rule'])


def delete_security_group_rule(neutron, sec_grp_rule):
    """
    Deletes a security group object from OpenStack
    :param neutron: the client
    :param sec_grp_rule: the SNAPS SecurityGroupRule object to delete
    """
    logger.info('Deleting security group rule with ID - %s',
                sec_grp_rule.id)
    neutron.delete_security_group_rule(sec_grp_rule.id)


def get_rules_by_security_group(neutron, sec_grp):
    """
    Retrieves all of the rules for a given security group
    :param neutron: the client
    :param sec_grp: a list of SNAPS SecurityGroupRule domain objects
    """
    logger.info('Retrieving security group rules associate with the '
                'security group - %s', sec_grp.name)
    out = list()
    rules = neutron.list_security_group_rules(
        **{'security_group_id': sec_grp.id})
    for rule in rules['security_group_rules']:
        if rule['security_group_id'] == sec_grp.id:
            out.append(SecurityGroupRule(**rule))
    return out


def get_rule_by_id(neutron, sec_grp, rule_id):
    """
    Deletes a security group object from OpenStack
    :param neutron: the client
    :param sec_grp: the SNAPS SecurityGroup domain object
    :param rule_id: the rule's ID
    :param sec_grp: a SNAPS SecurityGroupRule domain object
    """
    rules = neutron.list_security_group_rules(
        **{'security_group_id': sec_grp.id})
    for rule in rules['security_group_rules']:
        if rule['id'] == rule_id:
            return SecurityGroupRule(**rule)
    return None


def get_external_networks(neutron):
    """
    Returns a list of external OpenStack network object/dict for all external
    networks
    :param neutron: the client
    :return: a list of external networks of Type SNAPS-OO domain class Network
    """
    out = list()
    for network in neutron.list_networks(
            **{'router:external': True})['networks']:
        out.append(Network(**network))
    return out


def get_floating_ips(neutron, ports=None):
    """
    Returns all of the floating IPs
    When ports is not None, FIPs returned must be associated with one of the
    ports in the list and a tuple 2 where the first element being the port's
    name and the second being the FloatingIp SNAPS-OO domain object.
    When ports is None, all known FloatingIp SNAPS-OO domain objects will be
    returned in a list
    :param neutron: the Neutron client
    :param ports: a list of SNAPS-OO Port objects to join
    :return: a list of tuple 2 (port_name, SNAPS FloatingIp) objects when ports
             is not None else a list of Port objects
    """
    out = list()
    fips = neutron.list_floatingips()
    for fip in fips['floatingips']:
        if ports:
            for port_name, port in ports:
                if fip['port_id'] == port.id:
                    out.append((port.name, FloatingIp(
                        inst_id=fip['id'], ip=fip['floating_ip_address'])))
                    break
        else:
            out.append(FloatingIp(inst_id=fip['id'],
                                  ip=fip['floating_ip_address']))

    return out


def create_floating_ip(neutron, ext_net_name):
    """
    Returns the floating IP object that was created with this call
    :param neutron: the Neutron client
    :param ext_net_name: the name of the external network on which to apply the
                         floating IP address
    :return: the SNAPS FloatingIp object
    """
    logger.info('Creating floating ip to external network - ' + ext_net_name)
    ext_net = get_network(neutron, network_name=ext_net_name)
    if ext_net:
        fip = neutron.create_floatingip(
            body={'floatingip':
                  {'floating_network_id': ext_net.id}})

        return FloatingIp(inst_id=fip['floatingip']['id'],
                          ip=fip['floatingip']['floating_ip_address'])
    else:
        raise NeutronException(
            'Cannot create floating IP, external network not found')


def get_floating_ip(neutron, floating_ip):
    """
    Returns a floating IP object that should be identical to the floating_ip
    parameter
    :param neutron: the Neutron client
    :param floating_ip: the SNAPS FloatingIp object
    :return: hopefully the same floating IP object input
    """
    logger.debug('Attempting to retrieve existing floating ip with IP - %s',
                 floating_ip.ip)
    os_fip = __get_os_floating_ip(neutron, floating_ip)
    if os_fip:
        return FloatingIp(
            inst_id=os_fip['id'], ip=os_fip['floating_ip_address'])


def __get_os_floating_ip(neutron, floating_ip):
    """
    Returns an OpenStack floating IP object
    parameter
    :param neutron: the Neutron client
    :param floating_ip: the SNAPS FloatingIp object
    :return: hopefully the same floating IP object input
    """
    logger.debug('Attempting to retrieve existing floating ip with IP - %s',
                 floating_ip.ip)
    fips = neutron.list_floatingips(ip=floating_ip.id)

    for fip in fips['floatingips']:
        if fip['id'] == floating_ip.id:
            return fip


def delete_floating_ip(neutron, floating_ip):
    """
    Responsible for deleting a floating IP
    :param neutron: the Neutron client
    :param floating_ip: the SNAPS FloatingIp object
    :return:
    """
    logger.debug('Attempting to delete existing floating ip with IP - %s',
                 floating_ip.ip)
    return neutron.delete_floatingip(floating_ip.id)


def get_network_quotas(neutron, project_id):
    """
    Returns a list of all available keypairs
    :param nova: the Nova client
    :param project_id: the project's ID of the quotas to lookup
    :return: an object of type NetworkQuotas or None if not found
    """
    quota = neutron.show_quota(project_id)
    if quota:
        return NetworkQuotas(**quota['quota'])


def update_quotas(neutron, project_id, network_quotas):
    """
    Updates the networking quotas for a given project
    :param neutron: the Neutron client
    :param project_id: the project's ID that requires quota updates
    :param network_quotas: an object of type NetworkQuotas containing the
                           values to update
    :return:
    """
    update_body = dict()
    update_body['security_group'] = network_quotas.security_group
    update_body['security_group_rule'] = network_quotas.security_group_rule
    update_body['floatingip'] = network_quotas.floatingip
    update_body['network'] = network_quotas.network
    update_body['port'] = network_quotas.port
    update_body['router'] = network_quotas.router
    update_body['subnet'] = network_quotas.subnet

    return neutron.update_quota(project_id, {'quota': update_body})


class NeutronException(Exception):
    """
    Exception when calls to the Keystone client cannot be served properly
    """
