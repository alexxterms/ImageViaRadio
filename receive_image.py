#!/usr/bin/python
# -*- coding: UTF-8 -*-

"""
Image Receiver with Chunk Validation + NACK List
Protocol flow:
1. Receive chunks and validate checksums
2. Track missing/corrupted chunks
3. On END packet, send NACK list to sender
4. Wait for retransmissions
5. Repeat until complete, then save file
"""

import os
import sys
import time
import sx126x

# Configuration
SERIAL = "/dev/ttyS0"
FREQ = 433
MY_ADDR = 0          # This node's address
RECV_TIMEOUT = 5.0   # Seconds of silence before assuming END packet lost
NACK_ACK_TIMEOUT = 3.0  # Seconds to wait for ACK of NACK list
MAX_NACK_RETRIES = 3 # Maximum NACK list retries

# Packet type markers
PKT_DATA = 0x01
PKT_END = 0xFF
PKT_ACK = 0xAA

class ImageReceiver:
    def __init__(self, serial_num=SERIAL, freq=FREQ, my_addr=MY_ADDR):
        self.my_addr = my_addr
        self.node = sx126x.sx126x(
            serial_num=serial_num,
            freq=freq,
            addr=my_addr,
            power=22,
            rssi=False,
            air_speed=24000,  # Max speed
            relay=False
        )
        print(f"Receiver initialized: addr={my_addr}, freq={freq}MHz, airspeed=24kbps")

        # Storage for active transfers: file_id -> transfer_state
        self.transfers = {}

    def checksum(self, data):
        """Simple checksum: sum of all bytes modulo 256"""
        return sum(data) % 256

    def build_packet(self, dest_addr, pkt_type, file_id, seq, data=b""):
        """Build packet with addressing header + payload"""
        # Addressing header (6 bytes)
        header = bytes([
            (dest_addr >> 8) & 0xFF, dest_addr & 0xFF, self.node.offset_freq,
            (self.my_addr >> 8) & 0xFF, self.my_addr & 0xFF, self.node.offset_freq
        ])
        
        # Payload
        payload = bytes([
            pkt_type,
            (file_id >> 8) & 0xFF, file_id & 0xFF,
            (seq >> 8) & 0xFF, seq & 0xFF
        ]) + data
        
        return header + payload

    def send_packet(self, packet):
        """Send a packet via the LoRa module"""
        self.node.send(packet)

    def send_nack_list(self, sender_addr, file_id, missing_seqs):
        """Send NACK list to sender"""
        # Build NACK payload: type(1) + file_id(2) + num_missing(2) + seq_list
        num_missing = len(missing_seqs)
        
        # Check if NACK list fits in one packet (240 byte limit)
        # 6 (addressing) + 1 (type) + 2 (file_id) + 2 (num) + 2*num_missing
        max_seqs_per_packet = (230) // 2  # Conservative: ~115 seqs
        
        if num_missing > max_seqs_per_packet:
            print(f"⚠ Warning: NACK list too large ({num_missing} seqs), truncating to {max_seqs_per_packet}")
            missing_seqs = missing_seqs[:max_seqs_per_packet]
            num_missing = len(missing_seqs)
        
        # Build seq list
        seq_bytes = b""
        for seq in missing_seqs:
            seq_bytes += bytes([(seq >> 8) & 0xFF, seq & 0xFF])
        
        # NACK marker is 0xDD
        packet = self.build_packet(sender_addr, 0xDD, file_id, num_missing, seq_bytes)
        self.send_packet(packet)
        
        if num_missing == 0:
            print(f"✓ Sent COMPLETE notification (0 missing chunks)")
        else:
            print(f"✗ Sent NACK list: {num_missing} missing chunks")

    def wait_for_ack(self, file_id, timeout=NACK_ACK_TIMEOUT):
        """Wait for ACK from sender acknowledging NACK receipt"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.node.ser.in_waiting > 0:
                time.sleep(0.05)
                pkt = self.node.ser.read(self.node.ser.in_waiting)
                
                if len(pkt) < 6 + 5:
                    continue
                
                payload = pkt[6:]
                pkt_type = payload[0]
                recv_file_id = (payload[1] << 8) | payload[2]
                
                if pkt_type == PKT_ACK and recv_file_id == file_id:
                    print("✓ Received ACK for NACK list")
                    return True
            
            time.sleep(0.05)
        
        return False

    def process_data_packet(self, sender_addr, file_id, seq, checksum_byte, chunk_data):
        """Process a data chunk"""
        # Validate checksum
        expected_cs = self.checksum(chunk_data)
        
        if checksum_byte != expected_cs:
            print(f"✗ Chunk {seq}: checksum mismatch (expected {expected_cs}, got {checksum_byte})")
            # Will be marked as missing
            return False
        
        # Initialize transfer state if new
        if file_id not in self.transfers:
            self.transfers[file_id] = {
                "sender_addr": sender_addr,
                "chunks": {},
                "last_time": time.time(),
                "total_expected": None,
                "end_received": False
            }
        
        # Store chunk
        transfer = self.transfers[file_id]
        transfer["chunks"][seq] = chunk_data
        transfer["last_time"] = time.time()
        
        print(f"✓ Received chunk {seq} ({len(chunk_data)} bytes, {len(transfer['chunks'])} total)", end='\r')
        return True

    def process_end_packet(self, sender_addr, file_id, total_chunks):
        """Process END packet"""
        if file_id not in self.transfers:
            print(f"⚠ END packet for unknown file_id 0x{file_id:04X}, ignoring")
            return
        
        transfer = self.transfers[file_id]
        transfer["end_received"] = True
        transfer["total_expected"] = total_chunks
        transfer["last_time"] = time.time()
        
        print(f"\n✓ END packet received: expecting {total_chunks} total chunks")
        
        # Trigger NACK list generation
        self.handle_transfer_complete(file_id)

    def handle_transfer_complete(self, file_id):
        """Handle transfer completion: generate NACK list or save file"""
        transfer = self.transfers[file_id]
        sender_addr = transfer["sender_addr"]
        total_expected = transfer["total_expected"]
        received_chunks = transfer["chunks"]
        
        # Determine missing chunks
        if total_expected is None:
            # Don't know total yet, can't determine missing
            print("⚠ END packet without total_expected, inferring from max seq")
            total_expected = max(received_chunks.keys()) + 1 if received_chunks else 0
        
        missing_seqs = []
        for seq in range(total_expected):
            if seq not in received_chunks:
                missing_seqs.append(seq)
        
        print(f"\nTransfer summary: {len(received_chunks)}/{total_expected} chunks received")
        
        if len(missing_seqs) == 0:
            # Complete! Save file
            self.save_image(file_id)
        else:
            # Send NACK list
            print(f"Missing chunks: {missing_seqs[:10]}{'...' if len(missing_seqs) > 10 else ''}")
            
            for retry in range(MAX_NACK_RETRIES):
                self.send_nack_list(sender_addr, file_id, missing_seqs)
                
                # Wait for ACK
                if self.wait_for_ack(file_id):
                    print(f"Waiting for retransmissions...")
                    break
                else:
                    print(f"✗ No ACK received (retry {retry + 1}/{MAX_NACK_RETRIES})")
            else:
                print(f"✗ Failed to get ACK after {MAX_NACK_RETRIES} retries")

    def save_image(self, file_id):
        """Assemble and save the received image"""
        transfer = self.transfers[file_id]
        chunks = transfer["chunks"]
        
        # Sort chunks by sequence number
        sorted_seqs = sorted(chunks.keys())
        
        # Assemble file
        file_data = b""
        for seq in sorted_seqs:
            file_data += chunks[seq]
        
        # Save to file
        filename = f"received_{file_id:04X}.jpg"
        with open(filename, "wb") as f:
            f.write(file_data)
        
        print(f"\n✓✓✓ Image saved: {filename} ({len(file_data)} bytes) ✓✓✓")
        
        # Cleanup
        del self.transfers[file_id]

    def receive_loop(self):
        """Main receive loop"""
        print("\nListening for incoming image transfers...")
        print("Press Ctrl+C to exit\n")
        
        last_activity = {}  # file_id -> last_packet_time
        
        try:
            while True:
                # Check for incoming packets
                if self.node.ser.in_waiting > 0:
                    time.sleep(0.05)  # Let full packet arrive
                    pkt = self.node.ser.read(self.node.ser.in_waiting)
                    
                    if len(pkt) < 6 + 5:  # Minimum valid packet
                        continue
                    
                    # Parse addressing (skip first 6 bytes)
                    payload = pkt[6:]
                    
                    # Parse payload
                    pkt_type = payload[0]
                    file_id = (payload[1] << 8) | payload[2]
                    seq = (payload[3] << 8) | payload[4]
                    
                    # Extract sender address from packet header (bytes 3-4)
                    sender_addr = (pkt[3] << 8) | pkt[4]
                    
                    # Update activity timestamp
                    last_activity[file_id] = time.time()
                    
                    # Dispatch based on packet type
                    if pkt_type == PKT_DATA:
                        if len(payload) < 6:
                            continue
                        checksum_byte = payload[5]
                        chunk_data = payload[6:]
                        self.process_data_packet(sender_addr, file_id, seq, checksum_byte, chunk_data)
                    
                    elif pkt_type == PKT_END:
                        # seq field contains total_chunks for END packet
                        total_chunks = seq
                        self.process_end_packet(sender_addr, file_id, total_chunks)
                
                # Check for timeouts (END packet might have been lost)
                now = time.time()
                for file_id in list(self.transfers.keys()):
                    transfer = self.transfers[file_id]
                    if not transfer["end_received"] and now - transfer["last_time"] > RECV_TIMEOUT:
                        print(f"\n⚠ Timeout for file_id 0x{file_id:04X}, assuming END packet lost")
                        # Infer total from max received seq
                        max_seq = max(transfer["chunks"].keys()) if transfer["chunks"] else 0
                        transfer["total_expected"] = max_seq + 1
                        transfer["end_received"] = True
                        self.handle_transfer_complete(file_id)
                
                time.sleep(0.05)
        
        except KeyboardInterrupt:
            print("\n\nReceiver stopped.")


def main():
    if len(sys.argv) >= 2:
        my_addr = int(sys.argv[1])
    else:
        my_addr = MY_ADDR
    
    receiver = ImageReceiver(my_addr=my_addr)
    receiver.receive_loop()


if __name__ == "__main__":
    main()
