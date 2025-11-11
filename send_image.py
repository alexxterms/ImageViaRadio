#!/usr/bin/python
# -*- coding: UTF-8 -*-

"""
Image Sender with Bulk Transfer + Selective Retransmission
Uses a hybrid protocol:
1. Pre-chunk image to file
2. Send all chunks without waiting for ACK (fast)
3. Send END marker
4. Wait for NACK list from receiver
5. Selectively retransmit failed chunks
"""

import os
import sys
import time
import math
import random
import sx126x

# Configuration
SERIAL = "/dev/ttyS0"
FREQ = 433
MY_ADDR = 0          # This node's address
DEST_ADDR = 0        # Destination node address
CHUNK_SIZE = 200     # Bytes of image data per chunk
INTER_CHUNK_DELAY = 0.05  # Seconds between chunks during bulk send
NACK_TIMEOUT = 10.0  # Seconds to wait for NACK list after END packet
MAX_RETRY_ROUNDS = 3 # Maximum retransmission rounds

# Packet type markers
PKT_DATA = 0x01
PKT_END = 0xFF
PKT_ACK = 0xAA

class ImageSender:
    def __init__(self, serial_num=SERIAL, freq=FREQ, my_addr=MY_ADDR, dest_addr=DEST_ADDR):
        self.my_addr = my_addr
        self.dest_addr = dest_addr
        self.node = sx126x.sx126x(
            serial_num=serial_num,
            freq=freq,
            addr=my_addr,
            power=22,
            rssi=False,
            air_speed=24000,  # Max speed for faster transfer
            relay=False
        )
        print(f"Sender initialized: addr={my_addr}, freq={freq}MHz, airspeed=24kbps")

    def checksum(self, data):
        """Simple checksum: sum of all bytes modulo 256"""
        return sum(data) % 256

    def chunk_image_to_file(self, image_path, chunk_file):
        """Read image and save chunks to a file with headers"""
        with open(image_path, "rb") as f:
            image_data = f.read()
        
        file_size = len(image_data)
        total_chunks = math.ceil(file_size / CHUNK_SIZE)
        file_id = random.randint(0x0100, 0xFFFE)  # Avoid 0x00 and 0xFF
        
        print(f"Chunking {os.path.basename(image_path)}: {file_size} bytes -> {total_chunks} chunks")
        print(f"File ID: 0x{file_id:04X}")
        
        # Save chunks with metadata
        with open(chunk_file, "wb") as cf:
            # Write header: file_id (2), total_chunks (2), file_size (4)
            cf.write(bytes([
                (file_id >> 8) & 0xFF, file_id & 0xFF,
                (total_chunks >> 8) & 0xFF, total_chunks & 0xFF,
                (file_size >> 24) & 0xFF, (file_size >> 16) & 0xFF,
                (file_size >> 8) & 0xFF, file_size & 0xFF
            ]))
            
            # Write each chunk with its header
            for seq in range(total_chunks):
                start = seq * CHUNK_SIZE
                chunk_data = image_data[start:start + CHUNK_SIZE]
                cs = self.checksum(chunk_data)
                
                # Chunk format: seq(2) + checksum(1) + data
                cf.write(bytes([
                    (seq >> 8) & 0xFF, seq & 0xFF,
                    cs
                ]))
                cf.write(chunk_data)
        
        return file_id, total_chunks, file_size

    def build_packet(self, pkt_type, file_id, seq, data=b""):
        """Build packet with addressing header + payload"""
        # Addressing header (6 bytes)
        header = bytes([
            (self.dest_addr >> 8) & 0xFF, self.dest_addr & 0xFF, self.node.offset_freq,
            (self.my_addr >> 8) & 0xFF, self.my_addr & 0xFF, self.node.offset_freq
        ])
        
        # Payload: type(1) + file_id(2) + seq(2) + data
        payload = bytes([
            pkt_type,
            (file_id >> 8) & 0xFF, file_id & 0xFF,
            (seq >> 8) & 0xFF, seq & 0xFF
        ]) + data
        
        return header + payload

    def send_packet(self, packet):
        """Send a packet via the LoRa module"""
        self.node.send(packet)

    def send_all_chunks(self, chunk_file, file_id, total_chunks):
        """Send all chunks from file without waiting for ACK"""
        print(f"\nPhase 1: Bulk sending {total_chunks} chunks...")
        
        with open(chunk_file, "rb") as cf:
            # Skip header
            cf.read(8)
            
            for seq in range(total_chunks):
                # Read chunk: seq(2) + checksum(1) + data
                seq_bytes = cf.read(2)
                checksum_byte = cf.read(1)
                chunk_data = cf.read(CHUNK_SIZE)
                
                # Build and send packet
                packet = self.build_packet(PKT_DATA, file_id, seq, checksum_byte + chunk_data)
                self.send_packet(packet)
                
                print(f"Sent chunk {seq + 1}/{total_chunks}", end='\r')
                time.sleep(INTER_CHUNK_DELAY)
        
        print(f"\nAll {total_chunks} chunks sent.")

    def send_end_packet(self, file_id):
        """Send END marker packet"""
        packet = self.build_packet(PKT_END, file_id, 0xFFFF)
        self.send_packet(packet)
        print("END packet sent.")

    def wait_for_nack(self, file_id, timeout=NACK_TIMEOUT):
        """Wait for NACK list from receiver"""
        print(f"\nWaiting for NACK list (timeout {timeout}s)...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.node.ser.in_waiting > 0:
                time.sleep(0.1)  # Let full packet arrive
                pkt = self.node.ser.read(self.node.ser.in_waiting)
                
                if len(pkt) < 6 + 5:  # min: 6 addressing + 1 type + 2 file_id + 2 num_missing
                    continue
                
                # Parse: skip 6 addressing bytes
                payload = pkt[6:]
                pkt_type = payload[0]
                recv_file_id = (payload[1] << 8) | payload[2]
                
                if pkt_type == 0xDD and recv_file_id == file_id:  # NACK marker
                    num_missing = (payload[3] << 8) | payload[4]
                    
                    if num_missing == 0:
                        print("✓ No missing chunks! Transfer complete.")
                        return []
                    
                    # Extract missing sequence numbers
                    missing_seqs = []
                    for i in range(num_missing):
                        offset = 5 + i * 2
                        if offset + 1 < len(payload):
                            seq = (payload[offset] << 8) | payload[offset + 1]
                            missing_seqs.append(seq)
                    
                    print(f"✗ Received NACK list: {num_missing} missing chunks")
                    return missing_seqs
            
            time.sleep(0.1)
        
        print("✗ Timeout waiting for NACK list")
        return None  # Timeout

    def send_ack_for_nack(self, file_id):
        """Send ACK to acknowledge NACK list receipt"""
        packet = self.build_packet(PKT_ACK, file_id, 0x0000)
        self.send_packet(packet)
        print("ACK sent for NACK list receipt")

    def retransmit_chunks(self, chunk_file, file_id, missing_seqs):
        """Retransmit specific chunks"""
        print(f"\nPhase 2: Retransmitting {len(missing_seqs)} chunks...")
        
        with open(chunk_file, "rb") as cf:
            # Skip header
            cf.read(8)
            
            # Build index of chunk positions
            chunk_positions = {}
            pos = 8
            seq = 0
            while True:
                cf.seek(pos)
                seq_bytes = cf.read(2)
                if len(seq_bytes) < 2:
                    break
                checksum_byte = cf.read(1)
                chunk_data = cf.read(CHUNK_SIZE)
                chunk_positions[seq] = (pos, len(checksum_byte + chunk_data))
                pos += 2 + 1 + len(chunk_data)
                seq += 1
            
            # Retransmit requested chunks
            for idx, seq in enumerate(missing_seqs):
                if seq not in chunk_positions:
                    print(f"✗ Warning: chunk {seq} not found in file")
                    continue
                
                pos, size = chunk_positions[seq]
                cf.seek(pos + 2)  # Skip seq bytes
                checksum_byte = cf.read(1)
                chunk_data = cf.read(CHUNK_SIZE)
                
                packet = self.build_packet(PKT_DATA, file_id, seq, checksum_byte + chunk_data)
                self.send_packet(packet)
                
                print(f"Retransmitted chunk {seq} ({idx + 1}/{len(missing_seqs)})", end='\r')
                time.sleep(INTER_CHUNK_DELAY)
        
        print(f"\nRetransmission complete: {len(missing_seqs)} chunks sent.")

    def send_image(self, image_path):
        """Main send logic with retry rounds"""
        # Prepare chunks
        chunk_file = "chunks_temp.dat"
        file_id, total_chunks, file_size = self.chunk_image_to_file(image_path, chunk_file)
        
        try:
            # Phase 1: Bulk send
            self.send_all_chunks(chunk_file, file_id, total_chunks)
            self.send_end_packet(file_id)
            
            # Phase 2: Retry loop
            for retry_round in range(MAX_RETRY_ROUNDS):
                missing_seqs = self.wait_for_nack(file_id)
                
                if missing_seqs is None:
                    print(f"✗ No response from receiver (round {retry_round + 1}/{MAX_RETRY_ROUNDS})")
                    if retry_round < MAX_RETRY_ROUNDS - 1:
                        print("Resending END packet...")
                        self.send_end_packet(file_id)
                    continue
                
                if len(missing_seqs) == 0:
                    # Success!
                    print(f"\n✓ Image transfer complete: {os.path.basename(image_path)}")
                    print(f"  File size: {file_size} bytes")
                    print(f"  Total chunks: {total_chunks}")
                    print(f"  Retry rounds: {retry_round}")
                    break
                
                # Send ACK for NACK list
                self.send_ack_for_nack(file_id)
                
                # Retransmit missing chunks
                self.retransmit_chunks(chunk_file, file_id, missing_seqs)
                self.send_end_packet(file_id)
            else:
                print(f"\n✗ Transfer failed after {MAX_RETRY_ROUNDS} retry rounds")
        
        finally:
            # Cleanup
            if os.path.exists(chunk_file):
                os.remove(chunk_file)
                print(f"Cleaned up temporary file: {chunk_file}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python send_image.py <image_file> [dest_addr]")
        print("Example: python send_image.py photo.jpg 0")
        sys.exit(1)
    
    image_path = sys.argv[1]
    if not os.path.exists(image_path):
        print(f"Error: File not found: {image_path}")
        sys.exit(1)
    
    dest_addr = int(sys.argv[2]) if len(sys.argv) >= 3 else DEST_ADDR
    
    sender = ImageSender(dest_addr=dest_addr)
    sender.send_image(image_path)


if __name__ == "__main__":
    main()
