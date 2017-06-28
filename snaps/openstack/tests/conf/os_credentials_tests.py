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
        self.assertEqual(str(1234), proxy_settings.port)
        self.assertIsNone(proxy_settings.ssh_proxy_cmd)

    def test_minimum_kwargs(self):
        proxy_settings = ProxySettings(**{'host': 'foo', 'port': 1234})
        self.assertEqual('foo', proxy_settings.host)
        self.assertEqual(str(1234), proxy_settings.port)
        self.assertIsNone(proxy_settings.ssh_proxy_cmd)

    def test_all(self):
        proxy_settings = ProxySettings(host='foo', port='1234',
                                       ssh_proxy_cmd='proxy command')
        self.assertEqual('foo', proxy_settings.host)
        self.assertEqual(str(1234), proxy_settings.port)
        self.assertEqual('proxy command', proxy_settings.ssh_proxy_cmd)

    def test_all_kwargs(self):
        proxy_settings = ProxySettings(
            **{'host': 'foo', 'port': str(1234), 'ssh_proxy_cmd': 'proxy command'})
        self.assertEqual('foo', proxy_settings.host)
        self.assertEqual(str(1234), proxy_settings.port)
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

    def test_invalid_auth_url(self):
        with self.assertRaises(OSCredsError):
            OSCreds(username='foo', password='bar',
                    auth_url='http://foo.bar', project_name='hello')

    def test_invalid_auth_url_kwargs(self):
        with self.assertRaises(OSCredsError):
            OSCreds(**{'username': 'foo', 'password': 'bar',
                    'auth_url': 'http://foo.bar', 'project_name': 'hello'})

    def test_minimal(self):
        os_creds = OSCreds(
            username='foo', password='bar', auth_url='http://foo.bar:5000/v2',
            project_name='hello')
        self.assertEqual('foo', os_creds.username)
        self.assertEqual('bar', os_creds.password)
        self.assertEqual('http://foo.bar:5000/v2', os_creds.auth_url)
        self.assertEqual('hello', os_creds.project_name)
        self.assertIsNone(os_creds.proxy_settings)

    def test_minimal_kwargs(self):
        os_creds = OSCreds(**{'username': 'foo', 'password': 'bar',
                              'auth_url': 'http://foo.bar:5000/v2',
                              'project_name': 'hello'})
        self.assertEqual('foo', os_creds.username)
        self.assertEqual('bar', os_creds.password)
        self.assertEqual('http://foo.bar:5000/v2', os_creds.auth_url)
        self.assertEqual('hello', os_creds.project_name)
        self.assertIsNone(os_creds.proxy_settings)

    def test_proxy_settings_obj(self):
        proxy_settings = ProxySettings(host='foo', port=1234)
        os_creds = OSCreds(
            username='foo', password='bar', auth_url='http://foo.bar:5000/v2',
            project_name='hello', proxy_settings=proxy_settings)
        self.assertEqual('foo', os_creds.username)
        self.assertEqual('bar', os_creds.password)
        self.assertEqual('http://foo.bar:5000/v2', os_creds.auth_url)
        self.assertEqual('hello', os_creds.project_name)
        self.assertEqual('foo', os_creds.proxy_settings.host)
        self.assertEqual(str(1234), os_creds.proxy_settings.port)
        self.assertIsNone(os_creds.proxy_settings.ssh_proxy_cmd)

    def test_proxy_settings_obj_kwargs(self):
        proxy_settings = ProxySettings(host='foo', port=1234)
        os_creds = OSCreds(**{'username': 'foo', 'password': 'bar',
                              'auth_url': 'http://foo.bar:5000/v2',
                              'project_name': 'hello',
                              'proxy_settings': proxy_settings})
        self.assertEqual('foo', os_creds.username)
        self.assertEqual('bar', os_creds.password)
        self.assertEqual('http://foo.bar:5000/v2', os_creds.auth_url)
        self.assertEqual('hello', os_creds.project_name)
        self.assertEqual('foo', os_creds.proxy_settings.host)
        self.assertEqual(str(1234), os_creds.proxy_settings.port)
        self.assertIsNone(os_creds.proxy_settings.ssh_proxy_cmd)

    def test_proxy_settings_dict(self):
        os_creds = OSCreds(
            username='foo', password='bar', auth_url='http://foo.bar:5000/v2',
            project_name='hello', proxy_settings={'host': 'foo',
                                                  'port': '1234'})
        self.assertEqual('foo', os_creds.username)
        self.assertEqual('bar', os_creds.password)
        self.assertEqual('http://foo.bar:5000/v2', os_creds.auth_url)
        self.assertEqual('hello', os_creds.project_name)
        self.assertEqual('foo', os_creds.proxy_settings.host)
        self.assertEqual(str(1234), os_creds.proxy_settings.port)
        self.assertIsNone(os_creds.proxy_settings.ssh_proxy_cmd)

    def test_proxy_settings_dict_kwargs(self):
        os_creds = OSCreds(**{'username': 'foo', 'password': 'bar',
                              'auth_url': 'http://foo.bar:5000/v2',
                              'project_name': 'hello',
                              'proxy_settings': {'host': 'foo',
                                                 'port': str(1234)}})
        self.assertEqual('foo', os_creds.username)
        self.assertEqual('bar', os_creds.password)
        self.assertEqual('http://foo.bar:5000/v2', os_creds.auth_url)
        self.assertEqual('hello', os_creds.project_name)
        self.assertEqual('foo', os_creds.proxy_settings.host)
        self.assertEqual(str(1234), os_creds.proxy_settings.port)
        self.assertIsNone(os_creds.proxy_settings.ssh_proxy_cmd)
