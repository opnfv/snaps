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
import logging
import unittest

from snaps import test_suite_builder
from snaps.openstack.create_image import OpenStackImage
from snaps.openstack.tests import openstack_tests
from snaps.openstack.tests.os_source_file_test import OSComponentTestCase
from snaps.openstack.utils.tests.glance_utils_tests import GlanceUtilsTests

__author__ = 'spisarski'

logger = logging.getLogger('custom_image_test_runner')

ARG_NOT_SET = "argument not set"
LOG_LEVELS = {'FATAL': logging.FATAL, 'CRITICAL': logging.CRITICAL, 'ERROR': logging.ERROR, 'WARN': logging.WARN,
              'INFO': logging.INFO, 'DEBUG': logging.DEBUG}


def __run_tests(source_filename, ext_net_name, proxy_settings, ssh_proxy_cmd, use_keystone, use_floating_ips,
                log_level):
    """
    Compiles the tests that should run
    :param source_filename: the OpenStack credentials file (required)
    :param ext_net_name: the name of the external network to use for floating IPs (required)
    :param proxy_settings: <host>:<port> of the proxy server (optional)
    :param ssh_proxy_cmd: the command used to connect via SSH over some proxy server (optional)
    :param use_keystone: when true, tests creating users and projects will be exercised and must be run on a host that
                         has access to the cloud's administrative network
    :param use_floating_ips: when true, tests requiring floating IPs will be executed
    :param log_level: the logging level
    :return:
    """
    os_creds = openstack_tests.get_credentials(os_env_file=source_filename, proxy_settings_str=proxy_settings,
                                               ssh_proxy_cmd=ssh_proxy_cmd)
    image_creators = __create_images(os_creds)

    meta_list = list()

    # Create images from default
    meta_list.append(None)

    # Create images from specified URL
    meta_list.append(
        {'glance_tests': {'disk_url': openstack_tests.CIRROS_DEFAULT_IMAGE_URL},
         'cirros': {'disk_url': openstack_tests.CIRROS_DEFAULT_IMAGE_URL},
         'centos': {'disk_url': openstack_tests.CENTOS_DEFAULT_IMAGE_URL},
         'ubuntu': {'disk_url': openstack_tests.UBUNTU_DEFAULT_IMAGE_URL}})

    # Create images from file
    meta_list.append(
        {'glance_tests': {'disk_file': '../images/cirros-0.3.4-x86_64-disk.img'},
         'cirros': {'disk_file': '../images/cirros-0.3.4-x86_64-disk.img'},
         'centos': {'disk_file': '../images/CentOS-7-x86_64-GenericCloud.qcow2'},
         'ubuntu': {'disk_file': '../images/ubuntu-14.04-server-cloudimg-amd64-disk1.img'}})

    # Create images from Existing
    meta_list.append(
        {'glance_tests': {'disk_file': '../images/cirros-0.3.4-x86_64-disk.img'},
         'cirros': {'config': {'name': image_creators['cirros'].image_settings.name,
                               'exists': True, 'image_user': 'cirros'}},
         'centos': {'config': {'name': image_creators['centos'].image_settings.name,
                               'exists': True, 'image_user': 'centos'}},
         'ubuntu': {'config': {'name': image_creators['ubuntu'].image_settings.name,
                               'exists': True, 'image_user': 'ubuntu'}}})

    failure_count = 0
    error_count = 0

    try:
        for metadata in meta_list:
            logger.info('Starting tests with image metadata of - ' + str(metadata))
            suite = unittest.TestSuite()

            # Long running integration type tests
            suite.addTest(OSComponentTestCase.parameterize(
                GlanceUtilsTests, os_creds=os_creds, ext_net_name=ext_net_name, image_metadata=metadata,
                log_level=log_level))

            test_suite_builder.add_openstack_integration_tests(
                suite=suite, os_creds=os_creds, ext_net_name=ext_net_name, use_keystone=use_keystone,
                image_metadata=metadata, use_floating_ips=use_floating_ips, log_level=log_level)

            result = unittest.TextTestRunner(verbosity=2).run(suite)
            if result.errors:
                logger.error('Number of errors in test suite - ' + str(len(result.errors)))
                for test, message in result.errors:
                    logger.error(str(test) + " ERROR with " + message)
                    error_count += 1

            if result.failures:
                logger.error('Number of failures in test suite - ' + str(len(result.failures)))
                for test, message in result.failures:
                    logger.error(str(test) + " FAILED with " + message)
                    failure_count += 1

            if (result.errors and len(result.errors) > 0) or (result.failures and len(result.failures) > 0):
                logger.error('See above for test failures')
            else:
                logger.info('All tests completed successfully in run')

        logger.info('Total number of errors = ' + str(error_count))
        logger.info('Total number of failures = ' + str(failure_count))

        if error_count + failure_count > 0:
            exit(1)
    except Exception as e:
        logger.warn('Unexpected error running tests - %s', e)
        pass
    finally:
        for image_creator in image_creators.values():
            try:
                image_creator.clean()
            except Exception as e:
                logger.error('Exception thrown while cleaning image - %s', e)


