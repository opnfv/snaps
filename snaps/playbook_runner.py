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
import argparse
import ast
import logging
import os

import re

import yaml
from jinja2 import Environment, FileSystemLoader

from snaps.openstack.os_credentials import ProxySettings
from snaps.provisioning import ansible_utils

__author__ = 'spisarski'

logger = logging.getLogger('playbook_runner')


def main(parsed_args):
    """
    Uses ansible_utils for applying Ansible Playbooks to machines with a
    private key
    """
    logging.basicConfig(level=logging.DEBUG)
    logger.info('Starting Playbook Runner')

    proxy_settings = None
    if parsed_args.http_proxy:
        tokens = re.split(':', parsed_args.http_proxy)
        proxy_settings = ProxySettings(host=tokens[0], port=tokens[1],
                                       ssh_proxy_cmd=parsed_args.ssh_proxy_cmd)

    # Ensure can get an SSH client
    ssh = ansible_utils.ssh_client(
        parsed_args.ip_addr, parsed_args.host_user,
        private_key_filepath=parsed_args.priv_key,
        proxy_settings=proxy_settings)
    if ssh:
        ssh.close()

    env = Environment(loader=FileSystemLoader(
        searchpath=os.path.dirname(parsed_args.env_file)))
    template = env.get_template(os.path.basename(parsed_args.env_file))

    env_dict = dict()
    if parsed_args.vars:
        env_dict = ast.literal_eval(parsed_args.vars)

    output = template.render(**env_dict)

    variables = yaml.load(output)

    if not variables.get('env_file'):
        variables['env_file'] = parsed_args.env_file

    retval = ansible_utils.apply_playbook(
        parsed_args.playbook, [parsed_args.ip_addr], parsed_args.host_user,
        ssh_priv_key_file_path=parsed_args.priv_key,
        password=parsed_args.password, variables=variables,
        proxy_setting=proxy_settings)
    exit(retval)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--ip-addr', dest='ip_addr', required=True,
                        help='The Host IP Address')
    parser.add_argument('-u', '--host-user', dest='host_user', required=True,
                        help='Host user account')
    parser.add_argument('-k', '--priv-key', dest='priv_key', required=False,
                        help='The location of the private key file')
    parser.add_argument('-pw', '--password', dest='password', required=False,
                        help='The host-user password')
    parser.add_argument('-b', '--playbook', dest='playbook', required=True,
                        help='Playbook Location')
    parser.add_argument('-p', '--http-proxy', dest='http_proxy',
                        required=False, help='<host>:<port>')
    parser.add_argument('-s', '--ssh-proxy-cmd', dest='ssh_proxy_cmd',
                        required=False)
    parser.add_argument('-e', '--env-file', dest='env_file',
                        help='Yaml file containing playbook substitution vals',
                        required=False)
    parser.add_argument('-v', '--vars', dest='vars',
                        help='String renditon of a dict to pass into '
                             'playbook for additional subtitution values not '
                             'found in env_file',
                        required=False)
    args = parser.parse_args()

    main(args)
