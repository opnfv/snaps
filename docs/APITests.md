# SNAPS OpenStack API Testing

Tests designated as component tests extend the snaps.openstack.tests.OSComponentTestCase class and must be exercised
with OpenStack credentials for all as well as an external network for many. When leveraging the unit_test_suite.py
application, the -e argument and -n arguments will suffice. When attempting to execute these tests within your IDE
of choice (tested on IntelliJ), you will need to edit the [repo_dir]/snaps/openstack/tests/conf/os_env.yaml file as well
as ensuring that your run configuration's working directory is set to [repo_dir]/snaps.

# The Test Classes

## glance_utils_tests.py - GlanceSmokeTests
Ensures that a Glance client can be obtained as well as the proper exceptions thrown with the wrong credentials.

## keystone_utils_tests.py - KeystoneSmokeTests
Ensures that a Keystone client can be obtained as well as the proper exceptions thrown with the wrong credentials.

## neutron_utils_tests.py - NeutronSmokeTests
Ensures that a Neutron client can be obtained as well as the proper exceptions thrown with the wrong credentials.

## nova_utils_tests.py - NovaSmokeTests
Ensures that a Nova client can be obtained as well as the proper exceptions thrown with the wrong credentials.

## keystone_utils_tests.py - KeystoneUtilsTests
| Test Name 	| Keystone API Version 	| Description 	|
|---	|:-:	|---	|
|test_create_user_minimal|2 & 3|Tests the creation of a user with minimal configuration settings via the utility functions|
|test_create_project_minimal|2 & 3|Tests the creation of a project with minimal configuration settings via the utility functions|

## create_user_tests.py - CreateUserSuccessTests
| Test Name 	| Keystone API Version 	| Description 	|
|---	|:-:	|---	|
|test_create_user|2 & 3|Tests the creation of a user via the OpenStackUser class|
|test_create_user_2x|2 & 3|Tests the creation of a user a second time via the OpenStackUser class to ensure it is only created once|
|test_create_delete_user|2 & 3|Tests the creation and deletion of a user via the OpenStackUser class to ensure that clean() will not raise an exception|

## create_project_tests.py - CreateProjectSuccessTests
| Test Name 	| Keystone API Version 	| Description 	|
|---	|:-:	|---	|
|test_create_project|2 & 3|Tests the creation of a project via the OpenStackProject class|
|test_create_project_2x|2 & 3|Tests the creation of a project a second time via the OpenStackProject class to ensure it is only created once|
|test_create_delete_project|2 & 3|Tests the creation and deletion of a project via the OpenStackProject class to ensure that clean() will not raise an exception|

## create_project_tests.py - CreateProjectUserTests
| Test Name 	| Keystone API Version 	| Description 	|
|---	|:-:	|---	|
|test_create_project_sec_grp_one_user|2 & 3|Tests the creation of an OpenStack object to a project with a new users and to create a security group|
|test_create_project_sec_grp_two_users|2 & 3|Tests the creation of an OpenStack object to a project with two new users and to create a security group under each|

## glance_utils_tests.py - GlanceUtilsTests
| Test Name 	| Glance API Version 	| Description 	|
|---	|:-:	|---	|
|test_create_image_minimal_url|1|Tests the glance_utils.create_image() function with a URL|
|test_create_image_minimal_file|1|Tests the glance_utils.create_image() function with a file|

## neutron_utils_tests.py - NeutronUtilsNetworkTests
| Test Name 	| Neutron API Version 	| Description 	|
|---	|:-:	|---	|
|test_create_network|2|Ensures neutron_utils.create_network() properly creates a network|
|test_create_network_empty_name|2|Ensures neutron_utils.create_network() raises an exception when the network name is an empty string|
|test_create_network_null_name|2|Ensures neutron_utils.create_network() raises an exception when the network name is None|

## neutron_utils_tests.py - NeutronUtilsSubnetTests
| Test Name 	| Neutron API Version 	| Description 	|
|---	|:-:	|---	|
|test_create_subnet|2|Ensures neutron_utils.create_subnet() can properly create an OpenStack subnet object|
|test_create_subnet_null_name|2|Ensures neutron_utils.create_subnet() raises an exception when the subnet name is None|
|test_create_subnet_empty_name|2|Ensures neutron_utils.create_subnet() raises an exception when the subnet name is an empty string|
|test_create_subnet_null_cidr|2|Ensures neutron_utils.create_subnet() raises an exception when the subnet CIDR is None|
|test_create_subnet_empty_cidr|2|Ensures neutron_utils.create_subnet() raises an exception when the subnet CIDR is an empty string|

