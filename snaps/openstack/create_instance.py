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
import time

from neutronclient.common.exceptions import PortNotFoundClient
from novaclient.exceptions import NotFound

from snaps.openstack.create_network import PortSettings
from snaps.openstack.utils import glance_utils
from snaps.openstack.utils import neutron_utils
from snaps.openstack.utils import nova_utils
from snaps.provisioning import ansible_utils

__author__ = 'spisarski'

logger = logging.getLogger('create_instance')

POLL_INTERVAL = 3
STATUS_ACTIVE = 'ACTIVE'
STATUS_DELETED = 'DELETED'


class OpenStackVmInstance:
    """
    Class responsible for creating a VM instance in OpenStack
    """

    def __init__(self, os_creds, instance_settings, image_settings,
                 keypair_settings=None):
        """
        Constructor
        :param os_creds: The connection credentials to the OpenStack API
        :param instance_settings: Contains the settings for this VM
        :param image_settings: The OpenStack image object settings
        :param keypair_settings: The keypair metadata (Optional)
        :raises Exception
        """
        self.__os_creds = os_creds

        self.__nova = None
        self.__neutron = None

        self.instance_settings = instance_settings
        self.image_settings = image_settings
        self.keypair_settings = keypair_settings

        self.__floating_ip_dict = dict()

        # Instantiated in self.create()
        self.__ports = list()

        # Note: this object does not change after the VM becomes active
        self.__vm = None

    def create(self, cleanup=False, block=False):
        """
        Creates a VM instance
        :param cleanup: When true, only perform lookups for OpenStack objects.
        :param block: Thread will block until instance has either become
                      active, error, or timeout waiting.
                      Additionally, when True, floating IPs will not be applied
                      until VM is active.
        :return: The VM reference object
        """
        self.__nova = nova_utils.nova_client(self.__os_creds)
        self.__neutron = neutron_utils.neutron_client(self.__os_creds)

        self.__ports = self.__setup_ports(self.instance_settings.port_settings,
                                          cleanup)
        self.__lookup_existing_vm_by_name()
        if not self.__vm and not cleanup:
            self.__create_vm(block)
        return self.__vm

    def __lookup_existing_vm_by_name(self):
        """
        Populates the member variables 'self.vm' and 'self.floating_ips' if a
        VM with the same name already exists
        within the project
        """
        server = nova_utils.get_server(
            self.__nova, vm_inst_settings=self.instance_settings)
        if server:
            if server.name == self.instance_settings.name:
                self.__vm = server
                logger.info(
                    'Found existing machine with name - %s',
                    self.instance_settings.name)

                fips = neutron_utils.get_floating_ips(self.__neutron,
                                                      self.__ports)
                for port_name, fip in fips:
                    settings = self.instance_settings.floating_ip_settings
                    for fip_setting in settings:
                        if port_name == fip_setting.port_name:
                            self.__floating_ip_dict[fip_setting.name] = fip

    def __create_vm(self, block=False):
        """
        Responsible for creating the VM instance
        :param block: Thread will block until instance has either become
                      active, error, or timeout waiting. Floating IPs will be
                      assigned after active when block=True
        """
        glance = glance_utils.glance_client(self.__os_creds)
        self.__vm = nova_utils.create_server(
            self.__nova, self.__neutron, glance, self.instance_settings,
            self.image_settings, self.keypair_settings)
        logger.info('Created instance with name - %s',
                    self.instance_settings.name)

        if block:
            if not self.vm_active(block=True):
                raise VmInstanceCreationError(
                    'Fatal error, VM did not become ACTIVE within the alloted '
                    'time')

        # Create server should do this but found it needed to occur here
        for sec_grp_name in self.instance_settings.security_group_names:
            if self.vm_active(block=True):
                nova_utils.add_security_group(self.__nova, self.__vm,
                                              sec_grp_name)
            else:
                raise VmInstanceCreationError(
                    'Cannot applying security group with name ' +
                    sec_grp_name +
                    ' to VM that did not activate with name - ' +
                    self.instance_settings.name)

        self.__apply_floating_ips()

    def __apply_floating_ips(self):
        """
        Applies the configured floating IPs to the necessary ports
        """
        port_dict = dict()
        for key, port in self.__ports:
            port_dict[key] = port

        # Apply floating IPs
        for floating_ip_setting in self.instance_settings.floating_ip_settings:
            port = port_dict.get(floating_ip_setting.port_name)

            if not port:
                raise VmInstanceCreationError(
                    'Cannot find port object with name - ' +
                    floating_ip_setting.port_name)

            # Setup Floating IP only if there is a router with an external
            # gateway
            ext_gateway = self.__ext_gateway_by_router(
                floating_ip_setting.router_name)
            if ext_gateway:
                subnet = neutron_utils.get_subnet(
                    self.__neutron,
                    subnet_name=floating_ip_setting.subnet_name)
                floating_ip = neutron_utils.create_floating_ip(
                    self.__neutron, ext_gateway)
                self.__floating_ip_dict[floating_ip_setting.name] = floating_ip

                logger.info(
                    'Created floating IP %s via router - %s', floating_ip.ip,
                    floating_ip_setting.router_name)
                self.__add_floating_ip(floating_ip, port, subnet)
            else:
                raise VmInstanceCreationError(
                    'Unable to add floating IP to port, cannot locate router '
                    'with an external gateway ')

    def __ext_gateway_by_router(self, router_name):
        """
        Returns network name for the external network attached to a router or
        None if not found
        :param router_name: The name of the router to lookup
        :return: the external network name or None
        """
        router = neutron_utils.get_router(
            self.__neutron, router_name=router_name)
        if router and router.external_gateway_info:
            network = neutron_utils.get_network_by_id(
                self.__neutron,
                router.external_gateway_info['network_id'])
            if network:
                return network.name
        return None

    def clean(self):
        """
        Destroys the VM instance
        """

        # Cleanup floating IPs
        for name, floating_ip in self.__floating_ip_dict.items():
            try:
                logger.info('Deleting Floating IP - ' + floating_ip.ip)
                neutron_utils.delete_floating_ip(self.__neutron, floating_ip)
            except Exception as e:
                logger.error('Error deleting Floating IP - ' + str(e))
        self.__floating_ip_dict = dict()

        # Cleanup ports
        for name, port in self.__ports:
            logger.info('Deleting Port - ' + name)
            try:
                neutron_utils.delete_port(self.__neutron, port)
            except PortNotFoundClient as e:
                logger.warning('Unexpected error deleting port - %s', e)
                pass
        self.__ports = list()

        # Cleanup VM
        if self.__vm:
            try:
                logger.info(
                    'Deleting VM instance - ' + self.instance_settings.name)
                nova_utils.delete_vm_instance(self.__nova, self.__vm)
            except Exception as e:
                logger.error('Error deleting VM - %s', e)

            # Block until instance cannot be found or returns the status of
            # DELETED
            logger.info('Checking deletion status')

            try:
                if self.vm_deleted(block=True):
                    logger.info(
                        'VM has been properly deleted VM with name - %s',
                        self.instance_settings.name)
                    self.__vm = None
                else:
                    logger.error(
                        'VM not deleted within the timeout period of %s '
                        'seconds', self.instance_settings.vm_delete_timeout)
            except Exception as e:
                logger.error(
                    'Unexpected error while checking VM instance status - %s',
                    e)

    def __setup_ports(self, port_settings, cleanup):
        """
        Returns the previously configured ports or creates them if they do not
        exist
        :param port_settings: A list of PortSetting objects
        :param cleanup: When true, only perform lookups for OpenStack objects.
        :return: a list of OpenStack port tuples where the first member is the
                 port name and the second is the port object
        """
        ports = list()

        for port_setting in port_settings:
            port = neutron_utils.get_port(
                self.__neutron, port_settings=port_setting)
            if port:
                ports.append((port_setting.name, port))
            elif not cleanup:
                # Exception will be raised when port with same name already
                # exists
                ports.append(
                    (port_setting.name, neutron_utils.create_port(
                        self.__neutron, self.__os_creds, port_setting)))

        return ports

    def __add_floating_ip(self, floating_ip, port, subnet, timeout=30,
                          poll_interval=POLL_INTERVAL):
        """
        Returns True when active else False
        TODO - Make timeout and poll_interval configurable...
        """
        ip = None

        if subnet:
            # Take IP of subnet if there is one configured on which to place
            # the floating IP
            for fixed_ip in port.ips:
                if fixed_ip['subnet_id'] == subnet.id:
                    ip = fixed_ip['ip_address']
                    break
        else:
            # Simply take the first
            ip = port.ips[0]['ip_address']

        if ip:
            count = timeout / poll_interval
            while count > 0:
                logger.debug('Attempting to add floating IP to instance')
                try:
                    nova_utils.add_floating_ip_to_server(
                        self.__nova, self.__vm, floating_ip, ip)
                    logger.info(
                        'Added floating IP %s to port IP %s on instance %s',
                        floating_ip.ip, ip, self.instance_settings.name)
                    return
                except Exception as e:
                    logger.debug(
                        'Retry adding floating IP to instance. Last attempt '
                        'failed with - %s', e)
                    time.sleep(poll_interval)
                    count -= 1
                    pass
        else:
            raise VmInstanceCreationError(
                'Unable find IP address on which to place the floating IP')

        logger.error('Timeout attempting to add the floating IP to instance.')
        raise VmInstanceCreationError(
            'Timeout while attempting add floating IP to instance')

    def get_os_creds(self):
        """
        Returns the OpenStack credentials used to create these objects
        :return: the credentials
        """
        return self.__os_creds

    def get_vm_inst(self):
        """
        Returns the latest version of this server object from OpenStack
        :return: Server object
        """
        return self.__vm

    def get_console_output(self):
        """
        Returns the vm console object for parsing logs
        :return: the console output object
        """
        return nova_utils.get_server_console_output(self.__nova, self.__vm)

    def get_port_ip(self, port_name, subnet_name=None):
        """
        Returns the first IP for the port corresponding with the port_name
        parameter when subnet_name is None else returns the IP address that
        corresponds to the subnet_name parameter
        :param port_name: the name of the port from which to return the IP
        :param subnet_name: the name of the subnet attached to this IP
        :return: the IP or None if not found
        """
        port = self.get_port_by_name(port_name)
        if port:
            if subnet_name:
                subnet = neutron_utils.get_subnet(
                    self.__neutron, subnet_name=subnet_name)
                if not subnet:
                    logger.warning('Cannot retrieve port IP as subnet could '
                                   'not be located with name - %s',
                                   subnet_name)
                    return None
                for fixed_ip in port.ips:
                    if fixed_ip['subnet_id'] == subnet.id:
                        return fixed_ip['ip_address']
            else:
                if port.ips and len(port.ips) > 0:
                    return port.ips[0]['ip_address']
        return None

    def get_port_mac(self, port_name):
        """
        Returns the first IP for the port corresponding with the port_name
        parameter
        TODO - Add in the subnet as an additional parameter as a port may have
        multiple fixed_ips
        :param port_name: the name of the port from which to return the IP
        :return: the IP or None if not found
        """
        port = self.get_port_by_name(port_name)
        if port:
            return port.mac_address
        return None

    def get_port_by_name(self, port_name):
        """
        Retrieves the OpenStack port object by its given name
        :param port_name: the name of the port
        :return: the OpenStack port object or None if not exists
        """
        for key, port in self.__ports:
            if key == port_name:
                return port
        logger.warning('Cannot find port with name - ' + port_name)
        return None

    def get_vm_info(self):
        """
        Returns a dictionary of a VMs info as returned by OpenStack
        :return: a dict()
        """
        return nova_utils.get_server_info(self.__nova, self.__vm)

    def config_nics(self):
        """
        Responsible for configuring NICs on RPM systems where the instance has
        more than one configured port
        :return: the value returned by ansible_utils.apply_ansible_playbook()
        """
        if len(self.__ports) > 1 and len(self.__floating_ip_dict) > 0:
            if self.vm_active(block=True) and self.vm_ssh_active(block=True):
                for key, port in self.__ports:
                    port_index = self.__ports.index((key, port))
                    if port_index > 0:
                        nic_name = 'eth' + repr(port_index)
                        retval = self.__config_nic(
                            nic_name, port,
                            self.__get_first_provisioning_floating_ip().ip)
                        logger.info('Configured NIC - %s on VM - %s',
                                    nic_name, self.instance_settings.name)
                        return retval

    def __get_first_provisioning_floating_ip(self):
        """
        Returns the first floating IP tagged with the Floating IP name if
        exists else the first one found
        :return:
        """
        for floating_ip_setting in self.instance_settings.floating_ip_settings:
            if floating_ip_setting.provisioning:
                fip = self.__floating_ip_dict.get(floating_ip_setting.name)
                if fip:
                    return fip
                elif len(self.__floating_ip_dict) > 0:
                    for key, fip in self.__floating_ip_dict.items():
                        return fip

    def __config_nic(self, nic_name, port, ip):
        """
        Although ports/NICs can contain multiple IPs, this code currently only
        supports the first.

        :param nic_name: Name of the interface
        :param port: The port information containing the expected IP values.
        :param ip: The IP on which to apply the playbook.
        :return: the return value from ansible
        """
        port_ip = port.ips[0]['ip_address']
        variables = {
            'floating_ip': ip,
            'nic_name': nic_name,
            'nic_ip': port_ip
        }

        if self.image_settings.nic_config_pb_loc and self.keypair_settings:
            return self.apply_ansible_playbook(
                self.image_settings.nic_config_pb_loc, variables)
        else:
            logger.warning(
                'VM %s cannot self configure NICs eth1++. No playbook or '
                'keypairs found.', self.instance_settings.name)

    def apply_ansible_playbook(self, pb_file_loc, variables=None,
                               fip_name=None):
        """
        Applies a playbook to a VM
        :param pb_file_loc: the file location of the playbook to be applied
        :param variables: a dict() of substitution values required by the
                          playbook
        :param fip_name: the name of the floating IP to use for applying the
                         playbook (default - will take the first)
        :return: the return value from ansible
        """
        return ansible_utils.apply_playbook(
            pb_file_loc, [self.get_floating_ip(fip_name=fip_name).ip],
            self.get_image_user(), self.keypair_settings.private_filepath,
            variables, self.__os_creds.proxy_settings)

    def get_image_user(self):
        """
        Returns the instance sudo_user if it has been configured in the
        instance_settings else it returns the image_settings.image_user value
        """
        if self.instance_settings.sudo_user:
            return self.instance_settings.sudo_user
        else:
            return self.image_settings.image_user

    def vm_deleted(self, block=False, poll_interval=POLL_INTERVAL):
        """
        Returns true when the VM status returns the value of
        expected_status_code or instance retrieval throws a NotFound exception.
        :param block: When true, thread will block until active or timeout
                      value in seconds has been exceeded (False)
        :param poll_interval: The polling interval in seconds
        :return: T/F
        """
        try:
            return self.__vm_status_check(
                STATUS_DELETED, block,
                self.instance_settings.vm_delete_timeout, poll_interval)
        except NotFound as e:
            logger.debug(
                "Instance not found when querying status for %s with message "
                "%s", STATUS_DELETED, e)
            return True

    def vm_active(self, block=False, poll_interval=POLL_INTERVAL):
        """
        Returns true when the VM status returns the value of
        expected_status_code
        :param block: When true, thread will block until active or timeout
                      value in seconds has been exceeded (False)
        :param poll_interval: The polling interval in seconds
        :return: T/F
        """
        return self.__vm_status_check(STATUS_ACTIVE, block,
                                      self.instance_settings.vm_boot_timeout,
                                      poll_interval)

    def __vm_status_check(self, expected_status_code, block, timeout,
                          poll_interval):
        """
        Returns true when the VM status returns the value of
        expected_status_code
        :param expected_status_code: instance status evaluated with this
                                     string value
        :param block: When true, thread will block until active or timeout
                      value in seconds has been exceeded (False)
        :param timeout: The timeout value
        :param poll_interval: The polling interval in seconds
        :return: T/F
        """
        # sleep and wait for VM status change
        if block:
            start = time.time()
        else:
            return self.__status(expected_status_code)

        while timeout > time.time() - start:
            status = self.__status(expected_status_code)
            if status:
                logger.info('VM is - ' + expected_status_code)
                return True

            logger.debug('Retry querying VM status in ' + str(
                poll_interval) + ' seconds')
            time.sleep(poll_interval)
            logger.debug('VM status query timeout in ' + str(
                timeout - (time.time() - start)))

        logger.error(
            'Timeout checking for VM status for ' + expected_status_code)
        return False

    def __status(self, expected_status_code):
        """
        Returns True when active else False
        :param expected_status_code: instance status evaluated with this string
                                     value
        :return: T/F
        """
        if not self.__vm:
            return False

        status = nova_utils.get_server_status(self.__nova, self.__vm)
        if not status:
            logger.warning('Cannot find instance with id - ' + self.__vm.id)
            return False

        if status == 'ERROR':
            raise VmInstanceCreationError(
                'Instance had an error during deployment')
        logger.debug(
            'Instance status [%s] is - %s', self.instance_settings.name,
            status)
        return status == expected_status_code

    def vm_ssh_active(self, block=False, poll_interval=POLL_INTERVAL):
        """
        Returns true when the VM can be accessed via SSH
        :param block: When true, thread will block until active or timeout
                      value in seconds has been exceeded (False)
        :param poll_interval: The polling interval
        :return: T/F
        """
        # sleep and wait for VM status change
        logger.info('Checking if VM is active')

        timeout = self.instance_settings.ssh_connect_timeout

        if self.vm_active(block=True):
            if block:
                start = time.time()
            else:
                start = time.time() - timeout

            while timeout > time.time() - start:
                status = self.__ssh_active()
                if status:
                    logger.info('SSH is active for VM instance')
                    return True

                logger.debug('Retry SSH connection in ' + str(
                    poll_interval) + ' seconds')
                time.sleep(poll_interval)
                logger.debug('SSH connection timeout in ' + str(
                    timeout - (time.time() - start)))

        logger.error('Timeout attempting to connect with VM via SSH')
        return False

    def __ssh_active(self):
        """
        Returns True when can create a SSH session else False
        :return: T/F
        """
        if len(self.__floating_ip_dict) > 0:
            ssh = self.ssh_client()
            if ssh:
                ssh.close()
                return True
        return False

    def get_floating_ip(self, fip_name=None):
        """
        Returns the floating IP object byt name if found, else the first known,
        else None
        :param fip_name: the name of the floating IP to return
        :return: the SSH client or None
        """
        fip = None
        if fip_name and self.__floating_ip_dict.get(fip_name):
            return self.__floating_ip_dict.get(fip_name)
        if not fip:
            return self.__get_first_provisioning_floating_ip()

    def ssh_client(self, fip_name=None):
        """
        Returns an SSH client using the name or the first known floating IP if
        exists, else None
        :param fip_name: the name of the floating IP to return
        :return: the SSH client or None
        """
        fip = self.get_floating_ip(fip_name)
        if fip:
            return ansible_utils.ssh_client(
                self.__get_first_provisioning_floating_ip().ip,
                self.get_image_user(),
                self.keypair_settings.private_filepath,
                proxy_settings=self.__os_creds.proxy_settings)
        else:
            logger.warning(
                'Cannot return an SSH client. No Floating IP configured')

    def add_security_group(self, security_group):
        """
        Adds a security group to this VM. Call will block until VM is active.
        :param security_group: the SNAPS SecurityGroup domain object
        :return True if successful else False
        """
        self.vm_active(block=True)

        if not security_group:
            logger.warning('Security group object is None, cannot add')
            return False

        try:
            nova_utils.add_security_group(self.__nova, self.get_vm_inst(),
                                          security_group.name)
            return True
        except NotFound as e:
            logger.warning('Security group not added - ' + str(e))
            return False

    def remove_security_group(self, security_group):
        """
        Removes a security group to this VM. Call will block until VM is active
        :param security_group: the OpenStack security group object
        :return True if successful else False
        """
        self.vm_active(block=True)

        if not security_group:
            logger.warning('Security group object is None, cannot remove')
            return False

        try:
            nova_utils.remove_security_group(self.__nova, self.get_vm_inst(),
                                             security_group)
            return True
        except NotFound as e:
            logger.warning('Security group not removed - ' + str(e))
            return False


