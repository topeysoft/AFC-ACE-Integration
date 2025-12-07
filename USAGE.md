# AFC-ACE Usage Guide

How to operate your ACE Pro multi-material system with AFC.

## Quick Start

### Initial Setup

1. **Load Filament into ACE Slots**
   - Insert filament into ACE Pro slots (0-3)
   - ACE will automatically detect and grip filament

2. **Initialize AFC Lanes**
   ```
   PREP
   ```
   This command:
   - Queries all ACE devices
   - Checks slot status
   - Initializes lane configuration
   - Reports lane readiness

3. **Load First Tool**
   ```
   T0    # Load filament from lane 1 (slot 0)
   ```

4. **Ready to Print**
   - Start your multi-material print
   - AFC handles tool changes automatically

## Tool Selection

### Basic Tool Commands

```gcode
T0    # Select lane 1 (ACE slot 0)
T1    # Select lane 2 (ACE slot 1)
T2    # Select lane 3 (ACE slot 2)
T3    # Select lane 4 (ACE slot 3)
```

For multi-ACE setups:
```gcode
T4    # Lane 5 (second ACE, slot 0)
T5    # Lane 6 (second ACE, slot 1)
# ... and so on
```

### Tool Change Workflow

When you execute `T1` (for example), AFC performs these steps:

1. **Pre-toolchange**
   - Runs `_ACE_PRE_TOOLCHANGE` macro (if configured)
   - Parks toolhead if enabled

2. **Unload Current Filament**
   - Forms tip if `form_tip` enabled
   - Cuts tip if `tool_cut` enabled
   - Retracts filament to ACE

3. **Load New Filament**
   - Feeds from new ACE slot
   - Loads to toolhead
   - Enables feed assist

4. **Post-toolchange**
   - Purges filament (`POOP` macro)
   - Wipes nozzle (`BRUSH` macro)
   - Kicks purge blob (`KICK` macro)
   - Runs `_ACE_POST_TOOLCHANGE` macro

## ACE-Specific Commands

### Dryer Control

Start dryer:
```gcode
ACE_START_DRYING TEMP=50 DURATION=240
```
Parameters:
- `TEMP`: Target temperature in Celsius (default 55°C, max varies by ACE model)
- `DURATION`: Duration in minutes (default 240)

Stop dryer:
```gcode
ACE_STOP_DRYING
```

Note: Dryer won't turn off instantly - it needs time to cool down safely.

### Feed Assist

ACE Pro has built-in feed assist to help feed filament.

Enable for a lane:
```gcode
ACE_ENABLE_FEED_ASSIST LANE=0
```

Disable:
```gcode
ACE_DISABLE_FEED_ASSIST LANE=0
```

Feed assist is automatically enabled during tool changes.

### Device Status

Check ACE status:
```gcode
ACE_GET_STATUS
```

This shows:
- Number of ACE devices
- Lane statuses (empty/ready/loaded)
- Selected lane
- Dryer status and temperature
- Firmware versions

## AFC Features

All standard AFC features work with ACE:

### Endless Spool

Enable:
```gcode
AFC_ENDLESS_SPOOL ENABLE=1
```

Disable:
```gcode
AFC_ENDLESS_SPOOL ENABLE=0
```

**How it works:**
1. Set material types for lanes (e.g., T0 and T4 both as "PLA")
2. When T0 runs out during print, AFC pauses
3. AFC searches for another lane with matching material
4. Automatically switches to T4 and resumes print

### Gate Mapping

Set material info for a lane:
```gcode
ACE_GATE_MAP GATE=0 TYPE=PLA COLOR=FF0000 TEMP=210
```

Parameters:
- `GATE`: Lane index (0-3 for single ACE, 0-7 for dual ACE, etc.)
- `TYPE`: Material type (PLA, PETG, ABS, etc.)
- `COLOR`: Hex color code (e.g., FF0000 for red)
- `TEMP`: Printing temperature in Celsius

This information is used for:
- Endless spool matching
- Temperature control
- Slicer integration
- UI display

### Manual Feed/Retract

Feed filament manually:
```gcode
ACE_FEED INDEX=0 LENGTH=100 SPEED=50
```

Retract filament:
```gcode
ACE_RETRACT INDEX=0 LENGTH=100 SPEED=50
```

