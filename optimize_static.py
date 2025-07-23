#!/usr/bin/env python
"""
Script to optimize static files for production.

This script:
1. Minifies CSS and JavaScript files
2. Optimizes images
3. Generates gzip and brotli compressed versions of static files
"""

import os
import sys
import gzip
import brotli
import shutil
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# Check if required tools are installed
try:
    import csscompressor
    import jsmin
    from PIL import Image
except ImportError:
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "csscompressor", "jsmin", "pillow", "brotli"])
    import csscompressor
    import jsmin
    from PIL import Image

# Set paths
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / 'static'
OUTPUT_DIR = BASE_DIR / 'staticfiles'

# Create output directory if it doesn't exist
OUTPUT_DIR.mkdir(exist_ok=True)

# File extensions to process
CSS_EXTENSIONS = ['.css']
JS_EXTENSIONS = ['.js']
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif']
COMPRESS_EXTENSIONS = ['.css', '.js', '.html', '.txt', '.xml', '.json', '.svg']

# Counter for statistics
stats = {
    'css_files': 0,
    'js_files': 0,
    'image_files': 0,
    'compressed_files': 0,
    'total_original_size': 0,
    'total_optimized_size': 0
}

def get_file_size(path):
    """Get file size in bytes."""
    return os.path.getsize(path)

