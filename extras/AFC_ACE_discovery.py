# Armored Turtle Automated Filament Control - ACE Discovery
#
# Copyright (C) 2024 Armored Turtle
# ACE Discovery implementation adapted from KlipperACE by topeysoft
#
# This file may be distributed under the terms of the GNU GPLv3 license.

"""
ACE Pro Auto-Discovery
Handles USB enumeration and device identification
"""

import serial
import serial.tools.list_ports
import logging
import re
import os
import glob
import hashlib
from typing import List, Dict, Optional, Any
from .AFC_ACE_protocol import AceProtocol, ACE_VID, ACE_PID


class AceDiscovery:
    """Auto-detect ACE Pro devices on USB"""

    ACE_MANUFACTURER = "GDMicroelectronics"
    ACE_PRODUCT_NAME = "ACE"

    @staticmethod
    def sanitize_device_id(device_id: str) -> str:
        """
        Sanitize device_id to create a valid Python identifier.

        Replaces all non-alphanumeric characters (except underscores) with underscores.

        Args:
            device_id: Raw device identifier

        Returns:
            Sanitized device ID safe for use as Python variable name
        """
        return re.sub(r'[^a-zA-Z0-9_]', '_', device_id)

    @staticmethod
    def find_by_path_for_device(tty_device: str) -> Optional[str]:
        """
        Find /dev/serial/by-path symlink for a tty device.

        This provides stable device paths that don't change across reboots.

        Args:
            tty_device: Device path like /dev/ttyACM0

        Returns:
            str: Path like /dev/serial/by-path/platform-...-usb-0:1.3:1.0
            None: If no by-path symlink found or not on Linux
        """
        try:
            # Only available on Linux
            if not os.path.exists('/dev/serial/by-path'):
                return None

            # Get the real path of the tty device
            real_tty = os.path.realpath(tty_device)

            # Search all by-path symlinks
            by_path_pattern = "/dev/serial/by-path/*"
            for path in glob.glob(by_path_pattern):
                if os.path.realpath(path) == real_tty:
                    return path

            return None
        except Exception as e:
            logging.debug(f"AFC_ACE: Could not resolve by-path for {tty_device}: {e}")
            return None

    @staticmethod
    def find_by_id_for_device(tty_device: str) -> Optional[str]:
        """
        Find /dev/serial/by-id symlink for a tty device.

        Provides stable device identification based on USB device serial number.

        Args:
            tty_device: Device path like /dev/ttyACM0

        Returns:
            str: Path like /dev/serial/by-id/usb-ANYCUBIC_ACE_1-if00
            None: If no by-id symlink found or not on Linux
        """
        try:
            # Only available on Linux
            if not os.path.exists('/dev/serial/by-id'):
                return None

            # Get the real path of the tty device
            real_tty = os.path.realpath(tty_device)

            # Search all by-id symlinks
            by_id_pattern = "/dev/serial/by-id/*"
            for path in glob.glob(by_id_pattern):
                if os.path.realpath(path) == real_tty:
                    return path

            return None
        except Exception as e:
            logging.debug(f"AFC_ACE: Could not resolve by-id for {tty_device}: {e}")
            return None

    @staticmethod
    def _generate_device_id(device_info: Dict[str, Any]) -> str:
        """
        Generate device ID based on USB port location.

        This ensures the same physical USB port always maps to the same device ID,
        making lane assignments stable across reboots.

        Args:
            device_info: Device information dictionary

        Returns:
            Device ID string (e.g., 'hub_1_port_1_3')
        """
        # Always use USB location as the primary device ID
        if 'usb_location' in device_info and device_info['usb_location']:
            # USB location like "1-1.2" is stable as long as device stays in same port
            # Convert to readable format: "1-1.2" → "hub_1_port_1_2"
            usb_loc = device_info['usb_location']

            # Parse USB location format (e.g., "1-1.2" means bus 1, port 1.2)
            parts = usb_loc.split('-')
            if len(parts) >= 2:
                # Get the port path (everything after the bus number)
                port_path = parts[1]
                device_id = f"hub_{parts[0]}_port_{port_path}"
            else:
                # Fallback for simple format
                device_id = f"usb_{usb_loc}"

            # Sanitize to ensure valid Python identifier
            return AceDiscovery.sanitize_device_id(device_id)

        # Fallback: MAC address (if firmware provides it)
        if 'mac_address' in device_info and device_info['mac_address']:
            mac = device_info['mac_address']
            logging.info(f"AFC_ACE: Using MAC address for device_id (USB location not available)")
            return AceDiscovery.sanitize_device_id(f"mac_{mac}")

        # Fallback: Serial number (if firmware provides it)
        if 'serial_number' in device_info and device_info['serial_number']:
            sn = device_info['serial_number']
            logging.info(f"AFC_ACE: Using serial number for device_id (USB location not available)")
            return AceDiscovery.sanitize_device_id(f"sn_{sn}")

        # Last resort: Hash of firmware + model (NOT recommended)
        unique_str = f"{device_info.get('model', '')}_{device_info.get('firmware', '')}"
        hash_val = hashlib.md5(unique_str.encode()).hexdigest()[:8]
        logging.warning(f"AFC_ACE: Using firmware hash for device_id (not unique!)")
        return f"fw_{hash_val}"

    @staticmethod
    def find_ace_devices() -> List[Dict[str, Any]]:
        """
        Scan all USB serial ports and identify ACE devices.

        Returns:
            List of device info dictionaries
        """
        ace_devices = []
        ports = serial.tools.list_ports.comports()

        logging.info(f"AFC_ACE Discovery: Scanning {len(ports)} USB serial ports...")

        for port in ports:
            # Log all ports for debugging
            logging.debug(f"  Port: {port.device}")
            logging.debug(f"    VID:PID = 0x{port.vid:04X}:0x{port.pid:04X}" if port.vid and port.pid else "    VID:PID = None")
            logging.debug(f"    Manufacturer: {port.manufacturer}")
            logging.debug(f"    Product: {port.product}")
            logging.debug(f"    Serial: {port.serial_number}")
            logging.debug(f"    Location: {port.location}")

            # Method 1: VID/PID matching (most reliable)
            if port.vid == ACE_VID:
                logging.info(f"  ✓ Found ACE device by VID (0x{ACE_VID:04X}) at {port.device}")

                # Find stable by-path symlink (REQUIRED for Linux operation)
                by_path = AceDiscovery.find_by_path_for_device(port.device)

                if not by_path:
                    logging.warning(f"  ✗ No /dev/serial/by-path symlink found for {port.device}")
                    logging.warning(f"  Skipping device - by-path required for stable operation")
                    continue

                logging.info(f"  ✓ by-path: {by_path}")

                device_info = {
                    'port': by_path,  # Use by-path as the primary port
                    'port_tty': port.device,  # Keep ttyACM for reference/logging only
                    'hwid': port.hwid,
                    'serial_number': port.serial_number,
                    'manufacturer': port.manufacturer,
                    'product': port.product,
                    'vid': port.vid,
                    'pid': port.pid,
                    'location': port.location,  # USB hub location for stable ordering
                    'usb_location': port.location
                }

                # Generate device_id
                device_info['device_id'] = AceDiscovery._generate_device_id(device_info)
                ace_devices.append(device_info)

            # Method 2: Manufacturer/Product string matching (fallback)
            elif (port.manufacturer and AceDiscovery.ACE_MANUFACTURER.upper() in str(port.manufacturer).upper()) or \
                 (port.product and AceDiscovery.ACE_PRODUCT_NAME.upper() in str(port.product).upper()):
                logging.info(f"  ✓ Found ACE device by manufacturer/product string at {port.device}")

                # Find stable by-path symlink (REQUIRED for Linux operation)
                by_path = AceDiscovery.find_by_path_for_device(port.device)

                if not by_path:
                    logging.warning(f"  ✗ No /dev/serial/by-path symlink found for {port.device}")
                    logging.warning(f"  Skipping device - by-path required for stable operation")
                    continue

                logging.info(f"  ✓ by-path: {by_path}")

                device_info = {
                    'port': by_path,  # Use by-path as the primary port
                    'port_tty': port.device,  # Keep ttyACM for reference/logging only
                    'hwid': port.hwid,
                    'serial_number': port.serial_number,
                    'manufacturer': port.manufacturer,
                    'product': port.product,
                    'vid': port.vid,
                    'pid': port.pid,
                    'location': port.location,
                    'usb_location': port.location
                }

                # Generate device_id
                device_info['device_id'] = AceDiscovery._generate_device_id(device_info)
                ace_devices.append(device_info)

        # Sort by USB location for deterministic ordering
        ace_devices.sort(key=lambda x: x.get('location', '') or '')

        logging.info(f"AFC_ACE Discovery: Found {len(ace_devices)} ACE devices")
        return ace_devices

    @staticmethod
    def probe_ace_device(port: str, baud: int = 115200, timeout: float = 2.0) -> Optional[Dict[str, Any]]:
        """
        Connect to a port and verify it's an ACE device.

        Args:
            port: Serial port path
            baud: Baud rate (default 115200)
            timeout: Serial timeout (default 2.0s)

        Returns:
            Device info dict or None if not ACE
        """
        logging.info(f"AFC_ACE Probe: Attempting to probe {port} at {baud} baud...")

        try:
            # Create protocol handler and connect
            protocol = AceProtocol(port, baud, timeout)

            if not protocol.connect():
                logging.warning(f"AFC_ACE Probe: Failed to connect to {port}")
                return None

            # Send get_info command
            info = protocol.get_info()
            protocol.disconnect()

            if info:
                # Find stable by-path symlink (REQUIRED)
                by_path = AceDiscovery.find_by_path_for_device(port)

                if not by_path:
                    logging.warning(f"AFC_ACE Probe: ✗ No /dev/serial/by-path symlink found for {port}")
                    return None

                logging.info(f"AFC_ACE Probe: ✓ Successfully verified ACE device")
                logging.info(f"AFC_ACE Probe: Model: {info.get('model', 'Unknown')}, Firmware: {info.get('firmware', 'Unknown')}")
                logging.info(f"AFC_ACE Probe: by-path: {by_path} (tty: {port})")

                device_info = {
                    'port': by_path,  # by-path is the port
                    'port_tty': port,  # ttyACM for reference only
                    'model': info.get('model', 'Unknown'),
                    'firmware': info.get('firmware', 'Unknown'),
                    'serial_number': info.get('serial_number', None),
                    'mac_address': info.get('mac_address', None),
                    'num_lanes': 4  # ACE Pro has 4 lanes
                }

                return device_info
            else:
                logging.warning(f"AFC_ACE Probe: No response from {port}")
                return None

        except Exception as e:
            logging.error(f"AFC_ACE Probe: Error probing {port}: {e}")
            return None
