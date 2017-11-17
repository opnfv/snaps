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
import unittest

from snaps.config.qos import QoSConfig, QoSConfigError, Consumer


class QoSConfigUnitTests(unittest.TestCase):
    """
    Tests the construction of the QoSConfig class
    """

    def test_no_params(self):
        with self.assertRaises(QoSConfigError):
            QoSConfig()

    def test_empty_config(self):
        with self.assertRaises(QoSConfigError):
            QoSConfig(**dict())

    def test_name_only(self):
        with self.assertRaises(QoSConfigError):
            QoSConfig(name='foo')

    def test_config_with_name_only(self):
        with self.assertRaises(QoSConfigError):
            QoSConfig(**{'name': 'foo'})

    def test_invalid_consumer(self):
        with self.assertRaises(QoSConfigError):
            QoSConfig(name='foo', consumer='bar')

    def test_config_with_invalid_consumer(self):
        with self.assertRaises(QoSConfigError):
            QoSConfig(**{'name': 'foo', 'consumer': 'bar'})

    def test_name_consumer(self):
        settings = QoSConfig(name='foo', consumer=Consumer.front_end)

        self.assertEqual('foo', settings.name)
        self.assertEqual(Consumer.front_end, settings.consumer)
        self.assertEqual(dict(), settings.specs)

    def test_name_consumer_front_end_strings(self):
        settings = QoSConfig(name='foo', consumer='front-end')

        self.assertEqual('foo', settings.name)
        self.assertEqual(Consumer.front_end, settings.consumer)
        self.assertEqual(dict(), settings.specs)

    def test_name_consumer_back_end_strings(self):
        settings = QoSConfig(name='foo', consumer='back-end')

        self.assertEqual('foo', settings.name)
        self.assertEqual(Consumer.back_end, settings.consumer)
        self.assertEqual(dict(), settings.specs)

    def test_name_consumer_both_strings(self):
        settings = QoSConfig(name='foo', consumer='both')

        self.assertEqual('foo', settings.name)
        self.assertEqual(Consumer.both, settings.consumer)
        self.assertEqual(dict(), settings.specs)

    def test_all(self):
        specs = {'spec1': 'val1', 'spec2': 'val2'}
        settings = QoSConfig(name='foo', consumer=Consumer.both, specs=specs)

        self.assertEqual('foo', settings.name)
        self.assertEqual(Consumer.both, settings.consumer)
        self.assertEqual(specs, settings.specs)

    def test_config_all(self):
        settings = QoSConfig(
            **{'name': 'foo', 'consumer': 'both', 'specs': {'spec1': 'val1'}})

        self.assertEqual('foo', settings.name)
        self.assertEqual(Consumer.both, settings.consumer)
        self.assertEqual({'spec1': 'val1'}, settings.specs)
