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

STACK_DELETE_TIMEOUT = 1200
STACK_COMPLETE_TIMEOUT = 1200
POLL_INTERVAL = 3
STATUS_CREATE_FAILED = 'CREATE_FAILED'
STATUS_CREATE_COMPLETE = 'CREATE_COMPLETE'
STATUS_DELETE_COMPLETE = 'DELETE_COMPLETE'
STATUS_DELETE_FAILED = 'DELETE_FAILED'


class StackConfig(object):
    """
    Configuration for Heat stack
    """

    def __init__(self, **kwargs):
        """
        Constructor
        :param name: the stack's name (required)
        :param template: the heat template in dict() format (required if
                         template_path attribute is None)
        :param template_path: the location of the heat template file (required
                              if template attribute is None)
        :param env_values: dict() of strings for substitution of template
                           default values (optional)
        :param files: Supplies the contents of files referenced in the template
                      or the environment. This object must be a dict() of
                      strings where the key is the file URI or filename and the
                      value contains the file's contents (optional)
        """

        self.name = kwargs.get('name')
        self.template = kwargs.get('template')
        self.template_path = kwargs.get('template_path')
        self.env_values = kwargs.get('env_values')
        self.files = kwargs.get('files')

        if 'stack_create_timeout' in kwargs:
            self.stack_create_timeout = kwargs['stack_create_timeout']
        else:
            self.stack_create_timeout = STACK_COMPLETE_TIMEOUT

        if not self.name:
            raise StackConfigError('name is required')

        if not self.template and not self.template_path:
            raise StackConfigError('A Heat template is required')

    def __eq__(self, other):
        return (self.name == other.name and
                self.template == other.template and
                self.template_path == other.template_path and
                self.env_values == other.env_values and
                self.stack_create_timeout == other.stack_create_timeout)


class StackConfigError(Exception):
    """
    Exception to be thrown when an stack configuration are incorrect
    """
