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

from snaps.domain.volume import QoSSpec
from snaps.openstack.utils import keystone_utils

__author__ = 'spisarski'

logger = logging.getLogger('cinder_utils')

VERSION_1 = 1
VERSION_2 = 2
VERSION_3 = 3

"""
Utilities for basic neutron API calls
"""


def cinder_client(os_creds):
    """
    Creates and returns a cinder client object
    :return: the cinder client
    """
    return Client(version=os_creds.volume_api_version,
                  session=keystone_utils.keystone_session(os_creds),
                  region_name=os_creds.region_name)


def get_qos(cinder, qos_name=None, qos_settings=None):
    """
    Returns an OpenStack QoS object for a given name
    :param cinder: the Cinder client
    :param qos_name: the qos name to lookup
    :param qos_settings: the qos settings used for lookups
    :return: the qos object or None
    """
    if not qos_name and not qos_settings:
        return None

    qos_name = qos_name
    if qos_settings:
        qos_name = qos_settings.name

    qoss = cinder.qos_specs.list()
    for qos in qoss:
        if qos.name == qos_name:
            if qos_settings:
                if qos_settings.consumer.value == qos.consumer:
                    return QoSSpec(name=qos.name, spec_id=qos.id,
                                   consumer=qos.consumer)
            else:
                return QoSSpec(name=qos.name, spec_id=qos.id,
                               consumer=qos.consumer)


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


class CinderException(Exception):
    """
    Exception when calls to the Cinder client cannot be served properly
    """
