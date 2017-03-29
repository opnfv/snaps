Try an example
==============

Use launcher.py to deploy and clean up example environments.  These examples are described in YAML files.

#. Add your OpenStack connection information to the deploy-complex-network.yaml.

    Edit <path to repo>/examples/complex-network/deploy-complex-network.yaml

   -  openstack: the top level tag that denotes configuration for the OpenStack components

   -  connection: - contains the credentials and endpoints required to
      connect with OpenStack
   -  username: - the project's user (required)
   -  password: - the tentant's user password (required)
   -  auth\_url: - the URL to the OpenStack APIs (required)
   -  project\_name: - the name of the OpenStack project for the user
      (required)
   -  http\_proxy: - the {{ host }}:{{ port }} of the proxy server the
      HTTPPhotoman01(optional)

#. Go to the examples directory.

    ::

      cd <snaps repo>/examples/

#. Deploy the launcher.

    ::

      python launch.py -e ./complex-network/deploy-complex-network.yaml -d

#. Clean the deployment.

    ::

      python launch.py -e ./complex-network/deploy-complex-network.yaml -c

#. Customize the deployment by changing the yaml file.

    The configuration file used to deploy and provision a virtual environment has been designed to describe the required
    images, networks, SSH public and private keys, associated VMs, as well as any required post deployment provisioning
    tasks.

-  openstack: the top level tag that denotes configuration for the
   OpenStack components

   -  connection: - contains the credentials and endpoints required to
      connect with OpenStack
   -  username: - the project's user (required)
   -  password: - the tentant's user password (required)
   -  auth\_url: - the URL to the OpenStack APIs (required)
   -  project\_name: - the name of the OpenStack project for the user
      (required)
   -  http\_proxy: - the {{ host }}:{{ port }} of the proxy server the
      HTTPPhotoman01(optional)
   -  images: - describes each image
   -  image:

      -  name: The unique image name. If the name already exists for
         your project, a new one will not be created (required)
      -  format: The format type of the image i.e. qcow2 (required)
      -  download\_url: The HTTP download location of the image file
         (required)
      -  nic\_config\_pb\_loc: The file location relative to the CWD
         (python directory) to the Ansible Playbook used to configure
         VMs with more than one port. VMs get their first NIC configured
         for free while subsequent ones are not. This value/script will
         only be leveraged when necessary. Centos has been supported
         with
         "provisioning/ansible/centos-network-setup/configure\_host.yml".

   -  networks:
   -  network:

      -  name: The name of the network to be created. If one already
         exists, a new one will not be created (required)
      -  admin\_state\_up: T\|F (default True)
      -  shared: (optional)
      -  project\_name: Name of the project who owns the network. Note:
         only administrative users can specify projects other than their
         own (optional)
      -  external: T\|F whether or not network is external (default
         False)
      -  network\_type: The type of network to create. (optional)
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
         -  dns\_nameservers: List of DNS server IPs
         -  host\_routes: A list of host route dictionaries (optional)
            i.e.:
            ``yaml    "host_routes":[    {    "destination":"0.0.0.0/0",    "nexthop":"123.456.78.9"    },    {    "destination":"192.168.0.0/24",    "nexthop":"192.168.0.1"    }    ]``
         -  destination: The destination for a static route (optional)
         -  nexthop: The next hop for the destination (optional)
         -  ipv6\_ra\_mode: Valid values: "dhcpv6-stateful",
            "dhcpv6-stateless", and "slaac" (optional)
         -  ipv6\_address\_mode: Valid values: "dhcpv6-stateful",
            "dhcpv6-stateless", and "slaac" (optional)

   -  routers:

      -  router:
      -  name: The name of the router to be created. If one already
         exists, a new one will not be created (required)
      -  project\_name: Name of the project who owns the network. Note:
         only administrative users can specify projects other than their
         own (optional)
      -  internal\_subnets: A list of subnet names on which the router
         will be placed (optional)
      -  external\_gateway: A dictionary containing the external gateway
         parameters: "network\_id", "enable\_snat",
         "external\_fixed\_ips" (optional)
      -  interfaces: A list of port interfaces to create to other
         subnets (optional)

         -  port (Leverages the same class/structure as port objects on
            VM instances. See port definition below for a
            full accounting of the port attributes. The ones listed
            below are generally used for routers)

            -  name: The name given to the new port (must be unique for
               project) (required)
            -  network\_name: The name of the new port's network
               (required)
            -  ip\_addrs: A list of k/v pairs (optional)
            -  subnet\_name: the name of a subnet that is on the port's
               network
            -  ip: An IP address of the associated subnet to assign to
               the new port (optional but generally required for router
               interfaces)

   -  keypairs:

      -  keypair:
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
