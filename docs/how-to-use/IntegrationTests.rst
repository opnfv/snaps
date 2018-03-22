SNAPS OpenStack Integration Testing
===================================

These tests are ones designed to be run within their own dynamically created project along with a newly generated user
account and generally require other OpenStack object creators.

The Test Classes
================

create_security_group_tests.py - CreateSecurityGroupTests
---------------------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | API Versions  | Description                                               |
+=======================================+===============+===========================================================+
| test_create_group_without_rules       | Keysone 2 & 3 | Ensures the OpenStackSecurityGroup class can create a     |
|                                       | Neutron 2     | security group without any rules                          |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_group_admin_user_to_new   | Keysone 2 & 3 | Ensures the OpenStackSecurityGroup class can be created   |
| _project                              | Neutron 2     | by the admin user and associated with a new project       |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_group_new_user_to_admin   | Keysone 2 & 3 | Ensures the OpenStackSecurityGroup class can be created   |
| _project                              | Neutron 2     | by the new user and associated with the admin project     |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_delete_group              | Keysone 2 & 3 | Ensures the OpenStackSecurityGroup class clean() method   |
|                                       | Neutron 2     | will not raise an exception should the group be deleted by|
|                                       |               | some other process                                        |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_group_with_one_simple_rule| Keysone 2 & 3 | Ensures the OpenStackSecurityGroup class can create a     |
|                                       | Neutron 2     | security group with a single simple rule                  |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_group_with_one_complex    | Keysone 2 & 3 | Ensures the OpenStackSecurityGroup class can create a     |
| _rule                                 | Neutron 2     | security group with a single complex rule                 |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_group_with_several_rules  | Keysone 2 & 3 | Ensures the OpenStackSecurityGroup class can create a     |
|                                       | Neutron 2     | security group with several rules                         |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_add_rule                         | Keysone 2 & 3 | Ensures the OpenStackSecurityGroup#add_rule() method      |
|                                       | Neutron 2     | properly creates and associates the new rule              |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_remove_rule_by_id                | Keysone 2 & 3 | Ensures the OpenStackSecurityGroup#remove_rule() method   |
|                                       | Neutron 2     | properly deletes and disassociates the old rule via its ID|
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_remove_rule_by_setting           | Keysone 2 & 3 | Ensures the OpenStackSecurityGroup#remove_rule() method   |
|                                       | Neutron 2     | properly deletes and disassociates the old rule via its   |
|                                       |               | setting object                                            |
+---------------------------------------+---------------+-----------------------------------------------------------+

create_security_group_tests.py - CreateMultipleSecurityGroupTests
-----------------------------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | API Versions  | Description                                               |
+=======================================+===============+===========================================================+
| test_sec_grp_same_name_diff_proj      | Keysone 2 & 3 | Ensures the OpenStackSecurityGroup class does not         |
|                                       | Neutron 2     | initialize security groups with the same name from other  |
|                                       |               | project/tenants                                           |
+---------------------------------------+---------------+-----------------------------------------------------------+

create_image_tests.py - CreateImageSuccessTests
-----------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | Glance API    | Description                                               |
+=======================================+===============+===========================================================+
| test_create_image_clean_url           | 1 & 2         | Ensures the OpenStackImage class can create an image from |
|                                       |               | a download URL location                                   |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_image_clean_url_properties| 1 & 2         | Ensures the OpenStackImage class can create an image from |
|                                       |               | a download URL location with custom properties            |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_image_clean_file          | 1 & 2         | Ensures the OpenStackImage class can create an image from |
|                                       |               | a locally sourced image file                              |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_delete_image              | 1 & 2         | Ensures the OpenStackImage.clean() method deletes an image|
|                                       |               | and does not raise an exception on subsequent calls to the|
|                                       |               | clean() method                                            |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_same_image                | 1 & 2         | Ensures the OpenStackImage.create() method does not create|
|                                       |               | another image when one already exists with the same name  |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_same_image_new_settings   | 1 & 2         | Tests the creation of an OpenStack image when the image   |
|                                       |               | already exists and the configuration only contains the    |
|                                       |               | the name.                                                 |
+---------------------------------------+---------------+-----------------------------------------------------------+

create_image_tests.py - CreateImageNegativeTests
------------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | Glance API    | Description                                               |
+=======================================+===============+===========================================================+
| test_bad_image_name                   | 1 & 2         | Ensures OpenStackImage.create() results in an Exception   |
|                                       |               | being raised when the ImageConfig.name attribute has    |
|                                       |               | not been set                                              |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_bad_image_url                    | 1 & 2         | Ensures OpenStackImage.create() results in an Exception   |
|                                       |               | being raised when the download URL is invalid             |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_bad_image_type                   | 1 & 2         | Ensures OpenStackImage.create() results in an Exception   |
|                                       |               | being raised when the image format is 'foo'               |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_bad_image_file                   | 1 & 2         | Ensures OpenStackImage.create() results in an Exception   |
|                                       |               | being raised when the image file does not exist           |
+---------------------------------------+---------------+-----------------------------------------------------------+

