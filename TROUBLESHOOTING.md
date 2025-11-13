# Troubleshooting: Sender Sending but Receiver Not Receiving

## Quick Diagnostic Steps

### Step 1: Run the Debug Receiver

First, stop your normal receiver and run the debug version to see if ANY data is being received:

```bash
python3 debug_receiver.py
```

This will show you:
- Raw data being received (if any)
- Packet headers and addresses
- Whether packets are addressed to your receiver

**Keep this running while someone sends from the other Pi.**

---

## Common Issues and Solutions

### Issue 1: Address Mismatch ❌

**Problem**: Sender's `target_addr` doesn't match receiver's `addr`

**Check**:
- Sender default: sends to address **1**
- Receiver default: listening on address **1**

**Solution**:
If addresses don't match, either:

```python
# On sender - send to correct address
python3 image_sender.py photo.jpg 1  # Sends to address 1

# Or edit image_sender.py
target_addr=1  # Match receiver's address

# Or edit image_receiver.py
addr=1  # Match sender's target
```

---

### Issue 2: Frequency Mismatch ❌

**Problem**: Sender and receiver on different frequencies

**Check**:
- Both default to **868 MHz**
- Verify both are using same frequency

**Solution**:
Edit both files to use the same frequency:

```python
# In image_sender.py AND image_receiver.py
freq=868,  # Must be identical on both devices
```

---

### Issue 3: Serial Port Not Working ❌

**Problem**: Receiver can't access `/dev/ttyS0`

**Test**:
```bash
ls -l /dev/ttyS0
```

Should show: `crw-rw---- 1 root dialout`

**Solution**:
```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER

# Logout and login again (or reboot)
sudo reboot
```

---

### Issue 4: Serial Port Not Enabled ❌

**Problem**: Serial port not enabled in Raspberry Pi config

**Test**:
```bash
dmesg | grep ttyS0
# Should show serial port info
```

**Solution**:
```bash
sudo raspi-config
# Navigate to: Interface Options → Serial Port
# - Login shell over serial: NO
# - Serial port hardware: YES
sudo reboot
```

---

### Issue 5: Wrong Serial Port ❌

**Problem**: Using wrong serial port name

**Test**:
```bash
ls -l /dev/tty* | grep -E "ttyS0|ttyAMA0"
```

**Solution**:
Try alternative port names:
- Raspberry Pi 3B+/4B: `/dev/ttyS0`
- Older Pis: `/dev/ttyAMA0`

Edit both files if needed:
```python
serial_num="/dev/ttyAMA0"  # Try this if ttyS0 doesn't work
```

---

### Issue 6: Hardware Not Connected ❌

**Problem**: LoRa HAT not properly attached

**Check**:
1. LoRa HAT firmly seated on GPIO pins
2. M0 and M1 jumpers **REMOVED** from HAT
3. Antenna connected to LoRa module
4. Power LED on LoRa HAT is lit

---

### Issue 7: GPIO Conflict ❌

**Problem**: Another process using GPIO or serial

**Test**:
```bash
# Check what's using the serial port
sudo lsof | grep ttyS0

# Check GPIO
sudo lsof | grep gpio
```

**Solution**:
Kill conflicting processes or reboot.

---

### Issue 8: Buffer/Air Speed Mismatch ❌

**Problem**: Different buffer sizes or air speeds

**Check**:
Both sender and receiver should have:
```python
air_speed=2400,
buffer_size=240,
```

**Solution**:
Make sure both files have identical settings.

---

## Step-by-Step Debugging Process

### Phase 1: Hardware Verification

```bash
# On RECEIVER Pi:
# 1. Check serial port
ls -l /dev/ttyS0

# 2. Check user permissions
groups
# Should include 'dialout'

# 3. Check GPIO
ls /sys/class/gpio
```

### Phase 2: Basic Communication Test

```bash
# On RECEIVER Pi:
python3 debug_receiver.py

# On SENDER Pi - send test message:
python3 -c "
import sx126x
import time
node = sx126x.sx126x(serial_num='/dev/ttyS0', freq=868, addr=0, power=22, rssi=False, air_speed=2400, relay=False)
time.sleep(1)
# Send to address 1
data = bytes([0, 1]) + bytes([18]) + bytes([0, 0]) + bytes([18]) + b'HELLO'
node.send(data)
print('Test message sent!')
"
```

