"""VO-level testing for a given site in a VO"""

import io
import os
import time
from datetime import datetime, timezone

import click
import paramiko
from fabric import Connection
from imclient import IMClient

IM_REST_API = "https://im.egi.eu/im"
AUTH_FILE = "auth.dat"
MAX_NUM_CHECKS = 10


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
            output_file.write(
                "id = im; type = InfrastructureManager; token = {}\n".format(self.token)
                )
            output_file.write(
                "id = egi; type = EGI; host = {}; vo = {}; token = {}\n".format(
                    self.site, self.vo, self.token
                )
            )

    def delete_auth_file(self, filepath):
        if os.path.exists(filepath):
            os.remove(filepath)

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

    def launch_test_vm(self, ssh_command):
        # deploy VM
        tosca_template = self.create_vm_tosca_template()
        self.create_auth_file(AUTH_FILE)
        auth = IMClient.read_auth_data(AUTH_FILE)
        imclient = IMClient.init_client(IM_REST_API, auth)
        click.echo("[+] Creating test VM...")
        success, inf_id = imclient.create(tosca_template, desc_type="yaml")
        if not success:
            raise VOTestException(inf_id)
        click.echo(f"[+] Test VM successfully created with ID {inf_id}")
        # wait for VM to be ready
        state = "pending"
        attempts = 1
        while state != "configured" and attempts <= MAX_NUM_CHECKS:
            click.echo(
                f"[+] Waiting for test VM to be ready. Current state is: {state}. Attempt: {attempts}/{MAX_NUM_CHECKS}"
            )
            time.sleep(10)
            success, state = imclient.getvminfo(inf_id, 0, prop="state")
            attempts += 1
        # has the VM been configured?
        if state != "configured":
            click.secho(
                f"Test VM could not be configured after {attempts} attempts, reported state is: {state}",
                fg="red",
                bold=True,
            )
            success, state = imclient.getvminfo(inf_id, 0, prop="contmsg")
            click.echo(f"Further information about the VM: {state}")
            self.destroy_test_vm(inf_id)
            return False

        click.echo(
            f"[+] Test VM is now {state}. Waiting for 1 additional minute before testing the VM."
        )
        time.sleep(60)
        # run SSH command inside the VM
        success, outputs = imclient.get_infra_property(inf_id, "outputs")
        if not success:
            raise VOTestException(f"{success} {outputs}")
        ssh_host = outputs["node_ip"]
        ssh_user = outputs["node_creds"]["user"]
        ssh_pkey = outputs["node_creds"]["token"]
        # xref: https://stackoverflow.com/a/41862308
        pkey_io = io.StringIO()
        pkey_io.write(ssh_pkey)
        pkey_io.seek(0)
        ssh_rsa_key = paramiko.RSAKey.from_private_key(pkey_io)
        try:
            c = Connection(
                host=ssh_host, user=ssh_user, connect_kwargs={"pkey": ssh_rsa_key}
            )
            result = c.run(ssh_command, hide=True)
            if result.ok:
                click.secho(
                    f"[+] Command '{result.command}' sucessfully executed with output: {result.stdout}",
                    fg="green",
                    bold=True,
                )
            else:
                click.secho(
                    f"[-] Command '{result.command}' failed with output: {result.stderr}",
                    fg="red",
                    bold=True,
                )
        except Exception as e:
            click.echo(" ".join([click.style("ERROR:", fg="red"), str(e)]), err=True)
            success, state = imclient.getvminfo(inf_id, 0, prop="contmsg")
            click.echo(f"Further information about the VM: {state}")
        finally:
            # clean up
            self.destroy_test_vm(inf_id)
        return True

    def destroy_test_vm(self, inf_id):
        self.create_auth_file(AUTH_FILE)
        auth = IMClient.read_auth_data(AUTH_FILE)
        imclient = IMClient.init_client(IM_REST_API, auth)
        success, err = imclient.destroy(inf_id)
        if not success:
            raise VOTestException(err)
        click.echo(f"[+] Test VM successfully deleted with ID {inf_id}")
        self.delete_auth_file(AUTH_FILE)
