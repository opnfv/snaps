**********************
SNAPS-OO Library Usage
**********************

The pattern used within the SNAPS-OO library for creating OpenStack
instances have been made as consistent as possible amongst the different
instance types. Each consists of a constructor that takes in a
credentials object and generally takes in a single "settings"
(configuration) object. The only exception to this rule is with the
OpenStackVMInstance (creates an OpenStack Server) where it takes in the
additional settings used for the associated image and SSH key-pairs
credentials as those objects contain additional attributes required of
SNAPS, primarily when one needs to obtain remote access. After
instantiation, the create() method must be called to initiate all of the
necessary remote API calls to OpenStack required for proper instance
creation.

SNAPS Credentials
=================

As communicating with OpenStack is performed via secure remote RESTful
API calls, any function or method performing any type of query or CRUD
operation must know how to connect to the NFVI. The class ***OSCreds***
defined in *snaps.openstack.os\_credentials.py* contains everything
required to connect to any Keystone v2.0 or v3 authorization server. The
attributes are listed below:

-  username
-  password
-  auth\_url
-  project\_name (aka. tenant\_name)
-  identity\_api\_version (for obtaining Keystone authorization token.
   default = 2, Versions 2.0 & v3 only validated.)
-  image\_api\_version (default = 2, Glance version 1 & 2 only validated)
-  network\_api\_version (Neutron version 2 currently only validated)
-  compute\_api\_version (Nova version 2 currently only validated)
-  heat\_api\_version (Heat version 1 currently only validated)
-  volume\_api\_version (default = 2, Heat versions 2 & 3 currently only validated)
-  user\_domain\_id (default='default')
-  user\_domain\_name (default='Default')
-  project\_domain\_id (default='default')
-  project\_domain\_name (default='Default')
-  interface (default='admin', used to specify the endpoint type for keystone: public, admin, internal)
-  cacert (default=False, expected values T|F to denote server certificate verification, else value contains the path to an HTTPS certificate)
-  region_name (The region name default=None)
-  proxy\_settings

   -  host (the HTTP proxy host)
   -  port (the HTTP proxy port)
   -  https\_host (the HTTPS proxy host, default value of host)
   -  https\_port (the HTTPS proxy port, default value of port)
   -  ssh\_proxy\_cmd (same as the value placed into ssh -o
      ProxyCommand='<this config value>')

Create OS Credentials Object
----------------------------

.. code:: python

    from snaps.openstack.os_credentials import OSCreds
    os_creds=OSCreds(username='admin', password='admin',
                     auth_url='http://localhost:5000/v3', project_name='admin',
                     identity_api_version=3)

SNAPS Object Creators
=====================

Each creator minimally requires an OSCreds object for connecting to the
NFVI, associated \*Settings object for instance configuration, create()
method to make the necessary remote API calls and create all of the
necessary OpenStack instances required, and clean() method that is
responsible for deleting all associated OpenStack instances. Please see
the class diagram `here </display/SNAP/SNAPS-OO+Classes>`__. Below is a
textual representation of the requirements of each creator classes with
their associated setting classes and a sample code snippet on how to use
the code.

Create User
-----------
-  User - snaps.openstack.create\_user.OpenStackUser

   -  snaps.openstack.user.UserConfig

      -  name - the username (required)
      -  password - the user's password (required)
      -  project\_name - the name of the project to associated to this
         user (optional)
      -  domain\_name - the user's domain (default='default')
      -  email - the user's email address (optional)
      -  enabled - flag to determine whether or not the user should be
         enabled (default=True)
      -  roles - dict where key is the role's name and value is the name
         the project to associate with the role (optional)

.. code:: python

    from snaps.config.user import UserConfig
    from snaps.openstack.create_user import OpenStackUser
    user_settings = UserConfig(name='username', password='password')
    user_creator = OpenStackUser(os_creds, user_settings)
    user_creator.create()

    # Retrieve OS creds for new user for creating other OpenStack instance
    user_creds = user_creator.get_os_creds(os_creds.project_name)

    # Perform logic
    ...

    # Cleanup
    user_creator.clean()

