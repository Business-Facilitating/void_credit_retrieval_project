import json
import os
import pprint
import time
from datetime import datetime

import requests

# url = "https://wwwcie.ups.com/security/v1/oauth/token"
url = "https://onlinetools.ups.com/security/v1/oauth/token"

username = "Cs4KhQU4i8w80AHzi5UT3onZtx1CRgGUZD9wCu10LHjuL4tt"
password = "49yK1AvXl8JeuJCz2PHJM5D6I2ggsyTKgoFtN360fMDBnArn7vvzYUe0HHgxB6kP"

payload = {"grant_type": "client_credentials"}

headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "x-merchant-id": "string",
}

response = requests.post(url, data=payload, headers=headers, auth=(username, password))

data = response.json()
access_token = data["access_token"]

# Create output directory if it doesn't exist
output_dir = "data/output"
os.makedirs(output_dir, exist_ok=True)

# Generate timestamp for the batch
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

epoch_time = int(time.time())

# tracking_nums = [
#     "1ZVX23230333926007",  # UPS tracking number
#     "1ZX041680390454826",  # UPS tracking number void
#     "1ZX041680392116410",  # UPS tracking number void
#     "1ZX041680393993711",  # UPS tracking number void
#     "1ZX041680394889056",  # UPS tracking number"
# ]

tracking_nums = ["1Z6A2V900332443747"]

# Store all responses
all_responses = []

for i, inquiry_number in enumerate(tracking_nums, 1):
    print(f"Processing tracking number {i}/{len(tracking_nums)}: {inquiry_number}")

    url = "https://onlinetools.ups.com/api/track/v1/details/" + inquiry_number
    epoch_time = int(time.time())

    headers = {
        "transId": str(epoch_time),
        "transactionSrc": "testing",
        "Authorization": f"Bearer {access_token}",
    }

    response = requests.get(url, headers=headers)
    data = response.json()

    # Add metadata to the response
    response_with_metadata = {
        "tracking_number": inquiry_number,
        "request_timestamp": datetime.now().isoformat(),
        "response_status_code": response.status_code,
        "ups_response": data,
    }

    # Store in collection
    all_responses.append(response_with_metadata)

    # Save individual response
    individual_filename = f"ups_tracking_{inquiry_number}_{timestamp}.json"
    individual_filepath = os.path.join(output_dir, individual_filename)

    with open(individual_filepath, "w", encoding="utf-8") as f:
        json.dump(response_with_metadata, f, indent=2, ensure_ascii=False)

    # Print status summary
    if response.status_code == 200 and "trackResponse" in data:
        try:
            status = data["trackResponse"]["shipment"][0]["package"][0]["currentStatus"]
            print(f"  Status: {status['description']} (code: {status['code']})")
        except (KeyError, IndexError):
            print("  Status: Unable to parse status from response")
    else:
        print(f"  Error: HTTP {response.status_code}")

    print(f"  Saved to: {individual_filepath}")
    print()

# Save combined responses
combined_filename = f"ups_tracking_batch_{timestamp}.json"
combined_filepath = os.path.join(output_dir, combined_filename)

combined_data = {
    "batch_timestamp": datetime.now().isoformat(),
    "total_tracking_numbers": len(tracking_nums),
    "responses": all_responses,
}

with open(combined_filepath, "w", encoding="utf-8") as f:
    json.dump(combined_data, f, indent=2, ensure_ascii=False)

print(f"All responses saved to: {combined_filepath}")
print(f"Individual files saved to: {output_dir}")
print(f"Total tracking numbers processed: {len(tracking_nums)}")
