# Python scripts for creating virtual environments on OpenStack with Ansible playbooks for provisioning.

## Runtime Environment Setup
  * Python 2.7 (recommend leveraging a Virtual Python runtime, e.g. [Virtualenv](https://virtualenv.pypa.io), in your development environment)
  * Development packages for python and openssl. On CentOS/RHEL:

      \# yum install python-devel openssl-devel

  On Ubuntu:

      \# apt-get install python2.7-dev libssl-dev
  * Install SNAPS Library
    * pip install -e &lt;path to repo>/snaps/

## [Testing](Testing.md)
## [Virtual Environment Deployment](VirtEnvDeploy.md)

Also see the [CableLabs project wiki page](https://community.cablelabs.com/wiki/display/SNAPS/OpenStack+Instantiation%2C+Provisioning%2C+and+Testing)
for more information on these scripts.
