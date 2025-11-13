# 📡 ImageViaRadio - Complete LoRa Image Transmission System

![LoRa](https://img.shields.io/badge/LoRa-868MHz-blue)
![Python](https://img.shields.io/badge/Python-3.x-green)
![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-3B%2B%2F4B-red)

> Transmit JPEG images wirelessly over long distances using LoRa technology and Waveshare eByte Raspberry Pi LoRa HAT

## 🌟 Features

- ✅ **Reliable transmission** with MD5 checksum verification
- ✅ **Chunk-based protocol** for handling large images
- ✅ **Configurable parameters** (frequency, power, air speed)
- ✅ **Image optimization** tools included
- ✅ **Real-time progress** tracking
- ✅ **Long-range capability** (1-5 km depending on environment)
- ✅ **Easy to use** with comprehensive documentation

## 📚 Documentation Guide

### 🚀 Getting Started
1. **[QUICKSTART.md](QUICKSTART.md)** ← **START HERE!**
   - 5-minute setup guide
   - Basic usage examples
   - Quick reference commands

### 📖 Detailed Documentation
2. **[README.md](README.md)**
   - Complete technical documentation
   - Configuration options
   - Troubleshooting guide
   - Performance optimization

3. **[EXAMPLES.md](EXAMPLES.md)**
   - 12+ usage examples
   - Common scenarios
   - Code patterns
   - Integration examples

4. **[ARCHITECTURE.md](ARCHITECTURE.md)**
   - System architecture diagrams
   - Packet structure details
   - Data flow visualization
   - Hardware connections

5. **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)**
   - Project overview
   - File descriptions
   - Technical specifications

## 📁 Project Files

### Core Components
```
image_sender.py       → Transmit images via LoRa
image_receiver.py     → Receive and save images
sx126x.py            → LoRa driver (Waveshare)
```

### Utilities
```
optimize_image.py    → Compress images before sending
test_setup.py        → Verify system configuration
setup.sh             → Automated installation script
```

### Documentation
```
QUICKSTART.md        → Quick start guide
README.md            → Full documentation
EXAMPLES.md          → Usage examples
ARCHITECTURE.md      → System architecture
PROJECT_SUMMARY.md   → Project overview
INDEX.md             → This file
```

## ⚡ Quick Start (3 Steps)

### Step 1: Installation
```bash
# Run the automated setup script
./setup.sh

# Or manually install dependencies
sudo pip3 install RPi.GPIO pyserial Pillow
```

### Step 2: Start Receiver
```bash
# On receiving Raspberry Pi
python3 image_receiver.py
```

### Step 3: Send Image
```bash
# On sending Raspberry Pi
python3 image_sender.py photo.jpg
```

That's it! Your image will be transmitted and saved on the receiver.

## 🎯 Common Use Cases

| Use Case | Configuration | Details |
|----------|--------------|---------|
| **Security Camera** | Medium power, periodic capture | Send photos every 10 minutes |
| **Remote Monitoring** | High power, on-demand | Send when event detected |
| **Data Collection** | Low power, scheduled | Send at specific times daily |
| **Emergency Comms** | Max power, manual trigger | Long-range critical images |

## 🔧 System Requirements

### Hardware
- Raspberry Pi 3B+, 4B, or Zero series
- Waveshare eByte LoRa HAT (E22-400T22S or E22-900T22S)
- Antenna (included with HAT)
- Two complete setups (sender + receiver)

### Software
- Raspberry Pi OS (Raspbian)
- Python 3.x
- RPi.GPIO library
- pyserial library
- Pillow (optional, for optimization)

## 📊 Performance

| Image Size | Transfer Time* | Best Use |
|------------|---------------|----------|
| 5-10 KB | 30-60 sec | Thumbnails |
| 20-30 KB | 2-3 min | Low-res photos |
| 50-80 KB | 5-8 min | Medium-res photos |
| 100+ KB | 10+ min | High-res (compress first!) |

*At default settings (2400 bps, 0.1s delay)

## 🛠️ Configuration Presets

### Maximum Range
```python
freq=868, power=22, air_speed=1200
# Slower but reaches further
```

### Balanced (Default)
```python
freq=868, power=22, air_speed=2400
# Good speed and range
```

### Maximum Speed
```python
freq=868, power=22, air_speed=9600
# Faster but shorter range
```

## 📖 Usage Examples

### Example 1: Basic Transmission
```bash
# Receiver
python3 image_receiver.py

# Sender
python3 image_sender.py photo.jpg
```

### Example 2: Optimized Transmission
```bash
# Optimize first
python3 optimize_image.py photo.jpg small

# Send optimized version
python3 image_sender.py photo_optimized.jpg
```

### Example 3: Custom Target
```bash
# Send to receiver at address 5
python3 image_sender.py photo.jpg 5
```

## 🐛 Troubleshooting Quick Reference

### Problem: Permission Denied
```bash
sudo usermod -a -G dialout $USER
# Logout and login again
```

### Problem: No Serial Port
```bash
sudo raspi-config
# Interface Options → Serial Port
# Disable login shell, enable hardware
```

### Problem: Checksum Mismatch
```python
# In image_sender.py, increase delay:
sender.send_image(image_path, delay_between_packets=0.2)
```

## 📞 Where to Get Help

1. **Quick issues**: See [QUICKSTART.md](QUICKSTART.md) troubleshooting
2. **Detailed issues**: See [README.md](README.md) troubleshooting section
3. **Configuration**: Check [EXAMPLES.md](EXAMPLES.md) for patterns
4. **Hardware**: Consult Waveshare documentation

## 🧪 Testing Your Setup

```bash
# Run the test script
python3 test_setup.py

# This will:
# - Check all dependencies
# - Verify serial port access
# - Create test images
# - Show configuration status
```

## 🗺️ Learning Path

### Beginner (30 minutes)
1. Read QUICKSTART.md
2. Run setup.sh
3. Test with small image
4. ✓ Success!

### Intermediate (2 hours)
1. Read full README.md
2. Try different configurations
3. Optimize images before sending
4. Monitor RSSI

### Advanced (1 day)
1. Study ARCHITECTURE.md
2. Integrate with camera
3. Add custom processing
4. Build automated system

## 🎓 Example Projects

### Project 1: Security Camera
```python
# Capture photo every 10 minutes and send
while True:
    capture_photo()
    optimize_and_send()
    sleep(600)
```

### Project 2: Weather Station
```python
# Send weather data visualization
create_weather_chart()
send_chart_image()
```

### Project 3: Remote Monitoring
```python
# Send photo when motion detected
if motion_detected():
    capture_and_send()
```

## 📈 Performance Tips

1. **Compress images first** - Use `optimize_image.py`
2. **Start small** - Test with 10-20 KB images
3. **Monitor checksums** - Verify successful transmission
4. **Adjust delays** - Increase for reliability
5. **Check RSSI** - Monitor signal strength
6. **Use line of sight** - Better than through obstacles

## 🔐 Technical Specifications

- **Frequency**: 410-493 MHz or 850-930 MHz
- **Max Power**: 22 dBm (158 mW)
- **Air Speeds**: 1200 - 62500 bps
- **Range**: 1-5 km (environment dependent)
- **Packet Size**: Up to 240 bytes
- **Addressing**: 16-bit (0-65535)
- **Modulation**: LoRa (proprietary)

## 📦 What's Included

```
ImageViaRadio/
├── Core Scripts
│   ├── image_sender.py       # Send images
│   ├── image_receiver.py     # Receive images
│   └── sx126x.py            # LoRa driver
├── Utilities
│   ├── optimize_image.py    # Image compression
│   ├── test_setup.py        # System verification
│   └── setup.sh             # Installation script
├── Documentation
│   ├── INDEX.md             # This file
│   ├── QUICKSTART.md        # Quick start
│   ├── README.md            # Full docs
│   ├── EXAMPLES.md          # Examples
│   ├── ARCHITECTURE.md      # Architecture
│   └── PROJECT_SUMMARY.md   # Overview
└── Legacy
    └── main.py              # Original example
```

## 🚀 Next Steps

1. **If you're new**: Read [QUICKSTART.md](QUICKSTART.md)
2. **For setup help**: Run `./setup.sh`
3. **For testing**: Run `python3 test_setup.py`
4. **For examples**: See [EXAMPLES.md](EXAMPLES.md)
5. **For details**: Read [README.md](README.md)

## 💡 Pro Tips

- 📸 **Optimize first**: Small images transfer faster
- 🎯 **Test local**: Verify setup before going remote
- 📊 **Monitor progress**: Watch real-time transfer status
- ✅ **Check checksums**: Confirm successful reception
- 🔋 **Plan power**: Consider battery life for remote setups
- 📡 **Position antennas**: Vertical orientation works best

## 🌐 Additional Resources

- [Waveshare LoRa HAT Wiki](https://www.waveshare.com/)
- [eByte E22 Series Manual](http://www.ebyte.com/)
- [LoRa Technology Overview](https://www.semtech.com/lora)
- [Raspberry Pi Documentation](https://www.raspberrypi.org/documentation/)

## ⚖️ License

- LoRa driver (`sx126x.py`): Provided by Waveshare
- Application code: Open for educational and personal use
- See individual file headers for specific terms

## 👥 Credits

- **Hardware**: Waveshare eByte LoRa HAT
- **Driver**: Waveshare (sx126x.py)
- **Application**: Custom implementation for image transmission

---

## 📋 Quick Command Reference

```bash
# Installation
./setup.sh                              # Automated setup
sudo pip3 install RPi.GPIO pyserial    # Manual install

# Testing
python3 test_setup.py                  # Verify setup
python3 optimize_image.py test.jpg     # Test optimization

# Basic Usage
python3 image_receiver.py              # Start receiver
python3 image_sender.py photo.jpg      # Send image

# Advanced
python3 optimize_image.py photo.jpg small  # Optimize first
python3 image_sender.py optimized.jpg 5    # Send to address 5
```

---

**Ready to transmit images over LoRa? Start with [QUICKSTART.md](QUICKSTART.md)!** 🚀📡📷

---

*Last Updated: November 2025*
*Tested on: Raspberry Pi 4B with E22-900T22S LoRa HAT*
