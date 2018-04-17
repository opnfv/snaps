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
import json
import logging
import unittest
from concurrencytest import ConcurrentTestSuite, fork_for_tests

from snaps import file_utils
from snaps import test_suite_builder as tsb
from snaps.openstack.tests import openstack_tests

__author__ = 'spisarski'

logger = logging.getLogger('test_runner')

ARG_NOT_SET = "argument not set"
LOG_LEVELS = {'FATAL': logging.FATAL, 'CRITICAL': logging.CRITICAL,
              'ERROR': logging.ERROR, 'WARN': logging.WARN,
              'INFO': logging.INFO, 'DEBUG': logging.DEBUG}


def __create_concurrent_test_suite(
        source_filename, ext_net_name, proxy_settings, ssh_proxy_cmd,
        run_unit_tests, run_connection_tests, run_api_tests,
        run_integration_tests, run_staging_tests, flavor_metadata,
        image_metadata, use_keystone, use_floating_ips, continuous_integration,
        log_level):
    """
    Compiles the tests that can be run concurrently
    :param source_filename: the OpenStack credentials file (required)
    :param ext_net_name: the name of the external network to use for floating
                         IPs (required)
    :param run_unit_tests: when true, the tests not requiring OpenStack will be
                           added to the test suite
    :param run_connection_tests: when true, the tests that perform simple
                                 connections to OpenStack are executed
    :param run_api_tests: when true, the tests that perform simple API calls to
                          OpenStack are executed
    :param run_integration_tests: when true, the integration tests are executed
    :param run_staging_tests: when true, the staging tests are executed
    :param proxy_settings: <host>:<port> of the proxy server (optional)
    :param ssh_proxy_cmd: the command used to connect via SSH over some proxy
                          server (optional)
    :param flavor_metadata: dict() object containing the metadata for flavors
                            created for test VM instance
    :param image_metadata: dict() object containing the metadata for overriding
                           default images within the tests
    :param use_keystone: when true, tests creating users and projects will be
                         exercised and must be run on a host that
                         has access to the cloud's administrative network
    :param use_floating_ips: when true, tests requiring floating IPs will be
                             executed
    :param continuous_integration: when true, tests for CI will be run
    :param log_level: the logging level
    :return:
    """
    suite = unittest.TestSuite()

    os_creds = openstack_tests.get_credentials(
        os_env_file=source_filename, proxy_settings_str=proxy_settings,
        ssh_proxy_cmd=ssh_proxy_cmd)

    # Tests that do not require a remote connection to an OpenStack cloud
    if run_unit_tests:
        tsb.add_unit_tests(suite)

    # Basic connection tests
    if run_connection_tests:
        tsb.add_openstack_client_tests(
            suite=suite, os_creds=os_creds, ext_net_name=ext_net_name,
            use_keystone=use_keystone, log_level=log_level)

    # Tests the OpenStack API calls
    if run_api_tests:
        tsb.add_openstack_api_tests(
            suite=suite, os_creds=os_creds, ext_net_name=ext_net_name,
            use_keystone=use_keystone, flavor_metadata=flavor_metadata,
            image_metadata=image_metadata, log_level=log_level)

    # Long running integration type tests
    if run_integration_tests:
        tsb.add_openstack_integration_tests(
            suite=suite, os_creds=os_creds, ext_net_name=ext_net_name,
            use_keystone=use_keystone, flavor_metadata=flavor_metadata,
            image_metadata=image_metadata, use_floating_ips=use_floating_ips,
            log_level=log_level)

    if run_staging_tests:
        tsb.add_openstack_staging_tests(
            suite=suite, os_creds=os_creds, ext_net_name=ext_net_name,
            log_level=log_level)

    if continuous_integration:
        tsb.add_openstack_ci_tests(
            suite=suite, os_creds=os_creds, ext_net_name=ext_net_name,
            use_keystone=use_keystone, flavor_metadata=flavor_metadata,
            image_metadata=image_metadata, use_floating_ips=use_floating_ips,
            log_level=log_level)
    return suite


