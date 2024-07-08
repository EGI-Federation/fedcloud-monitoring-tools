"""Monitor VM instances running in the provider"""

import click
from fedcloud_vm_monitoring.appdb import AppDB
from fedcloud_vm_monitoring.site_monitor import SiteMonitor, SiteMonitorException
from fedcloudclient.decorators import oidc_params
from fedcloudclient.sites import list_sites
from fedcloudclient.sites import find_endpoint_and_project_id


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
    appdb = AppDB(vo)
    appdb_sites = appdb.get_sites_for_vo()
    fedcloudclient_sites = list_sites(vo)
    sites = [site] if site else set(appdb_sites + fedcloudclient_sites)
    for s in sites:
        click.secho(f"[.] Checking VO {vo} at {s}", fg="blue", bold=True)
        site_monitor = SiteMonitor(s, vo, access_token, max_days, ldap_config)
        try:
            site_monitor.vm_monitor(delete)
        except SiteMonitorException as e:
            click.echo(" ".join([click.style("ERROR:", fg="red"), str(e)]), err=True)
        if show_quotas:
            click.echo("[+] Quota information:")
            site_monitor.show_quotas()
        # TODO: volumes, ips, should look for those older than X days
        #       and not attached to any VM for deletion
        # site_monitor.vol_monitor()
        # site_monitor.ip_monitor()
