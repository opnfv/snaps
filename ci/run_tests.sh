#!/usr/bin/env bash

git clone https://gerrit.opnfv.org/gerrit/snaps
sudo pip install virtualenv

virtualenv vpy
source vpy/bin/activate
pip install ansible

ansible-playbook -i "192.168.122.2," ci_tests.yaml