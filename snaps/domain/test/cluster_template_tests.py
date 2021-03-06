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
    ContainerOrchestrationEngine, ServerType, DockerStorageDriver)
from snaps.domain.cluster_template import ClusterTemplate


class ClusterTemplateUnitTests(unittest.TestCase):
    """
    Tests the construction of the ClusterTypeConfig class
    """
    def test_all_named(self):
        labels = {'foo': 'bar'}
        config = ClusterTemplate(
            id='tmplt-id', name='foo', image='bar', keypair='keys',
            network_driver='driver', external_net='external',
            docker_volume_size=99, server_type=ServerType.baremetal.value,
            flavor='testFlavor', master_flavor='masterFlavor',
            coe=ContainerOrchestrationEngine.kubernetes.value,
            fixed_net='fixedNet', fixed_subnet='fixedSubnet',
            registry_enabled=False,
            docker_storage_driver=DockerStorageDriver.overlay.value,
            dns_nameserver='8.8.4.4', public=True, tls=False,
            http_proxy='http://foo:8080', https_proxy='https://foo:443',
            no_proxy='foo,bar', volume_driver='volDriver',
            master_lb_enabled=False, labels=labels)
        self.assertIsNotNone(config)
        self.assertEqual('tmplt-id', config.id)
        self.assertEqual('foo', config.name)
        self.assertEqual('bar', config.image)
        self.assertEqual('keys', config.keypair)
        self.assertEqual('driver', config.network_driver)
        self.assertEqual('external', config.external_net)
        self.assertEqual(99, config.docker_volume_size)
        self.assertEqual(ServerType.baremetal.value, config.server_type)
        self.assertEqual('testFlavor', config.flavor)
        self.assertEqual('masterFlavor', config.master_flavor)
        self.assertEqual(ContainerOrchestrationEngine.kubernetes.value,
                         config.coe)
        self.assertEqual('fixedNet', config.fixed_net)
        self.assertEqual('fixedSubnet', config.fixed_subnet)
        self.assertFalse(config.registry_enabled)
        self.assertEqual(DockerStorageDriver.overlay.value,
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
        config = ClusterTemplate(**{
            'id': 'tmplt-id', 'name': 'foo', 'image': 'bar', 'keypair': 'keys',
            'network_driver': 'driver', 'external_net': 'external',
            'docker_volume_size': '99', 'server_type': 'baremetal',
            'flavor': 'testFlavor', 'master_flavor': 'masterFlavor',
            'coe': 'kubernetes', 'fixed_net': 'fixedNet',
            'fixed_subnet': 'fixedSubnet', 'registry_enabled': False,
            'docker_storage_driver': 'overlay', 'dns_nameserver': '8.8.4.4',
            'public': 'true', 'tls': 'false', 'http_proxy': 'http://foo:8080',
            'https_proxy': 'https://foo:443', 'no_proxy': 'foo,bar',
            'volume_driver': 'volDriver', 'master_lb_enabled': False,
            'labels': labels})
        self.assertIsNotNone(config)
        self.assertEqual('tmplt-id', config.id)
        self.assertEqual('foo', config.name)
        self.assertEqual('bar', config.image)
        self.assertEqual('keys', config.keypair)
        self.assertEqual('driver', config.network_driver)
        self.assertEqual('external', config.external_net)
        self.assertEqual(99, config.docker_volume_size)
        self.assertEqual(ServerType.baremetal.value, config.server_type)
        self.assertEqual('testFlavor', config.flavor)
        self.assertEqual('masterFlavor', config.master_flavor)
        self.assertEqual(ContainerOrchestrationEngine.kubernetes.value,
                         config.coe)
        self.assertEqual('fixedNet', config.fixed_net)
        self.assertEqual('fixedSubnet', config.fixed_subnet)
        self.assertFalse(config.registry_enabled)
        self.assertEqual(DockerStorageDriver.overlay.value,
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
