#!/usr/bin/python
#
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
#
# This script is responsible for deploying virtual environments
import argparse
import logging
import os
import re

from snaps import file_utils
from snaps.openstack.create_flavor import FlavorSettings, OpenStackFlavor
from snaps.openstack.create_image import ImageSettings
from snaps.openstack.create_instance import VmInstanceSettings
from snaps.openstack.create_network import PortSettings, NetworkSettings
from snaps.openstack.create_router import RouterSettings
from snaps.openstack.create_keypairs import KeypairSettings
from snaps.openstack.os_credentials import OSCreds, ProxySettings
from snaps.openstack.utils import deploy_utils
from snaps.provisioning import ansible_utils

__author__ = 'spisarski'

logger = logging.getLogger('deploy_venv')

ARG_NOT_SET = "argument not set"


def __get_os_credentials(os_conn_config):
    """
    Returns an object containing all of the information required to access OpenStack APIs
    :param os_conn_config: The configuration holding the credentials
    :return: an OSCreds instance
    """
    proxy_settings = None
    http_proxy = os_conn_config.get('http_proxy')
    if http_proxy:
        tokens = re.split(':', http_proxy)
        ssh_proxy_cmd = os_conn_config.get('ssh_proxy_cmd')
        proxy_settings = ProxySettings(tokens[0], tokens[1], ssh_proxy_cmd)

    return OSCreds(username=os_conn_config.get('username'),
                   password=os_conn_config.get('password'),
                   auth_url=os_conn_config.get('auth_url'),
                   project_name=os_conn_config.get('project_name'),
                   proxy_settings=proxy_settings)


def __parse_ports_config(config):
    """
    Parses the "ports" configuration
    :param config: The dictionary to parse
    :param os_creds: The OpenStack credentials object
    :return: a list of PortConfig objects
    """
    out = list()
    for port_config in config:
        out.append(PortSettings(config=port_config.get('port')))
    return out


def __create_flavors(os_conn_config, flavors_config, cleanup=False):
    """
    Returns a dictionary of flavors where the key is the image name and the value is the image object
    :param os_conn_config: The OpenStack connection credentials
    :param flavors_config: The list of image configurations
    :param cleanup: Denotes whether or not this is being called for cleanup or not
    :return: dictionary
    """
    flavors = {}

    if flavors_config:
        try:
            for flavor_config_dict in flavors_config:
                flavor_config = flavor_config_dict.get('flavor')
                if flavor_config and flavor_config.get('name'):
                    flavor_creator = OpenStackFlavor(__get_os_credentials(os_conn_config),
                                                     FlavorSettings(flavor_config))
                    flavor_creator.create(cleanup=cleanup)
                    flavors[flavor_config['name']] = flavor_creator
        except Exception as e:
            for key, flavor_creator in flavors.iteritems():
                flavor_creator.clean()
            raise e
        logger.info('Created configured flavors')

    return flavors


def __create_images(os_conn_config, images_config, cleanup=False):
    """
    Returns a dictionary of images where the key is the image name and the value is the image object
    :param os_conn_config: The OpenStack connection credentials
    :param images_config: The list of image configurations
    :param cleanup: Denotes whether or not this is being called for cleanup or not
    :return: dictionary
    """
    images = {}

    if images_config:
        try:
            for image_config_dict in images_config:
                image_config = image_config_dict.get('image')
                if image_config and image_config.get('name'):
                    images[image_config['name']] = deploy_utils.create_image(__get_os_credentials(os_conn_config),
                                                                             ImageSettings(image_config), cleanup)
        except Exception as e:
            for key, image_creator in images.iteritems():
                image_creator.clean()
            raise e
        logger.info('Created configured images')

    return images


