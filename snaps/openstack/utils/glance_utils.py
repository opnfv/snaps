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
import os
import uuid

from snaps import file_utils
from glanceclient.client import Client

from snaps.domain.image import Image
from snaps.openstack.utils import keystone_utils

__author__ = 'spisarski'

logger = logging.getLogger('glance_utils')

VERSION_1 = 1.0
VERSION_2 = 2.0

"""
Utilities for basic neutron API calls
"""


def glance_client(os_creds):
    """
    Creates and returns a glance client object
    :return: the glance client
    """
    return Client(version=os_creds.image_api_version, session=keystone_utils.keystone_session(os_creds))


def get_image(glance, image_name=None):
    """
    Returns an OpenStack image object for a given name
    :param glance: the Glance client
    :param image_name: the image name to lookup
    :return: the image object or None
    """
    images = glance.images.list()
    for image in images:
        if glance.version == VERSION_1:
            if image.name == image_name:
                image = glance.images.get(image.id)
                return Image(name=image.name, image_id=image.id, size=image.size, properties=image.properties)
        elif glance.version == VERSION_2:
            if image['name'] == image_name:
                return Image(name=image['name'], image_id=image['id'], size=image['size'],
                             properties=image.get('properties'))
    return None


def get_image_status(glance, image):
    """
    Returns a new OpenStack Image object for a given OpenStack image object
    :param glance: the Glance client
    :param image: the domain Image object
    :return: the OpenStack Image object
    """
    if glance.version == VERSION_1:
        os_image = glance.images.get(image.id)
        return os_image.status
    elif glance.version == VERSION_2:
        os_image = glance.images.get(image.id)
        return os_image['status']
    else:
        raise Exception('Unsupported glance client version')


def create_image(glance, image_settings):
    """
    Creates and returns OpenStack image object with an external URL
    :param glance: the glance client
    :param image_settings: the image settings object
    :return: the OpenStack image object
    :raise Exception if using a file and it cannot be found
    """
    if glance.version == VERSION_1:
        return __create_image_v1(glance, image_settings)
    elif glance.version == VERSION_2:
        return __create_image_v2(glance, image_settings)
    else:
        raise Exception('Unsupported glance client version')


def __create_image_v1(glance, image_settings):
    """
    Creates and returns OpenStack image object with an external URL
    :param glance: the glance client
    :param image_settings: the image settings object
    :return: the OpenStack image object
    :raise Exception if using a file and it cannot be found
    """
    created_image = None

    if image_settings.url:
        if image_settings.extra_properties:
            created_image = glance.images.create(
                name=image_settings.name, disk_format=image_settings.format, container_format="bare",
                location=image_settings.url, properties=image_settings.extra_properties)
        else:
            created_image = glance.images.create(name=image_settings.name, disk_format=image_settings.format,
                                                 container_format="bare", location=image_settings.url)
    elif image_settings.image_file:
        image_file = file_utils.get_file(image_settings.image_file)
        if image_settings.extra_properties:
            created_image = glance.images.create(
                name=image_settings.name, disk_format=image_settings.format, container_format="bare", data=image_file,
                properties=image_settings.extra_properties)
        else:
            created_image = glance.images.create(
                name=image_settings.name, disk_format=image_settings.format, container_format="bare", data=image_file)

    return Image(name=image_settings.name, image_id=created_image.id, size=created_image.size,
                 properties=created_image.properties)


def __create_image_v2(glance, image_settings):
    """
    Creates and returns OpenStack image object with an external URL
    :param glance: the glance client v2
    :param image_settings: the image settings object
    :return: the OpenStack image object
    :raise Exception if using a file and it cannot be found
    """
    cleanup_file = False
    if image_settings.image_file:
        image_filename = image_settings.image_file
    elif image_settings.url:
        image_file = file_utils.download(image_settings.url, '/tmp', str(uuid.uuid4()))
        image_filename = image_file.name
        cleanup_file = True
    else:
        raise Exception('Filename or URL of image not configured')

    created_image = None
    try:
        kwargs = dict()
        kwargs['name'] = image_settings.name
        kwargs['disk_format'] = image_settings.format
        kwargs['container_format'] = 'bare'

        if image_settings.extra_properties:
            for key, value in image_settings.extra_properties.items():
                kwargs[key] = value

        created_image = glance.images.create(**kwargs)
        image_file = file_utils.get_file(image_filename)
        glance.images.upload(created_image['id'], image_file)
    except Exception as e:
        logger.error('Unexpected exception creating image. Rolling back')
        if created_image:
            delete_image(glance, created_image)
            raise e
    finally:
        if cleanup_file:
            os.remove(image_filename)

    updated_image = glance.images.get(created_image['id'])
    return Image(name=updated_image['name'], image_id=updated_image['id'], size=updated_image['size'],
                 properties=updated_image.get('properties'))


def delete_image(glance, image):
    """
    Deletes an image from OpenStack
    :param glance: the glance client
    :param image: the image to delete
    """
    if glance.version == VERSION_1:
        glance.images.delete(image)
    elif glance.version == VERSION_2:
        glance.images.delete(image.id)
    else:
        raise Exception('Unsupported glance client version')
