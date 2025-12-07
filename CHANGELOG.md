# Changelog

All notable changes to AFC-ACE Integration will be documented in this file.

## [Unreleased]

### Changed
- **Config file naming** - Changed from `ACE_units.cfg` to `AFC_ACE_Pro.cfg`
  - Follows AFC naming convention (`AFC_*.cfg` pattern)
  - Automatically loaded with `[include AFC/*.cfg]` - no separate include needed
  - Updated all documentation and installation scripts

### Why This Change?

The new naming convention provides several benefits:

1. **Consistency** - Matches AFC's file naming pattern (`AFC_BoxTurtle.cfg`, `AFC_NightOwl.cfg`, etc.)
2. **Auto-loading** - Files named `AFC_*.cfg` are automatically included with the standard `[include AFC/*.cfg]`
3. **Cleaner config** - Users don't need a separate include line for ACE
4. **Organization** - All AFC-related configs follow the same pattern

### Migration Guide

If you previously installed AFC-ACE with `ACE_units.cfg`:

**Old setup:**
```ini
# printer.cfg
[include AFC/*.cfg]
[include AFC/ACE_units.cfg]  ← separate include needed
```

**New setup:**
```ini
# printer.cfg
[include AFC/*.cfg]  ← AFC_ACE_Pro.cfg automatically included!
```

**Steps to migrate:**

1. Rename your existing file:
   ```bash
   cd ~/printer_data/config/AFC
   mv ACE_units.cfg AFC_ACE_Pro.cfg
   ```

2. Remove the explicit include from `printer.cfg`:
   ```bash
   # Remove this line (if present):
   # [include AFC/ACE_units.cfg]
   ```

3. Restart Klipper:
   ```bash
   sudo systemctl restart klipper
   ```

Your ACE configuration will now load automatically!

## [1.0.0] - Initial Release

### Added
- Native ACE Pro support for AFC
- Auto-detection of ACE devices via USB
- Multi-ACE support (4, 8, 12, 16+ lanes)
- Stable device mapping via `/dev/serial/by-path`
- Complete ACE protocol implementation
- Auto-configuration generation
- Comprehensive documentation
- Installation script
- Testing guide

### Features
- Tool changes (T0-T3 for single ACE, T0-T7 for dual ACE, etc.)
- Endless spool support
- Dryer control
- Feed assist
- Gate mapping
- Lane calibration
- All standard AFC features