def __create_networks(os_conn_config, network_confs, cleanup=False):
    """
    Returns a dictionary of networks where the key is the network name and the value is the network object
    :param os_conn_config: The OpenStack connection credentials
    :param network_confs: The list of network configurations
    :param cleanup: Denotes whether or not this is being called for cleanup or not
    :return: dictionary
    """
    network_dict = {}

    if network_confs:
        try:
            for network_conf in network_confs:
                net_name = network_conf['network']['name']
                os_creds = __get_os_credentials(os_conn_config)
                network_dict[net_name] = deploy_utils.create_network(
                    os_creds, NetworkSettings(config=network_conf['network']), cleanup)
        except Exception as e:
            for key, net_creator in network_dict.iteritems():
                net_creator.clean()
            raise e

        logger.info('Created configured networks')

    return network_dict


def __create_routers(os_conn_config, router_confs, cleanup=False):
    """
    Returns a dictionary of networks where the key is the network name and the value is the network object
    :param os_conn_config: The OpenStack connection credentials
    :param router_confs: The list of router configurations
    :param cleanup: Denotes whether or not this is being called for cleanup or not
    :return: dictionary
    """
    router_dict = {}
    os_creds = __get_os_credentials(os_conn_config)

    if router_confs:
        try:
            for router_conf in router_confs:
                router_name = router_conf['router']['name']
                router_dict[router_name] = deploy_utils.create_router(
                    os_creds, RouterSettings(config=router_conf['router']), cleanup)
        except Exception as e:
            for key, router_creator in router_dict.iteritems():
                router_creator.clean()
            raise e

        logger.info('Created configured networks')

    return router_dict


def __create_keypairs(os_conn_config, keypair_confs, cleanup=False):
    """
    Returns a dictionary of keypairs where the key is the keypair name and the value is the keypair object
    :param os_conn_config: The OpenStack connection credentials
    :param keypair_confs: The list of keypair configurations
    :param cleanup: Denotes whether or not this is being called for cleanup or not
    :return: dictionary
    """
    keypairs_dict = {}
    if keypair_confs:
        try:
            for keypair_dict in keypair_confs:
                keypair_config = keypair_dict['keypair']
                kp_settings = KeypairSettings(keypair_config)
                keypairs_dict[keypair_config['name']] = deploy_utils.create_keypair(
                    __get_os_credentials(os_conn_config), kp_settings, cleanup)
        except Exception as e:
            for key, keypair_creator in keypairs_dict.iteritems():
                keypair_creator.clean()
            raise e

        logger.info('Created configured keypairs')

    return keypairs_dict


def __create_instances(os_conn_config, instances_config, image_dict, keypairs_dict, cleanup=False):
    """
    Returns a dictionary of instances where the key is the instance name and the value is the VM object
    :param os_conn_config: The OpenStack connection credentials
    :param instances_config: The list of VM instance configurations
    :param image_dict: A dictionary of images that will probably be used to instantiate the VM instance
    :param keypairs_dict: A dictionary of keypairs that will probably be used to instantiate the VM instance
    :param cleanup: Denotes whether or not this is being called for cleanup or not
    :return: dictionary
    """
    os_creds = __get_os_credentials(os_conn_config)

    vm_dict = {}

    if instances_config:
        try:
            for instance_config in instances_config:
                conf = instance_config.get('instance')
                if conf:
                    if image_dict:
                        image_creator = image_dict.get(conf.get('imageName'))
                        if image_creator:
                            instance_settings = VmInstanceSettings(config=instance_config['instance'])
                            kp_name = conf.get('keypair_name')
                            vm_dict[conf['name']] = deploy_utils.create_vm_instance(
                                os_creds, instance_settings, image_creator.image_settings,
                                keypair_creator=keypairs_dict[kp_name], cleanup=cleanup)
                        else:
                            raise Exception('Image creator instance not found. Cannot instantiate')
                    else:
                        raise Exception('Image dictionary is None. Cannot instantiate')
                else:
                    raise Exception('Instance configuration is None. Cannot instantiate')
        except Exception as e:
            logger.error('Unexpected error creating instances. Attempting to cleanup environment - ' + e.message)
            for key, inst_creator in vm_dict.iteritems():
                inst_creator.clean()
            raise e

        logger.info('Created configured instances')

    return vm_dict


