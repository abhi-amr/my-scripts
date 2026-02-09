import json
import os
import time
import random
import requests
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
load_dotenv()



# ==================================================
# CONFIGURATION
# ==================================================

# LINKS
TARGET_DOMAIN = os.getenv("TARGET_DOMAIN")
TARGET_ENDPOINT = os.getenv("TARGET_ENDPOINT")
BASE_URL = f"https://{TARGET_DOMAIN}/{TARGET_ENDPOINT}"
START_ID = int(os.getenv("START_ID"))
END_ID = int(os.getenv("END_ID"))


#FILES
EXCEL_FILE_NAME = os.getenv("EXCEL_FILE_NAME")
EXCEL_FILE_URL = os.getenv("EXCEL_FILE_URL") # this is not being used 

# make service-account path relative to this script file (works no matter current CWD)
SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(__file__), "../google_sheet_creds.json")
DUMMY_RESPONSES_FILE = os.path.join(os.path.dirname(__file__), "dummy_response.json")

# Delay settings (human-like)
MIN_DELAY = float(os.getenv("MIN_DELAY"))
MAX_DELAY = float(os.getenv("MAX_DELAY"))

# Optional proxy (recommended if no VPN)
PROXIES = None
# Example:
# PROXIES = {
#     "http": "http://user:pass@proxy_ip:port",
#     "https": "http://user:pass@proxy_ip:port"
# }


#Service account details
TYPE = os.getenv("TYPE")
PROJECT_ID = os.getenv("PROJECT_ID")
PRIVATE_KEY_ID = os.getenv("PRIVATE_KEY_ID")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
CLIENT_EMAIL = os.getenv("CLIENT_EMAIL")
CLIENT_ID = os.getenv("CLIENT_ID")
AUTH_URI = os.getenv("AUTH_URI")
TOKEN_URI = os.getenv("TOKEN_URI")
AUTH_PROVIDER_X509_CERT_URL = os.getenv("AUTH_PROVIDER_X509_CERT_URL")
CLIENT_X509_CERT_URL = os.getenv("CLIENT_X509_CERT_URL")
UNIVERSE_DOMAIN = os.getenv("UNIVERSE_DOMAIN")





# ==================================================
# SETUP
# ==================================================

def get_service_account_info():
    return {
        "type": TYPE,
        "project_id": PROJECT_ID,
        "private_key_id": PRIVATE_KEY_ID,
        "private_key": PRIVATE_KEY,
        "client_email": CLIENT_EMAIL,
        "client_id": CLIENT_ID,
        "auth_uri": AUTH_URI,
        "token_uri": TOKEN_URI,
        "auth_provider_x509_cert_url": AUTH_PROVIDER_X509_CERT_URL,
        "client_x509_cert_url": CLIENT_X509_CERT_URL,
        "universe_domain": UNIVERSE_DOMAIN
    }

def connect_to_sheet(sheet_name=None):
    SCOPES = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(get_service_account_info(), scopes=SCOPES)
    client = gspread.authorize(creds)
    sh = client.open(EXCEL_FILE_NAME)
    if sheet_name:
        return sh.worksheet(sheet_name)
    return sh.sheet1

def create_session():
    session = requests.Session()

    # Headers copied from browser curl
    session.headers.update({
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Referer": f"https://{TARGET_DOMAIN}/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/141.0.0.0 Safari/537.36"
        ),
        "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    })

    if PROXIES:
        session.proxies.update(PROXIES)

    return session

def load_dummy_responses():
    if not os.path.exists(DUMMY_RESPONSES_FILE):
        print(f"Dummy responses file '{DUMMY_RESPONSES_FILE}' not found.")
        return {}

    with open(DUMMY_RESPONSES_FILE, "r") as f:
        return json.load(f)
    
def append_dynamic_json(sheet, data):

    # Step 1 — Get existing header
    existing_rows = sheet.get_all_values()

    if existing_rows:
        headers = existing_rows[0]
    else:
        headers = list(data.keys())
        sheet.append_row(headers)

    # Step 2 — Detect new keys
    new_keys = [k for k in data.keys() if k not in headers]

    # Step 3 — If new keys exist → extend header
    if new_keys:
        headers.extend(new_keys)

        # Update header row in sheet
        sheet.update(range_name="1:1", values=[headers])
        
        # IMPORTANT — reload header after update
        headers = sheet.row_values(1)

        # print(f"Added new columns: {new_keys}")

    # Step 4 — Build row aligned to header
    row = [data.get(h, "") for h in headers]

    # Step 5 — Append row
    sheet.append_row(row, value_input_option="USER_ENTERED")


# ==================================================
# MAIN LOGIC
# ==================================================


def main():
    print("SCRIPT STARTED")
    
    sheet = connect_to_sheet()
    session = create_session()

    # dummy_responses = load_dummy_responses()
    # responses = dummy_responses.get("responses", [])

    for identifier in range(START_ID, END_ID + 1):
        url = f"{BASE_URL}{identifier}"
        print(f"Processing ID: {identifier} | URL: {url}")
        try:
            response = session.get(url, timeout=12)
            response.raise_for_status()
            data = response.json()

            if data["validationStatus"] == "0":
                continue
            
            append_dynamic_json(sheet, data)

        except Exception as e:
            print(f"Error for response: {e}")

        # Human-like delay
        time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

    print("Completed. Data saved to Sheet.")
    print("SCRIPT COMPLETED")



if __name__ == "__main__":
    main()


