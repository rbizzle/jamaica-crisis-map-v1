"""
Test script for the /search_images endpoint.

Usage:
    python test_search.py

Before running:
    1. Make sure your backend is running (locally or on Cloud Run)
    2. Update BASE_URL below to point to your backend
"""

import requests
import json


# -------------------- CONFIG --------------------

# Update this to your backend URL
# BASE_URL = "http://localhost:8080"  # For local testing
BASE_URL = "https://melissa-backend-501310932916.us-central1.run.app"  # For Cloud Run

# -------------------- TEST CASES --------------------

def test_basic_search():
    """Test basic search without region-of-interest."""
    print("\n" + "="*60)
    print("TEST 1: Basic Search")
    print("="*60)
    
    payload = {
        "query": "flooded roads near Mandeville",
        "k": 5
    }
    
    print(f"\nRequest URL: {BASE_URL}/search_images")
    print(f"Request Body: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/search_images",
            json=payload,
            timeout=30
        )
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            results = response.json().get("results", [])
            print(f"\n✓ Success! Found {len(results)} results")
        else:
            print(f"\n✗ Error: {response.json().get('error')}")
            
    except Exception as e:
        print(f"\n✗ Request failed: {str(e)}")


def test_search_with_roi():
    """Test search with region-of-interest bounding box."""
    print("\n" + "="*60)
    print("TEST 2: Search with Region of Interest")
    print("="*60)
    
    payload = {
        "query": "damaged buildings and infrastructure",
        "k": 10,
        "roi": {
            "west": -78.0,
            "south": 17.5,
            "east": -76.0,
            "north": 18.7
        }
    }
    
    print(f"\nRequest URL: {BASE_URL}/search_images")
    print(f"Request Body: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/search_images",
            json=payload,
            timeout=30
        )
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            results = response.json().get("results", [])
            print(f"\n✓ Success! Found {len(results)} results in ROI")
        else:
            print(f"\n✗ Error: {response.json().get('error')}")
            
    except Exception as e:
        print(f"\n✗ Request failed: {str(e)}")


def test_various_queries():
    """Test different types of search queries."""
    print("\n" + "="*60)
    print("TEST 3: Various Search Queries")
    print("="*60)
    
    queries = [
        "coastal flooding",
        "damaged homes",
        "debris on streets",
        "water damage",
        "storm surge impact"
    ]
    
    for query in queries:
        print(f"\n--- Query: '{query}' ---")
        
        payload = {
            "query": query,
            "k": 3
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/search_images",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                results = response.json().get("results", [])
                print(f"✓ Found {len(results)} results")
                
                # Show top result if available
                if results:
                    top = results[0]
                    print(f"  Top result: {top.get('image_id')} (distance: {top.get('distance'):.4f})")
                    print(f"  Location: {top.get('center')}")
            else:
                print(f"✗ Error: {response.json().get('error')}")
                
        except Exception as e:
            print(f"✗ Request failed: {str(e)}")


def test_invalid_requests():
    """Test error handling with invalid requests."""
    print("\n" + "="*60)
    print("TEST 4: Error Handling")
    print("="*60)
    
    test_cases = [
        {
            "name": "Empty query",
            "payload": {"query": "", "k": 5}
        },
        {
            "name": "Missing query field",
            "payload": {"k": 5}
        },
        {
            "name": "Invalid k value",
            "payload": {"query": "test", "k": -1}
        }
    ]
    
    for test in test_cases:
        print(f"\n--- {test['name']} ---")
        print(f"Payload: {json.dumps(test['payload'], indent=2)}")
        
        try:
            response = requests.post(
                f"{BASE_URL}/search_images",
                json=test['payload'],
                timeout=30
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            
            if response.status_code != 200:
                print(f"✓ Correctly returned error")
            else:
                print(f"⚠ Expected error but got success")
                
        except Exception as e:
            print(f"✗ Request failed: {str(e)}")


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


# -------------------- MAIN --------------------

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("MELISSA BACKEND - SEARCH ENDPOINT TESTS")
    print("="*60)
    print(f"Target URL: {BASE_URL}")
    
    # First check if service is running
    if not test_health_check():
        print("\n⚠ Skipping search tests - service not available")
        return
    
    # Run search tests
    test_basic_search()
    test_search_with_roi()
    test_various_queries()
    test_invalid_requests()
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETED")
    print("="*60)


if __name__ == "__main__":
    main()