create_image_tests.py - CreateMultiPartImageTests
-------------------------------------------------

+----------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                              | Glance API    | Description                                               |
+========================================+===============+===========================================================+
| test_create_three_part_image_from_url  | 1 & 2         | Ensures that a 3-part image can be created when each part |
|                                        |               | is being sourced from URLs                                |
+----------------------------------------+---------------+-----------------------------------------------------------+
| test_create_three_part_image_from_file | 1 & 2         | Ensures that a 3-part image can be created when each part |
| _3_creators                            |               | is being sourced from local files and 3 creators are used |
+----------------------------------------+---------------+-----------------------------------------------------------+
| test_create_three_part_image_from_url  | 1 & 2         | Ensures that a 3-part image can be created when each part |
| _3_creators                            |               | is being sourced from a URL and 3 creators are used       |
+----------------------------------------+---------------+-----------------------------------------------------------+

create_keypairs_tests.py - CreateKeypairsTests
----------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | Nova API      | Description                                               |
+=======================================+===============+===========================================================+
| test_create_keypair_only              | 2             | Ensures that a keypair object can be created simply by    |
|                                       |               | only configuring a name                                   |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_keypair_large_key         | 2             | Ensures that a keypair object can be created with a large |
|                                       |               | key of 10000 bytes                                        |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_delete_keypair            | 2             | Ensures that a keypair object is deleted via              |
|                                       |               | OpenStackKeypair.clean() and subsequent calls do not      |
|                                       |               | result in exceptions                                      |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_keypair_save_pub_only     | 2             | Ensures that a keypair object can be created when the only|
|                                       |               | the public key is cached to disk                          |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_keypair_save_both         | 2             | Ensures that a keypair object can be created when both the|
|                                       |               | public and private keys are cached to disk                |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_keypair_from_file         | 2             | Ensures that a keypair object can be created with an      |
|                                       |               | existing public key file                                  |
+---------------------------------------+---------------+-----------------------------------------------------------+

create_keypairs_tests.py - CreateKeypairsCleanupTests
-----------------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | Nova API      | Description                                               |
+=======================================+===============+===========================================================+
| test_create_keypair_gen_files_delete_1| 2             | Ensures that new keypair files are deleted by default     |
|                                       |               | by OpenStackKeypair#clean()                               |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_keypair_gen_files_delete_2| 2             | Ensures that new keypair files are deleted by             |
|                                       |               | OpenStackKeypair#clean() when the settings delete_on_clean|
|                                       |               | attribute is set to True                                  |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_keypair_gen_files_keep    | 2             | Ensures that new keypair files are not deleted by         |
|                                       |               | OpenStackKeypair#clean()                                  |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_keypair_exist_files_keep  | 2             | Ensures that existing keypair files are not deleted by    |
|                                       |               | OpenStackKeypair#clean()                                  |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_keypair_exist_files_delete| 2             | Ensures that existing keypair files are deleted by        |
|                                       |               | OpenStackKeypair#clean()                                  |
+---------------------------------------+---------------+-----------------------------------------------------------+

create_network_tests.py - CreateNetworkSuccessTests
---------------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | Neutron API   | Description                                               |
+=======================================+===============+===========================================================+
| test_create_network_without_router    | 2             | Ensures that a network can be created via the             |
|                                       |               | OpenStackNetwork class without any routers                |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_delete_network            | 2             | Ensures that a router can be deleted via the              |
|                                       |               | OpenStackNetwork.clean() method                           |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_network_with_router       | 2             | Ensures that a network can be created via the             |
|                                       |               | OpenStackNetwork class with a router                      |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_networks_same_name        | 2             | Ensures that the OpenStackNetwork.create() method will not|
|                                       |               | create a network with the same name                       |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_networks_router_admin_user| 2             | Ensures that the networks, subnets, and routers can be    |
| _to_new_project                       |               | create created by an admin user and assigned to a new     |
|                                       |               | project ID                                                |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_networks_router_new_user  | 2             | Ensures that the networks, subnets, and routers can be    |
| _to_admin_project                     |               | create created by a new admin user and assigned to the    |
|                                       |               | 'admin' project ID                                        |
+---------------------------------------+---------------+-----------------------------------------------------------+

create_network_tests.py - CreateNetworkGatewayTests
---------------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | Neutron API   | Description                                               |
+=======================================+===============+===========================================================+
| test_create_subnet_default_gateway_ip | 2             | Ensures that a network can be created with a Subnet that  |
|                                       |               | has the gateway_ip automatically assigned                 |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_subnet_valid_gateway_ip   | 2             | Ensures that a network can be created with a Subnet that  |
|                                       |               | has the gateway_ip statically assigned with a valid IP    |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_subnet_no_gateway         | 2             | Ensures that a network can be created where no gateway_ip |
|                                       |               | is assigned                                               |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_subnet_invalid_gateway_ip | 2             | Ensures that a network cannot be created with a Subnet    |
|                                       |               | has an invalid gateway_ip value such as 'foo'             |
+---------------------------------------+---------------+-----------------------------------------------------------+

