# utils.py
request_counter = 0


def increment_counter():
    global request_counter
    request_counter += 1


# Configuration constants
GRID_URL = "https://authservice.apps.meo.pt/Services/GridTv/GridTvMng.svc/getGridAnon"
CHANNEL_DETAILS_URL = "https://meogouser.apps.meo.pt/Services/GridTv/GridTv.svc/GetChannelInfo?callLetter=" #! dont forget to add the channel id at the end
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