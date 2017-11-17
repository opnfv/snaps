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

import time
from jinja2 import Environment, FileSystemLoader
import os
import yaml

from snaps import file_utils
from snaps.config.flavor import FlavorConfig
from snaps.config.image import ImageConfig
from snaps.config.keypair import KeypairConfig
from snaps.config.project import ProjectConfig
from snaps.config.qos import QoSConfig
from snaps.config.router import RouterConfig
from snaps.config.user import UserConfig
from snaps.openstack.create_flavor import OpenStackFlavor
from snaps.openstack.create_image import OpenStackImage
from snaps.openstack.create_instance import VmInstanceSettings
from snaps.openstack.create_keypairs import OpenStackKeypair
from snaps.openstack.create_network import (
    PortSettings, NetworkSettings, OpenStackNetwork)
from snaps.openstack.create_project import OpenStackProject
from snaps.openstack.create_qos import OpenStackQoS
from snaps.openstack.create_router import OpenStackRouter
from snaps.openstack.create_security_group import (
    OpenStackSecurityGroup, SecurityGroupSettings)
from snaps.openstack.create_user import OpenStackUser
from snaps.openstack.create_volume import OpenStackVolume, VolumeSettings
from snaps.openstack.create_volume_type import (
    OpenStackVolumeType, VolumeTypeSettings)
from snaps.openstack.os_credentials import OSCreds, ProxySettings
from snaps.openstack.utils import deploy_utils
from snaps.provisioning import ansible_utils

__author__ = 'spisarski'

logger = logging.getLogger('snaps_launcher')

ARG_NOT_SET = "argument not set"
DEFAULT_CREDS_KEY = 'admin'


def __get_creds_dict(os_conn_config):
    """
    Returns a dict of OSCreds where the key is the creds name.
    For backwards compatibility, credentials not contained in a list (only
    one) will be returned with the key of None
    :param os_conn_config: the credential configuration
    :return: a dict of OSCreds objects
    """
    if 'connection' in os_conn_config:
        return {DEFAULT_CREDS_KEY: __get_os_credentials(os_conn_config)}
    elif 'connections' in os_conn_config:
        out = dict()
        for os_conn_dict in os_conn_config['connections']:
            config = os_conn_dict.get('connection')
            if not config:
                raise Exception('Invalid connection format')

            name = config.get('name')
            if not name:
                raise Exception('Connection config requires a name field')

            out[name] = __get_os_credentials(os_conn_dict)
        return out


def __get_creds(os_creds_dict, os_user_dict, inst_config):
    """
    Returns the appropriate credentials
    :param os_creds_dict: a dictionary of OSCreds objects where the name is the
                          key
    :param os_user_dict: a dictionary of OpenStackUser objects where the name
                         is the key
    :param inst_config:
    :return: an OSCreds instance or None
    """
    os_creds = os_creds_dict.get(DEFAULT_CREDS_KEY)
    if 'os_user' in inst_config:
        os_user_conf = inst_config['os_user']
        if 'name' in os_user_conf:
            user_creator = os_user_dict.get(os_user_conf['name'])
            if user_creator:
                return user_creator.get_os_creds(
                    project_name=os_user_conf.get('project_name'))
    elif 'os_creds_name' in inst_config:
        if 'os_creds_name' in inst_config:
            os_creds = os_creds_dict[inst_config['os_creds_name']]
    return os_creds


def __get_os_credentials(os_conn_config):
    """
    Returns an object containing all of the information required to access
    OpenStack APIs
    :param os_conn_config: The configuration holding the credentials
    :return: an OSCreds instance
    """
    config = os_conn_config.get('connection')
    if not config:
        raise Exception('Invalid connection configuration')

    proxy_settings = None
    http_proxy = config.get('http_proxy')
    if http_proxy:
        tokens = re.split(':', http_proxy)
        ssh_proxy_cmd = config.get('ssh_proxy_cmd')
        proxy_settings = ProxySettings(host=tokens[0], port=tokens[1],
                                       ssh_proxy_cmd=ssh_proxy_cmd)
    else:
        if 'proxy_settings' in config:
            host = config['proxy_settings'].get('host')
            port = config['proxy_settings'].get('port')
            if host and host != 'None' and port and port != 'None':
                proxy_settings = ProxySettings(**config['proxy_settings'])

    if proxy_settings:
        config['proxy_settings'] = proxy_settings
    else:
        if config.get('proxy_settings'):
            del config['proxy_settings']

    return OSCreds(**config)


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


