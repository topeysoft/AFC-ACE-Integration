# AFC-ACE Testing Guide

Quick reference for testing the AFC-ACE integration.

## Prerequisites

- ACE Pro device connected via USB
- AFC-Klipper-Add-On installed
- Klipper running on a Linux host (Raspberry Pi, etc.)

## Testing Steps

### 1. Installation Test

```bash
# From your Klipper host (SSH into your Pi)
cd ~/
git clone <your-repo>/AFC-ACE-Integration.git
cd AFC-ACE-Integration
./install-afc-ace.sh
```

**Expected Output:**
- ✓ Klipper found
- ✓ AFC found
- ✓ Python dependencies installed
- ✓ Modules linked
- List of detected ACE devices

**If it fails:**
- Check error messages
- Verify prerequisites are installed
- Check permissions on serial ports

### 2. Auto-Detection Test

```bash
# List detected devices
python3 utilities/detect_ace_devices.py
```

**Expected Output:**
```
Found 1 ACE device(s):

Device 0:
  Port (tty):      /dev/ttyACM0
  Port (by-path):  /dev/serial/by-path/platform-...
  Device ID:       hub_1_port_1_3
  Model:           ACE Pro
  Firmware:        v1.2.3
```

**If no devices found:**
- Check USB cable (must be data cable, not charge-only)
- Verify ACE Pro is powered on
- Check `dmesg | grep tty` for USB enumeration
- Check permissions: `ls -l /dev/ttyACM*`

### 3. Config Generation Test

```bash
# Generate config
python3 utilities/detect_ace_devices.py --generate-config > ~/printer_data/config/AFC/ACE_units.cfg
```

**Verify generated file:**
```bash
cat ~/printer_data/config/AFC/ACE_units.cfg
```

**Should contain:**
- `[AFC_ACE ace1]` section
- 4 `[AFC_lane legN]` sections
- Serial port or auto_detect configuration

### 4. Klipper Integration Test

```bash
# Edit printer.cfg
nano ~/printer_data/config/printer.cfg
```

**Add these lines:**
```ini
[include AFC/*.cfg]
[include AFC/ACE_units.cfg]
```

**Restart Klipper:**
```bash
sudo systemctl restart klipper
```

**Check Klipper log:**
```bash
tail -100 ~/printer_data/logs/klippy.log
```

**Look for:**
```
AFC_ACE: Initialized unit 'ace1'
AFC_ACE: Connected to ACE Pro (FW: v1.2.3)
AFC_ACE: Mapped lane 'leg1' → slot 0
AFC_ACE: Mapped lane 'leg2' → slot 1
AFC_ACE: Mapped lane 'leg3' → slot 2
AFC_ACE: Mapped lane 'leg4' → slot 3
```

**If errors:**
- Check for Python import errors (symlinks correct?)
- Check for serial port errors (permissions?)
- Check for config syntax errors (validate .cfg files)

### 5. AFC Command Test

**In Klipper console (Mainsail/Fluidd):**

```gcode
# Initialize lanes
PREP
```

**Expected:**
- Each lane reports status (EMPTY/LOCKED/LOADED)
- LEDs update if configured
- No errors

```gcode
# Check status
ACE_GET_STATUS
```

**Expected:**
```
Total ACE devices: 1
Total lanes: 4
Lane 0: ready
Lane 1: ready
Lane 2: empty
Lane 3: empty
```

### 6. Tool Change Test

**Load filament into ACE slot 0:**

```gcode
# Select lane 1 (slot 0)
T0
```

**Expected sequence:**
1. ACE feeds filament from slot 0
2. Filament loads to toolhead
3. Purge macro executes (if configured)
4. LED updates to "tool loaded"

**Test lane switch:**

```gcode
T1    # Switch to lane 2 (slot 1)
```

**Expected:**
1. Current filament unloads
2. Tip forming/cutting (if configured)
3. New filament loads from slot 1
4. Purge and wipe

### 7. Manual Feed Test

```gcode
# Feed 50mm from slot 0
ACE_FEED INDEX=0 LENGTH=50 SPEED=50
```

**Expected:**
- ACE feeds filament 50mm
- No errors

