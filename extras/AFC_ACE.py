# Armored Turtle Automated Filament Control - ACE Unit
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.

"""
ACE Pro Unit Driver for AFC
Implements AFC unit interface for ACE Pro hardware
"""

import traceback
import logging
from configparser import Error as error
from datetime import datetime

try: from extras.AFC_utils import ERROR_STR
except: raise error("Error when trying to import AFC_utils.ERROR_STR\n{trace}".format(trace=traceback.format_exc()))

try: from extras.AFC_lane import AFCLaneState
except: raise error(ERROR_STR.format(import_lib="AFC_lane", trace=traceback.format_exc()))

try: from extras.AFC_unit import afcUnit
except: raise error(ERROR_STR.format(import_lib="AFC_unit", trace=traceback.format_exc()))

try: from extras.AFC_ACE_protocol import AceProtocol
except: raise error(ERROR_STR.format(import_lib="AFC_ACE_protocol", trace=traceback.format_exc()))

try: from extras.AFC_ACE_discovery import AceDiscovery
except: raise error(ERROR_STR.format(import_lib="AFC_ACE_discovery", trace=traceback.format_exc()))


class afcACE(afcUnit):
    """
    ACE Pro unit driver for AFC.

    Implements the AFC unit interface to control ACE Pro hardware via USB protocol.
    Each ACE device provides 4 lanes (slots).
    """

    def __init__(self, config):
        """
        Initialize ACE unit.

        Args:
            config: Klipper configuration object
        """
        super().__init__(config)
        self.type = config.get('type', 'ACE')  # Changed from ACE_Pro to ACE to match class name AFC_ACE

        # ACE does NOT use a hub - it manages filament internally
        # Override the hub parameter from base class to prevent hub lookup errors
        self.hub = None

        # Create mock hub object to prevent lanes from auto-assigning to other hubs
        # AFC lanes check unit.hub_obj and auto-assign to first available hub if None
        class MockHub:
            def __init__(self):
                self.state = True  # Always "triggered" - ACE manages filament internally
                self.name = None   # No actual hub name
                self.lanes = {}    # Lanes will register here instead of real hub

        self.hub_obj = MockHub()

        # ACE-specific configuration
        self.serial = config.get('serial', None)
        self.auto_detect = config.getboolean('auto_detect', False)
        self.device_index = config.getint('device_index', 0)
        self.baud = config.getint('baud', 115200)

        # ACE protocol handler
        self.protocol = None
        self.device_id = None
        self.device_info = None

        # Lane to ACE slot mapping (AFC lane → ACE slot index)
        # ACE has 4 slots (0-3), each becomes a lane in AFC
        self.lane_to_slot = {}  # {lane_name: slot_index}

        # Status tracking
        self.last_status = None
        self.connected = False

        logging.info(f"AFC_ACE: Initialized unit '{self.name}'")

    def handle_connect(self):
        """
        Handle the connection event.
        Called when the printer connects.
        """
        super().handle_connect()

        # Set up ASCII art logo for AFC
        self.logo = '<span class=success--text> ___   _____  _____\n'
        self.logo += 'A   | |     || |   \n'
        self.logo += 'C---| | |---|| |---\n'
        self.logo += 'E   | |_____||_____|\n'
        self.logo += '  ' + self.name + '\n'

        self.logo_error = '<span class=error--text>E  _ _   _ _\n'
        self.logo_error += 'R |_|_|_|_|_|\n'
        self.logo_error += 'R |   ACE    |\n'
        self.logo_error += 'O |   ERROR  |\n'
        self.logo_error += 'R |  <span class=secondary--text>X</span>       |\n'
        self.logo_error += '! |_________|\n'
        self.logo_error += '  ' + self.name + '\n'

        # Connect to ACE device
        self._connect_ace()

        # Note: Lane mapping is built lazily in get_slot_for_lane()
        # because lanes aren't registered to the unit until after handle_connect()

    def _connect_ace(self):
        """Connect to ACE Pro device via USB"""
        try:
            # Auto-detect or use configured serial port
            if self.auto_detect:
                logging.info(f"AFC_ACE: Auto-detecting ACE devices...")
                devices = AceDiscovery.find_ace_devices()

                if not devices:
                    raise error(f"AFC_ACE: No ACE devices found during auto-detection")

                if self.device_index >= len(devices):
                    raise error(f"AFC_ACE: Device index {self.device_index} out of range (found {len(devices)} devices)")

                device = devices[self.device_index]
                self.serial = device['port']
                self.device_id = device['device_id']

                logging.info(f"AFC_ACE: Auto-detected device {self.device_index}: {self.serial} (ID: {self.device_id})")

            # Validate serial port
            if not self.serial:
                raise error(f"AFC_ACE: No serial port configured for unit '{self.name}'. Set 'serial' or enable 'auto_detect'")

            # Create protocol handler
            self.protocol = AceProtocol(self.serial, self.baud)

            # Connect
            if not self.protocol.connect():
                raise error(f"AFC_ACE: Failed to connect to {self.serial}")

            # Get device info
            self.device_info = self.protocol.get_info()

            if not self.device_info:
                raise error(f"AFC_ACE: Failed to get device info from {self.serial}")

            self.connected = True

            model = self.device_info.get('model', 'Unknown')
            firmware = self.device_info.get('firmware', 'Unknown')

            logging.info(f"AFC_ACE: ✓ Connected to {model} (FW: {firmware}) at {self.serial}")

            # Get initial status (with delay to allow device to be ready)
            import time
            time.sleep(0.2)
            self.last_status = self.protocol.get_status()

            if not self.last_status:
                logging.warning(f"AFC_ACE: Could not get initial status from {self.serial}, will retry later")

        except Exception as e:
            logging.error(f"AFC_ACE: Connection error: {e}")
            raise error(f"AFC_ACE: Failed to connect to ACE device: {e}")

    def _build_lane_mapping(self):
        """Build mapping between AFC lanes and ACE slots"""
        # Each lane in this unit corresponds to an ACE slot (0-3)
        # Lanes are registered with unit like "unit_name:slot_index"

        if not self.lanes:
            logging.debug(f"AFC_ACE: No lanes registered yet for unit '{self.name}', skipping mapping")
            return

        for lane in self.lanes.values():
            # Extract slot index from lane's unit specification
            # Lane config: unit: ace1:0  means slot 0 of unit ace1
            slot_index = lane.index  # This comes from unit:index in config

            self.lane_to_slot[lane.name] = slot_index

            logging.info(f"AFC_ACE: Mapped lane '{lane.name}' → slot {slot_index}")

    def get_slot_for_lane(self, lane) -> int:
        """
        Get ACE slot index for a lane.

        Args:
            lane: AFC lane object or lane name

        Returns:
            ACE slot index (0-3)
        """
        # Build mapping lazily if not done yet
        if not self.lane_to_slot and self.lanes:
            self._build_lane_mapping()

        lane_name = lane if isinstance(lane, str) else lane.name

        if lane_name not in self.lane_to_slot:
            raise error(f"AFC_ACE: Lane '{lane_name}' not mapped to ACE slot")

        return self.lane_to_slot[lane_name]

    def move_lane(self, lane, distance: float, speed: int, assist: bool = False):
        """
        Move filament in a lane.

        This is called by AFC lane.move() operations.
        Translates to ACE feed/retract commands.

        Args:
            lane: AFC lane object
            distance: Distance in mm (positive=feed, negative=retract)
            speed: Speed (10-80)
            assist: Enable feed assist during move
        """
        slot = self.get_slot_for_lane(lane)

        # Clamp speed to ACE limits (10-80)
        speed = max(10, min(80, int(speed)))

        try:
            if distance > 0:
                # Feed forward
                logging.debug(f"AFC_ACE: Feed slot {slot} distance {distance}mm speed {speed}")

                if assist:
                    self.protocol.set_feed_assist(slot, True)

                success = self.protocol.feed(slot, distance, speed)

                if not success:
                    logging.error(f"AFC_ACE: Feed command failed for slot {slot}")

            else:
                # Retract backward
                logging.debug(f"AFC_ACE: Retract slot {slot} distance {abs(distance)}mm speed {speed}")

                success = self.protocol.retract(slot, abs(distance), speed)

                if not success:
                    logging.error(f"AFC_ACE: Retract command failed for slot {slot}")

        except Exception as e:
            logging.error(f"AFC_ACE: Error moving lane '{lane.name}': {e}")
            raise

    def get_lane_status(self, lane) -> str:
        """
        Get status of a lane.

        Args:
            lane: AFC lane object

        Returns:
            Status string ('empty', 'ready', 'error', etc.)
        """
        slot = self.get_slot_for_lane(lane)

        try:
            # Get status from ACE
            status = self.protocol.get_status()

            if status and 'slots' in status:
                slot_status = status['slots'][slot]['status']

                # Map ACE status to AFC lane state
                # ACE statuses: 'empty', 'ready', 'loading', 'error'
                return slot_status

            return 'unknown'

        except Exception as e:
            logging.error(f"AFC_ACE: Error getting lane status: {e}")
            return 'error'

    def enable_feed_assist(self, lane, enable: bool = True):
        """
        Enable/disable feed assist for a lane.

        Args:
            lane: AFC lane object
            enable: True to enable, False to disable
        """
        slot = self.get_slot_for_lane(lane)

        try:
            success = self.protocol.set_feed_assist(slot, enable)

            if success:
                logging.debug(f"AFC_ACE: Feed assist {'enabled' if enable else 'disabled'} for slot {slot}")
            else:
                logging.warning(f"AFC_ACE: Failed to set feed assist for slot {slot}")

        except Exception as e:
            logging.error(f"AFC_ACE: Error setting feed assist: {e}")

    def start_dryer(self, temp: int, duration: int = 240):
        """
        Start ACE dryer.

        Args:
            temp: Target temperature in Celsius
            duration: Duration in minutes (default 240)
        """
        try:
            success = self.protocol.start_dryer(temp, duration)

            if success:
                logging.info(f"AFC_ACE: Dryer started at {temp}°C for {duration} minutes")
            else:
                logging.warning(f"AFC_ACE: Failed to start dryer")

        except Exception as e:
            logging.error(f"AFC_ACE: Error starting dryer: {e}")

    def stop_dryer(self):
        """Stop ACE dryer"""
        try:
            success = self.protocol.stop_dryer()

            if success:
                logging.info(f"AFC_ACE: Dryer stopped")
            else:
                logging.warning(f"AFC_ACE: Failed to stop dryer")

        except Exception as e:
            logging.error(f"AFC_ACE: Error stopping dryer: {e}")

    def system_Test(self, cur_lane, delay, assignTcmd, enable_movement):
        """
        System test for ACE lane.

        This is called by AFC's PREP command to test lanes.
        For ACE, we query the device status instead of physical sensor tests.

        Args:
            cur_lane: Lane to test
            delay: Delay between test steps
            assignTcmd: Whether to assign T command
            enable_movement: Whether to enable movement (for ACE, we just query status)
        """
        # Ensure lane mapping is built (lazy initialization)
        if not self.lane_to_slot and self.lanes:
            self._build_lane_mapping()

        msg = ''
        succeeded = True

        slot = self.get_slot_for_lane(cur_lane)

        try:
            # Get ACE slot status
            status = self.protocol.get_status()

            if not status or 'slots' not in status:
                # Communication error - but don't fail entirely, mark lane as unknown
                logging.warning(f"AFC_ACE: Could not get status for lane '{cur_lane.name}' (slot {slot})")
                self.afc.function.afc_led(cur_lane.led_not_ready, cur_lane.led_index)
                msg = "<span class=warning--text>UNKNOWN (Communication Error)</span>"
                cur_lane.status = AFCLaneState.NONE
                cur_lane.prep_state = True  # Set prep_state (exposed as 'prep' in API)
                cur_lane.load_state = True  # Set load_state (exposed as 'load' in API)
                logging.info(f"AFC_ACE: Set lane '{cur_lane.name}' prep_state={cur_lane.prep_state} load_state={cur_lane.load_state}")
                succeeded = True  # Don't fail prep for communication errors
                return msg, succeeded

            slot_info = status['slots'][slot]
            slot_status = slot_info['status']

            # Map ACE status to AFC states
            if slot_status == 'empty':
                self.afc.function.afc_led(cur_lane.led_not_ready, cur_lane.led_index)
                msg = 'EMPTY READY FOR SPOOL'
                cur_lane.status = AFCLaneState.NONE
                cur_lane.prep_state = True  # Lane is prepped (empty, ready for spool)
                cur_lane.load_state = True
                succeeded = True

            elif slot_status == 'ready':
                self.afc.function.afc_led(cur_lane.led_ready, cur_lane.led_index)
                msg = "<span class=success--text>LOCKED AND LOADED</span>"
                cur_lane.status = AFCLaneState.LOADED
                cur_lane.prep_state = True  # Lane is prepped (filament loaded and ready)
                cur_lane.load_state = True
                succeeded = True

                # Illuminate spool LED
                self.afc.function.afc_led(cur_lane.led_spool_illum, cur_lane.led_spool_index)

                # Check if loaded into toolhead
                if cur_lane.tool_loaded:
                    if cur_lane.extruder_obj and cur_lane.extruder_obj.lane_loaded == cur_lane.name:
                        self.afc.current = cur_lane.name
                        msg += "<span class=primary--text> in ToolHead</span>"

                        if self.afc.function.get_current_lane() == cur_lane.name:
                            self.afc.spool.set_active_spool(cur_lane.spool_id)
                            cur_lane.unit_obj.lane_tool_loaded(cur_lane)
                            cur_lane.status = AFCLaneState.TOOLED

            elif slot_status == 'error':
                self.afc.function.afc_led(cur_lane.led_fault, cur_lane.led_index)
                msg = "<span class=error--text>SLOT ERROR</span>"
                cur_lane.status = AFCLaneState.ERROR
                succeeded = False

            else:
                # Unknown status
                self.afc.function.afc_led(cur_lane.led_fault, cur_lane.led_index)
                msg = f"<span class=warning--text>UNKNOWN STATUS: {slot_status}</span>"
                succeeded = False

        except Exception as e:
            logging.error(f"AFC_ACE: Error during system test: {e}")
            self.afc.function.afc_led(cur_lane.led_fault, cur_lane.led_index)
            msg = "<span class=error--text>TEST ERROR</span>"
            succeeded = False

        return msg, succeeded

    def lane_tool_loaded(self, cur_lane):
        """
        Called when a lane is successfully loaded into the toolhead.

        Args:
            cur_lane: Lane that was loaded
        """
        # Update LED to show tool loaded
        if cur_lane.led_index is not None:
            self.afc.function.afc_led(cur_lane.led_tool_loaded, cur_lane.led_index)

        logging.info(f"AFC_ACE: Lane '{cur_lane.name}' loaded into toolhead")

    def calibrate_lane(self, cur_lane, tol):
        """
        Calibrate a lane.

        For ACE Pro, calibration is not needed since the device manages
        filament positioning internally via its protocol.

        Args:
            cur_lane: Lane to calibrate
            tol: Tolerance (unused for ACE)

        Returns:
            Tuple of (checked, msg, pos)
        """
        slot = self.get_slot_for_lane(cur_lane)

        # ACE handles filament positioning internally, no calibration needed
        msg = f"ACE Pro slot {slot} does not require calibration - device manages filament internally"

        self.afc.gcode.respond_info(msg)
        logging.info(f"AFC_ACE: {msg}")

        # Return success with current position (ACE manages this internally)
        return True, msg, 0.0

    def calibrate_bowden(self, cur_lane, dis, tol):
        """
        Calibrate bowden tube length.

        ACE Pro manages filament path internally, no bowden calibration needed.

        Args:
            cur_lane: Lane to calibrate
            dis: Distance (unused)
            tol: Tolerance (unused)

        Returns:
            Tuple of (checked, msg, pos)
        """
        msg = "ACE Pro does not require bowden calibration - device manages filament path"
        self.afc.gcode.respond_info(msg)
        return True, msg, 0.0

    def calibrate_hub(self, cur_lane, tol):
        """
        Calibrate hub distance.

        ACE Pro does not use a hub - it manages filament internally.

        Args:
            cur_lane: Lane to calibrate
            tol: Tolerance (unused)

        Returns:
            Tuple of (checked, msg, pos)
        """
        msg = "ACE Pro does not use a hub - no hub calibration needed"
        self.afc.gcode.respond_info(msg)
        return True, msg, 0.0


def load_config_prefix(config):
    """Klipper load function for [AFC_ACE name] sections"""
    return afcACE(config)

# Also support direct loading for backwards compatibility
load_config = load_config_prefix
