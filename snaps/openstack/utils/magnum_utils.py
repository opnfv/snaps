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

from magnumclient.client import Client

from snaps.domain.cluster_template import ClusterTemplate
from snaps.openstack.utils import keystone_utils

__author__ = 'spisarski'

logger = logging.getLogger('magnum_utils')


def magnum_client(os_creds, session=None):
    """
    Retrieves the Magnum client
    :param os_creds: the OpenStack credentialsf
    :param session: the keystone session object (optional)
    :return: the client
    """
    logger.debug('Retrieving Magnum Client')
    if not session:
        session = keystone_utils.keystone_session(os_creds)

    return Client(str(os_creds.magnum_api_version), session=session)


def get_cluster_template(magnum, template_config=None, template_name=None):
    """
    Returns the first ClusterTemplate domain object that matches the parameters
    :param magnum: the Magnum client
    :param template_config: a ClusterTemplateConfig object (optional)
    :param template_name: the name of the template to lookup
    :return: ClusterTemplate object or None
    """
    name = None
    if template_config:
        name = template_config.name
    elif template_name:
        name = template_name

    os_templates = magnum.cluster_templates.list()
    for os_template in os_templates:
        if os_template.name == name:
            return __map_os_cluster_template(os_template)


def get_cluster_template_by_id(magnum, tmplt_id):
    """
    Returns the first ClusterTemplate domain object that matches the parameters
    :param magnum: the Magnum client
    :param tmplt_id: the template's ID
    :return: ClusterTemplate object or None
    """
    return __map_os_cluster_template(magnum.cluster_templates.get(tmplt_id))


def create_cluster_template(magnum, cluster_template_config):
    """
    Creates a Magnum Cluster Template object in OpenStack
    :param magnum: the Magnum client
    :param cluster_template_config: a ClusterTemplateConfig object
    :return: a SNAPS ClusterTemplate domain object
    """
    config_dict = cluster_template_config.magnum_dict()
    os_cluster_template = magnum.cluster_templates.create(**config_dict)
    logger.info('Creating cluster template named [%s]',
                cluster_template_config.name)
    return __map_os_cluster_template(os_cluster_template)


def delete_cluster_template(magnum, tmplt_id):
    """
    Deletes a Cluster Template from OpenStack
    :param magnum: the Magnum client
    :param tmplt_id: the cluster template ID to delete
    """
    logger.info('Deleting cluster template with ID [%s]', tmplt_id)
    magnum.cluster_templates.delete(tmplt_id)


def __map_os_cluster_template(os_tmplt):
    """
    Returns a SNAPS ClusterTemplate object from an OpenStack ClusterTemplate
    object
    :param os_tmplt: the OpenStack ClusterTemplate object
    :return: SNAPS ClusterTemplate object
    """
    return ClusterTemplate(
        id=os_tmplt.uuid,
        name=os_tmplt.name,
        image=os_tmplt.image_id,
        keypair=os_tmplt.keypair_id,
        network_driver=os_tmplt.network_driver,
        external_net=os_tmplt.external_network_id,
        floating_ip_enabled=os_tmplt.floating_ip_enabled,
        docker_volume_size=os_tmplt.docker_volume_size,
        server_type=os_tmplt.server_type,
        flavor=os_tmplt.flavor_id,
        master_flavor=os_tmplt.master_flavor_id,
        coe=os_tmplt.coe,
        fixed_net=os_tmplt.fixed_network,
        fixed_subnet=os_tmplt.fixed_subnet,
        registry_enabled=os_tmplt.registry_enabled,
        insecure_registry=os_tmplt.insecure_registry,
        docker_storage_driver=os_tmplt.docker_storage_driver,
        dns_nameserver=os_tmplt.dns_nameserver,
        public=os_tmplt.public,
        tls_disabled=os_tmplt.tls_disabled,
        http_proxy=os_tmplt.http_proxy,
        https_proxy=os_tmplt.https_proxy,
        no_proxy=os_tmplt.no_proxy,
        volume_driver=os_tmplt.volume_driver,
        master_lb_enabled=os_tmplt.master_lb_enabled,
        labels=os_tmplt.labels
    )
