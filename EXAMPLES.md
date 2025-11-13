#!/usr/bin/python
# -*- coding: UTF-8 -*-

"""
Example Usage Scripts for LoRa Image Transmission
Shows common use cases and code patterns
"""

import os
import time

print("""
╔═══════════════════════════════════════════════════════════════╗
║         LoRa Image Transmission - Usage Examples             ║
╚═══════════════════════════════════════════════════════════════╝

This file contains example usage patterns for the image transmission
system. Copy and modify these examples for your specific needs.

""")

# ============================================================================
# EXAMPLE 1: Basic Image Sending
# ============================================================================
print("="*70)
print("EXAMPLE 1: Basic Image Sending")
print("="*70)
print("""
# Send a single image to the default receiver (address 1)

from image_sender import ImageSender

sender = ImageSender(
    serial_num="/dev/ttyS0",
    freq=868,           # Frequency in MHz
    addr=0,             # Own address
    power=22,           # Transmit power in dBm
    target_addr=1       # Target receiver address
)

sender.send_image("photo.jpg")
""")

# ============================================================================
# EXAMPLE 2: Send to Multiple Receivers
# ============================================================================
print("\n" + "="*70)
print("EXAMPLE 2: Send to Multiple Receivers")
print("="*70)
print("""
# Send the same image to multiple receivers sequentially

from image_sender import ImageSender

sender = ImageSender(
    serial_num="/dev/ttyS0",
    freq=868,
    addr=0,
    power=22,
    target_addr=1  # Will be changed for each receiver
)

image_path = "photo.jpg"
receivers = [1, 2, 3]  # List of receiver addresses

for receiver_addr in receivers:
    print(f"Sending to receiver {receiver_addr}...")
    sender.target_addr = receiver_addr
    sender.offset_freq = 868 - 850  # Update if needed
    sender.send_image(image_path, delay_between_packets=0.1)
    time.sleep(2)  # Wait between transmissions

print("All transmissions complete!")
""")

# ============================================================================
# EXAMPLE 3: Optimize Before Sending
# ============================================================================
print("\n" + "="*70)
print("EXAMPLE 3: Optimize Before Sending")
print("="*70)
print("""
# Optimize image for faster transmission

from optimize_image import ImageOptimizer
from image_sender import ImageSender

# Step 1: Optimize the image
optimizer = ImageOptimizer()
optimized_path = optimizer.optimize_image(
    "large_photo.jpg",
    preset='small'  # thumbnail, small, medium, or large
)

# Step 2: Send optimized image
if optimized_path:
    sender = ImageSender(
        serial_num="/dev/ttyS0",
        freq=868,
        addr=0,
        power=22,
        target_addr=1
    )
    sender.send_image(optimized_path)
""")

# ============================================================================
# EXAMPLE 4: Batch Send Multiple Images
# ============================================================================
print("\n" + "="*70)
print("EXAMPLE 4: Batch Send Multiple Images")
print("="*70)
print("""
# Send all images in a directory

import os
from image_sender import ImageSender

sender = ImageSender(
    serial_num="/dev/ttyS0",
    freq=868,
    addr=0,
    power=22,
    target_addr=1
)

image_dir = "./images_to_send/"
images = [f for f in os.listdir(image_dir) 
          if f.lower().endswith(('.jpg', '.jpeg'))]

for i, image_name in enumerate(images, 1):
    image_path = os.path.join(image_dir, image_name)
    print(f"Sending image {i}/{len(images)}: {image_name}")
    
    sender.send_image(image_path, delay_between_packets=0.1)
    
    # Wait between images
    if i < len(images):
        print("Waiting 5 seconds before next image...")
        time.sleep(5)

print(f"Batch complete! Sent {len(images)} images.")
""")

# ============================================================================
# EXAMPLE 5: Basic Receiver
# ============================================================================
print("\n" + "="*70)
print("EXAMPLE 5: Basic Receiver")
print("="*70)
print("""
# Continuously listen for incoming images

from image_receiver import ImageReceiver

receiver = ImageReceiver(
    serial_num="/dev/ttyS0",
    freq=868,           # Must match sender frequency
    addr=1,             # Must match sender's target_addr
    power=22,
    output_dir="received_images"
)

# Listen forever (until Ctrl+C)
receiver.listen()
""")

