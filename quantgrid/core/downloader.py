"""
QuantGrid Core - Model Downloader

Universal downloader for models from HuggingFace.
Works for ANY domain (finance, legal, code, medical, etc.)
"""

import os
from pathlib import Path
from typing import Optional
from huggingface_hub import snapshot_download, hf_hub_url
from rich.console import Console
from rich.progress import Progress

console = Console()


class ModelDownloader:
    """
    Universal model downloader.
    
    Downloads models from HuggingFace based on registry ID.
    Format: domain/model-name (e.g., "finance/sec-expert" or "code/django-helper")
    """
    
    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = cache_dir or str(Path.home() / ".cache" / "quantgrid")
        
    def pull(self, registry_id: str, force: bool = False) -> str:
        """
        Download a model from the registry.
        
        Args:
            registry_id: Format "domain/model-name"
            force: Re-download even if exists locally
            
        Returns:
            Local path to downloaded model
        """
        
        # Parse registry ID
        if "/" not in registry_id:
            raise ValueError(f"Invalid registry ID: {registry_id}. Format: 'domain/model-name'")
        
        domain, model_name = registry_id.split("/", 1)
        
        console.print(f"🌍 Locating [cyan]{model_name}[/cyan] in [magenta]{domain}[/magenta] sector...")
        
        # Build local path
        local_path = os.path.join(self.cache_dir, domain, model_name)
        
        # Check if already exists
        if os.path.exists(local_path) and not force:
            console.print(f"✅ Already installed at [dim]{local_path}[/dim]")
            console.print("💡 Use --force to re-download")
            return local_path
        
        # Download from HuggingFace
        # Convention: HF repo = "QuantGrid-Community/{model-name}"
        hf_repo_id = f"QuantGrid-Community/{model_name}"
        
        console.print(f"📥 Downloading from [dim]huggingface.co/{hf_repo_id}[/dim]...")
        
        try:
            with Progress() as progress:
                task = progress.add_task("[cyan]Downloading...", total=None)
                
                # Download model
                downloaded_path = snapshot_download(
                    repo_id=hf_repo_id,
                    local_dir=local_path,
                    local_dir_use_symlinks=False
                )
                
                progress.update(task, completed=True)
            
            console.print(f"✅ Installed to [green]{local_path}[/green]")
            return local_path
            
        except Exception as e:
            console.print(f"[red]❌ Download failed: {e}[/red]")
            console.print(f"💡 Make sure the model exists on HuggingFace")
            raise
    
    def list_local(self, domain: Optional[str] = None) -> list:
        """
        List locally installed models.
        
        Args:
            domain: Filter by domain (optional)
            
        Returns:
            List of (domain, model_name) tuples
        """
        models = []
        
        if not os.path.exists(self.cache_dir):
            return models
        
        # Scan cache directory
        for domain_dir in os.listdir(self.cache_dir):
            domain_path = os.path.join(self.cache_dir, domain_dir)
            
            if not os.path.isdir(domain_path):
                continue
            
            # Filter by domain if specified
            if domain and domain_dir != domain:
                continue
            
            # List models in this domain
            for model_name in os.listdir(domain_path):
                model_path = os.path.join(domain_path, model_name)
                
                if os.path.isdir(model_path):
                    models.append((domain_dir, model_name))
        
        return models
    
    def remove(self, registry_id: str) -> bool:
        """Remove a locally installed model"""
        domain, model_name = registry_id.split("/", 1)
        local_path = os.path.join(self.cache_dir, domain, model_name)
        
        if not os.path.exists(local_path):
            console.print(f"[yellow]Model not found locally[/yellow]")
            return False
        
        import shutil
        shutil.rmtree(local_path)
        console.print(f"✅ Removed [cyan]{registry_id}[/cyan]")
        return True


# Singleton instance
_downloader = None

def get_downloader() -> ModelDownloader:
    """Get the global downloader instance"""
    global _downloader
    if _downloader is None:
        _downloader = ModelDownloader()
    return _downloader


def pull_model(registry_id: str, force: bool = False) -> str:
    """Convenience function to pull a model"""
    downloader = get_downloader()
    return downloader.pull(registry_id, force=force)