class VmInstanceSettings:
    """
    Class responsible for holding configuration setting for a VM Instance
    """

    def __init__(self, **kwargs):
        """
        Constructor
        :param name: the name of the VM
        :param flavor: the VM's flavor
        :param port_settings: the port configuration settings (required)
        :param security_group_names: a set of names of the security groups to
                                     add to the VM
        :param floating_ip_settings: the floating IP configuration settings
        :param sudo_user: the sudo user of the VM that will override the
                          instance_settings.image_user when trying to
                          connect to the VM
        :param vm_boot_timeout: the amount of time a thread will sleep waiting
                                for an instance to boot
        :param vm_delete_timeout: the amount of time a thread will sleep
                                  waiting for an instance to be deleted
        :param ssh_connect_timeout: the amount of time a thread will sleep
                                    waiting obtaining an SSH connection to a VM
        :param availability_zone: the name of the compute server on which to
                                  deploy the VM (optional)
        :param userdata: the cloud-init script to run after the VM has been
                         started
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
                    self.port_settings.append(PortSettings(**port_setting))
                elif isinstance(port_setting, PortSettings):
                    self.port_settings.append(port_setting)

        if kwargs.get('security_group_names'):
            if isinstance(kwargs['security_group_names'], list):
                self.security_group_names = kwargs['security_group_names']
            elif isinstance(kwargs['security_group_names'], set):
                self.security_group_names = kwargs['security_group_names']
            elif isinstance(kwargs['security_group_names'], str):
                self.security_group_names = [kwargs['security_group_names']]
            else:
                raise VmInstanceSettingsError(
                    'Invalid data type for security_group_names attribute')
        else:
            self.security_group_names = set()

        self.floating_ip_settings = list()
        floating_ip_settings = kwargs.get('floating_ips')
        if not floating_ip_settings:
            floating_ip_settings = kwargs.get('floating_ip_settings')
        if floating_ip_settings:
            for floating_ip_config in floating_ip_settings:
                if isinstance(floating_ip_config, FloatingIpSettings):
                    self.floating_ip_settings.append(floating_ip_config)
                else:
                    self.floating_ip_settings.append(FloatingIpSettings(
                        **floating_ip_config['floating_ip']))

        if kwargs.get('vm_boot_timeout'):
            self.vm_boot_timeout = kwargs['vm_boot_timeout']
        else:
            self.vm_boot_timeout = 900

        if kwargs.get('vm_delete_timeout'):
            self.vm_delete_timeout = kwargs['vm_delete_timeout']
        else:
            self.vm_delete_timeout = 300

        if kwargs.get('ssh_connect_timeout'):
            self.ssh_connect_timeout = kwargs['ssh_connect_timeout']
        else:
            self.ssh_connect_timeout = 180

        if kwargs.get('availability_zone'):
            self.availability_zone = kwargs['availability_zone']
        else:
            self.availability_zone = None

        if not self.name or not self.flavor:
            raise VmInstanceSettingsError(
                'Instance configuration requires the attributes: name, flavor')

        if len(self.port_settings) == 0:
            raise VmInstanceSettingsError(
                'Instance configuration requires port settings (aka. NICS)')


class FloatingIpSettings:
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
        self.router_name = kwargs.get('router_name')
        self.subnet_name = kwargs.get('subnet_name')
        if kwargs.get('provisioning') is not None:
            self.provisioning = kwargs['provisioning']
        else:
            self.provisioning = True

        if not self.name or not self.port_name or not self.router_name:
            raise FloatingIpSettingsError(
                'The attributes name, port_name and router_name are required '
                'for FloatingIPSettings')


class VmInstanceSettingsError(Exception):
    """
    Exception to be thrown when an VM instance settings are incorrect
    """


class FloatingIpSettingsError(Exception):
    """
    Exception to be thrown when an VM instance settings are incorrect
    """


class VmInstanceCreationError(Exception):
    """
    Exception to be thrown when an VM instance cannot be created
    """
