#!/usr/bin/env python3
"""Convert PNG files into a single ICO file. No dependencies beyond stdlib.
Usage: python3 scripts/png-to-ico.py input16.png input32.png output.ico
"""
import sys
import struct

def create_ico(png_paths, output_path):
    images = []
    for path in png_paths:
        with open(path, 'rb') as f:
            data = f.read()
        w = struct.unpack('>I', data[16:20])[0]
        h = struct.unpack('>I', data[20:24])[0]
        images.append((w, h, data))

    header = struct.pack('<HHH', 0, 1, len(images))
    offset = 6 + 16 * len(images)

    directory = b''
    for w, h, data in images:
        directory += struct.pack('<BBBBHHII',
            w if w < 256 else 0,
            h if h < 256 else 0,
            0, 0, 1, 32,
            len(data), offset)
        offset += len(data)

    with open(output_path, 'wb') as f:
        f.write(header + directory)
        for _, _, data in images:
            f.write(data)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python3 scripts/png-to-ico.py input16.png input32.png output.ico", file=sys.stderr)
        sys.exit(1)
    *inputs, output = sys.argv[1:]
    # Validate PNG signature before processing
    for path in inputs:
        with open(path, 'rb') as f:
            sig = f.read(8)
        if sig != b'\x89PNG\r\n\x1a\n':
            print(f"Error: {path} is not a valid PNG file", file=sys.stderr)
            sys.exit(1)
    create_ico(inputs, output)
    print(f'Created {output}')
