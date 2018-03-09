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
import uuid

from magnumclient.common.apiclient.exceptions import BadRequest

from snaps.config.cluster_template import (
    ClusterTemplateConfig, ServerType,  ContainerOrchestrationEngine,
    DockerStorageDriver)
from snaps.config.flavor import FlavorConfig
from snaps.config.keypair import KeypairConfig
from snaps.openstack.create_flavor import OpenStackFlavor
from snaps.openstack.create_image import OpenStackImage
from snaps.openstack.create_keypairs import OpenStackKeypair
from snaps.openstack.os_credentials import OSCreds
from snaps.openstack.tests import openstack_tests
from snaps.openstack.tests.os_source_file_test import OSComponentTestCase
from snaps.openstack.utils import magnum_utils

__author__ = 'spisarski'

logger = logging.getLogger('magnum_utils_tests')


class MagnumSmokeTests(OSComponentTestCase):
    """
    Tests to ensure that the magnum client can communicate with the cloud
    """

    def test_connect_success(self):
        """
        Tests to ensure that the proper credentials can connect.
        """
        magnum = magnum_utils.magnum_client(
            self.os_creds, self.os_session)

        # This should not throw an exception
        self.assertIsNotNone(magnum.clusters.list())

    def test_nova_connect_fail(self):
        """
        Tests to ensure that the improper credentials cannot connect.
        """

        with self.assertRaises(RuntimeError):
            magnum_utils.magnum_client(
                OSCreds(username='user', password='pass',
                        auth_url=self.os_creds.auth_url,
                        project_name=self.os_creds.project_name,
                        proxy_settings=self.os_creds.proxy_settings))


class MagnumUtilsClusterTypeTests(OSComponentTestCase):
    """
    Tests individual functions within magnum_utils.py
    """

    def setUp(self):
        self.guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.cluster_type_name = self.guid + '-cluster-type'
        self.magnum = magnum_utils.magnum_client(
            self.os_creds, self.os_session)

        metadata = self.image_metadata
        if not metadata:
            metadata = dict()
        if 'extra_properties' not in metadata:
            metadata['extra_properties'] = dict()
        metadata['extra_properties']['os_distro'] = 'cirros'

        os_image_settings = openstack_tests.cirros_image_settings(
            name=self.guid + '-image', image_metadata=metadata)

        self.image_creator = OpenStackImage(self.os_creds, os_image_settings)

        self.flavor_creator = OpenStackFlavor(
            self.os_creds, FlavorConfig(
                name=self.guid + '-flavor', ram=512, disk=10, vcpus=1))

        keypair_priv_filepath = 'tmp/' + self.guid
        keypair_pub_filepath = keypair_priv_filepath + '.pub'

        self.keypair_creator = OpenStackKeypair(
            self.os_creds, KeypairConfig(
                name=self.guid + '-keypair',
                public_filepath=keypair_pub_filepath,
                private_filepath=keypair_priv_filepath))

        self.cluster_template = None

        try:
            self.image_creator.create()
            self.flavor_creator.create()
            self.keypair_creator.create()
        except:
            self.tearDown()
            raise

    def tearDown(self):
        if self.cluster_template:
            try:
                magnum_utils.delete_cluster_template(
                    self.magnum, self.cluster_template.id)
            except:
                pass
        if self.keypair_creator:
            try:
                self.keypair_creator.clean()
            except:
                pass
        if self.flavor_creator:
            try:
                self.flavor_creator.clean()
            except:
                pass
        if self.image_creator:
            try:
                self.image_creator.clean()
            except:
                pass

        super(self.__class__, self).__clean__()

    def test_create_cluster_template_simple(self):
        config = ClusterTemplateConfig(
            name=self.cluster_type_name,
            image=self.image_creator.image_settings.name,
            keypair=self.keypair_creator.keypair_settings.name,
            external_net=self.ext_net_name,
            flavor=self.flavor_creator.flavor_settings.name)

        self.cluster_template = magnum_utils.create_cluster_template(
            self.magnum, config)
        self.assertIsNotNone(self.cluster_template)
        self.assertTrue(
            validate_cluster_template(config, self.cluster_template))

        template_by_name = magnum_utils.get_cluster_template(
            self.magnum, template_name=config.name)
        self.assertEqual(self.cluster_template, template_by_name)
        template_by_id = magnum_utils.get_cluster_template_by_id(
            self.magnum, self.cluster_template.id)
        self.assertEqual(self.cluster_template, template_by_id)

    def test_create_cluster_template_all(self):
        config = ClusterTemplateConfig(
            name=self.cluster_type_name,
            image=self.image_creator.image_settings.name,
            keypair=self.keypair_creator.keypair_settings.name,
            network_driver='flannel', external_net=self.ext_net_name,
            floating_ip_enabled=True, docker_volume_size=100,
            server_type=ServerType.vm,
            flavor=self.flavor_creator.flavor_settings.name,
            master_flavor=self.flavor_creator.flavor_settings.name,
            coe=ContainerOrchestrationEngine.kubernetes,
            fixed_net='foo', fixed_subnet='bar',
            registry_enabled=True, insecure_registry='localhost',
            docker_storage_driver=DockerStorageDriver.overlay,
            dns_nameserver='8.8.4.4', public=True, tls_disabled=True,
            http_proxy=None, https_proxy=None, volume_driver='cinder',
            master_lb_enabled=False, labels={'foo': 'bar'})

        self.cluster_template = magnum_utils.create_cluster_template(
            self.magnum, config)
        self.assertIsNotNone(self.cluster_template)
        self.assertTrue(
            validate_cluster_template(config, self.cluster_template))

        template_by_name = magnum_utils.get_cluster_template(
            self.magnum, template_name=config.name)
        self.assertEqual(self.cluster_template, template_by_name)
        template_by_id = magnum_utils.get_cluster_template_by_id(
            self.magnum, self.cluster_template.id)
        self.assertEqual(self.cluster_template, template_by_id)

    def test_create_cluster_template_bad_image(self):
        config = ClusterTemplateConfig(
            name=self.cluster_type_name,
            image='foo',
            keypair=self.keypair_creator.keypair_settings.name,
            external_net=self.ext_net_name,
            flavor=self.flavor_creator.flavor_settings.name)

        with self.assertRaises(BadRequest):
            self.cluster_template = magnum_utils.create_cluster_template(
                self.magnum, config)

    def test_create_cluster_template_bad_ext_net(self):
        config = ClusterTemplateConfig(
            name=self.cluster_type_name,
            image=self.image_creator.image_settings.name,
            keypair=self.keypair_creator.keypair_settings.name,
            external_net='foo',
            flavor=self.flavor_creator.flavor_settings.name)

        with self.assertRaises(BadRequest):
            self.cluster_template = magnum_utils.create_cluster_template(
                self.magnum, config)

    def test_create_cluster_template_bad_flavor(self):
        config = ClusterTemplateConfig(
            name=self.cluster_type_name,
            image=self.image_creator.image_settings.name,
            keypair=self.keypair_creator.keypair_settings.name,
            external_net=self.ext_net_name,
            flavor='foo')

        with self.assertRaises(BadRequest):
            self.cluster_template = magnum_utils.create_cluster_template(
                self.magnum, config)

    def test_create_cluster_template_bad_master_flavor(self):
        config = ClusterTemplateConfig(
            name=self.cluster_type_name,
            image=self.image_creator.image_settings.name,
            keypair=self.keypair_creator.keypair_settings.name,
            external_net=self.ext_net_name,
            flavor=self.flavor_creator.flavor_settings.name,
            master_flavor='foo')

        with self.assertRaises(BadRequest):
            self.cluster_template = magnum_utils.create_cluster_template(
                self.magnum, config)

    def test_create_cluster_template_bad_network_driver(self):
        config = ClusterTemplateConfig(
            name=self.cluster_type_name,
            image=self.image_creator.image_settings.name,
            keypair=self.keypair_creator.keypair_settings.name,
            external_net=self.ext_net_name,
            network_driver='foo')

        with self.assertRaises(BadRequest):
            self.cluster_template = magnum_utils.create_cluster_template(
                self.magnum, config)

    def test_create_cluster_template_bad_volume_driver(self):
        config = ClusterTemplateConfig(
            name=self.cluster_type_name,
            image=self.image_creator.image_settings.name,
            keypair=self.keypair_creator.keypair_settings.name,
            external_net=self.ext_net_name,
            volume_driver='foo')

        with self.assertRaises(BadRequest):
            self.cluster_template = magnum_utils.create_cluster_template(
                self.magnum, config)


