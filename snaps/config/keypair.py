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


class KeypairConfig(object):
    """
    Class representing a keypair configuration
    """

    def __init__(self, **kwargs):
        """
        Constructor - all parameters are optional
        :param name: The keypair name.
        :param public_filepath: The path to/from the filesystem where the
                                public key file is or will be stored
        :param private_filepath: The path where the generated private key file
                                 will be stored
        :param key_size: The number of bytes for the key size when it needs to
                         be generated (Must be >=512 default 1024)
        :param delete_on_clean: when True, the key files will be deleted when
                                OpenStackKeypair#clean() is called
        :return:
        """

        self.name = kwargs.get('name')
        self.public_filepath = kwargs.get('public_filepath')
        self.private_filepath = kwargs.get('private_filepath')
        self.key_size = int(kwargs.get('key_size', 1024))

        if kwargs.get('delete_on_clean') is not None:
            if isinstance(kwargs.get('delete_on_clean'), bool):
                self.delete_on_clean = kwargs.get('delete_on_clean')
            else:
                self.delete_on_clean = str2bool(kwargs.get('delete_on_clean'))
        else:
            self.delete_on_clean = None

        if not self.name:
            raise KeypairConfigError('Name is a required attribute')

        if self.key_size < 512:
            raise KeypairConfigError('key_size must be >=512')


class KeypairConfigError(Exception):
    """
    Exception to be thrown when keypair settings are incorrect
    """