create_network_tests.py - CreateNetworkIPv6Tests
------------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | Neutron API   | Description                                               |
+=======================================+===============+===========================================================+
| test_create_network_one_ipv6_subnet   | 2             | Ensures that a network can be created with an IPv6 subnet |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_network_ipv4_ipv6_subnet  | 2             | Ensures that a network can be created with an IPv4 and    |
|                                       |               | IPv6 subnet                                               |
+---------------------------------------+---------------+-----------------------------------------------------------+

create_network_tests.py - CreateMultipleNetworkTests
----------------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | Neutron API   | Description                                               |
+=======================================+===============+===========================================================+
| test_network_same_name_diff_proj      | 2             | Ensures that a network with the same name can be created  |
|                                       |               | against different projects                                |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_network_create_by_admin_to       | 2             | Ensures that a network can be created by the admin user   |
| _different_project                    |               | to another project and that a creator with the credentials|
|                                       |               | to the other project will not create a new network with   |
|                                       |               | the same name                                             |
+---------------------------------------+---------------+-----------------------------------------------------------+

create_router_tests.py - CreateRouterSuccessTests
-------------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | Neutron API   | Description                                               |
+=======================================+===============+===========================================================+
| test_create_router_vanilla            | 2             | Ensures that a router can be created via the              |
|                                       |               | OpenStackRouter class with minimal settings               |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_router_admin_user_to_new  | 2             | Ensures that a router can be created by an admin user and |
| _project                              |               | assigned to a new project                                 |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_router_new_user_to_admin  | 2             | Ensures that a router can be created by a new user and    |
| _project                              |               | assigned to the admin project                             |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_delete_router             | 2             | Ensures that a router can be deleted via the              |
|                                       |               | OpenStackRouter.clean() method                            |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_router_admin_state_false  | 2             | Ensures that a router can created with                    |
|                                       |               | admin_state_up = False                                    |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_router_admin_state_True   | 2             | Ensures that a router can created with                    |
|                                       |               | admin_state_up = True                                     |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_router_private_network    | 2             | Ensures that a router port can be created against a       |
|                                       |               | private network                                           |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_router_external_network   | 2             | Ensures that a router can be created that is connected to |
|                                       |               | both external and private internal networks               |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_router_with_ext_port      | 2             | Ensures that a router can be created by an 'admin' user   |
|                                       |               | with a port to an external network                        |
+---------------------------------------+---------------+-----------------------------------------------------------+

create_router_tests.py - CreateRouterNegativeTests
--------------------------------------------------

+----------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                              | Neutron API   | Description                                               |
+========================================+===============+===========================================================+
| test_create_router_noname              | 2             | Ensures that an exception is raised when attempting to    |
|                                        |               | create a router without a name                            |
+----------------------------------------+---------------+-----------------------------------------------------------+
| test_create_router_invalid_gateway_name| 2             | Ensures that an exception is raised when attempting to    |
|                                        |               | create a router to an external network that does not exist|
+----------------------------------------+---------------+-----------------------------------------------------------+
| test_create_router_admin_ports         | 2             | Ensures that an exception is raised when attempting to    |
|                                        |               | create a router with ports to networks owned by another   |
|                                        |               | project                                                   |
+----------------------------------------+---------------+-----------------------------------------------------------+

create_router_tests.py - CreateMultipleRouterTests
--------------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | Neutron API   | Description                                               |
+=======================================+===============+===========================================================+
| test_router_same_name_diff_proj       | 2             | Ensures that a router with the same name can be created   |
|                                       |               | against different projects                                |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_router_create_by_admin_to        | 2             | Ensures that a router can be created by the admin user    |
| _different_project                    |               | to another project and that a creator with the credentials|
|                                       |               | to the other project will not create a new router with    |
|                                       |               | the same name                                             |
+---------------------------------------+---------------+-----------------------------------------------------------+

create_router_tests.py - CreateRouterSecurityGroupTests
-------------------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | Neutron API   | Description                                               |
+=======================================+===============+===========================================================+
| test_create_router_secure_port        | 2             | Ensures that a router's port can have a security group    |
|                                       |               | applied to it                                             |
+---------------------------------------+---------------+-----------------------------------------------------------+

create_qos_tests.py - CreateQoSTests
------------------------------------

