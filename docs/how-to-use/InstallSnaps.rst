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

    sudo yum -y update
    sudo yum install -y epel-release
    sudo yum install -y git gcc python-pip python-devel openssl-devel
    sudo pip install --upgrade pip

Ubuntu 14.04
------------
::

      sudo apt-get install git python2.7-dev libssl-dev python-pip
      sudo apt-get install corkscrew (optional for SSH over an HTTP proxy)

Ubuntu 16.04
------------
::

      sudo apt install python git python2.7-dev libssl-dev python-pip
      sudo apt install corkscrew (optional for SSH over an HTTP proxy)

Windows Server 2012
-------------------
::

      Install Python 2.7.x
      Install Git
      Install Microsoft Visual C++ Compiler for Python 2.7

      Cannot SSH from behind a proxy in the 'cmd' shell as corkscrew is only available for Cygwin
      Ansible functionality is not working on windows as an exception is being thrown while importing the packages

Optional: Setup a Python virtual environment
--------------------------------------------

Python 2.7 (recommend leveraging a Virtual Python runtime, e.g.
   `Virtualenv <https://virtualenv.pypa.io>`__, in your development
   environment)

Install SNAPS dependencies
--------------------------

The "pip" command below needs to be executed as root, if you are not using a virtual Python environment.

::

   git clone https://gerrit.opnfv.org/gerrit/snaps
   sudo pip install -e <path to repo>/snaps/
   (note: on CentOS 7 and Ubuntu 14.04 you may have to try the previous command several times)

SNAPS is now hosted on the Python Package Manager (PyPI).

::

   pip install snaps

This will install the stable Euphrates version.

The install should now be complete and you can start using the SNAPS-OO libraries.