Create Project
--------------
-  Project - snaps.openstack.create\_project.OpenStackProject

   -  snaps.openstack.project.ProjectConfig

      -  name - the project name (required)
      -  domain - the project's domain (default='default')
      -  description - the project's description (optional)
      -  enabled - flag to determine whether or not the project should
         be enabled (default=True)


.. code:: python

    from snaps.openstack.project import ProjectConfig
    from snaps.openstack.create_project import OpenStackProject
    project_settings = ProjectConfig(name='username', password='password')
    project_creator = OpenStackProject(os_creds, project_settings)
    project_creator.create()

    # Perform logic
    ...

    # Cleanup
    project_creator.clean()

Create Flavor
-------------
-  Flavor - snaps.openstack.create\_flavor.OpenStackFlavor

   -  snaps.config.flavor.FlavorConfig

      -  name - the flavor name (required)
      -  flavor\_id - the flavor's string ID (default='auto')
      -  ram - memory in MB to allocate to VM (required)
      -  disk - disk storage in GB (required)
      -  vcpus - the number of CPUs to allocate to VM (required)
      -  ephemeral - the size of the ephemeral disk in GB (default=0)
      -  swap - the size of the swap disk in GB (default=0)
      -  rxtx\_factor - the receive/transmit factor to be set on ports
         if backend supports QoS extension (default=1.0)
      -  is\_public - flag that denotes whether or not other projects
         can access image (default=True)
      -  metadata - freeform dict() for special metadata (optional)

.. code:: python

    from snaps.config.flavor import FlavorConfig
    from snaps.openstack.create_flavor import OpenStackFlavor
    flavor_settings = FlavorConfig(name='flavor-name', ram=4, disk=10, vcpus=2)
    flavor_creator = OpenStackFlavor(os_creds, flavor_settings)
    flavor_creator.create()

    # Perform logic
    ...

    # Cleanup
    flavor_creator.clean()

Create Image
------------
-  Image - snaps.openstack.create\_image.OpenStackImage

   -  snaps.config.image.ImageConfig

      -  name - the image name (required)
      -  image\_user - the default image user generally used by
         OpenStackVMInstance class for obtaining an SSH connection
         (required)
      -  img\_format or format - the image's format (i.e. qcow2) (required)
      -  url - the download URL to obtain the image file (this or
         image\_file must be configured, not both)
      -  image\_file - the location of the file to be sourced from the
         local filesystem (this or url must be configured, not both)
      -  extra\_properties - dict() object containing extra parameters to
         pass when loading the image (i.e. ids of kernel and initramfs images)
      -  nic\_config\_pb\_loc - the location of the ansible playbook
         that can configure additional NICs. Floating IPs are required
         to perform this operation. (optional and deprecated)
      -  kernel\_image\_settings - the image settings for a kernel image (optional)
      -  ramdisk\_image\_settings - the image settings for a ramdisk image (optional)
      -  public - image will be created with public visibility when True (default = False)


.. code:: python

    from snaps.openstack.create_image import OpenStackImage
    from snaps.config.image import ImageConfig
    image_settings = ImageConfig(name='image-name', image_user='ubuntu', img_format='qcow2',
                                 url='http://uec-images.ubuntu.com/releases/trusty/14.04/ubuntu-14.04-server-cloudimg-amd64-disk1.img')
    image_creator = OpenStackImage(os_creds, image_settings)
    image_creator.create()

    # Perform logic
    ...

    # Cleanup
    image_creator.clean()

