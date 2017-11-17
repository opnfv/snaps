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


class Consumer(enum.Enum):
    """
    QoS Specification consumer types
    """
    front_end = 'front-end'
    back_end = 'back-end'
    both = 'both'


class QoSConfig(object):
    def __init__(self, **kwargs):
        """
        Constructor
        :param name: the qos's name (required)
        :param consumer: the qos's consumer type of the enum type Consumer
                         (required)
        :param specs: dict of key/values
        """

        self.name = kwargs.get('name')

        if kwargs.get('consumer'):
            self.consumer = map_consumer(kwargs['consumer'])
        else:
            self.consumer = None

        self.specs = kwargs.get('specs')
        if not self.specs:
            self.specs = dict()

        if not self.name or not self.consumer:
            raise QoSConfigError(
                "The attributes name and consumer are required")


def map_consumer(consumer):
    """
    Takes a the protocol value maps it to the Consumer enum. When None return
    None
    :param consumer: the value to map to the Enum
    :return: the Protocol enum object
    :raise: Exception if value is invalid
    """
    if not consumer:
        return None
    elif isinstance(consumer, Consumer):
        return consumer
    elif isinstance(consumer, str):
        proto_str = str(consumer)
        if proto_str == 'front-end':
            return Consumer.front_end
        elif proto_str == 'back-end':
            return Consumer.back_end
        elif proto_str == 'both':
            return Consumer.both
        else:
            raise QoSConfigError('Invalid Consumer - ' + proto_str)
    else:
        if consumer.value == 'front-end':
            return Consumer.front_end
        elif consumer.value == 'back-end':
            return Consumer.back_end
        elif consumer.value == 'both':
            return Consumer.both
        else:
            raise QoSConfigError('Invalid Consumer - ' + consumer.value)


class QoSConfigError(Exception):
    """
    Exception to be thrown when an qos settings are incorrect
    """

    def __init__(self, message):
        Exception.__init__(self, message)
