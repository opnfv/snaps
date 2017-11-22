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

SecurityGroupRuleConfigUnitTests
--------------------------------

Ensures that all required members are included when constructing a
SecurityGroupRuleConfig object

SecurityGroupRuleSettingsUnitTests
----------------------------------

Ensures that all required members are included when constructing a
deprecated SecurityGroupRuleSettings object

SecurityGroupRuleDomainObjectTests
----------------------------------

Ensures that all required members are included when constructing a
SecurityGroupRule domain object

SecurityGroupConfigUnitTests
----------------------------

Ensures that all required members are included when constructing a
SecuirtyGroupConfig object

SecurityGroupSettingsUnitTests
------------------------------

Ensures that all required members are included when constructing a
deprecated SecuirtyGroupSettings object

SecurityGroupDomainObjectTests
------------------------------

Ensures that all required members are included when constructing a
SecurityGroup domain object

ImageConfigUnitTests
--------------------

Ensures that all required members are included when constructing a
ImageConfig object

ImageSettingsUnitTests
----------------------

Ensures that all required members are included when constructing a
ImageSettings object (deprecated see ImageConfigUnitTests)

ImageDomainObjectTests
----------------------

Ensures that all required members are included when constructing a
Image domain object

FlavorConfigUnitTests
---------------------

Ensures that all required members are included when constructing a
FlavorConfig object

FlavorSettingsUnitTests
-----------------------

Ensures that all required members are included when constructing a
deprecated FlavorSettings object

FlavorDomainObjectTests
-----------------------

Ensures that all required members are included when constructing a
Flavor domain object

KeypairConfigUnitTests
----------------------

Ensures that all required members are included when constructing a
KeypairConfig object

KeypairSettingsUnitTests
------------------------

Ensures that all required members are included when constructing a
deprecated KeypairSettings object

KeypairDomainObjectTests
------------------------

Ensures that all required members are included when constructing a
Keypair domain object

UserConfigUnitTests
-------------------

Ensures that all required members are included when constructing a
UserConfig object

UserSettingsUnitTests
---------------------

Ensures that all required members are included when constructing a
deprecated UserSettings object

UserDomainObjectTests
---------------------

Ensures that all required members are included when constructing a
User domain object

ProjectConfigUnitTests
----------------------

Ensures that all required members are included when constructing a
ProjectConfig object

ProjectSettingsUnitTests
------------------------

Ensures that all required members are included when constructing a
deprecated ProjectSettings object

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

NetworkConfigUnitTests
----------------------

Ensures that all required members are included when constructing a
NetworkConfig object

NetworkSettingsUnitTests
------------------------

Ensures that all required members are included when constructing a
deprecated NetworkSettings object

NetworkObjectTests
------------------

Ensures that all required members are included when constructing a
Network domain object

SubnetConfigUnitTests
---------------------

Ensures that all required members are included when constructing a
SubnetConfig object

SubnetSettingsUnitTests
-----------------------

Ensures that all required members are included when constructing a
deprecated SubnetSettings object

SubnetObjectTests
-----------------

Ensures that all required members are included when constructing a
Subnet domain object

PortConfigUnitTests
-------------------

Ensures that all required members are included when constructing a
PortConfig object

PortSettingsUnitTests
---------------------

Ensures that all required members are included when constructing a
deprecated PortSettings object

PortDomainObjectTests
---------------------

Ensures that all required members are included when constructing a
Port domain object

RouterConfigUnitTests
---------------------

Ensures that all required members are included when constructing a
RouterConfig object

RouterSettingsUnitTests
-----------------------

Ensures that all required members are included when constructing a
deprecated RouterSettings object

RouterDomainObjectTests
-----------------------

Ensures that all required members are included when constructing a
Router domain object

InterfaceRouterDomainObjectTests
--------------------------------

Ensures that all required members are included when constructing a
InterfaceRouter domain object

StackConfigUnitTests
--------------------

Ensures that all required members are included when constructing a
StackConfig object

StackSettingsUnitTests
----------------------

Ensures that all required members are included when constructing a
deprecated StackSettings object

StackDomainObjectTests
----------------------

Ensures that all required members are included when constructing a
Stack domain object (for Heat)

ResourceDomainObjectTests
-------------------------

Ensures that all required members are included when constructing a
Resource domain object (for Heat)

OutputDomainObjectTests
-----------------------

Ensures that all required members are included when constructing a
Output domain object (for Heat)

VolumeConfigUnitTests
---------------------

Ensures that all required members are included when constructing a
VolumeConfig object

VolumeSettingsUnitTests
-----------------------

Ensures that all required members are included when constructing a
deprecated VolumeSettings object

VolumeDomainObjectTests
-----------------------

Ensures that all required members are included when constructing a
Volume domain object (for Cinder)

VolumeTypeConfigUnitTests
-------------------------

Ensures that all required members are included when constructing a
VolumeTypeConfig object

VolumeTypeSettingsUnitTests
---------------------------

Ensures that all required members are included when constructing a
deprecated VolumeTypeSettings object

VolumeTypeDomainObjectTests
---------------------------

Ensures that all required members are included when constructing a
VolumeType domain object (for Cinder)

VolumeTypeEncryptionObjectTests
-------------------------------

Ensures that all required members are included when constructing a
VolumeTypeEncryption domain object (for Cinder)

QoSConfigUnitTests
------------------

Ensures that all required members are included when constructing a
QoSConfig object

QoSSettingsUnitTests
--------------------

Ensures that all required members are included when constructing a
deprecated QoSSettings object

QoSSpecDomainObjectTests
------------------------

Ensures that all required members are included when constructing a
QoSSpec domain object (for Cinder)

VolumeDomainObjectTests
-----------------------

Ensures that all required members are included when constructing a
Volume domain object (for Cinder)

FloatingIpConfigUnitTests
-------------------------

Ensures that all required members are included when constructing a
FloatingIpConfig object

FloatingIpSettingsUnitTests
---------------------------

Ensures that all required members are included when constructing a
depecated FloatingIpSettings object

FloatingIpDomainObjectTests
---------------------------

Ensures that all required members are included when constructing a
FloatingIp domain object

VmInstanceConfigUnitTests
-------------------------

Ensures that all required members are included when constructing a
VmInstanceConfig object

VmInstanceSettingsUnitTests
---------------------------

Ensures that all required members are included when constructing a
deprecated VmInstanceSettings object

VmInstDomainObjectTests
-----------------------

Ensures that all required members are included when constructing a
VmInst domain object

ClusterTemplateConfigUnitTests
------------------------------

Ensures that all required members are included when constructing a
ClusterTemplateConfig object

ClusterTemplateUnitTests
------------------------

Ensures that all required members are included when constructing a
ClusterTemplate object

SettingsUtilsUnitTests
----------------------

Ensures that the settings_utils.py#create_volume_config() function properly
maps a snaps.domain.Volume object correctly to a
snaps.config.volume.VolumeConfig object as well as a
snaps.domain.VolumeType object to a
snaps.config.volume.VolumeConfig object


Ensures that the settings_utils.py#create_flavor_config() function properly
maps a snaps.domain.Flavor object correctly to a
snaps.config.flavor.FlavorConfig object