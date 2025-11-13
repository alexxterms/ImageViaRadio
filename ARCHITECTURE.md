# System Architecture - ImageViaRadio

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     SENDER RASPBERRY PI                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. JPEG Image File  →  2. Image Optimizer (optional)          │
│     photo.jpg            optimize_image.py                      │
│     50 KB                ↓                                      │
│                         photo_optimized.jpg (15 KB)             │
│                          ↓                                      │
│  3. Image Sender        image_sender.py                         │
│     - Reads image                                               │
│     - Calculates MD5 checksum                                   │
│     - Splits into 200-byte chunks                               │
│     - Creates packets with headers                              │
│                          ↓                                      │
│  4. LoRa Driver         sx126x.py                               │
│     - Controls GPIO (M0, M1)                                    │
│     - Manages serial communication                              │
│     - Sends packets via UART                                    │
│                          ↓                                      │
│  5. LoRa HAT Module                                             │
│     - LoRa modulation                                           │
│     - RF transmission at 868 MHz                                │
│     - 22 dBm transmit power                                     │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          │ ~~~~ RF Signal ~~~~
                          │ (1-5 km range)
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                     RECEIVER RASPBERRY PI                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. LoRa HAT Module                                             │
│     - Receives RF signal at 868 MHz                             │
│     - LoRa demodulation                                         │
│     - Outputs to UART                                           │
│                          ↓                                      │
│  2. LoRa Driver         sx126x.py                               │
│     - Reads serial data                                         │
│     - Manages GPIO                                              │
│                          ↓                                      │
│  3. Image Receiver      image_receiver.py                       │
│     - Receives packets                                          │
│     - Identifies packet type (START/DATA/END)                   │
│     - Stores chunks in memory                                   │
│     - Reassembles complete image                                │
│     - Verifies MD5 checksum                                     │
│                          ↓                                      │
│  4. Saved Image File                                            │
│     received_images/20251112_143022_photo.jpg                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Packet Flow Diagram

```
SENDER                                    RECEIVER
  │                                          │
  │  START Packet                            │
  │  ─────────────────────────────────────>  │  Prepare to receive
  │  [IMGSTART][filename][size][chunks][md5] │  Initialize buffers
  │                                          │
  │  DATA Packet #0                          │
  │  ─────────────────────────────────────>  │  Store chunk 0
  │  [IMGDATA][0][200 bytes of image data]   │
  │                                          │
  │  DATA Packet #1                          │
  │  ─────────────────────────────────────>  │  Store chunk 1
  │  [IMGDATA][1][200 bytes of image data]   │
  │                                          │
  │  DATA Packet #2                          │
  │  ─────────────────────────────────────>  │  Store chunk 2
  │  [IMGDATA][2][200 bytes of image data]   │
  │                                          │
  │           ...                            │
  │  (continues for all chunks)              │
  │           ...                            │
  │                                          │
  │  DATA Packet #74                         │
  │  ─────────────────────────────────────>  │  Store chunk 74
  │  [IMGDATA][74][200 bytes of image data]  │
  │                                          │
  │  END Packet                              │
  │  ─────────────────────────────────────>  │  Reassemble image
  │  [IMG_END][total_chunks][md5]            │  Verify checksum
  │                                          │  Save to file
  │                                          │  ✓ Complete!
  │                                          │
```

## Packet Structure Details

```
┌──────────────────────────────────────────────────────────────┐
│                    LoRa Packet Format                        │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Byte 0-1:  Target Address (16-bit)                         │
│  Byte 2:    Target Frequency Offset                         │
│  Byte 3-4:  Source Address (16-bit)                         │
│  Byte 5:    Source Frequency Offset                         │
│  Byte 6+:   Payload (variable length, max ~230 bytes)       │
│                                                              │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                    START Packet Payload                      │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Bytes 0-7:     Header "IMGSTART" (8 bytes)                 │
│  Byte 8:        Filename length (1 byte)                    │
│  Bytes 9-N:     Filename (variable, max 50 bytes)           │
│  Bytes N+1-N+4: File size (4 bytes, big-endian)             │
│  Bytes N+5-N+8: Total chunks (4 bytes, big-endian)          │
│  Bytes N+9-N+40: MD5 checksum (32 bytes, hex string)        │
│                                                              │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                    DATA Packet Payload                       │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Bytes 0-6:     Header "IMGDATA" (7 bytes)                  │
│  Bytes 7-10:    Chunk number (4 bytes, big-endian)          │
│  Bytes 11+:     Chunk data (200 bytes, or less for last)    │
│                                                              │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                    END Packet Payload                        │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Bytes 0-6:     Header "IMG_END" (7 bytes)                  │
│  Bytes 7-10:    Total chunks (4 bytes, big-endian)          │
│  Bytes 11-42:   MD5 checksum (32 bytes, hex string)         │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## State Machine - Receiver

```
┌─────────────┐
│    IDLE     │  ← Initial state
└──────┬──────┘
       │
       │ START packet received
       ▼
