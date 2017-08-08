import logging
logging.basicConfig(level=logging.INFO)

# Credentials
from snaps.openstack.os_credentials import OSCreds, ProxySettings


proxy_settings = ProxySettings(host='10.197.123.27', port='3128',
                               ssh_proxy_cmd='/usr/local/bin/corkscrew 10.197.123.27 3128 %h %p')

os_creds = OSCreds(username='admin', password='cable123', auth_url='http://192.168.67.10:5000/v2.0/',
                   project_name='admin', proxy_settings=proxy_settings)


# Images
from snaps.openstack.create_image import ImageSettings, OpenStackImage

image_settings = ImageSettings(name='cirros-test', image_user='cirros', img_format='qcow2',
                               url='http://download.cirros-cloud.net/0.3.4/cirros-0.3.4-x86_64-disk.img')

image = OpenStackImage(os_creds, image_settings)
image.create()
# See in Horizon


# Network
from snaps.openstack.create_network import NetworkSettings, SubnetSettings, OpenStackNetwork

subnet_settings = SubnetSettings(name='test-subnet', cidr='10.0.0.1/24')
network_settings = NetworkSettings(name='test-net', subnet_settings=[subnet_settings])
network = OpenStackNetwork(os_creds, network_settings)
network.create()


# Flavors
from snaps.openstack.create_flavor import FlavorSettings, OpenStackFlavor

flavor_settings = FlavorSettings(name='test-flavor', ram=256, disk=10, vcpus=2)
flavor = OpenStackFlavor(os_creds, flavor_settings)
flavor.create()

# Instances
from snaps.openstack.create_network import PortSettings
from snaps.openstack.create_instance import VmInstanceSettings, OpenStackVmInstance

port_settings = PortSettings(name='test-port', network_name=network_settings.name)
instance_settings = VmInstanceSettings(name='test-inst', flavor=flavor_settings.name, port_settings=[port_settings])

vm_inst = OpenStackVmInstance(os_creds, instance_settings, image_settings)
vm_inst.create(block=True)

# Cleanup
vm_inst.clean()
flavor.clean()
network.clean()
image.clean()
