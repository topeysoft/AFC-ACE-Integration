# Armored Turtle Automated Filament Control - ACE Protocol
#
# Copyright (C) 2024 Armored Turtle
# ACE Protocol implementation adapted from KlipperACE by topeysoft
#
# This file may be distributed under the terms of the GNU GPLv3 license.

"""
ACE Pro USB Protocol Implementation
Handles JSON-RPC communication over serial with ACE Pro devices
"""

import struct
import json
import serial
import logging
import threading
from typing import Dict, Any, Optional, Tuple

# Protocol Constants
PROTOCOL_HEAD_BYTES = bytes([0xFF, 0xAA])
PROTOCOL_TAIL_BYTE = 0xFE
PROTOCOL_MIN_PACKET_SIZE = 7
CRC_INIT_VALUE = 0xFFFF

# ACE Device Constants
ACE_VID = 0x28E9  # GDMicroelectronics vendor ID
ACE_PID = 0x018A  # ACE product ID
LANES_PER_ACE = 4
DEFAULT_BAUD_RATE = 115200
DEFAULT_TIMEOUT = 2.0
REQUEST_TIMEOUT = 2.0


def calc_crc(buffer: bytes) -> int:
    """
    Calculate CRC16 for ACE protocol.

    Args:
        buffer: Payload bytes to calculate CRC for

    Returns:
        CRC16 value
    """
    _crc = CRC_INIT_VALUE
    for byte in buffer:
        data = byte
        data ^= _crc & 0xff
        data ^= (data & 0x0f) << 4
        _crc = ((data << 8) | (_crc >> 8)) ^ (data >> 4) ^ (data << 3)
    return _crc


