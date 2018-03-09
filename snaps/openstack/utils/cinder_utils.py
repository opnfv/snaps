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

from cinderclient.client import Client
from cinderclient.exceptions import NotFound

from snaps.domain.volume import (
    QoSSpec, VolumeType, VolumeTypeEncryption, Volume)
from snaps.openstack.utils import keystone_utils

__author__ = 'spisarski'

logger = logging.getLogger('cinder_utils')

VERSION_2 = 2
VERSION_3 = 3

"""
Utilities for basic neutron API calls
"""


def cinder_client(os_creds, session=None):
    """
    Creates and returns a cinder client object
    :param os_creds: the credentials for connecting to the OpenStack remote API
    :param session: the keystone session object (optional)
    :return: the cinder client
    """
    if not session:
        session = keystone_utils.keystone_session(os_creds)

    return Client(version=os_creds.volume_api_version,
                  session=session,
                  region_name=os_creds.region_name)


def get_volume(cinder, keystone=None, volume_name=None, volume_settings=None,
               project_name=None):
    """
    Returns an OpenStack volume object for a given name
    :param cinder: the Cinder client
    :param keystone: the Keystone client (required if project_name or
                     volume_settings.project_name is not None
    :param volume_name: the volume name to lookup
    :param volume_settings: the volume settings used for lookups
    :param project_name: the name of the project associated with the volume
    :return: the volume object or None
    """
    if volume_settings:
        volume_name = volume_settings.name

    volumes = cinder.volumes.list()
    for os_volume in volumes:
        if os_volume.name == volume_name:
            project_id = None
            if hasattr(os_volume, 'os-vol-tenant-attr:tenant_id'):
                project_id = getattr(
                    os_volume, 'os-vol-tenant-attr:tenant_id')

            if volume_settings and volume_settings.project_name:
                project_name = volume_settings.project_name

            if project_name:
                project = keystone_utils.get_project_by_id(
                    keystone, project_id)

                if project and project.name == project_name:
                    return __map_os_volume_to_domain(os_volume)
            else:
                return __map_os_volume_to_domain(os_volume)


def __get_os_volume_by_id(cinder, volume_id):
    """
    Returns an OpenStack volume object for a given name
    :param cinder: the Cinder client
    :param volume_id: the volume ID to lookup
    :return: the SNAPS-OO Domain Volume object or None
    """
    return cinder.volumes.get(volume_id)


def get_volume_by_id(cinder, volume_id):
    """
    Returns an OpenStack volume object for a given name
    :param cinder: the Cinder client
    :param volume_id: the volume ID to lookup
    :return: the SNAPS-OO Domain Volume object or None
    """
    os_volume = __get_os_volume_by_id(cinder, volume_id)
    return __map_os_volume_to_domain(os_volume)


def __map_os_volume_to_domain(os_volume):
    """
    Returns a SNAPS-OO domain Volume object that is created by an OpenStack
    Volume object
    :param os_volume: the OpenStack volume object
    :return: Volume domain object
    """
    project_id = None
    if hasattr(os_volume, 'os-vol-tenant-attr:tenant_id'):
        project_id = getattr(
            os_volume, 'os-vol-tenant-attr:tenant_id')

    return Volume(
        name=os_volume.name, volume_id=os_volume.id,
        project_id=project_id, description=os_volume.description,
        size=os_volume.size, vol_type=os_volume.volume_type,
        availability_zone=os_volume.availability_zone,
        multi_attach=os_volume.multiattach,
        attachments=os_volume.attachments)


def get_volume_status(cinder, volume):
    """
    Returns a new OpenStack Volume object for a given OpenStack volume object
    :param cinder: the Cinder client
    :param volume: the domain Volume object
    :return: the OpenStack Volume object
    """
    os_volume = cinder.volumes.get(volume.id)
    return os_volume.status


def create_volume(cinder, keystone, volume_settings):
    """
    Creates and returns OpenStack volume object with an external URL
    :param cinder: the cinder client
    :param keystone: the keystone client
    :param volume_settings: the volume settings object
    :return: the OpenStack volume object
    :raise Exception if using a file and it cannot be found
    """
    project_id = None
    if volume_settings.project_name:
        project = keystone_utils.get_project(
            keystone, project_name=volume_settings.project_name)
        if project:
            project_id = project.id
        else:
            raise KeystoneUtilsException(
                'Project cannot be found with name - '
                + volume_settings.project_name)
    os_volume = cinder.volumes.create(
        name=volume_settings.name,
        project_id=project_id,
        description=volume_settings.description,
        size=volume_settings.size,
        imageRef=volume_settings.image_name,
        volume_type=volume_settings.type_name,
        availability_zone=volume_settings.availability_zone,
        multiattach=volume_settings.multi_attach)

    return __map_os_volume_to_domain(os_volume)


