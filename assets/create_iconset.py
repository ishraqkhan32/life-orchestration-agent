#!/usr/bin/env python3
"""
Script to generate a proper icon.iconset folder for macOS iconutil from a 1024x1024 PNG.
"""
import os
from PIL import Image

def create_iconset(source_png="icon.png", iconset_dir="icon.iconset"):
    sizes = [
        (16, False), (16, True),
        (32, False), (32, True),
        (128, False), (128, True),
        (256, False), (256, True),
        (512, False), (512, True),
    ]
    size_map = {
        (16, False): "icon_16x16.png",
        (16, True):  "icon_16x16@2x.png",
        (32, False): "icon_32x32.png",
        (32, True):  "icon_32x32@2x.png",
        (128, False): "icon_128x128.png",
        (128, True):  "icon_128x128@2x.png",
        (256, False): "icon_256x256.png",
        (256, True):  "icon_256x256@2x.png",
        (512, False): "icon_512x512.png",
        (512, True):  "icon_512x512@2x.png",
    }
    scale = {False: 1, True: 2}

    if not os.path.exists(source_png):
        raise FileNotFoundError(f"Source PNG not found: {source_png}")
    if not os.path.exists(iconset_dir):
        os.makedirs(iconset_dir)

    img = Image.open(source_png).convert("RGBA")
    for base, is2x in sizes:
        size = base * scale[is2x]
        resized = img.resize((size, size), Image.Resampling.LANCZOS)
        out_path = os.path.join(iconset_dir, size_map[(base, is2x)])
        resized.save(out_path)
        print(f"Saved {out_path}")

if __name__ == "__main__":
    create_iconset() 