# AFC-ACE Frequently Asked Questions (FAQ)

## Configuration Questions

### Q: Do I need an AFC hub with ACE Pro?

**A: No, a hub is optional and usually not needed.**

ACE Pro manages filament feeding and routing internally via its USB protocol. Unlike BoxTurtle/NightOwl which use stepper motors and need a hub for filament merging, ACE Pro handles this in hardware.

**When you DON'T need a hub:**
- Standard ACE Pro setup
- ACE feeds directly to your extruder
- Using ACE's built-in feed assist

**When you MIGHT need a hub:**
- You have a physical AFC hub already installed in your filament path
- You're using ACE with other AFC units (mixed setup)
- You have specific routing requirements

**Configuration:**

```ini
# WITHOUT hub (recommended for most setups)
[AFC_ACE ace1]
auto_detect: true
extruder: extruder

# WITH hub (only if you have physical hub hardware)
[AFC_ACE ace1]
auto_detect: true
extruder: extruder
hub: hub    # Must have [AFC_hub hub] configured elsewhere
```

### Q: What's the difference between lanes and gates?

**A: We use "lanes" consistently throughout AFC-ACE.**

- **Lanes** - AFC's term for filament channels (used by BoxTurtle, NightOwl, and now ACE)
- **Gates** - Old term from some MMU systems, we've standardized on "lanes"

Each ACE Pro has 4 **lanes** (slots 0-3), mapped to T0-T3 commands.

### Q: Why am I getting "AFC_hub not found" error?

**A: You have `hub: hub` configured but no [AFC_hub hub] section.**

**Solutions:**

