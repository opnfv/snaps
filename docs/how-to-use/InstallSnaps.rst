****************
Installing SNAPS
****************


Install Dependencies
====================
A few packages need to installed onto your system, before you can install SNAPS.

Git is used to download the snaps source from the OPNFV Gerrit repository.

Python, GCC and additional libraries are required to compile and install the packages used by SNAPS.  These
dependencies need to be installed whether or not a virtual Python environment is used.

Note: SNAPS-OO works best under Python 2.7; however, all of the code except in snaps.openstack.provisioning.ansible
should work properly within a Python 3.4.4 runtime. Ansible support will not work in any Python 3.x when the Ansible
version is 2.3.0 or prior. No indications when this support will be added as of 5 May 2017.

CentOS 7
--------

::

    sudo yum install -7 git gcc python-pip python-devel openssl-devel

Ubuntu
------
::

      sudo apt-get install git python2.7-dev libssl-dev

Optional: Setup a Python virtual environment
--------------------------------------------

Python 2.7 (recommend leveraging a Virtual Python runtime, e.g.
   `Virtualenv <https://virtualenv.pypa.io>`__, in your development
   environment)

Install SNAPS dependencies
--------------------------

The "pip" command below needs to be executed as root, if you are not using a virtual Python environment.

::

   sudo pip install -e <path to repo>/snaps/

The install should now be complete and you can start using the SNAPS-OO libraries.
