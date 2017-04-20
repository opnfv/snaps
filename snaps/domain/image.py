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


class Image:
    """
    SNAPS domain object for Images. Should contain attributes that
    are shared amongst cloud providers
    """
    def __init__(self, name, image_id, size, properties=None):
        """
        Constructor
        :param name: the image's name
        :param image_id: the image's id
        :param size: the size of the image in bytes
        :param properties: the image's custom properties
        """
        self.name = name
        self.id = image_id
        self.size = size
        self.properties = properties
