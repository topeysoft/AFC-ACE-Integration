#!/bin/bash
# AFC-ACE Integration Installation Script
#
# Installs AFC-ACE integration for Armored Turtle AFC
# Requires: AFC-Klipper-Add-On to be already installed

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Directories
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
KLIPPER_DIR="${HOME}/klipper"
KLIPPER_EXTRAS="${KLIPPER_DIR}/klippy/extras"
AFC_DIR="${HOME}/AFC-Klipper-Add-On"
PRINTER_DATA_DIR="${HOME}/printer_data"
CONFIG_DIR="${PRINTER_DATA_DIR}/config"
AFC_CONFIG_DIR="${CONFIG_DIR}/AFC"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}AFC-ACE Integration Installer${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to print status messages
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script must NOT be run as root"
   exit 1
fi

# Check dependencies
echo -e "${BLUE}Checking dependencies...${NC}"

# Check if Klipper is installed
if [ ! -d "$KLIPPER_DIR" ]; then
    print_error "Klipper not found at $KLIPPER_DIR"
    print_error "Please install Klipper first"
    exit 1
fi
print_status "Klipper found at $KLIPPER_DIR"

# Check if AFC is installed
if [ ! -d "$AFC_DIR" ]; then
    print_error "AFC-Klipper-Add-On not found at $AFC_DIR"
    print_error "Please install AFC first:"
    echo ""
    echo "  cd ~"
    echo "  git clone https://github.com/ArmoredTurtle/AFC-Klipper-Add-On.git"
    echo "  cd AFC-Klipper-Add-On"
    echo "  ./install-afc.sh"
    echo ""
    exit 1
fi
print_status "AFC-Klipper-Add-On found at $AFC_DIR"

# Check if Python serial module is available
python3 -c "import serial" 2>/dev/null
if [ $? -ne 0 ]; then
    print_warning "pyserial not found, installing..."
    pip3 install --user pyserial
fi
print_status "Python dependencies installed"

echo ""
echo -e "${BLUE}Installing AFC-ACE modules...${NC}"

# Create symlinks to Klipper extras
for file in AFC_ACE.py AFC_ACE_protocol.py AFC_ACE_discovery.py; do
    SRC="${SCRIPT_DIR}/extras/${file}"
    DST="${KLIPPER_EXTRAS}/${file}"

    if [ -L "$DST" ]; then
        print_warning "Removing existing symlink: $DST"
        rm "$DST"
    elif [ -f "$DST" ]; then
        print_warning "Backing up existing file: $DST → ${DST}.bak"
        mv "$DST" "${DST}.bak"
    fi

    ln -sf "$SRC" "$DST"
    print_status "Linked $file → $DST"
done

echo ""
echo -e "${BLUE}Setting up configuration...${NC}"

# Create AFC config directory if it doesn't exist
if [ ! -d "$AFC_CONFIG_DIR" ]; then
    print_warning "Creating AFC config directory: $AFC_CONFIG_DIR"
    mkdir -p "$AFC_CONFIG_DIR"
fi

# Copy MCU config template
MCU_CONFIG_SRC="${SCRIPT_DIR}/config/mcu/ACE_Pro.cfg"
MCU_CONFIG_DST="${AFC_CONFIG_DIR}/mcu/ACE_Pro.cfg"

if [ ! -d "${AFC_CONFIG_DIR}/mcu" ]; then
    mkdir -p "${AFC_CONFIG_DIR}/mcu"
fi

if [ -f "$MCU_CONFIG_DST" ]; then
    print_warning "ACE_Pro.cfg already exists, skipping copy"
else
    cp "$MCU_CONFIG_SRC" "$MCU_CONFIG_DST"
    print_status "Copied ACE_Pro.cfg template to $MCU_CONFIG_DST"
fi

# Make utility script executable
chmod +x "${SCRIPT_DIR}/utilities/detect_ace_devices.py"
print_status "Made detect_ace_devices.py executable"

echo ""
echo -e "${BLUE}Auto-detecting ACE devices...${NC}"

# Run auto-detection
python3 "${SCRIPT_DIR}/utilities/detect_ace_devices.py"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Installation Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo ""
echo "1. Generate ACE configuration:"
echo -e "   ${YELLOW}cd ${SCRIPT_DIR}${NC}"
echo -e "   ${YELLOW}python3 utilities/detect_ace_devices.py --generate-config > ${AFC_CONFIG_DIR}/AFC_ACE_Pro.cfg${NC}"
echo ""
echo "2. Edit the generated configuration as needed:"
echo -e "   ${YELLOW}nano ${AFC_CONFIG_DIR}/AFC_ACE_Pro.cfg${NC}"
echo ""
echo "3. AFC-ACE config will be loaded automatically with:"
echo -e "   ${YELLOW}[include AFC/*.cfg]${NC}"
echo ""
echo "   (The AFC_ACE_Pro.cfg file is automatically included)"
echo ""
echo "4. Restart Klipper:"
echo -e "   ${YELLOW}sudo systemctl restart klipper${NC}"
echo ""
echo "5. Test your setup with:"
echo -e "   ${YELLOW}PREP${NC}  (Initialize lanes)"
echo -e "   ${YELLOW}T0${NC}    (Select lane 1)"
echo ""
echo -e "${BLUE}Documentation:${NC}"
echo "  ${SCRIPT_DIR}/README.md"
echo ""
echo -e "${BLUE}Support:${NC}"
echo "  AFC: https://armoredturtle.xyz/docs/"
echo "  GitHub Issues: <your-repo-url>"
echo ""
