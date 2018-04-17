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

from novaclient.exceptions import NotFound

from snaps.config.vm_inst import VmInstanceConfig, FloatingIpConfig
from snaps.openstack.openstack_creator import OpenStackComputeObject
from snaps.openstack.utils import (
    glance_utils, cinder_utils, settings_utils, keystone_utils)
from snaps.openstack.utils import neutron_utils
from snaps.openstack.utils import nova_utils
from snaps.openstack.utils.nova_utils import RebootType
from snaps.provisioning import ansible_utils

__author__ = 'spisarski'

logger = logging.getLogger('create_instance')

POLL_INTERVAL = 3
STATUS_ACTIVE = 'ACTIVE'
STATUS_DELETED = 'DELETED'


class OpenStackVmInstance(OpenStackComputeObject):
    """
    Class responsible for managing a VM instance in OpenStack
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
        super(self.__class__, self).__init__(os_creds)

        self.__neutron = None

        self.instance_settings = instance_settings
        self.image_settings = image_settings
        self.keypair_settings = keypair_settings

        self.__floating_ip_dict = dict()

        # Instantiated in self.create()
        self.__ports = list()

        # Note: this object does not change after the VM becomes active
        self.__vm = None

    def initialize(self):
        """
        Loads the existing VMInst, Port, FloatingIps
        :return: VMInst domain object
        """
        super(self.__class__, self).initialize()

        self.__neutron = neutron_utils.neutron_client(
            self._os_creds, self._os_session)
        self.__keystone = keystone_utils.keystone_client(
            self._os_creds, self._os_session)
        self.__cinder = cinder_utils.cinder_client(
            self._os_creds, self._os_session)
        self.__glance = glance_utils.glance_client(
            self._os_creds, self._os_session)

        self.__ports = self.__query_ports(self.instance_settings.port_settings)
        self.__lookup_existing_vm_by_name()

    def create(self, block=False):
        """
        Creates a VM instance and associated objects unless they already exist
        :param block: Thread will block until instance has either become
                      active, error, or timeout waiting.
                      Additionally, when True, floating IPs will not be applied
                      until VM is active.
        :return: VMInst domain object
        """
        self.initialize()

        if len(self.__ports) != len(self.instance_settings.port_settings):
            self.__ports = self.__create_ports(
                self.instance_settings.port_settings)
        if not self.__vm:
            self.__create_vm(block)

        return self.__vm

    def __lookup_existing_vm_by_name(self):
        """
        Populates the member variables 'self.vm' and 'self.floating_ips' if a
        VM with the same name already exists
        within the project
        """
        server = nova_utils.get_server(
            self._nova, self.__neutron, self.__keystone,
            vm_inst_settings=self.instance_settings)
        if server:
            if server.name == self.instance_settings.name:
                self.__vm = server
                logger.info(
                    'Found existing machine with name - %s',
                    self.instance_settings.name)

                fips = neutron_utils.get_port_floating_ips(
                    self.__neutron, self.__ports)
                for port_id, fip in fips:
                    settings = self.instance_settings.floating_ip_settings
                    for fip_setting in settings:
                        if port_id == fip_setting.port_id:
                            self.__floating_ip_dict[fip_setting.name] = fip
                        else:
                            port = neutron_utils.get_port_by_id(
                                self.__neutron, port_id)
                            if port and port.name == fip_setting.port_name:
                                self.__floating_ip_dict[fip_setting.name] = fip

    def __create_vm(self, block=False):
        """
        Responsible for creating the VM instance
        :param block: Thread will block until instance has either become
                      active, error, or timeout waiting. Floating IPs will be
                      assigned after active when block=True
        """
        self.__vm = nova_utils.create_server(
            self._nova, self.__keystone, self.__neutron, self.__glance,
            self.instance_settings, self.image_settings,
            self._os_creds.project_name, self.keypair_settings)
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
                nova_utils.add_security_group(self._nova, self.__vm,
                                              sec_grp_name)
            else:
                raise VmInstanceCreationError(
                    'Cannot applying security group with name ' +
                    sec_grp_name +
                    ' to VM that did not activate with name - ' +
                    self.instance_settings.name)

        if self.instance_settings.volume_names:
            for volume_name in self.instance_settings.volume_names:
                volume = cinder_utils.get_volume(
                    self.__cinder, self.__keystone, volume_name=volume_name,
                    project_name=self._os_creds.project_name)

                if volume and self.vm_active(block=True):
                    vm = nova_utils.attach_volume(
                        self._nova, self.__neutron, self.__keystone, self.__vm,
                        volume, self._os_creds.project_name)

                    if vm:
                        self.__vm = vm
                    else:
                        logger.warn(
                            'Volume [%s] attachment timeout ', volume.name)
                else:
                    logger.warn('Unable to attach volume named [%s]',
                                volume_name)

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
            self.add_floating_ip(floating_ip_setting)

    def add_floating_ip(self, floating_ip_setting):
        """
        Adds a floating IP to a running instance
        :param floating_ip_setting - the floating IP configuration
        :return: the floating ip object
        """
        port_dict = dict()
        for key, port in self.__ports:
            port_dict[key] = port

        # Apply floating IP
        port = port_dict.get(floating_ip_setting.port_name)

        if not port:
            raise VmInstanceCreationError(
                'Cannot find port object with name - ' +
                floating_ip_setting.port_name)

        # Setup Floating IP only if there is a router with an external
        # gateway
        ext_gateway = self.__ext_gateway_by_router(
            floating_ip_setting.router_name)
        if ext_gateway and self.vm_active(block=True):
            floating_ip = neutron_utils.create_floating_ip(
                self.__neutron, self.__keystone, ext_gateway, port.id)
            self.__floating_ip_dict[floating_ip_setting.name] = floating_ip

            logger.info(
                'Created floating IP %s via router - %s', floating_ip.ip,
                floating_ip_setting.router_name)

            return floating_ip
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
            self.__neutron, self.__keystone, router_name=router_name,
            project_name=self._os_creds.project_name)
        if router and router.external_network_id:
            network = neutron_utils.get_network_by_id(
                self.__neutron, router.external_network_id)
            if network:
                return network.name
        return None

    def clean(self):
        """
        Destroys the VM instance
        """

        # Cleanup floating IPs
        for name, floating_ip in self.__floating_ip_dict.items():
            logger.info('Deleting Floating IP - ' + floating_ip.ip)
            neutron_utils.delete_floating_ip(self.__neutron, floating_ip)

        self.__floating_ip_dict = dict()

        # Cleanup ports
        for name, port in self.__ports:
            logger.info('Deleting Port with ID - %s ', port.id)
            neutron_utils.delete_port(self.__neutron, port)

        self.__ports = list()

        if self.__vm:
            # Detach Volume
            for volume_rec in self.__vm.volume_ids:
                volume = cinder_utils.get_volume_by_id(
                    self.__cinder, volume_rec['id'])
                if volume:
                    vm = nova_utils.detach_volume(
                        self._nova, self.__neutron, self.__keystone, self.__vm,
                        volume, self._os_creds.project_name)
                    if vm:
                        self.__vm = vm
                    else:
                        logger.warn(
                            'Timeout waiting to detach volume %s', volume.name)
                else:
                    logger.warn('Unable to detach volume with ID - [%s]',
                                volume_rec['id'])

            # Cleanup VM
            logger.info(
                'Deleting VM instance - ' + self.instance_settings.name)

            try:
                nova_utils.delete_vm_instance(self._nova, self.__vm)
            except NotFound as e:
                logger.warn('Instance already deleted - %s', e)

            # Block until instance cannot be found or returns the status of
            # DELETED
            logger.info('Checking deletion status')

            if self.vm_deleted(block=True):
                logger.info(
                    'VM has been properly deleted VM with name - %s',
                    self.instance_settings.name)
                self.__vm = None
            else:
                logger.error(
                    'VM not deleted within the timeout period of %s '
                    'seconds', self.instance_settings.vm_delete_timeout)

        super(self.__class__, self).clean()

    def __query_ports(self, port_settings):
        """
        Returns the previously configured ports or an empty list if none
        exist
        :param port_settings: A list of PortSetting objects
        :return: a list of OpenStack port tuples where the first member is the
                 port name and the second is the port object
        """
        ports = list()

        for port_setting in port_settings:
            port = neutron_utils.get_port(
                self.__neutron, self.__keystone, port_settings=port_setting,
                project_name=self._os_creds.project_name)
            if port:
                ports.append((port_setting.name, port))

        return ports

    def __create_ports(self, port_settings):
        """
        Returns the previously configured ports or creates them if they do not
        exist
        :param port_settings: A list of PortSetting objects
        :return: a list of OpenStack port tuples where the first member is the
                 port name and the second is the port object
        """
        ports = list()

        for port_setting in port_settings:
            port = neutron_utils.get_port(
                self.__neutron, self.__keystone, port_settings=port_setting,
                project_name=self._os_creds.project_name)
            if not port:
                port = neutron_utils.create_port(
                    self.__neutron, self._os_creds, port_setting)
            if port:
                ports.append((port_setting.name, port))

        return ports

    def get_os_creds(self):
        """
        Returns the OpenStack credentials used to create these objects
        :return: the credentials
        """
        return self._os_creds

    def get_vm_inst(self):
        """
        Returns the latest version of this server object from OpenStack
        :return: Server object
        """
        return nova_utils.get_server_object_by_id(
            self._nova, self.__neutron, self.__keystone, self.__vm.id,
            self._os_creds.project_name)

    def get_console_output(self):
        """
        Returns the vm console object for parsing logs
        :return: the console output object
        """
        return nova_utils.get_server_console_output(self._nova, self.__vm)

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
                network = neutron_utils.get_network_by_id(
                    self.__neutron, port.network_id)
                subnet = neutron_utils.get_subnet(
                    self.__neutron, network, subnet_name=subnet_name)
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
        from warnings import warn
        warn('Do not use the returned dict() structure',
             DeprecationWarning)

        return nova_utils.get_server_info(self._nova, self.__vm)

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

        # When cannot be found above
        if len(self.__floating_ip_dict) > 0:
            for key, fip in self.__floating_ip_dict.items():
                return fip

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
            self.get_image_user(),
            ssh_priv_key_file_path=self.keypair_settings.private_filepath,
            variables=variables, proxy_setting=self._os_creds.proxy_settings)

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
        Returns true when the VM status returns the value of the constant
        STATUS_ACTIVE
        :param block: When true, thread will block until active or timeout
                      value in seconds has been exceeded (False)
        :param poll_interval: The polling interval in seconds
        :return: T/F
        """
        if self.__vm_status_check(
                STATUS_ACTIVE, block, self.instance_settings.vm_boot_timeout,
                poll_interval):
            self.__vm = nova_utils.get_server_object_by_id(
                self._nova, self.__neutron, self.__keystone, self.__vm.id,
                self._os_creds.project_name)
            return True
        return False

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
            if expected_status_code == STATUS_DELETED:
                return True
            else:
                return False

        status = nova_utils.get_server_status(self._nova, self.__vm)
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

    def vm_ssh_active(self, user_override=None, password=None, block=False,
                      timeout=None, poll_interval=POLL_INTERVAL):
        """
        Returns true when the VM can be accessed via SSH
        :param user_override: overrides the user with which to create the
                              connection
        :param password: overrides the use of a password instead of a private
                         key with which to create the connection
        :param block: When true, thread will block until active or timeout
                      value in seconds has been exceeded (False)
        :param timeout: the number of seconds to retry obtaining the connection
                        and overrides the ssh_connect_timeout member of the
                        self.instance_settings object
        :param poll_interval: The polling interval
        :return: T/F
        """
        # sleep and wait for VM status change
        logger.info('Checking if VM is active')

        if not timeout:
            timeout = self.instance_settings.ssh_connect_timeout

        if self.vm_active(block=True):
            if block:
                start = time.time()
            else:
                start = time.time() - timeout

            while timeout > time.time() - start:
                status = self.__ssh_active(
                    user_override=user_override, password=password)
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

    def __ssh_active(self, user_override=None, password=None):
        """
        Returns True when can create a SSH session else False
        :return: T/F
        """
        if len(self.__floating_ip_dict) > 0:
            ssh = self.ssh_client(
                user_override=user_override, password=password)
            if ssh:
                ssh.close()
                return True
        return False

    def cloud_init_complete(self, block=False, poll_interval=POLL_INTERVAL):
        """
        Returns true when the VM's cloud-init routine has completed.
        Note: this is currently done via SSH, therefore, if this instance does
              not have a Floating IP or a running SSH server, this routine
              will always return False or raise an Exception
        :param block: When true, thread will block until active or timeout
                      value in seconds has been exceeded (False)
        :param poll_interval: The polling interval
        :return: T/F
        """
        # sleep and wait for VM status change
        logger.info('Checking if cloud-init has completed')

        timeout = self.instance_settings.cloud_init_timeout

        if self.vm_active(block=True) and self.vm_ssh_active(block=True):
            if block:
                start = time.time()
            else:
                start = time.time() - timeout

            while timeout > time.time() - start:
                status = self.__cloud_init_complete()
                if status:
                    logger.info('cloud-init complete for VM instance')
                    return True

                logger.debug('Retry cloud-init query in ' + str(
                    poll_interval) + ' seconds')
                time.sleep(poll_interval)
                logger.debug('cloud-init complete timeout in ' + str(
                    timeout - (time.time() - start)))

        logger.error('Timeout waiting for cloud-init to complete')
        return False

    def __cloud_init_complete(self):
        """
        Returns True when can create a SSH session else False
        :return: T/F
        """
        if len(self.__floating_ip_dict) > 0:
            ssh = self.ssh_client()
            if ssh:
                stdin1, stdout1, sterr1 = ssh.exec_command(
                    'ls -l /var/lib/cloud/instance/boot-finished')
                return stdout1.channel.recv_exit_status() == 0
        return False

    def get_floating_ip(self, fip_name=None):
        """
        Returns the floating IP object byt name if found, else the first known,
        else None
        :param fip_name: the name of the floating IP to return
        :return: the SSH client or None
        """
        if fip_name and self.__floating_ip_dict.get(fip_name):
            return self.__floating_ip_dict.get(fip_name)
        else:
            return self.__get_first_provisioning_floating_ip()

    def ssh_client(self, fip_name=None, user_override=None, password=None):
        """
        Returns an SSH client using the name or the first known floating IP if
        exists, else None
        :param fip_name: the name of the floating IP to return
        :param user_override: the username to use instead of the default
        :param password: the password to use instead of the private key
        :return: the SSH client or None
        """
        fip = self.get_floating_ip(fip_name)

        ansible_user = self.get_image_user()
        if user_override:
            ansible_user = user_override

        if password:
            private_key = None
        else:
            private_key = self.keypair_settings.private_filepath

        if fip:
            return ansible_utils.ssh_client(
                self.__get_first_provisioning_floating_ip().ip,
                ansible_user,
                private_key_filepath=private_key,
                password=password,
                proxy_settings=self._os_creds.proxy_settings)
        else:
            FloatingIPAllocationError(
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
            nova_utils.add_security_group(self._nova, self.get_vm_inst(),
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
            nova_utils.remove_security_group(self._nova, self.get_vm_inst(),
                                             security_group)
            return True
        except NotFound as e:
            logger.warning('Security group not removed - ' + str(e))
            return False

    def reboot(self, reboot_type=RebootType.soft):
        """
        Issues a reboot call
        :param reboot_type: instance of
                            snaps.openstack.utils.nova_utils.RebootType
                            enumeration
        :return:
        """
        nova_utils.reboot_server(
            self._nova, self.__vm, reboot_type=reboot_type)


def generate_creator(os_creds, vm_inst, image_config, project_name,
                     keypair_config=None):
    """
    Initializes an OpenStackVmInstance object
    :param os_creds: the OpenStack credentials
    :param vm_inst: the SNAPS-OO VmInst domain object
    :param image_config: the associated ImageConfig object
    :param project_name: the associated project ID
    :param keypair_config: the associated KeypairConfig object (optional)
    :return: an initialized OpenStackVmInstance object
    """
    session = keystone_utils.keystone_session(os_creds)
    nova = nova_utils.nova_client(os_creds, session)
    keystone = keystone_utils.keystone_client(os_creds, session)
    neutron = neutron_utils.neutron_client(os_creds, session)

    try:
        derived_inst_config = settings_utils.create_vm_inst_config(
            nova, keystone, neutron, vm_inst, project_name)

        derived_inst_creator = OpenStackVmInstance(
            os_creds, derived_inst_config, image_config, keypair_config)
        derived_inst_creator.initialize()
        return derived_inst_creator
    finally:
        keystone_utils.close_session(session)


class VmInstanceSettings(VmInstanceConfig):
    """
    Deprecated, use snaps.config.vm_inst.VmInstanceConfig instead
    """
    def __init__(self, **kwargs):
        from warnings import warn
        warn('Use snaps.config.vm_inst.VmInstanceConfig instead',
             DeprecationWarning)
        super(self.__class__, self).__init__(**kwargs)


class FloatingIpSettings(FloatingIpConfig):
    """
    Deprecated, use snaps.config.vm_inst.FloatingIpConfig instead
    """
    def __init__(self, **kwargs):
        from warnings import warn
        warn('Use snaps.config.vm_inst.FloatingIpConfig instead',
             DeprecationWarning)
        super(self.__class__, self).__init__(**kwargs)


class VmInstanceCreationError(Exception):
    """
    Exception to be thrown when an VM instance cannot be created
    """


class FloatingIPAllocationError(Exception):
    """
    Exception to be thrown when an VM instance cannot allocate a floating IP
    """
