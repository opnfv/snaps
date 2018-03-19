SNAPS OpenStack API Testing
===========================

Tests designated as component tests extend the snaps.openstack.tests.OSComponentTestCase class and must be exercised
with OpenStack credentials for all as well as an external network for many. When leveraging the unit\_test\_suite.py
application, the -e argument and -n arguments will suffice. When attempting to execute these tests within your IDE
of choice (tested on IntelliJ), you will need to edit the [repo\_dir]/snaps/openstack/tests/conf/os\_env.yaml file as well
as ensuring that your run configuration's working directory is set to [repo\_dir]/snaps.

The Test Classes
================

glance_utils_tests.py - GlanceSmokeTests
----------------------------------------

Ensures that a Glance client can be obtained as well as the proper
exceptions thrown with the wrong credentials.

keystone_utils_tests.py - KeystoneSmokeTests
--------------------------------------------

Ensures that a Keystone client can be obtained as well as the proper
exceptions thrown with the wrong credentials.

neutron_utils_tests.py - NeutronSmokeTests
------------------------------------------

Ensures that a Neutron client can be obtained as well as the proper
exceptions thrown with the wrong credentials.

nova_utils_tests.py - NovaSmokeTests
------------------------------------

Ensures that a Nova client can be obtained as well as the proper
exceptions thrown with the wrong credentials.

cinder_utils_tests.py - CinderSmokeTests
----------------------------------------

Ensures that a Cinder client can be obtained as well as the proper
exceptions thrown with the wrong credentials.

heat_utils_tests.py - HeatSmokeTests
------------------------------------

Ensures that a Heat client can be obtained as well as the proper
exceptions thrown with the wrong credentials.

keystone_utils_tests.py - KeystoneUtilsTests
--------------------------------------------

+----------------------------------+---------------+-----------------------------------------------------------+
| Test Name                        | Keystone API  | Description                                               |
+==================================+===============+===========================================================+
| test_create_user_minimal         | 2 & 3         | Tests the creation of a user with minimal configuration   |
|                                  |               | settings via the utility functions                        |
+----------------------------------+---------------+-----------------------------------------------------------+
| test_create_project_minimal      | 2 & 3         | Tests the creation of a project with minimal configuration|
|                                  |               | settings via the utility functions                        |
+----------------------------------+---------------+-----------------------------------------------------------+
| test_get_endpoint_success        | 2 & 3         | Tests to ensure that proper credentials and proper service|
|                                  |               | type can succeed                                          |
+----------------------------------+---------------+-----------------------------------------------------------+
| test_get_endpoint_fail_without   | 2 & 3         | Tests to ensure that proper credentials and improper      |
| _proper_service                  |               | service type cannot succeed                               |
+----------------------------------+---------------+-----------------------------------------------------------+
| test_get_endpoint_fail_without   | 2 & 3         | Tests to ensure that improper credentials and proper      |
| _proper_credentials              |               | service type cannot succeed                               |
+----------------------------------+---------------+-----------------------------------------------------------+
| test_get_endpoint_with_each      | 2 & 3         | Tests to ensure that an interface URL is returned for each|
| _interface                       |               | supported interface type (i.e. public, internal, & admin) |
+----------------------------------+---------------+-----------------------------------------------------------+
| test_grant_user_role_to_project  | 2 & 3         | Tests to ensure that one can grant a new user's role to a |
|                                  |               | new project                                               |
+----------------------------------+---------------+-----------------------------------------------------------+

create_user_tests.py - CreateUserSuccessTests
---------------------------------------------
+----------------------------------+---------------+-----------------------------------------------------------+
| Test Name                        | Keystone API  | Description                                               |
+==================================+===============+===========================================================+
| test_create_user                 | 2 & 3         | Tests the creation of a user with minimal configuration   |
|                                  |               | settings via the utility functions                        |
+----------------------------------+---------------+-----------------------------------------------------------+
| test_create_user_2x              | 2 & 3         | Tests the creation of a user 2x and ensure it has been    |
|                                  |               | done only once                                            |
+----------------------------------+---------------+-----------------------------------------------------------+
| test_create_delete_user          | 2 & 3         | Tests the creation of a user and ensure clean can be      |
|                                  |               | called 2x without exceptions being raised                 |
+----------------------------------+---------------+-----------------------------------------------------------+
| test_create_admin_user           | 2 & 3         | Tests the creation of a user with an 'admin' role         |
+----------------------------------+---------------+-----------------------------------------------------------+

