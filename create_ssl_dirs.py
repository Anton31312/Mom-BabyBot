#!/usr/bin/env python
"""
Script to create SSL certificate directories for development.
This is a simplified version that just creates the directory structure
without generating actual certificates.
"""

import os
from pathlib import Path


def create_ssl_dirs():
    """Create SSL certificate directories."""
    print("Creating SSL certificate directories...")

    # Create directory for SSL certificates
    ssl_dir = Path("nginx/ssl")
    ssl_dir.mkdir(parents=True, exist_ok=True)

    # Create empty certificate files
    key_path = ssl_dir / "key.pem"
    cert_path = ssl_dir / "cert.pem"

    if not key_path.exists():
        with open(key_path, 'w') as f:
            f.write("# This is a placeholder for the SSL private key\n")
        print(f"Created placeholder private key: {key_path}")
    else:
        print(f"Private key already exists: {key_path}")

    if not cert_path.exists():
        with open(cert_path, 'w') as f:
            f.write("# This is a placeholder for the SSL certificate\n")
        print(f"Created placeholder certificate: {cert_path}")
    else:
        print(f"Certificate already exists: {cert_path}")

    print("SSL certificate directory creation complete!")
    print("\nNOTE: These are just placeholder files. For proper SSL certificates:")
    print("1. Download and install OpenSSL from https://slproweb.com/products/Win32OpenSSL.html")
    print("2. Run the original generate_ssl_certs.py script")
    print("   OR replace these files with your own SSL certificates")


if __name__ == "__main__":
    create_ssl_dirs()
