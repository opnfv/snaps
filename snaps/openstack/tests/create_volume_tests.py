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
from cinderclient.exceptions import NotFound, BadRequest

from snaps.config.volume import VolumeConfig, VolumeConfigError
from snaps.config.volume_type import VolumeTypeConfig
from snaps.openstack.create_image import OpenStackImage
from snaps.openstack.create_volume_type import OpenStackVolumeType
from snaps.openstack.tests import openstack_tests

try:
    from urllib.request import URLError
except ImportError:
    from urllib2 import URLError

import logging
import unittest
import uuid

from snaps.openstack.create_volume import (
    VolumeSettings, OpenStackVolume)
from snaps.openstack.tests.os_source_file_test import OSIntegrationTestCase
from snaps.openstack.utils import cinder_utils, keystone_utils

__author__ = 'spisarski'

logger = logging.getLogger('create_volume_tests')


class VolumeSettingsUnitTests(unittest.TestCase):
    """
    Tests the construction of the VolumeSettings class
    """

    def test_no_params(self):
        with self.assertRaises(VolumeConfigError):
            VolumeSettings()

    def test_empty_config(self):
        with self.assertRaises(VolumeConfigError):
            VolumeSettings(**dict())

    def test_name_only(self):
        settings = VolumeSettings(name='foo')
        self.assertEqual('foo', settings.name)
        self.assertIsNone(settings.description)
        self.assertEquals(1, settings.size)
        self.assertIsNone(settings.image_name)
        self.assertIsNone(settings.type_name)
        self.assertIsNone(settings.availability_zone)
        self.assertFalse(settings.multi_attach)

    def test_config_with_name_only(self):
        settings = VolumeSettings(**{'name': 'foo'})
        self.assertEqual('foo', settings.name)
        self.assertIsNone(settings.description)
        self.assertEquals(1, settings.size)
        self.assertIsNone(settings.image_name)
        self.assertIsNone(settings.type_name)
        self.assertIsNone(settings.availability_zone)
        self.assertFalse(settings.multi_attach)

    def test_all_strings(self):
        settings = VolumeSettings(
            name='foo', description='desc', size='2', image_name='image',
            type_name='type', availability_zone='zone1', multi_attach='true')

        self.assertEqual('foo', settings.name)
        self.assertEqual('desc', settings.description)
        self.assertEqual(2, settings.size)
        self.assertEqual('image', settings.image_name)
        self.assertEqual('type', settings.type_name)
        self.assertEqual('zone1', settings.availability_zone)
        self.assertTrue(settings.multi_attach)

    def test_all_correct_type(self):
        settings = VolumeSettings(
            name='foo', description='desc', size=2, image_name='image',
            type_name='bar', availability_zone='zone1', multi_attach=True)

        self.assertEqual('foo', settings.name)
        self.assertEqual('desc', settings.description)
        self.assertEqual(2, settings.size)
        self.assertEqual('image', settings.image_name)
        self.assertEqual('bar', settings.type_name)
        self.assertEqual('zone1', settings.availability_zone)
        self.assertTrue(settings.multi_attach)

    def test_config_all(self):
        settings = VolumeSettings(
            **{'name': 'foo', 'description': 'desc', 'size': '2',
               'image_name': 'foo', 'type_name': 'bar',
               'availability_zone': 'zone1', 'multi_attach': 'true'})

        self.assertEqual('foo', settings.name)
        self.assertEqual('desc', settings.description)
        self.assertEqual(2, settings.size)
        self.assertEqual('foo', settings.image_name)
        self.assertEqual('bar', settings.type_name)
        self.assertEqual('zone1', settings.availability_zone)
        self.assertTrue(settings.multi_attach)


