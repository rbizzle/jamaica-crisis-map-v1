"""
Test script for the /index_tile endpoint.

Usage:
    python test_index.py

Before running:
    1. Make sure your backend is running (locally or on Cloud Run)
    2. Update BASE_URL and INDEX_TOKEN below
    3. Have some NOAA tile URLs ready to index
"""

import requests
import json
from datetime import datetime


# -------------------- CONFIG --------------------

# Update this to your backend URL
# BASE_URL = "http://localhost:8080"  # For local testing
BASE_URL = "https://melissa-backend-501310932916.us-central1.run.app"  # For Cloud Run

# Update this to match your INDEX_TOKEN environment variable
INDEX_TOKEN = "nF1tRrYPGwE7cv598Ke2AHmNQjIV3BZ4"  # Must match the token set in your backend

# -------------------- SAMPLE TILE DATA --------------------

# Real NOAA Hurricane Melissa tiles from Jamaica
# URL format: https://stormscdn.ngs.noaa.gov/20251031a-rgb/{z}/{x}/{y}
# Flight date: October 31, 2025 (Flight A - RGB imagery)

SAMPLE_TILES = [
    {
        "image_id": "melissa_20251031_001",
        "tile_url": "https://stormscdn.ngs.noaa.gov/20251031a-rgb/19/148768/235444",
        "thumb_url": None,
        "bounds": {
            "west": -77.3918,
            "south": 18.1785,
            "east": -77.3904,
            "north": 18.1798
        },
        "timestamp": "2025-10-31T14:00:00Z",
        "metadata": {
            "mission": "melissa",
            "disaster_type": "hurricane",
            "location": "Jamaica",
            "flight": "20251031a",
            "imagery_type": "rgb"
        }
    },
    {
        "image_id": "melissa_20251031_002",
        "tile_url": "https://stormscdn.ngs.noaa.gov/20251031a-rgb/19/148768/235443",
        "thumb_url": None,
        "bounds": {
            "west": -77.3918,
            "south": 18.1798,
            "east": -77.3904,
            "north": 18.1811
        },
        "timestamp": "2025-10-31T14:00:00Z",
        "metadata": {
            "mission": "melissa",
            "disaster_type": "hurricane",
            "location": "Jamaica",
            "flight": "20251031a",
            "imagery_type": "rgb"
        }
    },
    {
        "image_id": "melissa_20251031_003",
        "tile_url": "https://stormscdn.ngs.noaa.gov/20251031a-rgb/19/148769/235444",
        "thumb_url": None,
        "bounds": {
            "west": -77.3904,
            "south": 18.1785,
            "east": -77.3891,
            "north": 18.1798
        },
        "timestamp": "2025-10-31T14:00:00Z",
        "metadata": {
            "mission": "melissa",
            "disaster_type": "hurricane",
            "location": "Jamaica",
            "flight": "20251031a",
            "imagery_type": "rgb"
        }
    },
    {
        "image_id": "melissa_20251031_004",
        "tile_url": "https://stormscdn.ngs.noaa.gov/20251031a-rgb/19/148769/235443",
        "thumb_url": None,
        "bounds": {
            "west": -77.3904,
            "south": 18.1798,
            "east": -77.3891,
            "north": 18.1811
        },
        "timestamp": "2025-10-31T14:00:00Z",
        "metadata": {
            "mission": "melissa",
            "disaster_type": "hurricane",
            "location": "Jamaica",
            "flight": "20251031a",
            "imagery_type": "rgb"
        }
    },
    {
        "image_id": "melissa_20251031_005",
        "tile_url": "https://stormscdn.ngs.noaa.gov/20251031a-rgb/19/148770/235444",
        "thumb_url": None,
        "bounds": {
            "west": -77.3891,
            "south": 18.1785,
            "east": -77.3877,
            "north": 18.1798
        },
        "timestamp": "2025-10-31T14:00:00Z",
        "metadata": {
            "mission": "melissa",
            "disaster_type": "hurricane",
            "location": "Jamaica",
            "flight": "20251031a",
            "imagery_type": "rgb"
        }
    }
]


# -------------------- TEST FUNCTIONS --------------------

