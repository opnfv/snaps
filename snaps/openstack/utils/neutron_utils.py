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
                  session=keystone_utils.keystone_session(os_creds))


def create_network(neutron, os_creds, network_settings):
    """
    Creates a network for OpenStack
    :param neutron: the client
    :param os_creds: the OpenStack credentials
    :param network_settings: A dictionary containing the network configuration
                             and is responsible for creating the network
                            request JSON body
    :return: the network object
    """
    if neutron and network_settings:
        logger.info('Creating network with name ' + network_settings.name)
        json_body = network_settings.dict_for_neutron(os_creds)
        return neutron.create_network(body=json_body)
    else:
        logger.error("Failed to create network")
        raise Exception


def delete_network(neutron, network):
    """
    Deletes a network for OpenStack
    :param neutron: the client
    :param network: the network object
    """
    if neutron and network:
        logger.info('Deleting network with name ' + network['network']['name'])
        neutron.delete_network(network['network']['id'])


def get_network(neutron, network_name, project_id=None):
    """
    Returns an object (dictionary) of the first network found with a given name
    and project_id (if included)
    :param neutron: the client
    :param network_name: the name of the network to retrieve
    :param project_id: the id of the network's project
    :return:
    """
    net_filter = dict()
    if network_name:
        net_filter['name'] = network_name
    if project_id:
        net_filter['project_id'] = project_id

    networks = neutron.list_networks(**net_filter)
    for network, netInsts in networks.items():
        for inst in netInsts:
            if inst.get('name') == network_name:
                if project_id and inst.get('project_id') == project_id:
                    return {'network': inst}
                else:
                    return {'network': inst}
    return None


def get_network_by_id(neutron, network_id):
    """
    Returns the network object (dictionary) with the given ID
    :param neutron: the client
    :param network_id: the id of the network to retrieve
    :return:
    """
    networks = neutron.list_networks(**{'id': network_id})
    for network, netInsts in networks.items():
        for inst in netInsts:
            if inst.get('id') == network_id:
                return {'network': inst}
    return None


def create_subnet(neutron, subnet_settings, os_creds, network=None):
    """
    Creates a network subnet for OpenStack
    :param neutron: the client
    :param network: the network object
    :param subnet_settings: A dictionary containing the subnet configuration
                            and is responsible for creating the subnet request
                            JSON body
    :param os_creds: the OpenStack credentials
    :return: the subnet object
    """
    if neutron and network and subnet_settings:
        json_body = {'subnets': [subnet_settings.dict_for_neutron(
            os_creds, network=network)]}
        logger.info('Creating subnet with name ' + subnet_settings.name)
        subnets = neutron.create_subnet(body=json_body)
        return {'subnet': subnets['subnets'][0]}
    else:
        logger.error("Failed to create subnet.")
        raise Exception


def delete_subnet(neutron, subnet):
    """
    Deletes a network subnet for OpenStack
    :param neutron: the client
    :param subnet: the subnet object
    """
    if neutron and subnet:
        logger.info('Deleting subnet with name ' + subnet['subnet']['name'])
        neutron.delete_subnet(subnet['subnet']['id'])


def get_subnet_by_name(neutron, subnet_name):
    """
    Returns the first subnet object (dictionary) found with a given name
    :param neutron: the client
    :param subnet_name: the name of the network to retrieve
    :return:
    """
    subnets = neutron.list_subnets(**{'name': subnet_name})
    for subnet, subnetInst in subnets.items():
        for inst in subnetInst:
            if inst.get('name') == subnet_name:
                return {'subnet': inst}
    return None


def create_router(neutron, os_creds, router_settings):
    """
    Creates a router for OpenStack
    :param neutron: the client
    :param os_creds: the OpenStack credentials
    :param router_settings: A dictionary containing the router configuration
                            and is responsible for creating the subnet request
                            JSON body
    :return: the router object
    """
    if neutron:
        json_body = router_settings.dict_for_neutron(neutron, os_creds)
        logger.info('Creating router with name - ' + router_settings.name)
        return neutron.create_router(json_body)
    else:
        logger.error("Failed to create router.")
        raise Exception


