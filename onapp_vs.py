#!/usr/bin/python
# -*- coding: utf-8 -*-

# https://docs.onapp.com/55api/virtual-servers
# https://libcloud.readthedocs.io/en/latest/compute/drivers/onapp.html

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: onapp_vs
short_description: Manage Virtual Server (VS) in OnApp Cloud
description:
    - Manage Virtual Server (VS) in OnApp Cloud
version_added: "2.7.0.0"
options:
notes:
    -
requirements: [ "" ]
author: Alexander Dobriakov, alexander.dobriakov@jalogica.com
'''

EXAMPLES = '''
'''

RETURN = '''
original_message:
    description: The original name param that was passed in
    type: str
message:
    description: The output message that the sample module generates
'''

try:
    from libcloud.compute.types import Provider
    from libcloud.compute.providers import get_driver
    HAS_LIBCLOUD = True
except ImportError:
    HAS_LIBCLOUD = False

from ansible.module_utils.basic import AnsibleModule
import os
import ConfigParser

def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        name=dict(type='str', required=True),
        new=dict(type='bool', required=False, default=False)
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # change is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        message=''
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        return result

###begin###################
    #
    # Instantiate driver
    config = ConfigParser.SafeConfigParser()
    libcloud_default_ini_path = os.path.expanduser("~/.ansible/libcloud.ini")
    if not os.path.exists(libcloud_default_ini_path):
        module.fail_json(msg="Confguration file can't be found ~/.ansible/libcloud.ini")
    config.read(libcloud_default_ini_path)
    host = config.get('driver', 'host')
    key = config.get('driver', 'key')
    secret = config.get('driver', 'secret')
    cls = get_driver(Provider.ONAPP)
    driver = cls(
        key=key,
        secret=secret,
        host=host
    )

    #
    # Create node
    #
    name = module.params['name']  # user-friendly VS description
    memory = 512  # amount of RAM assigned to the VS in MB
    cpus = 1  # number of CPUs assigned to the VS
    cpu_shares = 100
    # For KVM hypervisor the CPU priority value is always 100. For XEN, set a
    # custom value. The default value for XEN is 1
    hostname = 'vshostname'  # set the host name for this VS
    template_id = 968  # the ID of a template from which a VS should be built
    primary_disk_size = 10  # set the disk space for this VS
    swap_disk_size = None  # set swap space

    # optional parameter, but recommended
    rate_limit = None
    # set max port speed. If none set, the system sets port speed to unlimited

# first check if already exists
    # module.fail_json(msg=map(lambda x: x.uuid, driver.list_nodes()))
    node = [n for n in driver.list_nodes() if n.name == name]
    if node:
        result['changed'] = False
        result['id'] = node.extra['id']
        result['state'] = node.extra['state']
        result['strict_virtual_machine_id'] = node.extra['strict_virtual_machine_id']
        result['message'] = 'Virtual server with this name exists already'
        module.exit_json(**result)

    node = driver.create_node(
        name=name,
        ex_memory=memory,
        ex_cpus=cpus,
        ex_cpu_shares=cpu_shares,
        ex_hostname=hostname,
        ex_template_id=template_id,
        ex_primary_disk_size=primary_disk_size,
        ex_swap_disk_size=swap_disk_size,
        ex_rate_limit=rate_limit
    )
###end###################
    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)
    result['original_message'] = module.params['name']
    result['extra'] = '; '.join(node.extra)
    result['uuid'] = node.uuid
    result['admin_note'] = node.extra['admin_note']
    result['hostname'] = node.extra['hostname']
    result['hypervisor_id'] = node.extra['hypervisor_id']
    result['id'] = node.extra['id']
    result['name'] = node.name
    result['state'] = node.extra['state']
    result['public_ips'] = node.public_ips
    result['private_ips'] = node.private_ips

    # use whatever logic you need to determine whether or not this module
    # made any modifications to your target
    if module.params['new']:
        result['changed'] = True

    # during the execution of the module, if there is an exception or a
    # conditional state that effectively causes a failure, run
    # AnsibleModule.fail_json() to pass in the message and the result
    if module.params['name'] == 'fail me':
        module.fail_json(msg='You requested this to fail', **result)

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)

def main():
    if not HAS_LIBCLOUD:
        module.fail_json(msg='This module requires apache-libcloud to work! Please install it with pip install apache-libcloud')

    run_module()

if __name__ == '__main__':
    main()
