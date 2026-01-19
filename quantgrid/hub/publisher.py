"""
QuantGrid Hub - HuggingFace Publisher

Handles the actual storage of LoRA adapters on HuggingFace Hub.
This ensures zero-cost storage for the QuantGrid ecosystem.
"""

import os
from pathlib import Path
from huggingface_hub import HfApi, create_repo, upload_folder
from rich.console import Console
from loguru import logger

console = Console()

class ModelPublisher:
    """
    Handles uploading trained models to HuggingFace.
    """
    
    def __init__(self, token: str = None):
        self.api = HfApi(token=token)
        self.token = token or os.environ.get("HUGGINGFACE_TOKEN")

    def publish(
        self, 
        adapter_path: str, 
        repo_name: str, 
        organization: str = "QuantGrid-Community",
        private: bool = False
    ) -> str:
        """
        Uploads the adapter folder to HuggingFace.
        
        Args:
            adapter_path: Local path to the adapter folder
            repo_name: Name of the repository to create/update
            organization: HF Organization (or username)
            private: Whether the repo should be private
            
        Returns:
            The URL of the published model
        """
        repo_id = f"{organization}/{repo_name}"
        
        try:
            # 1. Create repo if it doesn't exist
            console.print(f"[dim]Checking repository: {repo_id}...[/dim]")
            create_repo(
                repo_id=repo_id,
                token=self.token,
                private=private,
                exist_ok=True,
                repo_type="model"
            )
            
            # 2. Upload the folder
            console.print(f"📤 Uploading to [cyan]huggingface.co/{repo_id}[/cyan]...")
            
            # We don't want to upload EVERYTHING (like temp files)
            # Just the essentials for a LoRA adapter
            allow_patterns = [
                "adapter_model.bin",
                "adapter_config.json",
                "README.md",
                "quantgrid_manifest.json"
            ]
            
            api_url = upload_folder(
                folder_path=adapter_path,
                repo_id=repo_id,
                token=self.token,
                repo_type="model",
                allow_patterns=allow_patterns
            )
            
            console.print(f"✅ Published successfully: [green]{api_url}[/green]")
            return api_url
            
        except Exception as e:
            logger.error(f"Failed to publish to HuggingFace: {e}")
            if "Unauthorized" in str(e):
                console.print("[red]❌ Error: Not authorized to upload to HuggingFace.[/red]")
                console.print("💡 Use 'huggingface-cli login' or set HUGGINGFACE_TOKEN environment variable.")
            else:
                console.print(f"[red]❌ Upload failed: {e}[/red]")
            raise

def get_publisher(token: str = None) -> ModelPublisher:
    """Get a publisher instance"""
    return ModelPublisher(token=token)