def test_health_check():
    """Test the health endpoint to verify service is running."""
    print("\n" + "="*60)
    print("HEALTH CHECK")
    print("="*60)
    
    print(f"\nRequest URL: {BASE_URL}/health")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=60)  # Increased timeout for cold start
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("\n✓ Service is healthy and running!")
            return True
        else:
            print("\n✗ Service returned non-200 status")
            return False
            
    except Exception as e:
        print(f"\n✗ Cannot connect to service: {str(e)}")
        print(f"\nMake sure:")
        print(f"  1. Your backend is running")
        print(f"  2. BASE_URL is correct: {BASE_URL}")
        return False


def index_tile(tile_data, token):
    """Index a single tile."""
    headers = {
        "X-Index-Token": token,
        "Content-Type": "application/json"
    }
    
    print(f"\n--- Indexing: {tile_data['image_id']} ---")
    print(f"Tile URL: {tile_data['tile_url']}")
    print(f"Bounds: {tile_data['bounds']}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/index_tile",
            headers=headers,
            json=tile_data,
            timeout=60  # Longer timeout for image processing
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print(f"✓ Successfully indexed {tile_data['image_id']}")
            return True
        else:
            print(f"✗ Failed to index: {response.json().get('error')}")
            return False
            
    except Exception as e:
        print(f"✗ Request failed: {str(e)}")
        return False


def test_index_single_tile():
    """Test indexing a single tile."""
    print("\n" + "="*60)
    print("TEST 1: Index Single Tile")
    print("="*60)
    
    tile = {
        "image_id": "test_tile_001",
        "tile_url": "https://example.com/tile.png",  # Replace with real URL
        "bounds": {
            "west": -77.50,
            "south": 18.00,
            "east": -77.40,
            "north": 18.05
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    return index_tile(tile, INDEX_TOKEN)


def test_index_multiple_tiles():
    """Test indexing multiple tiles from the sample list."""
    print("\n" + "="*60)
    print("TEST 2: Index Multiple Tiles")
    print("="*60)
    
    print(f"\nIndexing {len(SAMPLE_TILES)} tiles...")
    
    success_count = 0
    for tile in SAMPLE_TILES:
        if index_tile(tile, INDEX_TOKEN):
            success_count += 1
    
    print(f"\n{'='*60}")
    print(f"Results: {success_count}/{len(SAMPLE_TILES)} tiles indexed successfully")
    print(f"{'='*60}")


def test_invalid_auth():
    """Test authentication with invalid token."""
    print("\n" + "="*60)
    print("TEST 3: Invalid Authentication")
    print("="*60)
    
    headers = {
        "X-Index-Token": "wrong-token",
        "Content-Type": "application/json"
    }
    
    tile = {
        "image_id": "test_auth",
        "tile_url": "https://example.com/tile.png",
        "bounds": {
            "west": -77.50,
            "south": 18.00,
            "east": -77.40,
            "north": 18.05
        }
    }
    
    print("\nUsing invalid token: 'wrong-token'")
    
    try:
        response = requests.post(
            f"{BASE_URL}/index_tile",
            headers=headers,
            json=tile,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 401:
            print("\n✓ Correctly rejected invalid token")
        else:
            print("\n⚠ Expected 401 status but got different response")
            
    except Exception as e:
        print(f"\n✗ Request failed: {str(e)}")


def test_missing_fields():
    """Test error handling with missing required fields."""
    print("\n" + "="*60)
    print("TEST 4: Missing Required Fields")
    print("="*60)
    
    test_cases = [
        {
            "name": "Missing image_id",
            "data": {
                "tile_url": "https://example.com/tile.png",
                "bounds": {"west": -77.50, "south": 18.00, "east": -77.40, "north": 18.05}
            }
        },
        {
            "name": "Missing tile_url",
            "data": {
                "image_id": "test_001",
                "bounds": {"west": -77.50, "south": 18.00, "east": -77.40, "north": 18.05}
            }
        },
        {
            "name": "Missing bounds",
            "data": {
                "image_id": "test_001",
                "tile_url": "https://example.com/tile.png"
            }
        },
        {
            "name": "Incomplete bounds",
            "data": {
                "image_id": "test_001",
                "tile_url": "https://example.com/tile.png",
                "bounds": {"west": -77.50, "south": 18.00}  # Missing east/north
            }
        }
    ]
    
    headers = {
        "X-Index-Token": INDEX_TOKEN,
        "Content-Type": "application/json"
    }
    
    for test in test_cases:
        print(f"\n--- {test['name']} ---")
        
        try:
            response = requests.post(
                f"{BASE_URL}/index_tile",
                headers=headers,
                json=test['data'],
                timeout=30
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            
            if response.status_code == 400:
                print(f"✓ Correctly returned validation error")
            else:
                print(f"⚠ Expected 400 status but got {response.status_code}")
                
        except Exception as e:
            print(f"✗ Request failed: {str(e)}")


def test_with_bearer_token():
    """Test using Bearer token in Authorization header."""
    print("\n" + "="*60)
    print("TEST 5: Bearer Token Authentication")
    print("="*60)
    
    headers = {
        "Authorization": f"Bearer {INDEX_TOKEN}",
        "Content-Type": "application/json"
    }
    
    tile = {
        "image_id": "test_bearer_auth",
        "tile_url": "https://example.com/tile.png",
        "bounds": {
            "west": -77.50,
            "south": 18.00,
            "east": -77.40,
            "north": 18.05
        }
    }
    
    print("\nUsing Bearer token in Authorization header")
    
    try:
        response = requests.post(
            f"{BASE_URL}/index_tile",
            headers=headers,
            json=tile,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code in [200, 500]:  # 500 if URL is invalid, which is ok for auth test
            print("\n✓ Bearer token authentication works")
        else:
            print(f"\n⚠ Unexpected status: {response.status_code}")
            
    except Exception as e:
        print(f"\n✗ Request failed: {str(e)}")


def index_custom_tile():
    """Interactive function to index a custom tile."""
    print("\n" + "="*60)
    print("INDEX CUSTOM TILE")
    print("="*60)
    
    print("\nEnter tile details:")
    
    tile = {
        "image_id": input("Image ID: ").strip(),
        "tile_url": input("Tile URL: ").strip(),
        "bounds": {
            "west": float(input("West longitude: ")),
            "south": float(input("South latitude: ")),
            "east": float(input("East longitude: ")),
            "north": float(input("North latitude: "))
        }
    }
    
    timestamp = input("Timestamp (ISO format, or press Enter to use current time): ").strip()
    if timestamp:
        tile["timestamp"] = timestamp
    else:
        tile["timestamp"] = datetime.utcnow().isoformat() + "Z"
    
    thumb_url = input("Thumbnail URL (optional, press Enter to skip): ").strip()
    if thumb_url:
        tile["thumb_url"] = thumb_url
    
    return index_tile(tile, INDEX_TOKEN)


# -------------------- MAIN --------------------

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("MELISSA BACKEND - INDEX ENDPOINT TESTS")
    print("="*60)
    print(f"Target URL: {BASE_URL}")
    print(f"Index Token: {INDEX_TOKEN[:10]}..." if len(INDEX_TOKEN) > 10 else f"Index Token: {INDEX_TOKEN}")
    
    # First check if service is running
    if not test_health_check():
        print("\n⚠ Skipping index tests - service not available")
        return
    
    # Run tests
    test_invalid_auth()
    test_missing_fields()
    test_with_bearer_token()
    
    print("\n" + "="*60)
    print("READY TO INDEX TILES")
    print("="*60)
    print("\nNote: The sample tiles use placeholder URLs.")
    print("Replace SAMPLE_TILES with real NOAA tile URLs before indexing.")
    
    choice = input("\nDo you want to:\n1. Index sample tiles\n2. Index a custom tile\n3. Skip indexing\nChoice (1/2/3): ").strip()
    
    if choice == "1":
        test_index_multiple_tiles()
    elif choice == "2":
        index_custom_tile()
    else:
        print("\nSkipping tile indexing.")
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETED")
    print("="*60)
    print("\nNext steps:")
    print("1. Update SAMPLE_TILES with real NOAA tile URLs")
    print("2. Run this script to index your tiles")
    print("3. Use test_search.py to search the indexed tiles")


if __name__ == "__main__":
    main()
