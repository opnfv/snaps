SNAPS Unit Testing
==================

| Tests designated as Unit tests extend the unittest.TestCase class and
  can be exercised without any external resources
| other than the filesystem. Most of these tests simply ensure that the
  configuration settings classes check their
| constructor arguments properly.

The Test Classes
================

FileUtilsTests
--------------

-  testFileIsDirectory - ensures that the expected path is a directory
-  testFileNotExist - ensures that a file that does not exist returns
   False
-  testFileExists - ensures that a file that does exist returns True
-  testDownloadBadUrl - ensures that an Exception is thrown when
   attempting to download a file with a bad URL
-  testCirrosImageDownload - ensures that the Cirros image can be
   downloaded
-  testReadOSEnvFile - ensures that an OpenStack RC file can be properly
   parsed

ProxySettingsUnitTests
----------------------

Ensures that all required members are included when constructing a
ProxySettings object

OSCredsUnitTests
----------------

Ensures that all required members are included when constructing a
OSCreds object

SecurityGroupRuleSettingsUnitTests
----------------------------------

Ensures that all required members are included when constructing a
SecurityGroupRuleSettings object

SecurityGroupRuleDomainObjectTests
----------------------------------

Ensures that all required members are included when constructing a
SecurityGroupRule domain object

SecurityGroupSettingsUnitTests
------------------------------

Ensures that all required members are included when constructing a
SecuirtyGroupSettings object

SecurityGroupDomainObjectTests
------------------------------

Ensures that all required members are included when constructing a
SecurityGroup domain object

ImageSettingsUnitTests
----------------------

Ensures that all required members are included when constructing a
ImageSettings object

ImageDomainObjectTests
----------------------

Ensures that all required members are included when constructing a
Image domain object

FlavorSettingsUnitTests
-----------------------

Ensures that all required members are included when constructing a
FlavorSettings object

FlavorDomainObjectTests
-----------------------

Ensures that all required members are included when constructing a
Flavor domain object

KeypairSettingsUnitTests
------------------------

Ensures that all required members are included when constructing a
KeypairSettings object

KeypairDomainObjectTests
------------------------

Ensures that all required members are included when constructing a
Keypair domain object

UserSettingsUnitTests
---------------------

Ensures that all required members are included when constructing a
UserSettings object

UserDomainObjectTests
---------------------

Ensures that all required members are included when constructing a
User domain object

ProjectSettingsUnitTests
------------------------

Ensures that all required members are included when constructing a
ProjectSettings object

ProjectDomainObjectTests
------------------------

Ensures that all required members are included when constructing a
Project domain object

DomainDomainObjectTests
-----------------------

Ensures that all required members are included when constructing a
Domain domain object

ComputeQuotasDomainObjectTests
------------------------------

Ensures that all required members are included when constructing a
ComputeQuotas domain object

NetworkQuotasDomainObjectTests
------------------------------

Ensures that all required members are included when constructing a
NetworkQuotas domain object

RoleDomainObjectTests
---------------------

Ensures that all required members are included when constructing a
Role domain object

NetworkSettingsUnitTests
------------------------

Ensures that all required members are included when constructing a
NetworkSettings object

NetworkObjectTests
------------------

Ensures that all required members are included when constructing a
Network domain object

SubnetSettingsUnitTests
-----------------------

Ensures that all required members are included when constructing a
SubnetSettings object

SubnetObjectTests
-----------------

Ensures that all required members are included when constructing a
Subnet domain object

PortSettingsUnitTests
---------------------

Ensures that all required members are included when constructing a
PortSettings object

PortDomainObjectTests
---------------------

Ensures that all required members are included when constructing a
Port domain object

RouterSettingsUnitTests
-----------------------

Ensures that all required members are included when constructing a
RouterSettings object

RouterDomainObjectTests
-----------------------

Ensures that all required members are included when constructing a
Router domain object

InterfaceRouterDomainObjectTests
--------------------------------

Ensures that all required members are included when constructing a
InterfaceRouter domain object

StackSettingsUnitTests
----------------------

Ensures that all required members are included when constructing a
StackSettings object

StackDomainObjectTests
----------------------

Ensures that all required members are included when constructing a
Stack domain object

ResourceDomainObjectTests
-------------------------

Ensures that all required members are included when constructing a
Resource domain object

FloatingIpSettingsUnitTests
---------------------------

Ensures that all required members are included when constructing a
FloatingIpSettings object

FloatingIpDomainObjectTests
---------------------------

Ensures that all required members are included when constructing a
FloatingIp domain object

VmInstanceSettingsUnitTests
---------------------------

Ensures that all required members are included when constructing a
VmInstanceSettings object

VmInstDomainObjectTests
-----------------------

Ensures that all required members are included when constructing a
VmInst domain object