def __create_instances(os_creds_dict, creator_class, config_class, config,
                       config_key, cleanup=False, os_users_dict=None):
    """
    Returns a dictionary of SNAPS creator objects where the key is the name
    :param os_creds_dict: Dictionary of OSCreds objects where the key is the
                          name
    :param config: The list of configurations for the same type
    :param config_key: The list of configurations for the same type
    :param cleanup: Denotes whether or not this is being called for cleanup
    :return: dictionary
    """
    out = {}

    if config:
        try:
            for config_dict in config:
                inst_config = config_dict.get(config_key)
                if inst_config:
                    creator = creator_class(
                        __get_creds(os_creds_dict, os_users_dict, inst_config),
                        config_class(**inst_config))

                    if cleanup:
                        creator.initialize()
                    else:
                        creator.create()
                    out[inst_config['name']] = creator
            logger.info('Created configured %s', config_key)
        except Exception as e:
            logger.error('Unexpected error instantiating creator [%s] '
                         'with exception %s', creator_class, e)

    return out


def __create_vm_instances(os_creds_dict, os_users_dict, instances_config,
                          image_dict, keypairs_dict, cleanup=False):
    """
    Returns a dictionary of OpenStackVmInstance objects where the key is the
    instance name
    :param os_creds_dict: Dictionary of OSCreds objects where the key is the
                          name
    :param os_users_dict: Dictionary of OpenStackUser objects where the key is
                          the username
    :param instances_config: The list of VM instance configurations
    :param image_dict: A dictionary of images that will probably be used to
                       instantiate the VM instance
    :param keypairs_dict: A dictionary of keypairs that will probably be used
                          to instantiate the VM instance
    :param cleanup: Denotes whether or not this is being called for cleanup
    :return: dictionary
    """
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
                            kp_creator = keypairs_dict.get(
                                conf.get('keypair_name'))
                            vm_dict[conf[
                                'name']] = deploy_utils.create_vm_instance(
                                __get_creds(
                                    os_creds_dict, os_users_dict, conf),
                                instance_settings,
                                image_creator.image_settings,
                                keypair_creator=kp_creator,
                                init_only=cleanup)
                        else:
                            raise Exception('Image creator instance not found.'
                                            ' Cannot instantiate')
                    else:
                        raise Exception('Image dictionary is None. Cannot '
                                        'instantiate')
                else:
                    raise Exception('Instance configuration is None. Cannot '
                                    'instantiate')
            logger.info('Created configured instances')
        except Exception as e:
            logger.error('Unexpected error creating VM instances - %s', e)
    return vm_dict


