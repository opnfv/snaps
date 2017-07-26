#!/usr/bin/env bash

scp 192.168.122.3:$(ssh -o StrictHostKeyChecking=no 192.168.122.3 find /var/lib/lxc/controller00_nova_api_placement_container-* -name openrc) ~