class AcePacket:
    """
    ACE protocol packet encoder/decoder.

    Packet format:
    [HEAD(2)] [LEN(2)] [PAYLOAD(n)] [CRC(2)] [TAIL(1)]

    - HEAD: 0xFF 0xAA (2 bytes)
    - LEN: Payload length (2 bytes, little-endian)
    - PAYLOAD: JSON-encoded request/response
    - CRC: CRC16 of payload (2 bytes)
    - TAIL: 0xFE (1 byte)
    """

    @staticmethod
    def encode(request: Dict[str, Any]) -> bytes:
        """
        Encode JSON request to ACE protocol packet.

        Args:
            request: Dictionary containing JSON-RPC request

        Returns:
            Encoded packet bytes ready to send over serial
        """
        payload = json.dumps(request).encode('utf-8')

        data = PROTOCOL_HEAD_BYTES
        data += struct.pack('@H', len(payload))
        data += payload
        data += struct.pack('@H', calc_crc(payload))
        data += bytes([PROTOCOL_TAIL_BYTE])

        return data

    @staticmethod
    def decode(buffer: bytes) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Decode ACE protocol packet to JSON response.

        Args:
            buffer: Raw bytes received from serial port

        Returns:
            Tuple of (decoded_response, error_message)
            If successful, error_message is None
        """
        # Check minimum packet size
        if len(buffer) < PROTOCOL_MIN_PACKET_SIZE:
            return None, f"Packet too small: {len(buffer)} < {PROTOCOL_MIN_PACKET_SIZE}"

        # Validate header
        if buffer[0:2] != PROTOCOL_HEAD_BYTES:
            return None, f"Invalid protocol header: {buffer[0:2].hex()}"

        # Extract payload length
        payload_len = struct.unpack('<H', buffer[2:4])[0]

        # Check if we have complete packet
        expected_len = 4 + payload_len + 2 + 1  # header + len + payload + crc + tail
        if len(buffer) < expected_len:
            return None, f"Incomplete packet: expected {expected_len}, got {len(buffer)}"

        # Extract payload
        payload = buffer[4:4 + payload_len]

        # Validate CRC
        crc_data = buffer[4 + payload_len:4 + payload_len + 2]
        crc_calculated = struct.pack('@H', calc_crc(payload))

        if crc_data != crc_calculated:
            return None, f"CRC mismatch: expected {crc_calculated.hex()}, got {crc_data.hex()}"

        # Validate tail byte
        tail_byte = buffer[4 + payload_len + 2]
        if tail_byte != PROTOCOL_TAIL_BYTE:
            return None, f"Invalid tail byte: {tail_byte:02X}"

        # Decode JSON payload
        try:
            response = json.loads(payload.decode('utf-8'))
            return response, None
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            return None, f"JSON decode error: {e}"

    @staticmethod
    def find_packet_in_buffer(buffer: bytearray) -> Tuple[Optional[bytes], bytearray]:
        """
        Search for a complete packet in a buffer.

        Args:
            buffer: Accumulated bytes from serial reads

        Returns:
            Tuple of (packet_bytes, remaining_buffer)
            If no complete packet found, returns (None, buffer)
        """
        # Look for tail byte (end of packet marker)
        tail_index = buffer.find(PROTOCOL_TAIL_BYTE)

        if tail_index >= 0:
            # Found potential packet - extract it
            packet = bytes(buffer[:tail_index + 1])
            remaining = bytearray(buffer[tail_index + 1:])
            return packet, remaining

        # No complete packet yet
        return None, buffer


class AceProtocol:
    """
    ACE Pro USB protocol handler.
    Manages serial communication and command execution.
    """

    def __init__(self, port: str, baud: int = DEFAULT_BAUD_RATE, timeout: float = DEFAULT_TIMEOUT):
        """
        Initialize ACE protocol handler.

        Args:
            port: Serial port path (e.g., '/dev/ttyACM0' or '/dev/serial/by-path/...')
            baud: Baud rate (default 115200)
            timeout: Serial timeout in seconds
        """
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self.serial = None
        self._request_id = 0
        self.read_buffer = bytearray()
        self._lock = threading.Lock()  # Thread-safe access to serial port

    def connect(self) -> bool:
        """
        Open serial connection to ACE device.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Close existing connection if any
            if self.serial and self.serial.is_open:
                try:
                    self.serial.close()
                except:
                    pass

            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baud,
                timeout=self.timeout,
                write_timeout=self.timeout
                # Note: exclusive=True removed - can cause issues on some systems
            )

            # Clear any stale data in buffers
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()
            self.read_buffer = bytearray()

            logging.info(f"AFC_ACE: Connected to {self.port} at {self.baud} baud")

            # Give device time to stabilize after connection
            import time
            time.sleep(0.2)  # Increased from 0.1s to 0.2s

            return True
        except serial.SerialException as e:
            logging.error(f"AFC_ACE: Failed to connect to {self.port}: {e}")
            return False

    def disconnect(self):
        """Close serial connection"""
        if self.serial and self.serial.is_open:
            self.serial.close()
            logging.info(f"AFC_ACE: Disconnected from {self.port}")

    def _get_next_request_id(self) -> int:
        """Generate next request ID"""
        self._request_id = (self._request_id + 1) % 300000
        return self._request_id

    def send_command(self, method: str, params: Optional[Dict[str, Any]] = None, timeout: float = REQUEST_TIMEOUT) -> Optional[Dict[str, Any]]:
        """
        Send JSON-RPC command and wait for response.

        Args:
            method: JSON-RPC method name
            params: Optional parameters dictionary
            timeout: Response timeout in seconds

        Returns:
            Response dictionary or None on error
        """
        with self._lock:  # Ensure thread-safe serial access
            if not self.serial or not self.serial.is_open:
                logging.error("AFC_ACE: Serial port not open")
                return None

            # Build request
            request = {
                "id": self._get_next_request_id(),
                "method": method
            }
            if params:
                request["params"] = params

            # Encode and send
            packet = AcePacket.encode(request)

            try:
                # Small delay before sending to prevent overwhelming device
                import time
                time.sleep(0.05)

                self.serial.write(packet)
                self.serial.flush()

                # Wait for response
                import time
                start_time = time.time()

                while (time.time() - start_time) < timeout:
                    if self.serial.in_waiting > 0:
                        self.read_buffer += self.serial.read(self.serial.in_waiting)

                        # Try to extract packet
                        packet_bytes, self.read_buffer = AcePacket.find_packet_in_buffer(self.read_buffer)

                        if packet_bytes:
                            response, error = AcePacket.decode(packet_bytes)

                            if error:
                                logging.warning(f"AFC_ACE: Packet decode error: {error}")
                                continue

                            if response and 'result' in response:
                                return response['result']
                            elif response and 'error' in response:
                                logging.error(f"AFC_ACE: Command error: {response['error']}")
                                return None

                    time.sleep(0.05)

                logging.warning(f"AFC_ACE: Command '{method}' timed out after {timeout}s")
                return None

            except serial.SerialException as e:
                logging.error(f"AFC_ACE: Serial error during command '{method}': {e}")

                # Try to recover from I/O errors by reconnecting
                if "Input/output error" in str(e) or "[Errno 5]" in str(e):
                    logging.warning(f"AFC_ACE: Attempting to reconnect to {self.port}...")
                    self.disconnect()
                    if self.connect():
                        logging.info(f"AFC_ACE: Reconnected successfully, retrying command")
                        # Retry command once after reconnection
                        try:
                            packet = AcePacket.encode(request)
                            self.serial.write(packet)
                            self.serial.flush()

                            import time
                            start_time = time.time()
                            while (time.time() - start_time) < timeout:
                                if self.serial.in_waiting > 0:
                                    self.read_buffer += self.serial.read(self.serial.in_waiting)
                                    packet_bytes, self.read_buffer = AcePacket.find_packet_in_buffer(self.read_buffer)
                                    if packet_bytes:
                                        response, error = AcePacket.decode(packet_bytes)
                                        if error:
                                            continue
                                        if response and 'result' in response:
                                            return response['result']
                                        elif response and 'error' in response:
                                            return None
                                time.sleep(0.05)
                        except Exception as retry_error:
                            logging.error(f"AFC_ACE: Retry after reconnect failed: {retry_error}")
                    else:
                        logging.error(f"AFC_ACE: Reconnection failed")

                return None

    # ============================================================
    # ACE Commands
    # ============================================================

    def get_info(self) -> Optional[Dict[str, Any]]:
        """Get device information (model, firmware, etc.)"""
        return self.send_command("get_info")

    def get_status(self) -> Optional[Dict[str, Any]]:
        """Get device status (slots, dryer, temperature, etc.)"""
        return self.send_command("get_status")

    def feed(self, index: int, length: float, speed: int) -> bool:
        """
        Feed filament forward.

        Args:
            index: Lane index (0-3)
            length: Distance in mm
            speed: Speed (10-80)

        Returns:
            True if successful
        """
        result = self.send_command("feed", {
            "index": index,
            "len": int(length),
            "speed": speed
        })
        return result is not None

    def retract(self, index: int, length: float, speed: int) -> bool:
        """
        Retract filament backward.

        Args:
            index: Lane index (0-3)
            length: Distance in mm (positive value)
            speed: Speed (10-80)

        Returns:
            True if successful
        """
        result = self.send_command("back", {
            "index": index,
            "len": int(length),
            "speed": speed
        })
        return result is not None

    def set_feed_assist(self, index: int, enable: bool) -> bool:
        """
        Enable/disable feed assist for a lane.

        Args:
            index: Lane index (0-3)
            enable: True to enable, False to disable

        Returns:
            True if successful
        """
        method = "feed_assist" if enable else "feed_assist_off"
        params = {"index": index} if enable else None
        result = self.send_command(method, params)
        return result is not None

    def start_dryer(self, temp: int, duration: int = 240) -> bool:
        """
        Start dryer.

        Args:
            temp: Target temperature in Celsius
            duration: Duration in minutes (default 240)

        Returns:
            True if successful
        """
        result = self.send_command("dryer_start", {
            "temp": temp,
            "time": duration
        })
        return result is not None

    def stop_dryer(self) -> bool:
        """
        Stop dryer.

        Returns:
            True if successful
        """
        result = self.send_command("dryer_stop")
        return result is not None
