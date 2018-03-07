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
from snaps.domain.vm_inst import VmInst, FloatingIp


class VmInstDomainObjectTests(unittest.TestCase):
    """
    Tests the construction of the snaps.domain.test.Image class
    """

    def test_construction_positional(self):
        vm_inst = VmInst('name', 'id', '456', '123', list(), 'kp-name',
                         ['foo', 'bar'], ['123', '456'], 'host1', 'zone1')
        self.assertEqual('name', vm_inst.name)
        self.assertEqual('id', vm_inst.id)
        self.assertEqual('456', vm_inst.image_id)
        self.assertEqual('123', vm_inst.flavor_id)
        self.assertEqual(list(), vm_inst.ports)
        self.assertEqual('kp-name', vm_inst.keypair_name)
        self.assertEqual(['foo', 'bar'], vm_inst.sec_grp_names)
        self.assertEqual(['123', '456'], vm_inst.volume_ids)
        self.assertEqual('host1', vm_inst.compute_host)
        self.assertEqual('zone1', vm_inst.availability_zone)

    def test_construction_named(self):
        vm_inst = VmInst(
            availability_zone='zone1', compute_host='host1',
            volume_ids=['123', '456'], sec_grp_names=['foo', 'bar'],
            ports=list(), inst_id='id', name='name', flavor_id='123',
            image_id='456', keypair_name='kp-name')
        self.assertEqual('name', vm_inst.name)
        self.assertEqual('id', vm_inst.id)
        self.assertEqual('456', vm_inst.image_id)
        self.assertEqual('123', vm_inst.flavor_id)
        self.assertEqual(list(), vm_inst.ports)
        self.assertEqual('kp-name', vm_inst.keypair_name)
        self.assertEqual(['foo', 'bar'], vm_inst.sec_grp_names)
        self.assertEqual(['123', '456'], vm_inst.volume_ids)
        self.assertEqual('host1', vm_inst.compute_host)
        self.assertEqual('zone1', vm_inst.availability_zone)


class FloatingIpDomainObjectTests(unittest.TestCase):
    """
    Tests the construction of the snaps.domain.test.Image class
    """

    def test_construction_kwargs_ip_proj(self):
        kwargs = {'id': 'foo', 'description': 'bar', 'ip': '192.168.122.3',
                  'fixed_ip_address': '10.0.0.3',
                  'floating_network_id': 'id_of_net', 'port_id': 'id_of_port',
                  'router_id': 'id_of_router', 'project_id': 'id_of_proj'}
        vm_inst = FloatingIp(**kwargs)
        self.assertEqual('foo', vm_inst.id)
        self.assertEqual('bar', vm_inst.description)
        self.assertEqual('192.168.122.3', vm_inst.ip)
        self.assertEqual('10.0.0.3', vm_inst.fixed_ip_address)
        self.assertEqual('id_of_net', vm_inst.floating_network_id)
        self.assertEqual('id_of_port', vm_inst.port_id)
        self.assertEqual('id_of_router', vm_inst.router_id)
        self.assertEqual('id_of_proj', vm_inst.project_id)

    def test_construction_kwargs_fixed_ip_tenant(self):
        kwargs = {'id': 'foo', 'description': 'bar',
                  'floating_ip_address': '192.168.122.3',
                  'fixed_ip_address': '10.0.0.3',
                  'floating_network_id': 'id_of_net', 'port_id': 'id_of_port',
                  'router_id': 'id_of_router', 'tenant_id': 'id_of_proj'}
        vm_inst = FloatingIp(**kwargs)
        self.assertEqual('foo', vm_inst.id)
        self.assertEqual('bar', vm_inst.description)
        self.assertEqual('192.168.122.3', vm_inst.ip)
        self.assertEqual('10.0.0.3', vm_inst.fixed_ip_address)
        self.assertEqual('id_of_net', vm_inst.floating_network_id)
        self.assertEqual('id_of_port', vm_inst.port_id)
        self.assertEqual('id_of_router', vm_inst.router_id)
        self.assertEqual('id_of_proj', vm_inst.project_id)

    def test_construction_named_ip_proj(self):
        vm_inst = FloatingIp(
            id='foo', description='bar', ip='192.168.122.3',
            fixed_ip_address='10.0.0.3', floating_network_id='id_of_net',
            port_id='id_of_port', router_id='id_of_router',
            project_id='id_of_proj')
        self.assertEqual('foo', vm_inst.id)
        self.assertEqual('bar', vm_inst.description)
        self.assertEqual('192.168.122.3', vm_inst.ip)
        self.assertEqual('10.0.0.3', vm_inst.fixed_ip_address)
        self.assertEqual('id_of_net', vm_inst.floating_network_id)
        self.assertEqual('id_of_port', vm_inst.port_id)
        self.assertEqual('id_of_router', vm_inst.router_id)
        self.assertEqual('id_of_proj', vm_inst.project_id)

    def test_construction_kwargs_named_fixed_ip_tenant(self):
        vm_inst = FloatingIp(
            id='foo', description='bar', floating_ip_address='192.168.122.3',
            fixed_ip_address='10.0.0.3', floating_network_id='id_of_net',
            port_id='id_of_port', router_id='id_of_router',
            tenant_id='id_of_proj')
        self.assertEqual('foo', vm_inst.id)
        self.assertEqual('bar', vm_inst.description)
        self.assertEqual('192.168.122.3', vm_inst.ip)
        self.assertEqual('10.0.0.3', vm_inst.fixed_ip_address)
        self.assertEqual('id_of_net', vm_inst.floating_network_id)
        self.assertEqual('id_of_port', vm_inst.port_id)
        self.assertEqual('id_of_router', vm_inst.router_id)
        self.assertEqual('id_of_proj', vm_inst.project_id)
