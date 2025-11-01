"""
Sigen API Client
A Python client for interacting with the Sigen Cloud API.
"""

import json
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime


class SigenAPI:
    """Client for interacting with the Sigen Cloud API."""

    def __init__(self, base_url: str, username: str, password: str):
        """
        Initialize the Sigen API client.

        Args:
            base_url: The base URL for the Sigen API (e.g., https://api-aus.sigencloud.com)
            username: Your Sigen account username
            password: Your Sigen account password
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.access_token: Optional[str] = None
        self.system_id: Optional[str] = None
        self.inverter_serial_number: Optional[str] = None

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make an HTTP request to the Sigen API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (will be appended to base_url)
            **kwargs: Additional arguments to pass to requests

        Returns:
            Parsed JSON response

        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        url = f"{self.base_url}{endpoint}"

        # Add authorization header if we have a token
        if self.access_token:
            headers = kwargs.get('headers', {})
            headers['Authorization'] = f'Bearer {self.access_token}'
            kwargs['headers'] = headers

        response = requests.request(method, url, **kwargs)
        response.raise_for_status()

        return response.json()

    def _parse_data_field(self, response: Dict[str, Any]) -> Any:
        """
        Parse the 'data' field from a Sigen API response.
        The data field is often a JSON string that needs to be parsed.

        Args:
            response: The API response dictionary

        Returns:
            Parsed data object
        """
        data = response.get('data')
        if isinstance(data, str):
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return data
        return data

    # Authentication Methods

    def login(self) -> str:
        """
        Authenticate with the Sigen API and obtain an access token.

        Returns:
            The access token

        Raises:
            requests.exceptions.RequestException: If authentication fails
        """
        endpoint = '/openapi/auth/login/password'
        payload = {
            'username': self.username,
            'password': self.password
        }
        headers = {'Content-Type': 'application/json'}

        response = self._make_request('POST', endpoint, json=payload, headers=headers)
        data = self._parse_data_field(response)

        self.access_token = data['accessToken']
        return self.access_token

    # Inventory Methods

    def get_systems(self) -> List[Dict[str, Any]]:
        """
        Get a list of all systems associated with the account.

        Returns:
            List of system dictionaries
        """
        endpoint = '/openapi/system'
        response = self._make_request('GET', endpoint)
        systems = self._parse_data_field(response)

        # Cache the first system ID for convenience
        if systems and len(systems) > 0:
            self.system_id = systems[0].get('systemId')

        return systems

    def get_devices(self, system_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get a list of all devices for a specific system.

        Args:
            system_id: The system ID (uses cached ID if not provided)

        Returns:
            List of device dictionaries
        """
        sys_id = system_id or self.system_id
        if not sys_id:
            raise ValueError("No system_id provided or cached. Call get_systems() first.")

        endpoint = f'/openapi/system/{sys_id}/devices'
        response = self._make_request('GET', endpoint)

        # Parse each device (they're JSON strings in the array)
        devices_data = response.get('data', [])
        devices = []

        for device_string in devices_data:
            if isinstance(device_string, str):
                device = json.loads(device_string)
            else:
                device = device_string
            devices.append(device)

            # Cache the first inverter serial number
            if device.get('deviceType') == 'Inverter' and not self.inverter_serial_number:
                self.inverter_serial_number = device.get('serialNumber')

        return devices

    # Realtime Data Methods

    def get_system_summary(self, system_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get realtime summary data for a system.

        Args:
            system_id: The system ID (uses cached ID if not provided)

        Returns:
            Dictionary containing system summary data
        """
        sys_id = system_id or self.system_id
        if not sys_id:
            raise ValueError("No system_id provided or cached. Call get_systems() first.")

        endpoint = f'/openapi/systems/{sys_id}/summary'
        response = self._make_request('GET', endpoint)
        return self._parse_data_field(response)

    def get_system_energy_flow(self, system_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get realtime energy flow data for a system.

        Args:
            system_id: The system ID (uses cached ID if not provided)

        Returns:
            Dictionary containing energy flow data
        """
        sys_id = system_id or self.system_id
        if not sys_id:
            raise ValueError("No system_id provided or cached. Call get_systems() first.")

        endpoint = f'/openapi/systems/{sys_id}/energyFlow'
        response = self._make_request('GET', endpoint)
        return self._parse_data_field(response)

    def get_device_realtime_info(self,
                                  device_serial_number: Optional[str] = None,
                                  system_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get realtime information for a specific device.

        Args:
            device_serial_number: The device serial number (uses cached inverter SN if not provided)
            system_id: The system ID (uses cached ID if not provided)

        Returns:
            Dictionary containing device realtime information
        """
        sys_id = system_id or self.system_id
        dev_sn = device_serial_number or self.inverter_serial_number

        if not sys_id:
            raise ValueError("No system_id provided or cached. Call get_systems() first.")
        if not dev_sn:
            raise ValueError("No device_serial_number provided or cached. Call get_devices() first.")

        endpoint = f'/openapi/systems/{sys_id}/devices/{dev_sn}/realtimeInfo'
        response = self._make_request('GET', endpoint)
        return self._parse_data_field(response)

    # Historical Data Methods

    def get_system_history(self,
                          system_id: Optional[str] = None,
                          start_time: Optional[datetime] = None,
                          end_time: Optional[datetime] = None,
                          interval: Optional[str] = None) -> Dict[str, Any]:
        """
        Get historical data for a system.

        Args:
            system_id: The system ID (uses cached ID if not provided)
            start_time: Start time for historical data
            end_time: End time for historical data
            interval: Data interval (e.g., '5min', 'hour', 'day')

        Returns:
            Dictionary containing historical data
        """
        sys_id = system_id or self.system_id
        if not sys_id:
            raise ValueError("No system_id provided or cached. Call get_systems() first.")

        endpoint = f'/openapi/systems/{sys_id}/history'

        # Build query parameters
        params = {}
        if start_time:
            params['startTime'] = start_time.isoformat()
        if end_time:
            params['endTime'] = end_time.isoformat()
        if interval:
            params['interval'] = interval

        response = self._make_request('GET', endpoint, params=params)
        return self._parse_data_field(response)

    # Convenience Methods

    def initialize(self) -> 'SigenAPI':
        """
        Perform initial setup: login and fetch system/device info.

        Returns:
            Self for method chaining
        """
        self.login()
        self.get_systems()
        if self.system_id:
            self.get_devices()
        return self

    def get_current_power_flow(self, system_id: Optional[str] = None) -> Dict[str, float]:
        """
        Get simplified current power flow information.

        Args:
            system_id: The system ID (uses cached ID if not provided)

        Returns:
            Dictionary with power flow values in watts
        """
        energy_flow = self.get_system_energy_flow(system_id)

        # Extract relevant power values (adjust keys based on actual API response)
        power_flow = {}
        for key, value in energy_flow.items():
            if 'power' in key.lower() or 'watt' in key.lower():
                try:
                    power_flow[key] = float(value)
                except (ValueError, TypeError):
                    power_flow[key] = value

        return power_flow

    def __repr__(self) -> str:
        """String representation of the API client."""
        auth_status = "authenticated" if self.access_token else "not authenticated"
        system_info = f"system_id={self.system_id}" if self.system_id else "no system"
        return f"SigenAPI(base_url={self.base_url}, {auth_status}, {system_info})"
