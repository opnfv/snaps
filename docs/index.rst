Python scripts for creating virtual environments on OpenStack with Ansible playbooks for provisioning.
======================================================================================================

Runtime Environment Setup
-------------------------

-  Python 2.7 (recommend leveraging a Virtual Python runtime, e.g.
   `Virtualenv <https://virtualenv.pypa.io>`__, in your development
   environment)
-  Development packages for python and openssl. On CentOS/RHEL:

   # yum install python-devel openssl-devel

On Ubuntu:

::

      # apt-get install python2.7-dev libssl-dev

-  Install SNAPS Library

   -  pip install -e <path to repo>/snaps/

`Testing <Testing.rst>`__
-------------------------

`Virtual Environment Deployment <VirtEnvDeploy.rst>`__
------------------------------------------------------