def delete_router(neutron, router):
    """
    Deletes a router for OpenStack
    :param neutron: the client
    :param router: the router object
    """
    if neutron and router:
        logger.info('Deleting router with name - ' + router['router']['name'])
        neutron.delete_router(router=router['router']['id'])
        return True


def get_router_by_name(neutron, router_name):
    """
    Returns the first router object (dictionary) found with a given name
    :param neutron: the client
    :param router_name: the name of the network to retrieve
    :return:
    """
    routers = neutron.list_routers(**{'name': router_name})
    for router, routerInst in routers.items():
        for inst in routerInst:
            if inst.get('name') == router_name:
                return {'router': inst}
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
        raise Exception('Cannot add interface to the router. Both subnet and '
                        'port were sent in. Either or please.')

    if neutron and router and (router or subnet):
        logger.info('Adding interface to router with name ' +
                    router['router']['name'])
        return neutron.add_interface_router(
            router=router['router']['id'],
            body=__create_port_json_body(subnet, port))
    else:
        raise Exception('Unable to create interface router as neutron client,'
                        ' router or subnet were not created')


def remove_interface_router(neutron, router, subnet=None, port=None):
    """
    Removes an interface router for OpenStack
    :param neutron: the client
    :param router: the router object
    :param subnet: the subnet object (either subnet or port, not both)
    :param port: the port object
    """
    if router:
        try:
            logger.info('Removing router interface from router named ' +
                        router['router']['name'])
            neutron.remove_interface_router(
                router=router['router']['id'],
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
        raise Exception('Cannot create JSON body with both subnet and port')
    if not subnet and not port:
        raise Exception('Cannot create JSON body without subnet or port')

    if subnet:
        return {"subnet_id": subnet['subnet']['id']}
    else:
        return {"port_id": port['port']['id']}


def create_port(neutron, os_creds, port_settings):
    """
    Creates a port for OpenStack
    :param neutron: the client
    :param os_creds: the OpenStack credentials
    :param port_settings: the settings object for port configuration
    :return: the port object
    """
    json_body = port_settings.dict_for_neutron(neutron, os_creds)
    logger.info('Creating port for network with name - %s',
                port_settings.network_name)
    return neutron.create_port(body=json_body)


def delete_port(neutron, port):
    """
    Removes an OpenStack port
    :param neutron: the client
    :param port: the port object
    :return:
    """
    logger.info('Deleting port with name ' + port['port']['name'])
    neutron.delete_port(port['port']['id'])


def get_port_by_name(neutron, port_name):
    """
    Returns the first port object (dictionary) found with a given name
    :param neutron: the client
    :param port_name: the name of the port to retrieve
    :return:
    """
    ports = neutron.list_ports(**{'name': port_name})
    for port in ports['ports']:
        if port['name'] == port_name:
            return {'port': port}
    return None


def create_security_group(neutron, keystone, sec_grp_settings):
    """
    Creates a security group object in OpenStack
    :param neutron: the Neutron client
    :param keystone: the Keystone client
    :param sec_grp_settings: the security group settings
    :return: the security group object
    """
    logger.info('Creating security group with name - %s',
                sec_grp_settings.name)
    return neutron.create_security_group(
        sec_grp_settings.dict_for_neutron(keystone))


def delete_security_group(neutron, sec_grp):
    """
    Deletes a security group object from OpenStack
    :param neutron: the client
    :param sec_grp: the security group object to delete
    """
    logger.info('Deleting security group with name - %s',
                sec_grp['security_group']['name'])
    return neutron.delete_security_group(sec_grp['security_group']['id'])


def get_security_group(neutron, name):
    """
    Returns the first security group object of the given name else None
    :param neutron: the client
    :param name: the name of security group object to retrieve
    """
    logger.info('Retrieving security group with name - ' + name)

    groups = neutron.list_security_groups(**{'name': name})
    for group in groups['security_groups']:
        if group['name'] == name:
            return {'security_group': group}
    return None


def get_security_group_by_id(neutron, sec_grp_id):
    """
    Returns the first security group object of the given name else None
    :param neutron: the client
    :param sec_grp_id: the id of the security group to retrieve
    """
    logger.info('Retrieving security group with ID - ' + sec_grp_id)

    groups = neutron.list_security_groups(**{'id': sec_grp_id})
    for group in groups['security_groups']:
        if group['id'] == sec_grp_id:
            return {'security_group': group}
    return None


def create_security_group_rule(neutron, sec_grp_rule_settings):
    """
    Creates a security group object in OpenStack
    :param neutron: the client
    :param sec_grp_rule_settings: the security group rule settings
    :return: the security group object
    """
    logger.info('Creating security group to security group - %s',
                sec_grp_rule_settings.sec_grp_name)
    return neutron.create_security_group_rule(
        sec_grp_rule_settings.dict_for_neutron(neutron))


def delete_security_group_rule(neutron, sec_grp_rule):
    """
    Deletes a security group object from OpenStack
    :param neutron: the client
    :param sec_grp_rule: the security group rule object to delete
    """
    logger.info('Deleting security group rule with ID - %s',
                sec_grp_rule['security_group_rule']['id'])
    neutron.delete_security_group_rule(
        sec_grp_rule['security_group_rule']['id'])


def get_rules_by_security_group(neutron, sec_grp):
    """
    Retrieves all of the rules for a given security group
    :param neutron: the client
    :param sec_grp: the security group object
    """
    logger.info('Retrieving security group rules associate with the '
                'security group - %s', sec_grp['security_group']['name'])
    out = list()
    rules = neutron.list_security_group_rules(
        **{'security_group_id': sec_grp['security_group']['id']})
    for rule in rules['security_group_rules']:
        if rule['security_group_id'] == sec_grp['security_group']['id']:
            out.append({'security_group_rule': rule})
    return out


def get_rule_by_id(neutron, sec_grp, rule_id):
    """
    Deletes a security group object from OpenStack
    :param neutron: the client
    :param sec_grp: the security group object
    :param rule_id: the rule's ID
    """
    rules = neutron.list_security_group_rules(
        **{'security_group_id': sec_grp['security_group']['id']})
    for rule in rules['security_group_rules']:
        if rule['id'] == rule_id:
            return {'security_group_rule': rule}
    return None


def get_external_networks(neutron):
    """
    Returns a list of external OpenStack network object/dict for all external
    networks
    :param neutron: the client
    :return: a list of external networks (empty list if none configured)
    """
    out = list()
    for network in neutron.list_networks(
            **{'router:external': True})['networks']:
        out.append({'network': network})
    return out


def get_floating_ips(neutron):
    """
    Returns all of the floating IPs
    :param neutron: the Neutron client
    :return: a list of SNAPS FloatingIp objects
    """
    out = list()
    fips = neutron.list_floatingips()
    for fip in fips['floatingips']:
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
    ext_net = get_network(neutron, ext_net_name)
    if ext_net:
        fip = neutron.create_floatingip(
            body={'floatingip':
                  {'floating_network_id': ext_net['network']['id']}})

        return FloatingIp(inst_id=fip['floatingip']['id'],
                          ip=fip['floatingip']['floating_ip_address'])
    else:
        raise Exception('Cannot create floating IP, '
                        'external network not found')


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
    os_fip = get_os_floating_ip(neutron, floating_ip)
    if os_fip:
        return FloatingIp(
            inst_id=os_fip['id'], ip=os_fip['floating_ip_address'])


def get_os_floating_ip(neutron, floating_ip):
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