+----------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                              |  Cinder API   | Description                                               |
+========================================+===============+===========================================================+
| test_create_qos                        | 2 & 3         | Tests the creation of a QoS Spec with the class           |
|                                        |               | OpenStackQoS                                              |
+----------------------------------------+---------------+-----------------------------------------------------------+
| test_create_delete_qos                 | 2 & 3         | Tests the creation of a QoS Spec with the class           |
|                                        |               | OpenStackQoS, its deletion with cinder_utils.py the       |
|                                        |               | the attempts to use the clean() method to ensure an       |
|                                        |               | exception is not called                                   |
+----------------------------------------+---------------+-----------------------------------------------------------+
| test_create_same_qos                   | 2 & 3         | Tests the creation of a QoS Spec with the class           |
|                                        |               | OpenStackQoS then instantiates another OpenStackQoS       |
|                                        |               | object with the same configuration to ensure the second   |
|                                        |               | instance returns the ID of the original                   |
+----------------------------------------+---------------+-----------------------------------------------------------+

create_volume_type_tests.py - CreateSimpleVolumeTypeSuccessTests
----------------------------------------------------------------

+----------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                              |  Cinder API   | Description                                               |
+========================================+===============+===========================================================+
| test_create_volume_type                | 2 & 3         | Tests the creation of a Volume Type with the class        |
|                                        |               | OpenStackVolumeType                                       |
+----------------------------------------+---------------+-----------------------------------------------------------+
| test_create_delete_volume_type         | 2 & 3         | Tests the creation of a Volume Type with the class        |
|                                        |               | OpenStackVolumeType, its deletion with cinder_utils.py,   |
|                                        |               | then attempts to use the clean() method to ensure an      |
|                                        |               | exception is not raised                                   |
+----------------------------------------+---------------+-----------------------------------------------------------+
| test_create_same_volume_type           | 2 & 3         | Tests the creation of a Volume Type with the class        |
|                                        |               | OpenStackVolumeType then instantiates another             |
|                                        |               | OpenStackVolumeType object with the same configuration to |
|                                        |               | ensure the second instance returns the ID of the original |
+----------------------------------------+---------------+-----------------------------------------------------------+

create_volume_type_tests.py - CreateSimpleVolumeTypeComplexTests
----------------------------------------------------------------

+-----------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                               |  Cinder API   | Description                                               |
+=========================================+===============+===========================================================+
| test_volume_type_with_qos               | 2 & 3         | Tests the creation of a Volume Type with the class        |
|                                         |               | OpenStackVolumeType with a QoSSpec                        |
+-----------------------------------------+---------------+-----------------------------------------------------------+
| test_volume_type_with_encryption        | 2 & 3         | Tests the creation of a Volume Type with the class        |
|                                         |               | OpenStackVolumeType with encryption                       |
+-----------------------------------------+---------------+-----------------------------------------------------------+
| test_volume_type_with_qos_and_encryption| 2 & 3         | Tests the creation of a Volume Type with the class        |
|                                         |               | OpenStackVolumeType with encryption and QoS Spec          |
+-----------------------------------------+---------------+-----------------------------------------------------------+

create_volume_tests.py - CreateSimpleVolumeSuccessTests
-------------------------------------------------------

+----------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                              |  Cinder API   | Description                                               |
+========================================+===============+===========================================================+
| test_create_volume_simple              | 2 & 3         | Tests the creation of a Volume Type with the class        |
|                                        |               | OpenStackVolume                                           |
+----------------------------------------+---------------+-----------------------------------------------------------+
| test_create_delete_volume              | 2 & 3         | Tests the creation of a Volume with the class             |
|                                        |               | OpenStackVolume, its deletion with cinder_utils.py, then  |
|                                        |               | attempts to use the clean() method to ensure an           |
|                                        |               | exception is not raised                                   |
+----------------------------------------+---------------+-----------------------------------------------------------+
| test_create_same_volume                | 2 & 3         | Tests the creation of a Volume with the class             |
|                                        |               | OpenStackVolume then instantiates another                 |
|                                        |               | OpenStackVolume object with the same configuration to     |
|                                        |               | ensure the second instance returns the ID of the original |
+----------------------------------------+---------------+-----------------------------------------------------------+

create_volume_tests.py - CreateSimpleVolumeFailureTests
-------------------------------------------------------

+----------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                              |  Cinder API   | Description                                               |
+========================================+===============+===========================================================+
| test_create_volume_bad_size            | 2 & 3         | Tests to ensure that attempting to create a volume with a |
|                                        |               | size of -1 raises a BadRequest exception                  |
+----------------------------------------+---------------+-----------------------------------------------------------+
| test_create_volume_bad_type            | 2 & 3         | Tests to ensure that attempting to create a volume with a |
|                                        |               | type that does not exist raises a NotFound exception      |
+----------------------------------------+---------------+-----------------------------------------------------------+
| test_create_volume_bad_image           | 2 & 3         | Tests to ensure that attempting to create a volume with an|
|                                        |               | image that does not exist raises a BadRequest exception   |
+----------------------------------------+---------------+-----------------------------------------------------------+

create_volume_tests.py - CreateVolumeWithTypeTests
--------------------------------------------------

