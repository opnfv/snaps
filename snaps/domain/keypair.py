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


class Keypair:
    """
    SNAPS domain object for Keypairs. Should contain attributes that
    are shared amongst cloud providers
    """
    def __init__(self, name, kp_id, public_key, fingerprint=None):
        """
        Constructor
        :param name: the keypair's name
        :param kp_id: the keypair's id
        :param public_key: the keypair's public key
        :param fingerprint: the keypair's host fingerprint
        """
        self.name = name
        self.id = kp_id
        self.public_key = public_key
        self.fingerprint = fingerprint

    def __eq__(self, other):
        return (self.name == other.name and self.id == other.id and
                self.public_key == other.public_key)
