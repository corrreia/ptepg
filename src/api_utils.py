import requests

# Configuration constants
GRID_URL = "https://authservice.apps.meo.pt/Services/GridTv/GridTvMng.svc/getGridAnon"
PROGRAMS_URL = "https://authservice.apps.meo.pt/Services/GridTv/GridTvMng.svc/getProgramsFromChannels"
PROGRAM_DETAILS_URL = (
    "https://authservice.apps.meo.pt/Services/GridTv/GridTvMng.svc/getProgramDetails"
)
HEADERS = {
    "Origin": "https://www.meo.pt",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Content-Type": "application/json; charset=UTF-8",
    "Accept": "*/*",
}


def make_post_request(url, data=None):
    """Make a POST request to the specified URL with optional JSON data."""
    try:
        response = requests.post(url, headers=HEADERS, json=data)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return None
