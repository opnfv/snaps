#!/usr/bin/python
#
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
#
# This script is responsible for deploying virtual environments
import argparse
import logging
import re

import os
from snaps import file_utils
from snaps.openstack.create_flavor import FlavorSettings, OpenStackFlavor
from snaps.openstack.create_image import ImageSettings, OpenStackImage
from snaps.openstack.create_instance import VmInstanceSettings
from snaps.openstack.create_keypairs import KeypairSettings
from snaps.openstack.create_network import PortSettings, NetworkSettings
from snaps.openstack.create_router import RouterSettings
from snaps.openstack.os_credentials import OSCreds, ProxySettings
from snaps.openstack.utils import deploy_utils
from snaps.provisioning import ansible_utils

__author__ = 'spisarski'

logger = logging.getLogger('deploy_venv')

ARG_NOT_SET = "argument not set"


def __get_os_credentials(os_conn_config):
    """
    Returns an object containing all of the information required to access
    OpenStack APIs
    :param os_conn_config: The configuration holding the credentials
    :return: an OSCreds instance
    """
    proxy_settings = None
    http_proxy = os_conn_config.get('http_proxy')
    if http_proxy:
        tokens = re.split(':', http_proxy)
        ssh_proxy_cmd = os_conn_config.get('ssh_proxy_cmd')
        proxy_settings = ProxySettings(host=tokens[0], port=tokens[1],
                                       ssh_proxy_cmd=ssh_proxy_cmd)

    os_conn_config['proxy_settings'] = proxy_settings

    return OSCreds(**os_conn_config)


def __parse_ports_config(config):
    """
    Parses the "ports" configuration
    :param config: The dictionary to parse
    :return: a list of PortConfig objects
    """
    out = list()
    for port_config in config:
        out.append(PortSettings(**port_config.get('port')))
    return out


def __create_flavors(os_conn_config, flavors_config, cleanup=False):
    """
    Returns a dictionary of flavors where the key is the image name and the
    value is the image object
    :param os_conn_config: The OpenStack connection credentials
    :param flavors_config: The list of image configurations
    :param cleanup: Denotes whether or not this is being called for cleanup
    :return: dictionary
    """
    flavors = {}

    if flavors_config:
        try:
            for flavor_config_dict in flavors_config:
                flavor_config = flavor_config_dict.get('flavor')
                if flavor_config and flavor_config.get('name'):
                    flavor_creator = OpenStackFlavor(
                        __get_os_credentials(os_conn_config),
                        FlavorSettings(**flavor_config))
                    flavor_creator.create(cleanup=cleanup)
                    flavors[flavor_config['name']] = flavor_creator
        except Exception as e:
            for key, flavor_creator in flavors.items():
                flavor_creator.clean()
            raise e
        logger.info('Created configured flavors')

    return flavors


def __create_images(os_conn_config, images_config, cleanup=False):
    """
    Returns a dictionary of images where the key is the image name and the
    value is the image object
    :param os_conn_config: The OpenStack connection credentials
    :param images_config: The list of image configurations
    :param cleanup: Denotes whether or not this is being called for cleanup
    :return: dictionary
    """
    images = {}

    if images_config:
        try:
            for image_config_dict in images_config:
                image_config = image_config_dict.get('image')
                if image_config and image_config.get('name'):
                    images[image_config['name']] = deploy_utils.create_image(
                        __get_os_credentials(os_conn_config),
                        ImageSettings(**image_config), cleanup)
        except Exception as e:
            for key, image_creator in images.items():
                image_creator.clean()
            raise e
        logger.info('Created configured images')

    return images


def __create_networks(os_conn_config, network_confs, cleanup=False):
    """
    Returns a dictionary of networks where the key is the network name and the
    value is the network object
    :param os_conn_config: The OpenStack connection credentials
    :param network_confs: The list of network configurations
    :param cleanup: Denotes whether or not this is being called for cleanup
    :return: dictionary
    """
    network_dict = {}

    if network_confs:
        try:
            for network_conf in network_confs:
                net_name = network_conf['network']['name']
                os_creds = __get_os_credentials(os_conn_config)
                network_dict[net_name] = deploy_utils.create_network(
                    os_creds, NetworkSettings(**network_conf['network']),
                    cleanup)
        except Exception as e:
            for key, net_creator in network_dict.items():
                net_creator.clean()
            raise e

        logger.info('Created configured networks')

    return network_dict


