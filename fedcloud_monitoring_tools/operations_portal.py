"""Operations Portal queries"""

import requests


class OpsPortal:
    def __init__(self):
        self.vo_list = []

    def get_vo_list(self):
        if len(self.vo_list) == 0:
            r = requests.get(
                "http://cclavoisier01.in2p3.fr:8080/lavoisier/VoList?accept=json"
            )
            r.raise_for_status()
            self.vo_list = [vo["name"] for vo in r.json()["data"]]
        return self.vo_list
