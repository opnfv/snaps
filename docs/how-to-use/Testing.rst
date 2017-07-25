Running Unit Test Suite
=======================

Execute the tests
-----------------

::

    cd <path to repo>
    python snaps/test_runner.py -e <path to RC file> -n <external network name>

| \* All Supported Arguments
| \* -e [required - The path to the OpenStack RC file]
| \* -n [required - The name of the external network to use for routers
  and floating IPs]
| \* -p [optional - the proxy settings if required. Format :
| \* -s [optional - the proxy command used for SSH connections]
| \* -l [(default INFO) The log level]
| \* -u [optional - When set, the unit tests will be executed]
| \* -st [optional - When set, the staging tests will be executed]
| \* -c [optional - When set, the connection tests will be executed]
| \* -a [optional - When set, the API tests will be executed]
| \* -i [optional - When set, the integration tests will be executed]
| \* -k [optional - When set, tests project and user creation. Use only
  if host running tests has access to the cloud's admin network]
| \* -f [optional - When set, will execute tests requiring Floating
  IPS]
| \* -im [optional - File containing image endpoints to override
| \* -fm [optional - JSON string containing a dict() for flavor metadata default='{\"hw:mem_page_size\": \"any\"}']
| \* -ci [optional - runs the tests required by SNAPS-OO CI]
| \* -r [optional with default value of '1' - The number of test iterations to execute]
