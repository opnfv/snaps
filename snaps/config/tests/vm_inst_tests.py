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
from snaps.config.vm_inst import (
    FloatingIpConfig, VmInstanceConfig, FloatingIpConfigError,
    VmInstanceConfigError)


class VmInstanceConfigUnitTests(unittest.TestCase):
    """
    Tests the construction of the VmInstanceConfig class
    """

    def test_no_params(self):
        with self.assertRaises(VmInstanceConfigError):
            VmInstanceConfig()

    def test_empty_config(self):
        with self.assertRaises(VmInstanceConfigError):
            VmInstanceConfig(config=dict())

    def test_name_only(self):
        with self.assertRaises(VmInstanceConfigError):
            VmInstanceConfig(name='foo')

    def test_config_with_name_only(self):
        with self.assertRaises(VmInstanceConfigError):
            VmInstanceConfig(config={'name': 'foo'})

    def test_name_flavor_only(self):
        with self.assertRaises(VmInstanceConfigError):
            VmInstanceConfig(name='foo', flavor='bar')

    def test_config_with_name_flavor_only(self):
        with self.assertRaises(VmInstanceConfigError):
            VmInstanceConfig(config={'name': 'foo', 'flavor': 'bar'})

    def test_name_flavor_port_only(self):
        port_settings = PortConfig(name='foo-port', network_name='bar-net')
        settings = VmInstanceConfig(name='foo', flavor='bar',
                                    port_settings=[port_settings])
        self.assertEqual('foo', settings.name)
        self.assertEqual('bar', settings.flavor)
        self.assertEqual(1, len(settings.port_settings))
        self.assertEqual('foo-port', settings.port_settings[0].name)
        self.assertEqual('bar-net', settings.port_settings[0].network_name)
        self.assertEqual(0, len(settings.security_group_names))
        self.assertEqual(0, len(settings.floating_ip_settings))
        self.assertIsNone(settings.sudo_user)
        self.assertEqual(900, settings.vm_boot_timeout)
        self.assertEqual(300, settings.vm_delete_timeout)
        self.assertEqual(180, settings.ssh_connect_timeout)
        self.assertEqual(300, settings.cloud_init_timeout)
        self.assertIsNone(settings.availability_zone)
        self.assertIsNone(settings.volume_names)

    def test_config_with_name_flavor_port_only(self):
        port_settings = PortConfig(name='foo-port', network_name='bar-net')
        settings = VmInstanceConfig(
            **{'name': 'foo', 'flavor': 'bar', 'ports': [port_settings]})
        self.assertEqual('foo', settings.name)
        self.assertEqual('bar', settings.flavor)
        self.assertEqual(1, len(settings.port_settings))
        self.assertEqual('foo-port', settings.port_settings[0].name)
        self.assertEqual('bar-net', settings.port_settings[0].network_name)
        self.assertEqual(0, len(settings.security_group_names))
        self.assertEqual(0, len(settings.floating_ip_settings))
        self.assertIsNone(settings.sudo_user)
        self.assertEqual(900, settings.vm_boot_timeout)
        self.assertEqual(300, settings.vm_delete_timeout)
        self.assertEqual(180, settings.ssh_connect_timeout)
        self.assertEqual(300, settings.cloud_init_timeout)
        self.assertIsNone(settings.availability_zone)
        self.assertIsNone(settings.volume_names)

    def test_all(self):
        port_settings = PortConfig(name='foo-port', network_name='bar-net')
        fip_settings = FloatingIpConfig(name='foo-fip', port_name='bar-port',
                                        router_name='foo-bar-router')

        settings = VmInstanceConfig(
            name='foo', flavor='bar', port_settings=[port_settings],
            security_group_names=['sec_grp_1'],
            floating_ip_settings=[fip_settings], sudo_user='joe',
            vm_boot_timeout=999, vm_delete_timeout=333,
            ssh_connect_timeout=111, cloud_init_timeout=998,
            availability_zone='server name', volume_names=['vol1'])
        self.assertEqual('foo', settings.name)
        self.assertEqual('bar', settings.flavor)
        self.assertEqual(1, len(settings.port_settings))
        self.assertEqual('foo-port', settings.port_settings[0].name)
        self.assertEqual('bar-net', settings.port_settings[0].network_name)
        self.assertEqual(1, len(settings.security_group_names))
        self.assertEqual('sec_grp_1', settings.security_group_names[0])
        self.assertEqual(1, len(settings.floating_ip_settings))
        self.assertEqual('foo-fip', settings.floating_ip_settings[0].name)
        self.assertEqual('bar-port',
                         settings.floating_ip_settings[0].port_name)
        self.assertEqual('foo-bar-router',
                         settings.floating_ip_settings[0].router_name)
        self.assertEqual('joe', settings.sudo_user)
        self.assertEqual(999, settings.vm_boot_timeout)
        self.assertEqual(333, settings.vm_delete_timeout)
        self.assertEqual(111, settings.ssh_connect_timeout)
        self.assertEqual(998, settings.cloud_init_timeout)
        self.assertEqual('server name', settings.availability_zone)
        self.assertEqual('vol1', settings.volume_names[0])

    def test_config_all(self):
        port_settings = PortConfig(name='foo-port', network_name='bar-net')
        fip_settings = FloatingIpConfig(name='foo-fip', port_name='bar-port',
                                        router_name='foo-bar-router')

        settings = VmInstanceConfig(
            **{'name': 'foo', 'flavor': 'bar', 'ports': [port_settings],
               'security_group_names': ['sec_grp_1'],
               'floating_ips': [fip_settings], 'sudo_user': 'joe',
               'vm_boot_timeout': 999, 'vm_delete_timeout': 333,
               'ssh_connect_timeout': 111, 'cloud_init_timeout': 998,
               'availability_zone': 'server name', 'volume_names': ['vol2']})
        self.assertEqual('foo', settings.name)
        self.assertEqual('bar', settings.flavor)
        self.assertEqual(1, len(settings.port_settings))
        self.assertEqual('foo-port', settings.port_settings[0].name)
        self.assertEqual('bar-net', settings.port_settings[0].network_name)
        self.assertEqual(1, len(settings.security_group_names))
        self.assertEqual(1, len(settings.floating_ip_settings))
        self.assertEqual('foo-fip', settings.floating_ip_settings[0].name)
        self.assertEqual('bar-port',
                         settings.floating_ip_settings[0].port_name)
        self.assertEqual('foo-bar-router',
                         settings.floating_ip_settings[0].router_name)
        self.assertEqual('joe', settings.sudo_user)
        self.assertEqual(999, settings.vm_boot_timeout)
        self.assertEqual(333, settings.vm_delete_timeout)
        self.assertEqual(111, settings.ssh_connect_timeout)
        self.assertEqual(998, settings.cloud_init_timeout)
        self.assertEqual('server name', settings.availability_zone)
        self.assertEqual('vol2', settings.volume_names[0])


