# Quick Start Guide - LoRa Image Transmission

## 🚀 Quick Setup (5 Minutes)

### Step 1: Hardware Setup
1. Attach LoRa HAT to both Raspberry Pi devices
2. Remove M0 and M1 jumpers from the HATs
3. Connect antennas to both modules

### Step 2: Enable Serial Port (One-time setup)
```bash
sudo raspi-config
```
- Go to: **Interface Options** → **Serial Port**
- "Would you like a login shell accessible over serial?" → **No**
- "Would you like the serial port hardware to be enabled?" → **Yes**
- Reboot: `sudo reboot`

### Step 3: Install Dependencies
```bash
sudo apt-get update
sudo apt-get install python3-pip
sudo pip3 install RPi.GPIO pyserial
```

### Step 4: Copy Files to Both Raspberry Pis
Copy these files to both devices:
- `sx126x.py`
- `image_sender.py`
- `image_receiver.py`

---

## 📡 Basic Usage

### On Receiver Raspberry Pi:
```bash
python3 image_receiver.py
```
Leave this running - it will wait for images.

### On Sender Raspberry Pi:
```bash
python3 image_sender.py photo.jpg
```

That's it! The image will be transmitted and saved on the receiver.

---

## 📋 Example Workflow

### 1. Prepare an image on the sender:
```bash
# Take a photo or copy an image
cp /home/pi/Pictures/sunset.jpg ~/my_image.jpg
```

### 2. Start receiver (Receiver Pi):
```bash
cd ~/ImageViaRadio
python3 image_receiver.py
```
Output:
```
==================================================
LoRa Image Receiver
==================================================

Initializing LoRa module...
LoRa module initialized successfully!

Listening for images... (Press Ctrl+C to exit)
--------------------------------------------------
```

### 3. Send image (Sender Pi):
```bash
cd ~/ImageViaRadio
python3 image_sender.py my_image.jpg
```
Output:
```
==================================================
LoRa Image Sender
==================================================

Initializing LoRa module...
LoRa module initialized successfully!

==================================================
Image: my_image.jpg
Size: 15234 bytes
Checksum: a3b2c1d4e5f6...
==================================================

Splitting into 77 chunks of 200 bytes each

Sent START packet with metadata
Progress: [77/77] 100.0%

Sent END packet

==================================================
Image transmission completed!
==================================================
```

### 4. Check received image:
```bash
ls -lh received_images/
```

---

## ⚙️ Configuration

### Default Settings
- **Sender Address**: 0
- **Receiver Address**: 1
- **Frequency**: 868 MHz
- **Power**: 22 dBm (maximum)
- **Air Speed**: 2400 bps
- **Chunk Size**: 200 bytes

### Change Receiver Address
Edit `image_receiver.py` line ~25:
```python
receiver = ImageReceiver(
    addr=5,  # Change to any address 0-65535
    ...
)
```

### Change Target Address (Sender)
Send to a different receiver:
```bash
python3 image_sender.py photo.jpg 5
```

### Change Frequency
Edit both files to use the same frequency:
```python
freq=915,  # Must be 850-930 or 410-493 MHz
```

---

## 🔍 Testing Your Setup

### Test 1: Check Serial Port
```bash
ls -l /dev/ttyS0
```
Should show: `crw-rw---- 1 root dialout ...`

### Test 2: Add User to dialout Group
```bash
sudo usermod -a -G dialout $USER
# Logout and login again
```

### Test 3: Verify Permissions
```bash
groups
```
Should include `dialout`

### Test 4: Create Test Image
```bash
# Install Pillow (optional, for test image generation)
sudo pip3 install Pillow

# Run test script
python3 test_setup.py
```

---

## 📊 Performance Guide

### Image Size vs Transfer Time

| Image Size | Approx. Time | Best For |
|------------|--------------|----------|
| 5-10 KB    | 30-60 sec    | Small icons, thumbnails |
| 20-30 KB   | 2-3 min      | Low-res photos |
| 50-80 KB   | 5-8 min      | Medium-res photos |
| 100+ KB    | 10+ min      | High-res (not recommended) |