create_project_tests.py - CreateProjectSuccessTests
---------------------------------------------------

+----------------------------------+---------------+-----------------------------------------------------------+
| Test Name                        | Keystone API  | Description                                               |
+==================================+===============+===========================================================+
| test_create_project_bad_domain   | 3             | Ensures that keystone v3 clients using the domain ID      |
|                                  |               | project setting project creation will fail with an invalid|
|                                  |               | domain id/name                                            |
+----------------------------------+---------------+-----------------------------------------------------------+
| test_create_project              | 2 & 3         | Tests the creation of a project via the OpenStackProject  |
|                                  |               | class                                                     |
+----------------------------------+---------------+-----------------------------------------------------------+
| test_create_project_quota        | 2 & 3         | Tests the creation of a project via the OpenStackProject  |
| _override                        |               | class with overriding the default quota values            |
+----------------------------------+---------------+-----------------------------------------------------------+
| test_create_project_2x           | 2 & 3         | Tests the creation of a project a second time via the     |
|                                  |               | OpenStackProject class to ensure it is only created once  |
+----------------------------------+---------------+-----------------------------------------------------------+
| test_create_delete_project       | 2 & 3         | Tests the creation and deletion of a project via the      |
|                                  |               | OpenStackProject class to ensure that clean will not raise|
|                                  |               | an exception                                              |
+----------------------------------+---------------+-----------------------------------------------------------+
| test_update_quotas               | 2 & 3         | Tests the ability to update quota values                  |
|                                  | nova & neutron|                                                           |
+----------------------------------+---------------+-----------------------------------------------------------+

create_project_tests.py - CreateProjectUserTests
------------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | Keystone API  | Description                                               |
+=======================================+===============+===========================================================+
| test_create_project_sec_grp_one_user  | 2 & 3         | Tests the creation of an OpenStack object to a project    |
|                                       |               | with a new users and to create a security group           |
|                                       |               |                                                           |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_project_sec_grp_two_users | 2 & 3         | Tests the creation of an OpenStack object to a project    |
|                                       |               | with two new users and to create a security group under   |
|                                       |               | each                                                      |
+---------------------------------------+---------------+-----------------------------------------------------------+

glance_utils_tests.py - GlanceUtilsTests
----------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | Glance API    | Description                                               |
+=======================================+===============+===========================================================+
| test_create_image_minimal_url         | 1             | Tests the glance_utils.create_image() function with a URL |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_image_minimal_file        | 1             | Tests the glance_utils.create_image() function with a file|
+---------------------------------------+---------------+-----------------------------------------------------------+

neutron_utils_tests.py - NeutronUtilsNetworkTests
-------------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | Neutron API   | Description                                               |
+=======================================+===============+===========================================================+
| test_create_network                   | 2             | Ensures neutron_utils.create_network() properly creates a |
|                                       |               | network                                                   |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_network_empty_name        | 2             | Ensures neutron_utils.create_network() raises an exception|
|                                       |               | when the network name is an empty string                  |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_network_null_name         | 2             | Ensures neutron_utils.create_network() raises an exception|
|                                       |               | when the network name is None                             |
+---------------------------------------+---------------+-----------------------------------------------------------+