Create Keypair
--------------
-  Keypair - snaps.openstack.create\_keypair.OpenStackKeypair

   -  snaps.openstack.keypair.KeypairConfig

      -  name - the keypair name (required)
      -  public\_filepath - the file location to where the public key is
         to be written or currently resides (optional)
      -  private\_filepath - the file location to where the private key
         file is to be written or currently resides (optional but highly
         recommended to leverage or the private key will be lost
         forever)
      -  key\_size - The number of bytes for the key size when it needs to
         be generated (value must be >=512, default = 1024)
      -  delete\_on\_clean - when True, the key files will be deleted when
         OpenStackKeypair#clean() is called (default = False)

.. code:: python

    from snaps.openstack.keypair.KeypairConfig
    from snaps.openstack.create_keypairs import OpenStackKeypair
    keypair_settings = KeypairConfig(name='kepair-name', private_filepath='/tmp/priv-kp')
    keypair_creator = OpenStackKeypair(os_creds, keypair_settings)
    keypair_creator.create()

    # Perform logic
    ...

    # Cleanup
    keypair_creator.clean()

Create Network
--------------

-  Network - snaps.openstack.create\_network.OpenStackNetwork

   -  snaps.config_network.NetworkConfig

      -  name - the name of the network (required)
      -  admin\_state\_up - flag denoting the administrative status of
         the network (True = up, False = down)
      -  shared - flag indicating whether the network can be shared
         across projects/tenants (default=True)
      -  project\_name - the name of the project (optional - can only be
         set by admin users)
      -  external - flag determining if network has external access
         (default=False)
      -  network\_type - the type of network (i.e. vlan\|vxlan\|flat)
      -  physical\_network - the name of the physical network (required
         when network\_type is 'flat')
      -  segmentation\_id - the id of the segmentation (required
         when network\_type is 'vlan')
      -  subnet\_settings (list of optional
         snaps.config.network.SubnetConfig objects)

         -  cidr - the subnet's CIDR (required)
         -  ip\_version - 4 or 6 (default=4)
         -  name - the subnet name (required)
         -  project\_name - the name of the project (optional - can only
            be set by admin users)
         -  start - the start address for the allocation pools
         -  end - the end address for the allocation pools
         -  gateway\_ip - the gateway IP
         -  enable\_dhcp - flag to determine whether or not to enable
            DHCP (optional)
         -  dns\_nameservers - a list of DNS nameservers
         -  host\_routes - list of host route dictionaries for subnet
            (optional, see pydoc and Neutron API for more details)
         -  destination - the destination for static route (optional)
         -  nexthop - the next hop for the destination (optional)
         -  ipv6\_ra\_mode - valid values include: 'dhcpv6-stateful',
            'dhcp6v-stateless', 'slaac' (optional)
         -  ipvc\_address\_mode - valid values include:
            'dhcpv6-stateful', 'dhcp6v-stateless', 'slaac' (optional)

.. code:: python

    from snaps.config.network import NetworkConfig, SubnetConfig
    from snaps.openstack.create_network import OpenStackNetwork

    subnet_settings = SubnetConfig(name='subnet-name', cidr='10.0.0.0/24')
    network_settings = NetworkConfig(name='network-name', subnet_settings=[subnet_settings])

    network_creator = OpenStackNetwork(os_creds, network_settings)
    network_creator.create()

    # Perform logic
    ...

    # Cleanup
    network_creator.clean()

Create Security Group
---------------------

-  Security Group -
   snaps.openstack.create\_security\_group.OpenStackSecurityGroup

   -  snaps.openstack.create\_security\_group.SecurityGroupSettings

      -  name - the security group's name (required)
      -  description - the description (optional)
      -  project\_name - the name of the project (optional - can only be
         set by admin users)
      -  rule\_settings (list of
         optional snaps.openstack.create\_security\_group.SecurityGroupRuleSettings
         objects)

         -  sec\_grp\_name - the name of the associated security group
            (required)
         -  description - the description (optional)
         -  direction - enum
            snaps.openstack.create\_security\_group.Direction (required)
         -  remote\_group\_id - the group ID to associate with this rule
         -  protocol -
            enum snaps.openstack.create\_security\_group.Protocol
            (optional)
         -  ethertype -
            enum snaps.openstack.create\_security\_group.Ethertype
            (optional)
         -  port\_range\_min - the max port number in the range that is
            matched by the security group rule (optional)
         -  port\_range\_max - the min port number in the range that is
            matched by the security group rule (optional)
         -  sec\_grp\_rule - the rule object to a security group rule
            object to associate (note: does not work currently)
         -  remote\_ip\_prefix - the remote IP prefix to associate with
            this metering rule packet (optional)

