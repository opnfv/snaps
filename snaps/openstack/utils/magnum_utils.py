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

from magnumclient.client import Client

from snaps.openstack.utils import keystone_utils

__author__ = 'spisarski'

logger = logging.getLogger('heat_utils')


def magnum_client(os_creds):
    """
    Retrieves the Heat client
    :param os_creds: the OpenStack credentials
    :return: the client
    """
    logger.debug('Retrieving Nova Client')
    return Client(session=keystone_utils.keystone_session(os_creds))