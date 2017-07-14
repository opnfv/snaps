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
import logging

from keystoneclient.client import Client
from keystoneauth1.identity import v3, v2
from keystoneauth1 import session
import requests

from snaps.domain.project import Project
from snaps.domain.role import Role
from snaps.domain.user import User

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
        req_session.proxies = {
            'http':
                os_creds.proxy_settings.host + ':' +
                os_creds.proxy_settings.port}
    return session.Session(auth=auth, session=req_session,
                           verify=os_creds.cacert)


def keystone_client(os_creds):
    """
    Returns the keystone client
    :param os_creds: the OpenStack credentials (OSCreds) object
    :return: the client
    """
    return Client(
        version=os_creds.identity_api_version,
        session=keystone_session(os_creds), interface=os_creds.interface)


def get_endpoint(os_creds, service_type, interface='public'):
    """
    Returns the endpoint of specific service
    :param os_creds: the OpenStack credentials (OSCreds) object
    :param service_type: the type of specific service
    :param interface: the type of interface
    :return: the endpoint url
    """
    auth = get_session_auth(os_creds)
    key_session = keystone_session(os_creds)
    return key_session.get_endpoint(
        auth=auth, service_type=service_type, interface=interface)


def get_project(keystone=None, os_creds=None, project_name=None):
    """
    Returns the first project object or None if not found
    :param keystone: the Keystone client
    :param os_creds: the OpenStack credentials used to obtain the Keystone
                     client if the keystone parameter is None
    :param project_name: the name to query
    :return: the ID or None
    """
    if not project_name:
        return None

    if not keystone:
        if os_creds:
            keystone = keystone_client(os_creds)
        else:
            raise KeystoneException(
                'Cannot lookup project without the proper credentials')

    if keystone.version == V2_VERSION:
        projects = keystone.tenants.list()
    else:
        projects = keystone.projects.list(**{'name': project_name})

    for project in projects:
        if project.name == project_name:
            return Project(name=project.name, project_id=project.id)

    return None


def create_project(keystone, project_settings):
    """
    Creates a project
    :param keystone: the Keystone client
    :param project_settings: the project configuration
    :return: SNAPS-OO Project domain object
    """
    if keystone.version == V2_VERSION:
        return keystone.tenants.create(
            project_settings.name, project_settings.description,
            project_settings.enabled)

    return keystone.projects.create(
        project_settings.name, project_settings.domain,
        description=project_settings.description,
        enabled=project_settings.enabled)


def delete_project(keystone, project):
    """
    Deletes a project
    :param keystone: the Keystone clien
    :param project: the SNAPS-OO Project domain object
    """
    if keystone.version == V2_VERSION:
        keystone.tenants.delete(project.id)
    else:
        keystone.projects.delete(project.id)


def __get_os_user(keystone, user):
    """
    Returns the OpenStack user object
    :param keystone: the Keystone client object
    :param user: the SNAPS-OO User domain object
    :return:
    """
    return keystone.users.get(user.id)


def get_user(keystone, username, project_name=None):
    """
    Returns a user for a given name and optionally project
    :param keystone: the keystone client
    :param username: the username to lookup
    :param project_name: the associated project (optional)
    :return: a SNAPS-OO User domain object or None
    """
    project = get_project(keystone=keystone, project_name=project_name)

    if project:
        users = keystone.users.list(tenant_id=project.id)
    else:
        users = keystone.users.list()

    for user in users:
        if user.name == username:
            return User(name=user.name, user_id=user.id)

    return None


def create_user(keystone, user_settings):
    """
    Creates a user
    :param keystone: the Keystone client
    :param user_settings: the user configuration
    :return: a SNAPS-OO User domain object
    """
    project = None
    if user_settings.project_name:
        project = get_project(keystone=keystone,
                              project_name=user_settings.project_name)

    if keystone.version == V2_VERSION:
        project_id = None
        if project:
            project_id = project.id
        os_user = keystone.users.create(
            name=user_settings.name, password=user_settings.password,
            email=user_settings.email, tenant_id=project_id,
            enabled=user_settings.enabled)
    else:
        os_user = keystone.users.create(
            name=user_settings.name, password=user_settings.password,
            email=user_settings.email, project=project,
            domain=user_settings.domain_name, enabled=user_settings.enabled)

    for role_name, role_project in user_settings.roles.items():
        os_role = _get_os_role_by_name(keystone, role_name)
        os_project = get_project(keystone=keystone, project_name=role_project)

        if os_role and os_project:
            existing_roles = _get_os_roles_by_user(keystone, os_user,
                                                   os_project)
            found = False
            for role in existing_roles:
                if role.id == os_role.id:
                    found = True

            if not found:
                grant_user_role_to_project(
                    keystone=keystone, user=os_user, role=os_role,
                    project=os_project)

    if os_user:
        return User(name=os_user.name, user_id=os_user.id)


def delete_user(keystone, user):
    """
    Deletes a user
    :param keystone: the Keystone client
    :param user: the SNAPS-OO User domain object
    """
    keystone.users.delete(user.id)


def _get_os_role_by_name(keystone, name):
    """
    Returns an OpenStack role object of a given name or None if not exists
    :param keystone: the keystone client
    :param name: the role name
    :return: the SNAPS-OO Role domain object
    """
    roles = keystone.roles.list()
    for role in roles:
        if role.name == name:
            return Role(name=role.name, role_id=role.id)


def _get_os_roles_by_user(keystone, user, project):
    """
    Returns a list of OpenStack role object associated with a user
    :param keystone: the keystone client
    :param user: the OpenStack user object
    :param project: the OpenStack project object (only required for v2)
    :return: a list of SNAPS-OO Role domain objects
    """
    if keystone.version == V2_VERSION:
        os_user = __get_os_user(keystone, user)
        roles = keystone.roles.roles_for_user(os_user, project)
    else:
        roles = keystone.roles.list(user=user, project=project)

    out = list()
    for role in roles:
        out.append(Role(name=role.name, role_id=role.id))
    return out


def __get_os_role_by_id(keystone, role_id):
    """
    Returns an OpenStack role object of a given name or None if not exists
    :param keystone: the keystone client
    :param role_id: the role ID
    :return: a SNAPS-OO Role domain object
    """
    role = keystone.roles.get(role_id)
    return Role(name=role.name, role_id=role.id)


def create_role(keystone, name):
    """
    Creates an OpenStack role
    :param keystone: the keystone client
    :param name: the role name
    :return: a SNAPS-OO Role domain object
    """
    role = keystone.roles.create(name)
    return Role(name=role.name, role_id=role.id)


def delete_role(keystone, role):
    """
    Deletes an OpenStack role
    :param keystone: the keystone client
    :param role: the SNAPS-OO Role domain object to delete
    :return:
    """
    keystone.roles.delete(role.id)


def grant_user_role_to_project(keystone, role, user, project):
    """
    Grants user and role to a project
    :param keystone: the Keystone client
    :param role: the SNAPS-OO Role domain object used to join a project/user
    :param user: the user to add to the project (SNAPS-OO User Domain object
    :param project: the project to which to add a user
    :return:
    """

    os_role = __get_os_role_by_id(keystone, role.id)
    if keystone.version == V2_VERSION:
        keystone.roles.add_user_role(user, os_role, tenant=project)
    else:
        keystone.roles.grant(os_role, user=user, project=project)


class KeystoneException(Exception):
    """
    Exception when calls to the Keystone client cannot be served properly
    """
