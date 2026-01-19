"""
QuantGrid Hub - Submission Packaging

Packages adapters and signs them for Registry submission.
"""

import os
import shutil
import hashlib
import json
import time
from pathlib import Path
from loguru import logger


def hash_file(filepath: str) -> str:
    """Generate SHA256 hash of a file for integrity verification."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def prepare_submission(
    adapter_dir: str,
    author_name: str,
    dataset_desc: str,
    output_dir: str = "."
) -> dict:
    """
    Package the LoRA adapter for QuantGrid Hub.
    
    Args:
        adapter_dir: Path to adapter directory
        author_name: Contributor name/handle
        dataset_desc: Description of training dataset
        output_dir: Where to save the package
        
    Returns:
        Dict with submission details
    """
    logger.info("📦 Packaging Intelligence for Submission...")
    
    # 1. Verify structure
    adapter_path = Path(adapter_dir)
    if not adapter_path.exists():
        logger.error(f"❌ Adapter directory not found: {adapter_dir}")
        return None
    
    required_files = ["adapter_model.bin", "adapter_config.json"]
    for file in required_files:
        if not (adapter_path / file).exists():
            logger.error(f"❌ Missing required file: {file}")
            return None
    
    # 2. Verify QuantGrid compatibility
    metadata_path = adapter_path / "quantgrid_metadata.json"
    if metadata_path.exists():
        with open(metadata_path) as f:
            meta = json.load(f)
            if not meta.get("quantgrid_compatible"):
                logger.warning("⚠️  Adapter may not be compatible with QuantGrid Hub")
    
    # 3. Create metadata
    metadata = {
        "author": author_name,
        "timestamp": int(time.time()),
        "dataset_description": dataset_desc,
        "base_model": "Mistral-7B-v0.1",
        "lora_config": {"r": 16, "alpha": 32},  # Proof of Compatibility
        "version": "1.0",
        "quantgrid_version": "0.2.0",
    }
    
    # 4. Create archive
    timestamp = int(time.time())
    output_filename = f"quantgrid_submission_{timestamp}"
    output_path = Path(output_dir) / output_filename
    
    logger.info(f"🗜️  Creating archive: {output_filename}.zip")
    shutil.make_archive(str(output_path), 'zip', adapter_dir)
    
    zip_path = f"{output_path}.zip"
    
    # 5. Generate checksum
    logger.info("🔒 Generating integrity hash...")
    zip_hash = hash_file(zip_path)
    
    # 6. Create submission manifest
    submission_manifest = {
        "file": f"{output_filename}.zip",
        "hash": zip_hash,
        "size_mb": os.path.getsize(zip_path) / 1024 / 1024,
        "metadata": metadata,
    }
    
    manifest_path = Path(output_dir) / "submission_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(submission_manifest, f, indent=2)
    
    logger.info(f"\n✅ READY FOR UPLOAD!")
    logger.info(f"📁 File: {zip_path}")
    logger.info(f"📋 Manifest: {manifest_path}")
    logger.info(f"💾 Size: {submission_manifest['size_mb']:.2f} MB")
    logger.info(f"🔑 Hash: {zip_hash[:16]}...")
    logger.info(f"\n🚀 Next: Run 'quantgrid push {zip_path}'")
    
    return submission_manifest


if __name__ == "__main__":
    # Interactive CLI
    print("=== QuantGrid Intelligence Submitter ===")
    path = input("Path to adapter folder: ")
    name = input("Your Name/Handle: ")
    desc = input("Dataset Description (e.g. 'SEC 10-K Filings 2023'): ")
    
    prepare_submission(path, name, desc)