+----------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                              |  Cinder API   | Description                                               |
+========================================+===============+===========================================================+
| test_bad_volume_type                   | 2 & 3         | Tests to ensure the creation of a Volume with the         |
|                                        |               | OpenStackVolume#create() method raises a NotFound         |
|                                        |               | exception when attempting to apply a VolumeType that does |
|                                        |               | not exist                                                 |
+----------------------------------------+---------------+-----------------------------------------------------------+
| test_valid_volume_type                 | 2 & 3         | Tests to ensure the creation of a Volume with the         |
|                                        |               | OpenStackVolume#create() method properly creates the      |
|                                        |               | volume when associating with a valid VolumeType           |
+----------------------------------------+---------------+-----------------------------------------------------------+

create_volume_tests.py - CreateVolumeWithImageTests
---------------------------------------------------

+----------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                              |  Cinder API   | Description                                               |
+========================================+===============+===========================================================+
| test_bad_image_name                    | 2 & 3         | Tests to ensure the creation of a Volume with the         |
|                                        |               | OpenStackVolume#create() method raises a BadRequest       |
|                                        |               | exception when attempting to apply an image that does not |
|                                        |               | exist                                                     |
+----------------------------------------+---------------+-----------------------------------------------------------+
| test_valid_volume_image                | 2 & 3         | Tests to ensure the creation of a Volume with the         |
|                                        |               | OpenStackVolume#create() method properly creates the      |
|                                        |               | volume when associating with a valid image                |
+----------------------------------------+---------------+-----------------------------------------------------------+

create_volume_tests.py - CreateVolMultipleCredsTests
----------------------------------------------------

+----------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                              |  Cinder API   | Description                                               |
+========================================+===============+===========================================================+
| test_create_by_admin_to_other_proj     | 2 & 3         | Tests to ensure the creation of a Volume as a user with   |
|                                        |               | an 'admin' role can create a volume to another project    |
|                                        |               | and a creator with the credentails to that project will   |
|                                        |               | not create another with the same name                     |
|                                        |               | Currently inactive due to                                 |
|                                        |               | https://bugs.launchpad.net/cinder/+bug/1641982            |
+----------------------------------------+---------------+-----------------------------------------------------------+
| test_create_two_vol_same_name_diff_proj| 2 & 3         | Tests to ensure the creation of a Volume with the same    |
|                                        |               | name by two different creators with different credentials |
|                                        |               | will create two different volumes with the same name      |
|                                        |               | that are applied to each project in question              |
+----------------------------------------+---------------+-----------------------------------------------------------+

create_stack_tests.py - CreateStackSuccessTests
-----------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             |   Heat API    | Description                                               |
+=======================================+===============+===========================================================+
| test_create_stack_template_file       | 1-3           | Ensures that a Heat stack can be created with a file-based|
|                                       |               | Heat template file                                        |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_stack_template_dict       | 1-3           | Ensures that a Heat stack can be created with a dictionary|
|                                       |               | Heat template                                             |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_delete_stack              | 1-3           | Ensures that a Heat stack can be created and deleted      |
|                                       |               | while having clean() called 2x without an exception       |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_same_stack                | 1-3           | Ensures that a Heat stack with the same name cannot be    |
|                                       |               | created 2x                                                |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_retrieve_network_creators        | 1-3           | Ensures that an OpenStackHeatStack instance can return an |
|                                       |               | OpenStackNetwork instance configured as deployed          |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_retrieve_vm_inst_creators        | 1-3           | Ensures that an OpenStackHeatStack instance can return an |
|                                       |               | OpenStackVmInstance instance configured as deployed       |
+---------------------------------------+---------------+-----------------------------------------------------------+

create_stack_tests.py - CreateStackVolumeTests
----------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             |   Heat API    | Description                                               |
+=======================================+===============+===========================================================+
| test_retrieve_volume_creator          | 1-3           | Ensures that an OpenStackHeatStack instance can return a  |
|                                       |               | OpenStackVolume instance that it was responsible for      |
|                                       |               | deploying                                                 |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_retrieve_volume_type_creator     | 1-3           | Ensures that an OpenStackHeatStack instance can return a  |
|                                       |               | OpenStackVolumeType instance that it was responsible for  |
|                                       |               | deploying                                                 |
+---------------------------------------+---------------+-----------------------------------------------------------+

create_stack_tests.py - CreateStackFloatingIpTests
--------------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             |   Heat API    | Description                                               |
+=======================================+===============+===========================================================+
| test_connect_via_ssh_heat_vm          | 1             | Ensures that an OpenStackHeatStack instance can create a  |
|                                       |               | VM with a floating IP that can be accessed via            |
|                                       |               | OpenStackVmInstance                                       |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_connect_via_ssh_heat_vm_derived  | 1             | Ensures that an OpenStackHeatStack instance can create a  |
|                                       |               | VM with a floating IP where a generated initialized       |
|                                       |               | OpenStackHeatStack can return an initialized              |
|                                       |               | OpenStackVmInstance object that will be used to access the|
|                                       |               | VM via SSH                                                |
+---------------------------------------+---------------+-----------------------------------------------------------+

