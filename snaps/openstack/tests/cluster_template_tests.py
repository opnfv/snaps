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
from magnumclient.common.apiclient.exceptions import BadRequest

from snaps.config.cluster_template import ClusterTemplateConfig
from snaps.config.flavor import FlavorConfig
from snaps.config.keypair import KeypairConfig
from snaps.openstack.cluster_template import OpenStackClusterTemplate
from snaps.openstack.create_flavor import OpenStackFlavor
from snaps.openstack.create_image import OpenStackImage
from snaps.openstack.create_keypairs import OpenStackKeypair
from snaps.openstack.tests import openstack_tests

try:
    from urllib.request import URLError
except ImportError:
    from urllib2 import URLError

import logging
import uuid

from snaps.openstack.tests.os_source_file_test import OSIntegrationTestCase
from snaps.openstack.utils import magnum_utils

__author__ = 'spisarski'

logger = logging.getLogger('cluster_template_tests')


class CreateClusterTemplateTests(OSIntegrationTestCase):
    """
    Test for the OpenStackClusterTemplate class defined in py
    without any QoS Specs or Encryption
    """

    def setUp(self):
        """
        Instantiates the CreateClusterTemplate object that is responsible for
        downloading and creating an OS template config file within OpenStack
        """
        super(self.__class__, self).__start__()

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

        flavor_config = openstack_tests.get_flavor_config(
            name=self.guid + '-flavor', ram=512, disk=10,
            vcpus=1, metadata=self.flavor_metadata)
        self.flavor_creator = OpenStackFlavor(self.os_creds, flavor_config)

        keypair_priv_filepath = 'tmp/' + self.guid
        keypair_pub_filepath = keypair_priv_filepath + '.pub'

        self.keypair_creator = OpenStackKeypair(
            self.os_creds, KeypairConfig(
                name=self.guid + '-keypair',
                public_filepath=keypair_pub_filepath,
                private_filepath=keypair_priv_filepath))

        self.cluster_template_creator = None

        self.cluster_template_config = ClusterTemplateConfig(
            name=self.cluster_type_name,
            image=self.image_creator.image_settings.name,
            keypair=self.keypair_creator.keypair_settings.name,
            external_net=self.ext_net_name,
            flavor=self.flavor_creator.flavor_settings.name)

        try:
            self.image_creator.create()
            self.flavor_creator.create()
            self.keypair_creator.create()
        except:
            self.tearDown()
            raise

    def tearDown(self):
        """
        Cleans the template config
        """
        if self.cluster_template_creator:
            try:
                self.cluster_template_creator.clean()
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

    def test_create_cluster_template(self):
        """
        Tests the creation of an OpenStack cluster template.
        """
        # Create ClusterTemplate
        self.cluster_template_creator = OpenStackClusterTemplate(
            self.os_creds, self.cluster_template_config)
        created_cluster_template = self.cluster_template_creator.create()
        self.assertIsNotNone(created_cluster_template)
        self.assertEqual(self.cluster_template_config.name,
                         created_cluster_template.name)

        retrieved_cluster_template1 = magnum_utils.get_cluster_template(
            self.magnum, template_config=self.cluster_template_config)
        self.assertIsNotNone(retrieved_cluster_template1)
        self.assertEqual(created_cluster_template, retrieved_cluster_template1)

        retrieved_cluster_template2 = magnum_utils.get_cluster_template_by_id(
            self.magnum, created_cluster_template.id)
        self.assertEqual(created_cluster_template, retrieved_cluster_template2)

    def test_create_delete_cluster_template(self):
        """
        Tests the creation then deletion of an OpenStack template config to
        ensure clean() does not raise an Exception.
        """
        # Create ClusterTemplate
        self.cluster_template_creator = OpenStackClusterTemplate(
            self.os_creds, self.cluster_template_config)
        created_cluster_template = self.cluster_template_creator.create()
        self.assertIsNotNone(created_cluster_template)

        self.cluster_template_creator.clean()

        tmplt = magnum_utils.get_cluster_template(
            self.magnum, template_name=self.cluster_template_config.name)
        self.assertIsNone(tmplt)

    def test_create_same_cluster_template(self):
        """
        Tests the creation of an OpenStack cluster_template when one already
        exists.
        """
        # Create ClusterTemplate
        self.cluster_template_creator = OpenStackClusterTemplate(
            self.os_creds, self.cluster_template_config)
        cluster_template1 = self.cluster_template_creator.create()

        retrieved_cluster_template = magnum_utils.get_cluster_template(
            self.magnum, template_config=self.cluster_template_config)
        self.assertEqual(cluster_template1, retrieved_cluster_template)

        # Should be retrieving the instance data
        os_cluster_template_2 = OpenStackClusterTemplate(
            self.os_creds, self.cluster_template_config)
        cluster_template2 = os_cluster_template_2.create()
        self.assertEqual(cluster_template2, cluster_template2)

    def test_create_cluster_template_bad_flavor(self):
        """
        Tests the creation of an OpenStack cluster template raises an
        exception with an invalid flavor.
        """
        # Create ClusterTemplate
        cluster_template_config = ClusterTemplateConfig(
            name=self.cluster_type_name,
            image=self.image_creator.image_settings.name,
            keypair=self.keypair_creator.keypair_settings.name,
            external_net=self.ext_net_name,
            flavor='foo')

        self.cluster_template_creator = OpenStackClusterTemplate(
            self.os_creds, cluster_template_config)

        with self.assertRaises(BadRequest):
            self.cluster_template_creator.create()

    def test_create_cluster_template_bad_master_flavor(self):
        """
        Tests the creation of an OpenStack cluster template raises an
        exception with an invalid master flavor.
        """
        # Create ClusterTemplate
        cluster_template_config = ClusterTemplateConfig(
            name=self.cluster_type_name,
            image=self.image_creator.image_settings.name,
            keypair=self.keypair_creator.keypair_settings.name,
            external_net=self.ext_net_name,
            flavor=self.flavor_creator.flavor_settings.name,
            master_flavor='foo')

        self.cluster_template_creator = OpenStackClusterTemplate(
            self.os_creds, cluster_template_config)

        with self.assertRaises(BadRequest):
            self.cluster_template_creator.create()

    def test_create_cluster_template_bad_image(self):
        """
        Tests the creation of an OpenStack cluster template raises an
        exception with an invalid image.
        """
        # Create ClusterTemplate
        cluster_template_config = ClusterTemplateConfig(
            name=self.cluster_type_name,
            image='foo',
            keypair=self.keypair_creator.keypair_settings.name,
            external_net=self.ext_net_name,
            flavor=self.flavor_creator.flavor_settings.name)

        self.cluster_template_creator = OpenStackClusterTemplate(
            self.os_creds, cluster_template_config)

        with self.assertRaises(BadRequest):
            self.cluster_template_creator.create()

    def test_create_cluster_template_bad_network_driver(self):
        """
        Tests the creation of an OpenStack cluster template raises an
        exception with an invalid keypair.
        """
        # Create ClusterTemplate
        cluster_template_config = ClusterTemplateConfig(
            name=self.cluster_type_name,
            image=self.image_creator.image_settings.name,
            keypair=self.keypair_creator.keypair_settings.name,
            external_net=self.ext_net_name,
            flavor=self.flavor_creator.flavor_settings.name,
            network_driver='foo')

        self.cluster_template_creator = OpenStackClusterTemplate(
            self.os_creds, cluster_template_config)

        with self.assertRaises(BadRequest):
            self.cluster_template_creator.create()

    def test_create_cluster_template_bad_volume_driver(self):
        """
        Tests the creation of an OpenStack cluster template raises an
        exception with an invalid keypair.
        """
        # Create ClusterTemplate
        cluster_template_config = ClusterTemplateConfig(
            name=self.cluster_type_name,
            image=self.image_creator.image_settings.name,
            keypair=self.keypair_creator.keypair_settings.name,
            external_net=self.ext_net_name,
            flavor=self.flavor_creator.flavor_settings.name,
            volume_driver='foo')

        self.cluster_template_creator = OpenStackClusterTemplate(
            self.os_creds, cluster_template_config)

        with self.assertRaises(BadRequest):
            self.cluster_template_creator.create()
