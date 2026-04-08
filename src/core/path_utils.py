import os
import logging

class SecurityException(Exception):
    """Raised when a security boundary violation is detected."""
    pass

def validate_vault_path(path: str, vault_root: str) -> str:
    """
    Resolves and validates that a given path is strictly within the vault_root.
    Returns the absolute path if valid, raises SecurityException otherwise.
    """
    # 1. Resolve absolute paths
    abs_vault = os.path.abspath(vault_root)
    
    # If path is relative, join it with vault_root first
    if not os.path.isabs(path):
        target_path = os.path.join(abs_vault, path)
    else:
        target_path = path

    abs_target = os.path.abspath(target_path)

    # 2. Boundary Check: Ensure abs_target starts with abs_vault
    # Use commonpath to handle symlinks and different trailing slashes
    if os.path.commonpath([abs_vault]) != os.path.commonpath([abs_vault, abs_target]):
        logging.error(f"SECURITY ALERT: Path traversal attempt blocked: {abs_target} outside {abs_vault}")
        raise SecurityException(f"Path access violation: Access to {path} is prohibited.")

    return abs_target
