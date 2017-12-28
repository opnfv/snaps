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

from jinja2 import Environment, FileSystemLoader
import os
import yaml

from snaps import file_utils
from snaps.openstack.utils import launch_utils

__author__ = 'spisarski'

logger = logging.getLogger('snaps_launcher')

ARG_NOT_SET = "argument not set"


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
        clean = arguments.clean is not ARG_NOT_SET
        clean_image = arguments.clean_image is not ARG_NOT_SET
        deploy = arguments.deploy is not ARG_NOT_SET
        launch_utils.launch_config(
            config, arguments.tmplt_file, deploy, clean, clean_image)
    else:
        logger.error(
            'Unable to read configuration file - ' + arguments.tmplt_file)
        exit(1)

    exit(0)


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
