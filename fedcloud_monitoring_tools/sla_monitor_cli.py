"""Monitor Accounting status"""

import importlib

import click
import yaml
from fedcloud_monitoring_tools.accounting import Accounting
from fedcloud_monitoring_tools.appdb import AppDB
from fedcloud_monitoring_tools.goc import GOCDB
from fedcloud_monitoring_tools.operations_portal import OpsPortal
from fedcloudclient.sites import list_sites


def check_site_slas(site, acct, appdb, goc, gocdb_sites):
    sla_vos = set()
    appdb_vos = set(appdb.get_vo_for_site(site))
    click.secho(f"[-] Checking site {site}", fg="blue", bold=True)
    if site not in gocdb_sites:
        click.echo(f"[I] {site} is not present in any SLA")
    else:
        for sla_name, sla in gocdb_sites[site].items():
            click.echo(f"Information for SLA {sla_name}")
            sla_vos = sla_vos.union(sla["vos"])
            accounted_vos = sla["vos"].intersection(acct.site_vos(site))
            if accounted_vos:
                click.echo(
                    f"[OK] {site} has accounting info for SLA {sla_name} ({accounted_vos})"
                )
            else:
                click.echo(f"[ERR] {site} has no accounting info for SLA {sla_name}")
            info_vos = sla["vos"].intersection(appdb_vos)
            if info_vos:
                click.echo(f"[OK] {site} has configured {info_vos} for SLA {sla_name}")
            else:
                click.echo(f"[ERR] {site} has no configured VO for SLA {sla_name}")
            click.echo()
    click.secho(f"[-] Checking aditional VOs at {site}", fg="yellow", bold=True)
    # Now check which VOs are being reported without a SLA
    if not sla_vos:
        sla_vos = goc.sla_vos
    non_sla_vos = acct.site_vos(site) - sla_vos.union(set(["ops"]))
    if non_sla_vos:
        click.echo(
            f"[W] {site} has accounting for VOs {non_sla_vos} but not covered by SLA"
        )
    if "ops" not in acct.site_vos(site):
        click.echo(f"[W] {site} has no accounting for ops")
    non_sla_appdb_vos = appdb_vos - sla_vos.union(set(["ops"]))
    if non_sla_vos:
        click.echo(
            f"[W] {site} has VOs {non_sla_appdb_vos} configured but not covered by SLA"
        )
    if "ops" not in appdb_vos:
        click.echo(f"[W] {site} has no configuration for ops")
    click.echo()


def vo_in_map(vo, vo_map):
    flat_list = []
    for i in vo_map.values():
        if i is not None:
            flat_list += i
    return vo in flat_list


def check_vo_sla(acct, appdb, goc, ops_portal, user_cert, vo_map, vo):
    if not vo_in_map(vo, vo_map):
        click.secho(
            "[ERR] VO {} not found in the map file provided".format(vo),
            fg="red",
            bold=True,
        )
        return
    all_vos_acct = acct.accounting_all_vos()
    if vo not in all_vos_acct:
        click.secho(
            "[ERR] VO {} not found in Accounting Portal".format(vo), fg="red", bold=True
        )
        return
    all_vos_ops_portal = ops_portal.get_vo_list()
    if vo not in all_vos_ops_portal:
        click.secho(
            "[ERR] VO {} not found in Operations Portal".format(vo), fg="red", bold=True
        )
        return
    all_vos_gocdb = goc.get_sites_vo(user_cert, vo_map)
    if vo not in all_vos_gocdb:
        click.secho("[ERR] VO {} not found in GOCDB".format(vo), fg="red", bold=True)
        return
    sites_gocdb = sorted(all_vos_gocdb[vo])
    sites_acct = sorted([provider for provider in all_vos_acct[vo]])
    sites_appdb = sorted(appdb.get_sites_for_vo(vo))
    sites_fedcloudclient = sorted(list_sites(vo))
    if sites_gocdb == sites_appdb == sites_acct == sites_fedcloudclient:
        click.secho(
            "[OK] VO {}. The sites supporting the VO are: {}".format(vo, sites_gocdb),
            fg="green",
            bold=True,
        )
    elif "sla-group-with-multiple-vos" in sites_gocdb and sites_appdb == sites_acct == sites_fedcloudclient:
        click.secho(
            "[OK] VO {}. The sites supporting the VO are: {}".format(vo, sites_appdb),
            fg="green",
            bold=True,
        )

    else:
        click.secho(
            "[W] VO {}. Uncertain list of sites supporting the VO!".format(vo),
            fg="yellow",
            bold=True,
        )
        click.echo("Sites in GOCDB: {}".format(sites_gocdb))
        click.echo("Sites in AppDB: {}".format(sites_appdb))
        click.echo("Sites in Accounting Portal: {}".format(sites_acct))
        click.echo("Sites in fedcloudclient: {}".format(sites_fedcloudclient))
    click.echo("Accounting data per provider in the last {} days:".format(acct.days))
    for provider in all_vos_acct[vo]:
        click.echo("Site: {}, CPUh: {}".format(provider, all_vos_acct[vo][provider]))
    click.echo()


@click.command()
@click.option("--site", help="Site to check")
@click.option("--vo", help="Monitor SLAs per VO")
@click.option("--user-cert", required=True, help="User certificate (for GOCDB queries)")
@click.option("--vo-map-file", help="SLA-VO mapping file")
def main(
    site,
    vo,
    user_cert,
    vo_map_file,
):
    if vo_map_file:
        with open(vo_map_file) as f:
            vo_map_src = f.read()
    else:
        vo_map_src = importlib.resources.read_text(
            "fedcloud_monitoring_tools.data", "vos.yaml"
        )
    vo_map = yaml.load(vo_map_src, Loader=yaml.SafeLoader)
    acct = Accounting()
    goc = GOCDB()
    appdb = AppDB()
    ops_portal = OpsPortal()

    if vo:
        check_vo_sla(acct, appdb, goc, ops_portal, user_cert, vo_map, vo)
    else:
        gocdb_sites = goc.get_sites_slas(user_cert, vo_map)
        if site:
            check_site_slas(site, acct, appdb, goc, gocdb_sites)
        else:
            for site in acct.all_sites():
                check_site_slas(site, acct, appdb, goc, gocdb_sites)