def __create_routers(os_conn_config, router_confs, cleanup=False):
    """
    Returns a dictionary of networks where the key is the network name and the
    value is the network object
    :param os_conn_config: The OpenStack connection credentials
    :param router_confs: The list of router configurations
    :param cleanup: Denotes whether or not this is being called for cleanup
    :return: dictionary
    """
    router_dict = {}
    os_creds = __get_os_credentials(os_conn_config)

    if router_confs:
        try:
            for router_conf in router_confs:
                router_name = router_conf['router']['name']
                router_dict[router_name] = deploy_utils.create_router(
                    os_creds, RouterSettings(**router_conf['router']), cleanup)
        except Exception as e:
            for key, router_creator in router_dict.items():
                router_creator.clean()
            raise e

        logger.info('Created configured networks')

    return router_dict


def __create_keypairs(os_conn_config, keypair_confs, cleanup=False):
    """
    Returns a dictionary of keypairs where the key is the keypair name and the
    value is the keypair object
    :param os_conn_config: The OpenStack connection credentials
    :param keypair_confs: The list of keypair configurations
    :param cleanup: Denotes whether or not this is being called for cleanup
    :return: dictionary
    """
    keypairs_dict = {}
    if keypair_confs:
        try:
            for keypair_dict in keypair_confs:
                keypair_config = keypair_dict['keypair']
                kp_settings = KeypairSettings(**keypair_config)
                keypairs_dict[
                    keypair_config['name']] = deploy_utils.create_keypair(
                    __get_os_credentials(os_conn_config), kp_settings, cleanup)
        except Exception as e:
            for key, keypair_creator in keypairs_dict.items():
                keypair_creator.clean()
            raise e

        logger.info('Created configured keypairs')

    return keypairs_dict


