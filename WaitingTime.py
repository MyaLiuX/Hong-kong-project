import requests
import copy

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
        return copy.deepcopy(self._resident_raw) 

    def fetch_visitor(self):
        if self._visitor_raw is None:
            self._visitor_raw = self._fetch(self.VISITOR_URL)
        return copy.deepcopy(self._visitor_raw)

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
        else:
            return f"Unknown ({time})"


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
        elif time == 99:
            return 'Non Service Hours'
        else:
            return f"Unknown ({time})"
        
    @staticmethod
    def home_page_judging(time):
        if time == 0:
            return 'Port Clear'
        if time == 1 or time == 2:
            return 'Long Wait'
        if time == 4:
            return 'System Under Maintenance'
        if time == 99:
            return 'Non Service Hours'
        else:
            return f"Unknown ({time})"
        
    def home_page_showing(self):

            r_data = self.fetch_resident()
            v_data = self.fetch_visitor()

            if not r_data or not v_data:
                print("❌ Could not fetch data for both resident and visitor. Cannot generate home page status.")
                return {}

            home_show = {}
            common_keys = r_data.keys() & v_data.keys()

            print(f"\nFound {len(common_keys)} common control points.")

            for key in common_keys:
                if key in r_data and 'arrQueue' in r_data[key]:
                    time_code = r_data[key]['arrQueue']
                    status = self.home_page_judging(time_code)
                    home_show[key] = status
                else:
                    print(f"⚠️ Warning: Key '{key}' or 'arrQueue' not found in r_data, skipping.")

            return home_show

    def get_resident_times(self):
        r_data = self.fetch_resident()
        processed_data = {}
        for place, info in r_data.items():
            processed_info = info.copy()
            if isinstance(processed_info.get('arrQueue'), int):
                processed_info['arrQueue'] = self._judge_resident(processed_info['arrQueue'])
            if isinstance(processed_info.get('depQueue'), int):
                processed_info['depQueue'] = self._judge_resident(processed_info['depQueue'])
            processed_data[place] = processed_info
        return processed_data


    def get_visitor_times(self):
        v_data = self.fetch_visitor()
        processed_data = {}
        for place, info in v_data.items():
            processed_info = info.copy()
            if isinstance(processed_info.get('arrQueue'), int):
                processed_info['arrQueue'] = self._judge_visitor(processed_info['arrQueue'])
            if isinstance(processed_info.get('depQueue'), int):
                processed_info['depQueue'] = self._judge_visitor(processed_info['depQueue'])
            processed_data[place] = processed_info
        return processed_data

if __name__ == '__main__':
    client = WaitingTimeClient()
    resident = client.get_resident_times()
    visitor  = client.get_visitor_times()

    # print("Residents:")
    # for place, times in resident.items():
    #     print(f" - {place}: arrival {times['arrQueue']}, departure {times['depQueue']}")

    # print("\nVisitors:")
    # for place, times in visitor.items():
    #     print(f" - {place}: arrival {times['arrQueue']}, departure {times['depQueue']}")