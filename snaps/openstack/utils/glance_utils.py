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
    return Client(version=os_creds.image_api_version,
                  session=keystone_utils.keystone_session(os_creds))


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
                return Image(name=image.name, image_id=image.id,
                             size=image.size, properties=image.properties)
        elif glance.version == VERSION_2:
            if image['name'] == image_name:
                return Image(
                    name=image['name'], image_id=image['id'],
                    size=image['size'], properties=image.get('properties'))
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
        raise GlanceException('Unsupported glance client version')


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
        raise GlanceException('Unsupported glance client version')


def __create_image_v1(glance, image_settings):
    """
    Creates and returns OpenStack image object with an external URL
    :param glance: the glance client
    :param image_settings: the image settings object
    :return: the OpenStack image object
    :raise exceptions from the Glance client or IOError when opening a file
    """
    kwargs = {
        'name': image_settings.name, 'disk_format': image_settings.format,
        'container_format': 'bare', 'is_public': image_settings.public}

    if image_settings.extra_properties:
        kwargs['properties'] = image_settings.extra_properties

    if image_settings.url:
        kwargs['location'] = image_settings.url
    elif image_settings.image_file:
        image_file = open(image_settings.image_file, 'rb')
        kwargs['data'] = image_file
    else:
        logger.warn('Unable to create image with name - %s. No file or URL',
                    image_settings.name)
        return None

    created_image = glance.images.create(**kwargs)
    return Image(name=image_settings.name, image_id=created_image.id,
                 size=created_image.size, properties=created_image.properties)


def __create_image_v2(glance, image_settings):
    """
    Creates and returns OpenStack image object with an external URL
    :param glance: the glance client v2
    :param image_settings: the image settings object
    :return: the OpenStack image object
    :raise GlanceException or IOException or URLError
    """
    cleanup_temp_file = False
    image_file = None
    if image_settings.image_file:
        image_filename = image_settings.image_file
    elif image_settings.url:
        file_name = str(uuid.uuid4())
        try:
            image_file = file_utils.download(
                image_settings.url, './tmp', file_name)
            image_filename = image_file.name
        except:
            os.remove('./tmp/' + file_name)
            raise

        cleanup_temp_file = True
    else:
        raise GlanceException('Filename or URL of image not configured')

    created_image = None
    try:
        kwargs = dict()
        kwargs['name'] = image_settings.name
        kwargs['disk_format'] = image_settings.format
        kwargs['container_format'] = 'bare'

        if image_settings.public:
            kwargs['visibility'] = 'public'

        if image_settings.extra_properties:
            kwargs.update(image_settings.extra_properties)

        created_image = glance.images.create(**kwargs)
        image_file = open(image_filename, 'rb')
        glance.images.upload(created_image['id'], image_file)
    except:
        logger.error('Unexpected exception creating image. Rolling back')
        if created_image:
            delete_image(glance, created_image)
        raise
    finally:
        if image_file:
            image_file.close()
        if cleanup_temp_file:
            os.remove(image_filename)

    updated_image = glance.images.get(created_image['id'])
    return Image(
        name=updated_image['name'], image_id=updated_image['id'],
        size=updated_image['size'], properties=updated_image.get('properties'))


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
        raise GlanceException('Unsupported glance client version')


class GlanceException(Exception):
    """
    Exception when calls to the Glance client cannot be served properly
    """