create_stack_tests.py - CreateStackNestedResourceTests
------------------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             |   Heat API    | Description                                               |
+=======================================+===============+===========================================================+
| test_nested                           | 1             | Ensures that an OpenStackHeatStack with an external       |
|                                       |               | resource file with VMs with floating IPs can be accessed  |
|                                       |               | in the class OpenStackVmInstance and return the associated|
|                                       |               | initialized OpenStackVmInstance objects                   |
+---------------------------------------+---------------+-----------------------------------------------------------+

create_stack_tests.py - CreateStackRouterTests
----------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             |   Heat API    | Description                                               |
+=======================================+===============+===========================================================+
| test_retrieve_router_creator          | 1             | Ensures that an OpenStackHeatStack instance can return a  |
|                                       |               | OpenStackRouter instance that it was responsible for      |
|                                       |               | deploying                                                 |
+---------------------------------------+---------------+-----------------------------------------------------------+

create_stack_tests.py - CreateStackFlavorTests
----------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             |   Heat API    | Description                                               |
+=======================================+===============+===========================================================+
| test_retrieve_flavor_creator          | 1-3           | Ensures that an OpenStackHeatStack instance can return a  |
|                                       |               | OpenStackFlavor instance that it was responsible for      |
|                                       |               | deploying                                                 |
+---------------------------------------+---------------+-----------------------------------------------------------+

create_stack_tests.py - CreateStackKeypairTests
-----------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             |   Heat API    | Description                                               |
+=======================================+===============+===========================================================+
| test_retrieve_keypair_creator         | 1-3           | Ensures that an OpenStackHeatStack instance can return a  |
|                                       |               | OpenStackKeypair instance that it was responsible for     |
|                                       |               | deploying                                                 |
+---------------------------------------+---------------+-----------------------------------------------------------+

create_stack_tests.py - CreateStackSecurityGroupTests
-----------------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             |   Heat API    | Description                                               |
+=======================================+===============+===========================================================+
| test_retrieve_security_group_creator  | 1-3           | Ensures that an OpenStackHeatStack instance can return a  |
|                                       |               | OpenStackSecurityGroup instance that it was responsible   |
|                                       |               | for deploying                                             |
+---------------------------------------+---------------+-----------------------------------------------------------+

create_stack_tests.py - CreateComplexStackTests
-----------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             |   Heat API    | Description                                               |
+=======================================+===============+===========================================================+
| test_connect_via_ssh_heat_vm          | 1-3           | Ensures that two OpenStackHeatStack instances can return  |
|                                       |               | OpenStackVmInstance instances one configured with a       |
|                                       |               | floating IP and keypair and can be access via SSH         |
+---------------------------------------+---------------+-----------------------------------------------------------+

create_stack_tests.py - CreateStackNegativeTests
------------------------------------------------

+----------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                              |   Heat API    | Description                                               |
+========================================+===============+===========================================================+
| test_missing_dependencies              | 1-3           | Ensures that a Heat template fails to deploy when expected|
|                                        |               | dependencies are missing                                  |
+----------------------------------------+---------------+-----------------------------------------------------------+
| test_bad_stack_file                    | 1-3           | Ensures that a Heat template fails to deploy when the Heat|
|                                        |               | template file does not exist                              |
+----------------------------------------+---------------+-----------------------------------------------------------+

create_stack_tests.py - CreateStackFailureTests
-----------------------------------------------

+----------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                              |   Heat API    | Description                                               |
+========================================+===============+===========================================================+
| test_stack_failure                     | 1-3           | Ensures that a Heat template fails to deploy when expected|
|                                        |               | dependencies are missing                                  |
+----------------------------------------+---------------+-----------------------------------------------------------+

create_instance_tests.py - CreateInstanceSimpleTests
----------------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | API Versions  | Description                                               |
+=======================================+===============+===========================================================+
| test_create_delete_instance           | Nova 2        | Ensures that the OpenStackVmInstance.clean() method       |
|                                       | Neutron 2     | deletes the instance as well as ensuring the VmInst       |
|                                       |               | availability_zone is populated and compute_host is None   |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_admin_instance            | Nova 2        | Ensures that the VmInst object members availability_zone  |
|                                       | Neutron 2     | and compute_host return a value                           |
+---------------------------------------+---------------+-----------------------------------------------------------+

create_instance_tests.py - CreateInstanceExternalNetTests
---------------------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | API Versions  | Description                                               |
+=======================================+===============+===========================================================+
| test_create_instance_public_net       | Nova 2        | Ensures that an OpenStackVmInstance initialized as a user |
|                                       | Neutron 2     | of type 'admin' can create a VM against an external net   |
+---------------------------------------+---------------+-----------------------------------------------------------+

