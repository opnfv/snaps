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
from neutronclient.v2_0.client import _DictWithMeta

__author__ = 'spisarski'


def objects_equivalent(obj1, obj2):
    """
    Returns true if both objects are equivalent
    :param obj1:
    :param obj2:
    :return: T/F
    """
    if obj1 is None and obj2 is None:
        return True
    if type(obj1) is dict or type(obj1) is _DictWithMeta:
        return dicts_equivalent(obj1, obj2)
    elif type(obj1) is list:
        return lists_equivalent(obj1, obj2)
    else:
        return obj1 == obj2


def dicts_equivalent(dict1, dict2):
    """
    Returns true when each key/value pair is equal
    :param dict1: dict 1
    :param dict2: dict 2
    :return: T/F
    """
    if (type(dict1) is dict or type(dict1) is _DictWithMeta) and (type(dict2) is dict or type(dict2) is _DictWithMeta):
        for key, value1 in dict1.items():
            if not objects_equivalent(value1, dict2.get(key)):
                return False
        return True
    return False


def lists_equivalent(list1, list2):
    """
    Returns true when an item in list1 is also contained in list2
    :param list1: list 1
    :param list2: list 2
    :return: T/F
    """
    if len(list1) == len(list2) and type(list1) is list and type(list2) is list:
        for item1 in list1:
            has_equivalent = False
            for item2 in list2:
                has_equivalent = objects_equivalent(item1, item2)
                if has_equivalent:
                    break
            if not has_equivalent:
                return False
        return True
    return False