def __create_instances(os_conn_config, instances_config, image_dict,
                       keypairs_dict, cleanup=False):
    """
    Returns a dictionary of instances where the key is the instance name and
    the value is the VM object
    :param os_conn_config: The OpenStack connection credentials
    :param instances_config: The list of VM instance configurations
    :param image_dict: A dictionary of images that will probably be used to
                       instantiate the VM instance
    :param keypairs_dict: A dictionary of keypairs that will probably be used
                          to instantiate the VM instance
    :param cleanup: Denotes whether or not this is being called for cleanup
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
                            instance_settings = VmInstanceSettings(
                                **instance_config['instance'])
                            kp_name = conf.get('keypair_name')
                            vm_dict[conf[
                                'name']] = deploy_utils.create_vm_instance(
                                os_creds, instance_settings,
                                image_creator.image_settings,
                                keypair_creator=keypairs_dict[kp_name],
                                cleanup=cleanup)
                        else:
                            raise Exception('Image creator instance not found.'
                                            ' Cannot instantiate')
                    else:
                        raise Exception('Image dictionary is None. Cannot '
                                        'instantiate')
                else:
                    raise Exception('Instance configuration is None. Cannot '
                                    'instantiate')
        except Exception as e:
            logger.error('Unexpected error creating instances. Attempting to '
                         'cleanup environment - %s', e)
            for key, inst_creator in vm_dict.items():
                inst_creator.clean()
            raise e

        logger.info('Created configured instances')
    return vm_dict


def __apply_ansible_playbooks(ansible_configs, os_conn_config, vm_dict,
                              image_dict, flavor_dict, env_file):
    """
    Applies ansible playbooks to running VMs with floating IPs
    :param ansible_configs: a list of Ansible configurations
    :param os_conn_config: the OpenStack connection configuration used to
                           create an OSCreds instance
    :param vm_dict: the dictionary of newly instantiated VMs where the name is
                    the key
    :param image_dict: the dictionary of newly instantiated images where the
                       name is the key
    :param flavor_dict: the dictionary of newly instantiated flavors where the
                        name is the key
    :param env_file: the path of the environment for setting the CWD so
                     playbook location is relative to the deployment file
    :return: t/f - true if successful
    """
    logger.info("Applying Ansible Playbooks")
    if ansible_configs:
        # Ensure all hosts are accepting SSH session requests
        for vm_inst in list(vm_dict.values()):
            if not vm_inst.vm_ssh_active(block=True):
                logger.warning(
                    "Timeout waiting for instance to respond to SSH requests")
                return False

        # Set CWD so the deployment file's playbook location can leverage
        # relative paths
        orig_cwd = os.getcwd()
        env_dir = os.path.dirname(env_file)
        os.chdir(env_dir)

        # Apply playbooks
        for ansible_config in ansible_configs:
            os_creds = __get_os_credentials(os_conn_config)
            __apply_ansible_playbook(ansible_config, os_creds, vm_dict,
                                     image_dict, flavor_dict)

        # Return to original directory
        os.chdir(orig_cwd)

    return True


def __apply_ansible_playbook(ansible_config, os_creds, vm_dict, image_dict,
                             flavor_dict):
    """
    Applies an Ansible configuration setting
    :param ansible_config: the configuration settings
    :param os_creds: the OpenStack credentials object
    :param vm_dict: the dictionary of newly instantiated VMs where the name is
                    the key
    :param image_dict: the dictionary of newly instantiated images where the
                       name is the key
    :param flavor_dict: the dictionary of newly instantiated flavors where the
                        name is the key
    """
    if ansible_config:
        (remote_user, floating_ips, private_key_filepath,
         proxy_settings) = __get_connection_info(
            ansible_config, vm_dict)
        if floating_ips:
            retval = ansible_utils.apply_playbook(
                ansible_config['playbook_location'], floating_ips, remote_user,
                private_key_filepath,
                variables=__get_variables(ansible_config.get('variables'),
                                          os_creds, vm_dict, image_dict,
                                          flavor_dict),
                proxy_setting=proxy_settings)
            if retval != 0:
                # Not a fatal type of event
                logger.warning(
                    'Unable to apply playbook found at location - ' +
                    ansible_config('playbook_location'))


def __get_connection_info(ansible_config, vm_dict):
    """
    Returns a tuple of data required for connecting to the running VMs
    (remote_user, [floating_ips], private_key_filepath, proxy_settings)
    :param ansible_config: the configuration settings
    :param vm_dict: the dictionary of VMs where the VM name is the key
    :return: tuple where the first element is the user and the second is a list
             of floating IPs and the third is the
    private key file location and the fourth is an instance of the
    snaps.ProxySettings class
    (note: in order to work, each of the hosts need to have the same sudo_user
    and private key file location values)
    """
    if ansible_config.get('hosts'):
        hosts = ansible_config['hosts']
        if len(hosts) > 0:
            floating_ips = list()
            remote_user = None
            pk_file = None
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
                            raise Exception(
                                'Could not find floating IP for VM - ' +
                                vm.name)

                        pk_file = vm.keypair_settings.private_filepath
                        proxy_settings = vm.get_os_creds().proxy_settings
                else:
                    logger.error('Could not locate VM with name - ' + host)

            return remote_user, floating_ips, pk_file, proxy_settings
    return None


def __get_variables(var_config, os_creds, vm_dict, image_dict, flavor_dict):
    """
    Returns a dictionary of substitution variables to be used for Ansible
    templates
    :param var_config: the variable configuration settings
    :param os_creds: the OpenStack credentials object
    :param vm_dict: the dictionary of newly instantiated VMs where the name is
                    the key
    :param image_dict: the dictionary of newly instantiated images where the
                       name is the key
    :param flavor_dict: the dictionary of newly instantiated flavors where the
                        name is the key
    :return: dictionary or None
    """
    if var_config and vm_dict and len(vm_dict) > 0:
        variables = dict()
        for key, value in var_config.items():
            value = __get_variable_value(value, os_creds, vm_dict, image_dict,
                                         flavor_dict)
            if key and value:
                variables[key] = value
                logger.info(
                    "Set Jinga2 variable with key [%s] the value [%s]",
                    key, value)
            else:
                logger.warning('Key [%s] or Value [%s] must not be None',
                               str(key), str(value))
        return variables
    return None


def __get_variable_value(var_config_values, os_creds, vm_dict, image_dict,
                         flavor_dict):
    """
    Returns the associated variable value for use by Ansible for substitution
    purposes
    :param var_config_values: the configuration dictionary
    :param os_creds: the OpenStack credentials object
    :param vm_dict: the dictionary of newly instantiated VMs where the name is
                    the key
    :param image_dict: the dictionary of newly instantiated images where the
                       name is the key
    :param flavor_dict: the dictionary of newly instantiated flavors where the
                        name is the key
    :return:
    """
    if var_config_values['type'] == 'string':
        return __get_string_variable_value(var_config_values)
    if var_config_values['type'] == 'vm-attr':
        return __get_vm_attr_variable_value(var_config_values, vm_dict)
    if var_config_values['type'] == 'os_creds':
        return __get_os_creds_variable_value(var_config_values, os_creds)
    if var_config_values['type'] == 'port':
        return __get_vm_port_variable_value(var_config_values, vm_dict)
    if var_config_values['type'] == 'image':
        return __get_image_variable_value(var_config_values, image_dict)
    if var_config_values['type'] == 'flavor':
        return __get_flavor_variable_value(var_config_values, flavor_dict)
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
    :param vm_dict: the dictionary containing all VMs where the key is the VM's
                    name
    :return: the value
    """
    vm = vm_dict.get(var_config_values['vm_name'])
    if vm:
        if var_config_values['value'] == 'floating_ip':
            return vm.get_floating_ip().ip
        if var_config_values['value'] == 'image_user':
            return vm.get_image_user()


