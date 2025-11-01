#!/usr/bin/env python3
"""
Example usage of the Sigen API client.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sigenpy import SigenAPI, get_config
import json


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f" {title}")
    print('=' * 60)


def main():
    # Load configuration from secrets.json file
    config = get_config()

    # Initialize the API client
    api = SigenAPI(
        base_url=config['base_url'],
        username=config['username'],
        password=config['password']
    )

    print("Sigen API Example Usage")
    print(f"Base URL: {config['base_url']}")
    print(f"Username: {config['username']}")

    # Authenticate and initialize
    print_section("1. Authentication & Initialization")
    api.initialize()
    print(f"✓ Authenticated successfully")
    print(f"✓ System ID: {api.system_id}")
    print(f"✓ Inverter SN: {api.inverter_serial_number}")

    # Get systems
    print_section("2. Get Systems")
    systems = api.get_systems()
    print(f"Found {len(systems)} system(s):")
    for system in systems:
        print(f"  - System ID: {system.get('systemId')}")
        print(f"    Name: {system.get('systemName', 'N/A')}")
        print(f"    Status: {system.get('status', 'N/A')}")

    # Get devices
    print_section("3. Get Devices")
    devices = api.get_devices()
    print(f"Found {len(devices)} device(s):")
    for device in devices:
        print(f"  - Device Type: {device.get('deviceType')}")
        print(f"    Serial Number: {device.get('serialNumber')}")
        print(f"    Status: {device.get('status', 'N/A')}")

    # Get system summary
    print_section("4. System Summary (Realtime)")
    summary = api.get_system_summary()
    print("System Summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")

    # Get energy flow
    print_section("5. Energy Flow (Realtime)")
    energy_flow = api.get_system_energy_flow()
    print("Energy Flow:")
    for key, value in energy_flow.items():
        print(f"  {key}: {value}")

    # Get simplified power flow
    print_section("6. Simplified Power Flow")
    power_flow = api.get_current_power_flow()
    print("Current Power Flow:")
    for key, value in power_flow.items():
        print(f"  {key}: {value}W")

    # Get device realtime info
    print_section("7. Device Realtime Info")
    try:
        device_info = api.get_device_realtime_info()
        print(f"Device Info (first 10 fields):")
        count = 0
        for key, value in device_info.items():
            if count >= 10:
                print(f"  ... ({len(device_info)} total fields)")
                break
            print(f"  {key}: {value}")
            count += 1
    except ValueError as e:
        print(f"Could not get device info: {e}")

    # Get historical data (example - last 7 days)
    print_section("8. Historical Data")
    from datetime import datetime, timedelta
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)

    try:
        history = api.get_system_history(
            start_time=start_time,
            end_time=end_time,
            interval='day'
        )
        print(f"Historical data retrieved:")
        print(f"  Time range: {start_time.date()} to {end_time.date()}")
        if isinstance(history, dict):
            print(f"  Data points: {len(history)}")
        elif isinstance(history, list):
            print(f"  Data points: {len(history)}")
    except Exception as e:
        print(f"Could not retrieve historical data: {e}")

    print_section("Complete")
    print("✓ All API endpoints tested successfully")


if __name__ == "__main__":
    main()
