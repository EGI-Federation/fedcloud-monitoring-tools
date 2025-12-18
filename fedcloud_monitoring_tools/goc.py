"""Classes to interact with the GOCDB"""

import re
from xml.parsers.expat import ExpatError

import httpx
import xmltodict

GOC_PUBLIC_URL = "https://goc.egi.eu/gocdbpi/public/"
GOC_PRIVATE_URL = "https://goc.egi.eu/gocdbpi/private/"
SERVICE_TYPES = ["org.openstack.nova"]
SLA_GROUP_RE = r"EGI_(.*)_SLA"


class GOCDB:
    def __init__(self):
        self._cache = {}
        self.queries = 0
        self.sla_vos = set()

    def get_sla_groups(self, cert_file, scope="EGI,SLA"):
        client = httpx.Client(cert=cert_file)
        params = {"method": "get_service_group", "scope": scope}
        response = client.get(GOC_PRIVATE_URL, params=params)
        self.queries += 1
        try:
            groups = xmltodict.parse(response.text)["results"]["SERVICE_GROUP"]
        except ExpatError:
            print(f"\nXML to be parsed:\n{response.text}\n")
            exit("Cannot parse XML received from GOCDB.")
        return groups

    def flatten_vo_map(self, vo_map):
        all_vos = []
        for vo in vo_map.values():
            if vo:
                all_vos.extend(vo)
        return set(all_vos)

    def get_sites_vo(self, cert_file, vo_map):
        groups = self.get_sla_groups(cert_file)
        self.sla_vos = self.flatten_vo_map(vo_map)

        sites_per_vo = {}
        for group in groups:
            m = re.search(SLA_GROUP_RE, group["NAME"])
            if not m:
                continue
            sla_name = m.group(1)
            vos = vo_map.get(sla_name)
            if vos is not None and len(vos) != 1:
                # SLA service groups in GOCDB with multiple VOs are special.
                # All nova endpoints in the service group do not support all VOs.
                # Therefore, a special value is added to be treated accordingly.
                for vo in vos:
                    sites_per_vo[vo] = ["sla-group-with-multiple-vos"]
                continue
            elif vos is None:
                # This SLA service group does not have a VO associated, skipping
                continue
            # from this point on, there will be only one VO in the SLA service group in GOCDB
            # in these cases we can extract the list of providers supporting the VO properly
            sla_vo = vos[0]
            endpoints = group.get("SERVICE_ENDPOINT", [])
            if not isinstance(endpoints, list):
                endpoints = [endpoints]
            sites_per_vo[sla_vo] = []
            for endpoint in endpoints:
                svc = self.get_endpoint_site(endpoint)
                if svc:
                    site = svc["SITENAME"]
                    sites_per_vo[sla_vo].append(site)
        return sites_per_vo

    def get_sites_slas(self, cert_file, vo_map):
        groups = self.get_sla_groups(cert_file)
        self.sla_vos = self.flatten_vo_map(vo_map)

        sites = {}
        for group in groups:
            m = re.search(SLA_GROUP_RE, group["NAME"])
            if not m:
                continue
            sla_name = m.group(1)
            vos = vo_map.get(sla_name)
            endpoints = group.get("SERVICE_ENDPOINT", [])
            if not isinstance(endpoints, list):
                endpoints = [endpoints]
            for endpoint in endpoints:
                svc = self.get_endpoint_site(endpoint)
                if svc:
                    site = svc["SITENAME"]
                    site_info = sites.get("site", dict())
                    site_info[sla_name] = {"vos": set(vos or [])}
                    if site in sites:
                        sites[site].update(site_info)
                    else:
                        sites[site] = site_info
        return sites

    def get_endpoint_site(self, endpoint):
        key = endpoint["@PRIMARY_KEY"]
        service = {}
        if key in self._cache:
            return self._cache[key]
        if endpoint.get("SERVICE_TYPE", "") not in SERVICE_TYPES:
            return None
        params = {"method": "get_service"}
        if "HOSTNAME" in endpoint:
            params["hostname"] = endpoint["HOSTNAME"]
        if "SERVICE_TYPE" in endpoint:
            params["service_type"] = endpoint["SERVICE_TYPE"]
        r = httpx.get(GOC_PUBLIC_URL, params=params)
        self.queries += 1
        if r.text:
            results = xmltodict.parse(r.text).get("results", {})
            if results:
                service = results.get("SERVICE_ENDPOINT", {})
        if service:
            self._cache[key] = service
        return service
