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
import unittest

from snaps.config.network import PortConfig
from snaps.config.router import RouterConfig, RouterConfigError


class RouterConfigUnitTests(unittest.TestCase):
    """
    Class for testing the RouterConfig class
    """

    def test_no_params(self):
        with self.assertRaises(RouterConfigError):
            RouterConfig()

    def test_empty_config(self):
        with self.assertRaises(RouterConfigError):
            RouterConfig(**dict())

    def test_bad_internal_subnets_bad_key(self):
        with self.assertRaises(RouterConfigError):
            RouterConfig(name='foo', internal_subnets={'foo': 'bar'})

    def test_bad_internal_subnets_no_project(self):
        with self.assertRaises(RouterConfigError):
            RouterConfig(name='foo', internal_subnets={
                'subnet': {'subnet_name': 'bar', 'network_name': 'foo'}})

    def test_bad_internal_subnets_no_network(self):
        with self.assertRaises(RouterConfigError):
            RouterConfig(name='foo', internal_subnets={
                'subnet': {'subnet_name': 'bar', 'project_name': 'foo'}})

    def test_bad_internal_subnets_no_subnet(self):
        with self.assertRaises(RouterConfigError):
            RouterConfig(name='foo', internal_subnets={
                'subnet': {'project_name': 'bar', 'network_name': 'foo'}})

    def test_name_only(self):
        settings = RouterConfig(name='foo')
        self.assertEqual('foo', settings.name)
        self.assertIsNone(settings.project_name)
        self.assertIsNone(settings.external_gateway)
        self.assertTrue(settings.admin_state_up)
        self.assertIsNone(settings.enable_snat)
        self.assertIsNotNone(settings.internal_subnets)
        self.assertTrue(isinstance(settings.internal_subnets, list))
        self.assertEqual(0, len(settings.internal_subnets))
        self.assertIsNotNone(settings.port_settings)
        self.assertTrue(isinstance(settings.port_settings, list))
        self.assertEqual(0, len(settings.port_settings))

    def test_config_with_name_only(self):
        settings = RouterConfig(**{'name': 'foo'})
        self.assertEqual('foo', settings.name)
        self.assertIsNone(settings.project_name)
        self.assertIsNone(settings.external_gateway)
        self.assertTrue(settings.admin_state_up)
        self.assertIsNone(settings.enable_snat)
        self.assertIsNotNone(settings.internal_subnets)
        self.assertTrue(isinstance(settings.internal_subnets, list))
        self.assertEqual(0, len(settings.internal_subnets))
        self.assertIsNotNone(settings.port_settings)
        self.assertTrue(isinstance(settings.port_settings, list))
        self.assertEqual(0, len(settings.port_settings))

    def test_all_internal_subnets_str(self):
        port_settings = PortConfig(name='foo', network_name='bar')
        settings = RouterConfig(
            name='foo', project_name='bar', external_gateway='foo_gateway',
            admin_state_up=True, enable_snat=False,
            internal_subnets=['10.0.0.1/24'], interfaces=[port_settings])
        self.assertEqual('foo', settings.name)
        self.assertEqual('bar', settings.project_name)
        self.assertEqual('foo_gateway', settings.external_gateway)
        self.assertTrue(settings.admin_state_up)
        self.assertFalse(settings.enable_snat)
        self.assertIsNotNone(settings.internal_subnets)
        self.assertTrue(isinstance(settings.internal_subnets, list))
        self.assertEqual(1, len(settings.internal_subnets))
        self.assertEqual(['10.0.0.1/24'], settings.internal_subnets)
        self.assertEqual([port_settings], settings.port_settings)

    def test_all_internal_subnets_dict(self):
        port_settings = PortConfig(name='foo', network_name='bar')
        int_subs = {'subnet': {
            'project_name': 'proj_a', 'network_name': 'net_name',
            'subnet_name': 'sub_name'}}
        settings = RouterConfig(
            name='foo', project_name='bar', external_gateway='foo_gateway',
            admin_state_up=True, enable_snat=False,
            internal_subnets=int_subs,
            interfaces=[port_settings])
        self.assertEqual('foo', settings.name)
        self.assertEqual('bar', settings.project_name)
        self.assertEqual('foo_gateway', settings.external_gateway)
        self.assertTrue(settings.admin_state_up)
        self.assertFalse(settings.enable_snat)
        self.assertIsNotNone(settings.internal_subnets)
        self.assertTrue(isinstance(settings.internal_subnets, dict))
        self.assertEqual(1, len(settings.internal_subnets))
        self.assertEqual(int_subs, settings.internal_subnets)
        self.assertEqual([port_settings], settings.port_settings)

    def test_config_all_internal_subnets_str(self):
        int_subs = {'subnet': {
            'project_name': 'proj_a', 'network_name': 'net_name',
            'subnet_name': 'sub_name'}}
        settings = RouterConfig(
            **{'name': 'foo', 'project_name': 'bar',
               'external_gateway': 'foo_gateway', 'admin_state_up': True,
               'enable_snat': False,
               'internal_subnets': int_subs,
               'interfaces':
                   [{'port': {'name': 'foo-port',
                              'network_name': 'bar-net'}}]})
        self.assertEqual('foo', settings.name)
        self.assertEqual('bar', settings.project_name)
        self.assertEqual('foo_gateway', settings.external_gateway)
        self.assertTrue(settings.admin_state_up)
        self.assertFalse(settings.enable_snat)
        self.assertIsNotNone(settings.internal_subnets)
        self.assertTrue(isinstance(settings.internal_subnets, dict))
        self.assertEqual(1, len(settings.internal_subnets))
        self.assertEqual(int_subs, settings.internal_subnets)
        self.assertEqual([PortConfig(**{'name': 'foo-port',
                                        'network_name': 'bar-net'})],
                         settings.port_settings)
