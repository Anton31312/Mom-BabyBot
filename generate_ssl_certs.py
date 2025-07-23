#!/usr/bin/env python
"""
Script to generate self-signed SSL certificates for development.
"""

import os
import subprocess
import sys
import shutil
from pathlib import Path


def find_openssl_executable():
    """Find the OpenSSL executable on the system."""
    # Check if OpenSSL path is provided as an argument
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        return sys.argv[1]
        
    # Check if OpenSSL is in PATH
    openssl_path = shutil.which("openssl")
    if openssl_path:
        return openssl_path

    # Common Windows OpenSSL installation locations
    windows_paths = [
        r"C:\Program Files\OpenSSL-Win64\bin\openssl.exe",
        r"C:\Program Files\OpenSSL\bin\openssl.exe",
        r"C:\Program Files (x86)\OpenSSL-Win32\bin\openssl.exe",
        r"C:\OpenSSL-Win64\bin\openssl.exe",
        r"C:\OpenSSL-Win32\bin\openssl.exe",
    ]

    for path in windows_paths:
        if os.path.exists(path):
            return path

    return None


def generate_ssl_certs():
    """Generate self-signed SSL certificates for development."""
    print("Generating self-signed SSL certificates for development...")

    # Find OpenSSL executable
    openssl_path = find_openssl_executable()
    if not openssl_path:
        print("Error: OpenSSL executable not found.")
        print("\nTo generate SSL certificates, you need to install OpenSSL:")
        print("1. Download OpenSSL for Windows from https://slproweb.com/products/Win32OpenSSL.html")
        print("2. Install it and make sure it's added to your PATH")
        print("3. Run this script again")
        sys.exit(1)

    print(f"Using OpenSSL from: {openssl_path}")

    # Create directory for SSL certificates
    ssl_dir = Path("nginx/ssl")
    ssl_dir.mkdir(parents=True, exist_ok=True)

    # Generate private key
    key_path = ssl_dir / "key.pem"
    if not key_path.exists():
        subprocess.run([
            openssl_path, "genrsa",
            "-out", str(key_path),
            "2048"
        ], check=True)
        print(f"Generated private key: {key_path}")
    else:
        print(f"Private key already exists: {key_path}")

    # Generate certificate signing request
    csr_path = ssl_dir / "csr.pem"
    if not csr_path.exists():
        subprocess.run([
            openssl_path, "req",
            "-new",
            "-key", str(key_path),
            "-out", str(csr_path),
            "-subj", "/C=US/ST=State/L=City/O=Organization/CN=localhost"
        ], check=True)
        print(f"Generated certificate signing request: {csr_path}")
    else:
        print(f"Certificate signing request already exists: {csr_path}")

    # Generate self-signed certificate
    cert_path = ssl_dir / "cert.pem"
    if not cert_path.exists():
        subprocess.run([
            openssl_path, "x509",
            "-req",
            "-days", "365",
            "-in", str(csr_path),
            "-signkey", str(key_path),
            "-out", str(cert_path)
        ], check=True)
        print(f"Generated self-signed certificate: {cert_path}")
    else:
        print(f"Self-signed certificate already exists: {cert_path}")

    print("SSL certificate generation complete!")


if __name__ == "__main__":
    generate_ssl_certs()