def __create_sequential_test_suite(
        source_filename, ext_net_name, proxy_settings, ssh_proxy_cmd,
        run_integration_tests, flavor_metadata, image_metadata, use_keystone,
        use_floating_ips, log_level):
    """
    Compiles the tests that cannot be run in parallel
    :param source_filename: the OpenStack credentials file (required)
    :param ext_net_name: the name of the external network to use for floating
                         IPs (required)
    :param run_integration_tests: when true, the integration tests are executed
    :param proxy_settings: <host>:<port> of the proxy server (optional)
    :param ssh_proxy_cmd: the command used to connect via SSH over some proxy
                          server (optional)
    :param flavor_metadata: dict() object containing the metadata for flavors
                            created for test VM instance
    :param image_metadata: dict() object containing the metadata for overriding
                           default images within the tests
    :param use_keystone: when true, tests creating users and projects will be
                         exercised and must be run on a host that
                         has access to the cloud's administrative network
    :param use_floating_ips: when true, tests requiring floating IPs will be
                             executed
    :param log_level: the logging level
    :return:
    """
    if use_floating_ips and run_integration_tests:
        suite = unittest.TestSuite()

        os_creds = openstack_tests.get_credentials(
            os_env_file=source_filename, proxy_settings_str=proxy_settings,
            ssh_proxy_cmd=ssh_proxy_cmd)

        tsb.add_ansible_integration_tests(
                suite=suite, os_creds=os_creds, ext_net_name=ext_net_name,
                use_keystone=use_keystone, flavor_metadata=flavor_metadata,
                image_metadata=image_metadata, log_level=log_level)

        return suite


def __output_results(results):
    """
    Sends the test results to the logger
    :param results:
    :return:
    """

    if results.errors:
        logger.error('Number of errors in test suite - %s',
                     len(results.errors))
        for test, message in results.errors:
            logger.error(str(test) + " ERROR with " + message)

    if results.failures:
        logger.error('Number of failures in test suite - %s',
                     len(results.failures))
        for test, message in results.failures:
            logger.error(str(test) + " FAILED with " + message)


