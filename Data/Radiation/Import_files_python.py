import requests
import os

# Your EUMETSAT credentials
consumer_key = "mDpW8m3E2kBrw6qPV59nvORVI9Qa"
consumer_secret = "pQUBLgF4WtfhjdBpgvSWilqXfiIa"

# Get access token
token_url = "https://api.eumetsat.int/token"
response = requests.post(token_url, 
    data={"grant_type": "client_credentials"},
    auth=(consumer_key, consumer_secret))
token = response.json()["access_token"]
print(f"Token obtained: {token[:20]}...")

# Create output folder
out_dir = r"C:\Nikola\Year 3\Semester 5\Notebook\Data\Radiation"
os.makedirs(out_dir, exist_ok=True)

# Paste ALL URLs from your Excel column B here
urls = [
    
"https://api.eumetsat.int/data/download/1.0.0/collections/EO%3AEUM%3ADAT%3A0863/products/SISmm2026020100000042310001I1MA"
"https://api.eumetsat.int/data/download/1.0.0/collections/EO%3AEUM%3ADAT%3A0863/products/SISmm2026010100000042310001I1MA"
"https://api.eumetsat.int/data/download/1.0.0/collections/EO%3AEUM%3ADAT%3A0863/products/SISmm2025120100000042310001I1MA"
"https://api.eumetsat.int/data/download/1.0.0/collections/EO%3AEUM%3ADAT%3A0863/products/SISmm2025110100000042310001I1MA"
"https://api.eumetsat.int/data/download/1.0.0/collections/EO%3AEUM%3ADAT%3A0863/products/SISmm2025100100000042310001I1MA"
"https://api.eumetsat.int/data/download/1.0.0/collections/EO%3AEUM%3ADAT%3A0863/products/SISmm2025090100000042310001I1MA"
"https://api.eumetsat.int/data/download/1.0.0/collections/EO%3AEUM%3ADAT%3A0863/products/SISmm2025080100000042310001I1MA"
"https://api.eumetsat.int/data/download/1.0.0/collections/EO%3AEUM%3ADAT%3A0863/products/SISmm2025070100000042310001I1MA"
"https://api.eumetsat.int/data/download/1.0.0/collections/EO%3AEUM%3ADAT%3A0863/products/SISmm2025060100000042310001I1MA"
"https://api.eumetsat.int/data/download/1.0.0/collections/EO%3AEUM%3ADAT%3A0863/products/SISmm2025050100000042310001I1MA"
"https://api.eumetsat.int/data/download/1.0.0/collections/EO%3AEUM%3ADAT%3A0863/products/SISmm2025040100000042310001I1MA"
"https://api.eumetsat.int/data/download/1.0.0/collections/EO%3AEUM%3ADAT%3A0863/products/SISmm2025030100000042310001I1MA"
"https://api.eumetsat.int/data/download/1.0.0/collections/EO%3AEUM%3ADAT%3A0863/products/SISmm2025020100000042310001I1MA"
"https://api.eumetsat.int/data/download/1.0.0/collections/EO%3AEUM%3ADAT%3A0863/products/SISmm2025010100000042310001I1MA"
"https://api.eumetsat.int/data/download/1.0.0/collections/EO%3AEUM%3ADAT%3A0863/products/SISmm2024120100000042310001I1MA"
"https://api.eumetsat.int/data/download/1.0.0/collections/EO%3AEUM%3ADAT%3A0863/products/SISmm2024110100000042310001I1MA"
"https://api.eumetsat.int/data/download/1.0.0/collections/EO%3AEUM%3ADAT%3A0863/products/SISmm2024100100000042310001I1MA"
"https://api.eumetsat.int/data/download/1.0.0/collections/EO%3AEUM%3ADAT%3A0863/products/SISmm2024090100000042310001I1MA"
"https://api.eumetsat.int/data/download/1.0.0/collections/EO%3AEUM%3ADAT%3A0863/products/SISmm2024080100000042310001I1MA"
"https://api.eumetsat.int/data/download/1.0.0/collections/EO%3AEUM%3ADAT%3A0863/products/SISmm2024070100000042310001I1MA"
"https://api.eumetsat.int/data/download/1.0.0/collections/EO%3AEUM%3ADAT%3A0863/products/SISmm2024060100000042310001I1MA"
"https://api.eumetsat.int/data/download/1.0.0/collections/EO%3AEUM%3ADAT%3A0863/products/SISmm2024050100000042310001I1MA"
"https://api.eumetsat.int/data/download/1.0.0/collections/EO%3AEUM%3ADAT%3A0863/products/SISmm2024040100000042310001I1MA"
"https://api.eumetsat.int/data/download/1.0.0/collections/EO%3AEUM%3ADAT%3A0863/products/SISmm2024030100000042310001I1MA"
"https://api.eumetsat.int/data/download/1.0.0/collections/EO%3AEUM%3ADAT%3A0863/products/SISmm2024020100000042310001I1MA"
"https://api.eumetsat.int/data/download/1.0.0/collections/EO%3AEUM%3ADAT%3A0863/products/SISmm2024010100000042310001I1MA"
"https://api.eumetsat.int/data/download/1.0.0/collections/EO%3AEUM%3ADAT%3A0863/products/SISmm2023120100000042310001I1MA"
"https://api.eumetsat.int/data/download/1.0.0/collections/EO%3AEUM%3ADAT%3A0863/products/SISmm2023110100000042310001I1MA"
"https://api.eumetsat.int/data/download/1.0.0/collections/EO%3AEUM%3ADAT%3A0863/products/SISmm2023100100000042310001I1MA"

]

# Download each file
for url in urls:
    fname = url.split("/")[-1] + ".zip"
    fpath = os.path.join(out_dir, fname)
    
    if os.path.exists(fpath):
        print(f"Already exists: {fname}")
        continue
    
    print(f"Downloading: {fname}...")
    r = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    
    if r.status_code == 200:
        with open(fpath, "wb") as f:
            f.write(r.content)
        print(f"  Saved ({len(r.content) / 1024 / 1024:.1f} MB)")
    else:
        print(f"  ERROR: {r.status_code}")

print("Done!")