def __get_os_creds_variable_value(var_config_values, os_creds):
    """
    Returns the associated OS credentials value
    :param var_config_values: the configuration dictionary
    :param os_creds: the credentials
    :return: the value
    """
    logger.info("Retrieving OS Credentials")
    if os_creds:
        if var_config_values['value'] == 'username':
            logger.info("Returning OS username")
            return os_creds.username
        elif var_config_values['value'] == 'password':
            logger.info("Returning OS password")
            return os_creds.password
        elif var_config_values['value'] == 'auth_url':
            logger.info("Returning OS auth_url")
            return os_creds.auth_url
        elif var_config_values['value'] == 'project_name':
            logger.info("Returning OS project_name")
            return os_creds.project_name

    logger.info("Returning none")
    return None


def __get_vm_port_variable_value(var_config_values, vm_dict):
    """
    Returns the associated OS credentials value
    :param var_config_values: the configuration dictionary
    :param vm_dict: the dictionary containing all VMs where the key is the VM's
                    name
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


def __get_image_variable_value(var_config_values, image_dict):
    """
    Returns the associated image value
    :param var_config_values: the configuration dictionary
    :param image_dict: the dictionary containing all images where the key is
                       the name
    :return: the value
    """
    logger.info("Retrieving image values")

    if image_dict:
        if var_config_values.get('image_name'):
            image_creator = image_dict.get(var_config_values['image_name'])
            if image_creator:
                if var_config_values.get('value') and \
                                var_config_values['value'] == 'id':
                    return image_creator.get_image().id
                if var_config_values.get('value') and \
                        var_config_values['value'] == 'user':
                    return image_creator.image_settings.image_user

    logger.info("Returning none")
    return None


def __get_flavor_variable_value(var_config_values, flavor_dict):
    """
    Returns the associated flavor value
    :param var_config_values: the configuration dictionary
    :param flavor_dict: the dictionary containing all flavor creators where the
                        key is the name
    :return: the value or None
    """
    logger.info("Retrieving flavor values")

    if flavor_dict:
        if var_config_values.get('flavor_name'):
            flavor_creator = flavor_dict.get(var_config_values['flavor_name'])
            if flavor_creator:
                if var_config_values.get('value') and \
                                var_config_values['value'] == 'id':
                    return flavor_creator.get_flavor().id


def main(arguments):
    """
    Will need to set environment variable ANSIBLE_HOST_KEY_CHECKING=False or
    Create a file located in /etc/ansible/ansible/cfg or ~/.ansible.cfg
    containing the following content:

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
    logger.debug('Read configuration file - ' + arguments.environment)

    if config:
        os_config = config.get('openstack')

        os_conn_config = None
        creators = list()
        vm_dict = dict()
        images_dict = dict()
        flavors_dict = dict()

        if os_config:
            try:
                os_conn_config = os_config.get('connection')

                # Create flavors
                flavors_dict = __create_flavors(
                    os_conn_config, os_config.get('flavors'),
                    arguments.clean is not ARG_NOT_SET)
                creators.append(flavors_dict)

                # Create images
                images_dict = __create_images(
                    os_conn_config, os_config.get('images'),
                    arguments.clean is not ARG_NOT_SET)
                creators.append(images_dict)

                # Create network
                creators.append(__create_networks(
                    os_conn_config, os_config.get('networks'),
                    arguments.clean is not ARG_NOT_SET))

                # Create routers
                creators.append(__create_routers(
                    os_conn_config, os_config.get('routers'),
                    arguments.clean is not ARG_NOT_SET))

                # Create keypairs
                keypairs_dict = __create_keypairs(
                    os_conn_config, os_config.get('keypairs'),
                    arguments.clean is not ARG_NOT_SET)
                creators.append(keypairs_dict)

                # Create instance
                vm_dict = __create_instances(
                    os_conn_config, os_config.get('instances'),
                    images_dict, keypairs_dict,
                    arguments.clean is not ARG_NOT_SET)
                creators.append(vm_dict)
                logger.info(
                    'Completed creating/retrieving all configured instances')
            except Exception as e:
                logger.error(
                    'Unexpected error deploying environment. Rolling back due'
                    ' to - ' + str(e))
                __cleanup(creators)
                raise

        # Must enter either block
        if arguments.clean is not ARG_NOT_SET:
            # Cleanup Environment
            __cleanup(creators, arguments.clean_image is not ARG_NOT_SET)
        elif arguments.deploy is not ARG_NOT_SET:
            logger.info('Configuring NICs where required')
            for vm in vm_dict.values():
                vm.config_nics()
            logger.info('Completed NIC configuration')

            # Provision VMs
            ansible_config = config.get('ansible')
            if ansible_config and vm_dict:
                if not __apply_ansible_playbooks(ansible_config,
                                                 os_conn_config, vm_dict,
                                                 images_dict, flavors_dict,
                                                 arguments.environment):
                    logger.error("Problem applying ansible playbooks")
    else:
        logger.error(
            'Unable to read configuration file - ' + arguments.environment)
        exit(1)

    exit(0)