def main(arguments):
    """
    Begins running unit tests.
    argv[1] if used must be the source filename else os_env.yaml will be
    leveraged instead
    argv[2] if used must be the proxy server <host>:<port>
    """
    logger.info('Starting test suite')

    log_level = LOG_LEVELS.get(arguments.log_level, logging.DEBUG)

    flavor_metadata = None
    if arguments.flavor_metadata:
        flavor_metadata = json.loads(arguments.flavor_metadata)

    image_metadata = None
    if arguments.image_metadata_file:
        image_metadata = file_utils.read_yaml(arguments.image_metadata_file)

    concurrent_suite = None
    sequential_suite = None

    if arguments.env and arguments.ext_net:
        unit = arguments.include_unit != ARG_NOT_SET
        connection = arguments.include_connection != ARG_NOT_SET
        api = arguments.include_api != ARG_NOT_SET
        integration = arguments.include_integration != ARG_NOT_SET
        ci = arguments.continuous_integration != ARG_NOT_SET
        staging = arguments.include_staging != ARG_NOT_SET
        if (not unit and not connection and not api and not integration
                and not staging and not ci):
            unit = True
            connection = True
            api = True
            integration = True

        concurrent_suite = __create_concurrent_test_suite(
            arguments.env, arguments.ext_net, arguments.proxy,
            arguments.ssh_proxy_cmd, unit, connection, api,
            integration, staging, flavor_metadata, image_metadata,
            arguments.use_keystone != ARG_NOT_SET,
            arguments.floating_ips != ARG_NOT_SET,
            ci, log_level)

        if (arguments.include_integration != ARG_NOT_SET
                and arguments.floating_ips != ARG_NOT_SET):
            sequential_suite = __create_sequential_test_suite(
                arguments.env, arguments.ext_net, arguments.proxy,
                arguments.ssh_proxy_cmd, integration, flavor_metadata,
                image_metadata,
                arguments.use_keystone != ARG_NOT_SET,
                arguments.floating_ips != ARG_NOT_SET, log_level)
    else:
        logger.error('Environment file or external network not defined')
        exit(1)

    i = 0
    while i < int(arguments.num_runs):
        i += 1

        if concurrent_suite:
            logger.info('Running Concurrent Tests')
            concurrent_runner = unittest.TextTestRunner(verbosity=2)
            concurrent_suite = ConcurrentTestSuite(
                concurrent_suite, fork_for_tests(int(arguments.threads)))
            concurrent_results = concurrent_runner.run(concurrent_suite)
            __output_results(concurrent_results)

            if ((concurrent_results.errors
                    and len(concurrent_results.errors) > 0)
                    or (concurrent_results.failures
                        and len(concurrent_results.failures) > 0)):
                logger.error('See above for test failures')
                exit(1)
            else:
                logger.info(
                    'Concurrent tests completed successfully in run #%s', i)

        if sequential_suite:
            logger.info('Running Sequential Tests')
            sequential_runner = unittest.TextTestRunner(verbosity=2)
            sequential_results = sequential_runner.run(sequential_suite)
            __output_results(sequential_results)

            if ((sequential_results.errors
                    and len(sequential_results.errors) > 0)
                or (sequential_results.failures
                    and len(sequential_results.failures) > 0)):
                logger.error('See above for test failures')
                exit(1)
            else:
                logger.info(
                    'Sequential tests completed successfully in run #%s', i)

    logger.info('Successful completion of %s test runs', i)
    exit(0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-e', '--env', dest='env', required=True,
        help='OpenStack credentials file')
    parser.add_argument(
        '-n', '--net', dest='ext_net', required=True,
        help='External network name')
    parser.add_argument(
        '-p', '--proxy', dest='proxy', nargs='?', default=None,
        help='Optonal HTTP proxy socket (<host>:<port>)')
    parser.add_argument(
        '-s', '--ssh-proxy-cmd', dest='ssh_proxy_cmd', nargs='?', default=None,
        help='Optonal SSH proxy command value')
    parser.add_argument(
        '-l', '--log-level', dest='log_level', default='INFO',
        help='Logging Level (FATAL|CRITICAL|ERROR|WARN|INFO|DEBUG)')
    parser.add_argument(
        '-u', '--unit-tests', dest='include_unit', default=ARG_NOT_SET,
        nargs='?', help='When argument is set, all tests not requiring '
                        'OpenStack will be executed')
    parser.add_argument(
        '-c', '--connection-tests', dest='include_connection',
        default=ARG_NOT_SET, nargs='?',
        help='When argument is set, simple OpenStack connection tests will be '
             'executed')
    parser.add_argument(
        '-a', '--api-tests', dest='include_api', default=ARG_NOT_SET,
        nargs='?',
        help='When argument is set, OpenStack API tests will be executed')
    parser.add_argument(
        '-i', '--integration-tests', dest='include_integration',
        default=ARG_NOT_SET, nargs='?',
        help='When argument is set, OpenStack integrations tests will be '
             'executed')
    parser.add_argument(
        '-st', '--staging-tests', dest='include_staging', default=ARG_NOT_SET,
        nargs='?',
        help='When argument is set, OpenStack staging tests will be executed')
    parser.add_argument(
        '-f', '--floating-ips', dest='floating_ips', default=ARG_NOT_SET,
        nargs='?', help='When argument is set, all integration tests requiring'
                        ' Floating IPs will be executed')
    parser.add_argument(
        '-k', '--use-keystone', dest='use_keystone', default=ARG_NOT_SET,
        nargs='?',
        help='When argument is set, the tests will exercise the keystone APIs '
             'and must be run on a machine that has access to the admin '
             'network and is able to create users and groups')
    parser.add_argument(
        '-fm', '--flavor-meta', dest='flavor_metadata',
        help='JSON string to be used as flavor metadata for all test instances'
             ' created')
    parser.add_argument(
        '-im', '--image-meta', dest='image_metadata_file', default=None,
        help='Location of YAML file containing the image metadata')
    parser.add_argument(
        '-ci', '--continuous-integration', dest='continuous_integration',
        default=ARG_NOT_SET, nargs='?',
        help='When argument is set, OpenStack integrations tests will be '
             'executed')
    parser.add_argument(
        '-r', '--num-runs', dest='num_runs', default=1,
        help='Number of test runs to execute (default 1)')
    parser.add_argument(
        '-t', '--threads', dest='threads', default=4,
        help='Number of threads to execute the tests (default 4)')

    args = parser.parse_args()

    main(args)
