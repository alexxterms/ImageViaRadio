#!/bin/bash

# Installation and Setup Script for LoRa Image Transmission
# Run this on both Raspberry Pi devices (sender and receiver)

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║   LoRa Image Transmission - Installation & Setup Script      ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
    else
        echo -e "${RED}✗${NC} $2"
    fi
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

echo "This script will:"
echo "  1. Update system packages"
echo "  2. Install Python dependencies"
echo "  3. Configure serial port access"
echo "  4. Verify hardware connections"
echo "  5. Run basic tests"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Installation cancelled."
    exit 1
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "Step 1: System Update"
echo "════════════════════════════════════════════════════════════════"

print_info "Updating package lists..."
sudo apt-get update > /dev/null 2>&1
print_status $? "Package lists updated"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "Step 2: Install Python Dependencies"
echo "════════════════════════════════════════════════════════════════"

# Check if Python 3 is installed
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    print_status 0 "Python 3 is installed: $PYTHON_VERSION"
else
    print_status 1 "Python 3 is not installed"
    print_info "Installing Python 3..."
    sudo apt-get install -y python3 python3-pip
fi

# Install pip if not present
if ! command -v pip3 &> /dev/null; then
    print_info "Installing pip..."
    sudo apt-get install -y python3-pip
fi

# Install required packages
print_info "Installing RPi.GPIO..."
sudo pip3 install RPi.GPIO --break-system-packages > /dev/null 2>&1
print_status $? "RPi.GPIO installed"

print_info "Installing pyserial..."
sudo pip3 install pyserial --break-system-packages > /dev/null 2>&1
print_status $? "pyserial installed"

print_info "Installing Pillow (for image optimization)..."
sudo pip3 install Pillow --break-system-packages > /dev/null 2>&1
print_status $? "Pillow installed (optional)"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "Step 3: Configure Serial Port"
echo "════════════════════════════════════════════════════════════════"

# Check if user is in dialout group
if groups $USER | grep -q '\bdialout\b'; then
    print_status 0 "User '$USER' is in dialout group"
else
    print_status 1 "User '$USER' is NOT in dialout group"
    print_info "Adding user to dialout group..."
    sudo usermod -a -G dialout $USER
    print_status $? "User added to dialout group"
    echo -e "${YELLOW}⚠ You must LOGOUT and LOGIN again for this to take effect!${NC}"
fi

# Check if serial port exists
if [ -e /dev/ttyS0 ]; then
    print_status 0 "Serial port /dev/ttyS0 exists"
    ls -l /dev/ttyS0 | grep -q "dialout"
    print_status $? "Serial port has correct permissions"
else
    print_status 1 "Serial port /dev/ttyS0 not found"
    echo -e "${YELLOW}⚠ You may need to enable serial port in raspi-config${NC}"
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "Step 4: Hardware Check"
echo "════════════════════════════════════════════════════════════════"

# Check GPIO
if [ -d /sys/class/gpio ]; then
    print_status 0 "GPIO interface available"
else
    print_status 1 "GPIO interface not found"
fi

# Check for LoRa HAT (basic check)
print_info "Hardware checks:"
echo "    - Is LoRa HAT attached to GPIO header?"
echo "    - Are M0 and M1 jumpers REMOVED?"
echo "    - Is antenna connected to LoRa module?"
echo ""
read -p "All hardware properly connected? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status 0 "Hardware configuration confirmed"
else
    print_status 1 "Please check hardware connections"
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "Step 5: File Permissions"
echo "════════════════════════════════════════════════════════════════"

# Make scripts executable
chmod +x image_sender.py 2>/dev/null
print_status $? "image_sender.py is executable"

chmod +x image_receiver.py 2>/dev/null
print_status $? "image_receiver.py is executable"

chmod +x optimize_image.py 2>/dev/null
print_status $? "optimize_image.py is executable"

chmod +x test_setup.py 2>/dev/null
print_status $? "test_setup.py is executable"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "Step 6: Configuration Check"
echo "════════════════════════════════════════════════════════════════"

echo ""
echo "Serial Port Configuration:"
echo "  Run: sudo raspi-config"
echo "  Go to: Interface Options → Serial Port"
echo "  - Login shell over serial: NO"
echo "  - Serial port hardware enabled: YES"
echo "  Then reboot: sudo reboot"
echo ""
read -p "Have you configured serial port in raspi-config? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status 0 "Serial port configuration confirmed"
else
    print_status 1 "Please configure serial port before using"
    echo ""
    echo "To configure now, run:"
    echo "  sudo raspi-config"
    echo ""
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "Installation Summary"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Create summary report
SUMMARY_FILE="setup_report.txt"
{
    echo "LoRa Image Transmission - Setup Report"
    echo "Generated: $(date)"
    echo "User: $USER"
    echo "Hostname: $(hostname)"
    echo ""
    echo "System Information:"
    echo "  OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
    echo "  Kernel: $(uname -r)"
    echo "  Python: $(python3 --version)"
    echo ""
    echo "Python Packages:"
    pip3 list 2>/dev/null | grep -E "RPi.GPIO|pyserial|Pillow" || echo "  (run 'pip3 list' to check)"
    echo ""
    echo "Groups: $(groups $USER)"
    echo ""
    echo "Serial Port:"
    ls -l /dev/ttyS0 2>/dev/null || echo "  /dev/ttyS0 not found"
    echo ""
} > $SUMMARY_FILE

print_status 0 "Setup report saved to: $SUMMARY_FILE"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "Next Steps"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "1. If you added yourself to dialout group:"
echo "   ${YELLOW}LOGOUT and LOGIN again${NC} (or reboot)"
echo ""
echo "2. If serial port is not configured:"
echo "   Run: ${YELLOW}sudo raspi-config${NC}"
echo "   Then: ${YELLOW}sudo reboot${NC}"
echo ""
echo "3. Test the setup:"
echo "   python3 test_setup.py"
echo ""
echo "4. Read the documentation:"
echo "   • QUICKSTART.md - Getting started guide"
echo "   • README.md - Comprehensive documentation"
echo "   • EXAMPLES.md - Usage examples"
echo ""
echo "5. Start using:"
echo "   ${GREEN}Receiver:${NC} python3 image_receiver.py"
echo "   ${GREEN}Sender:${NC}   python3 image_sender.py photo.jpg"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "Installation complete!"
echo "════════════════════════════════════════════════════════════════"
echo ""
