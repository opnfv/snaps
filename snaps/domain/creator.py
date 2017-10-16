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

__author__ = 'spisarski'


class CloudObject(object):
    """
    Base class for all cloud objects to create or manage
    """

    def initialize(self):
        """
        Method used to initialize object via queries
        :return:
        """
        raise NotImplementedError('Please implement this abstract method')

    def create(self):
        """
        Method to be called to create this cloud object. First line should
        generally be a call to initialize()
        :return:
        """
        raise NotImplementedError('Please implement this abstract method')

    def clean(self):
        """
        Method used to delete objects on the cloud
        :return:
        """
        raise NotImplementedError('Please implement this abstract method')
