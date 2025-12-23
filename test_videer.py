#!/usr/bin/env python3
"""
Test script for Videer application
"""
import sys
import os

# Test imports
print("Testing imports...")
try:
    from pexels_client import PexelsClient
    print("✓ pexels_client imported successfully")
except Exception as e:
    print(f"✗ Failed to import pexels_client: {e}")
    sys.exit(1)

# Test PexelsClient initialization
print("\nTesting PexelsClient initialization...")
try:
    client = PexelsClient("test_api_key")
    print("✓ PexelsClient initialized successfully")
    print(f"  - Base URL: {client.BASE_URL}")
    print(f"  - Headers configured: {bool(client.headers)}")
except Exception as e:
    print(f"✗ Failed to initialize PexelsClient: {e}")
    sys.exit(1)

# Test static methods
print("\nTesting PexelsClient static methods...")
try:
    test_video_data = {
        "video_files": [
            {"quality": "hd", "link": "https://example.com/video_hd.mp4"},
            {"quality": "sd", "link": "https://example.com/video_sd.mp4"}
        ]
    }
    
    hd_url = PexelsClient.get_video_file(test_video_data, quality="hd")
    sd_url = PexelsClient.get_video_file(test_video_data, quality="sd")
    
    assert hd_url == "https://example.com/video_hd.mp4", "HD URL mismatch"
    assert sd_url == "https://example.com/video_sd.mp4", "SD URL mismatch"
    
    print("✓ Static methods work correctly")
except Exception as e:
    print(f"✗ Static method test failed: {e}")
    sys.exit(1)

# Test GUI imports (without creating window in headless environment)
print("\nTesting GUI imports...")
try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext
    print("✓ tkinter modules imported successfully")
except Exception as e:
    print(f"✗ Failed to import tkinter: {e}")
    print("  Note: GUI may not be available in headless environments")

print("\n" + "="*50)
print("All tests passed successfully! ✓")
print("="*50)
print("\nTo run the application:")
print("  1. Get your free API key from https://www.pexels.com/api/")
print("  2. Run: python3 videer_gui.py")
print("  3. Enter your API key and start searching for videos!")