┌─────────────┐
│ RECEIVING   │  ← Collecting DATA packets
└──────┬──────┘
       │
       │ END packet received
       ▼
┌─────────────┐
│ PROCESSING  │  ← Reassembling & verifying
└──────┬──────┘
       │
       │ Save complete
       ▼
┌─────────────┐
│    IDLE     │  ← Ready for next image
└─────────────┘
```

## File Processing Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                  SENDER: Image Processing                        │
└──────────────────────────────────────────────────────────────────┘

Original Image              Optimization (Optional)
   photo.jpg               optimize_image.py
   100 KB                           │
   1024x768                         ▼
      │                      ┌──────────────┐
      │                      │  Resize      │
      │                      │  640x480     │
      │                      └──────┬───────┘
      │                             │
      │                      ┌──────▼───────┐
      │                      │  Compress    │
      │                      │  Quality 75% │
      │                      └──────┬───────┘
      │                             │
      └─────────────────────────────▼
                          photo_optimized.jpg
                          30 KB
                          640x480
                               │
                               ▼
                      ┌─────────────────┐
                      │  Read file      │
                      │  Calculate MD5  │
                      └────────┬────────┘
                               │
                      ┌────────▼────────┐
                      │  Split into     │
                      │  chunks (200 B) │
                      └────────┬────────┘
                               │
                      ┌────────▼────────┐
                      │  Add headers &  │
                      │  sequencing     │
                      └────────┬────────┘
                               │
                               ▼
                        Transmit packets

┌──────────────────────────────────────────────────────────────────┐
│                  RECEIVER: Image Reconstruction                  │
└──────────────────────────────────────────────────────────────────┘

Receive packets
      │
      ▼
┌─────────────┐
│  START pkt  │  → Extract metadata
└──────┬──────┘    (filename, size, chunks, checksum)
       │
       ▼
┌─────────────┐
│  DATA pkts  │  → Store chunks in memory dictionary
└──────┬──────┘    {0: bytes, 1: bytes, 2: bytes, ...}
       │
       ▼
┌─────────────┐
│  END packet │  → Trigger reassembly
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Reassemble      │  → Concatenate chunks in order
│ image_data = [] │    for i in range(total_chunks):
│ for chunk...    │        image_data += chunks[i]
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Verify checksum │  → Calculate MD5
│ MD5(image_data) │    Compare with expected
└────────┬────────┘    ✓ Match? → Good!
         │             ✗ Mismatch? → Corrupted
         ▼
┌─────────────────┐
│ Save to file    │  → received_images/timestamp_filename.jpg
│ with timestamp  │
└─────────────────┘
```

## Timing Diagram

```
Time    Sender                                Receiver
(sec)   
────────────────────────────────────────────────────────────────
 0.0    Send START packet ──────────────────→ Receive START
        "photo.jpg, 15000 bytes, 75 chunks"   Initialize buffers

 0.1    Send DATA chunk 0 ───────────────────→ Store chunk 0
        [200 bytes]

 0.2    Send DATA chunk 1 ───────────────────→ Store chunk 1
        [200 bytes]

 0.3    Send DATA chunk 2 ───────────────────→ Store chunk 2
        [200 bytes]

 ...    ... (continue for all chunks) ...     ... (buffering) ...

 7.4    Send DATA chunk 74 ──────────────────→ Store chunk 74
        [200 bytes]

 7.5    Send END packet ─────────────────────→ Receive END
        "75 chunks, checksum"                  Begin processing
                                               Reassemble chunks
                                               Verify checksum: ✓
                                               Save file
                                               Display stats

 7.6                                           Ready for next image
────────────────────────────────────────────────────────────────

Total Time: ~7.6 seconds for 15 KB image (with 0.1s delay)
Throughput: ~1,975 bytes/second
```

