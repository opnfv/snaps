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
from snaps.domain.project import Project, Domain, ComputeQuotas, NetworkQuotas


class ProjectDomainObjectTests(unittest.TestCase):
    """
    Tests the construction of the snaps.domain.project.Project class
    """

    def test_construction_positional_minimal(self):
        project = Project('foo', '123-456')
        self.assertEqual('foo', project.name)
        self.assertEqual('123-456', project.id)
        self.assertIsNone(project.domain_id)

    def test_construction_positional_all(self):
        project = Project('foo', '123-456', 'hello')
        self.assertEqual('foo', project.name)
        self.assertEqual('123-456', project.id)
        self.assertEqual('hello', project.domain_id)

    def test_construction_named_minimal(self):
        project = Project(project_id='123-456', name='foo')
        self.assertEqual('foo', project.name)
        self.assertEqual('123-456', project.id)
        self.assertIsNone(project.domain_id)

    def test_construction_named_all(self):
        project = Project(domain_id='hello', project_id='123-456', name='foo')
        self.assertEqual('foo', project.name)
        self.assertEqual('123-456', project.id)
        self.assertEqual('hello', project.domain_id)


class DomainDomainObjectTests(unittest.TestCase):
    """
    Tests the construction of the snaps.domain.project.Domain class
    """

    def test_construction_positional(self):
        domain = Domain('foo', '123-456')
        self.assertEqual('foo', domain.name)
        self.assertEqual('123-456', domain.id)

    def test_construction_named_minimal(self):
        domain = Domain(domain_id='123-456', name='foo')
        self.assertEqual('foo', domain.name)
        self.assertEqual('123-456', domain.id)


class ComputeQuotasDomainObjectTests(unittest.TestCase):
    """
    Tests the construction of the snaps.domain.project.ComputeQuotas class
    """

    def test_construction_positional(self):
        quotas = ComputeQuotas(
            metadata_items=64, cores=5, instances= 4, injected_files= 3,
            injected_file_content_bytes=5120,ram=25600, fixed_ips=100,
            key_pairs=50)
        self.assertEqual(64, quotas.metadata_items)
        self.assertEqual(5, quotas.cores)
        self.assertEqual(4, quotas.instances)
        self.assertEqual(3, quotas.injected_files)
        self.assertEqual(5120, quotas.injected_file_content_bytes)
        self.assertEqual(25600, quotas.ram)
        self.assertEqual(100, quotas.fixed_ips)
        self.assertEqual(50, quotas.key_pairs)

    def test_construction_named_minimal(self):
        quotas = ComputeQuotas(
            **{'metadata_items': 64, 'cores': 5, 'instances': 4,
               'injected_files': 3, 'injected_file_content_bytes': 5120,
               'ram': 25600, 'fixed_ips': 100, 'key_pairs': 50})
        self.assertEqual(64, quotas.metadata_items)
        self.assertEqual(5, quotas.cores)
        self.assertEqual(4, quotas.instances)
        self.assertEqual(3, quotas.injected_files)
        self.assertEqual(5120, quotas.injected_file_content_bytes)
        self.assertEqual(25600, quotas.ram)
        self.assertEqual(100, quotas.fixed_ips)
        self.assertEqual(50, quotas.key_pairs)


class NetworkQuotasDomainObjectTests(unittest.TestCase):
    """
    Tests the construction of the snaps.domain.project.NetworkQuotas class
    """

    def test_construction_positional(self):
        quotas = NetworkQuotas(
            security_group=5, security_group_rule=50,
            floatingip=25, network=5, port=25, router=6, subnet=7)
        self.assertEqual(5, quotas.security_group)
        self.assertEqual(50, quotas.security_group_rule)
        self.assertEqual(25, quotas.floatingip)
        self.assertEqual(5, quotas.network)
        self.assertEqual(25, quotas.port)
        self.assertEqual(6, quotas.router)
        self.assertEqual(7, quotas.subnet)

    def test_construction_named_minimal(self):
        quotas = NetworkQuotas(
            **{'security_group': 5, 'security_group_rule': 50,
               'floatingip': 25, 'network': 5, 'port': 25, 'router': 6,
               'subnet': 7})
        self.assertEqual(5, quotas.security_group)
        self.assertEqual(50, quotas.security_group_rule)
        self.assertEqual(25, quotas.floatingip)
        self.assertEqual(5, quotas.network)
        self.assertEqual(25, quotas.port)
        self.assertEqual(6, quotas.router)
        self.assertEqual(7, quotas.subnet)
