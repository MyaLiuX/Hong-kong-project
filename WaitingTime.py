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
        # These will store raw fetched data to avoid re-fetching within a short period
        # if multiple calls to get_..._times happen before refresh()
        self._resident_raw = None
        self._visitor_raw  = None

    def _fetch(self, url):
        try:
            print(f"🌐 Fetching from {url}")
            response = requests.get(url, headers=self.headers, timeout=10) # 10-second timeout
            response.raise_for_status() # Raises an HTTPError for bad responses (4XX or 5XX)
            print(f"✅ Status Code: {response.status_code} from {url}")
            # print("📦 First 300 chars of response:", response.text[:300]) # Good for debugging
            return response.json()
        except requests.exceptions.RequestException as e: # Catch network/HTTP errors
            print(f"❌ Error fetching API data from {url}: {e}")
            return {} # Return empty dict on failure
        except ValueError as e: # Catch JSON decoding errors
            print(f"❌ Error decoding JSON from {url}: {e}")
            return {} # Return empty dict on failure

    def refresh(self):
        """Clears cached raw data to force a fresh fetch on next call."""
        print("🔄 Refreshing cached data. Next 'get' will fetch from API.")
        self._resident_raw = None
        self._visitor_raw = None

    def fetch_resident(self):
        """Fetches raw resident data, using cache if available."""
        if self._resident_raw is None:
            print("Cache miss for resident raw data. Fetching from API.")
            self._resident_raw = self._fetch(self.RESIDENT_URL)
        return copy.deepcopy(self._resident_raw) if self._resident_raw else {}

    def fetch_visitor(self):
        """Fetches raw visitor data, using cache if available."""
        if self._visitor_raw is None:
            print("Cache miss for visitor raw data. Fetching from API.")
            self._visitor_raw = self._fetch(self.VISITOR_URL)
        return copy.deepcopy(self._visitor_raw) if self._visitor_raw else {}

    @staticmethod
    def _judge_resident(time):
        if time == 0: return 'Less than 15 minutes'
        if time == 1: return 'Less than 30 minutes'
        if time == 2: return 'Less than 30 minutes' # Note: As per your original, 1 and 2 map to same string
        if time == 4: return 'System Under Maintenance'
        if time == 99: return 'Non Service Hours'
        return f"Unknown ({time})"

    @staticmethod
    def _judge_visitor(time):
        if time == 0: return 'Less than 30 minutes'
        if time == 1: return 'Less than 45 minutes'
        if time == 2: return '45 minutes or above'
        if time == 4: return 'System Under Maintenance'
        if time == 99: return 'Non Service Hours'
        return f"Unknown ({time})"

    @staticmethod
    def home_page_judging(time):
        if time == 0: return 'Port Clear'
        if time == 1 or time == 2: return 'Long Wait'
        if time == 4: return 'System Under Maintenance'
        if time == 99: return 'Non Service Hours'
        return f"Unknown ({time})"

    def home_page_showing(self, r_data_raw, v_data_raw):
        # This method expects RAW data (with numeric queues)
        if not r_data_raw or not v_data_raw:
            print("❌ Could not get raw data for resident and/or visitor. Cannot generate home page status.")
            return {} # Return empty dict

        home_show_statuses = {}
        # Get control point keys, excluding 'lastUpdate'
        r_keys = set(r_data_raw.keys()) - {'lastUpdate'}
        v_keys = set(v_data_raw.keys()) - {'lastUpdate'}
        common_keys = r_keys & v_keys

        # print(f"Generating home page status for {len(common_keys)} common control points.")

        for key in common_keys:
            # Using resident arrival queue for the home page status, as per your original logic
            if isinstance(r_data_raw.get(key), dict) and 'arrQueue' in r_data_raw[key]:
                time_code = r_data_raw[key]['arrQueue']
                status = self.home_page_judging(time_code)
                home_show_statuses[key] = status
            else:
                print(f"⚠️ Warning (home_page_showing): Key '{key}' data malformed or 'arrQueue' missing in r_data_raw. Skipping.")
        return home_show_statuses

    def get_resident_times(self):
        """Fetches and processes resident data, adding lastUpdate to each item."""
        # self.refresh() # Call this if you want get_resident_times to ALWAYS fetch fresh, bypassing client-level cache
        r_data_raw = self.fetch_resident() # Gets raw data (cached or fresh)
        if not r_data_raw:
            print("❌ No raw resident data to process.")
            return {}

        processed_data = {}
        # Get the top-level lastUpdate time
        last_update_time = r_data_raw.get("lastUpdate", "N/A")

        for place, info_dict in r_data_raw.items():
            if place == "lastUpdate": # Skip the top-level 'lastUpdate' key itself
                continue
            if isinstance(info_dict, dict): # Ensure we are processing a control point's data
                processed_info = info_dict.copy() # Make a copy to modify
                processed_info['lastUpdate'] = last_update_time # Add the global lastUpdate

                if 'arrQueue' in processed_info and isinstance(processed_info['arrQueue'], int):
                    processed_info['arrQueue'] = self._judge_resident(processed_info['arrQueue'])
                if 'depQueue' in processed_info and isinstance(processed_info['depQueue'], int):
                    processed_info['depQueue'] = self._judge_resident(processed_info['depQueue'])
                processed_data[place] = processed_info
            # else: print(f"ℹ️ Skipping non-dict item in resident data: {place}")
        return processed_data

    def get_visitor_times(self):
        """Fetches and processes visitor data, adding lastUpdate to each item."""
        # self.refresh() # Call this if you want get_visitor_times to ALWAYS fetch fresh
        v_data_raw = self.fetch_visitor()
        if not v_data_raw:
            print("❌ No raw visitor data to process.")
            return {}

        processed_data = {}
        last_update_time = v_data_raw.get("lastUpdate", "N/A")

        for place, info_dict in v_data_raw.items():
            if place == "lastUpdate":
                continue
            if isinstance(info_dict, dict):
                processed_info = info_dict.copy()
                processed_info['lastUpdate'] = last_update_time

                if 'arrQueue' in processed_info and isinstance(processed_info['arrQueue'], int):
                    processed_info['arrQueue'] = self._judge_visitor(processed_info['arrQueue'])
                if 'depQueue' in processed_info and isinstance(processed_info['depQueue'], int):
                    processed_info['depQueue'] = self._judge_visitor(processed_info['depQueue'])
                processed_data[place] = processed_info
            # else: print(f"ℹ️ Skipping non-dict item in visitor data: {place}")
        return processed_data

