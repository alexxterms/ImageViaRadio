#!/usr/bin/python
# -*- coding: UTF-8 -*-

"""
Quick Diagnostic Script
Checks sender and receiver configuration for mismatches
"""

import sys
import os

print("\n" + "="*70)
print("LoRa Image Transmission - Configuration Diagnostic")
print("="*70 + "\n")

def check_file_exists(filename):
    """Check if file exists"""
    if os.path.exists(filename):
        print(f"✓ {filename} found")
        return True
    else:
        print(f"✗ {filename} NOT found")
        return False

def extract_config(filename, config_name):
    """Extract configuration from Python file"""
    try:
        with open(filename, 'r') as f:
            content = f.read()
            
        # Simple regex-like extraction
        configs = {}
        
        # Look for common patterns
        import re
        
        # Extract serial_num
        match = re.search(r'serial_num\s*=\s*["\']([^"\']+)["\']', content)
        if match:
            configs['serial_num'] = match.group(1)
            
        # Extract freq
        match = re.search(r'freq\s*=\s*(\d+)', content)
        if match:
            configs['freq'] = int(match.group(1))
            
        # Extract addr (own address)
        match = re.search(r'addr\s*=\s*(\d+)', content)
        if match:
            configs['addr'] = int(match.group(1))
            
        # Extract target_addr (for sender)
        match = re.search(r'target_addr\s*=\s*(\d+)', content)
        if match:
            configs['target_addr'] = int(match.group(1))
            
        # Extract power
        match = re.search(r'power\s*=\s*(\d+)', content)
        if match:
            configs['power'] = int(match.group(1))
            
        # Extract air_speed
        match = re.search(r'air_speed\s*=\s*(\d+)', content)
        if match:
            configs['air_speed'] = int(match.group(1))
            
        # Extract buffer_size
        match = re.search(r'buffer_size\s*=\s*(\d+)', content)
        if match:
            configs['buffer_size'] = int(match.group(1))
            
        return configs
    except Exception as e:
        print(f"Error reading {filename}: {e}")
        return {}

# Check files exist
print("Checking files...")
sender_exists = check_file_exists("image_sender.py")
receiver_exists = check_file_exists("image_receiver.py")
print()

if not sender_exists or not receiver_exists:
    print("Error: Missing required files!")
    sys.exit(1)

# Extract configurations
print("Extracting configurations...")
sender_config = extract_config("image_sender.py", "Sender")
receiver_config = extract_config("image_receiver.py", "Receiver")
print()

# Display sender configuration
print("="*70)
print("SENDER Configuration (image_sender.py)")
print("="*70)
for key, value in sender_config.items():
    print(f"  {key:20} = {value}")
print()

# Display receiver configuration
print("="*70)
print("RECEIVER Configuration (image_receiver.py)")
print("="*70)
for key, value in receiver_config.items():
    print(f"  {key:20} = {value}")
print()

# Check for issues
print("="*70)
print("COMPATIBILITY CHECK")
print("="*70)

issues_found = False

# Check 1: Frequency match
if sender_config.get('freq') == receiver_config.get('freq'):
    print(f"✓ Frequency matches: {sender_config.get('freq')} MHz")
else:
    print(f"✗ FREQUENCY MISMATCH!")
    print(f"  Sender: {sender_config.get('freq')} MHz")
    print(f"  Receiver: {receiver_config.get('freq')} MHz")
    print(f"  FIX: Both must use the same frequency")
    issues_found = True

# Check 2: Address compatibility
sender_target = sender_config.get('target_addr')
receiver_addr = receiver_config.get('addr')

if sender_target == receiver_addr or sender_target == 65535:
    print(f"✓ Addresses compatible:")
    print(f"  Sender target: {sender_target}")
    print(f"  Receiver addr: {receiver_addr}")
else:
    print(f"✗ ADDRESS MISMATCH!")
    print(f"  Sender is sending to address: {sender_target}")
    print(f"  Receiver is listening on address: {receiver_addr}")
    print(f"  FIX: Sender's target_addr must equal Receiver's addr")
    issues_found = True