class FloatingIpConfigUnitTests(unittest.TestCase):
    """
    Tests the construction of the FloatingIpConfig class
    """

    def test_no_params(self):
        with self.assertRaises(FloatingIpConfigError):
            FloatingIpConfig()

    def test_empty_config(self):
        with self.assertRaises(FloatingIpConfigError):
            FloatingIpConfig(**dict())

    def test_name_only(self):
        with self.assertRaises(FloatingIpConfigError):
            FloatingIpConfig(name='foo')

    def test_config_with_name_only(self):
        with self.assertRaises(FloatingIpConfigError):
            FloatingIpConfig(**{'name': 'foo'})

    def test_name_port_only(self):
        with self.assertRaises(FloatingIpConfigError):
            FloatingIpConfig(name='foo', port_name='bar')

    def test_config_with_name_port_only(self):
        with self.assertRaises(FloatingIpConfigError):
            FloatingIpConfig(**{'name': 'foo', 'port_name': 'bar'})

    def test_name_router_only(self):
        with self.assertRaises(FloatingIpConfigError):
            FloatingIpConfig(name='foo', router_name='bar')

    def test_config_with_name_router_only(self):
        with self.assertRaises(FloatingIpConfigError):
            FloatingIpConfig(**{'name': 'foo', 'router_name': 'bar'})

    def test_name_port_router_name_only(self):
        settings = FloatingIpConfig(name='foo', port_name='foo-port',
                                    router_name='bar-router')
        self.assertEqual('foo', settings.name)
        self.assertEqual('foo-port', settings.port_name)
        self.assertIsNone(settings.port_id)
        self.assertEqual('bar-router', settings.router_name)
        self.assertIsNone(settings.subnet_name)
        self.assertTrue(settings.provisioning)

    def test_name_port_router_id_only(self):
        settings = FloatingIpConfig(name='foo', port_id='foo-port',
                                    router_name='bar-router')
        self.assertEqual('foo', settings.name)
        self.assertEqual('foo-port', settings.port_id)
        self.assertIsNone(settings.port_name)
        self.assertEqual('bar-router', settings.router_name)
        self.assertIsNone(settings.subnet_name)
        self.assertTrue(settings.provisioning)

    def test_config_with_name_port_router_only(self):
        settings = FloatingIpConfig(
            **{'name': 'foo', 'port_name': 'foo-port',
               'router_name': 'bar-router'})
        self.assertEqual('foo', settings.name)
        self.assertEqual('foo-port', settings.port_name)
        self.assertIsNone(settings.port_id)
        self.assertEqual('bar-router', settings.router_name)
        self.assertIsNone(settings.subnet_name)
        self.assertTrue(settings.provisioning)

    def test_all(self):
        settings = FloatingIpConfig(name='foo', port_name='foo-port',
                                    router_name='bar-router',
                                    subnet_name='bar-subnet',
                                    provisioning=False)
        self.assertEqual('foo', settings.name)
        self.assertEqual('foo-port', settings.port_name)
        self.assertIsNone(settings.port_id)
        self.assertEqual('bar-router', settings.router_name)
        self.assertEqual('bar-subnet', settings.subnet_name)
        self.assertFalse(settings.provisioning)

    def test_config_all(self):
        settings = FloatingIpConfig(
            **{'name': 'foo', 'port_name': 'foo-port',
               'router_name': 'bar-router', 'subnet_name': 'bar-subnet',
               'provisioning': False})
        self.assertEqual('foo', settings.name)
        self.assertEqual('foo-port', settings.port_name)
        self.assertIsNone(settings.port_id)
        self.assertEqual('bar-router', settings.router_name)
        self.assertEqual('bar-subnet', settings.subnet_name)
        self.assertFalse(settings.provisioning)
