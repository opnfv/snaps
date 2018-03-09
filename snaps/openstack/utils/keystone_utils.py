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
import logging

import keystoneauth1
from keystoneclient.client import Client
from keystoneauth1.identity import v3, v2
from keystoneauth1 import session
import requests
from keystoneclient.exceptions import NotFound

from snaps.domain.project import Project, Domain
from snaps.domain.role import Role
from snaps.domain.user import User

logger = logging.getLogger('keystone_utils')

V2_VERSION_NUM = 2.0
V2_VERSION_STR = 'v' + str(V2_VERSION_NUM)


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
                           user_domain_name=os_creds.user_domain_name,
                           project_domain_id=os_creds.project_domain_id,
                           project_domain_name=os_creds.project_domain_name)
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
                os_creds.proxy_settings.port,
            'https':
                os_creds.proxy_settings.https_host + ':' +
                os_creds.proxy_settings.https_port
        }
    return session.Session(auth=auth, session=req_session,
                           verify=os_creds.cacert)


def close_session(session):
    """
    Closes a keystone session
    :param session: a session.Session object
    """
    if isinstance(session, keystoneauth1.session.Session):
        session.session.close()


def keystone_client(os_creds, session=None):
    """
    Returns the keystone client
    :param os_creds: the OpenStack credentials (OSCreds) object
    :param session: the keystone session object (optional)
    :return: the client
    """

    if not session:
        session = keystone_session(os_creds)

    return Client(
        version=os_creds.identity_api_version,
        session=session,
        interface=os_creds.interface,
        region_name=os_creds.region_name)


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
        auth=auth, service_type=service_type, region_name=os_creds.region_name,
        interface=interface)


def get_project(keystone=None, project_settings=None, project_name=None):
    """
    Returns the first project where the project_settings is used for the query
    if not None, else the project_name parameter is used for the query. If both
    parameters are None, None is returned
    :param keystone: the Keystone client
    :param project_settings: a ProjectConfig object
    :param project_name: the name to query
    :return: the SNAPS-OO Project domain object or None
    """
    proj_filter = dict()

    if project_name:
        proj_filter['name'] = project_name
    elif project_settings:
        proj_filter['name'] = project_settings.name
        proj_filter['description'] = project_settings.description
        proj_filter['domain_name'] = project_settings.domain_name
        proj_filter['enabled'] = project_settings.enabled
    else:
        return None

    if keystone.version == V2_VERSION_STR:
        projects = keystone.tenants.list()
    else:
        projects = keystone.projects.list(**proj_filter)

    for project in projects:
        if project.name == proj_filter['name']:
            domain_id = None
            if keystone.version != V2_VERSION_STR:
                domain_id = project.domain_id

            return Project(name=project.name, project_id=project.id,
                           domain_id=domain_id)


def get_project_by_id(keystone, proj_id):
    """
    Returns the first project where the project_settings is used for the query
    if not None, else the project_name parameter is used for the query. If both
    parameters are None, None is returned
    :param keystone: the Keystone client
    :param proj_id: the project ID
    """
    if proj_id and len(proj_id) > 0:
        try:
            os_proj = keystone.projects.get(proj_id)
            if os_proj:
                return Project(name=os_proj.name, project_id=os_proj.id,
                               domain_id=os_proj)
        except NotFound:
            pass
        except KeyError:
            pass


def create_project(keystone, project_settings):
    """
    Creates a project
    :param keystone: the Keystone client
    :param project_settings: the project configuration
    :return: SNAPS-OO Project domain object
    """
    domain_id = None

    if keystone.version == V2_VERSION_STR:
        os_project = keystone.tenants.create(
            project_settings.name, project_settings.description,
            project_settings.enabled)
    else:
        os_domain = __get_os_domain_by_name(
            keystone, project_settings.domain_name)
        if not os_domain:
            os_domain = project_settings.domain_name
        os_project = keystone.projects.create(
            project_settings.name, os_domain,
            description=project_settings.description,
            enabled=project_settings.enabled)
        domain_id = os_project.domain_id

    logger.info('Created project with name - %s', project_settings.name)
    return Project(
        name=os_project.name, project_id=os_project.id, domain_id=domain_id)


