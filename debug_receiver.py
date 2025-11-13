#!/usr/bin/python
# -*- coding: UTF-8 -*-

"""
Debug Receiver - Shows raw data being received
Use this to troubleshoot communication issues
"""

import sys
import sx126x
import time
import termios
import tty

print("\n" + "="*60)
print("LoRa Debug Receiver - Raw Data Monitor")
print("="*60 + "\n")

# Initialize LoRa module
print("Initializing LoRa module...")
node = sx126x.sx126x(
    serial_num="/dev/ttyS0",
    freq=868,
    addr=1,           # Receiver address
    power=22,
    rssi=True,        # Enable RSSI to see signal strength
    air_speed=2400,
    buffer_size=240,
    relay=False
)

print("LoRa module initialized!")
print(f"Listening on frequency: 868 MHz")
print(f"Own address: 1")
print(f"Buffer size: 240 bytes")
print("\nWaiting for data... (Press Ctrl+C to exit)")
print("-" * 60 + "\n")

# Save terminal settings
old_settings = termios.tcgetattr(sys.stdin)

try:
    # Set terminal to raw mode
    tty.setcbreak(sys.stdin.fileno())
    
    packet_count = 0
    
    while True:
        if node.ser.inWaiting() > 0:
            packet_count += 1
            time.sleep(0.1)  # Wait for full packet
            raw_data = node.ser.read(node.ser.inWaiting())
            
            print(f"\n{'='*60}")
            print(f"Packet #{packet_count} - Received {len(raw_data)} bytes")
            print(f"{'='*60}")
            
            # Show raw bytes (hex)
            print("Raw data (hex):")
            hex_str = ' '.join([f'{b:02x}' for b in raw_data[:100]])  # First 100 bytes
            print(f"  {hex_str}")
            if len(raw_data) > 100:
                print(f"  ... (+ {len(raw_data) - 100} more bytes)")
            
            # Parse header
            if len(raw_data) >= 6:
                target_addr = (raw_data[0] << 8) + raw_data[1]
                target_freq = raw_data[2]
                sender_addr = (raw_data[3] << 8) + raw_data[4]
                sender_freq = raw_data[5]
                
                print(f"\nHeader info:")
                print(f"  Target address: {target_addr}")
                print(f"  Target freq offset: {target_freq}")
                print(f"  Sender address: {sender_addr}")
                print(f"  Sender freq offset: {sender_freq}")
                
                # Check if addressed to us
                if target_addr == 1 or target_addr == 65535:
                    print(f"  ✓ Packet addressed to us (addr {target_addr})")
                else:
                    print(f"  ✗ Packet NOT for us (target={target_addr}, we are 1)")
            
            # Show payload
            if len(raw_data) > 6:
                payload = raw_data[6:]
                print(f"\nPayload ({len(payload)} bytes):")
                
                # Try to interpret as text
                try:
                    # Check for known headers
                    if payload.startswith(b'IMGSTART'):
                        print("  Type: START packet")
                    elif payload.startswith(b'IMGDATA'):
                        print("  Type: DATA packet")
                    elif payload.startswith(b'IMG_END'):
                        print("  Type: END packet")
                    else:
                        # Try to decode as text
                        text_preview = payload[:50].decode('utf-8', errors='replace')
                        print(f"  Preview: {text_preview}")
                except:
                    print(f"  (Binary data)")
                
                # Show first bytes
                hex_payload = ' '.join([f'{b:02x}' for b in payload[:50]])
                print(f"  Hex: {hex_payload}")
                if len(payload) > 50:
                    print(f"       ... (+ {len(payload) - 50} more bytes)")
            
            print("-" * 60)
        
        time.sleep(0.01)  # Small delay

except KeyboardInterrupt:
    print("\n\nDebug receiver stopped by user")
    print(f"Total packets received: {packet_count}")
finally:
    # Restore terminal settings
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
