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
    if os.path.exists(file_path):
        if os.path.isdir(file_path):
            return False
        return os.path.isfile(file_path)
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
            logger.debug('Saving file to - ' + os.path.abspath(download_file.name))
            response = __get_url_response(url)
            download_file.write(response.read())
        return download_file
    finally:
        if download_file:
            download_file.close()


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
        with open(config_file_path) as config_file:
            config = yaml.safe_load(config_file)
            logger.info('Loaded configuration')
        return config
    finally:
        if config_file:
            logger.info('Closing configuration file')
            config_file.close()


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