def delete_project(keystone, project):
    """
    Deletes a project
    :param keystone: the Keystone clien
    :param project: the SNAPS-OO Project domain object
    """
    logger.info('Deleting project with name - %s', project.name)
    if keystone.version == V2_VERSION_STR:
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
    project = None
    if project_name:
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
        project = get_project(
            keystone=keystone, project_name=user_settings.project_name)

    if keystone.version == V2_VERSION_STR:
        project_id = None
        if project:
            project_id = project.id
        os_user = keystone.users.create(
            name=user_settings.name, password=user_settings.password,
            email=user_settings.email, tenant_id=project_id,
            enabled=user_settings.enabled)
    else:
        os_domain = __get_os_domain_by_name(
            keystone, user_settings.domain_name)
        if not os_domain:
            os_domain = user_settings.domain_name
        os_user = keystone.users.create(
            name=user_settings.name, password=user_settings.password,
            email=user_settings.email, project=project,
            domain=os_domain, enabled=user_settings.enabled)

    for role_name, role_project in user_settings.roles.items():
        os_role = get_role_by_name(keystone, role_name)
        os_project = get_project(keystone=keystone, project_name=role_project)

        if os_role and os_project:
            existing_roles = get_roles_by_user(keystone, os_user, os_project)
            found = False
            for role in existing_roles:
                if role.id == os_role.id:
                    found = True

            if not found:
                grant_user_role_to_project(
                    keystone=keystone, user=os_user, role=os_role,
                    project=os_project)

    if os_user:
        logger.info('Created user with name - %s', os_user.name)
        return User(name=os_user.name, user_id=os_user.id)


def delete_user(keystone, user):
    """
    Deletes a user
    :param keystone: the Keystone client
    :param user: the SNAPS-OO User domain object
    """
    logger.info('Deleting user with name - %s', user.name)
    keystone.users.delete(user.id)


def get_role_by_name(keystone, name):
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


def get_roles_by_user(keystone, user, project):
    """
    Returns a list of SNAPS-OO Role domain objects associated with a user
    :param keystone: the keystone client
    :param user: the OpenStack user object
    :param project: the OpenStack project object (only required for v2)
    :return: a list of SNAPS-OO Role domain objects
    """
    if keystone.version == V2_VERSION_STR:
        os_user = __get_os_user(keystone, user)
        roles = keystone.roles.roles_for_user(os_user, project)
    else:
        roles = keystone.roles.list(user=user, project=project)

    out = list()
    for role in roles:
        out.append(Role(name=role.name, role_id=role.id))
    return out


def get_role_by_id(keystone, role_id):
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
    logger.info('Created role with name - %s', role.name)
    return Role(name=role.name, role_id=role.id)


def delete_role(keystone, role):
    """
    Deletes an OpenStack role
    :param keystone: the keystone client
    :param role: the SNAPS-OO Role domain object to delete
    :return:
    """
    logger.info('Deleting role with name - %s', role.name)
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

    os_role = get_role_by_id(keystone, role.id)
    logger.info('Granting role %s to project %s', role.name, project.name)
    if keystone.version == V2_VERSION_STR:
        keystone.roles.add_user_role(user, os_role, tenant=project)
    else:
        keystone.roles.grant(os_role, user=user, project=project)


def get_domain_by_id(keystone, domain_id):
    """
    Returns the first OpenStack domain with the given name else None
    :param keystone: the Keystone client
    :param domain_id: the domain ID to retrieve
    :return: the SNAPS-OO Domain domain object
    """
    if keystone.version != V2_VERSION_STR:
        domain = keystone.domains.get(domain_id)
        if domain:
            return Domain(name=domain.name, domain_id=domain.id)


def __get_os_domain_by_name(keystone, domain_name):
    """
    Returns the first OpenStack domain with the given name else None
    :param keystone: the Keystone client
    :param domain_name: the domain name to lookup
    :return: the OpenStack domain object
    """
    domains = keystone.domains.list(name=domain_name)
    for domain in domains:
        if domain.name == domain_name:
            return domain


class KeystoneException(Exception):
    """
    Exception when calls to the Keystone client cannot be served properly
    """