class CreateSimpleVolumeSuccessTests(OSIntegrationTestCase):
    """
    Test for the CreateVolume class defined in create_volume.py
    """

    def setUp(self):
        """
        Instantiates the CreateVolume object that is responsible for
        downloading and creating an OS volume file within OpenStack
        """
        super(self.__class__, self).__start__()

        guid = uuid.uuid4()
        self.volume_settings = VolumeConfig(
            name=self.__class__.__name__ + '-' + str(guid))

        self.cinder = cinder_utils.cinder_client(
            self.os_creds, self.os_session)
        self.keystone = keystone_utils.keystone_client(
            self.os_creds, self.os_session)
        self.volume_creator = None

    def tearDown(self):
        """
        Cleans the volume and downloaded volume file
        """
        if self.volume_creator:
            self.volume_creator.clean()

        super(self.__class__, self).__clean__()

    def test_create_volume_simple(self):
        """
        Tests the creation of a simple OpenStack volume.
        """
        # Create Volume
        self.volume_creator = OpenStackVolume(
            self.os_creds, self.volume_settings)
        created_volume = self.volume_creator.create(block=True)
        self.assertIsNotNone(created_volume)

        retrieved_volume = cinder_utils.get_volume(
            self.cinder, self.keystone, volume_settings=self.volume_settings,
            project_name=self.os_creds.project_name)

        self.assertIsNotNone(retrieved_volume)
        self.assertEqual(created_volume.id, retrieved_volume.id)
        self.assertTrue(created_volume == retrieved_volume)

    def test_create_delete_volume(self):
        """
        Tests the creation then deletion of an OpenStack volume to ensure
        clean() does not raise an Exception.
        """
        # Create Volume
        self.volume_creator = OpenStackVolume(
            self.os_creds, self.volume_settings)
        created_volume = self.volume_creator.create(block=True)
        self.assertIsNotNone(created_volume)

        retrieved_volume = cinder_utils.get_volume(
            self.cinder, self.keystone, volume_settings=self.volume_settings,
            project_name=self.os_creds.project_name)
        self.assertIsNotNone(retrieved_volume)
        self.assertEqual(created_volume, retrieved_volume)

        # Delete Volume manually
        self.volume_creator.clean()

        self.assertIsNone(cinder_utils.get_volume(
            self.cinder, self.keystone, volume_settings=self.volume_settings,
            project_name=self.os_creds.project_name))

        # Must not throw an exception when attempting to cleanup non-existent
        # volume
        self.volume_creator.clean()
        self.assertIsNone(self.volume_creator.get_volume())

    def test_create_same_volume(self):
        """
        Tests the creation of an OpenStack volume when one already exists.
        """
        # Create Volume
        self.volume_creator = OpenStackVolume(
            self.os_creds, self.volume_settings)
        volume1 = self.volume_creator.create(block=True)

        retrieved_volume = cinder_utils.get_volume(
            self.cinder, self.keystone, volume_settings=self.volume_settings,
            project_name=self.os_creds.project_name)
        self.assertEqual(volume1, retrieved_volume)

        # Should be retrieving the instance data
        os_volume_2 = OpenStackVolume(
            self.os_creds, self.volume_settings)
        volume2 = os_volume_2.create(block=True)
        self.assertEqual(volume1, volume2)