def __apply_ansible_playbooks(ansible_configs, vm_dict, env_file):
    """
    Applies ansible playbooks to running VMs with floating IPs
    :param ansible_configs: a list of Ansible configurations
    :param vm_dict: the dictionary of newly instantiated VMs where the VM name is the key
    :param env_file: the path of the environment for setting the CWD so playbook location is relative to the deployment
                     file
    :return: t/f - true if successful
    """
    logger.info("Applying Ansible Playbooks")
    if ansible_configs:
        # Ensure all hosts are accepting SSH session requests
        for vm_inst in vm_dict.values():
            if not vm_inst.vm_ssh_active(block=True):
                logger.warn("Timeout waiting for instance to respond to SSH requests")
                return False

        # Set CWD so the deployment file's playbook location can leverage relative paths
        orig_cwd = os.getcwd()
        env_dir = os.path.dirname(env_file)
        os.chdir(env_dir)

        # Apply playbooks
        for ansible_config in ansible_configs:
            __apply_ansible_playbook(ansible_config, vm_dict)

        # Return to original directory
        os.chdir(orig_cwd)

    return True


def __apply_ansible_playbook(ansible_config, vm_dict):
    """
    Applies an Ansible configuration setting
    :param ansible_config: the configuration settings
    :param vm_dict: the dictionary of newly instantiated VMs where the VM name is the key
    :return:
    """
    if ansible_config:
        remote_user, floating_ips, private_key_filepath, proxy_settings = __get_connection_info(ansible_config, vm_dict)
        if floating_ips:
            ansible_utils.apply_playbook(ansible_config['playbook_location'], floating_ips, remote_user,
                                         private_key_filepath,
                                         variables=__get_variables(ansible_config.get('variables'), vm_dict),
                                         proxy_setting=proxy_settings)


def __get_connection_info(ansible_config, vm_dict):
    """
    Returns a tuple of data required for connecting to the running VMs
    (remote_user, [floating_ips], private_key_filepath, proxy_settings)
    :param ansible_config: the configuration settings
    :param vm_dict: the dictionary of VMs where the VM name is the key
    :return: tuple where the first element is the user and the second is a list of floating IPs and the third is the
    private key file location and the fourth is an instance of the snaps.ProxySettings class
    (note: in order to work, each of the hosts need to have the same sudo_user and private key file location values)
    """
    if ansible_config.get('hosts'):
        hosts = ansible_config['hosts']
        if len(hosts) > 0:
            floating_ips = list()
            remote_user = None
            private_key_filepath = None
            proxy_settings = None
            for host in hosts:
                vm = vm_dict.get(host)
                if vm:
                    fip = vm.get_floating_ip()
                    if fip:
                        remote_user = vm.get_image_user()

                        if fip:
                            floating_ips.append(fip.ip)
                        else:
                            raise Exception('Could not find floating IP for VM - ' + vm.name)

                        private_key_filepath = vm.keypair_settings.private_filepath
                        proxy_settings = vm.get_os_creds().proxy_settings
                else:
                    logger.error('Could not locate VM with name - ' + host)

            return remote_user, floating_ips, private_key_filepath, proxy_settings
    return None


def __get_variables(var_config, vm_dict):
    """
    Returns a dictionary of substitution variables to be used for Ansible templates
    :param var_config: the variable configuration settings
    :param vm_dict: the dictionary of VMs where the VM name is the key
    :return: dictionary or None
    """
    if var_config and vm_dict and len(vm_dict) > 0:
        variables = dict()
        for key, value in var_config.iteritems():
            value = __get_variable_value(value, vm_dict)
            if key and value:
                variables[key] = value
                logger.info("Set Jinga2 variable with key [" + key + "] the value [" + value + ']')
            else:
                logger.warn('Key [' + str(key) + '] or Value [' + str(value) + '] must not be None')
        return variables
    return None