.. code:: python

    from snaps.config.network import SubnetConfig
    from snaps.config.rule import RuleConfig
    from snaps.openstack.create_security_group import SecurityGroupSettings, SecurityGroupRuleSettings, Direction, OpenStackSecurityGroup

    rule_settings = RuleConfig(name='subnet-name', cidr='10.0.0.0/24')
    network_settings = SubnetConfig(name='network-name', subnet_settings=[subnet_settings])

    sec_grp_name = 'sec-grp-name'
    rule_settings = SecurityGroupRuleSettings(name=sec_grp_name, direction=Direction.ingress)
    security_group_settings = SecurityGroupSettings(name=sec_grp_name, rule_settings=[rule_settings])

    security_group_creator = OpenStackSecurityGroup(os_creds, security_group_settings)
    security_group_creator.create()

    # Perform logic
    ...

    # Cleanup
    security_group_creator.clean()

Create Router
-------------

-  Router - snaps.openstack.create\_router.OpenStackRouter

   -  snaps.openstack.router.RouterConfig

      -  name - the router name (required)
      -  project\_name - the name of the project (optional - can only be
         set by admin users)
      -  external\_gateway - the name of the external network (optional)
      -  admin\_state\_up - flag to denote the administrative status of
         the router (default=True)
      -  external\_fixed\_ips - dictionary containing the IP address
         parameters (parameter not tested)
      -  internal\_subnets - list of subnet names to which this router
         will connect (optional)
      -  port\_settings (list of optional
         snaps.config.network.PortConfig objects) - creates
         custom ports to internal subnets (similar to internal\_subnets
         with more control)

         -  name - the port's display name
         -  network\_name - the name of the network on which to create the port
         -  admin\_state\_up - A boolean value denoting the administrative
            status of the port (default = True)
         -  project\_name - the name of the project (optional - can only
            be set by admin users)
         -  mac\_address - the port's MAC address to set (optional and
            recommended not to set this configuration value)
         -  ip\_addrs - list of dict() objects containing two keys 'subnet_name'
            and 'ip' where the value of the 'ip' entry is the expected IP
            address assigned. This value gets mapped to the fixed\_ips
            attribute (optional)
         -  fixed\_ips - dict() where the key is the subnet ID and value is the
            associated IP address to assign to the port (optional)
         -  security\_groups - list of security group IDs (not tested)
         -  allowed\_address\_pairs - A dictionary containing a set of zero or
            more allowed address pairs. An address pair contains an IP address
            and MAC address (optional)
         -  opt\_value - the extra DHCP option value (optional)
         -  opt\_name - the extra DHCP option name (optional)
         -  device\_owner - The ID of the entity that uses this port.
            For example, a DHCP agent (optional)
         -  device\_id - The ID of the device that uses this port.
            For example, a virtual server (optional)

.. code:: python

    from snaps.config.router import RouterConfig
    from snaps.openstack.create_router import OpenStackRouter

    router_settings = RouterConfig(name='router-name', external_gateway='external')
    router_creator = OpenStackRouter(os_creds, router_settings)
    router_creator.create()

    # Perform logic
    ...

    # Cleanup
    router_creator.clean()

Create QoS Spec
---------------

-  Volume Type - snaps.openstack.create\_qos.OpenStackQoS

   -  snaps.openstack.qos.QoSConfig

      -  name - the volume type's name (required)
      -  consumer - the qos's consumer type of the enum type Consumer (required)
      -  specs - freeform dict() to be added as 'specs' (optional)

