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

from snaps.config.cluster_template import (
    ClusterTemplateConfig, ClusterTemplateConfigError, ServerType,
    DockerStorageDriver, ContainerOrchestrationEngine)


class ClusterTemplateConfigUnitTests(unittest.TestCase):
    """
    Tests the construction of the ClusterTemplateConfig class
    """

    def test_no_params(self):
        with self.assertRaises(ClusterTemplateConfigError):
            ClusterTemplateConfig()

    def test_empty_config(self):
        with self.assertRaises(ClusterTemplateConfigError):
            ClusterTemplateConfig(config=dict())

    def test_name_only(self):
        with self.assertRaises(ClusterTemplateConfigError):
            ClusterTemplateConfig(name='foo')

    def test_minimal_named(self):
        config = ClusterTemplateConfig(
            name='foo', image='bar', keypair='keys', external_net='external')
        self.assertIsNotNone(config)
        self.assertEqual('foo', config.name)
        self.assertEqual('bar', config.image)
        self.assertEqual('keys', config.keypair)
        self.assertIsNone(config.network_driver)
        self.assertEqual('external', config.external_net)
        self.assertTrue(config.floating_ip_enabled)
        self.assertEqual(3, config.docker_volume_size)
        self.assertEqual(ServerType.vm, config.server_type)
        self.assertIsNone(config.flavor)
        self.assertIsNone(config.master_flavor)
        self.assertEqual(ContainerOrchestrationEngine.kubernetes, config.coe)
        self.assertIsNone(config.fixed_net)
        self.assertIsNone(config.fixed_subnet)
        self.assertTrue(config.registry_enabled)
        self.assertIsNone(config.insecure_registry)
        self.assertEqual(DockerStorageDriver.devicemapper,
                         config.docker_storage_driver)
        self.assertIsNone(config.dns_nameserver)
        self.assertFalse(config.public)
        self.assertFalse(config.tls_disabled)
        self.assertIsNone(config.http_proxy)
        self.assertIsNone(config.https_proxy)
        self.assertIsNone(config.no_proxy)
        self.assertIsNone(config.volume_driver)
        self.assertTrue(config.master_lb_enabled)
        self.assertIsNone(config.labels)

    def test_minimal_config(self):
        config = ClusterTemplateConfig(
            **{'name': 'foo', 'image': 'bar', 'keypair': 'keys',
               'external_net': 'external'})
        self.assertIsNotNone(config)
        self.assertEqual('foo', config.name)
        self.assertEqual('bar', config.image)
        self.assertEqual('keys', config.keypair)
        self.assertIsNone(config.network_driver)
        self.assertEqual('external', config.external_net)
        self.assertTrue(config.floating_ip_enabled)
        self.assertEqual(3, config.docker_volume_size)
        self.assertEqual(ServerType.vm, config.server_type)
        self.assertIsNone(config.flavor)
        self.assertIsNone(config.master_flavor)
        self.assertEqual(ContainerOrchestrationEngine.kubernetes, config.coe)
        self.assertIsNone(config.fixed_net)
        self.assertIsNone(config.fixed_subnet)
        self.assertTrue(config.registry_enabled)
        self.assertIsNone(config.insecure_registry)
        self.assertEqual(DockerStorageDriver.devicemapper,
                         config.docker_storage_driver)
        self.assertIsNone(config.dns_nameserver)
        self.assertFalse(config.public)
        self.assertFalse(config.tls_disabled)
        self.assertIsNone(config.http_proxy)
        self.assertIsNone(config.https_proxy)
        self.assertIsNone(config.no_proxy)
        self.assertIsNone(config.volume_driver)
        self.assertTrue(config.master_lb_enabled)
        self.assertIsNone(config.labels)

    def test_all_named(self):
        labels = {'foo': 'bar'}
        config = ClusterTemplateConfig(
            name='foo', image='bar', keypair='keys', network_driver='driver',
            external_net='external', docker_volume_size=99,
            server_type=ServerType.baremetal, flavor='testFlavor',
            master_flavor='masterFlavor',
            coe=ContainerOrchestrationEngine.kubernetes, fixed_net='fixedNet',
            fixed_subnet='fixedSubnet', registry_enabled=False,
            docker_storage_driver=DockerStorageDriver.overlay,
            dns_nameserver='8.8.4.4', public=True, tls=False,
            http_proxy='http://foo:8080', https_proxy='https://foo:443',
            no_proxy='foo,bar', volume_driver='volDriver',
            master_lb_enabled=False, labels=labels)
        self.assertIsNotNone(config)
        self.assertEqual('foo', config.name)
        self.assertEqual('bar', config.image)
        self.assertEqual('keys', config.keypair)
        self.assertEqual('driver', config.network_driver)
        self.assertEqual('external', config.external_net)
        self.assertEqual(99, config.docker_volume_size)
        self.assertEqual(ServerType.baremetal, config.server_type)
        self.assertEqual('testFlavor', config.flavor)
        self.assertEqual('masterFlavor', config.master_flavor)
        self.assertEqual(ContainerOrchestrationEngine.kubernetes, config.coe)
        self.assertEqual('fixedNet', config.fixed_net)
        self.assertEqual('fixedSubnet', config.fixed_subnet)
        self.assertFalse(config.registry_enabled)
        self.assertEqual(DockerStorageDriver.overlay,
                         config.docker_storage_driver)
        self.assertEqual('8.8.4.4', config.dns_nameserver)
        self.assertTrue(config.public)
        self.assertFalse(config.tls_disabled)
        self.assertEqual('http://foo:8080', config.http_proxy)
        self.assertEqual('https://foo:443', config.https_proxy)
        self.assertEqual('foo,bar', config.no_proxy)
        self.assertEqual('volDriver', config.volume_driver)
        self.assertFalse(config.master_lb_enabled)
        self.assertEqual(labels, config.labels)

    def test_all_config(self):
        labels = {'foo': 'bar'}
        config = ClusterTemplateConfig(**{
            'name': 'foo', 'image': 'bar', 'keypair': 'keys',
            'network_driver': 'driver', 'external_net': 'external',
            'docker_volume_size': '99', 'server_type': 'baremetal',
            'flavor': 'testFlavor', 'master_flavor': 'masterFlavor',
            'coe': 'kubernetes', 'fixed_net': 'fixedNet',
            'fixed_subnet': 'fixedSubnet', 'registry_enabled': 'false',
            'docker_storage_driver': 'overlay', 'dns_nameserver': '8.8.4.4',
            'public': 'true', 'tls': 'false', 'http_proxy': 'http://foo:8080',
            'https_proxy': 'https://foo:443', 'no_proxy': 'foo,bar',
            'volume_driver': 'volDriver', 'master_lb_enabled': 'false',
            'labels': labels})
        self.assertIsNotNone(config)
        self.assertEqual('foo', config.name)
        self.assertEqual('bar', config.image)
        self.assertEqual('keys', config.keypair)
        self.assertEqual('driver', config.network_driver)
        self.assertEqual('external', config.external_net)
        self.assertEqual(99, config.docker_volume_size)
        self.assertEqual(ServerType.baremetal, config.server_type)
        self.assertEqual('testFlavor', config.flavor)
        self.assertEqual('masterFlavor', config.master_flavor)
        self.assertEqual(ContainerOrchestrationEngine.kubernetes, config.coe)
        self.assertEqual('fixedNet', config.fixed_net)
        self.assertEqual('fixedSubnet', config.fixed_subnet)
        self.assertFalse(config.registry_enabled)
        self.assertEqual(DockerStorageDriver.overlay,
                         config.docker_storage_driver)
        self.assertEqual('8.8.4.4', config.dns_nameserver)
        self.assertTrue(config.public)
        self.assertFalse(config.tls_disabled)
        self.assertEqual('http://foo:8080', config.http_proxy)
        self.assertEqual('https://foo:443', config.https_proxy)
        self.assertEqual('foo,bar', config.no_proxy)
        self.assertEqual('volDriver', config.volume_driver)
        self.assertFalse(config.master_lb_enabled)
        self.assertEqual(labels, config.labels)