def __get_variable_value(var_config_values, vm_dict):
    """
    Returns the associated variable value for use by Ansible for substitution purposes
    :param var_config_values: the configuration dictionary
    :param vm_dict: the dictionary containing all VMs where the key is the VM's name
    :return:
    """
    if var_config_values['type'] == 'string':
        return __get_string_variable_value(var_config_values)
    if var_config_values['type'] == 'vm-attr':
        return __get_vm_attr_variable_value(var_config_values, vm_dict)
    if var_config_values['type'] == 'os_creds':
        return __get_os_creds_variable_value(var_config_values, vm_dict)
    if var_config_values['type'] == 'port':
        return __get_vm_port_variable_value(var_config_values, vm_dict)
    return None


def __get_string_variable_value(var_config_values):
    """
    Returns the associated string value
    :param var_config_values: the configuration dictionary
    :return: the value contained in the dictionary with the key 'value'
    """
    return var_config_values['value']


def __get_vm_attr_variable_value(var_config_values, vm_dict):
    """
    Returns the associated value contained on a VM instance
    :param var_config_values: the configuration dictionary
    :param vm_dict: the dictionary containing all VMs where the key is the VM's name
    :return: the value
    """
    vm = vm_dict.get(var_config_values['vm_name'])
    if vm:
        if var_config_values['value'] == 'floating_ip':
            return vm.get_floating_ip().ip


def __get_os_creds_variable_value(var_config_values, vm_dict):
    """
    Returns the associated OS credentials value
    :param var_config_values: the configuration dictionary
    :param vm_dict: the dictionary containing all VMs where the key is the VM's name
    :return: the value
    """
    logger.info("Retrieving OS Credentials")
    vm = vm_dict.values()[0]

    if vm:
        if var_config_values['value'] == 'username':
            logger.info("Returning OS username")
            return vm.get_os_creds().username
        elif var_config_values['value'] == 'password':
            logger.info("Returning OS password")
            return vm.get_os_creds().password
        elif var_config_values['value'] == 'auth_url':
            logger.info("Returning OS auth_url")
            return vm.get_os_creds().auth_url
        elif var_config_values['value'] == 'project_name':
            logger.info("Returning OS project_name")
            return vm.get_os_creds().project_name

    logger.info("Returning none")
    return None


def __get_vm_port_variable_value(var_config_values, vm_dict):
    """
    Returns the associated OS credentials value
    :param var_config_values: the configuration dictionary
    :param vm_dict: the dictionary containing all VMs where the key is the VM's name
    :return: the value
    """
    port_name = var_config_values.get('port_name')
    vm_name = var_config_values.get('vm_name')

    if port_name and vm_name:
        vm = vm_dict.get(vm_name)
        if vm:
            port_value_id = var_config_values.get('port_value')
            if port_value_id:
                if port_value_id == 'mac_address':
                    return vm.get_port_mac(port_name)
                if port_value_id == 'ip_address':
                    return vm.get_port_ip(port_name)


