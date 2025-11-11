# Image Transfer over LoRa

Transfer images reliably over LoRa radio using bulk transfer + selective retransmission protocol.

## Protocol Overview

This implementation uses a smart hybrid approach:

1. **Phase 1: Bulk Transfer** - Sender transmits all chunks rapidly without waiting for ACKs
2. **Phase 2: Selective Retry** - Receiver reports only missing/corrupted chunks via NACK list
3. **Phase 3: Retransmission** - Sender retransmits only the failed chunks
4. **Phase 4: Completion** - Receiver assembles and saves the complete image

### Why This Approach?

- **Fast**: ~2× faster than per-chunk ACK (no wait between packets)
- **Reliable**: Checksums detect corruption, selective retries ensure 100% delivery
- **Efficient**: Only retransmit failed chunks, not entire file

## Hardware Requirements

- 2× Raspberry Pi (3B+, 4B, or Zero)
- 2× EBYTE E22 LoRa modules (SX126x-based)
- Properly configured serial ports (`/dev/ttyS0`)

## Installation

1. **Enable Serial Port** on both Raspberry Pis:
   ```bash
   sudo raspi-config
   # Interface Options -> Serial Port
   # - Disable serial console: NO
   # - Enable serial port hardware: YES
   ```

2. **Install Dependencies**:
   ```bash
   sudo apt-get update
   sudo apt-get install python3-rpi.gpio python3-serial
   ```

3. **Clone/Copy Files**:
   ```bash
   cd /home/pi/ImageViaRadio
   # Ensure you have: sx126x.py, send_image.py, receive_image.py
   chmod +x send_image.py receive_image.py
   ```

4. **Connect LoRa HAT**:
   - Attach HAT to Pi GPIO header
   - **Remove M0 and M1 jumpers** (controlled by GPIO)

## Usage

### Receiver Side (start first)

```bash
sudo python3 receive_image.py [my_address]
```

**Example**:
```bash
sudo python3 receive_image.py 0
```

The receiver will:
- Listen for incoming chunks
- Validate checksums
- Send NACK list when transfer completes
- Save received image as `received_XXXX.bin`

### Sender Side

```bash
sudo python3 send_image.py <image_file> [dest_address]
```

**Example**:
```bash
sudo python3 send_image.py photo.jpg 0
```

The sender will:
- Chunk the image to a temporary file
- Send all chunks rapidly
- Wait for NACK list from receiver
- Retransmit missing chunks
- Retry up to 3 rounds if needed

## Configuration

Edit the constants at the top of each script:

### Common Settings

```python
SERIAL = "/dev/ttyS0"      # Serial port
FREQ = 868                  # Frequency in MHz (850-930 or 410-493)
MY_ADDR = 0                 # This node's address (0-65534)
DEST_ADDR = 0               # Destination address
```

### Sender Settings

```python
CHUNK_SIZE = 200            # Bytes per chunk (max ~230)
INTER_CHUNK_DELAY = 0.05    # Seconds between chunks
NACK_TIMEOUT = 10.0         # Wait time for NACK list
MAX_RETRY_ROUNDS = 3        # Maximum retry attempts
```

### Receiver Settings

```python
RECV_TIMEOUT = 5.0          # Silence timeout to trigger NACK
NACK_ACK_TIMEOUT = 3.0      # Wait time for NACK ACK
MAX_NACK_RETRIES = 3        # NACK list retry attempts
```

### Airspeed Tradeoffs

Both scripts use `air_speed=62500` (62.5 kbps, maximum speed):

| Airspeed | Range | Speed | Best For |
|----------|-------|-------|----------|
| 2400     | Long  | Slow  | Max range, noisy environments |
| 9600     | Med   | Med   | Balanced |
| 62500    | Short | Fast  | Close range, clean link |

**To change**: Edit the `air_speed=62500` parameter in both scripts' `sx126x.sx126x()` initialization.

## Performance Estimates

**50 KB image at 62.5 kbps (256 chunks of 200 bytes)**:

- Perfect link (0% loss): ~33 seconds
- 5% packet loss: ~35 seconds
- 10% packet loss: ~40 seconds

**Compare to per-chunk ACK**: 60-90 seconds for same transfer.

## Protocol Details

### Packet Format

All packets start with a 6-byte addressing header:

```
[dest_addr_high][dest_addr_low][freq_offset]  # 3 bytes
[src_addr_high][src_addr_low][freq_offset]    # 3 bytes
```

### Data Packet (PKT_DATA = 0x01)

```
<addressing header>
[0x01]                          # Packet type
[file_id_high][file_id_low]     # 2 bytes
[seq_high][seq_low]             # 2 bytes
[checksum]                      # 1 byte (sum of data % 256)
[...chunk data...]              # up to 200 bytes
```

### END Packet (PKT_END = 0xFF)

```
<addressing header>
[0xFF]                          # Packet type
[file_id_high][file_id_low]     # 2 bytes
[total_high][total_low]         # 2 bytes (total chunks)
```

### NACK Packet (0xDD)

```
<addressing header>
[0xDD]                          # NACK marker
[file_id_high][file_id_low]     # 2 bytes
[num_missing_high][num_missing_low]  # 2 bytes
[seq1_high][seq1_low]           # 2 bytes per missing chunk
[seq2_high][seq2_low]
...
```

### ACK Packet (PKT_ACK = 0xAA)

```
<addressing header>
[0xAA]                          # ACK marker
[file_id_high][file_id_low]     # 2 bytes
[0x00][0x00]                    # 2 bytes (unused)
```

## Troubleshooting

### "Permission denied" on /dev/ttyS0
- Run with `sudo`, or add user to `dialout` group:
  ```bash
  sudo usermod -a -G dialout $USER
  # Log out and back in
  ```

### No packets received
- Check frequency and addresses match on both sides
- Verify antennas are connected
- Test with shorter distance
- Check M0/M1 jumpers are removed

### High packet loss
- Reduce airspeed (try 9600 or 2400)
- Increase transmission power (already max at 22 dBm)
- Check for interference
- Improve antenna placement

### Terminal in weird state after crash
```bash
reset
# or
stty sane
```

### Checksum failures
- Check for electrical interference near radio
- Try lower airspeed
- Verify power supply is stable

## File ID Collision

Each transfer uses a random 16-bit file_id (0x0100-0xFFFE). The probability of collision is very low, but if it happens:
- Receiver will mix chunks from two different files
- Restart receiver between transfers if you suspect collision

## Limitations

- **No multi-file queue**: One transfer at a time
- **No compression**: Sends raw bytes (add Pillow compression if needed)
- **No encryption**: Data sent in plaintext
- **NACK list size**: Max ~115 missing chunks per NACK packet (truncated if more)
- **No file type detection**: Receiver saves as `.bin` (rename manually)

## Future Enhancements

- Add optional JPEG compression with Pillow
- Implement file type detection and auto-extension
- Add progress bar with `tqdm`
- Support multiple concurrent transfers
- Add encryption layer
- Implement run-length encoding for large NACK lists
- Add forward error correction (FEC)

## License

Based on EBYTE E22 example code. Educational use only.

## Support

For issues with:
- **LoRa module**: Check EBYTE documentation
- **Protocol**: Review packet format and add debug prints
- **Hardware**: Verify GPIO connections and serial port config
