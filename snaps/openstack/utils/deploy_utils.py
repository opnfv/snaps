#
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
#
# This utility makes it easy to create OpenStack objects
import logging

from snaps.openstack.create_project import OpenStackProject
from snaps.openstack.create_user import OpenStackUser
from snaps.openstack.create_image import OpenStackImage
from snaps.openstack.create_network import OpenStackNetwork
from snaps.openstack.create_router import OpenStackRouter
from snaps.openstack.create_keypairs import OpenStackKeypair
from snaps.openstack.create_instance import OpenStackVmInstance
from snaps.openstack.create_security_group import OpenStackSecurityGroup

logger = logging.getLogger('deploy_utils')


def create_image(os_creds, image_settings, cleanup=False):
    """
    Creates an image in OpenStack if necessary
    :param os_creds: The OpenStack credentials object
    :param image_settings: The image settings object
    :param cleanup: Denotes whether or not this is being called for cleanup
    :return: A reference to the image creator object from which the image
             object can be accessed
    """
    image_creator = OpenStackImage(os_creds, image_settings)

    if cleanup:
        image_creator.initialize()
    else:
        image_creator.create()
    return image_creator


def create_network(os_creds, network_settings, cleanup=False):
    """
    Creates a network on which the CMTSs can attach
    :param os_creds: The OpenStack credentials object
    :param network_settings: The network settings object
    :param cleanup: Denotes whether or not this is being called for cleanup
    :return: A reference to the network creator objects for each network from
             which network elements such as the subnet, router, interface
             router, and network objects can be accessed.
    """
    # Check for OS for network existence
    # If exists return network instance data
    # Else, create network and return instance data

    logger.info('Attempting to create network with name - %s',
                network_settings.name)

    network_creator = OpenStackNetwork(os_creds, network_settings)

    if cleanup:
        network_creator.initialize()
    else:
        network_creator.create()
    logger.info('Created network ')
    return network_creator


def create_router(os_creds, router_settings, cleanup=False):
    """
    Creates a network on which the CMTSs can attach
    :param os_creds: The OpenStack credentials object
    :param router_settings: The RouterConfig instance
    :param cleanup: Denotes whether or not this is being called for cleanup
    :return: A reference to the network creator objects for each network from
             which network elements such as the subnet, router, interface
             router, and network objects can be accessed.
    """
    # Check for OS for network existence
    # If exists return network instance data
    # Else, create network and return instance data
    logger.info('Attempting to create router with name - %s',
                router_settings.name)
    router_creator = OpenStackRouter(os_creds, router_settings)

    if cleanup:
        router_creator.initialize()
    else:
        router_creator.create()
    logger.info('Created router ')
    return router_creator


def create_keypair(os_creds, keypair_settings, cleanup=False):
    """
    Creates a keypair that can be applied to an instance
    :param os_creds: The OpenStack credentials object
    :param keypair_settings: The KeypairConfig object
    :param cleanup: Denotes whether or not this is being called for cleanup
    :return: A reference to the keypair creator object
    """
    keypair_creator = OpenStackKeypair(os_creds, keypair_settings)

    if cleanup:
        keypair_creator.initialize()
    else:
        keypair_creator.create()
    return keypair_creator


def create_vm_instance(os_creds, instance_settings, image_settings,
                       keypair_creator=None, init_only=False):
    """
    Creates a VM instance
    :param os_creds: The OpenStack credentials
    :param instance_settings: Instance of VmInstanceConfig
    :param image_settings: The object containing image settings
    :param keypair_creator: The object responsible for creating the keypair
                            associated with this VM instance. (optional)
    :param init_only: Denotes whether or not this is being called for
                      initialization (T) or creation (F) (default False)
    :return: A reference to the VM instance object
    """
    kp_settings = None
    if keypair_creator:
        kp_settings = keypair_creator.keypair_settings
    vm_creator = OpenStackVmInstance(os_creds, instance_settings,
                                     image_settings, kp_settings)
    if init_only:
        vm_creator.initialize()
    else:
        vm_creator.create()
    return vm_creator


def create_user(os_creds, user_settings):
    """
    Creates an OpenStack user
    :param os_creds: The OpenStack credentials
    :param user_settings: The user configuration settings
    :return: A reference to the user instance object
    """
    user_creator = OpenStackUser(os_creds, user_settings)
    user_creator.create()
    return user_creator


def create_project(os_creds, project_settings):
    """
    Creates an OpenStack user
    :param os_creds: The OpenStack credentials
    :param project_settings: The user project configuration settings
    :return: A reference to the project instance object
    """
    project_creator = OpenStackProject(os_creds, project_settings)
    project_creator.create()
    return project_creator


def create_security_group(os_creds, sec_grp_settings):
    """
    Creates an OpenStack Security Group
    :param os_creds: The OpenStack credentials
    :param sec_grp_settings: The security group settings
    :return: A reference to the project instance object
    """
    sg_creator = OpenStackSecurityGroup(os_creds, sec_grp_settings)
    sg_creator.create()
    return sg_creator
