#!/usr/bin/env python3
"""
Simple test script to authenticate and get system list from Sigen API.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sigenpy import SigenAPI, get_config
import json

def main():
    print("=" * 60)
    print("Testing Sigen API - Get Systems")
    print("=" * 60)

    # Load configuration from secrets.json file (one directory up)
    print("\n1. Loading configuration...")
    try:
        secrets_path = os.path.join(os.path.dirname(__file__), '..', 'secrets.json')
        config = get_config(secrets_path)
        print(f"✓ Config loaded successfully")
        print(f"  Base URL: {config['base_url']}")
        print(f"  Username: {config['username']}")
        print(f"  Region: {config.get('region', 'N/A')}")
    except Exception as e:
        print(f"✗ Failed to load config: {e}")
        return

    # Initialize API client
    print("\n2. Initializing API client...")
    api = SigenAPI(
        base_url=config['base_url'],
        username=config['username'],
        password=config['password']
    )
    print(f"✓ API client initialized")

    # Authenticate
    print("\n3. Authenticating...")
    try:
        token = api.login()
        print(f"✓ Authentication successful")
        print(f"  Access token: {token[:20]}...{token[-20:]}")
    except Exception as e:
        print(f"✗ Authentication failed: {e}")
        return

    # Get systems
    print("\n4. Fetching systems...")
    try:
        systems = api.get_systems()
        print(f"✓ Successfully retrieved {len(systems)} system(s)")
        print(f"  Cached system_id: {api.system_id}")

        print("\n" + "=" * 60)
        print("SYSTEM LIST")
        print("=" * 60)

        for idx, system in enumerate(systems, 1):
            print(f"\nSystem #{idx}:")
            print(json.dumps(system, indent=2))

    except Exception as e:
        print(f"✗ Failed to get systems: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n" + "=" * 60)
    print("TEST COMPLETED SUCCESSFULLY")
    print("=" * 60)

if __name__ == "__main__":
    main()
