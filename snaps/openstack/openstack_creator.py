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
from snaps.domain.creator import CloudObject
from snaps.openstack.utils import (
    nova_utils, neutron_utils, keystone_utils, cinder_utils, magnum_utils)

__author__ = 'spisarski'


class OpenStackCloudObject(CloudObject):
    """
    Abstract class for all OpenStack object creators
    """

    def __init__(self, os_creds):
        """
        Constructor
        :param os_creds: the OpenStack credentials object
        """
        self._os_creds = os_creds
        self._os_session = None
        self._keystone = None

    def initialize(self):
        self._os_session = keystone_utils.keystone_session(self._os_creds)
        self._keystone = keystone_utils.keystone_client(
            self._os_creds, session=self._os_session)

    def create(self):
        raise NotImplementedError('Do not override abstract method')

    def clean(self):
        if self._os_session:
            keystone_utils.close_session(self._os_session)


class OpenStackComputeObject(OpenStackCloudObject):
    """
    Abstract class for all OpenStack compute creators
    """

    def __init__(self, os_creds):
        """
        Constructor
        :param os_creds: the OpenStack credentials object
        """
        super(OpenStackComputeObject, self).__init__(os_creds)
        self._nova = None

    def initialize(self):
        super(OpenStackComputeObject, self).initialize()
        self._nova = nova_utils.nova_client(self._os_creds, self._os_session)

    def create(self):
        raise NotImplementedError('Do not override abstract method')


class OpenStackNetworkObject(OpenStackCloudObject):
    """
    Abstract class for all OpenStack compute creators
    """

    def __init__(self, os_creds):
        """
        Constructor
        :param os_creds: the OpenStack credentials object
        """
        super(OpenStackNetworkObject, self).__init__(os_creds)
        self._neutron = None

    def initialize(self):
        super(OpenStackNetworkObject, self).initialize()
        self._neutron = neutron_utils.neutron_client(
            self._os_creds, self._os_session)

    def create(self):
        raise NotImplementedError('Do not override abstract method')


class OpenStackIdentityObject(OpenStackCloudObject):
    """
    Abstract class for all OpenStack compute creators
    """

    def __init__(self, os_creds):
        """
        Constructor
        :param os_creds: the OpenStack credentials object
        """
        super(OpenStackIdentityObject, self).__init__(os_creds)

    def initialize(self):
        super(OpenStackIdentityObject, self).initialize()

    def create(self):
        raise NotImplementedError('Do not override abstract method')


class OpenStackVolumeObject(OpenStackCloudObject):
    """
    Abstract class for all OpenStack compute creators
    """

    def __init__(self, os_creds):
        """
        Constructor
        :param os_creds: the OpenStack credentials object
        """
        super(OpenStackVolumeObject, self).__init__(os_creds)
        self._cinder = None

    def initialize(self):
        super(OpenStackVolumeObject, self).initialize()
        self._cinder = cinder_utils.cinder_client(
            self._os_creds, self._os_session)

    def create(self):
        raise NotImplementedError('Do not override abstract method')


class OpenStackMagnumObject(OpenStackCloudObject):
    """
    Abstract class for all OpenStack compute creators
    """

    def __init__(self, os_creds):
        """
        Constructor
        :param os_creds: the OpenStack credentials object
        """
        super(OpenStackMagnumObject, self).__init__(os_creds)
        self._magnum = None

    def initialize(self):
        super(OpenStackMagnumObject, self).initialize()
        self._magnum = magnum_utils.magnum_client(
            self._os_creds, self._os_session)

    def create(self):
        raise NotImplementedError('Do not override abstract method')
