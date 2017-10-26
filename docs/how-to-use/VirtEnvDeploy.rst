Try an example
==============

Use launcher.py to deploy and clean up example environments.  These examples are described in YAML files.

#. Add your OpenStack connection information.

    Edit <path to repo>/examples/inst-w-volume/deploy-env.yaml with your OpenStack
    credentials and authorization URL

   -  openstack: the top level tag that denotes configuration for the OpenStack components

   -  connection: - contains the credentials and endpoints required to
      connect with OpenStack
   -  username: - the project's user (required)
   -  password: - the tentant's user password (required)
   -  auth\_url: - the URL to the OpenStack APIs (required)
   -  project\_name: - the name of the OpenStack project for the user
      (required)
   -  http\_proxy: - the {{ host }}:{{ port }} of the proxy server (optional)

#. Go to the examples directory.

    ::

      cd <snaps repo>/examples/

#. Deploy the launcher.

    ::

      python launch.py -t ./inst-w-volume/deploy-vm-with-volume.yaml -e ./inst-w-volume/deploy-env.yaml -d

#. Clean the deployment.

    ::

      python launch.py -t ./complex-network/deploy-complex-network.yaml -e ./inst-w-volume/deploy-env.yaml -c

#. Customize the deployment by changing the yaml file.

    The configuration file used to deploy and provision a virtual environment has been designed to describe the required
    images, networks, SSH public and private keys, associated VMs, as well as any required post deployment provisioning
    tasks.

