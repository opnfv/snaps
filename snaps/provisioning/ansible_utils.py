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

from collections import namedtuple

import os
import paramiko

try:
    from ansible.parsing.dataloader import DataLoader
    from ansible.vars.manager import VariableManager
    from ansible.inventory.manager import InventoryManager
    from ansible.executor.playbook_executor import PlaybookExecutor
except:
    pass

__author__ = 'spisarski'

logger = logging.getLogger('ansible_utils')


def apply_playbook(playbook_path, hosts_inv=None, host_user=None,
                   ssh_priv_key_file_path=None, password=None, variables=None,
                   proxy_setting=None):
    """
    Executes an Ansible playbook to the given host
    :param playbook_path: the (relative) path to the Ansible playbook
    :param hosts_inv: a list of hostnames/ip addresses to which to apply the
                      Ansible playbook (not required when PB is configured for
                      localhost)
    :param host_user: A user for the host instances (must be a password-less
                      sudo user if playbook has "sudo: yes") (not required when
                      PB is configured for localhost)
    :param ssh_priv_key_file_path: the file location of the ssh key. Required
                                   if password is None (not required when PB is
                                   configured for localhost)
    :param password: the file location of the ssh key. Required if
                     ssh_priv_key_file_path is None (not required when PB is
                     configured for localhost)
    :param variables: a dictionary containing any substitution variables needed
                      by the Jinga 2 templates
    :param proxy_setting: instance of os_credentials.ProxySettings class
    :raises AnsibleException when the return code from the Ansible library is
            not 0
    :return: the return code from the Ansible library only when 0.
             Implementation now raises an exception otherwise
    """
    if not os.path.isfile(playbook_path):
        raise AnsibleException(
            'Requested playbook not found - ' + playbook_path)

    pk_file_path = None
    if ssh_priv_key_file_path:
        pk_file_path = os.path.expanduser(ssh_priv_key_file_path)
        if not password:
            if not os.path.isfile(pk_file_path):
                raise AnsibleException(
                    'Requested private SSH key not found - ' + pk_file_path)

    passwords = None
    if password:
        passwords = {'conn_pass': password, 'become_pass': password}

    import ansible.constants
    ansible.constants.HOST_KEY_CHECKING = False

    loader = DataLoader()
    inventory = InventoryManager(loader=loader)
    if hosts_inv:
        for host in hosts_inv:
            inventory.add_host(host=host, group='ungrouped')
        connection = 'ssh'
    else:
        connection = 'local'

    variable_manager = VariableManager(loader=loader, inventory=inventory)

    if variables:
        variable_manager.extra_vars = variables

    ssh_extra_args = None
    if proxy_setting and proxy_setting.ssh_proxy_cmd:
        ssh_extra_args = '-o ProxyCommand=\'%s\'' % proxy_setting.ssh_proxy_cmd

    options = namedtuple(
        'Options', ['listtags', 'listtasks', 'listhosts', 'syntax',
                    'connection', 'module_path', 'forks', 'remote_user',
                    'private_key_file', 'ssh_common_args', 'ssh_extra_args',
                    'become', 'become_method', 'become_user', 'verbosity',
                    'check', 'timeout', 'diff'])

    ansible_opts = options(
        listtags=False, listtasks=False, listhosts=False, syntax=False,
        connection=connection, module_path=None, forks=100,
        remote_user=host_user, private_key_file=pk_file_path,
        ssh_common_args=None, ssh_extra_args=ssh_extra_args, become=None,
        become_method=None, become_user=None, verbosity=11111, check=False,
        timeout=30, diff=None)

    logger.debug('Setting up Ansible Playbook Executor for playbook - ' +
                 playbook_path)
    executor = PlaybookExecutor(
        playbooks=[playbook_path],
        inventory=inventory,
        variable_manager=variable_manager,
        loader=loader,
        options=ansible_opts,
        passwords=passwords)

    logger.debug('Executing Ansible Playbook - ' + playbook_path)
    ret_val = executor.run()

    if ret_val != 0:
        raise AnsibleException(
            'Error applying playbook [{}] with value [{}] using the connection'
            ' type of [{}]'.format(
                playbook_path, ret_val, connection))

    return ret_val


def ssh_client(ip, user, private_key_filepath=None, password=None,
               proxy_settings=None):
    """
    Retrieves and attemts an SSH connection
    :param ip: the IP of the host to connect
    :param user: the user with which to connect
    :param private_key_filepath: when None, password is required
    :param password: when None, private_key_filepath is required
    :param proxy_settings: instance of os_credentials.ProxySettings class
                           (optional)
    :return: the SSH client if can connect else false
    """
    logger.debug('Retrieving SSH client')
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.MissingHostKeyPolicy())

    try:
        proxy_cmd = None
        if proxy_settings and proxy_settings.ssh_proxy_cmd:
            proxy_cmd_str = str(proxy_settings.ssh_proxy_cmd.replace('%h', ip))
            proxy_cmd_str = proxy_cmd_str.replace("%p", '22')
            proxy_cmd = paramiko.ProxyCommand(proxy_cmd_str)

        pk_abs_path = None
        if not password and private_key_filepath:
            pk_abs_path = os.path.expanduser(private_key_filepath)

        ssh.connect(
            ip, username=user, key_filename=pk_abs_path, password=password,
            sock=proxy_cmd)
        logger.info('Obtained SSH connection to %s', ip)
        return ssh
    except Exception as e:
        logger.debug('Unable to connect via SSH with message - ' + str(e))


class AnsibleException(Exception):
    """
    Exception when calls to the Keystone client cannot be served properly
    """