def main(arguments):
    """
    Will need to set environment variable ANSIBLE_HOST_KEY_CHECKING=False or ...
    Create a file located in /etc/ansible/ansible/cfg or ~/.ansible.cfg containing the following content:

    [defaults]
    host_key_checking = False

    CWD must be this directory where this script is located.

    :return: To the OS
    """
    log_level = logging.INFO
    if arguments.log_level != 'INFO':
        log_level = logging.DEBUG
    logging.basicConfig(level=log_level)

    logger.info('Starting to Deploy')
    config = file_utils.read_yaml(arguments.environment)
    logger.info('Read configuration file - ' + arguments.environment)

    if config:
        os_config = config.get('openstack')

        image_dict = {}
        network_dict = {}
        router_dict = {}
        keypairs_dict = {}
        vm_dict = {}

        if os_config:
            try:
                os_conn_config = os_config.get('connection')

                # Create flavors
                flavor_dict = __create_flavors(os_conn_config, os_config.get('flavors'),
                                              arguments.clean is not ARG_NOT_SET)

                # Create images
                image_dict = __create_images(os_conn_config, os_config.get('images'),
                                             arguments.clean is not ARG_NOT_SET)

                # Create network
                network_dict = __create_networks(os_conn_config, os_config.get('networks'),
                                                 arguments.clean is not ARG_NOT_SET)

                # Create network
                router_dict = __create_routers(os_conn_config, os_config.get('routers'),
                                               arguments.clean is not ARG_NOT_SET)

                # Create keypairs
                keypairs_dict = __create_keypairs(os_conn_config, os_config.get('keypairs'),
                                                  arguments.clean is not ARG_NOT_SET)

                # Create instance
                vm_dict = __create_instances(os_conn_config, os_config.get('instances'), image_dict, keypairs_dict,
                                             arguments.clean is not ARG_NOT_SET)
                logger.info('Completed creating/retrieving all configured instances')
            except Exception as e:
                logger.error('Unexpected error deploying environment. Rolling back due to - ' + e.message)
                __cleanup(vm_dict, keypairs_dict, router_dict, network_dict, image_dict, flavor_dict, True)
                raise e


        # Must enter either block
        if arguments.clean is not ARG_NOT_SET:
            # Cleanup Environment
            __cleanup(vm_dict, keypairs_dict, router_dict, network_dict, image_dict, flavor_dict,
                      arguments.clean_image is not ARG_NOT_SET)
        elif arguments.deploy is not ARG_NOT_SET:
            logger.info('Configuring NICs where required')
            for vm in vm_dict.itervalues():
                vm.config_nics()
            logger.info('Completed NIC configuration')

            # Provision VMs
            ansible_config = config.get('ansible')
            if ansible_config and vm_dict:
                if not __apply_ansible_playbooks(ansible_config, vm_dict, arguments.environment):
                    logger.error("Problem applying ansible playbooks")
    else:
        logger.error('Unable to read configuration file - ' + arguments.environment)
        exit(1)

    exit(0)


def __cleanup(vm_dict, keypairs_dict, router_dict, network_dict, image_dict, flavor_dict, clean_image=False):
    for key, vm_inst in vm_dict.iteritems():
        vm_inst.clean()
    for key, kp_inst in keypairs_dict.iteritems():
        kp_inst.clean()
    for key, router_inst in router_dict.iteritems():
        router_inst.clean()
    for key, net_inst in network_dict.iteritems():
        net_inst.clean()
    if clean_image:
        for key, image_inst in image_dict.iteritems():
            image_inst.clean()
    for key, flavor_inst in flavor_dict.iteritems():
        flavor_inst.clean()


if __name__ == '__main__':
    # To ensure any files referenced via a relative path will begin from the diectory in which this file resides
    os.chdir(os.path.dirname(os.path.realpath(__file__)))

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--deploy', dest='deploy', nargs='?', default=ARG_NOT_SET,
                        help='When used, environment will be deployed and provisioned')
    parser.add_argument('-c', '--clean', dest='clean', nargs='?', default=ARG_NOT_SET,
                        help='When used, the environment will be removed')
    parser.add_argument('-i', '--clean-image', dest='clean_image', nargs='?', default=ARG_NOT_SET,
                        help='When cleaning, if this is set, the image will be cleaned too')
    parser.add_argument('-e', '--env', dest='environment', required=True,
                        help='The environment configuration YAML file - REQUIRED')
    parser.add_argument('-l', '--log-level', dest='log_level', default='INFO', help='Logging Level (INFO|DEBUG)')
    args = parser.parse_args()

    if args.deploy is ARG_NOT_SET and args.clean is ARG_NOT_SET:
        print 'Must enter either -d for deploy or -c for cleaning up and environment'
        exit(1)
    if args.deploy is not ARG_NOT_SET and args.clean is not ARG_NOT_SET:
        print 'Cannot enter both options -d/--deploy and -c/--clean'
        exit(1)
    main(args)
