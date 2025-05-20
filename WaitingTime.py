import requests

class WaitingTimeClient:
    RESIDENT_URL = 'https://secure1.info.gov.hk/immd/mobileapps/2bb9ae17/data/CPQueueTimeR.json'
    VISITOR_URL  = 'https://secure1.info.gov.hk/immd/mobileapps/2bb9ae17/data/CPQueueTimeV.json'

    headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
    }

    def __init__(self):
        self._resident_raw = None
        self._visitor_raw  = None

    def _fetch(self, url):
        try:
            print(f"🌐 Fetching from {url}")
            response = requests.get(url, headers=self.headers, timeout=10)
            print(f"✅ Status Code: {response.status_code}")
            print("📦 First 300 chars of response:", response.text[:300])
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print("❌ Error fetching API data:", e)
            return {}
        
    def refresh(self):
        self._resident_raw = None
        self._visitor_raw = None

    def fetch_resident(self):
        if self._resident_raw is None:
            self._resident_raw = self._fetch(self.RESIDENT_URL)
        return self._resident_raw

    def fetch_visitor(self):
        if self._visitor_raw is None:
            self._visitor_raw = self._fetch(self.VISITOR_URL)
        return self._visitor_raw

    @staticmethod
    def _judge_resident(time):
        if time == 0:
            return 'Less than 15 minutes'
        elif time == 1:
            return 'Less than 30 minutes'
        elif time == 2:
            return 'Less than 30 minutes'
        elif time == 4:
            return 'System Under Maintenance'
        elif time == 99:
            return 'Non Service Hours'

    @staticmethod
    def _judge_visitor(time):
        if time == 0:
            return 'Less than 30 minutes'
        elif time == 1:
            return 'Less than 45 minutes'
        elif time == 2:
            return '45 minutes or above'
        elif time == 4:
            return 'System Under Maintenance'
        else:
            return 'Non Service Hours'


    def get_resident_times(self):
        r_data = self.fetch_resident()
        for place, info in r_data.items():
            info['arrQueue'] = self._judge_resident(info['arrQueue'])
            info['depQueue'] = self._judge_resident(info['depQueue'])
        return r_data

    def get_visitor_times(self):
        v_data = self.fetch_visitor()
        for place, info in v_data.items():
            info['arrQueue'] = self._judge_visitor(info['arrQueue'])
            info['depQueue'] = self._judge_visitor(info['depQueue'])
        return v_data

if __name__ == '__main__':
    client = WaitingTimeClient()
    resident = client.get_resident_times()
    visitor  = client.get_visitor_times()

    print("Residents:")
    for place, times in resident.items():
        print(f" - {place}: arrival {times['arrQueue']}, departure {times['depQueue']}")

    print("\nVisitors:")
    for place, times in visitor.items():
        print(f" - {place}: arrival {times['arrQueue']}, departure {times['depQueue']}")