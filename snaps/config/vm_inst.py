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
from snaps.config.network import PortConfig


class VmInstanceConfig(object):
    """
    Class responsible for holding configuration setting for a VM Instance
    """

    def __init__(self, **kwargs):
        """
        Constructor
        :param name: the name of the VM
        :param flavor: the VM's flavor name
        :param port_settings: the port configuration settings (required)
        :param security_group_names: a set of names of the security groups to
                                     add to the VM
        :param floating_ip_settings: the floating IP configuration settings
        :param sudo_user: the sudo user of the VM that will override the
                          instance_settings.image_user when trying to
                          connect to the VM
        :param vm_boot_timeout: the amount of time a thread will wait
                                for an instance to boot
        :param vm_delete_timeout: the amount of time a thread will wait
                                  for an instance to be deleted
        :param ssh_connect_timeout: the amount of time a thread will wait
                                    to obtain an SSH connection to a VM
        :param cloud_init_timeout: the amount of time a thread will wait for
                                   cloud-init to complete
        :param availability_zone: the name of the compute server on which to
                                  deploy the VM (optional)
        :param volume_names: a list of the names of the volume to attach
                             (optional)
        :param userdata: the string contents of any optional cloud-init script
                         to execute after the VM has been activated.
                         This value may also contain a dict who's key value
                         must contain the key 'cloud-init_file' which denotes
                         the location of some file containing the cloud-init
                         script
        """
        self.name = kwargs.get('name')
        self.flavor = kwargs.get('flavor')
        self.sudo_user = kwargs.get('sudo_user')
        self.userdata = kwargs.get('userdata')

        self.port_settings = list()
        port_settings = kwargs.get('ports')
        if not port_settings:
            port_settings = kwargs.get('port_settings')
        if port_settings:
            for port_setting in port_settings:
                if isinstance(port_setting, dict):
                    self.port_settings.append(PortConfig(**port_setting))
                elif isinstance(port_setting, PortConfig):
                    self.port_settings.append(port_setting)

        if kwargs.get('security_group_names'):
            if isinstance(kwargs['security_group_names'], list):
                self.security_group_names = kwargs['security_group_names']
            elif isinstance(kwargs['security_group_names'], set):
                self.security_group_names = kwargs['security_group_names']
            elif isinstance(kwargs['security_group_names'], str):
                self.security_group_names = [kwargs['security_group_names']]
            else:
                raise VmInstanceConfigError(
                    'Invalid data type for security_group_names attribute')
        else:
            self.security_group_names = set()

        self.floating_ip_settings = list()
        floating_ip_settings = kwargs.get('floating_ips')
        if not floating_ip_settings:
            floating_ip_settings = kwargs.get('floating_ip_settings')
        if floating_ip_settings:
            for floating_ip_config in floating_ip_settings:
                if isinstance(floating_ip_config, FloatingIpConfig):
                    self.floating_ip_settings.append(floating_ip_config)
                else:
                    self.floating_ip_settings.append(FloatingIpConfig(
                        **floating_ip_config['floating_ip']))

        self.vm_boot_timeout = kwargs.get('vm_boot_timeout', 900)
        self.vm_delete_timeout = kwargs.get('vm_delete_timeout', 300)
        self.ssh_connect_timeout = kwargs.get('ssh_connect_timeout', 180)
        self.cloud_init_timeout = kwargs.get('cloud_init_timeout', 300)
        self.availability_zone = kwargs.get('availability_zone')
        self.volume_names = kwargs.get('volume_names')

        if self.volume_names and not isinstance(self.volume_names, list):
            raise VmInstanceConfigError('volume_names must be a list')

        if not self.name or not self.flavor:
            raise VmInstanceConfigError(
                'Instance configuration requires the attributes: name, flavor')

        if len(self.port_settings) == 0:
            raise VmInstanceConfigError(
                'Instance configuration requires port settings (aka. NICS)')


class FloatingIpConfig(object):
    """
    Class responsible for holding configuration settings for a floating IP
    """

    def __init__(self, **kwargs):
        """
        Constructor
        :param name: the name of the floating IP
        :param port_name: the name of the router to the external network
        :param router_name: the name of the router to the external network
        :param subnet_name: the name of the subnet on which to attach the
                            floating IP
        :param provisioning: when true, this floating IP can be used for
                             provisioning

        TODO - provisioning flag is a hack as I have only observed a single
        Floating IPs that actually works on an instance. Multiple floating IPs
        placed on different subnets from the same port are especially
        troublesome as you cannot predict which one will actually connect.
        For now, it is recommended not to setup multiple floating IPs on an
        instance unless absolutely necessary.
        """
        self.name = kwargs.get('name')
        self.port_name = kwargs.get('port_name')
        self.port_id = kwargs.get('port_id')
        self.router_name = kwargs.get('router_name')
        self.subnet_name = kwargs.get('subnet_name')
        if kwargs.get('provisioning') is not None:
            self.provisioning = kwargs['provisioning']
        else:
            self.provisioning = True

        # if not self.name or not self.port_name or not self.router_name:
        if not self.name or not self.router_name:
            raise FloatingIpConfigError(
                'The attributes name, port_name and router_name are required')

        if not self.port_name and not self.port_id:
            raise FloatingIpConfigError(
                'The attributes port_name or port_id are required')


class VmInstanceConfigError(Exception):
    """
    Exception to be thrown when an VM instance settings are incorrect
    """


class FloatingIpConfigError(Exception):
    """
    Exception to be thrown when an VM instance settings are incorrect
    """