neutron_utils_tests.py - NeutronUtilsSubnetTests
------------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | Neutron API   | Description                                               |
+=======================================+===============+===========================================================+
| test_create_subnet                    | 2             | Ensures neutron_utils.create_network() can properly create|
|                                       |               | an OpenStack subnet object                                |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_subnet_null_name          | 2             | Ensures neutron_utils.create_network() raises an exception|
|                                       |               | when the subnet name is None                              |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_subnet_empty_name         | 2             | Ensures neutron_utils.create_network() raises an exception|
|                                       |               | when the subnet name is an empty string                   |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_subnet_null_cidr          | 2             | Ensures neutron_utils.create_network() raises an exception|
|                                       |               | when the subnet CIDR is None                              |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_subnet_empty_cidr         | 2             | Ensures neutron_utils.create_network() raises an exception|
|                                       |               | when the subnet CIDR is an empty string                   |
+---------------------------------------+---------------+-----------------------------------------------------------+

neutron_utils_tests.py - NeutronUtilsIPv6Tests
----------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | Neutron API   | Description                                               |
+=======================================+===============+===========================================================+
| test_create_network_slaac             | 2             | Ensures neutron_utils.create_network() can properly create|
|                                       |               | an OpenStack network with an IPv6 subnet when DHCP is True|
|                                       |               | and modes are 'slaac'                                     |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_network_stateful          | 2             | Ensures neutron_utils.create_network() can properly create|
|                                       |               | an OpenStack network with an IPv6 subnet when DHCP is True|
|                                       |               | and modes are 'stateful'                                  |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_network_stateless         | 2             | Ensures neutron_utils.create_network() can properly create|
|                                       |               | an OpenStack network with an IPv6 subnet when DHCP is True|
|                                       |               | and modes are 'stateless'                                 |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_network_no_dhcp_slaac     | 2             | Ensures neutron_utils.create_network() raises a BadRequest|
|                                       |               | exception when deploying the network with an IPv6 subnet  |
|                                       |               | when DHCP is False and modes are 'slaac'                  |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_network_invalid_start_ip  | 2             | Ensures neutron_utils.create_network() sets the start IP  |
|                                       |               | address to the minimum value when the start configuration |
|                                       |               | parameter is some garbage value                           |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_network_invalid_end_ip    | 2             | Ensures neutron_utils.create_network() sets the end IP    |
|                                       |               | address to the maximum value when the end configuration   |
|                                       |               | parameter is some garbage value                           |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_network_with_bad_cidr     | 2             | Ensures neutron_utils.create_network() raises a BadRequest|
|                                       |               | exception when the IPv6 CIDR is incorrect                 |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_network_invalid_gateway_ip| 2             | Ensures neutron_utils.create_network() raises a BadRequest|
|                                       |               | exception when the IPv6 gateway IP does not match the CIDR|
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_network_with_bad_dns      | 2             | Ensures neutron_utils.create_network() raises a BadRequest|
|                                       |               | exception when the IPv6 DNS IP address is not a valid IPv6|
|                                       |               | address                                                   |
+---------------------------------------+---------------+-----------------------------------------------------------+

neutron_utils_tests.py - NeutronUtilsRouterTests
------------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | Neutron API   | Description                                               |
+=======================================+===============+===========================================================+
| test_create_router_simple             | 2             | Ensures neutron_utils.create_router() can properly create |
|                                       |               | a simple OpenStack router object                          |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_router_with_public_inter  | 2             | Ensures neutron_utils.create_router() can properly create |
| face                                  |               | an OpenStack router object with an interface to the       |
|                                       |               | external network                                          |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_add_interface_router             | 2             | Ensures neutron_utils.add_interface_router() properly adds|
|                                       |               | an interface to another subnet                            |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_add_interface_router_null_router | 2             | Ensures neutron_utils.add_interface_router() raises an    |
|                                       |               | exception when the router object is None                  |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_add_interface_router_null_subnet | 2             | Ensures neutron_utils.add_interface_router() raises an    |
|                                       |               | exception when the subnet object is None                  |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_add_interface_router_missing_sub | 2             | Ensures neutron_utils.add_interface_router() raises an    |
| net                                   |               | exception when the subnet object had been deleted         |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_port                      | 2             | Ensures neutron_utils.create_port() can properly create an|
|                                       |               | OpenStack port object                                     |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_port_empty_name           | 2             | Ensures neutron_utils.create_port() raises an exception   |
|                                       |               | when the port name is an empty string                     |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_port_null_name            | 2             | Ensures neutron_utils.create_port() raises an exception   |
|                                       |               | when the port name is None                                |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_port_null_network_object  | 2             | Ensures neutron_utils.create_port() raises an exception   |
|                                       |               | when the network object is None                           |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_port_null_ip              | 2             | Ensures neutron_utils.create_port() raises an exception   |
|                                       |               | when the assigned IP value is None                        |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_port_invalid_ip           | 2             | Ensures neutron_utils.create_port() raises an exception   |
|                                       |               | when the assigned IP value is invalid                     |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_port_invalid_ip_to_subnet | 2             | Ensures neutron_utils.create_port() raises an exception   |
|                                       |               | when the assigned IP value is not part of CIDR            |
+---------------------------------------+---------------+-----------------------------------------------------------+

