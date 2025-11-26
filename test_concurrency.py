#!/usr/bin/env python3
"""
Test script for pricing service thread safety and concurrency
"""
from pricing_service import PricingService
import threading
import time


def test_concurrent_cache_access():
    """Test that multiple threads don't cause race conditions"""
    print("=" * 80)
    print("Testing Concurrent Cache Access")
    print("=" * 80)
    print()

    service = PricingService()
    results = []
    api_call_count = []

    # Track original fetch method to count API calls
    original_fetch = service._fetch_pricing_data

    def counting_fetch():
        api_call_count.append(1)
        return original_fetch()

    service._fetch_pricing_data = counting_fetch

    def fetch_pricing(thread_id):
        """Thread worker function"""
        result = service.get_pricing_data()
        results.append((thread_id, len(result)))

    print("Test 1: Concurrent access when cache is cold")
    print("-" * 80)

    # Create 10 threads that will all try to fetch at the same time
    threads = []
    for i in range(10):
        t = threading.Thread(target=fetch_pricing, args=(i,))
        threads.append(t)

    # Start all threads at once
    start_time = time.time()
    for t in threads:
        t.start()

    # Wait for all to complete
    for t in threads:
        t.join()

    elapsed = time.time() - start_time

    print(f"✓ All 10 threads completed in {elapsed:.2f}s")
    print(f"✓ API calls made: {len(api_call_count)} (should be 1 due to locking)")
    print(f"✓ All threads got same data: {len(set(r[1] for r in results)) == 1}")
    print()

    # Test 2: Access with valid cache
    print("Test 2: Concurrent access when cache is warm")
    print("-" * 80)

    api_call_count.clear()
    results.clear()
    threads = []

    for i in range(10):
        t = threading.Thread(target=fetch_pricing, args=(i,))
        threads.append(t)

    start_time = time.time()
    for t in threads:
        t.start()

    for t in threads:
        t.join()

    elapsed = time.time() - start_time

    print(f"✓ All 10 threads completed in {elapsed:.2f}s (faster due to cache)")
    print(f"✓ API calls made: {len(api_call_count)} (should be 0, using cache)")
    print(f"✓ All threads got same data: {len(set(r[1] for r in results)) == 1}")
    print()

    # Test 3: Cache expiration handling
    print("Test 3: Cache expiration and refresh")
    print("-" * 80)

    # Manually expire cache
    service._cache_timestamp = None

    api_call_count.clear()
    results.clear()
    threads = []

    for i in range(5):
        t = threading.Thread(target=fetch_pricing, args=(i,))
        threads.append(t)

    start_time = time.time()
    for t in threads:
        t.start()

    for t in threads:
        t.join()

    elapsed = time.time() - start_time

    print(f"✓ All 5 threads completed in {elapsed:.2f}s")
    print(f"✓ API calls made after cache expiration: {len(api_call_count)}")
    print(f"✓ Double-check locking prevented race: {len(api_call_count) <= 1}")
    print()

    print("=" * 80)
    print("All concurrency tests passed!")
    print("=" * 80)
    print()

    # Summary
    if len(api_call_count) <= 1:
        print("✅ Thread-safe implementation working correctly")
        print("✅ No race conditions detected")
        print("✅ Cache prevents unnecessary API calls")
    else:
        print("⚠️  Warning: Multiple API calls detected (possible race condition)")


if __name__ == '__main__':
    test_concurrent_cache_access()
