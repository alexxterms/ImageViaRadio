#!/usr/bin/python
# -*- coding: UTF-8 -*-

"""
Image Optimizer for LoRa Transmission
Compresses and resizes images for optimal LoRa transmission
"""

import sys
import os
from PIL import Image

class ImageOptimizer:
    """Optimize images for LoRa transmission"""
    
    PRESETS = {
        'thumbnail': {'size': (160, 120), 'quality': 60, 'target': '~3-5 KB'},
        'small': {'size': (320, 240), 'quality': 70, 'target': '~10-15 KB'},
        'medium': {'size': (640, 480), 'quality': 75, 'target': '~30-50 KB'},
        'large': {'size': (800, 600), 'quality': 80, 'target': '~60-100 KB'},
    }
    
    def __init__(self):
        pass
    
    def get_image_info(self, image_path):
        """Get image information"""
        try:
            img = Image.open(image_path)
            size = img.size
            mode = img.mode
            file_size = os.path.getsize(image_path)
            return {
                'width': size[0],
                'height': size[1],
                'mode': mode,
                'size_bytes': file_size,
                'size_kb': file_size / 1024
            }
        except Exception as e:
            print(f"Error reading image: {e}")
            return None
    
    def optimize_image(self, input_path, output_path=None, preset='small', 
                       custom_size=None, quality=None):
        """
        Optimize an image for LoRa transmission
        
        Args:
            input_path: Input image path
            output_path: Output path (auto-generated if None)
            preset: Preset name ('thumbnail', 'small', 'medium', 'large')
            custom_size: Custom size tuple (width, height) - overrides preset
            quality: JPEG quality 0-100 - overrides preset
        
        Returns:
            Output path if successful, None otherwise
        """
        try:
            # Open image
            img = Image.open(input_path)
            original_info = self.get_image_info(input_path)
            
            # Get preset or custom settings
            if custom_size and quality:
                target_size = custom_size
                target_quality = quality
            elif preset in self.PRESETS:
                config = self.PRESETS[preset]
                target_size = config['size']
                target_quality = config['quality']
            else:
                print(f"Unknown preset: {preset}")
                return None
            
            # Convert to RGB if necessary (for JPEG)
            if img.mode in ('RGBA', 'P', 'LA'):
                # Create white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize maintaining aspect ratio
            img.thumbnail(target_size, Image.Resampling.LANCZOS)
            
            # Generate output path if not provided
            if output_path is None:
                base, ext = os.path.splitext(input_path)
                output_path = f"{base}_optimized.jpg"
            
            # Save optimized image
            img.save(output_path, 'JPEG', quality=target_quality, optimize=True)
            
            # Get optimized info
            optimized_info = self.get_image_info(output_path)
            
            # Print results
            print("\n" + "="*60)
            print("Image Optimization Complete")
            print("="*60)
            print(f"\nOriginal:")
            print(f"  Size: {original_info['width']}x{original_info['height']} pixels")
            print(f"  File: {original_info['size_kb']:.2f} KB ({original_info['size_bytes']} bytes)")
            
            print(f"\nOptimized:")
            print(f"  Size: {optimized_info['width']}x{optimized_info['height']} pixels")
            print(f"  File: {optimized_info['size_kb']:.2f} KB ({optimized_info['size_bytes']} bytes)")
            print(f"  Quality: {target_quality}%")
            
            reduction = (1 - optimized_info['size_bytes'] / original_info['size_bytes']) * 100
            print(f"\nReduction: {reduction:.1f}%")
            
            # Estimate transmission time (rough estimate at 250 bytes/sec)
            est_time = optimized_info['size_bytes'] / 250
            print(f"Est. transmission time: ~{est_time:.0f} seconds")
            
            print(f"\nSaved to: {output_path}")
            print("="*60 + "\n")
            
            return output_path
            
        except Exception as e:
            print(f"Error optimizing image: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def batch_optimize(self, input_dir, output_dir=None, preset='small'):
        """
        Batch optimize all images in a directory
        
        Args:
            input_dir: Input directory path
            output_dir: Output directory (created if doesn't exist)
            preset: Optimization preset
        """
        if output_dir is None:
            output_dir = os.path.join(input_dir, 'optimized')
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Created output directory: {output_dir}\n")
        
        # Supported formats
        supported = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff')
        
        # Find images
        images = [f for f in os.listdir(input_dir) 
                 if f.lower().endswith(supported) and os.path.isfile(os.path.join(input_dir, f))]
        
        if not images:
            print(f"No images found in {input_dir}")
            return
        
        print(f"Found {len(images)} images to optimize\n")
        
        success_count = 0
        for i, image_name in enumerate(images, 1):
            input_path = os.path.join(input_dir, image_name)
            output_name = os.path.splitext(image_name)[0] + '_optimized.jpg'
            output_path = os.path.join(output_dir, output_name)
            
            print(f"[{i}/{len(images)}] Processing: {image_name}")
            
            if self.optimize_image(input_path, output_path, preset):
                success_count += 1
        
        print(f"\nBatch optimization complete: {success_count}/{len(images)} successful")


def print_usage():
    """Print usage information"""
    print("\n" + "="*60)
    print("Image Optimizer for LoRa Transmission")
    print("="*60 + "\n")
    print("Usage:")
    print("  python3 optimize_image.py <image_path> [preset]")
    print("  python3 optimize_image.py --batch <input_dir> [preset]")
    print()
    print("Presets:")
    for name, config in ImageOptimizer.PRESETS.items():
        print(f"  {name:10} - {config['size'][0]}x{config['size'][1]:3} pixels, "
              f"quality {config['quality']:2}% - {config['target']}")
    print()
    print("Examples:")
    print("  # Optimize single image (default: small)")
    print("  python3 optimize_image.py photo.jpg")
    print()
    print("  # Optimize with specific preset")
    print("  python3 optimize_image.py photo.jpg thumbnail")
    print()
    print("  # Batch optimize all images in directory")
    print("  python3 optimize_image.py --batch ./my_photos/ medium")
    print()


def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    optimizer = ImageOptimizer()
    
    # Check for batch mode
    if sys.argv[1] == '--batch':
        if len(sys.argv) < 3:
            print("Error: --batch requires input directory")
            print_usage()
            sys.exit(1)
        
        input_dir = sys.argv[2]
        preset = sys.argv[3] if len(sys.argv) > 3 else 'small'
        
        if not os.path.isdir(input_dir):
            print(f"Error: '{input_dir}' is not a directory")
            sys.exit(1)
        
        optimizer.batch_optimize(input_dir, preset=preset)
    
    # Single image mode
    else:
        input_path = sys.argv[1]
        preset = sys.argv[2] if len(sys.argv) > 2 else 'small'
        
        if not os.path.exists(input_path):
            print(f"Error: Image file '{input_path}' not found")
            sys.exit(1)
        
        # Show image info first
        print("\n" + "="*60)
        print("Original Image Information")
        print("="*60)
        info = optimizer.get_image_info(input_path)
        if info:
            print(f"  Size: {info['width']}x{info['height']} pixels")
            print(f"  Mode: {info['mode']}")
            print(f"  File: {info['size_kb']:.2f} KB ({info['size_bytes']} bytes)")
            
            # Estimate if optimization is needed
            if info['size_kb'] < 20:
                print(f"\n  ℹ Image is already small ({info['size_kb']:.1f} KB)")
                print(f"  Estimated transmission: ~{info['size_bytes']/250:.0f} seconds")
            elif info['size_kb'] > 100:
                print(f"\n  ⚠ Image is large ({info['size_kb']:.1f} KB)")
                print(f"  Recommended: Use 'thumbnail' or 'small' preset")
        print("="*60)
        
        output_path = optimizer.optimize_image(input_path, preset=preset)
        
        if output_path:
            print(f"Ready to send with:")
            print(f"  python3 image_sender.py {output_path}")


if __name__ == "__main__":
    main()
