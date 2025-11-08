"""
Test script to find working NOAA tile URLs
"""
import requests

# Common NOAA storm names and dates
test_urls = [
    # Hurricane Ian 2022 - Florida
    "https://storms.ngs.noaa.gov/storms/ian/20220929_oblique/tiles/19/165234/234567.png",
    "https://storms.ngs.noaa.gov/storms/ian/20221001_oblique/tiles/19/165234/234567.png",
    
    # Hurricane Fiona 2022 - Puerto Rico
    "https://storms.ngs.noaa.gov/storms/fiona/20220920_oblique/tiles/19/153234/123456.png",
    
    # Hurricane Idalia 2023 - Florida
    "https://storms.ngs.noaa.gov/storms/idalia/20230831_oblique/tiles/19/165234/234567.png",
]

print("Testing NOAA tile URLs...\n")

for url in test_urls:
    try:
        response = requests.head(url, timeout=10)
        if response.status_code == 200:
            print(f"✓ FOUND: {url}")
        else:
            print(f"✗ {response.status_code}: {url}")
    except Exception as e:
        print(f"✗ ERROR: {url} - {str(e)}")

print("\n" + "="*60)
print("If you found working URLs above, use them in test_index.py")
print("="*60)
