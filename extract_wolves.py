
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ==========================================
# 1. API CONFIGURATION
# ==========================================

url = "https://get.data.gov.lt/datasets/gov/vstt/vilku_medziokles/Vilkas/:format/json"

page_size = 10
next_page = None

all_wolves = []
page_number = 0
seen_tokens = set()

# Test only two pages for now
max_pages = 2

# ==========================================
# 2. CONFIGURE AUTOMATIC RETRIES
# ==========================================

session = requests.Session()

retry_strategy = Retry(
    total=2,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
    raise_on_status=False
)

adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)

# ==========================================
# 3. EXTRACT DATA USING PAGINATION
# ==========================================

while page_number < max_pages:

    # Request parameters
    params = {
        "_limit": page_size,
        "_sort": "_id"
    }

    # Add pagination token after the first page
    if next_page is not None:
        params["_page"] = next_page

    print(f"\nRequesting page {page_number + 1}...")
    print(f"Request parameters: {params}")

    try:
        response = session.get(
            url,
            params=params,
            timeout=30
        )

        print(f"HTTP status: {response.status_code}")
        print(f"Request URL: {response.url}")

        # Handle unsuccessful HTTP responses
        if response.status_code != 200:
            print("\nAPI error response:")
            print(response.text[:2000])
            print("Extraction stopped.")
            break

        # Convert JSON response to Python objects
        data = response.json()

        # Extract records
        wolves = data["_data"]

        # Add records to the complete list
        all_wolves.extend(wolves)

        page_number += 1

        print(f"Page {page_number}: {len(wolves)} records")
        print(f"Total collected: {len(all_wolves)}")

        # Retrieve pagination token
        next_page = data.get("_page", {}).get("next")

        # Stop when no further pages exist
        if not next_page:
            print("No more pages available.")
            break

        # Prevent repeated pagination tokens
        if next_page in seen_tokens:
            print("Error: Repeated pagination token.")
            break

        seen_tokens.add(next_page)

    except requests.exceptions.RequestException as error:
        print(f"\nRequest failed: {error}")
        break

    except (ValueError, KeyError, TypeError) as error:
        print(f"\nInvalid API response: {error}")
        break

# ==========================================
# 4. FINAL SUMMARY
# ==========================================

print("\n================================")
print("EXTRACTION SUMMARY")
print("================================")

print(f"Pages retrieved: {page_number}")
print(f"Records collected: {len(all_wolves)}")

if all_wolves:
    print("\nExample record:")
    print(all_wolves[0])

print("\nScript finished.")