1. **Remove the hub line** (recommended if you don't have physical hub):
   ```ini
   [AFC_ACE ace1]
   auto_detect: true
   extruder: extruder
   # hub: hub  ← Comment out or delete this line
   ```

2. **Add an AFC hub config** (only if you have physical hub hardware):
   ```ini
   [AFC_hub hub]
   # Your hub configuration here
   ```

### Q: Can I use ACE Pro with other AFC units (BoxTurtle, NightOwl)?

**A: Yes! AFC supports mixed unit setups.**

Example with 1 ACE Pro (4 lanes) + 1 BoxTurtle (4 lanes):

```ini
# ACE Pro unit (lanes T0-T3)
[AFC_ACE ace1]
auto_detect: true
extruder: extruder

[AFC_lane leg1]
unit: ace1:0
map: T0
extruder: extruder

# ... T1-T3

# BoxTurtle unit (lanes T4-T7)
[AFC_BoxTurtle turtle1]
extruder: extruder
hub: hub

[AFC_lane leg5]
unit: turtle1:0
map: T4
extruder: extruder

# ... T5-T7
```

Total: 8 lanes (T0-T7)

## Hardware Questions

### Q: How many ACE Pro devices can I use?

**A: Theoretically unlimited, practically 4-6 is reasonable.**

Each ACE Pro adds 4 lanes:
- 1 ACE = 4 lanes (T0-T3)
- 2 ACE = 8 lanes (T0-T7)
- 3 ACE = 12 lanes (T0-T11)
- 4 ACE = 16 lanes (T0-T15)

**Limitations:**
- USB bandwidth (each ACE is a separate USB device)
- Physical space and cable management
- Print time (more tool changes = longer prints)

### Q: Do I need `/dev/serial/by-path` or can I use `/dev/ttyACM0`?

**A: `/dev/serial/by-path` is strongly recommended for stability.**

| Path Type | Stability | Notes |
|-----------|-----------|-------|
| `/dev/ttyACM0` | ❌ Unstable | Changes on reboot, device order not guaranteed |
| `/dev/serial/by-path/...` | ✅ Stable | Always same USB port = same path |
| `auto_detect: true` | ✅ Stable | Uses by-path internally, best option |

**Recommendation:** Use `auto_detect: true` with `device_index` for reliable operation.

### Q: What if my ACE devices swap order after reboot?

**A: Use `device_index` with auto-detection for consistent ordering.**

ACE devices are sorted by USB location (bus-port path), which is stable as long as devices stay in the same physical USB ports.

```ini
# First ACE (always in first USB port)
[AFC_ACE ace1]
auto_detect: true
device_index: 0  # Always finds first ACE by USB location

# Second ACE (always in second USB port)
[AFC_ACE ace2]
auto_detect: true
device_index: 1  # Always finds second ACE by USB location
```

**Important:** Keep ACE devices in the same physical USB ports!

## Feature Questions

### Q: Does endless spool work with ACE?

**A: Yes! All AFC features work with ACE.**

Enable endless spool:
```gcode
AFC_ENDLESS_SPOOL ENABLE=1
```

Set material types for matching:
```gcode
ACE_GATE_MAP GATE=0 TYPE=PLA COLOR=FF0000 TEMP=210
ACE_GATE_MAP GATE=1 TYPE=PLA COLOR=00FF00 TEMP=210
```

When lane 0 runs out, AFC automatically switches to lane 1 (same material type).

### Q: Can I control the ACE dryer?

**A: Yes, via G-code commands.**

```gcode
# Start dryer at 50°C for 4 hours
ACE_START_DRYING TEMP=50 DURATION=240

# Stop dryer
ACE_STOP_DRYING

# Check dryer status
ACE_GET_STATUS
```

**Note:** Dryer won't turn off instantly - it cools down safely over time.

### Q: Does tip forming/cutting work with ACE?

**A: Yes, AFC's standard tip forming and cutting macros work.**

Configure in your ACE unit or per-lane:
```ini
[AFC_ACE ace1]
# ... other config ...

# Use AFC's tip forming
form_tip: true

# Use tip cutting (if you have a cutter)
tool_cut: true
```

The ACE hardware handles feeding/retracting, while AFC macros handle tip preparation.

### Q: Can I use Spoolman with ACE?

**A: Yes! Spoolman integration works normally.**

AFC tracks filament usage across all lanes (including ACE lanes). Configure Spoolman in AFC.cfg and assign spools to lanes via Spoolman's web UI.

## Troubleshooting

### Q: ACE device not detected during auto-detection?

**Checklist:**
1. ✅ ACE Pro is powered on
2. ✅ USB cable is data-capable (not charge-only)
3. ✅ USB cable connected to host running Klipper
4. ✅ Ran detection as non-root user
5. ✅ User is in dialout/tty groups

**Test:**
```bash
# Check USB enumeration
lsusb | grep ACE

# Check for tty devices
ls -l /dev/ttyACM*

# Test auto-detection
python3 ~/AFC-ACE-Integration/utilities/detect_ace_devices.py
```

### Q: "Permission denied" on serial port?

**A: Add your user to dialout group.**

```bash
sudo usermod -a -G dialout $USER
sudo usermod -a -G tty $USER
# Then logout and login again
```

Verify:
```bash
groups  # Should show dialout and tty
```

### Q: Tool changes fail / filament doesn't load?

**Possible causes:**

1. **Feed assist not enabled**
   ```gcode
   ACE_ENABLE_FEED_ASSIST LANE=0
   ```

2. **Distance calibration needed**
   ```gcode
   LANE_CALIBRATION
   ```

3. **Filament tip not clean**
   - Cut tip at 45° angle
   - Remove any blobs or strings

4. **Speed too high/low**
   - Try different feed speeds (30-60 recommended)

### Q: How do I update AFC-ACE?

**A: Pull latest code and re-run installer.**

```bash
cd ~/AFC-ACE-Integration
git pull
./install-afc-ace.sh

# Restart Klipper
sudo systemctl restart klipper
```

Your config files are not overwritten during updates.

## Advanced Topics

### Q: Can I have different extruders for different ACE lanes?

**A: Yes, configure extruder per lane.**

```ini
[AFC_ACE ace1]
# No extruder at unit level
auto_detect: true

[AFC_lane leg1]
unit: ace1:0
map: T0
extruder: extruder    # Left extruder

[AFC_lane leg2]
unit: ace1:1
map: T1
extruder: extruder1   # Right extruder (IDEX)
```

### Q: How do I debug ACE communication issues?

**A: Enable debug logging.**

```ini
[AFC_ACE ace1]
auto_detect: true
extruder: extruder
log_level: DEBUG  # Add this for verbose logging
```

Then check Klipper log:
```bash
tail -f ~/printer_data/logs/klippy.log | grep AFC_ACE
```

### Q: Can I use ACE with Klipper on Windows/macOS?

**A: Linux only for production use.**

- **Linux** (RPi, etc.): ✅ Full support with `/dev/serial/by-path`
- **macOS**: ⚠️ Development only (no `/dev/serial/by-path`, use manual serial)
- **Windows**: ❌ Not supported (Klipper runs in WSL, USB passthrough issues)

**Recommendation:** Use Raspberry Pi or similar Linux SBC for Klipper.

---

**Didn't find your answer?**
- Check [INSTALLATION.md](./INSTALLATION.md) for setup help
- Check [USAGE.md](./USAGE.md) for operating instructions
- Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for common issues
- Ask on [AFC Discord](https://discord.gg/eT8zc3bvPR)
