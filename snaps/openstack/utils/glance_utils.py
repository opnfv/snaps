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


def glance_client(os_creds, session=None):
    """
    Creates and returns a glance client object
    :param os_creds: the credentials for connecting to the OpenStack remote API
    :param session: the keystone session object (optional)
    :return: the glance client
    """
    if not session:
        session = keystone_utils.keystone_session(os_creds)

    return Client(version=os_creds.image_api_version,
                  session=session,
                  region_name=os_creds.region_name)


def get_image(glance, image_name=None, image_settings=None):
    """
    Returns an OpenStack image object for a given name
    :param glance: the Glance client
    :param image_name: the image name to lookup
    :param image_settings: the image settings used for lookups
    :return: the image object or None
    """
    img_filter = dict()
    if image_settings:
        if image_settings.exists:
            img_filter = {'name': image_settings.name}
        else:
            img_filter = {'name': image_settings.name,
                          'disk_format': image_settings.format}
    elif image_name:
        img_filter = {'name': image_name}

    images = glance.images.list(**{'filters': img_filter})
    for image in images:
        if glance.version == VERSION_1:
            image = glance.images.get(image.id)
            return Image(name=image.name, image_id=image.id,
                         size=image.size, properties=image.properties)
        elif glance.version == VERSION_2:
            return Image(
                name=image['name'], image_id=image['id'],
                size=image['size'], properties=image.get('properties'))


def get_image_by_id(glance, image_id):
    """
    Returns an OpenStack image object for a given name
    :param glance: the Glance client
    :param image_id: the image ID to lookup
    :return: the SNAPS-OO Domain Image object or None
    """
    image = glance.images.get(image_id)
    return Image(
        name=image['name'], image_id=image['id'],
        size=image['size'], properties=image.get('properties'))


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

    image_file = None

    try:
        if image_settings.extra_properties:
            kwargs['properties'] = image_settings.extra_properties

        if image_settings.url:
            kwargs['location'] = image_settings.url
        elif image_settings.image_file:
            image_file = open(image_settings.image_file, 'rb')
            kwargs['data'] = image_file
        else:
            logger.warn(
                'Unable to create image with name - %s. No file or URL',
                image_settings.name)
            return None

        created_image = glance.images.create(**kwargs)
        return Image(name=image_settings.name, image_id=created_image.id,
                     size=created_image.size,
                     properties=created_image.properties)
    finally:
        if image_file:
            image_file.close()


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
    if image_settings.image_file is not None:
        image_filename = image_settings.image_file
    elif image_settings.url:
        file_name = str(uuid.uuid4())
        try:
            image_file = file_utils.download(
                image_settings.url, './tmp', file_name)
            image_filename = image_file.name
        except:
            if image_file:
                os.remove(image_file.name)
            raise

        cleanup_temp_file = True
    else:
        raise GlanceException('Filename or URL of image not configured')

    os_image = None
    try:
        kwargs = dict()
        kwargs['name'] = image_settings.name
        kwargs['disk_format'] = image_settings.format
        kwargs['container_format'] = 'bare'

        if image_settings.public:
            kwargs['visibility'] = 'public'

        if image_settings.extra_properties:
            kwargs.update(image_settings.extra_properties)

        os_image = glance.images.create(**kwargs)
        image_file = open(os.path.expanduser(image_filename), 'rb')
        glance.images.upload(os_image['id'], image_file)
    except:
        logger.error('Unexpected exception creating image. Rolling back')
        if os_image:
            delete_image(glance, Image(
                name=os_image['name'], image_id=os_image['id'],
                size=os_image['size'], properties=os_image.get('properties')))
        raise
    finally:
        if image_file:
            logger.debug('Closing file %s', image_file.name)
            image_file.close()
        if cleanup_temp_file:
            logger.info('Removing file %s', image_file.name)
            os.remove(image_filename)

    return get_image_by_id(glance, os_image['id'])


def delete_image(glance, image):
    """
    Deletes an image from OpenStack
    :param glance: the glance client
    :param image: the image to delete
    """
    logger.info('Deleting image named - %s', image.name)
    glance.images.delete(image.id)


class GlanceException(Exception):
    """
    Exception when calls to the Glance client cannot be served properly
    """