```gcode
# Retract 50mm from slot 0
ACE_RETRACT INDEX=0 LENGTH=50 SPEED=50
```

**Expected:**
- ACE retracts filament 50mm
- No errors

### 8. Dryer Test

```gcode
# Start dryer
ACE_START_DRYING TEMP=50 DURATION=5
```

**Expected:**
- ACE dryer starts heating
- Status shows dryer running

**Check dryer status:**
```gcode
ACE_GET_STATUS
```

**Should show:**
```
Dryer: running
Temperature: 50°C
Remaining time: ~5 minutes
```

**Stop dryer:**
```gcode
ACE_STOP_DRYING
```

**Expected:**
- Dryer begins cooldown
- Status shows dryer stopping

### 9. Multi-ACE Test (if applicable)

**If you have 2+ ACE devices:**

```bash
# Verify all detected
python3 utilities/detect_ace_devices.py
```

**Should show Device 0, Device 1, etc.**

**Generate config with all devices:**
```bash
python3 utilities/detect_ace_devices.py --generate-config > ~/printer_data/config/AFC/ACE_units.cfg
```

**Verify config has:**
- Multiple `[AFC_ACE aceN]` sections
- Lanes numbered T0-T7 (for 2 ACEs), T0-T11 (for 3 ACEs), etc.

**Test tool changes across ACEs:**
```gcode
T0    # Lane 1 (ACE 1, slot 0)
T4    # Lane 5 (ACE 2, slot 0)
```

**Expected:**
- Tool change works across different ACE devices
- Both ACEs respond correctly

### 10. Stress Test

**Rapid tool changes:**
```gcode
T0
T1
T2
T3
T0
```

**Expected:**
- All changes complete successfully
- No communication errors
- ACE responds reliably

**Long-duration test:**
- Run a multi-hour print with tool changes
- Monitor for USB disconnects
- Check for memory leaks or performance degradation

## Common Issues

### Serial Port Permissions

```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER
sudo usermod -a -G tty $USER

# Then logout and login again
```

### USB Path Not Found

**Symptom:** Device detected but no `/dev/serial/by-path`

**Solution:**
- Only works on Linux (not macOS)
- Check udev is running: `systemctl status udev`
- Replug USB device

### Import Errors

**Symptom:** `ImportError: No module named AFC_ACE_protocol`

**Solution:**
```bash
# Check symlinks exist
ls -l ~/klipper/klippy/extras/AFC_ACE*.py

# Re-run installer if missing
cd ~/AFC-ACE-Integration
./install-afc-ace.sh
```

### Communication Timeout

**Symptom:** `AFC_ACE: Command 'get_status' timed out`

**Solution:**
- Check USB cable quality
- Try lower baud rate (in config: `baud: 57600`)
- Check ACE firmware is up to date
- Verify ACE is powered and responsive

## Success Criteria

✅ Installation completes without errors
✅ Auto-detection finds all ACE devices
✅ Config generation creates valid files
✅ Klipper starts without errors
✅ PREP initializes all lanes
✅ Tool changes work (T0-T3)
✅ Manual feed/retract work
✅ Dryer control works
✅ Multi-ACE lanes work (if applicable)
✅ No USB disconnects during long prints

## Reporting Issues

When reporting issues, include:

1. **Hardware:**
   - Number of ACE devices
   - USB connection type (direct/hub)
   - Klipper host (Pi model, OS version)

2. **Software:**
   - AFC version
   - Klipper version
   - AFC-ACE commit hash

3. **Logs:**
   ```bash
   # Klipper log
   tail -200 ~/printer_data/logs/klippy.log

   # Auto-detection output
   python3 utilities/detect_ace_devices.py

   # USB devices
   lsusb
   ls -l /dev/serial/by-path/
   ```

4. **Config:**
   ```bash
   cat ~/printer_data/config/AFC/ACE_units.cfg
   ```

5. **Steps to reproduce**

## Next Steps After Testing

Once testing is successful:

1. **Document your setup** - Note any quirks or adjustments
2. **Test edge cases** - Filament runout, errors, recovery
3. **Long-term reliability** - Run for several days
4. **Share feedback** - Report successes and issues
5. **Contribute improvements** - PRs welcome!

---

Good luck with testing! 🚀