create_instance_tests.py - SimpleHealthCheck
--------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | API Versions  | Description                                               |
+=======================================+===============+===========================================================+
| test_check_vm_ip_dhcp                 | Nova 2        | Tests the creation of an OpenStack instance with a single |
|                                       | Neutron 2     | port and it's assigned IP address                         |
+---------------------------------------+---------------+-----------------------------------------------------------+

create_instance_tests.py - CreateInstanceTwoNetTests
----------------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | API Versions  | Description                                               |
+=======================================+===============+===========================================================+
| test_ping_via_router                  | Nova 2        | Tests the ability of two VMs on different private overlay |
|                                       | Neutron 2     | networks tied together with a router to ping each other   |
+---------------------------------------+---------------+-----------------------------------------------------------+

create_instance_tests.py - CreateInstanceSingleNetworkTests
-----------------------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | API Versions  | Description                                               |
+=======================================+===============+===========================================================+
| test_single_port_static               | Nova 2        | Ensures that an instance with a single port/NIC with a    |
|                                       | Neutron 2     | static IP can be created                                  |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_ssh_client_fip_before_active     | Nova 2        | Ensures that an instance can be reached over SSH when the |
|                                       | Neutron 2     | floating IP is assigned prior to the VM becoming ACTIVE   |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_ssh_client_fip_after_active      | Nova 2        | Ensures that an instance can be reached over SSH when the |
|                                       | Neutron 2     | floating IP is assigned after to the VM becoming ACTIVE   |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_ssh_client_fip_after_init        | Nova 2        | Ensures that an instance can have a floating IP assigned  |
|                                       | Neutron 2     | added after initialization                                |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_ssh_client_fip_reverse_engineer  | Nova 2        | Ensures that an instance can be reverse engineered and    |
|                                       | Neutron 2     | allows for a floating IP to be added after initialization |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_ssh_client_fip_after_reboot      | Nova 2        | Ensures that an instance can be reached over SSH after    |
|                                       | Neutron 2     | a reboot call has been issued                             |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_ssh_client_fip_second_creator    | Nova 2        | Ensures that an instance can be reached over SSH via a    |
|                                       | Neutron 2     | second identical creator object                           |
+---------------------------------------+---------------+-----------------------------------------------------------+

create_instance_tests.py - CreateInstancePortManipulationTests
--------------------------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | API Versions  | Description                                               |
+=======================================+===============+===========================================================+
| test_set_custom_valid_ip_one_subnet   | Nova 2        | Ensures that an instance's can have a valid static IP is  |
|                                       | Neutron 2     | properly assigned                                         |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_set_one_port_two_ip_one_subnet   | Nova 2        | Ensures that an instance can have two static IPs on a     |
|                                       | Neutron 2     | single port from a single subnet                          |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_set_one_port_two_ip_two_subnets  | Nova 2        | Ensures that an instance can have two static IPs on a     |
|                                       | Neutron 2     | single port from different subnets on a network           |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_set_custom_invalid_ip_one_subnet | Nova 2        | Ensures that an instance's port with an invalid static IP |
|                                       | Neutron 2     | raises an exception                                       |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_set_custom_valid_mac             | Nova 2        | Ensures that an instance's port can have a valid MAC      |
|                                       | Neutron 2     | address properly assigned                                 |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_set_custom_invalid_mac           | Nova 2        | Ensures that an instance's port with an invalid MAC       |
|                                       | Neutron 2     | address raises and exception                              |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_set_custom_mac_and_ip            | Nova 2        | Ensures that an instance's port with a valid static IP and|
|                                       | Neutron 2     | MAC are properly assigned                                 |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_set_allowed_address_pairs        | Nova 2        | Ensures the configured allowed_address_pairs is properly  |
|                                       | Neutron 2     | set on a VMs port                                         |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_set_allowed_address_pairs_bad_mac| Nova 2        | Ensures the port cannot be created when a bad MAC address |
|                                       | Neutron 2     | format is used in the allowed_address_pairs port attribute|
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_set_allowed_address_pairs_bad_ip | Nova 2        | Ensures the port cannot be created when a bad IP address  |
|                                       | Neutron 2     | format is used in the allowed_address_pairs port attribute|
+---------------------------------------+---------------+-----------------------------------------------------------+

create_instance_tests.py - CreateInstanceOnComputeHost
------------------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | API Versions  | Description                                               |
+=======================================+===============+===========================================================+
| test_deploy_vm_to_each_compute_node   | Nova 2        | Tests to ensure that one can fire up an instance on each  |
|                                       | Neutron 2     | active compute node                                       |
+---------------------------------------+---------------+-----------------------------------------------------------+

create_instance_tests.py - CreateInstanceFromThreePartImage
-----------------------------------------------------------

+-----------------------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                                           | API Versions  | Description                                               |
+=====================================================+===============+===========================================================+
| test_create_delete_instance_from_three_part_image   | Nova 2        | Tests to ensure that one can fire up an instance then     |
|                                                     | Neutron 2     | delete it when using a 3-part image                       |
+-----------------------------------------------------+---------------+-----------------------------------------------------------+