.. code:: python

    from snaps.openstack.qos import QoSConfig
    from snaps.openstack.create_qos import OpenStackQoS

    qos_settings = QoSConfig(name='stack-name', consumer=Consumer.front-end)
    qos_creator = OpenStackQoS(os_creds, vol_type_settings)
    qos_creator.create()

    # Perform logic
    ...

    # Cleanup
    qos_creator.clean()

Create Volume Type
------------------

-  Volume Type - snaps.openstack.create\_volume\_type.OpenStackVolumeType

   -  snaps.config.volume\_type.VolumeTypeConfig

      -  name - the volume type's name (required)
      -  description - the volume type's description (optional)
      -  encryption - instance or config for VolumeTypeEncryptionConfig (optional)
      -  qos\_spec\_name - name of the QoS Spec to associate (optional)
      -  public - instance or config for VolumeTypeEncryptionConfig (optional)

.. code:: python

    from snaps.config.volume_type import VolumeTypeConfig
    from snaps.openstack.create_volume_type import OpenStackVolumeType

    vol_type_settings = VolumeTypeConfig(name='stack-name')
    vol_type_creator = OpenStackHeatStack(os_creds, vol_type_settings)
    vol_type_creator.create()

    # Perform logic
    ...

    # Cleanup
    vol_type_creator.clean()

Create Volume
-------------

-  Volume - snaps.openstack.create\_volume.OpenStackVolume

   -  snaps.config.volume.VolumeConfig

      -  name - the volume type's name (required)
      -  description - the volume type's description (optional)
      -  size - size of volume in GB (default = 1)
      -  image_name - when a glance image is used for the image source (optional)
      -  type\_name - the associated volume's type name (optional)
      -  availability\_zone - the name of the compute server on which to
         deploy the volume (optional)
      -  multi_attach - when true, volume can be attached to more than one
         server (default = False)

.. code:: python

    from snaps.config.volume import VolumeConfig
    from snaps.openstack.create\_volume import OpenStackVolume

    vol_settings = VolumeConfig(name='stack-name')
    vol_creator = OpenStackVolume(os_creds, vol_settings)
    vol_creator.create()

    # Perform logic
    ...

    # Cleanup
    vol_type_creator.clean()

Create Heat Stack
-----------------

-  Heat Stack - snaps.openstack.create\_stack.OpenStackHeatStack

   -  snaps.config.stack.StackConfig

      -  name - the stack's name (required)
      -  template - the heat template in dict() format (required when
         template_path is None)
      -  template\_path - the location of the heat template file (required
         when template is None)
      -  env\_values - dict() of strings for substitution of template
         default values (optional)

.. code:: python

    from snaps.config.stack import StackConfig
    from snaps.openstack.create_stack import OpenStackHeatStack

    stack_settings = StackConfig(name='stack-name', template_path='/tmp/template.yaml')
    stack_creator = OpenStackHeatStack(os_creds, stack_settings)
    stack_creator.create()

    # Perform logic
    ...

    # Cleanup
    stack_creator.clean()

Create VM Instance
------------------

