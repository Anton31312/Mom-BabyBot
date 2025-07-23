#!/usr/bin/env python
"""
Script to generate self-signed SSL certificates for development.
"""

import os
import subprocess
from pathlib import Path

def generate_ssl_certs():
    """Generate self-signed SSL certificates for development."""
    print("Generating self-signed SSL certificates for development...")
    
    # Create directory for SSL certificates
    ssl_dir = Path("nginx/ssl")
    ssl_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate private key
    key_path = ssl_dir / "key.pem"
    if not key_path.exists():
        subprocess.run([
            "openssl", "genrsa",
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
            "openssl", "req",
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
            "openssl", "x509",
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