def validate_cluster_template(tmplt_config, tmplt_obj):
    """
    Returns true if the configuration matches the ClusterTemplate object
    :param tmplt_config: the ClusterTemplateConfig object
    :param tmplt_obj: the ClusterTemplate domain object
    :return: T/F
    """
    if not tmplt_config.network_driver:
        network_driver = 'flannel'
    else:
        network_driver = tmplt_config.network_driver

    return (
        tmplt_config.coe.value == tmplt_obj.coe and
        tmplt_config.dns_nameserver == tmplt_obj.dns_nameserver and
        tmplt_config.docker_storage_driver.value
        == tmplt_obj.docker_storage_driver and
        tmplt_config.docker_volume_size == tmplt_obj.docker_volume_size and
        tmplt_config.external_net == tmplt_obj.external_net and
        tmplt_config.fixed_net == tmplt_obj.fixed_net and
        tmplt_config.fixed_subnet == tmplt_obj.fixed_subnet and
        tmplt_config.flavor == tmplt_obj.flavor and
        tmplt_config.floating_ip_enabled == tmplt_obj.floating_ip_enabled and
        tmplt_config.http_proxy == tmplt_obj.http_proxy and
        tmplt_config.https_proxy == tmplt_obj.https_proxy and
        tmplt_config.no_proxy == tmplt_obj.no_proxy and
        tmplt_config.image == tmplt_obj.image and
        tmplt_config.insecure_registry == tmplt_obj.insecure_registry and
        tmplt_config.keypair == tmplt_obj.keypair and
        tmplt_config.labels == tmplt_obj.labels and
        tmplt_config.master_flavor == tmplt_obj.master_flavor and
        tmplt_config.master_lb_enabled == tmplt_obj.master_lb_enabled and
        tmplt_config.name == tmplt_obj.name and
        network_driver == tmplt_obj.network_driver and
        tmplt_config.no_proxy == tmplt_obj.no_proxy and
        tmplt_config.public == tmplt_obj.public and
        tmplt_config.registry_enabled == tmplt_obj.registry_enabled and
        tmplt_config.server_type.value == tmplt_obj.server_type and
        tmplt_config.tls_disabled == tmplt_obj.tls_disabled and
        tmplt_config.volume_driver == tmplt_obj.volume_driver
    )
