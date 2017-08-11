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


class Stack:
    """
    SNAPS domain object for Heat Stacks. Should contain attributes that
    are shared amongst cloud providers
    """
    def __init__(self, name, stack_id):
        """
        Constructor
        :param name: the stack's name
        :param stack_id: the stack's stack_id
        """
        self.name = name
        self.id = stack_id

    def __eq__(self, other):
        return (self.name == other.name and
                self.id == other.id)


class Resource:
    """
    SNAPS domain object for resources created by a heat template
    """
    def __init__(self, resource_type, resource_id):
        """
        Constructor
        :param resource_type: the type
        :param resource_id: the ID attached to the resource of the given type
        """
        self.type = resource_type
        self.id = resource_id
