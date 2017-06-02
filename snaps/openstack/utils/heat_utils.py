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

from heatclient.client import Client
from snaps import file_utils
from snaps.domain.stack import Stack

from snaps.openstack.utils import keystone_utils

__author__ = 'spisarski'

logger = logging.getLogger('heat_utils')


def heat_client(os_creds):
    """
    Retrieves the Heat client
    :param os_creds: the OpenStack credentials
    :return: the client
    """
    logger.debug('Retrieving Nova Client')
    return Client(1, session=keystone_utils.keystone_session(os_creds))


def get_stack_by_name(heat_cli, stack_name):
    """
    Returns a domain Stack object
    :param heat_cli: the OpenStack heat client
    :param stack_name: the name of the heat stack
    :return: the Stack domain object else None
    """
    stacks = heat_cli.stacks.list(**{'name': stack_name})
    for stack in stacks:
        return Stack(name=stack.identifier, stack_id=stack.id)

    return None


def get_stack_by_id(heat_cli, stack_id):
    """
    Returns a domain Stack object for a given ID
    :param heat_cli: the OpenStack heat client
    :param stack_id: the ID of the heat stack to retrieve
    :return: the Stack domain object else None
    """
    stacks = heat_cli.stacks.list(**{'id': stack_id})
    for stack in stacks:
        return Stack(name=stack.identifier, stack_id=stack.id)

    return None


def get_stack_status(heat_cli, stack_id):
    """
    Returns the status of a Stack for a given ID
    :param heat_cli: the OpenStack heat client
    :param stack_id: the ID of the heat stack to retrieve
    :return: the status code
    """
    stacks = heat_cli.stacks.list(**{'id': stack_id})
    for stack in stacks:
        if stack:
            return stack.stack_status
    return None


def create_stack(heat_cli, stack_settings):
    """
    Executes an Ansible playbook to the given host
    :param heat_cli: the OpenStack heat client object
    :param stack_settings: the stack configuration
    :return: the Stack domain object
    """
    args = dict()
    args['template'] = file_utils.read_file(stack_settings.template_path)
    args['stack_name'] = stack_settings.name

    if stack_settings.env_values:
        args['parameters'] = stack_settings.env_values

    stack = heat_cli.stacks.create(**args)

    return get_stack_by_id(heat_cli, stack_id=stack['stack']['id'])


def delete_stack(heat_cli, stack):
    """
    Deletes the Heat stack
    :param heat_cli: the OpenStack heat client object
    :param stack: the OpenStack Heat stack object
    """
    heat_cli.stacks.delete(stack.id)