class CreateSimpleVolumeFailureTests(OSIntegrationTestCase):
    """
    Test for the CreateVolume class defined in create_volume.py
    """

    def setUp(self):
        """
        Instantiates the CreateVolume object that is responsible for
        downloading and creating an OS volume file within OpenStack
        """
        super(self.__class__, self).__start__()

        self.guid = uuid.uuid4()
        self.cinder = cinder_utils.cinder_client(
            self.os_creds, self.os_session)
        self.volume_creator = None

    def tearDown(self):
        """
        Cleans the volume and downloaded volume file
        """
        if self.volume_creator:
            self.volume_creator.clean()

        super(self.__class__, self).__clean__()

    def test_create_volume_bad_size(self):
        """
        Tests the creation of an OpenStack volume with a negative size to
        ensure it raises a BadRequest exception.
        """
        volume_settings = VolumeConfig(
            name=self.__class__.__name__ + '-' + str(self.guid), size=-1)

        # Create Volume
        self.volume_creator = OpenStackVolume(self.os_creds, volume_settings)

        with self.assertRaises(BadRequest):
            self.volume_creator.create(block=True)

    def test_create_volume_bad_type(self):
        """
        Tests the creation of an OpenStack volume with a type that does not
        exist to ensure it raises a NotFound exception.
        """
        volume_settings = VolumeConfig(
            name=self.__class__.__name__ + '-' + str(self.guid),
            type_name='foo')

        # Create Volume
        self.volume_creator = OpenStackVolume(self.os_creds, volume_settings)

        with self.assertRaises(NotFound):
            self.volume_creator.create(block=True)

    def test_create_volume_bad_image(self):
        """
        Tests the creation of an OpenStack volume with an image that does not
        exist to ensure it raises a BadRequest exception.
        """
        volume_settings = VolumeConfig(
            name=self.__class__.__name__ + '-' + str(self.guid),
            image_name='foo')

        # Create Volume
        self.volume_creator = OpenStackVolume(self.os_creds, volume_settings)

        with self.assertRaises(BadRequest):
            self.volume_creator.create(block=True)


class CreateVolumeWithTypeTests(OSIntegrationTestCase):
    """
    Test cases for the CreateVolume when attempting to associate it to a
    Volume Type
    """

    def setUp(self):
        super(self.__class__, self).__start__()

        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.volume_name = guid + '-vol'
        self.volume_type_name = guid + '-vol-type'

        self.volume_type_creator = OpenStackVolumeType(
            self.admin_os_creds, VolumeTypeConfig(name=self.volume_type_name))
        self.volume_type_creator.create()
        self.volume_creator = None

    def tearDown(self):
        if self.volume_creator:
            self.volume_creator.clean()
        if self.volume_type_creator:
            self.volume_type_creator.clean()

        super(self.__class__, self).__clean__()

    def test_bad_volume_type(self):
        """
        Expect a NotFound to be raised when the volume type does not exist
        """
        self.volume_creator = OpenStackVolume(
            self.os_creds,
            VolumeConfig(name=self.volume_name, type_name='foo'))

        with self.assertRaises(NotFound):
            self.volume_creator.create()

    def test_valid_volume_type(self):
        """
        Expect a NotFound to be raised when the volume type does not exist
        """
        self.volume_creator = OpenStackVolume(
            self.admin_os_creds, VolumeConfig(
                name=self.volume_name, type_name=self.volume_type_name))

        created_volume = self.volume_creator.create(block=True)
        self.assertIsNotNone(created_volume)
        self.assertEqual(self.volume_type_name, created_volume.type)


class CreateVolumeWithImageTests(OSIntegrationTestCase):
    """
    Test cases for the CreateVolume when attempting to associate it to an Image
    """

    def setUp(self):
        super(self.__class__, self).__start__()

        self.cinder = cinder_utils.cinder_client(
            self.os_creds, self.os_session)

        guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.volume_name = guid + '-vol'
        self.image_name = guid + '-image'

        os_image_settings = openstack_tests.cirros_image_settings(
            name=self.image_name, image_metadata=self.image_metadata)
        # Create Image
        self.image_creator = OpenStackImage(self.os_creds,
                                            os_image_settings)
        self.image_creator.create()
        self.volume_creator = None

    def tearDown(self):
        if self.volume_creator:
            try:
                self.volume_creator.clean()
            except:
                pass
        if self.image_creator:
            try:
                self.image_creator.clean()
            except:
                pass

        super(self.__class__, self).__clean__()

    def test_bad_image_name(self):
        """
        Tests OpenStackVolume#create() method to ensure a volume is NOT created
        when associating it to an invalid image name
        """
        self.volume_creator = OpenStackVolume(
            self.os_creds,
            VolumeConfig(name=self.volume_name, image_name='foo'))

        with self.assertRaises(BadRequest):
            self.volume_creator.create(block=True)

    def test_valid_volume_image(self):
        """
        Tests OpenStackVolume#create() method to ensure a volume is NOT created
        when associating it to an invalid image name
        """
        self.volume_creator = OpenStackVolume(
            self.os_creds,
            VolumeConfig(name=self.volume_name, image_name=self.image_name))

        created_volume = self.volume_creator.create(block=True)
        self.assertIsNotNone(created_volume)
        self.assertEqual(
            self.volume_creator.volume_settings.name, created_volume.name)
        self.assertTrue(self.volume_creator.volume_active())

        retrieved_volume = cinder_utils.get_volume_by_id(
            self.cinder, created_volume.id)

        self.assertEqual(created_volume, retrieved_volume)


