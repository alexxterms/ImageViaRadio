#!/usr/bin/python
# -*- coding: UTF-8 -*-

"""
Image Receiver for LoRa HAT
Receives JPEG images transmitted in chunks and reassembles them
"""

import sys
import sx126x
import time
import os
import hashlib
import termios
import tty

class ImageReceiver:
    def __init__(self, serial_num="/dev/ttyS0", freq=868, addr=1, power=22, 
                 output_dir="received_images"):
        """
        Initialize the Image Receiver
        
        Args:
            serial_num: Serial port (default: /dev/ttyS0)
            freq: Frequency in MHz (850-930 or 410-493)
            addr: Own address (0-65535)
            power: Transmit power in dBm (10, 13, 17, 22)
            output_dir: Directory to save received images
        """
        print("Initializing LoRa module...")
        self.node = sx126x.sx126x(
            serial_num=serial_num,
            freq=freq,
            addr=addr,
            power=power,
            rssi=False,
            air_speed=2400,
            buffer_size=240,
            relay=False
        )
        
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Created output directory: {output_dir}")
        
        # State variables for receiving
        self.receiving = False
        self.filename = None
        self.filesize = 0
        self.total_chunks = 0
        self.expected_checksum = None
        self.received_chunks = {}
        self.start_time = None
        
        print("LoRa module initialized successfully!")
        
    def calculate_checksum(self, data):
        """Calculate MD5 checksum of data"""
        return hashlib.md5(data).hexdigest()
    
    def reset_state(self):
        """Reset receiver state"""
        self.receiving = False
        self.filename = None
        self.filesize = 0
        self.total_chunks = 0
        self.expected_checksum = None
        self.received_chunks = {}
        self.start_time = None
    
    def process_packet(self, raw_data):
        """Process received packet"""
        try:
            # The LoRa module receives data in this format:
            # [sender_addr_high] [sender_addr_low] [sender_freq_offset] [payload...] [rssi if enabled]
            # So we skip the first 3 bytes to get to the payload
            
            if len(raw_data) < 3:
                return
            
            # Skip first 3 bytes (sender address + frequency)
            # If RSSI is enabled, skip last byte too
            if self.node.rssi and len(raw_data) > 3:
                payload = raw_data[3:-1]  # Skip first 3 and last 1
            else:
                payload = raw_data[3:]  # Skip first 3 bytes only
            
            # Check packet type
            if payload.startswith(b'IMGSTART'):
                self.handle_start_packet(payload)
            elif payload.startswith(b'IMGDATA'):
                self.handle_data_packet(payload)
            elif payload.startswith(b'IMG_END'):
                self.handle_end_packet(payload)
                
        except Exception as e:
            print(f"\nError processing packet: {e}")
            import traceback
            traceback.print_exc()
    
    def handle_start_packet(self, payload):
        """Handle START packet"""
        try:
            self.reset_state()
            
            # Parse: [Header: 8] [filename_len: 1] [filename: var] [filesize: 4] [total_chunks: 4] [checksum: 32]
            idx = 8  # Skip 'IMGSTART'
            filename_len = payload[idx]
            idx += 1
            
            self.filename = payload[idx:idx+filename_len].decode('utf-8')
            idx += filename_len
            
            self.filesize = int.from_bytes(payload[idx:idx+4], 'big')
            idx += 4
            
            self.total_chunks = int.from_bytes(payload[idx:idx+4], 'big')
            idx += 4
            
            self.expected_checksum = payload[idx:idx+32].decode('utf-8')
            
            self.receiving = True
            self.start_time = time.time()
            
            print(f"\n{'='*50}")
            print(f"Receiving image: {self.filename}")
            print(f"Size: {self.filesize} bytes")
            print(f"Total chunks: {self.total_chunks}")
            print(f"Checksum: {self.expected_checksum}")
            print(f"{'='*50}\n")
            
        except Exception as e:
            print(f"Error parsing START packet: {e}")
            self.reset_state()
    
    def handle_data_packet(self, payload):
        """Handle DATA packet"""
        if not self.receiving:
            return
        
        try:
            # Parse: [Header: 7] [chunk_num: 4] [chunk_data]
            chunk_num = int.from_bytes(payload[7:11], 'big')
            chunk_data = payload[11:]
            
            # Store chunk
            if chunk_num not in self.received_chunks:
                self.received_chunks[chunk_num] = chunk_data
                
                # Progress indicator
                received_count = len(self.received_chunks)
                progress = received_count / self.total_chunks * 100
                print(f"\rReceived: [{received_count}/{self.total_chunks}] {progress:.1f}%", 
                      end='', flush=True)
            
        except Exception as e:
            print(f"\nError parsing DATA packet: {e}")
    
    def handle_end_packet(self, payload):
        """Handle END packet and save the image"""
        if not self.receiving:
            return
        
        try:
            print("\n\nReceived END packet. Processing image...")
            
            # Check if we have all chunks
            if len(self.received_chunks) != self.total_chunks:
                missing = self.total_chunks - len(self.received_chunks)
                print(f"Warning: Missing {missing} chunks!")
                print(f"Received {len(self.received_chunks)}/{self.total_chunks} chunks")
            
            # Reassemble image
            image_data = b''
            for i in range(self.total_chunks):
                if i in self.received_chunks:
                    image_data += self.received_chunks[i]
                else:
                    print(f"Missing chunk {i}")
            
            # Verify checksum
            actual_checksum = self.calculate_checksum(image_data)
            checksum_match = actual_checksum == self.expected_checksum
            
            # Save image
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_filename = f"{timestamp}_{self.filename}"
            output_path = os.path.join(self.output_dir, output_filename)
            
            with open(output_path, 'wb') as f:
                f.write(image_data)
            
            # Calculate statistics
            duration = time.time() - self.start_time
            throughput = self.filesize / duration if duration > 0 else 0
            
            print(f"\n{'='*50}")
            print(f"Image saved: {output_path}")
            print(f"File size: {len(image_data)} bytes (expected: {self.filesize})")
            print(f"Checksum match: {'✓ YES' if checksum_match else '✗ NO'}")
            print(f"  Expected: {self.expected_checksum}")
            print(f"  Actual:   {actual_checksum}")
            print(f"Transfer time: {duration:.2f} seconds")
            print(f"Throughput: {throughput:.2f} bytes/sec")
            print(f"{'='*50}\n")
            
            self.reset_state()
            
        except Exception as e:
            print(f"\nError saving image: {e}")
            import traceback
            traceback.print_exc()
            self.reset_state()
    
    def listen(self):
        """Listen for incoming packets"""
        print("\nListening for images... (Press Ctrl+C to exit)")
        print(f"Configuration:")
        print(f"  Frequency: {self.node.freq} MHz")
        print(f"  Own address: {self.node.addr}")
        print(f"  Air speed: 2400 bps")
        print(f"  Buffer size: 240 bytes")
        print("-" * 50 + "\n")
        
        packet_count = 0
        last_check_time = time.time()
        
        try:
            while True:
                # Check if data is available
                bytes_waiting = self.node.ser.inWaiting()
                
                if bytes_waiting > 0:
                    # Show that we detected data
                    current_time = time.time()
                    if current_time - last_check_time > 2:  # Print status every 2 seconds
                        print(f"[Status] Buffer has {bytes_waiting} bytes waiting...")
                        last_check_time = current_time
                    
                    # Give more time for complete packet to arrive at slow air speed
                    time.sleep(0.3)
                    
                    # Read what's available now
                    raw_data = self.node.ser.read(self.node.ser.inWaiting())
                    
                    if len(raw_data) > 3:
                        packet_count += 1
                        
                        payload = raw_data[3:]
                        if payload.startswith(b'IMGSTART'):
                            print(f"\n[Packet #{packet_count}] START packet ({len(raw_data)} bytes)")
                        elif payload.startswith(b'IMG_END'):
                            print(f"\n[Packet #{packet_count}] END packet ({len(raw_data)} bytes)")
                        elif payload.startswith(b'IMGDATA'):
                            # Show occasional progress for data packets
                            if packet_count % 10 == 0:
                                print(f"[Packet #{packet_count}] DATA packet ({len(raw_data)} bytes)")
                        
                        self.process_packet(raw_data)
                else:
                    # No data waiting, small sleep to prevent CPU spinning
                    time.sleep(0.01)
                
        except KeyboardInterrupt:
            print("\n\nReceiver stopped by user")
            print(f"Total packets received: {packet_count}")


def main():
    print("\n" + "="*50)
    print("LoRa Image Receiver")
    print("="*50 + "\n")
    
    # Save terminal settings
    old_settings = termios.tcgetattr(sys.stdin)
    
    try:
        # Set terminal to raw mode
        tty.setcbreak(sys.stdin.fileno())
        
        receiver = ImageReceiver(
            serial_num="/dev/ttyS0",
            freq=868,
            addr=1,
            power=22,
            output_dir="received_images"
        )
        
        receiver.listen()
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Restore terminal settings
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)


if __name__ == "__main__":
    main()
