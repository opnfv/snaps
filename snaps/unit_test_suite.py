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
import argparse
import logging
import unittest
import os

from snaps import test_suite_builder

__author__ = 'spisarski'

logger = logging.getLogger('unit_test_suite')

ARG_NOT_SET = "argument not set"
LOG_LEVELS = {'FATAL': logging.FATAL, 'CRITICAL': logging.CRITICAL, 'ERROR': logging.ERROR, 'WARN': logging.WARN,
              'INFO': logging.INFO, 'DEBUG': logging.DEBUG}


def __create_test_suite(source_filename, ext_net_name, proxy_settings, ssh_proxy_cmd, run_unit_tests, use_keystone,
                        use_floating_ips, log_level):
    """
    Compiles the tests that should run
    :param source_filename: the OpenStack credentials file (required)
    :param ext_net_name: the name of the external network to use for floating IPs (required)
    :param run_unit_tests: when true, the tests not requiring OpenStack will be added to the test suite
    :param proxy_settings: <host>:<port> of the proxy server (optional)
    :param ssh_proxy_cmd: the command used to connect via SSH over some proxy server (optional)
    :param use_keystone: when true, tests creating users and projects will be exercised and must be run on a host that
                         has access to the cloud's administrative network
    :param use_floating_ips: when true, tests requiring floating IPs will be executed
    :param log_level: the logging level
    :return:
    """
    suite = unittest.TestSuite()

    # Tests that do not require a remote connection to an OpenStack cloud
    if run_unit_tests:
        test_suite_builder.add_unit_tests(suite)

    # Basic connection tests
    test_suite_builder.add_openstack_client_tests(suite, source_filename, ext_net_name, use_keystone=use_keystone,
                                                  http_proxy_str=proxy_settings, log_level=log_level)

    # Tests the OpenStack API calls
    test_suite_builder.add_openstack_api_tests(suite, source_filename, ext_net_name, use_keystone=use_keystone,
                                               http_proxy_str=proxy_settings, log_level=log_level)

    # Long running integration type tests
    test_suite_builder.add_openstack_integration_tests(suite, source_filename, ext_net_name, use_keystone=use_keystone,
                                                       proxy_settings=proxy_settings, ssh_proxy_cmd=ssh_proxy_cmd,
                                                       use_floating_ips=use_floating_ips,
                                                       log_level=log_level)
    return suite


def main(arguments):
    """
    Begins running unit tests.
    argv[1] if used must be the source filename else os_env.yaml will be leveraged instead
    argv[2] if used must be the proxy server <host>:<port>
    """
    logger.info('Starting test suite')

    log_level = LOG_LEVELS.get(arguments.log_level, logging.DEBUG)

    suite = None
    if arguments.env and arguments.ext_net:
        suite = __create_test_suite(arguments.env, arguments.ext_net, arguments.proxy, arguments.ssh_proxy_cmd,
                                    arguments.include_units != ARG_NOT_SET,
                                    arguments.use_keystone != ARG_NOT_SET,
                                    arguments.no_floating_ips == ARG_NOT_SET, log_level)
    else:
        logger.error('Environment file or external network not defined')
        exit(1)

    # To ensure any files referenced via a relative path will begin from the diectory in which this file resides
    os.chdir(os.path.dirname(os.path.realpath(__file__)))

    result = unittest.TextTestRunner(verbosity=2).run(suite)

    if result.errors:
        logger.error('Number of errors in test suite - ' + str(len(result.errors)))
        for test, message in result.errors:
            logger.error(str(test) + " ERROR with " + message)

    if result.failures:
        logger.error('Number of failures in test suite - ' + str(len(result.failures)))
        for test, message in result.failures:
            logger.error(str(test) + " FAILED with " + message)

    if (result.errors and len(result.errors) > 0) or (result.failures and len(result.failures) > 0):
        logger.error('See above for test failures')
        exit(1)
    else:
        logger.info('All tests completed successfully')

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
    parser.add_argument('-k', '--use-keystone', dest='use_keystone', default=ARG_NOT_SET, nargs='?',
                        help='When argument is set, the tests will exercise the keystone APIs and must be run on a ' +
                             'machine that has access to the admin network' +
                             ' and is able to create users and groups')
    parser.add_argument('-f', '--no-floating-ips', dest='no_floating_ips', default=ARG_NOT_SET, nargs='?',
                        help='When argument is set, all tests requiring Floating IPs will not be executed')
    parser.add_argument('-u', '--include-units', dest='include_units', default=ARG_NOT_SET, nargs='?',
                        help='When argument is set, all tests not requiring OpenStack will be executed')
    args = parser.parse_args()

    main(args)
