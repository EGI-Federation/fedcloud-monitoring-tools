"""Class for interaction with the accounting portal"""

import datetime
import numbers

import httpx

ACCOUNTING_DAYS = 90
ACCOUNTING_URL = "https://accounting.egi.eu/"
SITE_VO_ACCOUNTING = (
    "cloud/sum_elap_processors/SITE/VO/"
    "{start_year}/{start_month}/{end_year}/{end_month}"
    "/all/onlyinfrajobs/JSON/"
)


class Accounting:
    def __init__(self):
        self._data = {}
        self.days = ACCOUNTING_DAYS

    def _get_accounting_data(self):
        """Gets accounting data for sites / vos over the last 90 days"""
        today = datetime.date.today()
        start = today - datetime.timedelta(days=self.days)
        url = ACCOUNTING_URL + SITE_VO_ACCOUNTING.format(
            start_year=start.year,
            start_month=start.month,
            end_year=today.year,
            end_month=today.month,
        )
        # accounting generates a redirect here
        r = httpx.get(url, follow_redirects=True)
        self._data = r.json()
        return self._data

    def site_vos(self, site):
        if not self._data:
            self._get_accounting_data()
        for col in self._data:
            if col["id"] == site:
                return set(
                    [
                        vo[0]
                        for vo in col.items()
                        if isinstance(vo[1], numbers.Number)
                        and vo[1] != 0
                        and vo[0] not in ["Total", "Percent"]
                    ]
                )
        return set([])

    def all_sites(self):
        if not self._data:
            self._get_accounting_data()
        for col in self._data:
            if col["id"] == "xlegend":
                return [site[1] for site in col.items() if site[0] != "id"]
        return []

    def all_vos(self):
        if not self._data:
            self._get_accounting_data()
        for col in self._data:
            if col["id"] == "ylegend":
                return [vo for vo in col.values() if vo != 'ylegend' and vo != 'id']

    def accounting_all_vos(self):
        active_VOs = {}
        for vo in self.all_vos():
            active_VOs[vo] = {}
            for i in self._data:
                if i["id"] != 'Total' and \
                   i["id"] != 'Percent' and \
                   i["id"] != 'var' and \
                   i["id"] != 'xlegend' and \
                   i["id"] != 'ylegend' and \
                   vo in i and \
                   i[vo] is not None and \
                   float(i[vo]) > 0.0:
                   # loop over all sites having > 0 CPUh for this VO
                    site = i["id"]
                    cpuh = float(i[vo])
                    active_VOs[vo][site] = cpuh
            # it may happen that the VO doesn't have accounting after all
            if len(active_VOs[vo]) == 0:
                active_VOs.pop(vo)

        return active_VOs
