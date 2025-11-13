#!/usr/bin/python
# -*- coding: UTF-8 -*-

"""
Test script for LoRa Image Transmission System
Creates a small test image and verifies the transmission setup
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont
import random

def create_test_image(filename="test_image.jpg", size=(320, 240)):
    """
    Create a simple test JPEG image
    
    Args:
        filename: Output filename
        size: Image size tuple (width, height)
    """
    print(f"Creating test image: {filename}")
    
    # Create image with random background color
    img = Image.new('RGB', size, color=(
        random.randint(50, 200),
        random.randint(50, 200),
        random.randint(50, 200)
    ))
    
    draw = ImageDraw.Draw(img)
    
    # Draw some shapes
    # Rectangle
    draw.rectangle([10, 10, 100, 100], fill='red', outline='yellow', width=3)
    
    # Ellipse
    draw.ellipse([120, 10, 220, 110], fill='blue', outline='cyan', width=3)
    
    # Line
    draw.line([10, 120, 220, 120], fill='white', width=5)
    
    # Polygon (triangle)
    draw.polygon([
        (240, 50), (300, 120), (180, 120)
    ], fill='green', outline='yellow')
    
    # Add text
    try:
        # Try to use default font
        draw.text((20, 150), "LoRa Test Image", fill='white')
        draw.text((20, 170), f"Size: {size[0]}x{size[1]}", fill='white')
        draw.text((20, 190), "Generated for testing", fill='yellow')
    except:
        print("Note: Default font used (PIL font unavailable)")
    
    # Save as JPEG
    img.save(filename, 'JPEG', quality=85)
    file_size = os.path.getsize(filename)
    
    print(f"✓ Test image created successfully!")
    print(f"  Size: {size[0]}x{size[1]} pixels")
    print(f"  File size: {file_size} bytes ({file_size/1024:.2f} KB)")
    
    return filename, file_size


def create_sample_images():
    """Create multiple test images of different sizes"""
    print("\n" + "="*60)
    print("Creating Sample Test Images")
    print("="*60 + "\n")
    
    samples = [
        ("small_test.jpg", (160, 120)),   # ~5-10 KB
        ("medium_test.jpg", (320, 240)),  # ~15-25 KB
        ("large_test.jpg", (640, 480)),   # ~50-80 KB
    ]
    
    created_files = []
    
    for filename, size in samples:
        try:
            filepath, filesize = create_test_image(filename, size)
            created_files.append((filepath, filesize))
            print()
        except Exception as e:
            print(f"✗ Failed to create {filename}: {e}\n")
    
    print("="*60)
    print(f"Created {len(created_files)} test images")
    print("="*60 + "\n")
    
    # Print usage instructions
    print("Usage Instructions:")
    print("-" * 60)
    print("\n1. Start the receiver on the receiving Raspberry Pi:")
    print("   python3 image_receiver.py\n")
    
    print("2. Send a test image from the sending Raspberry Pi:")
    for filepath, filesize in created_files:
        est_time = (filesize / 250) * 1.2  # Rough estimate
        print(f"   python3 image_sender.py {filepath}")
        print(f"   (Estimated time: ~{est_time:.0f} seconds)\n")
    
    print("-" * 60)
    
    return created_files


def verify_requirements():
    """Verify that required libraries are available"""
    print("\n" + "="*60)
    print("Verifying Requirements")
    print("="*60 + "\n")
    
    requirements = {
        'PIL': 'Pillow (for test image generation)',
        'RPi.GPIO': 'RPi.GPIO (for LoRa control)',
        'serial': 'pyserial (for UART communication)'
    }
    
    missing = []
    
    for module, description in requirements.items():
        try:
            __import__(module)
            print(f"✓ {module:15} - {description}")
        except ImportError:
            print(f"✗ {module:15} - {description} - NOT FOUND")
            missing.append(module)
    
    print()
    
    if missing:
        print("Missing modules. Install with:")
        if 'PIL' in missing:
            print("  sudo pip3 install Pillow")
        if 'RPi.GPIO' in missing:
            print("  sudo pip3 install RPi.GPIO")
        if 'serial' in missing:
            print("  sudo pip3 install pyserial")
        print()
        return False
    else:
        print("✓ All requirements satisfied!")
        print()
        return True


def check_serial_port():
    """Check if serial port is accessible"""
    print("\n" + "="*60)
    print("Checking Serial Port")
    print("="*60 + "\n")
    
    serial_port = "/dev/ttyS0"
    
    if os.path.exists(serial_port):
        print(f"✓ Serial port {serial_port} exists")
        
        # Check if accessible
        try:
            import serial
            ser = serial.Serial(serial_port, 9600, timeout=1)
            ser.close()
            print(f"✓ Serial port {serial_port} is accessible")
            return True
        except PermissionError:
            print(f"✗ Permission denied on {serial_port}")
            print(f"\nFix with:")
            print(f"  sudo usermod -a -G dialout $USER")
            print(f"  (then logout and login again)")
            return False
        except Exception as e:
            print(f"✗ Error accessing {serial_port}: {e}")
            return False
    else:
        print(f"✗ Serial port {serial_port} not found")
        print(f"\nMake sure:")
        print(f"  1. Serial interface is enabled in raspi-config")
        print(f"  2. Serial login shell is disabled")
        print(f"  3. Raspberry Pi has been rebooted after config changes")
        return False


def main():
    print("\n" + "="*60)
    print("LoRa Image Transmission - Test Script")
    print("="*60)
    
    # Check requirements
    if not verify_requirements():
        print("\n⚠ Please install missing requirements first")
        return
    
    # Check serial port (only if RPi.GPIO is available)
    try:
        import RPi.GPIO
        check_serial_port()
    except ImportError:
        print("\n⚠ Skipping serial port check (not on Raspberry Pi)")
    
    # Create test images
    print()
    response = input("Create test images? (y/n): ").strip().lower()
    
    if response == 'y':
        try:
            create_sample_images()
        except Exception as e:
            print(f"\nError creating test images: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("\nSkipped test image creation")
    
    print("\n" + "="*60)
    print("Test Complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
