"""FedCloud Information System queries"""

import requests


class FedCloudIS:
    def __init__(self):
        self.sites = {}

    def get_sites_for_vo(self, vo):
        query = f"https://is.cloud.egi.eu/sites/?vo_name={vo}"
        r = requests.get(query)
        r.raise_for_status()
        data = r.json()
        return [site["name"] for site in data]

    def vo_check(self, site, vo):
        if not self.sites:
            self.sites = self.get_sites_for_vo(vo)
        return site in self.sites

    def get_vo_for_site(self, site):
        try:
            query = f"https://is.cloud.egi.eu/site/{site}/projects"
            r = requests.get(query)
            r.raise_for_status()
        except requests.exceptions.HTTPError:
            return []
        data = r.json()
        if data:
            return [vo["name"] for vo in data]
        else:
            return []

    def all_vos(self):
        query = "https://is.cloud.egi.eu/vos/"
        r = requests.get(query)
        r.raise_for_status()
        return r.json()
