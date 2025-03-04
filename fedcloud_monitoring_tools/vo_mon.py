"""VO-level testing for a given site in a VO"""

import ipaddress
import subprocess
from collections import defaultdict
from datetime import datetime, timezone

import click
import ldap3
import paramiko
from dateutil.parser import parse
from fedcloudclient.openstack import fedcloud_openstack
from fedcloudclient.sites import find_endpoint_and_project_id
from ldap3.core.exceptions import LDAPException
from paramiko import SSHException

from imclient import IMClient
import time
import os

IM_REST_API = "https://im.egi.eu/im"
AUTH_FILE = "auth.dat"

class VOTestException(Exception):
    pass


class VOTest:
    """Helper class to call im-client easily"""

    def __init__(self, vo, site, token):
        self.vo = vo
        self.site = site
        self.token = token
        self.now = datetime.now(timezone.utc)

    def create_auth_file(self, filepath):
        with open(filepath, "w") as output_file:
            output_file.write("id = im; type = InfrastructureManager; token = \"{}\"\n".format(self.token))
            output_file.write("id = egi; type = EGI; host = {}; vo = {}; token = \"{}\"\n".format(self.site, self.vo, self.token))

    def delete_auth_file(self, filepath):
        if os.path.exists(filepath): os.remove(filepath)

    def create_vm_tosca_template(self):
        inf_desc = """
            tosca_definitions_version: tosca_simple_yaml_1_0
            
            imports:
            - grycap_custom_types: https://raw.githubusercontent.com/grycap/tosca/main/custom_types.yaml
            
            topology_template:
              node_templates:
                simple_node:
                  type: tosca.nodes.indigo.Compute
                  capabilities:
                    endpoint:
                      properties:
                        network_name: PUBLIC
                    host:
                      properties:
                        num_cpus: 2
                        mem_size: 4 GB
                    os:
                      properties:
                        image: appdb://SITE/egi.ubuntu.24.04?VO
              outputs:
                node_ip:
                  value: { get_attribute: [ simple_node, public_address, 0 ] }
                node_creds:
                  value: { get_attribute: [ simple_node, endpoint, credential, 0 ] }
        """
        return inf_desc.replace("SITE", self.site).replace("VO", self.vo)

    def launch_test_vm(self):
        self.create_auth_file(AUTH_FILE)
        tosca_template = self.create_vm_tosca_template()
        auth = IMClient.read_auth_data(AUTH_FILE)
        imclient = IMClient.init_client(IM_REST_API, auth)
        click.echo(f"[+] Creating test VM...")
        success, inf_id = imclient.create(tosca_template, desc_type="yaml")
        if not success:
            raise VOTestException(inf_id)
        click.echo(f"[+] Test VM successfully created with ID {inf_id}")
        state = "pending"
        while state != "configured":
            click.echo(f"[+] Waiting for test VM to be ready...")
            time.sleep(10)
            success, state = imclient.getvminfo(inf_id, 0, prop='state')
        click.echo(f"[+] Waiting for test VM to be ready...")
        time.sleep(30)
#        click.echo(f"[+] Waiting for test VM to be ready...")
#        success, info = imclient._wait()
#        click.echo(f"[+] IM: {success}, {inf_id}")
        # TODO: need to ssh into VM here
        success, err = imclient.destroy(inf_id)
        if not success:
            raise VOTestException(err)
        click.echo(f"[+] Test VM successfully deleted with ID {inf_id}")
        self.delete_auth_file(AUTH_FILE)
