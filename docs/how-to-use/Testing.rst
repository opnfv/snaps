Running Unit Test Suite
=======================

Execute the tests
-----------------

::

cd <path to repo>
python snaps/unit_test_suite.py -e <path to RC file> -n <external network name>

| \* All Supported Arguments
| \* -e [required - The path to the OpenStack RC file]
| \* -n [required - The name of the external network to use for routers
  and floating IPs]
| \* -p [optional - the proxy settings if required. Format :
| \* -s [optional - the proxy command used for SSH connections]
| \* -l [(default INFO) The log level]
| \* -k [optional - When set, tests project and user creation. Use only
  if host running tests has access to the cloud's admin network]
| \* -f [optional - When set, will not execute tests requiring Floating
  IPS]
| \* -u [optional - When set, the unit tests will be executed]