# Check 3: Serial port match
if sender_config.get('serial_num') == receiver_config.get('serial_num'):
    print(f"✓ Serial port: {sender_config.get('serial_num')}")
else:
    print(f"⚠ Different serial ports (OK if on different devices):")
    print(f"  Sender: {sender_config.get('serial_num')}")
    print(f"  Receiver: {receiver_config.get('serial_num')}")

# Check 4: Air speed match
if sender_config.get('air_speed') == receiver_config.get('air_speed'):
    print(f"✓ Air speed matches: {sender_config.get('air_speed')} bps")
else:
    print(f"✗ AIR SPEED MISMATCH!")
    print(f"  Sender: {sender_config.get('air_speed')} bps")
    print(f"  Receiver: {receiver_config.get('air_speed')} bps")
    print(f"  FIX: Both must use the same air speed")
    issues_found = True

# Check 5: Buffer size match
if sender_config.get('buffer_size') == receiver_config.get('buffer_size'):
    print(f"✓ Buffer size matches: {sender_config.get('buffer_size')} bytes")
else:
    print(f"⚠ Buffer size mismatch:")
    print(f"  Sender: {sender_config.get('buffer_size')} bytes")
    print(f"  Receiver: {receiver_config.get('buffer_size')} bytes")
    print(f"  FIX: Should be the same for best results")

print()

# Check system requirements
print("="*70)
print("SYSTEM CHECK")
print("="*70)

# Check serial port
import os
if os.path.exists("/dev/ttyS0"):
    print(f"✓ Serial port /dev/ttyS0 exists")
    
    # Check permissions
    import stat
    st = os.stat("/dev/ttyS0")
    if st.st_mode & stat.S_IRWXG:
        print(f"✓ Serial port has group permissions")
    else:
        print(f"⚠ Serial port may need permission adjustment")
else:
    print(f"✗ Serial port /dev/ttyS0 NOT found")
    print(f"  Check if serial port is enabled in raspi-config")
    issues_found = True

# Check user groups
import grp
try:
    dialout_group = grp.getgrnam('dialout')
    import pwd
    username = pwd.getpwuid(os.getuid()).pw_name
    
    if username in dialout_group.gr_mem:
        print(f"✓ User '{username}' is in dialout group")
    else:
        print(f"✗ User '{username}' is NOT in dialout group")
        print(f"  FIX: sudo usermod -a -G dialout {username}")
        print(f"       Then logout and login again")
        issues_found = True
except:
    print(f"⚠ Could not check dialout group membership")

# Check Python packages
try:
    import RPi.GPIO
    print(f"✓ RPi.GPIO is installed")
except ImportError:
    print(f"✗ RPi.GPIO is NOT installed")
    print(f"  FIX: sudo pip3 install RPi.GPIO")
    issues_found = True

try:
    import serial
    print(f"✓ pyserial is installed")
except ImportError:
    print(f"✗ pyserial is NOT installed")
    print(f"  FIX: sudo pip3 install pyserial")
    issues_found = True

print()

# Summary
print("="*70)
print("SUMMARY")
print("="*70)

if issues_found:
    print("✗ ISSUES FOUND - Please fix the problems above")
    print()
    print("Common fixes:")
    print("  1. Make sure frequency matches on both sender and receiver")
    print("  2. Make sure sender's target_addr matches receiver's addr")
    print("  3. Make sure air_speed and buffer_size match")
    print("  4. Add user to dialout group if needed")
    print("  5. Enable serial port in raspi-config")
    print()
    print("For detailed troubleshooting, see TROUBLESHOOTING.md")
else:
    print("✓ Configuration looks good!")
    print()
    print("If sender is still not communicating with receiver:")
    print("  1. Run debug_receiver.py to see if ANY data is received")
    print("  2. Check antenna connections on both devices")
    print("  3. Make sure M0 and M1 jumpers are removed from HAT")
    print("  4. Try devices closer together initially")
    print("  5. See TROUBLESHOOTING.md for more help")

print()
print("="*70)