def delete_volume(cinder, volume):
    """
    Deletes an volume from OpenStack
    :param cinder: the cinder client
    :param volume: the volume to delete
    """
    logger.info('Deleting volume named - %s', volume.name)
    return cinder.volumes.delete(volume.id)


def get_volume_type(cinder, volume_type_name=None, volume_type_settings=None):
    """
    Returns an OpenStack volume type object for a given name
    :param cinder: the Cinder client
    :param volume_type_name: the volume type name to lookup
    :param volume_type_settings: the volume type settings used for lookups
    :return: the volume type object or None
    """
    if not volume_type_name and not volume_type_settings:
        return None

    if volume_type_settings:
        volume_type_name = volume_type_settings.name

    volume_types = cinder.volume_types.list()
    for vol_type in volume_types:
        if vol_type.name == volume_type_name:
            encryption = get_volume_encryption_by_type(cinder, vol_type)
            return VolumeType(vol_type.name, vol_type.id, vol_type.is_public,
                              encryption, None)


def __get_os_volume_type_by_id(cinder, volume_type_id):
    """
    Returns an OpenStack volume type object for a given name
    :param cinder: the Cinder client
    :param volume_type_id: the volume_type ID to lookup
    :return: the SNAPS-OO Domain Volume object or None
    """
    try:
        return cinder.volume_types.get(volume_type_id)
    except NotFound:
        logger.info('Volume with ID [%s] does not exist',
                    volume_type_id)


def get_volume_type_by_id(cinder, volume_type_id):
    """
    Returns an OpenStack volume type object for a given name
    :param cinder: the Cinder client
    :param volume_type_id: the volume_type ID to lookup
    :return: the SNAPS-OO Domain Volume object or None
    """
    os_vol_type = __get_os_volume_type_by_id(cinder, volume_type_id)
    if os_vol_type:
        temp_vol_type = VolumeType(os_vol_type.name, os_vol_type.id,
                                   os_vol_type.is_public, None, None)
        encryption = get_volume_encryption_by_type(cinder, temp_vol_type)

        qos_spec = None
        if os_vol_type.qos_specs_id:
            qos_spec = get_qos_by_id(cinder, os_vol_type.qos_specs_id)

        return VolumeType(os_vol_type.name, os_vol_type.id,
                          os_vol_type.is_public, encryption, qos_spec)


def create_volume_type(cinder, type_settings):
    """
    Creates and returns OpenStack volume type object with an external URL
    :param cinder: the cinder client
    :param type_settings: the volume type settings object
    :return: the volume type domain object
    :raise Exception if using a file and it cannot be found
    """
    vol_type = cinder.volume_types.create(
        type_settings.name, type_settings.description,
        type_settings.public)

    vol_encryption = None
    if type_settings.encryption:
        try:
            vol_encryption = create_volume_encryption(
                cinder, vol_type, type_settings.encryption)
        except Exception as e:
            logger.warn('Error creating volume encryption - %s', e)

    qos_spec = None
    if type_settings.qos_spec_name:
        try:
            qos_spec = get_qos(cinder, qos_name=type_settings.qos_spec_name)
            cinder.qos_specs.associate(qos_spec, vol_type.id)
        except NotFound as e:
            logger.warn('Unable to locate qos_spec named %s - %s',
                        type_settings.qos_spec_name, e)

    return VolumeType(vol_type.name, vol_type.id, vol_type.is_public,
                      vol_encryption, qos_spec)


def delete_volume_type(cinder, vol_type):
    """
    Deletes an volume from OpenStack
    :param cinder: the cinder client
    :param vol_type: the VolumeType domain object
    """
    logger.info('Deleting volume named - %s', vol_type.name)
    cinder.volume_types.delete(vol_type.id)