-  openstack: the top level tag that denotes configuration for the
   OpenStack components

   -  connections: the different connections/credentials to be used by the
      launcher application

       -  connection: the credentials and endpoints required to connect to an
          OpenStack project/tenant

          -  name: the name of the credentials for use when creating objects (required)
          -  username: the project's user (required)
          -  password: the tentant's user password (required)
          -  auth\_url: the URL to the OpenStack APIs (required)
          -  project\_name: the name of the OpenStack project for the user
             (required)
          -  identity\_api\_version: the Keystone client version to use (default = 2)
          -  image\_api\_version: the Glance client version to use (default = 2)
          -  network\_api\_version: the Neutron client version to use (default = 2)
          -  compute\_api\_version: the Nova client version to use (default = 2)
          -  heat\_api\_version: the Heat client version to use (default = 1)
          -  volume\_api\_version: the Cinder client version to use (default = 2)
          -  user\_domain\_id: the user domain ID to use (default = 'default')
          -  user\_domain\_name: the user domain name to use (default = 'Default')
          -  project\_domain\_id: the project domain ID to use (default = 'default')
          -  project\_domain\_name: the project domain name to use (default = 'Default')
          -  interface: Used to specify the endpoint type for keystone (default = 'public')
          -  cacert: True for https or the certification file location (default = False)
          -  region\_name: the region (default = None)
          -  proxy\_settings: for accessing APIs hidden behind an HTTP proxy

              - host: hostname or IP of HTTP proxy host (required)
              - port: port number of the HTTP proxy server (required)
              - http\_host: hostname or IP of HTTPS proxy host (default = host)
              - port: port number of the HTTPS proxy server (default = port)
              - ssh\_proxy\_cmd: the OpenSSH command used to access the SSH port
                of a VM (optional)

   -  projects: the projects/tenants to create

       -  project: a project/tenant to create (admin user credentials required)

          -  os\_creds\_name: the connection name (default = 'default'
             required or use "os\_user" below instead)
          -  name: the project's name (required)
          -  domain or domain_name: the project's domain name (default = 'Default')
          -  description: the description (optional)
          -  users: a list of users to associate to the project (optional)
          -  enabled: when True the project will be enabled on creation (default = True)

   -  users: the users to create

       -  user: a user to create (admin user credentials required)

          -  os\_creds\_name: the connection name (required)
          -  name: the username (required)
          -  password: the user's password (required)
          -  project\_name: the user's primary project name (optional)
          -  domain\_name: the user's domain name (default = 'Default')
          -  email: the user's email address (optional)
          -  roles: dict where key is the role's name and value is the name
             of the project to associate with the role (optional)

   -  flavors: the flavors to create

       -  flavor: a flavor to create (admin user credentials required)

          -  os\_creds\_name: the connection name (default = 'default'
             required or use "os\_user" below instead)
          -  name: the name (required)
          -  flavor\_id: the string ID (default 'auto')
          -  ram: the required RAM in MB (required)
          -  disk: the size of the root disk in GB (required)
          -  vcpus: the number of virtual CPUs (required)
          -  ephemeral: the size of the ephemeral disk in GB (default 0)
          -  swap: the size of the dedicated swap disk in GB (default 0)
          -  rxtx\_factor: the receive/transmit factor to be set on ports if
             backend supports QoS extension (default 1.0)
          -  is\_public: denotes whether or not the flavor is public (default = True)
          -  metadata: freeform dict() for special metadata (optional)

   -  qos_specs: the QoS Specs to create

       -  qos_spec: a QoS Spec to create (admin user credentials required)

          -  os\_creds\_name: the connection name (default = 'default'
             required or use "os\_user" below instead)
          -  name: the name (required)
          -  consumer: enumerations: 'front-end', 'back-end', 'both' (required)
          -  specs: dict of custom values (optional)

   -  volume_types: the Volume Type to create

       -  volume_type: a Volume Type to create (admin user credentials required)

          -  os\_creds\_name: the connection name (default = 'default'
             required or use "os\_user" below instead)
          -  name: the name (required)
          -  description: the description (optional)
          -  qos_spec_name: the name of the associate QoS Spec (optional)
          -  public: visibility (default - False)
          -  encryption: the encryption settings (optional)

             -  name: the name (required)
             -  provider_class: the provider class (required i.e. LuksEncryptor)
             -  control_location: enumerations: 'front-end', 'back-end' (required)
             -  cipher: the encryption algorithm/mode to use (optional)
             -  key_size: the size of the encryption key, in bits (optional)

   -  volumes: the Volume to create

       -  volume: a Volume to create

          -  os\_creds\_name: the connection name (default = 'default'
             required or use "os\_user" below instead)
          -  os\_user: the connection from a new user defined in template
             (required or use "os\_creds\_name" above

              - name: the user's name (required)
              - project\_name: the project name to use

          -  name: the name (required)
          -  description: the description (optional)
          -  size: the volume size in GB (default = 1)
          -  image_name: the image name to leverage (optional)
          -  type_name: the volume type name to associate (optional)
          -  availability_zone: the zone name on which to deploy (optional)
          -  multi_attach: when true, volume can be attached to more than one VM
             (default = False)

   -  images: describes each image to create

       -  image:

          -  os\_creds\_name: the connection name (default = 'default'
             required or use "os\_user" below instead)
          -  os\_user: the connection from a new user defined in template
             (required or use "os\_creds\_name" above

              - name: the user's name (required)
              - project\_name: the project name to use

          -  name: The unique image name. If the name already exists for
             your project, a new one will not be created (required)
          -  image\_user: the image's default sudo user (required)
          -  format or img\_format: the image format type (required i.e. qcow2)
          -  url or download\_url: The HTTP download location of the image file
             (required when "image_file" below has not been configured)
          -  image\_file: the image file location (required when "url" has not
             been configured)
          -  kernel\_image\_settings: the settings for a kernel image (optional)
          -  ramdisk\_image\_settings: the settings for a kernel image (optional)
          -  public: publically visibile when True (default = True)

   -  networks:
       -  network:

          -  os\_creds\_name: the connection name (default = 'default'
             required or use "os\_user" below instead)
          -  os\_user: the connection from a new user defined in template
             (required or use "os\_creds\_name" above

              - name: the user's name (required)
              - project\_name: the project name to use

          -  name: The name of the network to be created. If one already
             exists, a new one will not be created (required)
          -  admin\_state\_up: T\|F (default True)
          -  shared: (optional)
          -  project\_name: Name of the project who owns the network. Note:
             only administrative users can specify projects other than their
             own (optional)
          -  external: T\|F whether or not network is external (default False)
          -  network\_type: The type of network to create (optional)
          -  physical\_network: the name of the physical network
             (required when network_type is 'flat')
          -  segmentation\_id: the id of the segmentation
             (required when network_type is 'vlan')
          -  subnets:
              -  subnet:

                 -  name: The name of the network to be created. If one already
                    exists, a new one will not be created. Note: although
                    OpenStack allows for multiple subnets to be applied to any
                    given network, we have not included support as our current
                    use cases does not utilize this functionality (required)
                 -  cidr: The subnet mask value (required)
                 -  dns\_nameservers: A list of IP values used for DNS
                    resolution (default: 8.8.8.8)
                 -  ip\_version: 4\|6 (default: 4)
                 -  project\_name: Name of the project who owns the network.
                    Note: only administrative users can specify projects other
                    than their own (optional)
                 -  start: The start address for allocation\_pools (optional)
                 -  end: The ending address for allocation\_pools (optional)
                 -  gateway\_ip: The IP address to the gateway (optional)
                 -  enable\_dhcp: T\|F (optional)
                 -  dns\_nameservers: List of DNS server IPs (default = ['8.8.8.8']
                 -  host\_routes: A list of host route dictionaries (optional)
                    i.e.:
                    ``yaml    "host_routes":[    {    "destination":"0.0.0.0/0",    "nexthop":"123.456.78.9"    },    {    "destination":"192.168.0.0/24",    "nexthop":"192.168.0.1"    }    ]``
                 -  destination: The destination for a static route (optional)
                 -  nexthop: The next hop for the destination (optional)
                 -  ipv6\_ra\_mode: Valid values: "dhcpv6-stateful",
                    "dhcpv6-stateless", and "slaac" (optional)
                 -  ipv6\_address\_mode: Valid values: "dhcpv6-stateful",
                    "dhcpv6-stateless", and "slaac" (optional)

   -  security_groups:

      -  security_group:

          -  os\_creds\_name: the connection name (default = 'default'
             required or use "os\_user" below instead)
          -  os\_user: the connection from a new user defined in template
             (required or use "os\_creds\_name" above

              - name: the user's name (required)
              - project\_name: the project name to use

          -  name: The name of the security group to be created (required)
          -  description: The security group's description (optional)
          -  project\_name: Name of the project who owns the security group (optional)
          -  rule\_settings: List of rules to place onto security group (optional)

              -  description: the rule's description (optional)
              -  protocol: rule's protcol ('icmp' or 'tcp' or 'udp' or 'null')
              -  ethertype: rule's ethertype ('4' or '6')
              -  port\_range\_min: The minimum port number in the range that is
                 matched by the security group rule. When the protocol is 'tcp'
                 or 'udp', this value must be <= 'port_range_max' (optional)
              -  port\_range\_max: The maximum port number in the range that is
                 matched by the security group rule. When the protocol is 'tcp'
                 or 'udp', this value must be <= 'port_range_max' (optional)
              -  remote\_ip\_prefix: The remote IP prefix to associate with this
                 metering rule packet (optional)

   -  routers:

      -  router:

          -  os\_creds\_name: the connection name (default = 'default'
             required or use "os\_user" below instead)
          -  os\_user: the connection from a new user defined in template
             (required or use "os\_creds\_name" above

              - name: the user's name (required)
              - project\_name: the project name to use

          -  name: The name of the router to be created (required)
          -  project\_name: Name of the project who owns the network (optional)
          -  external\_gateway: Name of the external network to which to route
             (optional)
          -  admin\_state\_up: T\|F (default True)
          -  external\_fixed\_ids: Dictionary containing the IP address
             parameters (optional)
          -  internal\_subnets: List of subnet names to which to connect this
             router (optional)

             -  port_settings (Leverages the same class/structure as port objects on
                VM instances. See port definition below for a
                full accounting of the port attributes. The ones listed
                below are generally used for routers)

                -  name: The name given to the new port (required and must be
                   unique for project)
                -  network\_name: The name of the network on which to create
                   the port (optional)
                -  admin\_state\_up: T\|F (default True)
                -  project\_name: Name of the project who owns the network (optional)
                -  mac\_address: The port's MAC address (optional)
                -  ip\_addrs: A list of k/v pairs (optional)
                -  security\_groups: a list of names of the the security groups
                   to apply to the port
                -  opt\_value: The extra DHCP option value (optional)
                -  opt\_name: The extra DHCP option name (optional)

   -  keypairs:

      -  keypair:

          -  os\_creds\_name: the connection name (default = 'default'
             required or use "os\_user" below instead)
          -  os\_user: the connection from a new user defined in template
             (required or use "os\_creds\_name" above

              - name: the user's name (required)
              - project\_name: the project name to use

          -  name: The name of the keypair to be created. If one already
             exists, a new one will not be created but simply loaded from
             its configured file location (required)
          -  public\_filepath: The path to where the generated public key
             will be stored if it does not exist (optional but really
             required for provisioning purposes)
          -  private\_filepath: The path to where the generated private key
             will be stored if it does not exist (optional but really
             required for provisioning purposes)

   -  instances:

      -  instance:

          -  os\_creds\_name: the connection name (default = 'default'
             required or use "os\_user" below instead)
          -  os\_user: the connection from a new user defined in template
             (required or use "os\_creds\_name" above

              - name: the user's name (required)
              - project\_name: the project name to use

          -  name: The unique instance name for project. (required)
          -  flavor: Must be one of the preconfigured flavors (required)
          -  imageName: The name of the image to be used for deployment
             (required)
          -  keypair\_name: The name of the keypair to attach to instance
             (optional but required for NIC configuration and Ansible
             provisioning)
          -  sudo\_user: The name of a sudo\_user that is attached to the
             keypair (optional but required for NIC configuration and
             Ansible provisioning)
          -  vm\_boot\_timeout: The number of seconds to block waiting for
             an instance to deploy and boot (default 900)
          -  vm\_delete\_timeout: The number of seconds to block waiting for
             an instance to be deleted (default 300)
          -  ssh\_connect\_timeout: The number of seconds to block waiting
             for an instance to achieve an SSH connection (default 120)
          -  ports: A list of port configurations (should contain at least
             one)
          -  port: Denotes the configuration of a NIC

             -  name: The unique port name for project (required)
             -  network\_name: The name of the network to which the port is
                attached (required)
             -  ip\_addrs: Static IP addresses to be added to the port by
                subnet (optional)
             -  subnet\_name: The name of the subnet
             -  ip: The assigned IP address (when null, OpenStack will
                assign an IP to the port)
             -  admin\_state\_up: T\|F (default True)
             -  project\_name: The name of the project who owns the network.
                Only administrative users can specify a the project ID other
                than their own (optional)
             -  mac\_address: The desired MAC for the port (optional)
             -  fixed\_ips: A dictionary that allows one to specify only a
                subnet ID, OpenStack Networking allocates an available IP
                from that subnet to the port. If you specify both a subnet
                ID and an IP address, OpenStack Networking tries to allocate
                the specified address to the port. (optional)
             -  seurity\_groups: A list of security group IDs (optional)
             -  allowed\_address\_pairs: A dictionary containing a set of
                zero or more allowed address pairs. An address pair contains
                an IP address and MAC address. (optional)
             -  opt\_value: The extra DHCP option value (optional)
             -  opt\_name: The extra DHCP option name (optional)
             -  device\_owner: The ID of the entity that uses this port. For
                example, a DHCP agent (optional)
             -  device\_id: The ID of the device that uses this port. For
                example, a virtual server (optional)

       -  floating\_ips: list of floating\_ip configurations (optional)

          -  floating\_ip:
          -  name: Must be unique for VM instance (required)
          -  port\_name: The name of the port requiring access to the
             external network (required)
          -  subnet\_name: The name of the subnet contains the IP address on
             the port on which to create the floating IP (optional)
          -  router\_name: The name of the router connected to an external
             network used to attach the floating IP (required)
          -  provisioning: (True\|False) Denotes whether or not this IP can
             be used for Ansible provisioning (default True)

-  ansible: Each set of attributes below are contained in a list

   -  playbook\_location: Full path or relative to the directory in
      which the deployment file resides (required)
   -  hosts: A list of hosts to which the playbook will be executed
      (required)
   -  variables: Should your Ansible scripts require any substitution
      values to be applied with Jinga2templates, the values defined here
      will be used to for substitution
   -  tag name = substitution variable names. For instance, for any file
      being pushed to the host being provisioned containing a value such
      as {{ foo }}, you must specify a tag name of "foo"

      -  vm\_name:
      -  type: string\|port\|os\_creds\|vm-attr (note: will need to make
         changes to deploy\_venv.py#\_\_get\_variable\_value() for
         additional support)
      -  when type == string, an tag name "value" must exist and its
         value will be used for template substituion
      -  when type == port, custom code has been written to extract
         certain assigned values to the port:

         -  vm\_name: must correspond to a VM's name as configured in
            this file
         -  port\_name: The name of the port from which to extract the
            substitution values (required)
         -  port\_value: The port value. Currently only supporting
            "mac\_address" and "ip\_address" (only the first)

      -  when type == os\_creds, custom code has been written to extract
         the file's connection values:

         -  username: connection's user
         -  password: connection's password
         -  auth\_url: connection's URL
         -  project\_name: connection's project

      -  when type == vm-attr, custom code has been written to extract
         the following attributes from the vm:

         -  vm\_name: must correspond to a VM's name as configured in
            this file
         -  value -> floating\_ip: is currently the only vm-attr
            supported
