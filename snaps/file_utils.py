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

import os
import logging

from cryptography.hazmat.primitives import serialization

try:
    import urllib.request as urllib
except ImportError:
    import urllib2 as urllib

import yaml

__author__ = 'spisarski'

"""
Utilities for basic file handling
"""

logger = logging.getLogger('file_utils')


def file_exists(file_path):
    """
    Returns True if the image file already exists and throws an exception if
    the path is a directory
    :return:
    """
    expanded_path = os.path.expanduser(file_path)
    if os.path.exists(expanded_path):
        if os.path.isdir(expanded_path):
            return False
        return os.path.isfile(expanded_path)
    return False


def download(url, dest_path, name=None):
    """
    Download a file to a destination path given a URL
    :param url: the endpoint to the file to download
    :param dest_path: the directory to save the file
    :param name: the file name (optional)
    :rtype : File object
    """
    if not name:
        name = url.rsplit('/')[-1]
    dest = dest_path + '/' + name
    logger.debug('Downloading file from - ' + url)
    # Override proxy settings to use localhost to download file
    download_file = None

    if not os.path.isdir(dest_path):
        try:
            os.mkdir(dest_path)
        except:
            raise
    try:
        with open(dest, 'wb') as download_file:
            logger.debug('Saving file to - %s',
                         os.path.abspath(download_file.name))
            response = __get_url_response(url)
            download_file.write(response.read())
        return download_file
    finally:
        if download_file:
            download_file.close()


def save_keys_to_files(keys=None, pub_file_path=None, priv_file_path=None):
    """
    Saves the generated RSA generated keys to the filesystem
    :param keys: the keys to save generated by cryptography
    :param pub_file_path: the path to the public keys
    :param priv_file_path: the path to the private keys
    """
    if keys:
        if pub_file_path:
            # To support '~'
            pub_expand_file = os.path.expanduser(pub_file_path)
            pub_dir = os.path.dirname(pub_expand_file)

            if not os.path.isdir(pub_dir):
                os.mkdir(pub_dir)

            public_handle = None
            try:
                public_handle = open(pub_expand_file, 'wb')
                public_bytes = keys.public_key().public_bytes(
                    serialization.Encoding.OpenSSH,
                    serialization.PublicFormat.OpenSSH)
                public_handle.write(public_bytes)
            finally:
                if public_handle:
                    public_handle.close()

            os.chmod(pub_expand_file, 0o400)
            logger.info("Saved public key to - " + pub_expand_file)
        if priv_file_path:
            # To support '~'
            priv_expand_file = os.path.expanduser(priv_file_path)
            priv_dir = os.path.dirname(priv_expand_file)
            if not os.path.isdir(priv_dir):
                os.mkdir(priv_dir)

            private_handle = None
            try:
                private_handle = open(priv_expand_file, 'wb')
                private_handle.write(
                    keys.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.TraditionalOpenSSL,
                        encryption_algorithm=serialization.NoEncryption()))
            finally:
                if private_handle:
                    private_handle.close()

            os.chmod(priv_expand_file, 0o400)
            logger.info("Saved private key to - " + priv_expand_file)


def save_string_to_file(string, file_path, mode=None):
    """
    Stores
    :param string: the string contents to store
    :param file_path: the file path to create
    :param mode: the file's mode
    :return: the file object
    """
    save_file = open(file_path, 'w')
    try:
        save_file.write(string)
        if mode:
            os.chmod(file_path, mode)
        return save_file
    finally:
        save_file.close()


def get_content_length(url):
    """
    Returns the number of bytes to be downloaded from the given URL
    :param url: the URL to inspect
    :return: the number of bytes
    """
    response = __get_url_response(url)
    return response.headers['Content-Length']


def __get_url_response(url):
    """
    Returns a response object for a given URL
    :param url: the URL
    :return: the response
    """
    proxy_handler = urllib.ProxyHandler({})
    opener = urllib.build_opener(proxy_handler)
    urllib.install_opener(opener)
    return urllib.urlopen(url)


def read_yaml(config_file_path):
    """
    Reads the yaml file and returns a dictionary object representation
    :param config_file_path: The file path to config
    :return: a dictionary
    """
    logger.debug('Attempting to load configuration file - ' + config_file_path)
    config_file = None
    try:
        with open(config_file_path, 'r') as config_file:
            config = yaml.safe_load(config_file)
            logger.info('Loaded configuration')
        return config
    finally:
        if config_file:
            logger.info('Closing configuration file')
            config_file.close()


def persist_dict_to_yaml(the_dict, file_name):
    """
    Creates a YAML file from a dict
    :param the_dict: the dictionary to store
    :param conf_dir: the directory used to store the config file
    :return: the file object
    """
    logger.info('Persisting %s to [%s]', the_dict, file_name)
    file_path = os.path.expanduser(file_name)
    yaml_from_dict = yaml.dump(
        the_dict, default_flow_style=False, default_style='')
    return save_string_to_file(yaml_from_dict, file_path)


def read_os_env_file(os_env_filename):
    """
    Reads the OS environment source file and returns a map of each key/value
    Will ignore lines beginning with a '#' and will replace any single or
    double quotes contained within the value
    :param os_env_filename: The name of the OS environment file to read
    :return: a dictionary
    """
    if os_env_filename:
        logger.info('Attempting to read OS environment file - %s',
                    os_env_filename)
        out = {}
        env_file = None
        try:
            env_file = open(os_env_filename)
            for line in env_file:
                line = line.lstrip()
                if not line.startswith('#') and line.startswith('export '):
                    line = line.lstrip('export ').strip()
                    tokens = line.split('=')
                    if len(tokens) > 1:
                        # Remove leading and trailing ' & " characters from
                        # value
                        out[tokens[0]] = tokens[1].lstrip('\'').lstrip('\"').rstrip('\'').rstrip('\"')
        finally:
            if env_file:
                env_file.close()
        return out


def read_file(filename):
    """
    Returns the contents of a file as a string
    :param filename: the name of the file
    :return:
    """
    out = str()
    the_file = None
    try:
        the_file = open(filename)
        for line in the_file:
            out += line
        return out
    finally:
        if the_file:
            the_file.close()