Parameters:
- `INDEX`: Lane index (0-3)
- `LENGTH`: Distance in mm
- `SPEED`: Speed (10-80)

## Print Workflow

### Starting a Print

1. **Prepare lanes:**
   ```
   PREP
   ```

2. **Load starting filament:**
   ```
   T0    # Or whichever lane you want to start with
   ```

3. **Start print:**
   - Use your slicer's generated gcode
   - AFC handles tool changes automatically

### During Print

- **Monitor status**: Use `ACE_GET_STATUS` between prints
- **Adjust dryer**: `ACE_START_DRYING` for hygroscopic materials
- **Endless spool**: Automatically handles runouts if enabled

### After Print

1. **Unload filament** (optional):
   ```
   T-1    # Unloads current filament
   ```

2. **Turn off dryer** (if used):
   ```
   ACE_STOP_DRYING
   ```

## Slicer Configuration

### PrusaSlicer / OrcaSlicer

Add tool change gcode:

```gcode
; Tool change to tool {next_extruder}
T{next_extruder}
```

### Cura

Add tool change script:

```gcode
;TYPE:TOOL-CHANGE
T{new_tool}
```

### Color Painting

1. Paint objects in slicer with different colors
2. Slicer generates T0, T1, T2... commands
3. AFC maps T commands to ACE lanes
4. ACE automatically loads correct filament

## Tips and Best Practices

### Filament Loading

- **Pre-cut filament tips** - Clean, angled cuts load more reliably
- **Feed assist** - Enable for flexible filaments or long Bowden tubes
- **Distance calibration** - Use `LANE_CALIBRATION` to tune distances

### Tool Changes

- **Purge volume** - Adjust `POOP` macro for your nozzle size and materials
- **Tip forming** - Critical for reliable unloads, tune `AFC_form_tip` settings
- **Retraction speed** - Slower speeds prevent filament grinding

### Multi-ACE Setup

- **Label slots** - Physical labels on ACE devices prevent loading errors
- **Group by material** - Keep similar materials on same ACE for faster changes
- **Endless spool redundancy** - Duplicate materials across ACEs for reliability

### Maintenance

- **Check ACE filament paths** - Clean dust and debris from slots
- **Monitor temperature** - Verify dryer doesn't overheat materials
- **Firmware updates** - Keep ACE firmware current for bug fixes

## Advanced Features

### Custom Macros

Create pre/post toolchange macros:

```gcode
[gcode_macro _ACE_PRE_TOOLCHANGE]
gcode:
    # Your custom pre-toolchange logic
    SAVE_GCODE_STATE NAME=toolchange_state
    G91
    G1 Z10 F1000    # Lift Z before toolchange
    G90

[gcode_macro _ACE_POST_TOOLCHANGE]
gcode:
    # Your custom post-toolchange logic
    RESTORE_GCODE_STATE NAME=toolchange_state
```

### Spoolman Integration

AFC integrates with Spoolman for filament tracking:

1. Configure Spoolman in AFC
2. Assign spools to lanes via Spoolman UI
3. AFC automatically tracks filament usage
4. Endless spool uses Spoolman material data

## Troubleshooting

### Tool Change Failures

**Problem**: Tool change fails, filament doesn't load

**Solutions**:
1. Check filament tip is clean and angled
2. Enable feed assist: `ACE_ENABLE_FEED_ASSIST LANE=0`
3. Calibrate lane distance: `LANE_CALIBRATION`
4. Verify ACE slot has filament loaded: `ACE_GET_STATUS`

### Purge Issues

**Problem**: Not enough purge, previous color visible

**Solutions**:
1. Increase purge volume in `POOP` macro
2. Check nozzle temperature is correct for new filament
3. Verify tip cutting is working properly

### Feed Assist Problems

**Problem**: Feed assist too strong/weak

**Solutions**:
1. Adjust feed assist settings in ACE firmware
2. Use manual feed to test: `ACE_FEED INDEX=0 LENGTH=10 SPEED=30`
3. Disable if causing issues: `ACE_DISABLE_FEED_ASSIST`

## Next Steps

- **[CONFIGURATION.md](./CONFIGURATION.md)** - Advanced configuration options
- **[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)** - Detailed troubleshooting guide
- **[AFC Documentation](https://armoredturtle.xyz/docs/)** - Complete AFC reference