if __name__ == '__main__':
    client = WaitingTimeClient()

    print("\n--- Getting Processed Resident Times (with lastUpdate per item) ---")
    resident_processed = client.get_resident_times()
    for place, times in resident_processed.items():
        print(f" - {place}: arrival '{times.get('arrQueue', 'N/A')}', departure '{times.get('depQueue', 'N/A')}', updated '{times.get('lastUpdate', 'N/A')}'")

    print("\n--- Getting Processed Visitor Times (with lastUpdate per item) ---")
    visitor_processed  = client.get_visitor_times()
    for place, times in visitor_processed.items():
        print(f" - {place}: arrival '{times.get('arrQueue', 'N/A')}', departure '{times.get('depQueue', 'N/A')}', updated '{times.get('lastUpdate', 'N/A')}'")

    print("\n--- Getting Home Page Showing (uses fresh raw data internally) ---")
    raw_res = client.fetch_resident() # Fetches again if refresh was called or first time
    raw_vis = client.fetch_visitor()  # Fetches again if refresh was called or first time
    
    home_display = client.home_page_showing(raw_res, raw_vis)
    print("Home Page Display Statuses:", home_display)
    print("Overall Resident Data Last Update (from raw):", raw_res.get("lastUpdate"))
    print("Overall Visitor Data Last Update (from raw):", raw_vis.get("lastUpdate"))
