# AFC-ACE Installation Guide

Complete guide to installing AFC-ACE integration for Anycubic Color Engine Pro.

## Prerequisites

### Required Software
- **Klipper** - 3D printer firmware
- **Moonraker** - Klipper API server
- **AFC-Klipper-Add-On** - Armored Turtle's multi-material system

### Required Hardware
- **Anycubic ACE Pro** - One or more devices
- **USB Connection** - Data-capable USB cable (not charge-only)
- **3D Printer** - Running Klipper firmware

## Installation Steps

### Step 1: Install Prerequisites

If you haven't already installed AFC, do that first:

```bash
cd ~/
git clone https://github.com/ArmoredTurtle/AFC-Klipper-Add-On.git
cd AFC-Klipper-Add-On
./install-afc.sh
```

Follow AFC's installation guide to configure your base AFC system (extruder, macros, etc.).

### Step 2: Install AFC-ACE Integration

Clone and install the AFC-ACE integration:

```bash
cd ~/
git clone <your-repo>/AFC-ACE-Integration.git
cd AFC-ACE-Integration
./install-afc-ace.sh
```

The installer will:
1. Check for Klipper and AFC installation
2. Install Python dependencies (pyserial)
3. Create symlinks to Klipper extras directory
4. Copy configuration templates
5. Auto-detect connected ACE devices

### Step 3: Generate Configuration

Auto-detect your ACE devices and generate configuration:

```bash
cd ~/AFC-ACE-Integration
python3 utilities/detect_ace_devices.py --generate-config > ~/printer_data/config/AFC/ACE_units.cfg
```

This will create a configuration file with all detected ACE devices and their lanes.

### Step 4: Configure Your Printer

Edit the generated configuration to match your setup:

```bash
nano ~/printer_data/config/AFC/ACE_units.cfg
```

Key things to configure:
- **Extruder name** - Match your printer's extruder
- **Hub configuration** - If using AFC hub
- **Sensor pins** - Optional prep/load sensors (if you have external sensors)
- **LED indices** - If using LED feedback

### Step 5: Include in printer.cfg

Add these lines to your `printer.cfg`:

```ini
# AFC base system (if not already included)
[include AFC/*.cfg]

# AFC-ACE units
[include AFC/ACE_units.cfg]
```

### Step 6: Restart Klipper

Restart Klipper to load the new configuration:

```bash
sudo systemctl restart klipper
```

Or use your web interface (Mainsail/Fluidd) to restart.

### Step 7: Verify Installation

Check Klipper console for successful initialization:

```
AFC_ACE: Connected to ACE Pro (FW: v1.2.3) at /dev/serial/by-path/...
AFC_ACE: Mapped lane 'leg1' → slot 0
AFC_ACE: Mapped lane 'leg2' → slot 1
...
```

## Verification

### Test Auto-Detection

List all detected ACE devices:

```bash
cd ~/AFC-ACE-Integration
python3 utilities/detect_ace_devices.py
```

Expected output:
```
Found 1 ACE device(s):

Device 0:
  Port (tty):      /dev/ttyACM0
  Port (by-path):  /dev/serial/by-path/platform-...
  Device ID:       hub_1_port_1_3
  Model:           ACE Pro
  Firmware:        v1.2.3
```

### Test AFC Commands

Run AFC initialization:

```
PREP
```

This should:
1. Connect to all ACE devices
2. Query slot status
3. Initialize lanes
4. Report lane status

Test tool selection:

```
T0    # Select lane 1 (ACE slot 0)
T1    # Select lane 2 (ACE slot 1)
```

### Check ACE Status

Query ACE device status:

```
ACE_GET_STATUS
```

This displays:
- Number of ACE devices connected
- Lane status (empty/ready/loaded)
- Dryer status and temperature
- Firmware information

## Troubleshooting

### No ACE Devices Found

**Problem:** `detect_ace_devices.py` finds no devices

**Solutions:**
1. Check USB cable is data-capable (not charge-only)
2. Verify ACE Pro is powered on
3. Check `dmesg | grep tty` for USB enumeration
4. Try different USB port
5. Check USB permissions: `ls -l /dev/ttyACM*`

### Connection Errors

**Problem:** `AFC_ACE: Failed to connect to /dev/ttyACM0`

**Solutions:**
1. Check serial port permissions:
   ```bash
   sudo usermod -a -G dialout $USER
   sudo usermod -a -G tty $USER
   ```
   Then logout and login again

2. Verify port is not in use:
   ```bash
   lsof /dev/ttyACM0
   ```

3. Check `/dev/serial/by-path` exists (Linux only):
   ```bash
   ls -l /dev/serial/by-path/
   ```

### Unstable Device Detection

**Problem:** ACE devices swap order on reboot

**Solutions:**
1. **Use `by-path` serial ports** (recommended):
   - AFC-ACE automatically uses `/dev/serial/by-path/...`
   - These paths are stable across reboots

2. **Use auto-detection with device_index**:
   - Devices are sorted by USB location
   - Keep ACE devices in same USB ports

3. **Check USB hub setup**:
   - Some USB hubs don't preserve port order
   - Connect ACE devices directly to host if possible

### Klipper Fails to Start

**Problem:** Klipper error on startup

**Solutions:**
1. Check Klipper log:
   ```bash
   tail -f ~/printer_data/logs/klippy.log
   ```

2. Common errors:
   - **Import error**: Check symlinks in `~/klipper/klippy/extras/`
   - **Config error**: Validate `ACE_units.cfg` syntax
   - **Serial error**: Verify ACE is connected and accessible

3. Temporarily disable AFC-ACE to isolate issue:
   ```ini
   # Comment out in printer.cfg:
   # [include AFC/ACE_units.cfg]
   ```

## Next Steps

- **[CONFIGURATION.md](./CONFIGURATION.md)** - Detailed configuration reference
- **[USAGE.md](./USAGE.md)** - Operating your AFC-ACE system
- **[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)** - Common issues and solutions

## Getting Help

- **AFC Documentation**: https://armoredturtle.xyz/docs/
- **GitHub Issues**: <your-repo-url>/issues
- **AFC Discord**: https://discord.gg/eT8zc3bvPR
