#!/usr/bin/env bash

set -e

# Setup Python runtime
sudo pip install virtualenv
virtualenv ./vpy
source ./vpy/bin/activate
pip install -chttps://git.openstack.org/cgit/openstack/requirements/plain/upper-constraints.txt?h=stable/pike -e ../

# $1 is the IP to the pod's build server
# $2 is the IP to the pod's control server

# This operation installs squid on the pod's build server
ansible-playbook -i ${1}, setup_proxy.yaml

# Get RC file from control server
filename=$(ssh -o StrictHostKeyChecking=no root@${2} find /var/lib/lxc/controller00_nova_api_placement_container-* -name openrc)
scp root@${2}:${filename} .

# Execute tests
python ../snaps/test_runner.py -e openrc -n public -ci -p ${1}:3128

# Cleanup virtual python runtime
rm -rf ./vpy
