#!/usr/bin/python
# -*- coding: UTF-8 -*-

"""
Image Sender for LoRa HAT
Transmits JPEG images by splitting them into chunks
"""

import sys
import sx126x
import time
import os
import hashlib

class ImageSender:
    def __init__(self, serial_num="/dev/ttyS0", freq=868, addr=0, power=22, 
                 target_addr=1, chunk_size=200):
        """
        Initialize the Image Sender
        
        Args:
            serial_num: Serial port (default: /dev/ttyS0)
            freq: Frequency in MHz (850-930 or 410-493)
            addr: Own address (0-65535)
            power: Transmit power in dBm (10, 13, 17, 22)
            target_addr: Target node address to send to
            chunk_size: Size of each data chunk in bytes (max 200 for safety)
        """
        print("Initializing LoRa module...")
        # Use 240 byte buffer for maximum throughput
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
        
        self.target_addr = target_addr
        self.chunk_size = chunk_size
        self.freq = freq
        self.offset_freq = freq - (850 if freq > 850 else 410)
        print("LoRa module initialized successfully!")
        
    def calculate_checksum(self, data):
        """Calculate MD5 checksum of data"""
        return hashlib.md5(data).hexdigest()
    
    def send_image(self, image_path, delay_between_packets=4.0):
        """
        Send an image file via LoRa
        
        Args:
            image_path: Path to the JPEG image file
            delay_between_packets: Delay in seconds between packets (default: 1.0)
        """
        if not os.path.exists(image_path):
            print(f"Error: Image file '{image_path}' not found!")
            return False
            
        # Read the image file
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
        except Exception as e:
            print(f"Error reading image file: {e}")
            return False
            
        file_size = len(image_data)
        file_name = os.path.basename(image_path)
        checksum = self.calculate_checksum(image_data)
        
        print(f"\n{'='*50}")
        print(f"Image: {file_name}")
        print(f"Size: {file_size} bytes")
        print(f"Checksum: {checksum}")
        print(f"{'='*50}\n")
        
        # Calculate number of chunks
        total_chunks = (file_size + self.chunk_size - 1) // self.chunk_size
        print(f"Splitting into {total_chunks} chunks of {self.chunk_size} bytes each\n")
        
        # Send START packet with metadata
        self.send_start_packet(file_name, file_size, total_chunks, checksum)
        time.sleep(0.5)  # Give receiver time to prepare
        
        # Send data chunks
        for chunk_num in range(total_chunks):
            start_idx = chunk_num * self.chunk_size
            end_idx = min(start_idx + self.chunk_size, file_size)
            chunk_data = image_data[start_idx:end_idx]
            
            self.send_data_packet(chunk_num, chunk_data)
            
            # Progress indicator
            progress = (chunk_num + 1) / total_chunks * 100
            print(f"\rProgress: [{chunk_num + 1}/{total_chunks}] {progress:.1f}%", end='', flush=True)
            
            time.sleep(delay_between_packets)
        
        print("\n")
        
        # Send END packet
        self.send_end_packet(total_chunks, checksum)
        
        print(f"\n{'='*50}")
        print("Image transmission completed!")
        print(f"{'='*50}\n")
        
        return True
    
    def send_start_packet(self, filename, filesize, total_chunks, checksum):
        """Send START packet with file metadata"""
        # Packet format: [Header: 'IMGSTART'] [filename_len] [filename] [filesize] [total_chunks] [checksum]
        header = b'IMGSTART'
        filename_bytes = filename.encode('utf-8')[:50]  # Limit filename to 50 chars
        filename_len = len(filename_bytes)
        
        # Create metadata payload
        metadata = header + bytes([filename_len]) + filename_bytes
        metadata += filesize.to_bytes(4, 'big')
        metadata += total_chunks.to_bytes(4, 'big')
        metadata += checksum.encode('utf-8')[:32]
        
        self.send_packet(metadata)
        print("Sent START packet with metadata")
    
    def send_data_packet(self, chunk_num, chunk_data):
        """Send a data chunk packet"""
        # Packet format: [Header: 'IMGDATA'] [chunk_num: 4 bytes] [chunk_data]
        header = b'IMGDATA'
        chunk_num_bytes = chunk_num.to_bytes(4, 'big')
        packet_payload = header + chunk_num_bytes + chunk_data
        
        self.send_packet(packet_payload)
    
    def send_end_packet(self, total_chunks, checksum):
        """Send END packet to signal transmission complete"""
        # Packet format: [Header: 'IMG_END'] [total_chunks] [checksum]
        header = b'IMG_END'
        packet_payload = header + total_chunks.to_bytes(4, 'big') + checksum.encode('utf-8')[:32]
        
        self.send_packet(packet_payload)
        print("Sent END packet")
    
    def send_packet(self, payload):
        """
        Send a packet via LoRa with proper addressing
        Format: [target_addr_high] [target_addr_low] [freq_offset] 
                [own_addr_high] [own_addr_low] [own_freq_offset] [payload]
        """
        packet = bytes([self.target_addr >> 8])  # Target address high byte
        packet += bytes([self.target_addr & 0xff])  # Target address low byte
        packet += bytes([self.offset_freq])  # Target frequency offset
        packet += bytes([self.node.addr >> 8])  # Own address high byte
        packet += bytes([self.node.addr & 0xff])  # Own address low byte
        packet += bytes([self.node.offset_freq])  # Own frequency offset
        packet += payload
        
        self.node.send(packet)


def main():
    print("\n" + "="*50)
    print("LoRa Image Sender")
    print("="*50 + "\n")
    
    if len(sys.argv) < 2:
        print("Usage: python image_sender.py <image_path> [target_address]")
        print("Example: python image_sender.py photo.jpg 1")
        sys.exit(1)
    
    image_path = sys.argv[1]
    target_addr = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    
    try:
        sender = ImageSender(
            serial_num="/dev/ttyS0",
            freq=868,
            addr=0,
            power=22,
            target_addr=target_addr,
            chunk_size=200  # Safe chunk size (240 - overhead)
        )
        
        sender.send_image(image_path, delay_between_packets=0.1)
        
    except KeyboardInterrupt:
        print("\n\nTransmission interrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
