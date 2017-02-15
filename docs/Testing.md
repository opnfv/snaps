# Running Unit Test Suite
These tests are written in Python and require an that it is setup before running the tests.
See [install directions](index.md) for Python installation instructions.

## Start by cloning the snaps-provisioning repository

  ```
  git clone https://gerrit.cablelabs.com/snaps-provisioning
  ```

## Install Library

  ```
  pip install -e <path to repo>/
  ```


## Execute the tests

  ```
  cd <path to repo>
  python snaps/unit_test_suite.py -e [path to RC file] -n [external network name]
  ```
    * All Supported Arguments
      * -e [required - The path to the OpenStack RC file]
      * -n [required - The name of the external network to use for routers and floating IPs]
      * -p [optional - the proxy settings if required. Format <host>:<port>
      * -s [optional - the proxy command used for SSH connections]
      * -l [(default INFO) The log level]
      * -k [optional - When set, tests project and user creation. Use only if host running tests has access to the cloud's admin network]
      * -f [optional - When set, will not execute tests requiring Floating IPS]
      * -u [optional - When set, the unit tests will be executed]

# Test descriptions
## [Unit Testing] (UnitTests.md) - Tests that do not require a connection to OpenStack
## [OpenStack API Tests] (APITests.md) - Tests many individual OpenStack API calls
## [Integration Tests] (IntegrationTests.md) - Tests OpenStack object creation in a context. These tests will be run within a custom project as a specific user.
