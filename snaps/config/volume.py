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
from neutronclient.common.utils import str2bool


class VolumeConfig(object):
    def __init__(self, **kwargs):
        """
        Constructor
        :param name: the volume's name (required)
        :param project_name: the name of the project to associate (optional)
            note: due to a bug in the Cinder API, this functionality will not
            work. see https://bugs.launchpad.net/cinder/+bug/1641982
        :param description: the volume's name (optional)
        :param size: the volume's size in GB (default 1)
        :param image_name: when a glance image is used for the image source
                           (optional)
        :param type_name: the associated volume's type name (optional)
        :param availability_zone: the name of the compute server on which to
                                  deploy the volume (optional)
        :param multi_attach: when true, volume can be attached to more than one
                             server (default False)
        """

        self.name = kwargs.get('name')
        self.project_name = kwargs.get('project_name')
        self.description = kwargs.get('description')
        self.size = int(kwargs.get('size', 1))
        self.image_name = kwargs.get('image_name')
        self.type_name = kwargs.get('type_name')
        self.availability_zone = kwargs.get('availability_zone')

        if kwargs.get('multi_attach'):
            self.multi_attach = str2bool(str(kwargs.get('multi_attach')))
        else:
            self.multi_attach = False

        if not self.name:
            raise VolumeConfigError("The attribute name is required")


class VolumeConfigError(Exception):
    """
    Exception to be thrown when an volume settings are incorrect
    """

    def __init__(self, message):
        Exception.__init__(self, message)
