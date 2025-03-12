"""Monitor VM instances running in the provider"""

import click
from fedcloud_monitoring_tools.appdb import AppDB
from fedcloud_monitoring_tools.vm_monitor import VmMonitor, VmMonitorException
from fedcloudclient.decorators import oidc_params
from fedcloudclient.sites import list_sites


@click.command()
@oidc_params
@click.option("--site", help="Restrict the monitoring to the site provided")
@click.option(
    "--vo",
    default="vo.access.egi.eu",
    help="VO name to monitor",
    show_default=True,
)
@click.option(
    "--max-days",
    default=90,
    show_default=True,
    help="Maximum number of days instances can be running for triggering deletion",
)
@click.option(
    "--delete",
    default=False,
    is_flag=True,
    help="Ask for deletion of VMs",
    show_default=True,
)
@click.option(
    "--show-quotas",
    default=True,
    help="Show quotas for VO",
    show_default=True,
)
@click.option(
    "--check-ssh",
    default=False,
    help="Check SSH version on target VMs",
    show_default=True,
)
@click.option(
    "--check-cups",
    default=False,
    help="Check whether TCP/UDP port 631 is accessible",
    show_default=True,
)
@click.option(
    "--ldap-server",
    default="ldaps://ldap.aai.egi.eu:636",
    help="LDAP server for VO membership",
    show_default=True,
)
@click.option(
    "--ldap-base-dn",
    default="ou=people,dc=ldap,dc=aai,dc=egi,dc=eu",
    help="LDAP base DN",
    show_default=True,
)
@click.option("--ldap-user", help="LDAP user")
@click.option("--ldap-password", help="LDAP password")
@click.option(
    "--ldap-search-filter",
    default="(isMemberOf=CO:COU:vo.access.egi.eu:members)",
    show_default=True,
    help="LDAP search filter",
)
def main(
    access_token,
    site,
    vo,
    max_days,
    delete,
    show_quotas,
    check_ssh,
    check_cups,
    ldap_server,
    ldap_base_dn,
    ldap_user,
    ldap_password,
    ldap_search_filter,
):
    ldap_config = {}
    if ldap_user and ldap_password:
        ldap_config.update(
            {
                "server": ldap_server,
                "username": ldap_user,
                "password": ldap_password,
                "base_dn": ldap_base_dn,
                "search_filter": ldap_search_filter,
            }
        )
    appdb = AppDB()
    appdb_sites = appdb.get_sites_for_vo(vo)
    fedcloudclient_sites = list_sites(vo)
    sites = [site] if site else set(appdb_sites + fedcloudclient_sites)
    for s in sites:
        click.secho(f"[.] Checking VO {vo} at {s}", fg="blue", bold=True)
        vm_monitor = VmMonitor(
            s, vo, access_token, max_days, check_ssh, check_cups, ldap_config
        )
        try:
            vm_monitor.vm_monitor(delete)
            if show_quotas:
                click.echo("[+] Quota information:")
                vm_monitor.show_quotas()
            vm_monitor.check_unused_floating_ips()
            vm_monitor.check_unused_security_groups()
            vm_monitor.check_unused_volumes()
        except VmMonitorException as e:
            click.echo(" ".join([click.style("ERROR:", fg="red"), str(e)]), err=True)
