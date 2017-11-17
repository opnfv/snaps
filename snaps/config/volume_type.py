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
import enum
from neutronclient.common.utils import str2bool


class VolumeTypeConfig(object):
    def __init__(self, **kwargs):
        """
        Constructor
        :param name: the volume's name (required)
        :param description: the volume's name (optional)
        :param encryption: VolumeTypeEncryptionConfig (optional)
        :param qos_spec_name: name of the QoS Spec to associate (optional)
        :param public: volume visibility where True denotes global
                       (default - False)

        TODO - Implement project_access parameter that will associate this
        VolumeType to a list of project names
        """

        self.name = kwargs.get('name')
        self.description = kwargs.get('description')
        self.qos_spec_name = kwargs.get('qos_spec_name')

        if 'encryption' in kwargs:
            if isinstance(kwargs['encryption'], dict):
                self.encryption = VolumeTypeEncryptionConfig(
                    **kwargs['encryption'])
            elif isinstance(kwargs['encryption'],
                            VolumeTypeEncryptionConfig):
                self.encryption = kwargs['encryption']
        else:
            self.encryption = None

        if 'public' in kwargs:
            if isinstance(kwargs['public'], str):
                self.public = str2bool(kwargs['public'])
            else:
                self.public = kwargs['public']
        else:
            self.public = False

        if not self.name:
            raise VolumeTypeConfigError("The attribute name is required")

    def __eq__(self, other):
        return (self.name == other.name
                and self.description == other.description
                and self.qos_spec_name == other.qos_spec_name
                and self.encryption == other.encryption
                and self.public == other.public)


class ControlLocation(enum.Enum):
    """
    QoS Specification consumer types
    """
    front_end = 'front-end'
    back_end = 'back-end'


class VolumeTypeEncryptionConfig(object):
    def __init__(self, **kwargs):
        """
        Constructor
        :param name: the volume's name (required)
        :param provider_class: the volume's provider class (e.g. LuksEncryptor)
        :param control_location: the notional service where encryption is
                                 performed (e.g., front-end=Nova). The default
                                 value is 'front-end.'
        :param cipher: the encryption algorithm/mode to use
                       (e.g., aes-xts-plain64). If the field is left empty,
                       the provider default will be used
        :param key_size: the size of the encryption key, in bits
                         (e.g., 128, 256). If the field is left empty, the
                         provider default will be used
        """

        self.name = kwargs.get('name')
        self.provider_class = kwargs.get('provider_class')
        self.control_location = kwargs.get('control_location')
        if kwargs.get('control_location'):
            self.control_location = map_control_location(
                kwargs['control_location'])
        else:
            self.control_location = None

        self.cipher = kwargs.get('cipher')
        self.key_size = kwargs.get('key_size')

        if (not self.name or not self.provider_class
                or not self.control_location):
            raise VolumeTypeConfigError(
                'The attributes name, provider_class, and control_location '
                'are required')

    def __eq__(self, other):
        return (self.name == other.name
                and self.provider_class == other.provider_class
                and self.control_location == other.control_location
                and self.cipher == other.cipher
                and self.key_size == other.key_size)


def map_control_location(control_location):
    """
    Takes a the protocol value maps it to the Consumer enum. When None return
    None
    :param control_location: the value to map to the Enum
    :return: a ControlLocation enum object
    :raise: Exception if control_location parameter is invalid
    """
    if not control_location:
        return None
    elif isinstance(control_location, ControlLocation):
        return control_location
    else:
        proto_str = str(control_location)
        if proto_str == 'front-end':
            return ControlLocation.front_end
        elif proto_str == 'back-end':
            return ControlLocation.back_end
        else:
            raise VolumeTypeConfigError('Invalid Consumer - ' + proto_str)


class VolumeTypeConfigError(Exception):
    """
    Exception to be thrown when an volume settings are incorrect
    """

    def __init__(self, message):
        Exception.__init__(self, message)
