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
import logging

from snaps import file_utils
from glanceclient.client import Client
from snaps.openstack.utils import keystone_utils

__author__ = 'spisarski'

logger = logging.getLogger('glance_utils')

"""
Utilities for basic neutron API calls
"""


def glance_client(os_creds):
    """
    Creates and returns a glance client object
    :return: the glance client
    """
    return Client(version=os_creds.image_api_version, session=keystone_utils.keystone_session(os_creds))


def get_image(nova, glance, image_name):
    """
    Returns an OpenStack image object for a given name
    :param nova: the Nova client
    :param glance: the Glance client
    :param image_name: the image name to lookup
    :return: the image object or None
    """
    try:
        image_dict = nova.images.find(name=image_name)
        if image_dict:
            return glance.images.get(image_dict.id)
    except:
        pass
    return None


def create_image(glance, image_settings):
    """
    Creates and returns OpenStack image object with an external URL
    :param glance: the glance client
    :param image_settings: the image settings object
    :return: the OpenStack image object
    :raise Exception if using a file and it cannot be found
    """
    if image_settings.url:
        return glance.images.create(name=image_settings.name, disk_format=image_settings.format,
                                    container_format="bare", location=image_settings.url)
    elif image_settings.image_file:
        image_file = file_utils.get_file(image_settings.image_file)
        return glance.images.create(name=image_settings.name, disk_format=image_settings.format,
                                    container_format="bare", data=image_file)


def delete_image(glance, image):
    """
    Deletes an image from OpenStack
    :param glance: the glance client
    :param image: the image to delete
    """
    glance.images.delete(image)
