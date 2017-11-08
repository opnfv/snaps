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
import unittest

from snaps.openstack.os_credentials import (
    OSCredsError, OSCreds, ProxySettings, ProxySettingsError)
from snaps.openstack.utils import cinder_utils

__author__ = 'spisarski'

logger = logging.getLogger('os_credentials_test')


class ProxySettingsUnitTests(unittest.TestCase):
    """
    Tests the construction of the ProxySettings class
    """

    def test_no_params(self):
        with self.assertRaises(ProxySettingsError):
            ProxySettings()

    def test_empty_kwargs(self):
        with self.assertRaises(ProxySettingsError):
            ProxySettings(**dict())

    def test_host_only(self):
        with self.assertRaises(ProxySettingsError):
            ProxySettings(host='foo')

    def test_host_only_kwargs(self):
        with self.assertRaises(ProxySettingsError):
            ProxySettings(**{'host': 'foo'})

    def test_port_only(self):
        with self.assertRaises(ProxySettingsError):
            ProxySettings(port=1234)

    def test_port_only_kwargs(self):
        with self.assertRaises(ProxySettingsError):
            ProxySettings(**{'port': 1234})

    def test_minimum(self):
        proxy_settings = ProxySettings(host='foo', port=1234)
        self.assertEqual('foo', proxy_settings.host)
        self.assertEqual('1234', proxy_settings.port)
        self.assertEqual('foo', proxy_settings.https_host)
        self.assertEqual('1234', proxy_settings.https_port)
        self.assertIsNone(proxy_settings.ssh_proxy_cmd)

    def test_minimum_kwargs(self):
        proxy_settings = ProxySettings(**{'host': 'foo', 'port': 1234})
        self.assertEqual('foo', proxy_settings.host)
        self.assertEqual('1234', proxy_settings.port)
        self.assertEqual('foo', proxy_settings.https_host)
        self.assertEqual('1234', proxy_settings.https_port)
        self.assertIsNone(proxy_settings.ssh_proxy_cmd)

    def test_all(self):
        proxy_settings = ProxySettings(
            host='foo', port=1234, https_host='bar', https_port=2345,
            ssh_proxy_cmd='proxy command')
        self.assertEqual('foo', proxy_settings.host)
        self.assertEqual('1234', proxy_settings.port)
        self.assertEqual('bar', proxy_settings.https_host)
        self.assertEqual('2345', proxy_settings.https_port)
        self.assertEqual('proxy command', proxy_settings.ssh_proxy_cmd)

    def test_all_kwargs(self):
        proxy_settings = ProxySettings(
            **{'host': 'foo', 'port': 1234, 'https_host': 'bar',
               'https_port': 2345, 'ssh_proxy_cmd': 'proxy command'})
        self.assertEqual('foo', proxy_settings.host)
        self.assertEqual('1234', proxy_settings.port)
        self.assertEqual('bar', proxy_settings.https_host)
        self.assertEqual('2345', proxy_settings.https_port)
        self.assertEqual('proxy command', proxy_settings.ssh_proxy_cmd)