**Expected on receiver**: You should see a packet with "HELLO"

### Phase 3: Check Addresses

```bash
# Run this on SENDER to verify configuration:
python3 -c "
from image_sender import ImageSender
sender = ImageSender()
print(f'Sender address: {sender.node.addr}')
print(f'Target address: {sender.target_addr}')
print(f'Frequency: {sender.freq} MHz')
print(f'Offset: {sender.offset_freq}')
"

# Run this on RECEIVER to verify:
python3 -c "
from image_receiver import ImageReceiver
receiver = ImageReceiver()
print(f'Receiver address: {receiver.node.addr}')
print(f'Frequency: {receiver.node.freq} MHz')
"
```

**These MUST match**:
- Sender `target_addr` = Receiver `addr`
- Sender `freq` = Receiver `freq`

### Phase 4: Monitor with RSSI

Edit `image_receiver.py` line ~35 to enable RSSI:
```python
rssi=True,  # Change from False to True
```

This will show signal strength, helping you verify communication.

---

## Quick Fixes Checklist

Try these in order:

- [ ] **Reboot both Raspberry Pis** - Clears GPIO/serial locks
- [ ] **Check addresses match** - Sender target = Receiver addr
- [ ] **Verify frequency** - Same on both (868 MHz)
- [ ] **Run debug_receiver.py** - See if ANY data arrives
- [ ] **Check serial permissions** - User in dialout group
- [ ] **Verify serial port enabled** - In raspi-config
- [ ] **Check antenna** - Firmly connected on both sides
- [ ] **Remove jumpers** - M0 and M1 jumpers removed
- [ ] **Check distance** - Start with devices close together
- [ ] **Test basic send** - Use debug test above

---

## Advanced Debugging

### Enable Verbose Logging

Add this to beginning of `image_receiver.py` `process_packet()`:

```python
def process_packet(self, raw_data):
    """Process received packet"""
    print(f"\nDEBUG: process_packet called with {len(raw_data)} bytes")
    print(f"DEBUG: First 20 bytes: {raw_data[:20]}")
    
    try:
        # ... rest of code
```

### Monitor Serial Port

```bash
# Install minicom
sudo apt-get install minicom

# Monitor serial (on receiver, while sender sends)
sudo minicom -D /dev/ttyS0 -b 9600
```

### Check Module Firmware

```python
# Run on both Pis to check LoRa module settings
import sx126x
node = sx126x.sx126x(serial_num='/dev/ttyS0', freq=868, addr=0, power=22, rssi=False, air_speed=2400, relay=False)
# Module should initialize without errors
```

---

## Most Common Solution

**90% of "not receiving" issues are due to**:

1. **Address mismatch** - Sender sending to wrong address
2. **User not in dialout group** - Permission denied on serial port
3. **Serial port not enabled** - Not configured in raspi-config

**Try this first**:

```bash
# On both Pis:
sudo usermod -a -G dialout $USER
sudo raspi-config  # Enable serial hardware, disable login shell
sudo reboot

# Verify addresses in code match
# Then try again
```

---

## Still Not Working?

Run this complete diagnostic:

```bash
# On RECEIVER Pi - save as check_receiver.sh
#!/bin/bash
echo "=== Receiver Diagnostic ==="
echo ""
echo "1. Serial Port:"
ls -l /dev/ttyS0
echo ""
echo "2. User Groups:"
groups
echo ""
echo "3. GPIO:"
ls /sys/class/gpio/ | head -5
echo ""
echo "4. Python packages:"
pip3 list | grep -E "RPi.GPIO|serial"
echo ""
echo "5. Receiver config:"
python3 -c "from image_receiver import ImageReceiver; r=ImageReceiver(); print(f'Addr: {r.node.addr}, Freq: {r.node.freq}')"
echo ""
echo "=== End Diagnostic ==="
```

Run and share the output for further help.

---

## Contact Checklist

If nothing works, provide:
- [ ] Output of `debug_receiver.py` (does it show ANY packets?)
- [ ] Output of diagnostic script above
- [ ] Raspberry Pi model (3B+, 4B, etc.)
- [ ] LoRa HAT model (E22-400T22S or E22-900T22S)
- [ ] Sender address and receiver address (from code)
- [ ] Frequency used on both (from code)
- [ ] Distance between devices
- [ ] Any error messages
