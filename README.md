# Image Transmission via LoRa Radio

This project enables JPEG image transmission over LoRa radio using the Waveshare eByte Raspberry Pi LoRa HAT.

## Hardware Requirements

- Raspberry Pi (3B+, 4B, or Zero series)
- Waveshare eByte LoRa HAT (E22-400T22S or E22-900T22S)
- Two setups for sender and receiver

## Software Requirements

```bash
sudo apt-get update
sudo apt-get install python3 python3-pip
sudo pip3 install RPi.GPIO pyserial
```

## Setup

1. **Enable Serial Interface**
   ```bash
   sudo raspi-config
   ```
   - Navigate to: Interface Options → Serial Port
   - Disable serial login shell: No
   - Enable serial interface: Yes
   - Reboot

2. **Hardware Configuration**
   - Attach LoRa HAT to Raspberry Pi GPIO header
   - Remove M0 and M1 jumpers from the HAT when connected to RPi

## Project Files

- `sx126x.py` - LoRa driver provided by Waveshare
- `image_sender.py` - Transmits JPEG images
- `image_receiver.py` - Receives and saves JPEG images
- `main.py` - Original example script

## Usage

### Receiver Side (Run First)

On the receiving Raspberry Pi:

```bash
python3 image_receiver.py
```

**Configuration:**
- Address: 1
- Frequency: 868 MHz
- Saves images to `received_images/` directory

### Sender Side

On the sending Raspberry Pi:

```bash
python3 image_sender.py <image_path> [target_address]
```

**Examples:**
```bash
# Send to address 1 (default)
python3 image_sender.py photo.jpg

# Send to specific address
python3 image_sender.py photo.jpg 1

# Send with custom path
python3 image_sender.py /home/pi/Pictures/sunset.jpg 1
```

**Configuration:**
- Address: 0
- Frequency: 868 MHz
- Target: Address 1 (configurable)

## How It Works

### Transmission Protocol

1. **START Packet**
   - Contains: filename, file size, total chunks, MD5 checksum
   - Prepares receiver for incoming data

2. **DATA Packets**
   - Each contains: chunk number + image data (200 bytes)
   - Numbered sequentially for reassembly
   - Progress displayed in real-time

3. **END Packet**
   - Signals transmission complete
   - Contains: total chunks, checksum for verification

### Packet Structure

```
[Target Addr High][Target Addr Low][Freq Offset]
[Own Addr High][Own Addr Low][Own Freq Offset]
[Payload Data]
```

### Data Chunking

- Images are split into 200-byte chunks
- LoRa buffer size: 240 bytes (200 data + overhead)
- Chunks numbered for proper reassembly
- MD5 checksum verifies integrity

## Configuration Options

### Frequency Bands

- **E22-400T22S**: 410-493 MHz
- **E22-900T22S**: 850-930 MHz

Default: 868 MHz

### Transmit Power

- 10 dBm (10 mW)
- 13 dBm (20 mW)
- 17 dBm (50 mW)
- 22 dBm (158 mW) - Default, maximum range

### Air Speed

- 1200 bps
- 2400 bps - Default, good balance
- 4800 bps
- 9600 bps
- 19200 bps
- 38400 bps
- 62500 bps - Fastest, shortest range

### Addresses

- Range: 0-65535
- Address 65535: Broadcast (receives from all)
- Nodes must match address and frequency to communicate

## Customization

### Change Sender Configuration

Edit `image_sender.py`:

```python
sender = ImageSender(
    serial_num="/dev/ttyS0",
    freq=868,              # Change frequency
    addr=0,                # Change own address
    power=22,              # Change power (10, 13, 17, 22)
    target_addr=1,         # Change target address
    chunk_size=200         # Adjust chunk size (max 200)
)
```

### Change Receiver Configuration

Edit `image_receiver.py`:

```python
receiver = ImageReceiver(
    serial_num="/dev/ttyS0",
    freq=868,              # Match sender frequency
    addr=1,                # Must match sender's target_addr
    power=22,
    output_dir="received_images"  # Change save directory
)
```

### Adjust Transmission Speed

In `image_sender.py`, modify delay:

```python
sender.send_image(image_path, delay_between_packets=0.1)  # seconds
```

- Lower values = faster transmission, higher packet loss risk
- Higher values = slower transmission, more reliable
- Recommended: 0.05 - 0.2 seconds

## Performance

### Typical Transmission Rates

- **2400 bps air speed**: ~200-300 bytes/second
- **9600 bps air speed**: ~600-800 bytes/second

### Example Transfer Times

| Image Size | Time (2400 bps) | Time (9600 bps) |
|------------|-----------------|-----------------|
| 10 KB      | ~40 seconds     | ~15 seconds     |
| 50 KB      | ~3 minutes      | ~1 minute       |
| 100 KB     | ~6 minutes      | ~2 minutes      |

*Note: Times include packet overhead and delays*

## Troubleshooting

### Permission Denied on /dev/ttyS0

```bash
sudo usermod -a -G dialout $USER
# Logout and login again
```

### No Data Received

1. Check frequency matches on both devices
2. Verify addresses (sender's target_addr = receiver's addr)
3. Check antenna connections
4. Ensure modules are in normal mode (M0=LOW, M1=LOW)
5. Verify serial port is enabled in raspi-config

### Incomplete Transmission

1. Increase `delay_between_packets` in sender
2. Check for interference on the frequency
3. Reduce distance between devices
4. Increase transmit power

### Checksum Mismatch

1. Increase delay between packets
2. Check for RF interference
3. Resend the image
4. Lower air speed for more reliability

## Advanced Features

### Send with Higher Reliability

```python
# In image_sender.py, increase delay
sender.send_image(image_path, delay_between_packets=0.2)

# Use lower air speed for better range
self.node = sx126x.sx126x(
    serial_num=serial_num,
    freq=freq,
    addr=addr,
    power=power,
    rssi=False,
    air_speed=1200,  # Lower = more reliable
    buffer_size=240,
    relay=False
)
```

### Monitor Signal Strength

Enable RSSI (Received Signal Strength Indicator):

```python
self.node = sx126x.sx126x(
    serial_num=serial_num,
    freq=freq,
    addr=addr,
    power=power,
    rssi=True,  # Enable RSSI monitoring
    air_speed=2400,
    buffer_size=240,
    relay=False
)
```

## Technical Specifications

- **Modulation**: LoRa (Long Range)
- **Frequency Bands**: 410-493 MHz or 850-930 MHz
- **Max Power**: 22 dBm (158 mW)
- **Communication Range**: 
  - Line of sight: up to 3-5 km
  - Urban: 1-2 km
- **Max Packet Size**: 240 bytes
- **Addressing**: 16-bit (0-65535)

## License

This project uses the Waveshare driver which is provided as-is. Check manufacturer documentation for specific license terms.

## References

- [Waveshare LoRa HAT Documentation](https://www.waveshare.com/)
- [eByte E22 Series Manual](http://www.ebyte.com/)
- Original driver by Waveshare

## Support

For issues specific to:
- **LoRa HAT hardware**: Contact Waveshare support
- **This implementation**: Check the code comments and adjust parameters
- **Raspberry Pi serial setup**: Consult Raspberry Pi documentation
