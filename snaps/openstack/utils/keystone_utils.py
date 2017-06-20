# Copyright (c) 2016 Cable Television Laboratories, Inc. ("CableLabs")
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
import requests
from keystoneclient.client import Client
from keystoneauth1.identity import v3, v2
from keystoneauth1 import session
import logging
import os
from oslo_utils import strutils


logger = logging.getLogger('keystone_utils')

V2_VERSION = 'v2.0'


def get_session_auth(os_creds):
    """
    Return the session auth for keystone session
    :param os_creds: the OpenStack credentials (OSCreds) object
    :return: the auth
    """
    if os_creds.identity_api_version == 3:
        auth = v3.Password(auth_url=os_creds.auth_url,
                           username=os_creds.username,
                           password=os_creds.password,
                           project_name=os_creds.project_name,
                           user_domain_id=os_creds.user_domain_id,
                           project_domain_id=os_creds.project_domain_id)
    else:
        auth = v2.Password(auth_url=os_creds.auth_url,
                           username=os_creds.username,
                           password=os_creds.password,
                           tenant_name=os_creds.project_name)
    return auth


def keystone_session(os_creds):
    """
    Creates a keystone session used for authenticating OpenStack clients
    :param os_creds: The connection credentials to the OpenStack API
    :return: the client object
    """
    logger.debug('Retrieving Keystone Session')

    auth = get_session_auth(os_creds)

    req_session = None
    if os_creds.proxy_settings:
        req_session = requests.Session()
        req_session.proxies = {'http': os_creds.proxy_settings.host + ':' + os_creds.proxy_settings.port}
    https_cacert = os.getenv('OS_CACERT', '')
    https_insecure = strutils.bool_from_string(
        os.environ.get("OS_INSECURE"))
    return session.Session(auth=auth, session=req_session,
                           verify=(https_cacert or not https_insecure))


def keystone_client(os_creds):
    """
    Returns the keystone client
    :param os_creds: the OpenStack credentials (OSCreds) object
    :return: the client
    """
    return Client(version=os_creds.identity_api_version, session=keystone_session(os_creds))


def get_endpoint(os_creds, service_type, endpoint_type='publicURL'):
    """
    Returns the endpoint of specific service
    :param os_creds: the OpenStack credentials (OSCreds) object
    :param service_type: the type of specific service
    :param endpoint_type: the type of endpoint
    :return: the endpoint url
    """
    auth = get_session_auth(os_creds)
    key_session = keystone_session(os_creds)
    return key_session.get_endpoint(auth=auth, service_type=service_type, endpoint_type=endpoint_type)


def get_project(keystone=None, os_creds=None, project_name=None):
    """
    Returns the first project object or None if not found
    :param keystone: the Keystone client
    :param os_creds: the OpenStack credentials used to obtain the Keystone client if the keystone parameter is None
    :param project_name: the name to query
    :return: the ID or None
    """
    if not project_name:
        return None

    if not keystone:
        if os_creds:
            keystone = keystone_client(os_creds)
        else:
            raise Exception('Cannot lookup project without the proper credentials')

    if keystone.version == V2_VERSION:
        projects = keystone.tenants.list()
    else:
        projects = keystone.projects.list(**{'name': project_name})

    for project in projects:
        if project.name == project_name:
            return project

    return None


def create_project(keystone, project_settings):
    """
    Creates a project
    :param keystone: the Keystone client
    :param project_settings: the project configuration
    :return:
    """
    if keystone.version == V2_VERSION:
        return keystone.tenants.create(project_settings.name, project_settings.description, project_settings.enabled)

    return keystone.projects.create(project_settings.name, project_settings.domain,
                                    description=project_settings.description,
                                    enabled=project_settings.enabled)


def delete_project(keystone, project):
    """
    Deletes a project
    :param keystone: the Keystone clien
    :param project: the OpenStack project object
    """
    if keystone.version == V2_VERSION:
        keystone.tenants.delete(project)
    else:
        keystone.projects.delete(project)


def get_user(keystone, username, project_name=None):
    """
    Returns a user for a given name and optionally project
    :param keystone: the keystone client
    :param username: the username to lookup
    :param project_name: the associated project (optional)
    :return:
    """
    project = get_project(keystone=keystone, project_name=project_name)

    if project:
        users = keystone.users.list(tenant_id=project.id)
    else:
        users = keystone.users.list()

    for user in users:
        if user.name == username:
            return user

    return None


def create_user(keystone, user_settings):
    """
    Creates a user
    :param keystone: the Keystone client
    :param user_settings: the user configuration
    :return:
    """
    project = None
    if user_settings.project_name:
        project = get_project(keystone=keystone, project_name=user_settings.project_name)

    if keystone.version == V2_VERSION:
        project_id = None
        if project:
            project_id = project.id
        return keystone.users.create(name=user_settings.name, password=user_settings.password,
                                     email=user_settings.email, tenant_id=project_id, enabled=user_settings.enabled)
    else:
        # TODO - need to support groups
        return keystone.users.create(name=user_settings.name, password=user_settings.password,
                                     email=user_settings.email, project=project,
                                     # email=user_settings.email, project=project, group='default',
                                     domain=user_settings.domain_name,
                                     enabled=user_settings.enabled)


def delete_user(keystone, user):
    """
    Deletes a user
    :param keystone: the Keystone client
    :param user: the OpenStack user object
    """
    keystone.users.delete(user)


def create_role(keystone, name):
    """
    Creates an OpenStack role
    :param keystone: the keystone client
    :param name: the role name
    :return:
    """
    return keystone.roles.create(name)


def delete_role(keystone, role):
    """
    Deletes an OpenStack role
    :param keystone: the keystone client
    :param role: the role to delete
    :return:
    """
    keystone.roles.delete(role)


def assoc_user_to_project(keystone, role, user, project):
    """
    Adds a user to a project
    :param keystone: the Keystone client
    :param role: the role used to join a project/user
    :param user: the user to add to the project
    :param project: the project to which to add a user
    :return:
    """
    if keystone.version == V2_VERSION:
        keystone.roles.add_user_role(user, role, tenant=project)
    else:
        keystone.roles.grant(role, user=user, project=project)