## Hardware Connection Diagram

```
┌────────────────────────────────────┐
│      Raspberry Pi (Sender)         │
│                                    │
│  GPIO Header (40-pin)              │
│  ┌──────────────────────────────┐ │
│  │ Pin 1  [3.3V]    [5V]  Pin 2 │ │
│  │ Pin 3  [GPIO 2]  [5V]  Pin 4 │ │
│  │ ...                      ...  │ │
│  │ Pin 13 [GPIO 27] - M1         │ │  ←─ LoRa HAT Control
│  │ Pin 15 [GPIO 22] - M0         │ │  ←─ LoRa HAT Control
│  │ ...                      ...  │ │
│  │ Pin 8  [GPIO 14] - TXD        │ │  ←─ Serial TX
│  │ Pin 10 [GPIO 15] - RXD        │ │  ←─ Serial RX
│  └──────────────────────────────┘ │
└─────────────┬──────────────────────┘
              │
              │ (Stacks on top)
              ▼
┌────────────────────────────────────┐
│      eByte LoRa HAT                │
│                                    │
│  ┌────────────────────┐            │
│  │  E22 LoRa Module   │            │
│  │  868/915 MHz       │            │
│  │  22 dBm output     │            │
│  └────────┬───────────┘            │
│           │                        │
│      ┌────▼────┐                   │
│      │ Antenna │ ← SMA Connector   │
│      │    ═╪═  │   (or IPEX)       │
│      └─────────┘                   │
└────────────────────────────────────┘

              │
              │ ~~~~ 868 MHz RF ~~~~
              │    (up to 5 km)
              │
              ▼
          
┌────────────────────────────────────┐
│      eByte LoRa HAT                │
│      (Receiver)                    │
│  ┌────────────────────┐            │
│  │ Antenna            │            │
│  │    ═╪═             │            │
│  └─────┬──────────────┘            │
│        │                           │
│  ┌─────▼──────────────┐            │
│  │  E22 LoRa Module   │            │
│  │  868/915 MHz       │            │
│  └────────────────────┘            │
└─────────────┬──────────────────────┘
              │
              │ (Stacks on top)
              ▼
┌────────────────────────────────────┐
│      Raspberry Pi (Receiver)       │
│                                    │
│  Same GPIO connections as sender   │
│                                    │
└────────────────────────────────────┘
```

## Memory Usage Flow

```
SENDER (Minimal Memory Usage)
─────────────────────────────
1. Read entire image into memory
   image_data = [15,000 bytes]

2. Process chunk by chunk
   for i in range(75):
       chunk = image_data[i*200 : (i+1)*200]
       send(chunk)
       # Previous chunk released from memory

Memory Peak: ~15 KB + overhead


RECEIVER (Buffered Memory Usage)
─────────────────────────────────
1. Receive START packet
   Store metadata

2. Receive DATA packets
   chunks = {
       0: [200 bytes],
       1: [200 bytes],
       2: [200 bytes],
       ...
       74: [200 bytes]
   }
   Memory grows with each packet

3. Reassemble
   image_data = chunks[0] + chunks[1] + ... + chunks[74]
   
Memory Peak: ~30 KB (chunks + reassembled)
```

## Error Handling Flow

```
┌──────────────┐
│ Send Packet  │
└──────┬───────┘
       │
       ▼
┌──────────────┐     Timeout?
│ Receive Ack? │────────No─────┐
└──────┬───────┘                │
       │ Yes                    │
       ▼                        ▼
┌──────────────┐         ┌──────────────┐
│   Success    │         │  (Continue)  │
└──────────────┘         │ No auto-retry│
                         │ User can     │
                         │ resend image │
                         └──────────────┘

Note: Current implementation does not include
automatic retry. Reliability achieved through:
- Configurable packet delays
- Checksum verification
- Manual resend if needed
```

---

This architecture ensures reliable image transmission over LoRa
with configurable parameters for different use cases and environments.