class OSCredsUnitTests(unittest.TestCase):
    """
    Tests the construction of the OSCreds class
    """

    def test_no_params(self):
        with self.assertRaises(OSCredsError):
            OSCreds()

    def test_empty_kwargs(self):
        with self.assertRaises(OSCredsError):
            OSCreds(**dict())

    def test_username_only(self):
        with self.assertRaises(OSCredsError):
            OSCreds(username='foo')

    def test_username_only_kwargs(self):
        with self.assertRaises(OSCredsError):
            OSCreds(**{'username': 'foo'})

    def test_password_only(self):
        with self.assertRaises(OSCredsError):
            OSCreds(password='foo')

    def test_password_only_kwargs(self):
        with self.assertRaises(OSCredsError):
            OSCreds(**{'password': 'foo'})

    def test_auth_url_only(self):
        with self.assertRaises(OSCredsError):
            OSCreds(auth_url='foo')

    def test_auth_url_only_kwargs(self):
        with self.assertRaises(OSCredsError):
            OSCreds(**{'auth_url': 'foo'})

    def test_project_name_only(self):
        with self.assertRaises(OSCredsError):
            OSCreds(project_name='foo')

    def test_project_name_only_kwargs(self):
        with self.assertRaises(OSCredsError):
            OSCreds(**{'project_name': 'foo'})

    def test_minimal(self):
        os_creds = OSCreds(
            username='foo', password='bar', auth_url='http://foo.bar:5000/v2',
            project_name='hello')
        self.assertEqual('foo', os_creds.username)
        self.assertEqual('bar', os_creds.password)
        self.assertEqual('http://foo.bar:5000/v2.0', os_creds.auth_url)
        self.assertEqual('hello', os_creds.project_name)
        self.assertEqual(2, os_creds.identity_api_version)
        self.assertEqual(2, os_creds.image_api_version)
        self.assertEqual(2, os_creds.compute_api_version)
        self.assertEqual(1, os_creds.heat_api_version)
        self.assertEqual(cinder_utils.VERSION_2, os_creds.volume_api_version)
        self.assertEqual(1, os_creds.magnum_api_version)
        self.assertEqual('default', os_creds.user_domain_id)
        self.assertEqual('Default', os_creds.user_domain_name)
        self.assertEqual('default', os_creds.project_domain_id)
        self.assertEqual('Default', os_creds.project_domain_name)
        self.assertEqual('public', os_creds.interface)
        self.assertFalse(os_creds.cacert)
        self.assertIsNone(os_creds.proxy_settings)
        self.assertIsNone(os_creds.region_name)

    def test_minimal_kwargs(self):
        os_creds = OSCreds(**{'username': 'foo', 'password': 'bar',
                              'auth_url': 'http://foo.bar:5000/v2',
                              'project_name': 'hello'})
        self.assertEqual('foo', os_creds.username)
        self.assertEqual('bar', os_creds.password)
        self.assertEqual('http://foo.bar:5000/v2.0', os_creds.auth_url)
        self.assertEqual('hello', os_creds.project_name)
        self.assertEqual(2, os_creds.identity_api_version)
        self.assertEqual(2, os_creds.image_api_version)
        self.assertEqual(2, os_creds.compute_api_version)
        self.assertEqual(1, os_creds.heat_api_version)
        self.assertEqual(cinder_utils.VERSION_2, os_creds.volume_api_version)
        self.assertEqual(1, os_creds.magnum_api_version)
        self.assertEqual('default', os_creds.user_domain_id)
        self.assertEqual('Default', os_creds.user_domain_name)
        self.assertEqual('default', os_creds.project_domain_id)
        self.assertEqual('Default', os_creds.project_domain_name)
        self.assertEqual('public', os_creds.interface)
        self.assertFalse(os_creds.cacert)
        self.assertIsNone(os_creds.proxy_settings)
        self.assertIsNone(os_creds.region_name)

    def test_all_kwargs_versions_str(self):
        os_creds = OSCreds(
            **{'username': 'foo', 'password': 'bar',
               'auth_url': 'http://foo.bar:5000/v2', 'project_name': 'hello',
               'identity_api_version': '5', 'image_api_version': '6',
               'compute_api_version': '7', 'heat_api_version': '8.0',
               'volume_api_version': '9.5', 'magnum_api_version': '10.6',
               'cacert': 'true', 'region_name': 'test_region'})
        self.assertEqual('foo', os_creds.username)
        self.assertEqual('bar', os_creds.password)
        self.assertEqual('http://foo.bar:5000/v5', os_creds.auth_url)
        self.assertEqual('hello', os_creds.project_name)
        self.assertEqual(5, os_creds.identity_api_version)
        self.assertEqual(6, os_creds.image_api_version)
        self.assertEqual(7, os_creds.compute_api_version)
        self.assertEqual(8.0, os_creds.heat_api_version)
        self.assertEqual(9.5, os_creds.volume_api_version)
        self.assertEqual(10.6, os_creds.magnum_api_version)
        self.assertEqual('default', os_creds.user_domain_id)
        self.assertEqual('Default', os_creds.user_domain_name)
        self.assertEqual('default', os_creds.project_domain_id)
        self.assertEqual('Default', os_creds.project_domain_name)
        self.assertEqual('public', os_creds.interface)
        self.assertTrue(os_creds.cacert)
        self.assertIsNone(os_creds.proxy_settings)
        self.assertEqual('test_region', os_creds.region_name)

    def test_all_kwargs_versions_num(self):
        os_creds = OSCreds(
            **{'username': 'foo', 'password': 'bar',
               'auth_url': 'http://foo.bar:5000/v2', 'project_name': 'hello',
               'identity_api_version': 5, 'image_api_version': 6,
               'compute_api_version': 7, 'heat_api_version': 8.0,
               'volume_api_version': 9.5, 'magnum_api_version': 10.6,
               'cacert': True, 'region_name': 'test_region'})
        self.assertEqual('foo', os_creds.username)
        self.assertEqual('bar', os_creds.password)
        self.assertEqual('http://foo.bar:5000/v5', os_creds.auth_url)
        self.assertEqual('hello', os_creds.project_name)
        self.assertEqual(5, os_creds.identity_api_version)
        self.assertEqual(6, os_creds.image_api_version)
        self.assertEqual(7, os_creds.compute_api_version)
        self.assertEqual(8.0, os_creds.heat_api_version)
        self.assertEqual(9.5, os_creds.volume_api_version)
        self.assertEqual(10.6, os_creds.magnum_api_version)
        self.assertEqual('default', os_creds.user_domain_id)
        self.assertEqual('Default', os_creds.user_domain_name)
        self.assertEqual('default', os_creds.project_domain_id)
        self.assertEqual('Default', os_creds.project_domain_name)
        self.assertEqual('public', os_creds.interface)
        self.assertTrue(os_creds.cacert)
        self.assertIsNone(os_creds.proxy_settings)
        self.assertEqual('test_region', os_creds.region_name)

    def test_proxy_settings_obj(self):
        proxy_settings = ProxySettings(host='foo', port=1234)
        os_creds = OSCreds(
            username='foo', password='bar', auth_url='http://foo.bar:5000/',
            project_name='hello', proxy_settings=proxy_settings)
        self.assertEqual('foo', os_creds.username)
        self.assertEqual('bar', os_creds.password)
        self.assertEqual('http://foo.bar:5000/v2.0', os_creds.auth_url)
        self.assertEqual('hello', os_creds.project_name)
        self.assertEqual(2, os_creds.identity_api_version)
        self.assertEqual(2, os_creds.image_api_version)
        self.assertEqual(2, os_creds.compute_api_version)
        self.assertEqual(1, os_creds.heat_api_version)
        self.assertEqual(cinder_utils.VERSION_2, os_creds.volume_api_version)
        self.assertEqual(1, os_creds.magnum_api_version)
        self.assertEqual('default', os_creds.user_domain_id)
        self.assertEqual('Default', os_creds.user_domain_name)
        self.assertEqual('default', os_creds.project_domain_id)
        self.assertEqual('Default', os_creds.project_domain_name)
        self.assertEqual('public', os_creds.interface)
        self.assertFalse(os_creds.cacert)
        self.assertEqual('foo', os_creds.proxy_settings.host)
        self.assertEqual('1234', os_creds.proxy_settings.port)
        self.assertIsNone(os_creds.proxy_settings.ssh_proxy_cmd)
        self.assertIsNone(os_creds.region_name)

    def test_proxy_settings_obj_kwargs(self):
        proxy_settings = ProxySettings(host='foo', port=1234)
        os_creds = OSCreds(
            **{'username': 'foo', 'password': 'bar',
               'auth_url': 'http://foo.bar:5000/v2', 'project_name': 'hello',
               'proxy_settings': proxy_settings, 'region_name': 'test_region',
               'user_domain_id': 'domain1', 'user_domain_name': 'domain2',
               'project_domain_id': 'domain3',
               'project_domain_name': 'domain4'})
        self.assertEqual('foo', os_creds.username)
        self.assertEqual('bar', os_creds.password)
        self.assertEqual('http://foo.bar:5000/v2.0', os_creds.auth_url)
        self.assertEqual('hello', os_creds.project_name)
        self.assertEqual(2, os_creds.identity_api_version)
        self.assertEqual(2, os_creds.image_api_version)
        self.assertEqual(2, os_creds.compute_api_version)
        self.assertEqual(1, os_creds.heat_api_version)
        self.assertEqual(cinder_utils.VERSION_2, os_creds.volume_api_version)
        self.assertEqual(1, os_creds.magnum_api_version)
        self.assertEqual('domain1', os_creds.user_domain_id)
        self.assertEqual('domain2', os_creds.user_domain_name)
        self.assertEqual('domain3', os_creds.project_domain_id)
        self.assertEqual('domain4', os_creds.project_domain_name)
        self.assertEqual('public', os_creds.interface)
        self.assertFalse(os_creds.cacert)
        self.assertEqual('foo', os_creds.proxy_settings.host)
        self.assertEqual('1234', os_creds.proxy_settings.port)
        self.assertIsNone(os_creds.proxy_settings.ssh_proxy_cmd)
        self.assertEqual('test_region', os_creds.region_name)

    def test_proxy_settings_dict(self):
        os_creds = OSCreds(
            username='foo', password='bar', auth_url='http://foo.bar:5000/v2',
            project_name='hello', proxy_settings={'host': 'foo', 'port': 1234},
            user_domain_id='domain1', user_domain_name='domain2',
            project_domain_id='domain3', project_domain_name='domain4')
        self.assertEqual('foo', os_creds.username)
        self.assertEqual('bar', os_creds.password)
        self.assertEqual('http://foo.bar:5000/v2.0', os_creds.auth_url)
        self.assertEqual('hello', os_creds.project_name)
        self.assertEqual(2, os_creds.identity_api_version)
        self.assertEqual(2, os_creds.image_api_version)
        self.assertEqual(2, os_creds.compute_api_version)
        self.assertEqual(1, os_creds.heat_api_version)
        self.assertEqual(cinder_utils.VERSION_2, os_creds.volume_api_version)
        self.assertEqual(1, os_creds.magnum_api_version)
        self.assertEqual('domain1', os_creds.user_domain_id)
        self.assertEqual('domain2', os_creds.user_domain_name)
        self.assertEqual('domain3', os_creds.project_domain_id)
        self.assertEqual('domain4', os_creds.project_domain_name)
        self.assertEqual('public', os_creds.interface)
        self.assertFalse(os_creds.cacert)
        self.assertEqual('foo', os_creds.proxy_settings.host)
        self.assertEqual('1234', os_creds.proxy_settings.port)
        self.assertIsNone(os_creds.proxy_settings.ssh_proxy_cmd)

    def test_proxy_settings_dict_kwargs(self):
        os_creds = OSCreds(
            **{'username': 'foo', 'password': 'bar',
               'auth_url': 'http://foo.bar:5000/v2', 'project_name': 'hello',
               'proxy_settings': {'host': 'foo', 'port': 1234},
               'region_name': 'test_region'})
        self.assertEqual('foo', os_creds.username)
        self.assertEqual('bar', os_creds.password)
        self.assertEqual('http://foo.bar:5000/v2.0', os_creds.auth_url)
        self.assertEqual('hello', os_creds.project_name)
        self.assertEqual(2, os_creds.identity_api_version)
        self.assertEqual(2, os_creds.image_api_version)
        self.assertEqual(2, os_creds.compute_api_version)
        self.assertEqual(1, os_creds.heat_api_version)
        self.assertEqual(cinder_utils.VERSION_2, os_creds.volume_api_version)
        self.assertEqual(1, os_creds.magnum_api_version)
        self.assertEqual('default', os_creds.user_domain_id)
        self.assertEqual('Default', os_creds.user_domain_name)
        self.assertEqual('default', os_creds.project_domain_id)
        self.assertEqual('Default', os_creds.project_domain_name)
        self.assertEqual('public', os_creds.interface)
        self.assertFalse(os_creds.cacert)
        self.assertEqual('foo', os_creds.proxy_settings.host)
        self.assertEqual('1234', os_creds.proxy_settings.port)
        self.assertIsNone(os_creds.proxy_settings.ssh_proxy_cmd)
        self.assertEqual('test_region', os_creds.region_name)