def __create_images(os_creds):
    """
    Returns a dictionary of 
    :param os_creds: 
    :return: 
    """
    image_meta = {'cirros': {'disk_url': openstack_tests.CIRROS_DEFAULT_IMAGE_URL,
                             'kernel_url': openstack_tests.CIRROS_DEFAULT_KERNEL_IMAGE_URL,
                             'ramdisk_url': openstack_tests.CIRROS_DEFAULT_RAMDISK_IMAGE_URL},
                  'centos': {'disk_file': '../images/CentOS-7-x86_64-GenericCloud.qcow2'},
                  'ubuntu': {'disk_file': '../images/ubuntu-14.04-server-cloudimg-amd64-disk1.img'}}
    cirros_image_settings = openstack_tests.cirros_image_settings(name='static_image_test-cirros',
                                                                  image_metadata=image_meta, public=True)
    centos_image_settings = openstack_tests.centos_image_settings(name='static_image_test-centos',
                                                                  image_metadata=image_meta, public=True)
    ubuntu_image_settings = openstack_tests.ubuntu_image_settings(name='static_image_test-ubuntu',
                                                                  image_metadata=image_meta, public=True)

    out = dict()
    out['cirros'] = OpenStackImage(os_creds, cirros_image_settings)
    out['cirros'].create()
    out['centos'] = OpenStackImage(os_creds, centos_image_settings)
    out['centos'].create()
    out['ubuntu'] = OpenStackImage(os_creds, ubuntu_image_settings)
    out['ubuntu'].create()

    return out


def main(arguments):
    """
    Begins running tests with different image_metadata configuration.
    argv[1] if used must be the source filename else os_env.yaml will be leveraged instead
    argv[2] if used must be the proxy server <host>:<port>
    """
    log_level = LOG_LEVELS.get(arguments.log_level, logging.DEBUG)
    logging.basicConfig(level=log_level)
    logger.info('Starting test suite')

    __run_tests(arguments.env, arguments.ext_net, arguments.proxy, arguments.ssh_proxy_cmd,
                arguments.use_keystone != ARG_NOT_SET, arguments.floating_ips != ARG_NOT_SET, log_level)

    exit(0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-e', '--env', dest='env', required=True, help='OpenStack credentials file')
    parser.add_argument('-n', '--net', dest='ext_net', required=True, help='External network name')
    parser.add_argument('-p', '--proxy', dest='proxy', nargs='?', default=None,
                        help='Optonal HTTP proxy socket (<host>:<port>)')
    parser.add_argument('-s', '--ssh-proxy-cmd', dest='ssh_proxy_cmd', nargs='?', default=None,
                        help='Optonal SSH proxy command value')
    parser.add_argument('-l', '--log-level', dest='log_level', default='INFO',
                        help='Logging Level (FATAL|CRITICAL|ERROR|WARN|INFO|DEBUG)')
    parser.add_argument('-f', '--floating-ips', dest='floating_ips', default=ARG_NOT_SET, nargs='?',
                        help='When argument is set, all integration tests requiring Floating IPs will be executed')
    parser.add_argument('-k', '--use-keystone', dest='use_keystone', default=ARG_NOT_SET, nargs='?',
                        help='When argument is set, the tests will exercise the keystone APIs and must be run on a ' +
                             'machine that has access to the admin network' +
                             ' and is able to create users and groups')

    args = parser.parse_args()

    main(args)