### Tips for Faster Transfer
1. **Reduce Image Size** before sending:
   ```bash
   # Install ImageMagick
   sudo apt-get install imagemagick
   
   # Resize image
   convert input.jpg -resize 50% output.jpg
   
   # Or reduce quality
   convert input.jpg -quality 70 output.jpg
   ```

2. **Use Lower Resolution**:
   - 320x240 pixels: ~10-20 KB
   - 640x480 pixels: ~40-60 KB
   - 1024x768 pixels: ~100-150 KB

3. **Optimize JPEG Quality**:
   - Quality 70-80 is usually sufficient
   - Lower quality = smaller file = faster transfer

---

## 🐛 Troubleshooting

### Problem: "Permission denied: '/dev/ttyS0'"
**Solution:**
```bash
sudo usermod -a -G dialout $USER
# Then logout and login
```

### Problem: No data received
**Check:**
1. Both devices on same frequency? (default: 868 MHz)
2. Sender target address matches receiver address?
3. Antennas connected?
4. Serial port enabled on both devices?

**Test:**
```bash
# On both devices, check serial port
ls -l /dev/ttyS0
```

### Problem: Checksum mismatch
**Solutions:**
- Increase delay between packets:
  Edit `image_sender.py`:
  ```python
  sender.send_image(image_path, delay_between_packets=0.2)  # Increase to 0.2
  ```
- Move devices closer together
- Check antenna connections
- Reduce image size

### Problem: Slow transmission
**Expected:**
- 200-300 bytes/second is normal at 2400 bps
- 10 KB image takes ~40-60 seconds

**To improve:**
- Use smaller images (compress before sending)
- Increase air speed (edit both files):
  ```python
  air_speed=9600,  # Faster but shorter range
  ```

### Problem: Incomplete transmission
**Solutions:**
1. Check console for "Missing chunks" message
2. Resend the image
3. Increase delay between packets
4. Reduce interference (change frequency)

---

## 💡 Pro Tips

### 1. Batch Processing
Send multiple images:
```bash
for img in *.jpg; do
    python3 image_sender.py "$img"
    sleep 5
done
```

### 2. Compress Before Sending
```bash
# Quick compress script
convert input.jpg -resize 640x480 -quality 75 output.jpg
python3 image_sender.py output.jpg
```

### 3. Monitor Progress
The sender shows real-time progress:
```
Progress: [45/77] 58.4%
```

### 4. Verify Transfer
Check the checksum match in receiver output:
```
Checksum match: ✓ YES
```

### 5. Save Bandwidth
For thumbnails or previews, use tiny images:
```bash
convert photo.jpg -resize 160x120 -quality 60 thumbnail.jpg
# Results in ~3-5 KB file, transfers in ~20 seconds
```

---

## 📁 File Structure
```
ImageViaRadio/
├── sx126x.py              # LoRa driver (don't modify)
├── image_sender.py        # Send images
├── image_receiver.py      # Receive images
├── test_setup.py          # Test and create sample images
├── main.py                # Original example (reference)
├── README.md              # Full documentation
├── QUICKSTART.md          # This file
└── received_images/       # Received images saved here
```

---

## 🎯 Common Use Cases

### Scenario 1: Security Camera
1. Capture image on sender Pi with camera
2. Automatically send to receiver Pi
3. Receiver saves and can trigger alerts

### Scenario 2: Remote Monitoring
1. Take photo of sensor/meter
2. Send to base station
3. Process and log data

### Scenario 3: Field Data Collection
1. Capture images in remote location
2. Transmit to nearby base station
3. Base station uploads to cloud/network

---

## 📞 Getting Help

1. **Check the full README.md** for detailed information
2. **Run test_setup.py** to verify your setup
3. **Check LoRa HAT LEDs** - they should blink during transmission
4. **Use RSSI** to check signal strength (see README.md)

---

## ✅ Quick Checklist

- [ ] LoRa HAT attached to both Pis
- [ ] M0 and M1 jumpers removed
- [ ] Antennas connected
- [ ] Serial port enabled (raspi-config)
- [ ] User in dialout group
- [ ] Python packages installed (RPi.GPIO, pyserial)
- [ ] Same frequency on both devices (default: 868 MHz)
- [ ] Sender target_addr = Receiver addr
- [ ] Receiver running before sending

---

**Ready to transmit!** 🚀📡📷
