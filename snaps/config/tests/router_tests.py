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

from snaps.config.router import RouterConfig, RouterConfigError
from snaps.openstack.create_network import PortSettings


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

    def test_all(self):
        port_settings = PortSettings(name='foo', network_name='bar')
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

    def test_config_all(self):
        settings = RouterConfig(
            **{'name': 'foo', 'project_name': 'bar',
               'external_gateway': 'foo_gateway', 'admin_state_up': True,
               'enable_snat': False, 'internal_subnets': ['10.0.0.1/24'],
               'interfaces':
                   [{'port': {'name': 'foo-port',
                              'network_name': 'bar-net'}}]})
        self.assertEqual('foo', settings.name)
        self.assertEqual('bar', settings.project_name)
        self.assertEqual('foo_gateway', settings.external_gateway)
        self.assertTrue(settings.admin_state_up)
        self.assertFalse(settings.enable_snat)
        self.assertIsNotNone(settings.internal_subnets)
        self.assertTrue(isinstance(settings.internal_subnets, list))
        self.assertEqual(1, len(settings.internal_subnets))
        self.assertEqual(['10.0.0.1/24'], settings.internal_subnets)
        self.assertEqual([PortSettings(**{'name': 'foo-port',
                                          'network_name': 'bar-net'})],
                         settings.port_settings)