# ============================================================================
# EXAMPLE 6: Custom Receiver with Callbacks
# ============================================================================
print("\n" + "="*70)
print("EXAMPLE 6: Receiver with Custom Actions")
print("="*70)
print("""
# Extend the receiver to perform actions after receiving

from image_receiver import ImageReceiver
import os

class MyReceiver(ImageReceiver):
    def handle_end_packet(self, payload):
        # Call parent method to save the image
        super().handle_end_packet(payload)
        
        # Perform custom actions after receiving
        if self.filename:
            print("\\nCustom action: Processing received image...")
            
            # Example: Copy to another location
            # Example: Upload to server
            # Example: Send confirmation
            # Example: Trigger alert
            
            print("Custom processing complete!")

# Use the custom receiver
receiver = MyReceiver(
    serial_num="/dev/ttyS0",
    freq=868,
    addr=1,
    power=22,
    output_dir="received_images"
)

receiver.listen()
""")

# ============================================================================
# EXAMPLE 7: Camera Integration (Sender)
# ============================================================================
print("\n" + "="*70)
print("EXAMPLE 7: Raspberry Pi Camera Integration")
print("="*70)
print("""
# Capture photo with Pi Camera and send immediately

from picamera import PiCamera
from image_sender import ImageSender
from optimize_image import ImageOptimizer
import time

# Initialize camera
camera = PiCamera()
camera.resolution = (640, 480)

# Initialize LoRa sender
sender = ImageSender(
    serial_num="/dev/ttyS0",
    freq=868,
    addr=0,
    power=22,
    target_addr=1
)

# Initialize optimizer
optimizer = ImageOptimizer()

# Capture and send loop
try:
    photo_count = 0
    while True:
        photo_count += 1
        
        # Capture photo
        print(f"Capturing photo {photo_count}...")
        filename = f"capture_{photo_count}.jpg"
        camera.capture(filename)
        
        # Optimize
        print("Optimizing...")
        optimized = optimizer.optimize_image(filename, preset='small')
        
        # Send
        if optimized:
            print("Sending...")
            sender.send_image(optimized)
            
            # Clean up
            os.remove(filename)  # Remove original
            os.remove(optimized)  # Remove optimized after sending
        
        # Wait before next capture
        print("Waiting 60 seconds...")
        time.sleep(60)
        
except KeyboardInterrupt:
    print("\\nStopped by user")
    camera.close()
""")

# ============================================================================
# EXAMPLE 8: Scheduled Transmission
# ============================================================================
print("\n" + "="*70)
print("EXAMPLE 8: Scheduled Image Transmission")
print("="*70)
print("""
# Send images at specific times

from image_sender import ImageSender
from datetime import datetime
import time

sender = ImageSender(
    serial_num="/dev/ttyS0",
    freq=868,
    addr=0,
    power=22,
    target_addr=1
)

# Send times (24-hour format)
send_times = ["08:00", "12:00", "16:00", "20:00"]

print("Scheduled sender started...")
print(f"Will send at: {', '.join(send_times)}")

while True:
    now = datetime.now().strftime("%H:%M")
    
    if now in send_times:
        print(f"\\nTime to send! ({now})")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Assume image is updated by another process
        image_path = "latest_capture.jpg"
        
        if os.path.exists(image_path):
            sender.send_image(image_path)
            print("Transmission complete!")
        else:
            print("No image found to send.")
        
        # Sleep for 61 seconds to avoid re-sending in the same minute
        time.sleep(61)
    else:
        # Check every 10 seconds
        time.sleep(10)
""")