def get_volume_encryption_by_type(cinder, volume_type):
    """
    Returns an OpenStack volume type object for a given name
    :param cinder: the Cinder client
    :param volume_type: the VolumeType domain object
    :return: the VolumeEncryption domain object or None
    """
    os_vol_type = __get_os_volume_type_by_id(cinder, volume_type.id)
    encryption = cinder.volume_encryption_types.get(os_vol_type)
    if hasattr(encryption, 'encryption_id'):
        cipher = None
        if hasattr(encryption, 'cipher'):
            cipher = encryption.cipher
        key_size = None
        if hasattr(encryption, 'key_size'):
            key_size = encryption.key_size
        return VolumeTypeEncryption(
            encryption.encryption_id, encryption.volume_type_id,
            encryption.control_location, encryption.provider, cipher, key_size)


def create_volume_encryption(cinder, volume_type, encryption_settings):
    """
    Creates and returns OpenStack volume type object with an external URL
    :param cinder: the cinder client
    :param volume_type: the VolumeType object to associate the encryption
    :param encryption_settings: the volume type encryption settings object
    :return: the VolumeTypeEncryption domain object
    """
    specs = {'name': encryption_settings.name,
             'provider': encryption_settings.provider_class}
    if encryption_settings.key_size:
        specs['key_size'] = encryption_settings.key_size
    if encryption_settings.provider_class:
        specs['provider_class'] = encryption_settings.provider_class
    if encryption_settings.control_location:
        specs['control_location'] = encryption_settings.control_location.value
    if encryption_settings.cipher:
        specs['cipher'] = encryption_settings.cipher

    encryption = cinder.volume_encryption_types.create(volume_type.id, specs)

    cipher = None
    if hasattr(encryption, 'cipher'):
        cipher = encryption.cipher
    key_size = None
    if hasattr(encryption, 'key_size'):
        key_size = encryption.key_size
    return VolumeTypeEncryption(
        encryption.encryption_id, encryption.volume_type_id,
        encryption.control_location, encryption.provider, cipher, key_size)


def delete_volume_type_encryption(cinder, vol_type):
    """
    Deletes an volume from OpenStack
    :param cinder: the cinder client
    :param vol_type: the associated VolumeType domain object
    """
    logger.info('Deleting volume encryption for volume type - %s',
                vol_type.name)
    os_vol_type = __get_os_volume_type_by_id(cinder, vol_type.id)
    cinder.volume_encryption_types.delete(os_vol_type)


def __get_os_qos(cinder, qos_name=None, qos_settings=None):
    """
    Returns an OpenStack QoS object for a given name
    :param cinder: the Cinder client
    :param qos_name: the qos name to lookup
    :param qos_settings: the qos settings used for lookups
    :return: the qos object or None
    """
    if not qos_name and not qos_settings:
        return None

    if qos_settings:
        qos_name = qos_settings.name

    qoss = cinder.qos_specs.list()
    for qos in qoss:
        if qos.name == qos_name:
            return qos


def get_qos(cinder, qos_name=None, qos_settings=None):
    """
    Returns an OpenStack QoS object for a given name
    :param cinder: the Cinder client
    :param qos_name: the qos name to lookup
    :param qos_settings: the qos settings used for lookups
    :return: the qos object or None
    """
    os_qos = __get_os_qos(cinder, qos_name, qos_settings)
    if os_qos:
        return QoSSpec(name=os_qos.name, spec_id=os_qos.id,
                       consumer=os_qos.consumer)


def get_qos_by_id(cinder, qos_id):
    """
    Returns an OpenStack qos object for a given name
    :param cinder: the Cinder client
    :param qos_id: the qos ID to lookup
    :return: the SNAPS-OO Domain Volume object or None
    """
    qos = cinder.qos_specs.get(qos_id)
    return QoSSpec(name=qos.name, spec_id=qos.id, consumer=qos.consumer)


def create_qos(cinder, qos_settings):
    """
    Creates and returns OpenStack qos object with an external URL
    :param cinder: the cinder client
    :param qos_settings: the qos settings object
    :return: the qos domain object
    :raise Exception if using a file and it cannot be found
    """
    specs = qos_settings.specs
    specs['consumer'] = qos_settings.consumer.value
    qos = cinder.qos_specs.create(qos_settings.name, qos_settings.specs)
    return QoSSpec(name=qos.name, spec_id=qos.id, consumer=qos.consumer)


def delete_qos(cinder, qos):
    """
    Deletes an QoS from OpenStack
    :param cinder: the cinder client
    :param qos: the qos domain object to delete
    """
    logger.info('Deleting QoS named - %s', qos.name)
    cinder.qos_specs.delete(qos.id)


class KeystoneUtilsException(Exception):
    """
    Exception when calls to the Keystone client cannot be served properly
    """
