# SNAPS Unit Testing

Tests designated as Unit tests extend the unittest.TestCase class and can be exercised without any external resources
other than the filesystem. Most of these tests simply ensure that the configuration settings classes check their
constructor arguments properly.

# The Test Classes

## FileUtilsTests
* testFileIsDirectory - ensures that the expected path is a directory
* testFileNotExist - ensures that a file that does not exist returns False
* testFileExists - ensures that a file that does exist returns True
* testDownloadBadUrl - ensures that an Exception is thrown when attempting to download a file with a bad URL
* testCirrosImageDownload - ensures that the Cirros image can be downloaded
* testReadOSEnvFile - ensures that an OpenStack RC file can be properly parsed

## SecurityGroupRuleSettingsUnitTests
Ensures that all required members are included when constructing a SecurityGroupRuleSettings object

## SecurityGroupSettingsUnitTests
Ensures that all required members are included when constructing a SecuirtyGroupSettings object

## ImageSettingsUnitTests
Ensures that all required members are included when constructing a ImageSettings object

## KeypairSettingsUnitTests
Ensures that all required members are included when constructing a KeypairSettings object

## UserSettingsUnitTests
Ensures that all required members are included when constructing a UserSettings object

## ProjectSettingsUnitTests
Ensures that all required members are included when constructing a ProjectSettings object

## NetworkSettingsUnitTests
Ensures that all required members are included when constructing a NetworkSettings object

## SubnetSettingsUnitTests
Ensures that all required members are included when constructing a SubnetSettings object

## PortSettingsUnitTests
Ensures that all required members are included when constructing a PortSettings object

## FloatingIpSettingsUnitTests
Ensures that all required members are included when constructing a FloatingIpSettings object

## VmInstanceSettingsUnitTests
Ensures that all required members are included when constructing a VmInstanceSettings object
