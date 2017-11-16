# Copyright (c) 2017 Cable Television Laboratories, Inc. ("CableLabs")
#                    and others.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


class ImageConfig(object):
    def __init__(self, **kwargs):
        """
        Constructor
        :param name: the image's name (required)
        :param image_user: the image's default sudo user (required)
        :param format or img_format: the image format type (required)
        :param url or download_url: the image download location (requires url
                                    or img_file)
        :param image_file: the image file location (requires url or img_file)
        :param extra_properties: dict() object containing extra parameters to
                                 pass when loading the image;
                                 can be ids of kernel and initramfs images for
                                 a 3-part image
        :param nic_config_pb_loc: the file location to the Ansible Playbook
                                  that can configure multiple NICs
        :param kernel_image_settings: the settings for a kernel image
        :param ramdisk_image_settings: the settings for a ramdisk image
        :param exists: When True, an image with the given name must exist
        :param public: When True, an image will be created with public
                       visibility
        """

        self.name = kwargs.get('name')
        self.image_user = kwargs.get('image_user')
        self.format = kwargs.get('format')
        if not self.format:
            self.format = kwargs.get('img_format')

        self.url = kwargs.get('url')
        if not self.url:
            self.url = kwargs.get('download_url')
        if self.url == 'None':
            self.url = None

        self.image_file = kwargs.get('image_file')
        if self.image_file == 'None':
            self.image_file = None

        self.extra_properties = kwargs.get('extra_properties')
        self.nic_config_pb_loc = kwargs.get('nic_config_pb_loc')

        kernel_image_settings = kwargs.get('kernel_image_settings')
        if kernel_image_settings:
            if isinstance(kernel_image_settings, dict):
                self.kernel_image_settings = ImageConfig(
                    **kernel_image_settings)
            else:
                self.kernel_image_settings = kernel_image_settings
        else:
            self.kernel_image_settings = None

        ramdisk_image_settings = kwargs.get('ramdisk_image_settings')
        if ramdisk_image_settings:
            if isinstance(ramdisk_image_settings, dict):
                self.ramdisk_image_settings = ImageConfig(
                    **ramdisk_image_settings)
            else:
                self.ramdisk_image_settings = ramdisk_image_settings
        else:
            self.ramdisk_image_settings = None

        if 'exists' in kwargs and kwargs['exists'] is True:
            self.exists = True
        else:
            self.exists = False

        if 'public' in kwargs and kwargs['public'] is True:
            self.public = True
        else:
            self.public = False

        if not self.name:
            raise ImageConfigError("The attribute name is required")

        if not (self.url or self.image_file) and not self.exists:
            raise ImageConfigError(
                'URL or image file must be set or image must already exist')

        if not self.image_user:
            raise ImageConfigError('Image user is required')

        if not self.format and not self.exists:
            raise ImageConfigError(
                'Format is required when the image should not already exist')


class ImageConfigError(Exception):
    """
    Exception to be thrown when an image settings are incorrect
    """

    def __init__(self, message):
        Exception.__init__(self, message)
