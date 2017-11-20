import logging

from snaps.config.vm_inst import VmInstanceConfig

logging.basicConfig(level=logging.INFO)

# Credentials
from snaps.openstack.os_credentials import OSCreds, ProxySettings


proxy_settings = ProxySettings(
    host='10.197.123.27', port='3128',
    ssh_proxy_cmd='/usr/local/bin/corkscrew 10.197.123.27 3128 %h %p')

os_creds = OSCreds(
    username='admin', password='cable123',
    auth_url='http://192.168.67.10:5000/v2.0/', project_name='admin',
    proxy_settings=proxy_settings)


# Images
from snaps.openstack.create_image import OpenStackImage
from snaps.config.image import ImageConfig

image_settings = ImageConfig(name='cirros-test', image_user='cirros', img_format='qcow2',
                             url='http://download.cirros-cloud.net/0.3.4/cirros-0.3.4-x86_64-disk.img')

image = OpenStackImage(os_creds, image_settings)
image.create()
# See in Horizon


# Network
from snaps.config.network import NetworkConfig, SubnetConfig
from snaps.openstack.create_network import OpenStackNetwork

subnet_settings = SubnetConfig(name='test-subnet', cidr='10.0.0.1/24')
network_settings = NetworkConfig(
    name='test-net', subnet_settings=[subnet_settings])
network = OpenStackNetwork(os_creds, network_settings)
network.create()


# Flavors
from snaps.config.flavor import FlavorConfig
from snaps.openstack.create_flavor import OpenStackFlavor

flavor_settings = FlavorConfig(name='test-flavor', ram=256, disk=10, vcpus=2)
flavor = OpenStackFlavor(os_creds, flavor_settings)
flavor.create()

# Instances
from snaps.config.network import PortConfig
from snaps.openstack.create_instance import OpenStackVmInstance

port_settings = PortConfig(
    name='test-port', network_name=network_settings.name)
instance_settings = VmInstanceConfig(
    name='test-inst', flavor=flavor_settings.name,
    port_settings=[port_settings])

vm_inst = OpenStackVmInstance(os_creds, instance_settings, image_settings)
vm_inst.create(block=True)

# Cleanup
vm_inst.clean()
flavor.clean()
network.clean()
image.clean()
