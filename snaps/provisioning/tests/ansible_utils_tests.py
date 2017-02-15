# Copyright (c) 2016 Cable Television Laboratories, Inc. ("CableLabs")
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

import os
import uuid

from snaps.openstack import create_instance
from snaps.openstack import create_keypairs
from snaps.openstack import create_network
from snaps.openstack import create_router
from snaps.openstack import create_image
from snaps.openstack import create_flavor
from scp import SCPClient

from snaps.provisioning import ansible_utils
from snaps.openstack.tests import openstack_tests
from snaps.openstack.tests.os_source_file_test import OSIntegrationTestCase

VM_BOOT_TIMEOUT = 600

ip_1 = '10.0.1.100'
ip_2 = '10.0.1.200'


class AnsibleProvisioningTests(OSIntegrationTestCase):
    """
    Test for the CreateInstance class with two NIC/Ports, eth0 with floating IP and eth1 w/o
    """

    def setUp(self):
        """
        Instantiates the CreateImage object that is responsible for downloading and creating an OS image file
        within OpenStack
        """
        super(self.__class__, self).__start__()

        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.keypair_priv_filepath = 'tmp/' + guid
        self.keypair_pub_filepath = self.keypair_priv_filepath + '.pub'
        self.keypair_name = guid + '-kp'
        self.vm_inst_name = guid + '-inst'
        self.test_file_local_path = 'tmp/' + guid + '-hello.txt'
        self.port_1_name = guid + '-port-1'
        self.port_2_name = guid + '-port-2'
        self.floating_ip_name = guid + 'fip1'

        # Setup members to cleanup just in case they don't get created
        self.inst_creator = None
        self.keypair_creator = None
        self.flavor_creator = None
        self.router_creator = None
        self.network_creator = None
        self.image_creator = None

        try:
            # Create Image
            os_image_settings = openstack_tests.ubuntu_url_image(name=guid + '-' + '-image')
            self.image_creator = create_image.OpenStackImage(self.os_creds, os_image_settings)
            self.image_creator.create()

            # First network is public
            self.pub_net_config = openstack_tests.get_pub_net_config(
                net_name=guid + '-pub-net', subnet_name=guid + '-pub-subnet',
                router_name=guid + '-pub-router', external_net=self.ext_net_name)

            self.network_creator = create_network.OpenStackNetwork(self.os_creds, self.pub_net_config.network_settings)
            self.network_creator.create()

            # Create routers
            self.router_creator = create_router.OpenStackRouter(self.os_creds, self.pub_net_config.router_settings)
            self.router_creator.create()

            # Create Flavor
            self.flavor_creator = create_flavor.OpenStackFlavor(
                self.admin_os_creds,
                create_flavor.FlavorSettings(name=guid + '-flavor-name', ram=2048, disk=10, vcpus=2))
            self.flavor_creator.create()

            # Create Key/Pair
            self.keypair_creator = create_keypairs.OpenStackKeypair(
                self.os_creds, create_keypairs.KeypairSettings(
                    name=self.keypair_name, public_filepath=self.keypair_pub_filepath,
                    private_filepath=self.keypair_priv_filepath))
            self.keypair_creator.create()

            # Create instance
            ports_settings = list()
            ports_settings.append(
                create_network.PortSettings(name=self.port_1_name,
                                            network_name=self.pub_net_config.network_settings.name))

            instance_settings = create_instance.VmInstanceSettings(
                name=self.vm_inst_name, flavor=self.flavor_creator.flavor_settings.name, port_settings=ports_settings,
                floating_ip_settings=[create_instance.FloatingIpSettings(
                    name=self.floating_ip_name, port_name=self.port_1_name,
                    router_name=self.pub_net_config.router_settings.name)])

            self.inst_creator = create_instance.OpenStackVmInstance(
                self.os_creds, instance_settings, self.image_creator.image_settings,
                keypair_settings=self.keypair_creator.keypair_settings)
        except Exception as e:
            self.tearDown()
            raise Exception(e.message)

    def tearDown(self):
        """
        Cleans the created objects
        """
        if self.inst_creator:
            self.inst_creator.clean()

        if self.keypair_creator:
            self.keypair_creator.clean()

        if self.flavor_creator:
            self.flavor_creator.clean()

        if os.path.isfile(self.keypair_pub_filepath):
            os.remove(self.keypair_pub_filepath)

        if os.path.isfile(self.keypair_priv_filepath):
            os.remove(self.keypair_priv_filepath)

        if self.router_creator:
            self.router_creator.clean()

        if self.network_creator:
            self.network_creator.clean()

        if self.image_creator:
            self.image_creator.clean()

        if os.path.isfile(self.test_file_local_path):
            os.remove(self.test_file_local_path)

        super(self.__class__, self).__clean__()

    def test_apply_simple_playbook(self):
        """
        Tests application of an Ansible playbook that simply copies over a file:
        1. Have a ~/.ansible.cfg (or alternate means) to set host_key_checking = False
        2. Set the following environment variable in your executing shell: ANSIBLE_HOST_KEY_CHECKING=False
        Should this not be performed, the creation of the host ssh key will cause your ansible calls to fail.
        """
        self.inst_creator.create(block=True)

        # Block until VM's ssh port has been opened
        self.assertTrue(self.inst_creator.vm_ssh_active(block=True))

        ssh_client = self.inst_creator.ssh_client()
        self.assertIsNotNone(ssh_client)
        out = ssh_client.exec_command('pwd')[1].channel.in_buffer.read(1024)
        self.assertIsNotNone(out)
        self.assertGreater(len(out), 1)

        # Need to use the first floating IP as subsequent ones are currently broken with Apex CO
        ip = self.inst_creator.get_floating_ip().ip
        user = self.inst_creator.get_image_user()
        priv_key = self.inst_creator.keypair_settings.private_filepath

        retval = ansible_utils.apply_playbook('provisioning/tests/playbooks/simple_playbook.yml', [ip], user, priv_key,
                                              proxy_setting=self.os_creds.proxy_settings)
        self.assertEquals(0, retval)

        ssh = ansible_utils.ssh_client(ip, user, priv_key, self.os_creds.proxy_settings)
        self.assertIsNotNone(ssh)
        scp = SCPClient(ssh.get_transport())
        scp.get('~/hello.txt', self.test_file_local_path)

        self.assertTrue(os.path.isfile(self.test_file_local_path))

        with open(self.test_file_local_path) as f:
            file_contents = f.readline()
            self.assertEquals('Hello World!', file_contents)

    def test_apply_template_playbook(self):
        """
        Tests application of an Ansible playbook that applies a template to a file:
        1. Have a ~/.ansible.cfg (or alternate means) to set host_key_checking = False
        2. Set the following environment variable in your executing shell: ANSIBLE_HOST_KEY_CHECKING=False
        Should this not be performed, the creation of the host ssh key will cause your ansible calls to fail.
        """
        self.inst_creator.create(block=True)

        # Block until VM's ssh port has been opened
        self.assertTrue(self.inst_creator.vm_ssh_active(block=True))

        # Need to use the first floating IP as subsequent ones are currently broken with Apex CO
        ip = self.inst_creator.get_floating_ip().ip
        user = self.inst_creator.get_image_user()
        priv_key = self.inst_creator.keypair_settings.private_filepath

        ansible_utils.apply_playbook('provisioning/tests/playbooks/template_playbook.yml', [ip], user, priv_key,
                                     variables={'name': 'Foo'}, proxy_setting=self.os_creds.proxy_settings)

        ssh = ansible_utils.ssh_client(ip, user, priv_key, self.os_creds.proxy_settings)
        self.assertIsNotNone(ssh)
        scp = SCPClient(ssh.get_transport())
        scp.get('/tmp/hello.txt', self.test_file_local_path)

        self.assertTrue(os.path.isfile(self.test_file_local_path))

        with open(self.test_file_local_path) as f:
            file_contents = f.readline()
            self.assertEquals('Hello Foo!', file_contents)
