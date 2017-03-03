****************
Installing SNAPS
****************


Install Dependencies
====================
A few packages need to installed onto your system, before you can install SNAPS.

Git is used to download the snaps source from the OPNFV Gerrit repository.

Python, GCC and additional libraries are required to compile and install the packages used by SNAPS.  These
dependencies need to be installed whether or not a virtual Python environment is used.

CentOS 7
--------

::

    # yum install -7 git gcc python-pip python-devel openssl-devel

Ubuntu
------
::

      # apt-get install git python2.7-dev libssl-dev

Optional: Setup a Python virtual environment
--------------------------------------------

Python 2.7 (recommend leveraging a Virtual Python runtime, e.g.
   `Virtualenv <https://virtualenv.pypa.io>`__, in your development
   environment)

Install SNAPS dependencies
--------------------------

The "pip" command below needs to be executed as root, if you are not using a virtual Python environment.

::

   #  pip install -e <path to repo>/snaps/

The install should now be complete and you can start using the SNAPS-OO libraries.
