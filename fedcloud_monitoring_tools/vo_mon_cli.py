"""VO-level testing"""

import click
from fedcloud_monitoring_tools.appdb import AppDB
from fedcloud_monitoring_tools.vo_mon import VOTest, VOTestException
from fedcloudclient.decorators import oidc_params
from fedcloudclient.sites import list_sites

@click.command()
@oidc_params
@click.option("--site", help="Restrict the testing to the site provided")
@click.option(
    "--vo",
    default="vo.access.egi.eu",
    help="VO name to test",
    show_default=True,
)
def main(site, vo, access_token):
    # gather all sites in a given VO
    appdb = AppDB(vo)
    appdb_sites = appdb.get_sites_for_vo()
    fedcloudclient_sites = list_sites(vo)
    sites = [site] if site else set(appdb_sites + fedcloudclient_sites)
    for s in sites:
        click.secho(f"[.] Testing VO {vo} at {s}", fg="blue", bold=True)
        try:
            vo_test = VOTest(vo, site, access_token)
            vo_test.launch_test_vm()

        except VOTestException as e:
            click.echo(" ".join([click.style("ERROR:", fg="red"), str(e)]), err=True)
