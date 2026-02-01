"""
AnchorGrid Hub - Weekly Merge Script

Aggregates approved adapters into the main model via linear averaging.
Runs weekly as a cron job.
"""

import os
from pathlib import Path
from datetime import datetime
from loguru import logger

from anchorgrid.hub.merging import ModelSoup
from anchorgrid.hub.registry import AnchorGridHub
from anchorgrid.core.versioning import ModelVersionManager


def weekly_merge():
    """
    The 'Hive Mind Synchronization Event'
    
    1. Loads all adapters from approved queue
    2. Merges them using linear averaging
    3. Publishes new CalVer release
    4. Clears approved queue
    """
    logger.info("🐝 === WEEKLY HIVE MIND MERGE ===" )
    logger.info(f"📅 Date: {datetime.now().isoformat()}")
    
    # Paths
    approved_dir = Path("./approved_adapters")
    output_dir = Path("./merged_models")
    output_dir.mkdir(exist_ok=True)
    
    # 1. Find all approved adapters
    adapters = list(approved_dir.glob("*/adapter_model.bin"))
    adapter_dirs = [a.parent for a in adapters]
    
    if not adapter_dirs:
        logger.warning("⚠️  No adapters to merge this week")
        return
    
    logger.info(f"🔍 Found {len(adapter_dirs)} adapters:")
    for adapter in adapter_dirs:
        logger.info(f"  - {adapter.name}")
    
    # 2. Merge using ModelSoup
    logger.info("🍲 Creating Model Soup...")
    
    merger = ModelSoup(base_model_id="mistralai/Mistral-7B-v0.1")
    merged_model = merger.merge_adapters(
        [str(d) for d in adapter_dirs],
        method="linear"
    )
    
    # 3. Generate version
    version_manager = ModelVersionManager()
    version = version_manager.get_current_version()
    
    # 4. Save merged model
    output_path = output_dir / f"anchorgrid-analyst-{version}"
    output_path.mkdir(exist_ok=True)
    
    logger.info(f"💾 Saving merged model: {output_path}")
    merged_model.save_pretrained(str(output_path))
    
    # Write version metadata
    with open(output_path / "version.txt", "w") as f:
        f.write(version)
    
    with open(output_path / "contributors.txt", "w") as f:
        for adapter in adapter_dirs:
            f.write(f"{adapter.name}\n")
    
    logger.info(f"✅ Merge Complete! Version: {version}")
    logger.info(f"👥 {len(adapter_dirs)} contributors this week")
    
    # 5. Upload to Hub (TODO: Implement upload to CDN/S3)
    logger.info("☁️  Uploading to Hub...")
    # hub = AnchorGridHub()
    # hub.upload_release(output_path, version)
    
    # 6. Clear approved queue
    logger.info("🧹 Clearing approved queue...")
    for adapter_dir in adapter_dirs:
        # Move to archive
        archive_dir = Path("./archived_adapters") / version
        archive_dir.mkdir(parents=True, exist_ok=True)
        adapter_dir.rename(archive_dir / adapter_dir.name)
    
    logger.info(f"🎉 Weekly merge complete! {version} is live.\n")


if __name__ == "__main__":
    # Run weekly merge
    weekly_merge()
    
    # To run as cron job (every Sunday at 3 AM):
    # 0 3 * * 0 cd /opt/anchorgrid-hub && python -m anchorgrid.hub.weekly_merge
