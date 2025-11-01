#!/usr/bin/env python3
"""
Real-time Energy Flow Display with ANSI Colors
Displays the current energy flow data with color-coded values.
Refreshes every 10 seconds.
"""

import sys
import os
import time
from datetime import datetime
from io import StringIO

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sigenpy import SigenAPI, get_config


# Configuration
REFRESH_INTERVAL_SECONDS = 10


# ANSI Color codes and cursor control
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'

    # Regular colors
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'

    # Background colors
    BG_BLACK = '\033[40m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_RED = '\033[41m'

    # Cursor control
    CURSOR_HOME = '\033[H'  # Move cursor to home position
    CLEAR_SCREEN = '\033[2J'  # Clear entire screen
    HIDE_CURSOR = '\033[?25l'  # Hide cursor
    SHOW_CURSOR = '\033[?25h'  # Show cursor


def clear_screen():
    """Clear the terminal screen using ANSI codes."""
    print(Colors.CURSOR_HOME + Colors.CLEAR_SCREEN, end='', flush=True)


def format_power(value, unit='kW', power_type='default'):
    """
    Format power value with appropriate color based on direction and magnitude.

    Args:
        value: Power value (in kW or kWh as returned by API)
        unit: Unit string (default 'kW')
        power_type: Type of power - 'solar', 'grid', 'battery', 'ev', 'load', 'heatpump', 'default'

    Returns:
        Formatted colored string
    """
    try:
        val = float(value)
    except (ValueError, TypeError):
        return f"{Colors.GRAY}{value}{Colors.RESET}"

    # Avoid displaying -0.00 by treating very small negative values as zero
    if abs(val) <= 0.01:  # Smaller than what would round to 0.01
        val = 0.0

    # Determine color based on power type and value
    if power_type in ['solar']:
        # Solar: always zero (gray) or positive (green)
        if val > 0.1:
            color = Colors.GREEN if val <= 1.0 else Colors.GREEN + Colors.BOLD
        else:
            color = Colors.GRAY
    elif power_type in ['load', 'heatpump']:
        # Load/Heat Pump: always zero (gray) or positive (red)
        if val > 0.1:
            color = Colors.RED if val <= 1.0 else Colors.RED + Colors.BOLD
        else:
            color = Colors.GRAY
    elif power_type == 'ev':
        # EV: positive (red), zero (gray), negative (green)
        if val > 0.1:
            color = Colors.RED if val <= 1.0 else Colors.RED + Colors.BOLD
        elif val < -0.1:
            color = Colors.GREEN if val >= -1.0 else Colors.GREEN + Colors.BOLD
        else:
            color = Colors.GRAY
    else:
        # Grid/Battery/Default: positive (green), zero (gray), negative (red)
        if val > 0.1:
            color = Colors.GREEN if val <= 1.0 else Colors.GREEN + Colors.BOLD
        elif val < -0.1:
            color = Colors.RED if val >= -1.0 else Colors.RED + Colors.BOLD
        else:
            color = Colors.GRAY

    return f"{color}{val:>7.2f} {unit}{Colors.RESET}"


def get_status_description(value, power_type):
    """
    Get status description for power values.

    Args:
        value: Power value (in kW)
        power_type: Type of power - 'solar', 'grid', 'battery'

    Returns:
        Status description string or empty string
    """
    try:
        val = float(value)
    except (ValueError, TypeError):
        return ""

    # Avoid displaying status for very small values
    if abs(val) <= 0.01:  
        val = 0.0

    if power_type == 'solar':
        if val > 0.1:
            return f"{Colors.GREEN}Generating{Colors.RESET}"
        else:
            return f"{Colors.GRAY}Idle{Colors.RESET}"
    elif power_type == 'grid':
        # Grid: positive = exporting, negative = importing
        if val > 0.1:
            return f"{Colors.GREEN}Exporting{Colors.RESET}"
        elif val < -0.1:
            return f"{Colors.RED}Importing{Colors.RESET}"
        else:
            return f"{Colors.GRAY}Idle{Colors.RESET}"
    elif power_type == 'battery':
        # Battery: positive = charging, negative = discharging
        if val > 0.1:
            return f"{Colors.GREEN}Charging{Colors.RESET}"
        elif val < -0.1:
            return f"{Colors.RED}Discharging{Colors.RESET}"
        else:
            return f"{Colors.GRAY}Idle{Colors.RESET}"
    else:
        return ""


def calculate_solar_power(energy_flow):
    """
    Calculate solar power from energy balance if API reports 0.00.

    Energy balance: Solar = Grid + Battery + Load + EV + HeatPump
    - Grid positive = exporting (solar going to grid)
    - Battery positive = charging (solar going to battery)
    - Load, EV, HeatPump positive = consuming (solar powering them)

    Args:
        energy_flow: Energy flow data dictionary

    Returns:
        Calculated solar power value or None if calculation not possible
    """
    try:
        pv_power = float(energy_flow.get('pvPower', 0))

        # Only calculate if pvPower is exactly zero
        if pv_power == 0.0:
            grid = float(energy_flow.get('gridPower', 0))
            battery = float(energy_flow.get('batteryPower', 0))
            load = float(energy_flow.get('loadPower', 0))
            ev = float(energy_flow.get('evPower', 0))
            heat_pump = float(energy_flow.get('heatPumpPower', 0))

            # Solar = Grid + Battery + Load + EV + HeatPump
            calculated_solar = grid + battery + load + ev + heat_pump

            # Return calculated value if it's positive (or zero)
            if calculated_solar > 0.0:
                return calculated_solar

    except (ValueError, TypeError, KeyError):
        pass

    return None


def format_percentage(value):
    """
    Format percentage value with color gradient.

    Args:
        value: Percentage value (0-100)

    Returns:
        Formatted colored string
    """
    try:
        val = float(value)
    except (ValueError, TypeError):
        return f"{Colors.GRAY}{value}%{Colors.RESET}"

    if val > 80:
        color = Colors.GREEN + Colors.BOLD
    elif val > 50:
        color = Colors.GREEN
    elif val > 20:
        color = Colors.YELLOW
    else:
        color = Colors.RED

    # Create a simple bar
    bar_length = 20
    filled = int(bar_length * val / 100)
    bar = '█' * filled + '░' * (bar_length - filled)

    return f"{color}{bar} {val:>5.1f}%{Colors.RESET}"


def build_display(api, energy_flow, seconds_until_refresh=None, last_update_time=None):
    """
    Build the entire display as a string buffer.
    This minimizes the time between clearing and redrawing.

    Args:
        api: SigenAPI instance
        energy_flow: Energy flow data dictionary
        seconds_until_refresh: Optional countdown value for refresh timer
        last_update_time: Timestamp of last successful data update

    Returns:
        String containing the complete display
    """
    output = StringIO()

    # Header
    output.write(f"{Colors.CYAN}{Colors.BOLD}{'=' * 75}{Colors.RESET}\n")
    output.write(f"{Colors.CYAN}{Colors.BOLD}  SIGEN ENERGY FLOW MONITOR{Colors.RESET}\n")
    output.write(f"{Colors.CYAN}{Colors.BOLD}{'=' * 75}{Colors.RESET}\n")
    output.write(f"{Colors.GRAY}  System ID: {api.system_id}{Colors.RESET}\n")
    output.write(f"{Colors.GRAY}  Inverter: {api.inverter_serial_number}{Colors.RESET}\n")

    # Display update time with age indicator if stale
    if last_update_time:
        time_since_update = (datetime.now() - last_update_time).total_seconds()
        update_str = f"Updated: {last_update_time.strftime('%Y-%m-%d %H:%M:%S')}"

        if time_since_update > 60:
            # Calculate time ago
            minutes_ago = int(time_since_update / 60)
            if minutes_ago == 1:
                time_ago_str = f"{Colors.BOLD}{Colors.WHITE} ({minutes_ago} minute ago){Colors.RESET}"
            else:
                time_ago_str = f"{Colors.BOLD}{Colors.WHITE} ({minutes_ago} minutes ago){Colors.RESET}"
            output.write(f"{Colors.GRAY}  {update_str}{time_ago_str}\n")
        else:
            output.write(f"{Colors.GRAY}  {update_str}{Colors.RESET}\n")
    else:
        output.write(f"{Colors.GRAY}  Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}\n")

    output.write(f"{Colors.CYAN}{'=' * 75}{Colors.RESET}\n\n")

    # Battery SOC section (separate panel with wider bar)
    if 'batterySoc' in energy_flow:
        output.write(f"{Colors.BOLD}{Colors.CYAN}┌─ BATTERY STATE OF CHARGE ───────────────────────────────────────────────┐{Colors.RESET}\n")
        output.write(f"{Colors.CYAN}│{Colors.RESET}\n")
        soc_value = energy_flow['batterySoc']
        try:
            soc = float(soc_value)
            # Wider bar (50 characters)
            bar_length = 50
            filled = int(bar_length * soc / 100)
            bar = '█' * filled + '░' * (bar_length - filled)

            # Color based on charge level
            if soc > 80:
                color = Colors.GREEN + Colors.BOLD
            elif soc > 50:
                color = Colors.GREEN
            elif soc > 20:
                color = Colors.YELLOW
            else:
                color = Colors.RED

            output.write(f"{Colors.CYAN}│{Colors.RESET}   {color}{bar} {soc:>5.1f}%{Colors.RESET}\n")
        except (ValueError, TypeError):
            output.write(f"{Colors.CYAN}│{Colors.RESET}   {Colors.GRAY}Unable to display SOC{Colors.RESET}\n")

        output.write(f"{Colors.CYAN}│{Colors.RESET}\n")
        output.write(f"{Colors.BOLD}{Colors.CYAN}└─────────────────────────────────────────────────────────────────────────┘{Colors.RESET}\n\n")

    # Energy Flow section
    output.write(f"{Colors.BOLD}{Colors.BLUE}┌─ ENERGY FLOW ───────────────────────────────────────────────────────────┐{Colors.RESET}\n")
    output.write(f"{Colors.BLUE}│{Colors.RESET}\n")

    # Define field order and their power types
    field_order = [
        ('pvPower', 'Solar Power', 'kW', 'solar'),
        ('batteryPower', 'Battery Power', 'kW', 'battery'),
        ('gridPower', 'Grid Power', 'kW', 'grid'),
        ('loadPower', 'Load Consumption', 'kW', 'load'),
        ('evPower', 'EV Power', 'kW', 'ev'),
        ('heatPumpPower', 'Heat Pump Power', 'kW', 'heatpump'),
        ('batteryCapacity', 'Battery Capacity', 'kWh', 'default'),
    ]

    for key, label, unit, ptype in field_order:
        if key in energy_flow:
            value = energy_flow[key]

            # Use calculated solar power if API reports 0.00
            if key == 'pvPower':
                calculated = calculate_solar_power(energy_flow)
                if calculated is not None:
                    value = calculated

            formatted_value = format_power(value, unit, ptype)
            status = get_status_description(value, ptype)
            if status:
                output.write(f"{Colors.BLUE}│{Colors.RESET}   {label:<30} {formatted_value}   {status}\n")
            else:
                output.write(f"{Colors.BLUE}│{Colors.RESET}   {label:<30} {formatted_value}\n")

    # Display any unknown fields
    displayed_keys = [k for k, _, _, _ in field_order] + ['batterySoc']
    for key, value in energy_flow.items():
        if key not in displayed_keys:
            output.write(f"{Colors.BLUE}│{Colors.RESET}   {Colors.GRAY}{key:<30} {value}{Colors.RESET}\n")

    output.write(f"{Colors.BLUE}│{Colors.RESET}\n")
    output.write(f"{Colors.BOLD}{Colors.BLUE}└─────────────────────────────────────────────────────────────────────────┘{Colors.RESET}\n\n")

    # Footer
    if seconds_until_refresh is not None:
        output.write(f"{Colors.GRAY}Press Ctrl+C to exit | Refreshing in {seconds_until_refresh} seconds...{Colors.RESET}\n")
    else:
        output.write(f"{Colors.GRAY}Press Ctrl+C to exit{Colors.RESET}\n")

    return output.getvalue()


def main():
    # Load configuration
    config = get_config()

    # Initialize API
    api = SigenAPI(
        base_url=config['base_url'],
        username=config['username'],
        password=config['password']
    )

    # Authenticate
    print(f"{Colors.YELLOW}Authenticating...{Colors.RESET}")
    api.initialize()
    print(f"{Colors.GREEN}✓ Connected to Sigen API{Colors.RESET}\n")
    time.sleep(1)

    # Clear screen and hide cursor for cleaner display
    clear_screen()
    print(Colors.HIDE_CURSOR, end='', flush=True)

    # Main loop
    last_valid_energy_flow = None
    last_update_time = None

    try:
        while True:
            # Get fresh data (do this BEFORE clearing screen to minimize blank time)
            try:
                energy_flow = api.get_system_energy_flow()

                # Validate that we got data and it's not empty/None
                if energy_flow and isinstance(energy_flow, dict) and len(energy_flow) > 0:
                    # Check if values are valid (not all None)
                    has_valid_data = any(v is not None for v in energy_flow.values())

                    if has_valid_data:
                        # Update our cached data and timestamp
                        last_valid_energy_flow = energy_flow
                        last_update_time = datetime.now()
                    # else: keep old values, don't update timestamp

                # If we don't have any valid data yet, skip this iteration
                if last_valid_energy_flow is None:
                    raise Exception("No valid data received yet")

                # Display with countdown (using last valid data)
                for countdown in range(REFRESH_INTERVAL_SECONDS, 0, -1):
                    # Build the complete display in memory with countdown
                    display_content = build_display(api, last_valid_energy_flow, countdown, last_update_time)

                    # Clear and redraw
                    clear_screen()

                    # Write all at once with a single flush
                    print(display_content, end='', flush=True)

                    # Wait 1 second before updating countdown
                    time.sleep(1)

            except Exception as e:
                # If we have old data, keep displaying it
                if last_valid_energy_flow is not None:
                    for countdown in range(REFRESH_INTERVAL_SECONDS, 0, -1):
                        display_content = build_display(api, last_valid_energy_flow, countdown, last_update_time)
                        clear_screen()
                        print(display_content, end='', flush=True)
                        time.sleep(1)
                else:
                    # No data at all yet, show error
                    clear_screen()
                    print(f"{Colors.RED}Error fetching data: {e}{Colors.RESET}", flush=True)
                    time.sleep(REFRESH_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        # Show cursor again before exiting
        print(Colors.SHOW_CURSOR, end='', flush=True)
        print(f"\n\n{Colors.YELLOW}Exiting...{Colors.RESET}")
        sys.exit(0)
    finally:
        # Ensure cursor is shown even if something goes wrong
        print(Colors.SHOW_CURSOR, end='', flush=True)


if __name__ == "__main__":
    main()
