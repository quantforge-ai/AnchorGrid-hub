"""
QuantGrid Version Manager

Automatically checks for and loads new model versions from Hub.
Users get updates without changing their code.
"""

import os
import requests
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional
from loguru import logger


class ModelVersionManager:
    """
    Manages automatic model version updates from QuantGrid Hub.
    
    Versioning Scheme:
    - CalVer: YYYY.WW (Year.Week)
    - Example: 2024.15 = Week 15 of 2024
    - New versions released weekly after merges
    """
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Args:
            cache_dir: Where to cache models (default: ~/.quantgrid/models)
        """
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path.home() / ".quantgrid" / "models"
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.hub_url = os.getenv("QUANTGRID_HUB_URL", "https://hub.quantgrid.dev")
    
    def get_current_version(self) -> str:
        """
        Get current CalVer version (YYYY.WW)
        
        Returns:
            Current week version string
        """
        now = datetime.now()
        year = now.year
        week = now.isocalendar()[1]  # ISO week number
        return f"{year}.{week:02d}"
    
    def get_installed_version(self, model_name: str = "quantgrid-analyst") -> Optional[str]:
        """
        Check what version is currently installed.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Version string or None if not installed
        """
        model_dir = self.cache_dir / model_name
        version_file = model_dir / "version.txt"
        
        if version_file.exists():
            with open(version_file) as f:
                return f.read().strip()
        return None
    
    def check_for_updates(self, model_name: str = "quantgrid-analyst") -> dict:
        """
        Check if a new version is available.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Dict with update info: {available: bool, current: str, latest: str}
        """
        installed = self.get_installed_version(model_name)
        
        try:
            # Query Hub for latest version
            response = requests.get(f"{self.hub_url}/latest_version/{model_name}", timeout=5)
            
            if response.status_code == 200:
                latest = response.json()["version"]
                
                return {
                    "available": installed != latest,
                    "current": installed or "None",
                    "latest": latest
                }
        except Exception as e:
            logger.warning(f"Could not check for updates: {e}")
        
        # Fallback
        return {
            "available": False,
            "current": installed or "None",
            "latest": self.get_current_version()
        }
    
    def auto_update(self, model_name: str = "quantgrid-analyst", force: bool = False) -> str:
        """
        Automatically download and install the latest model version.
        
        Args:
            model_name: Name of the model
            force: Force re-download even if up to date
            
        Returns:
            Path to installed model
        """
        update_info = self.check_for_updates(model_name)
        
        if not update_info["available"] and not force:
            logger.info(f"✅ Already on latest version: {update_info['current']}")
            return str(self.cache_dir / model_name)
        
        logger.info(f"📥 Downloading {model_name} v{update_info['latest']}...")
        
        try:
            # Download from Hub
            response = requests.get(
                f"{self.hub_url}/download/{model_name}",
                stream=True,
                timeout=300
            )
            
            if response.status_code == 200:
                # Save to temp location
                temp_file = self.cache_dir / f"{model_name}_latest.zip"
                
                with open(temp_file, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # Extract
                model_dir = self.cache_dir / model_name
                if model_dir.exists():
                    shutil.rmtree(model_dir)  # Remove old version
                
                shutil.unpack_archive(temp_file, model_dir)
                temp_file.unlink()  # Cleanup
                
                # Write version file
                with open(model_dir / "version.txt", "w") as f:
                    f.write(update_info["latest"])
                
                logger.info(f"✅ Updated to v{update_info['latest']}")
                return str(model_dir)
            else:
                logger.error(f"Download failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Update failed: {e}")
        
        # Return existing version if update failed
        return str(self.cache_dir / model_name)
    
    def get_model_path(
        self,
        model_name: str = "quantgrid-analyst",
        auto_update_enabled: bool = True
    ) -> str:
        """
        Get the path to the model, with optional auto-update.
        
        This is the main API - users call this to get model paths.
        
        Args:
            model_name: Name of the model
            auto_update_enabled: Whether to check for updates
            
        Returns:
            Path to model directory
        """
        if auto_update_enabled:
            return self.auto_update(model_name, force=False)
        else:
            model_dir = self.cache_dir / model_name
            if model_dir.exists():
                return str(model_dir)
            else:
                # First time installation
                return self.auto_update(model_name, force=True)


# Singleton instance
_version_manager = None

def get_version_manager() -> ModelVersionManager:
    """Get the global version manager instance"""
    global _version_manager
    if _version_manager is None:
        _version_manager = ModelVersionManager()
    return _version_manager