def __cleanup(creators, clean_image=False):
    for creator_dict in reversed(creators):
        for key, creator in creator_dict.items():
            if (isinstance(creator, OpenStackImage) and clean_image) or \
                    not isinstance(creator, OpenStackImage):
                try:
                    creator.clean()
                except Exception as e:
                    logger.warning('Error cleaning component - %s', e)


if __name__ == '__main__':
    # To ensure any files referenced via a relative path will begin from the
    # directory in which this file resides
    os.chdir(os.path.dirname(os.path.realpath(__file__)))

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-d', '--deploy', dest='deploy', nargs='?', default=ARG_NOT_SET,
        help='When used, environment will be deployed and provisioned')
    parser.add_argument(
        '-c', '--clean', dest='clean', nargs='?', default=ARG_NOT_SET,
        help='When used, the environment will be removed')
    parser.add_argument(
        '-i', '--clean-image', dest='clean_image', nargs='?',
        default=ARG_NOT_SET,
        help='When cleaning, if this is set, the image will be cleaned too')
    parser.add_argument(
        '-e', '--env', dest='environment', required=True,
        help='The environment configuration YAML file - REQUIRED')
    parser.add_argument(
        '-l', '--log-level', dest='log_level', default='INFO',
        help='Logging Level (INFO|DEBUG)')
    args = parser.parse_args()

    if args.deploy is ARG_NOT_SET and args.clean is ARG_NOT_SET:
        print(
            'Must enter either -d for deploy or -c for cleaning up and '
            'environment')
        exit(1)
    if args.deploy is not ARG_NOT_SET and args.clean is not ARG_NOT_SET:
        print('Cannot enter both options -d/--deploy and -c/--clean')
        exit(1)
    main(args)