def __apply_ansible_playbooks(ansible_configs, os_creds_dict, vm_dict,
                              image_dict, flavor_dict, env_file):
    """
    Applies ansible playbooks to running VMs with floating IPs
    :param ansible_configs: a list of Ansible configurations
    :param os_creds_dict: Dictionary of OSCreds objects where the key is the
                          name
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
            if 'pre_sleep_time' in ansible_config:
                try:
                    sleep_time = int(ansible_config['pre_sleep_time'])
                    logger.info('Waiting %s seconds to apply playbooks',
                                sleep_time)
                    time.sleep(sleep_time)
                except:
                    pass

            os_creds = os_creds_dict.get(None, 'admin')
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
                    'Unable to apply playbook found at location - %s',
                    ansible_config.get('playbook_location'))


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
    if var_config_values['type'] == 'floating_ip':
        return __get_vm_fip_variable_value(var_config_values, vm_dict)
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


def __get_vm_fip_variable_value(var_config_values, vm_dict):
    """
    Returns the floating IP value if found
    :param var_config_values: the configuration dictionary
    :param vm_dict: the dictionary containing all VMs where the key is the VM's
                    name
    :return: the floating IP string value or None
    """
    fip_name = var_config_values.get('fip_name')
    vm_name = var_config_values.get('vm_name')

    if vm_name:
        vm = vm_dict.get(vm_name)
        if vm:
            fip = vm.get_floating_ip(fip_name)
            if fip:
                return fip.ip


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

    # Apply env_file/substitution file to template
    env = Environment(loader=FileSystemLoader(
        searchpath=os.path.dirname(arguments.tmplt_file)))
    template = env.get_template(os.path.basename(arguments.tmplt_file))

    env_dict = dict()
    if arguments.env_file:
        env_dict = file_utils.read_yaml(arguments.env_file)
    output = template.render(**env_dict)

    config = yaml.load(output)

    if config:
        os_config = config.get('openstack')

        creators = list()
        vm_dict = dict()
        images_dict = dict()
        flavors_dict = dict()
        os_creds_dict = dict()
        clean = arguments.clean is not ARG_NOT_SET

        if os_config:
            os_creds_dict = __get_creds_dict(os_config)

            try:
                # Create projects
                projects_dict = __create_instances(
                    os_creds_dict, OpenStackProject, ProjectConfig,
                    os_config.get('projects'), 'project', clean)
                creators.append(projects_dict)

                # Create users
                users_dict = __create_instances(
                    os_creds_dict, OpenStackUser, UserConfig,
                    os_config.get('users'), 'user', clean)
                creators.append(users_dict)

                # Associate new users to projects
                if not clean:
                    for project_creator in projects_dict.values():
                        users = project_creator.project_settings.users
                        for user_name in users:
                            user_creator = users_dict.get(user_name)
                            if user_creator:
                                project_creator.assoc_user(
                                    user_creator.get_user())

                # Create flavors
                flavors_dict = __create_instances(
                    os_creds_dict, OpenStackFlavor, FlavorConfig,
                    os_config.get('flavors'), 'flavor', clean, users_dict)
                creators.append(flavors_dict)

                # Create QoS specs
                qos_dict = __create_instances(
                    os_creds_dict, OpenStackQoS, QoSConfig,
                    os_config.get('qos_specs'), 'qos_spec', clean, users_dict)
                creators.append(qos_dict)

                # Create volume types
                vol_type_dict = __create_instances(
                    os_creds_dict, OpenStackVolumeType, VolumeTypeSettings,
                    os_config.get('volume_types'), 'volume_type', clean,
                    users_dict)
                creators.append(vol_type_dict)

                # Create volume types
                vol_dict = __create_instances(
                    os_creds_dict, OpenStackVolume, VolumeSettings,
                    os_config.get('volumes'), 'volume', clean, users_dict)
                creators.append(vol_dict)

                # Create images
                images_dict = __create_instances(
                    os_creds_dict, OpenStackImage, ImageConfig,
                    os_config.get('images'), 'image', clean, users_dict)
                creators.append(images_dict)

                # Create networks
                creators.append(__create_instances(
                    os_creds_dict, OpenStackNetwork, NetworkSettings,
                    os_config.get('networks'), 'network', clean, users_dict))

                # Create routers
                creators.append(__create_instances(
                    os_creds_dict, OpenStackRouter, RouterConfig,
                    os_config.get('routers'), 'router', clean, users_dict))

                # Create keypairs
                keypairs_dict = __create_instances(
                    os_creds_dict, OpenStackKeypair, KeypairConfig,
                    os_config.get('keypairs'), 'keypair', clean, users_dict)
                creators.append(keypairs_dict)

                # Create security groups
                creators.append(__create_instances(
                    os_creds_dict, OpenStackSecurityGroup,
                    SecurityGroupSettings,
                    os_config.get('security_groups'), 'security_group', clean,
                    users_dict))

                # Create instance
                vm_dict = __create_vm_instances(
                    os_creds_dict, users_dict, os_config.get('instances'),
                    images_dict, keypairs_dict,
                    arguments.clean is not ARG_NOT_SET)
                creators.append(vm_dict)
                logger.info(
                    'Completed creating/retrieving all configured instances')
            except Exception as e:
                logger.error(
                    'Unexpected error deploying environment. Rolling back due'
                    ' to - ' + str(e))
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
                                                 os_creds_dict, vm_dict,
                                                 images_dict, flavors_dict,
                                                 arguments.tmplt_file):
                    logger.error("Problem applying ansible playbooks")
    else:
        logger.error(
            'Unable to read configuration file - ' + arguments.tmplt_file)
        exit(1)

    exit(0)


def __cleanup(creators, clean_image=False):
    for creator_dict in reversed(creators):
        for key, creator in creator_dict.items():
            if ((isinstance(creator, OpenStackImage) and clean_image)
                    or not isinstance(creator, OpenStackImage)):
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
        '-t', '--tmplt', dest='tmplt_file', required=True,
        help='The SNAPS deployment template YAML file - REQUIRED')
    parser.add_argument(
        '-e', '--env-file', dest='env_file',
        help='Yaml file containing substitution values to the env file')
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