# ============================================================================
# EXAMPLE 9: Configuration for Long Range
# ============================================================================
print("\n" + "="*70)
print("EXAMPLE 9: Long Range Configuration")
print("="*70)
print("""
# Optimize for maximum range (slower but more reliable)

from image_sender import ImageSender

sender = ImageSender(
    serial_num="/dev/ttyS0",
    freq=868,
    addr=0,
    power=22,           # Maximum power
    target_addr=1,
    chunk_size=180      # Smaller chunks for reliability
)

# Override air speed for longer range (requires modifying __init__)
# In image_sender.py, change:
#   air_speed=1200,  # Slowest = longest range

# Send with longer delays between packets
sender.send_image(
    "photo.jpg",
    delay_between_packets=0.3  # Longer delay = more reliable
)
""")

# ============================================================================
# EXAMPLE 10: Fast Transmission Configuration
# ============================================================================
print("\n" + "="*70)
print("EXAMPLE 10: Fast Transmission Configuration")
print("="*70)
print("""
# Optimize for speed (shorter range, higher data rate)

from image_sender import ImageSender

sender = ImageSender(
    serial_num="/dev/ttyS0",
    freq=868,
    addr=0,
    power=22,
    target_addr=1,
    chunk_size=200      # Maximum chunk size
)

# Override air speed for faster transmission (requires modifying __init__)
# In image_sender.py, change:
#   air_speed=9600,  # or even 38400 for maximum speed

# Send with minimal delays
sender.send_image(
    "photo.jpg",
    delay_between_packets=0.05  # Minimum safe delay
)

# Note: Fast transmission may result in packet loss at longer distances
""")

# ============================================================================
# EXAMPLE 11: Error Recovery
# ============================================================================
print("\n" + "="*70)
print("EXAMPLE 11: Error Recovery and Retry")
print("="*70)
print("""
# Implement retry logic for failed transmissions

from image_sender import ImageSender
import time

def send_with_retry(image_path, max_retries=3):
    sender = ImageSender(
        serial_num="/dev/ttyS0",
        freq=868,
        addr=0,
        power=22,
        target_addr=1
    )
    
    for attempt in range(max_retries):
        print(f"Transmission attempt {attempt + 1}/{max_retries}")
        
        try:
            success = sender.send_image(image_path)
            
            if success:
                print("Transmission successful!")
                return True
            
        except Exception as e:
            print(f"Error during transmission: {e}")
        
        if attempt < max_retries - 1:
            wait_time = 5 * (attempt + 1)
            print(f"Waiting {wait_time} seconds before retry...")
            time.sleep(wait_time)
    
    print("All retry attempts failed.")
    return False

# Usage
send_with_retry("important_photo.jpg")
""")

# ============================================================================
# EXAMPLE 12: Logging Transmissions
# ============================================================================
print("\n" + "="*70)
print("EXAMPLE 12: Transmission Logging")
print("="*70)
print("""
# Log all transmissions to a file

from image_sender import ImageSender
from datetime import datetime
import json

def log_transmission(image_path, success, duration, file_size):
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'image': image_path,
        'success': success,
        'duration_seconds': duration,
        'file_size_bytes': file_size,
        'throughput_bps': file_size / duration if duration > 0 else 0
    }
    
    with open('transmission_log.json', 'a') as f:
        f.write(json.dumps(log_entry) + '\\n')

# Wrapper function
def send_and_log(image_path):
    import os
    import time
    
    sender = ImageSender(
        serial_num="/dev/ttyS0",
        freq=868,
        addr=0,
        power=22,
        target_addr=1
    )
    
    file_size = os.path.getsize(image_path)
    start_time = time.time()
    
    try:
        success = sender.send_image(image_path)
        duration = time.time() - start_time
        log_transmission(image_path, True, duration, file_size)
        return True
    except Exception as e:
        duration = time.time() - start_time
        log_transmission(image_path, False, duration, file_size)
        print(f"Error: {e}")
        return False

# Usage
send_and_log("photo.jpg")
""")

# ============================================================================
print("\n" + "="*70)
print("For more examples and detailed documentation, see:")
print("  - README.md (comprehensive documentation)")
print("  - QUICKSTART.md (getting started guide)")
print("  - ARCHITECTURE.md (system architecture)")
print("="*70)
print("""
To run any example:
1. Copy the code to a new Python file
2. Adjust parameters for your setup
3. Run with: python3 your_script.py

Happy transmitting! 📡
""")