def optimize_css(source_path, dest_path):
    """Minify CSS file."""
    try:
        with open(source_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        minified = csscompressor.compress(content)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        
        with open(dest_path, 'w', encoding='utf-8') as f:
            f.write(minified)
        
        original_size = get_file_size(source_path)
        optimized_size = get_file_size(dest_path)
        
        stats['css_files'] += 1
        stats['total_original_size'] += original_size
        stats['total_optimized_size'] += optimized_size
        
        print(f"Optimized CSS: {source_path.relative_to(BASE_DIR)} "
              f"({original_size / 1024:.1f}KB -> {optimized_size / 1024:.1f}KB, "
              f"{(1 - optimized_size / original_size) * 100:.1f}% reduction)")
        
        return dest_path
    except Exception as e:
        print(f"Error optimizing CSS {source_path}: {e}")
        # Copy original file if optimization fails
        shutil.copy2(source_path, dest_path)
        return dest_path

def optimize_js(source_path, dest_path):
    """Minify JavaScript file."""
    try:
        with open(source_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        minified = jsmin.jsmin(content)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        
        with open(dest_path, 'w', encoding='utf-8') as f:
            f.write(minified)
        
        original_size = get_file_size(source_path)
        optimized_size = get_file_size(dest_path)
        
        stats['js_files'] += 1
        stats['total_original_size'] += original_size
        stats['total_optimized_size'] += optimized_size
        
        print(f"Optimized JS: {source_path.relative_to(BASE_DIR)} "
              f"({original_size / 1024:.1f}KB -> {optimized_size / 1024:.1f}KB, "
              f"{(1 - optimized_size / original_size) * 100:.1f}% reduction)")
        
        return dest_path
    except Exception as e:
        print(f"Error optimizing JS {source_path}: {e}")
        # Copy original file if optimization fails
        shutil.copy2(source_path, dest_path)
        return dest_path

def optimize_image(source_path, dest_path):
    """Optimize image file."""
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        
        # Open image
        img = Image.open(source_path)
        
        # Save optimized image
        if source_path.suffix.lower() in ['.jpg', '.jpeg']:
            img.save(dest_path, 'JPEG', optimize=True, quality=85)
        elif source_path.suffix.lower() == '.png':
            img.save(dest_path, 'PNG', optimize=True)
        elif source_path.suffix.lower() == '.gif':
            img.save(dest_path, 'GIF', optimize=True)
        else:
            # For unsupported formats, just copy the file
            shutil.copy2(source_path, dest_path)
        
        original_size = get_file_size(source_path)
        optimized_size = get_file_size(dest_path)
        
        stats['image_files'] += 1
        stats['total_original_size'] += original_size
        stats['total_optimized_size'] += optimized_size
        
        print(f"Optimized image: {source_path.relative_to(BASE_DIR)} "
              f"({original_size / 1024:.1f}KB -> {optimized_size / 1024:.1f}KB, "
              f"{(1 - optimized_size / original_size) * 100:.1f}% reduction)")
        
        return dest_path
    except Exception as e:
        print(f"Error optimizing image {source_path}: {e}")
        # Copy original file if optimization fails
        shutil.copy2(source_path, dest_path)
        return dest_path

def compress_file(path):
    """Create gzip and brotli compressed versions of a file."""
    try:
        # Gzip compression
        with open(path, 'rb') as f_in:
            with gzip.open(f"{path}.gz", 'wb', compresslevel=9) as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Brotli compression
        with open(path, 'rb') as f_in:
            content = f_in.read()
            compressed = brotli.compress(content, quality=11)
            with open(f"{path}.br", 'wb') as f_out:
                f_out.write(compressed)
        
        stats['compressed_files'] += 1
        
        original_size = get_file_size(path)
        gzip_size = get_file_size(f"{path}.gz")
        brotli_size = get_file_size(f"{path}.br")
        
        print(f"Compressed: {Path(path).relative_to(OUTPUT_DIR)} "
              f"(Original: {original_size / 1024:.1f}KB, "
              f"Gzip: {gzip_size / 1024:.1f}KB, "
              f"Brotli: {brotli_size / 1024:.1f}KB)")
    except Exception as e:
        print(f"Error compressing {path}: {e}")

def process_file(source_path, dest_path):
    """Process a single file based on its extension."""
    source_path = Path(source_path)
    dest_path = Path(dest_path)
    
    # Skip if source doesn't exist
    if not source_path.exists():
        return
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    
    # Process based on file extension
    if source_path.suffix.lower() in CSS_EXTENSIONS:
        optimize_css(source_path, dest_path)
    elif source_path.suffix.lower() in JS_EXTENSIONS:
        optimize_js(source_path, dest_path)
    elif source_path.suffix.lower() in IMAGE_EXTENSIONS:
        optimize_image(source_path, dest_path)
    else:
        # Copy other files without processing
        shutil.copy2(source_path, dest_path)
    
    # Compress file if it has a compressible extension
    if dest_path.suffix.lower() in COMPRESS_EXTENSIONS:
        compress_file(dest_path)

def process_directory(source_dir, dest_dir):
    """Process all files in a directory recursively."""
    tasks = []
    
    for root, dirs, files in os.walk(source_dir):
        # Calculate relative path
        rel_path = os.path.relpath(root, source_dir)
        
        # Create corresponding output directory
        output_dir = os.path.join(dest_dir, rel_path)
        os.makedirs(output_dir, exist_ok=True)
        
        # Process each file
        for file in files:
            source_file = os.path.join(root, file)
            dest_file = os.path.join(output_dir, file)
            tasks.append((source_file, dest_file))
    
    # Process files in parallel
    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        for source_file, dest_file in tasks:
            executor.submit(process_file, source_file, dest_file)

def main():
    """Main function to optimize static files."""
    print("Starting static files optimization...")
    
    # Process static directory
    process_directory(STATIC_DIR, OUTPUT_DIR)
    
    # Print statistics
    print("\nOptimization complete!")
    print(f"Processed {stats['css_files']} CSS files, {stats['js_files']} JS files, {stats['image_files']} images")
    print(f"Compressed {stats['compressed_files']} files")
    print(f"Total size reduction: {stats['total_original_size'] / 1024:.1f}KB -> {stats['total_optimized_size'] / 1024:.1f}KB "
          f"({(1 - stats['total_optimized_size'] / stats['total_original_size']) * 100:.1f}% reduction)")

if __name__ == "__main__":
    main()