-  VM Instances - snaps.openstack.create\_instance.OpenStackVmInstance

   -  snaps.openstack.create\_instance.VmInstanceSettings

      -  name - the name of the VM (required)
      -  flavor - the name of the flavor (required)
      -  port\_settings - list of
         snaps.config.network.PortConfig objects where each
         denote a NIC (see above in create router section for details)
         API does not require, but newer NFVIs now require VMs have at
         least one network
      -  security\_group\_names - a list of security group names to
         apply to VM
      -  floating\_ip\_settings (list of
         snaps.openstack\_create\_instance.FloatingIpSettings objects)

         -  name - a name to a floating IP for easy lookup 
         -  port\_name - the name of the VM port on which the floating
            IP should be applied (required)
         -  router\_name - the name of the router to the external
            network (required)
         -  subnet\_name - the name of the subnet on which to attach the
            floating IP (optional)
         -  provisioning - when true, this floating IP will be used for
            provisioning which will come into play once we are able to
            get multiple floating IPs working.

      -  sudo\_user - overrides the image\_settings.image\_user value
         when attempting to connect via SSH
      -  vm\_boot\_timeout - the number of seconds that the thread will
         block when querying the VM's status when building (default=900)
      -  vm\_delete\_timeout - the number of seconds that the thread
         will block when querying the VM's status when deleting
         (default=300)
      -  ssh\_connect\_timeout - the number of seconds that the thread
         will block when attempting to obtain an SSH connection
         (default=180)
      -  availability\_zone - the name of the compute server on which to
         deploy the VM (optional must be admin)
      -  userdata - the cloud-init script to execute after VM has been
         started

   -  image\_settings - see snaps.config.image.ImageConfig
      above (required)
   -  keypair\_settings - see
      snaps.openstack.keypair.KeypairConfig above (optional)

.. code:: python

    from snaps.openstack.create_instance import VmInstanceSettings, FloatingIpSettings, OpenStackVmInstance
    from snaps.config.network import PortConfig

    port_settings = PortConfig(name='port-name', network_name=network_settings.name)
    floating_ip_settings = FloatingIpSettings(name='fip1', port_name=port_settings.name, router_name=router_settings.name)
    instance_settings = VmInstanceSettings(name='vm-name', flavor='flavor_settings.name', port_settings=[port_settings],
                                           floating_ip_settings=[floating_ip_settings])

    instance_creator = OpenStackVmInstance(os_creds, instance_settings, image_settings, kepair_settings)
    instance_creator.create()

    # Perform logic
    ...
    ssh_client = instance_creator.ssh_client()
    ...

    # Cleanup
    instance_creator.clean()

Ansible Provisioning
====================

Being able to easily create OpenStack instances such as virtual networks
and VMs is a good start to the problem of NFV; however, an NFVI is
useless unless there is some software performing some function. This is
why we added Ansible playbook support to SNAPS-OO which can be located
in snaps.provisioning.ansible\_utils#apply\_playbook. See below for a
description of that function's parameters:

-  playbook\_path - the file location of the ansible playbook
-  hosts\_inv - a list of hosts/IP addresses to which the playbook will
   be applied
-  host\_user - the user (preferably sudo) to use for applying the
   playbook
-  ssh\_priv\_key\_file\_path - the location to the private key file
   used for SSH
-  variables - a dict() of substitution values for Jinga2 templates
   leveraged by Ansible
-  proxy\_setting - used to extract the SSH proxy command (optional)

Apply Ansible Playbook Utility
------------------------------

.. code:: python

    from snaps.provisioning import ansible_utils

    ansible_utils.apply_playbook(playbook_path='provisioning/tests/playbooks/simple_playbook.yml',
                                 hosts_inv=[ip], host_user=user, ssh_priv_key_file_path=priv_key,
                                 proxy_setting=self.os_creds.proxy_settings)

OpenStack Utilities
===================

For those who do like working procedurally, SNAPS-OO also leverages
utilitarian functions for nearly every query or request made to
OpenStack. This pattern will make it easier to deal with API version
changes as they would all be made in one place. (see keystone\_utils for
an example of this pattern as this is the only API where SNAPS is
supporting more than one version)

-  snaps.openstack.utils.keystone\_utils - for calls to the Keystone
   APIs (support for versions 2 & 3)
-  snaps.openstack.utils.glance\_utils - for calls to the Glance APIs
   (support for versions 1 & 2)
-  snaps.openstack.utils.neutron\_utils - for calls to the Neutron APIs
   (version 2)
-  snaps.openstack.utils.nova\_utils - for calls to the Nova APIs (version 2)
-  snaps.openstack.utils.heat\_utils - for calls to the Heat APIs (version 1)
-  snaps.openstack.utils.cinder\_utils - for calls to the Cinder APIs
   (support for versions 2 & 3)
