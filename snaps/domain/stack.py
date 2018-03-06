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
    def __init__(self, name, stack_id, stack_project_id,
                 status, status_reason):
        """
        Constructor
        :param name: the stack's name
        :param stack_id: the stack's stack_id
        :param stack_project_id: the project ID that was spawned from this
                                 deployment
        :param status: the stack's last known status code
        :param status_reason: the stack's last known explanation of the status
        """
        self.name = name
        self.id = stack_id
        self.stack_project_id = stack_project_id
        self.status = status
        self.status_reason = status_reason

    def __eq__(self, other):
        return (self.name == other.name and
                self.id == other.id)


class Resource:
    """
    SNAPS domain object for a resource created by a heat template
    """
    def __init__(self, name, resource_type, resource_id, status,
                 status_reason):
        """
        Constructor
        :param name: the resource's name
        :param resource_type: the resource's type
        :param resource_id: the ID attached to the resource of the given type
        :param status: the resource's status code
        :param status_reason: the resource's status code reason
        """
        self.name = name
        self.type = resource_type
        self.id = resource_id
        self.status = status
        self.status_reason = status_reason


class Output:
    """
    SNAPS domain object for an output defined by a heat template
    """
    def __init__(self, **kwargs):
        """
        Constructor
        :param description: the output description
        :param output_key: the output's key
        """
        self.description = kwargs.get('description')
        self.key = kwargs.get('output_key')
        self.value = kwargs.get('output_value')
