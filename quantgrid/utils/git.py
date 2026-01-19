import os
import subprocess
import getpass

def get_current_branch():
    """Returns the name of the current git branch"""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except:
        return "unknown"

def generate_rescue_branch_name(message):
    """
    Creates a 'Walk of Shame' branch name.
    """
    user = getpass.getuser().lower().replace(" ", "")
    # Minimal slug from message
    slug_parts = message.lower().split()[:3]
    slug = "-".join(slug_parts).replace("/", "-") or "unnamed-work"
    
    # Mischievous prefixes
    prefixes = ["oops", "rescue", "panic-save", "main-is-lava"]
    import random
    prefix = random.choice(prefixes)
    
    return f"grid-auto/{prefix}-{user}-{slug}"