class CreateVolMultipleCredsTests(OSIntegrationTestCase):
    """
    Test for the OpenStackVolume class and how it interacts with volumes
    created with differenct credentials and to other projects with the same
    name
    """
    def setUp(self):
        super(self.__class__, self).__start__()

        self.guid = self.__class__.__name__ + '-' + str(uuid.uuid4())
        self.volume_creators = list()

    def tearDown(self):
        for volume_creator in self.volume_creators:
            volume_creator.clean()

        super(self.__class__, self).__clean__()

    # TODO - activate after cinder API bug has been fixed
    # see https://bugs.launchpad.net/cinder/+bug/1641982 as to why this test
    # is not activated
    # def test_create_by_admin_to_other_proj(self):
    #     """
    #     Creates a volume as admin to the project of os_creds then instantiates
    #     a creator object with the os_creds project to ensure it initializes
    #     without creation
    #     """
    #     self.volume_creators.append(OpenStackVolume(
    #         self.admin_os_creds, VolumeConfig(
    #             name=self.guid + '-vol',
    #             project_name=self.os_creds.project_name)))
    #     admin_vol = self.volume_creators[0].create(block=True)
    #
    #     self.volume_creators.append(OpenStackVolume(
    #         self.os_creds, VolumeConfig(name=self.guid + '-vol')))
    #     proj_vol = self.volume_creators[1].create(block=True)
    #
    #     self.assertEqual(admin_vol, proj_vol)

    def test_create_two_vol_same_name_diff_proj(self):
        """
        Creates a volume as admin to the project of os_creds then instantiates
        a creator object with the os_creds project to ensure it initializes
        without creation
        """
        vol_name = self.guid + '-vol'
        self.volume_creators.append(OpenStackVolume(
            self.admin_os_creds, VolumeConfig(name=vol_name)))
        admin_vol = self.volume_creators[0].create(block=True)
        self.assertIsNotNone(admin_vol)

        admin_key = keystone_utils.keystone_client(
            self.admin_os_creds, self.admin_os_session)
        admin_proj = keystone_utils.get_project(
            admin_key, project_name=self.admin_os_creds.project_name)
        self.assertEqual(admin_vol.project_id, admin_proj.id)

        admin_cinder = cinder_utils.cinder_client(
            self.admin_os_creds, self.admin_os_session)
        admin_vol_get = cinder_utils.get_volume(
            admin_cinder, admin_key, volume_name=vol_name,
            project_name=self.admin_os_creds.project_name)
        self.assertIsNotNone(admin_vol_get)
        self.assertEqual(admin_vol, admin_vol_get)

        self.volume_creators.append(OpenStackVolume(
            self.os_creds, VolumeConfig(name=vol_name)))
        proj_vol = self.volume_creators[1].create(block=True)
        self.assertIsNotNone(proj_vol)

        self.assertNotEqual(admin_vol, proj_vol)

        proj_key = keystone_utils.keystone_client(
            self.os_creds, self.os_session)
        proj_cinder = cinder_utils.cinder_client(
            self.os_creds, self.os_session)
        proj_vol_get = cinder_utils.get_volume(
            proj_cinder, proj_key, volume_name=vol_name,
            project_name=self.os_creds.project_name)

        self.assertIsNotNone(proj_vol_get)
        self.assertEqual(proj_vol, proj_vol_get)
