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
|                                       |               | being raised when the ImageSettings.name attribute has    |
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
| test_create_keypair_gen_files_delete_2| 2             | Ensures that new keypair files are deleted by         |
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

create_stack_tests.py - CreateStackSuccessTests
-----------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | Neutron API   | Description                                               |
+=======================================+===============+===========================================================+
| test_create_stack_template_file       | 2             | Ensures that a Heat stack can be created with a file-based|
|                                       |               | Heat template file                                        |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_stack_template_dict       | 2             | Ensures that a Heat stack can be created with a dictionary|
|                                       |               | Heat template                                             |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_delete_stack              | 2             | Ensures that a Heat stack can be created and deleted      |
|                                       |               | while having clean() called 2x without an exception       |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_same_stack                | 2             | Ensures that a Heat stack with the same name cannot be    |
|                                       |               | created 2x                                                |
+---------------------------------------+---------------+-----------------------------------------------------------+
| test_create_same_stack                | 2             | Ensures that a Heat stack with the same name cannot be    |
|                                       |               | created 2x                                                |
+---------------------------------------+---------------+-----------------------------------------------------------+

create_stack_tests.py - CreateStackNegativeTests
------------------------------------------------

+----------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                              | Neutron API   | Description                                               |
+========================================+===============+===========================================================+
| test_missing_dependencies              | 2             | Ensures that a Heat template fails to deploy when expected|
|                                        |               | dependencies are missing                                  |
+----------------------------------------+---------------+-----------------------------------------------------------+
| test_bad_stack_file                    | 2             | Ensures that a Heat template fails to deploy when the Heat|
|                                        |               | template file does not exist                              |
+----------------------------------------+---------------+-----------------------------------------------------------+

create_instance_tests.py - CreateInstanceSimpleTests
----------------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | API Versions  | Description                                               |
+=======================================+===============+===========================================================+
| test_create_delete_instance           | Nova 2        | Ensures that the OpenStackVmInstance.clean() method       |
|                                       | Neutron 2     | deletes the instance                                      |
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

create_instance_tests.py - CreateInstancePubPrivNetTests
--------------------------------------------------------

+---------------------------------------+---------------+-----------------------------------------------------------+
| Test Name                             | API Versions  | Description                                               |
+=======================================+===============+===========================================================+
| test_dual_ports_dhcp                  | Nova 2        | Ensures that a VM with two ports/NICs can have its second |
|                                       | Neutron 2     | NIC configured via SSH/Ansible after startup              |
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