create_instance_tests.py - CreateInstanceIPv6NetworkTests (Staging)
-------------------------------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | API Versions  | Description                                               |
+=======================================+===============+===========================================================+
| test_v4fip_v6overlay                  | Nova 2        | Expects a BadRequest exception to be raised when          |
|                                       | Neutron 2     | attempting to add an IPv4 floating IP to a VM with an IPv6|
|                                       |               | port                                                      |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_fip_v4and6_overlay               | Nova 2        | Connects to a VM via a floating IP joined to a port that  |
|                                       | Neutron 2     | has been confiured with both IPv4 and IPv6 addresses      |
+---------------------------------------+---------------+-----------------------------------------------------------+

create_instance_tests.py - InstanceSecurityGroupTests
-----------------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | API Versions  | Description                                               |
+=======================================+===============+===========================================================+
| test_add_security_group               | Nova 2        | Ensures that a VM instance can have security group added  |
|                                       | Neutron 2     | to it while its running                                   |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_add_invalid_security_group       | Nova 2        | Ensures that a VM instance does not accept the addition of|
|                                       | Neutron 2     | a security group that no longer exists                    |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_remove_security_group            | Nova 2        | Ensures that a VM instance accepts the removal of a       |
|                                       | Neutron 2     | security group                                            |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_remove_security_group_never_added| Nova 2        | Ensures that a VM instance does not accept the removal of |
|                                       | Neutron 2     | a security group that was never added in the first place  |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_add_same_security_group          | Nova 2        | Ensures that a VM instance does not add a security group  |
|                                       | Neutron 2     | that has already been added to the instance               |
+---------------------------------------+---------------+-----------------------------------------------------------+

create_instance_tests.py - CreateInstanceVolumeTests
----------------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | API Versions  | Description                                               |
+=======================================+===============+===========================================================+
| test_create_instance_with_one_volume  | Nova 2        | Ensures that a VM instance can have one volume attached   |
|                                       | Cinder 2 & 3  | to it                                                     |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_instance_with_two_volumes | Nova 2        | Ensures that a VM instance can have two volumes attached  |
|                                       | Cinder 2 & 3  | to it                                                     |
+---------------------------------------+---------------+-----------------------------------------------------------+

ansible_utils_tests.py - AnsibleProvisioningTests
-------------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | API Versions  | Description                                               |
+=======================================+===============+===========================================================+
| test_apply_simple_playbook            | Nova 2        | Ensures that an instance assigned with a floating IP will |
|                                       | Neutron 2     | apply a simple Ansible playbook                           |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_apply_template_playbook          | Nova 2        | Ensures that an instance assigned with a floating IP will |
|                                       | Neutron 2     | apply a Ansible playbook containing Jinga2 substitution   |
|                                       |               | values                                                    |
+---------------------------------------+---------------+-----------------------------------------------------------+

cluster_template_tests.py - CreateClusterTemplateTests
------------------------------------------------------

+----------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                              |  Magnum API   | Description                                               |
+========================================+===============+===========================================================+
| test_create_cluster_template           | 1             | Tests the creation of a Cluster template with the class   |
|                                        |               | OpenStackClusterTemplate                                  |
+----------------------------------------+---------------+-----------------------------------------------------------+
| test_create_delete_cluster_template    | 1             | Tests the creation and deletiong of a Cluster template    |
|                                        |               | with the class OpenStackClusterTemplate                   |
+----------------------------------------+---------------+-----------------------------------------------------------+
| test_create_same_cluster_template      | 1             | Tests the creation of a Cluster template 2x using the same|
|                                        |               | config object to ensure it was only created once          |
+----------------------------------------+---------------+-----------------------------------------------------------+
| test_create_cluster_template_bad_flavor| 1             | Tests to ensure OpenStackClusterTemplate#create() will    |
|                                        |               | raise an exception when the flavor is invalid             |
+----------------------------------------+---------------+-----------------------------------------------------------+
| test_create_cluster_template_bad_master| 1             | Tests to ensure OpenStackClusterTemplate#create() will    |
| _flavor                                |               | raise an exception when the master flavor is invalid      |
+----------------------------------------+---------------+-----------------------------------------------------------+
| test_create_cluster_template_bad_image | 1             | Tests to ensure OpenStackClusterTemplate#create() will    |
|                                        |               | raise an exception when the image is invalid              |
+----------------------------------------+---------------+-----------------------------------------------------------+
| test_create_cluster_template_bad       | 1             | Tests to ensure OpenStackClusterTemplate#create() will    |
| _network_driver                        |               | raise an exception when the network driver is invalid     |
+----------------------------------------+---------------+-----------------------------------------------------------+
| test_create_cluster_template_bad       | 1             | Tests to ensure OpenStackClusterTemplate#create() will    |
| _volume_driver                         |               | raise an exception when the volume driver is invalid      |
+----------------------------------------+---------------+-----------------------------------------------------------+