neutron_utils_tests.py - NeutronUtilsSecurityGroupTests
-------------------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | Neutron API   | Description                                               |
+=======================================+===============+===========================================================+
| test_create_delete_simple_sec_grp     | 2             | Ensures that a security group can be created              |
|                                       |               | (neutron_utils.create_security_group() and deleted via    |
|                                       |               | neutron_utils.delete_security_group()                     |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_sec_grp_no_name           | 2             | Ensures that neutron_utils.create_security_group() raises |
|                                       |               | an exception when attempting to create a security group   |
|                                       |               | without a name                                            |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_sec_grp_no_rules          | 2             | Ensures that neutron_utils.create_security_group() can    |
|                                       |               | create a security group without any rules                 |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_sec_grp_one_rule          | 2             | Ensures that neutron_utils.create_security_group_rule()   |
|                                       |               | can add a rule to a security group                        |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_get_sec_grp_by_id                | 2             | Ensures that neutron_utils.get_security_group_by_id()     |
|                                       |               | returns the expected security group                       |
+---------------------------------------+---------------+-----------------------------------------------------------+

neutron_utils_tests.py - NeutronUtilsFloatingIpTests
----------------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | Neutron API   | Description                                               |
+=======================================+===============+===========================================================+
| test_floating_ips                     | 2             | Ensures that a floating IP can be created                 |
+---------------------------------------+---------------+-----------------------------------------------------------+

cinder_utils_tests.py - CinderUtilsQoSTests
-------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             |  Cinder API   | Description                                               |
+=======================================+===============+===========================================================+
| test_create_qos_both                  | 2 & 3         | Ensures that a QoS Spec can be created with a Consumer    |
|                                       |               | value of 'both'                                           |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_qos_front                 | 2 & 3         | Ensures that a QoS Spec can be created with a Consumer    |
|                                       |               | value of 'front-end'                                      |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_qos_back                  | 2 & 3         | Ensures that a QoS Spec can be created with a Consumer    |
|                                       |               | value of 'back-end'                                       |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_delete_qos                | 2 & 3         | Ensures that a QoS Spec can be created and deleted        |
+---------------------------------------+---------------+-----------------------------------------------------------+

cinder_utils_tests.py - CinderUtilsSimpleVolumeTypeTests
--------------------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             |  Cinder API   | Description                                               |
+=======================================+===============+===========================================================+
| test_create_simple_volume_type        | 2 & 3         | Tests the creation of a simple volume type with the       |
|                                       |               | function cinder_utils#create_volume_type()                |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_delete_volume_type        | 2 & 3         | Tests the creation of a simple volume type with the       |
|                                       |               | function cinder_utils#create_volume_type() then deletes   |
|                                       |               | with the function cinder_utils#delete_volume_type()       |
+---------------------------------------+---------------+-----------------------------------------------------------+

cinder_utils_tests.py - CinderUtilsAddEncryptionTests
-----------------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             |  Cinder API   | Description                                               |
+=======================================+===============+===========================================================+
| test_create_simple_encryption         | 2 & 3         | Tests the creation of a simple volume type encryption     |
|                                       |               | with the function cinder_utils#create_volume_encryption() |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_delete_encryption         | 2 & 3         | Tests the creation of a simple volume type encryption     |
|                                       |               | with the function cinder_utils#create_volume_encryption() |
|                                       |               | then deletes with the function                            |
|                                       |               | cinder_utils#delete_volume_type_encryption()              |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_with_all_attrs            | 2 & 3         | Tests the creation of a simple volume type encryption     |
|                                       |               | with the function cinder_utils#create_volume_encryption() |
|                                       |               | where all configuration attributes have been set          |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_bad_key_size              | 2 & 3         | Tests to ensure that the function                         |
|                                       |               | cinder_utils#create_volume_encryption() raises a          |
|                                       |               | BadRequest exception when the key_size attribute is -1    |
+---------------------------------------+---------------+-----------------------------------------------------------+

cinder_utils_tests.py - CinderUtilsVolumeTypeCompleteTests
----------------------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             |  Cinder API   | Description                                               |
+=======================================+===============+===========================================================+
| test_create_with_encryption           | 2 & 3         | Tests the creation of a volume type with encryption       |
|                                       |               | with the function cinder_utils#create_volume_type()       |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_with_qos                  | 2 & 3         | Tests the creation of a volume type with a QoS Spec       |
|                                       |               | with the function cinder_utils#create_volume_type()       |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_with_invalid_qos          | 2 & 3         | Tests the creation of a volume type with an invalid QoS   |
|                                       |               | Spec with the function cinder_utils#create_volume_type()  |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_with_qos_and_encryption   | 2 & 3         | Tests the creation of a volume type with a QoS Spec and   |
|                                       |               | encryption with the function                              |
|                                       |               | cinder_utils#create_volume_type()                         |
+---------------------------------------+---------------+-----------------------------------------------------------+

cinder_utils_tests.py - CinderUtilsVolumeTests
----------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             |  Cinder API   | Description                                               |
+=======================================+===============+===========================================================+
| test_create_simple_volume             | 2 & 3         | Tests the creation of a simple volume with the function   |
|                                       |               | cinder_utils#create_volume()                              |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_delete_volume             | 2 & 3         | Tests the creation of a volume with the function          |
|                                       |               | cinder_utils#create_volume() then deletion with the       |
|                                       |               | function cinder_utils#delete_volume()                     |
+---------------------------------------+---------------+-----------------------------------------------------------+

nova_utils_tests.py - NovaUtilsKeypairTests
-------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | Nova API      | Description                                               |
+=======================================+===============+===========================================================+
| test_create_keypair                   | 2             | Ensures that a keypair can be properly created via        |
|                                       |               | nova_utils.upload_keypair() with a public_key object      |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_delete_keypair            | 2             | Ensures that a keypair can be properly deleted via        |
|                                       |               | nova_utils.delete_keypair()                               |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_key_from_file             | 2             | Ensures that a keypair can be properly created via        |
|                                       |               | nova_utils.upload_keypair_file()                          |
+---------------------------------------+---------------+-----------------------------------------------------------+

nova_utils_tests.py - NovaUtilsFlavorTests
------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | Nova API      | Description                                               |
+=======================================+===============+===========================================================+
| test_create_flavor                    | 2             | Ensures that a flavor can be properly created via         |
|                                       |               | nova_utils.create_flavor()                                |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_delete_flavor             | 2             | Ensures that a flavor can be properly deleted via         |
|                                       |               | nova_utils.delete_flavor()                                |
+---------------------------------------+---------------+-----------------------------------------------------------+

nova_utils_tests.py - NovaUtilsInstanceTests
--------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | Nova API      | Description                                               |
+=======================================+===============+===========================================================+
| test_create_instance                  | 2             | Ensures that a VM instance can be properly created via    |
|                                       |               | nova_utils.create_server()                                |
+---------------------------------------+---------------+-----------------------------------------------------------+

nova_utils_tests.py - NovaUtilsInstanceVolumeTests
--------------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | Nova API      | Description                                               |
+=======================================+===============+===========================================================+
| test_add_remove_volume                | 2             | Ensures that a VM instance can properly attach and detach |
|                                       |               | a volume using the nova interface while waiting for       |
|                                       |               | the update to fully occur                                 |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_attach_volume_nowait             | 2             | Ensures that the call to nova_utils.attach_volume raises  |
|                                       |               | an exception when the timeout is too short to return an   |
|                                       |               | properly updated VmInst object                            |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_detach_volume_nowait             | 2             | Ensures that the call to nova_utils.detach_volume raises  |
|                                       |               | an exception when the timeout is too short to return an   |
|                                       |               | properly updated VmInst object                            |
+---------------------------------------+---------------+-----------------------------------------------------------+

create_flavor_tests.py - CreateFlavorTests
------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | Nova API      | Description                                               |
+=======================================+===============+===========================================================+
| test_create_flavor                    | 2             | Ensures that the OpenStackFlavor class's create() method  |
|                                       |               | creates an OpenStack flavor object                        |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_flavor_existing           | 2             | Ensures that the OpenStackFlavor class's create() will not|
|                                       |               | create a flavor with the same name more than once         |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_clean_flavor              | 2             | Ensures that the OpenStackFlavor class's clean() method   |
|                                       |               | will delete the flavor object                             |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_delete_flavor             | 2             | Ensures that the OpenStackFlavor class's clean() method   |
|                                       |               | will not raise an exception when called and the object no |
|                                       |               | longer exists                                             |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_delete_flavor_all_settings| 2             | Ensures that the OpenStackFlavor class will create a      |
|                                       |               | a flavor properly with all supported settings             |
+---------------------------------------+---------------+-----------------------------------------------------------+

heat_utils_tests.py - HeatUtilsCreateSimpleStackTests
-----------------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | Heat API      | Description                                               |
+=======================================+===============+===========================================================+
| test_create_stack                     | 1-3           | Tests the heat_utils.create_stack() with a test template  |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_stack_x2                  | 1-3           | Tests the heat_utils.create_stack() with a test template  |
|                                       |               | and attempts to deploy a second time w/o actually         |
|                                       |               | deploying any objects                                     |
+---------------------------------------+---------------+-----------------------------------------------------------+

heat_utils_tests.py - HeatUtilsCreateComplexStackTests
------------------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | Heat API      | Description                                               |
+=======================================+===============+===========================================================+
| test_get_settings_from_stack          | 1-3           | Tests the heat_utils functions that are responsible for   |
|                                       |               | reverse engineering settings objects of the types deployed|
|                                       |               | by Heat                                                   |
+---------------------------------------+---------------+-----------------------------------------------------------+

heat_utils_tests.py - HeatUtilsRouterTests
------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | Heat API      | Description                                               |
+=======================================+===============+===========================================================+
| test_create_router_with_stack         | 1-3           | Tests ability of the function                             |
|                                       |               | heat_utils.get_stack_routers() to return the correct      |
|                                       |               | OpenStackRouter instance                                  |
+---------------------------------------+---------------+-----------------------------------------------------------+

heat_utils_tests.py - HeatUtilsVolumeTests
------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | Heat API      | Description                                               |
+=======================================+===============+===========================================================+
| test_create_vol_with_stack            | 1-3           | Tests ability of the function                             |
|                                       |               | heat_utils.create_stack() to return the correct           |
|                                       |               | Volume domain objects deployed with Heat                  |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_vol_types_with_stack      | 1-3           | Tests ability of the function                             |
|                                       |               | heat_utils.get_stack_volumes_types() to return the correct|
|                                       |               | VolumeType domain objects deployed with Heat              |
+---------------------------------------+---------------+-----------------------------------------------------------+

heat_utils_tests.py - HeatUtilsKeypairTests
-------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | Heat API      | Description                                               |
+=======================================+===============+===========================================================+
| test_create_keypair_with_stack        | 1-3           | Tests ability of the function                             |
|                                       |               | heat_utils.get_stack_keypairs() to return the correct     |
|                                       |               | Keypair domain objects deployed with Heat                 |
+---------------------------------------+---------------+-----------------------------------------------------------+

heat_utils_tests.py - HeatUtilsSecurityGroupTests
-------------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | Heat API      | Description                                               |
+=======================================+===============+===========================================================+
| test_create_security_group_with_stack | 1-3           | Tests ability of the function                             |
|                                       |               | heat_utils.get_stack_security_groups() to return the      |
|                                       |               | correct SecurityGroup domain objects deployed with Heat   |
+---------------------------------------+---------------+-----------------------------------------------------------+

heat_utils_tests.py - HeatUtilsFlavorTests
------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | Heat API      | Description                                               |
+=======================================+===============+===========================================================+
| test_create_flavor_with_stack         | 1-3           | Tests ability of the function                             |
|                                       |               | heat_utils.get_stack_flavors() to return the correct      |
|                                       |               | Flavor domain objects deployed with Heat                  |
+---------------------------------------+---------------+-----------------------------------------------------------+

magnum_utils_tests.py - MagnumUtilsTests
----------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | Magnum API    | Description                                               |
+=======================================+===============+===========================================================+
| test_create_cluster_template_simple   | 1             | Tests ability of the function                             |
|                                       |               | magnum_utils.create_cluster_template() to create a simple |
|                                       |               | cluster template OpenStack object with minimal config     |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_cluster_template_all      | 1             | Tests ability of the function                             |
|                                       |               | magnum_utils.create_cluster_template() to create a        |
|                                       |               | cluster template OpenStack object with maximum config     |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_cluster_template_bad_image| 1             | Ensures the function                                      |
|                                       |               | magnum_utils.create_cluster_template() will raise a       |
|                                       |               | BadRequest exception when the image does not exist        |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_cluster_template_bad_ext  | 1             | Ensures the function                                      |
| _net                                  |               | magnum_utils.create_cluster_template() will raise a       |
|                                       |               | BadRequest exception when the external network does not   |
|                                       |               | exist                                                     |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_cluster_template_bad      | 1             | Ensures the function                                      |
| _flavor                               |               | magnum_utils.create_cluster_template() will raise a       |
|                                       |               | BadRequest exception when the flavor does not exist       |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_cluster_template_bad      | 1             | Ensures the function                                      |
| _master_flavor                        |               | magnum_utils.create_cluster_template() will raise a       |
|                                       |               | BadRequest exception when the master flavor does not exist|
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_cluster_template_bad      | 1             | Ensures the function                                      |
| _network_driver                       |               | magnum_utils.create_cluster_template() will raise a       |
|                                       |               | BadRequest exception when the network driver is invalid   |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_cluster_template_bad      | 1             | Ensures the function                                      |
| _volume_driver                        |               | magnum_utils.create_cluster_template() will raise a       |
|                                       |               | BadRequest exception when the volume driver is invalid    |
+---------------------------------------+---------------+-----------------------------------------------------------+

settings_utils_tests.py - SettingsUtilsNetworkingTests
------------------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | API           | Description                                               |
+=======================================+===============+===========================================================+
| test_derive_net_settings_no_subnet    | Neutron 2     | Tests to ensure that derived NetworkConfig from an        |
|                                       |               | OpenStack network are correct without a subnet            |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_derive_net_settings_two_subnets  | Neutron 2     | Tests to ensure that derived NetworkConfig from an        |
|                                       |               | OpenStack network are correct with two subnets            |
+---------------------------------------+---------------+-----------------------------------------------------------+


settings_utils_tests.py - SettingsUtilsVmInstTests
--------------------------------------------------
+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | API           | Description                                               |
+=======================================+===============+===========================================================+
| test_derive_vm_inst_config            | Neutron 2     | Tests to ensure that derived VmInstanceSettings from an   |
|                                       |               | OpenStack VM instance is correct                          |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_derive_image_settings            | Neutron 2     | Tests to ensure that derived ImageConfig from an        |
|                                       |               | OpenStack VM instance is correct                          |
+---------------------------------------+---------------+-----------------------------------------------------------+
