import pprint
import time

import requests

# url = "https://wwwcie.ups.com/security/v1/oauth/token"
url = "https://onlinetools.ups.com/security/v1/oauth/token"

username = "1nKP9i2iNWZkThuXuO8APEoFvKf12RjQbuUdqVZ9wbwA2ssZ"
password = "BqFPh3XeP9ksiC8Ow8gbaOMzig6jCV9J2BTGScHzTNgT7g8kFXbXZZIGEUaymEuw"

payload = {"grant_type": "client_credentials"}

headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "x-merchant-id": "string",
}

print("Making OAuth request to UPS API...")
print(f"URL: {url}")
print(f"Username: {username[:10]}...")

try:
    response = requests.post(
        url, data=payload, headers=headers, auth=(username, password), timeout=10
    )
    print(f"OAuth response status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        access_token = data["access_token"]
        print(f"Access token obtained: {access_token[:20]}...")
        # print(access_token)
    else:
        print(f"OAuth failed with status {response.status_code}")
        print(f"Response: {response.text}")
        exit(1)

except requests.exceptions.RequestException as e:
    print(f"OAuth request failed: {e}")
    exit(1)


epoch_time = int(time.time())

tracking_nums = ["1Z9348700392705721"]  # Same tracking number from ups_api.py

for inquiry_number in tracking_nums:
    version = "v2409"
    shipmentidentificationnumber = inquiry_number
    url = (
        "https://onlinetools.ups.com/api/shipments/"
        + version
        + "/void/cancel/"
        + shipmentidentificationnumber
    )
    # No query parameters needed; the tracking number is  in the path
    epoch_time = int(time.time())

    headers = {
        "transId": str(epoch_time),
        "transactionSrc": "testing",
        "Authorization": f"Bearer {access_token}",
    }

    query = {"trackingnumber": "1Z9348700392705721"}

    print(f"Making void request for tracking number: {shipmentidentificationnumber}")
    print(f"Void URL: {url}")

    try:
        response = requests.delete(url, headers=headers, params=query, timeout=15)
        print(f"Void response status: {response.status_code}")

        if response.status_code in (200, 202, 204):
            print("Void request accepted/successful.")
            try:
                data = response.json()
                pprint.pprint(data)
            except ValueError:
                print("No JSON body in response.")
        else:
            print(f"Void request failed with status {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            print(f"Response: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"Void request failed: {e}")
