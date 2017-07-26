#!/usr/bin/env bash

set -e

sudo pip install virtualenv
virtualenv vpy
source vpy/bin/activate
pip install ansible

ansible-playbook -i "192.168.122.2," ci_tests.yaml