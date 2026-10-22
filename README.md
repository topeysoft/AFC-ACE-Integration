# AFC-ACE Integration

<div align="center">

**Native ACE Pro Support for AFC Multi-Material System**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Beta](https://img.shields.io/badge/Status-Beta-orange)]()
[![Klipper](https://img.shields.io/badge/Klipper-Compatible-blue)]()

</div>

---

## 📖 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
- [Documentation](#documentation)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage Examples](#usage-examples)
- [Contributing](#contributing)
- [Credits](#credits)
- [License](#license)

## Overview

AFC-ACE Integration brings native Anycubic Color Engine (ACE) Pro support to the Armored Turtle AFC (Automated Filament Control) multi-material system. This standalone integration combines AFC's powerful macro ecosystem with ACE Pro's USB-based hardware, enabling seamless multi-color/multi-material printing.

### What It Does

- **Bridges AFC ↔ ACE Pro** - Makes ACE Pro work as a native AFC unit (like BoxTurtle/NightOwl)
- **Auto-Detection** - Automatically discovers ACE devices on USB
- **Multi-ACE Support** - Scale to 8, 12, 16+ lanes with multiple ACE devices
- **No Dependencies** - Standalone integration, no KlipperACE required
- **Full AFC Features** - Endless spool, tip forming, purging, spoolman, etc.

## Features

### ✨ Core Features

- **🔌 Plug-and-Play** - Auto-detects ACE devices, generates config automatically
- **📡 USB Protocol** - Native ACE Pro protocol implementation (JSON-RPC over serial)
- **🎯 Lane Management** - Each ACE slot becomes an AFC lane (4 lanes per ACE)
- **🔄 Multi-ACE** - Support for 2, 3, 4+ ACE devices (8, 12, 16+ lanes)
- **📍 Stable Mapping** - Uses `/dev/serial/by-path` for reliable device identification
- **🌡️ Dryer Control** - Start/stop ACE dryer via G-code commands
- **⚡ Feed Assist** - ACE's built-in feed assist for reliable feeding

### 🎨 AFC Integration

All standard AFC features work seamlessly:

| Feature | Status | Description |
|---------|--------|-------------|
| Tool Changes | ✅ | T0, T1, T2, T3... commands work natively |
| Endless Spool | ✅ | Auto-switch to backup lane on runout |
| Tip Forming | ✅ | Clean filament tips for reliable unloads |
| Purge Macros | ✅ | POOP, BRUSH, KICK - full macro support |
| Gate Mapping | ✅ | Material type, color, temperature per lane |
| Spoolman | ✅ | Filament tracking and management |
| LED Feedback | ✅ | Visual status indicators |
| Calibration | ✅ | Lane distance tuning |

## Quick Start

### Installation (3 minutes)

```bash
# 1. Install AFC (if not already installed)
cd ~/
git clone https://github.com/ArmoredTurtle/AFC-Klipper-Add-On.git
cd AFC-Klipper-Add-On
./install-afc.sh

# 2. Install AFC-ACE
cd ~/
git clone <your-repo>/AFC-ACE-Integration.git
cd AFC-ACE-Integration
./install-afc-ace.sh

# 3. Generate config
python3 utilities/detect_ace_devices.py --generate-config > ~/printer_data/config/AFC/AFC_ACE_Pro.cfg

# 4. Add to printer.cfg (AFC_ACE_Pro.cfg is auto-loaded)
echo "[include AFC/*.cfg]" >> ~/printer_data/config/printer.cfg

# 5. Restart Klipper
sudo systemctl restart klipper
```

### First Use

```gcode
PREP    # Initialize lanes
T0      # Load filament from lane 1
T1      # Switch to lane 2
```

## Documentation

| Document | Description |
|----------|-------------|
| **[INSTALLATION.md](./INSTALLATION.md)** | Complete installation guide with troubleshooting |
| **[USAGE.md](./USAGE.md)** | Operating manual with examples and workflows |
| **[TESTING_GUIDE.md](./TESTING_GUIDE.md)** | Testing procedures and validation steps |
| **[PROJECT_SUMMARY.md](./PROJECT_SUMMARY.md)** | Technical architecture and code overview |

## Project Structure

```
AFC-ACE-Integration/
├── extras/                          # Python modules
│   ├── AFC_ACE.py                  # ACE unit driver (implements AFC interface)
│   ├── AFC_ACE_protocol.py         # USB protocol handler (JSON-RPC)
│   └── AFC_ACE_discovery.py        # Auto-detection and enumeration
│
├── config/                          # Configuration templates
│   ├── mcu/
│   │   └── ACE_Pro.cfg             # Comprehensive template with docs
│   ├── AFC_ACE_single_example.cfg  # Single ACE (4 lanes) example
│   └── AFC_ACE_multi_example.cfg   # Multi-ACE (8+ lanes) example
│
├── utilities/
│   └── detect_ace_devices.py       # Auto-detection and config generator
│
├── install-afc-ace.sh               # Installation script
│
└── docs/                            # Documentation
    ├── README.md                   # This file
    ├── INSTALLATION.md             # Install guide
    ├── USAGE.md                    # User manual
    ├── TESTING_GUIDE.md            # Test procedures
    └── PROJECT_SUMMARY.md          # Technical details
```

## Requirements

### Hardware
- **ACE Pro** - One or more Anycubic Color Engine Pro devices
- **USB Cable** - Data-capable cable (not charge-only)
- **3D Printer** - Running Klipper firmware
- **Linux Host** - Raspberry Pi, Orange Pi, or similar (for `/dev/serial/by-path` support)

### Software
- **Klipper** - 3D printer firmware
- **Moonraker** - Klipper API server
- **AFC-Klipper-Add-On** - Multi-material system
- **Python 3** - With pyserial library

## Installation

See [INSTALLATION.md](./INSTALLATION.md) for complete installation guide.

### Quick Install

```bash
cd ~/AFC-ACE-Integration
./install-afc-ace.sh
```

The installer:
1. ✅ Checks dependencies (Klipper, AFC)
2. ✅ Installs Python libraries
3. ✅ Creates symlinks to Klipper
4. ✅ Copies configuration templates
5. ✅ Auto-detects ACE devices

## Usage Examples

### Single ACE (4 lanes)

```ini
[AFC_ACE ace1]
auto_detect: true
extruder: extruder

[AFC_lane lane1]
unit: ace1:0
map: T0
extruder: extruder

# ... lanes 2-4
```

### Multi-ACE (8 lanes)

```ini
# First ACE
[AFC_ACE ace1]
auto_detect: true
device_index: 0

# Second ACE
[AFC_ACE ace2]
auto_detect: true
device_index: 1

# Lanes T0-T7
```

### Commands

```gcode
# Initialization
PREP                                    # Initialize all lanes

# Tool changes
T0                                      # Select lane 1
T4                                      # Select lane 5 (multi-ACE)

# Dryer control
ACE_START_DRYING TEMP=50 DURATION=240  # Start dryer
ACE_STOP_DRYING                         # Stop dryer

# Status
ACE_GET_STATUS                          # Show device status

# Manual control
ACE_FEED INDEX=0 LENGTH=50 SPEED=50    # Feed 50mm
ACE_RETRACT INDEX=0 LENGTH=50 SPEED=50 # Retract 50mm

# Endless spool
AFC_ENDLESS_SPOOL ENABLE=1              # Enable auto-switching

# Gate mapping
ACE_GATE_MAP GATE=0 TYPE=PLA COLOR=FF0000 TEMP=210
```

## Contributing

Contributions welcome! Please:

1. **Fork** the repository
2. **Create** a feature branch
3. **Test** your changes thoroughly
4. **Document** new features
5. **Submit** a pull request

### Development Setup

```bash
git clone <your-fork>/AFC-ACE-Integration.git
cd AFC-ACE-Integration

# Make changes
# Test on real hardware
# Document in appropriate .md files
```

### Reporting Issues

When reporting bugs, please include:
- Hardware setup (number of ACEs, USB connection)
- Software versions (Klipper, AFC)
- Error logs (`~/printer_data/logs/klippy.log`)
- Configuration files
- Steps to reproduce

## Credits

This project builds upon excellent work by:

### Projects
- **[AFC-Klipper-Add-On](https://github.com/ArmoredTurtle/AFC-Klipper-Add-On)** by Armored Turtle
  - Multi-material management framework
  - Macro system and lane management

- **[KlipperACE](https://github.com/topeysoft/MultiACEManager)** by topeysoft
  - ACE Pro protocol implementation
  - USB auto-detection system

### Special Thanks
- **Armored Turtle Community** - AFC development and support
- **Klipper Team** - Firmware foundation
- **ACE Pro Users** - Testing and feedback

## License

This project is licensed under the MIT License - see [LICENSE](./LICENSE) file for details.

### Code Attribution

This project incorporates code adapted from:
- **KlipperACE** - Protocol and discovery code (~580 lines)
- **AFC-Klipper-Add-On** - Interface implementation

All adapted code is clearly attributed and compatible with MIT licensing.

---

<div align="center">

**[Documentation](./INSTALLATION.md)** • **[Issues](https://github.com/your-repo/issues)** • **[Discord](https://discord.gg/eT8zc3bvPR)**

Made with ❤️ for the AFC community

</div>