## neutron_utils_tests.py - NeutronUtilsRouterTests
| Test Name 	| Neutron API Version 	| Description 	|
|---	|:-:	|---	|
|test_create_router_simple|2|Ensures neutron_utils.create_router() can properly create a simple OpenStack router object|
|test_create_router_with_public_interface|2|Ensures neutron_utils.create_router() can properly create an OpenStack router object with an interface to the external network|
|test_create_router_empty_name|2|Ensures neutron_utils.create_router() raises an exception when the name is an empty string|
|test_create_router_null_name|2|Ensures neutron_utils.create_router() raises an exception when the name is None|
|test_add_interface_router|2|Ensures neutron_utils.add_interface_router() properly adds an interface to another subnet|
|test_add_interface_router_null_router|2|Ensures neutron_utils.add_interface_router() raises an exception when the router object is None|
|test_add_interface_router_null_subnet|2|Ensures neutron_utils.add_interface_router() raises an exception when the subnet object is None|
|test_create_port|2|Ensures neutron_utils.create_port() can properly create an OpenStack port object|
|test_create_port_empty_name|2|Ensures neutron_utils.create_port() raises an exception when the port name is an empty string|
|test_create_port_null_name|2|Ensures neutron_utils.create_port() raises an exception when the port name is None|
|test_create_port_null_network_object|2|Ensures neutron_utils.create_port() raises an exception when the network object is None|
|test_create_port_null_ip|2|Ensures neutron_utils.create_port() raises an exception when the assigned IP value is None|
|test_create_port_invalid_ip|2|Ensures neutron_utils.create_port() raises an exception when the assigned IP value is invalid|
|test_create_port_invalid_ip_to_subnet|2|Ensures neutron_utils.create_port() raises an exception when the assigned IP value is not part of CIDR|

## neutron_utils_tests.py - NeutronUtilsSecurityGroupTests
| Test Name 	| Neutron API Version 	| Description 	|
|---	|:-:	|---	|
|test_create_delete_simple_sec_grp|2|Ensures that a security group can be created (neutron_utils.create_security_group() and deleted via neutron_utils.delete_security_group()|
|test_create_sec_grp_no_name|2|Ensures that neutron_utils.create_security_group() raises an exception when attempting to create a security group without a name|
|test_create_sec_grp_no_rules|2|Ensures that neutron_utils.create_security_group() can create a security group without any rules|
|test_create_sec_grp_one_rule|2|Ensures that neutron_utils.create_security_group_rule() can add a rule to a security group|

## nova_utils_tests.py - NovaUtilsKeypairTests
| Test Name 	| Nova API Version 	| Description 	|
|---	|:-:	|---	|
|test_create_keypair|2|Ensures that a keypair can be properly created via nova_utils.upload_keypair() with a public_key object|
|test_create_delete_keypair|2|Ensures that a keypair can be properly deleted via nova_utils.delete_keypair()|
|test_create_key_from_file|2|Ensures that a keypair can be properly created via nova_utils.upload_keypair_file()|
|test_floating_ips|2|Ensures that a floating IP can be properly created via nova_utils.create_floating_ip() [note: this test should be moved to a new class]|

## nova_utils_tests.py - NovaUtilsFlavorTests
| Test Name 	| Nova API Version 	| Description 	|
|---	|:-:	|---	|
|test_create_flavor|2|Ensures that a flavor can be properly created via nova_utils.create_flavor()|
|test_create_delete_flavor|2|Ensures that a flavor can be properly deleted via nova_utils.delete_flavor()|

## create_flavor_tests.py - CreateFlavorTests
| Test Name 	| Nova API Version 	| Description 	|
|---	|:-:	|---	|
|test_create_flavor|2|Ensures that the OpenStackFlavor class's create() method creates an OpenStack flavor object|
|test_create_flavor_existing|2|Ensures that the OpenStackFlavor class's create() will not create a flavor with the same name more than once|
|test_create_clean_flavor|2|Ensures that the OpenStackFlavor class's clean() method will delete the flavor object|
|test_create_delete_flavor|2|Ensures that the OpenStackFlavor class's clean() method will not raise an exception when called and the object no longer exists|
