"""
Path resolution utilities for workspace pollution avoidance
Provides OS-appropriate default data directories following platform conventions
"""

import os
import platform
from pathlib import Path
from typing import Optional


def get_user_data_dir(app_name: str = "mcp-assoc-memory") -> Path:
    """
    Get OS-appropriate user data directory for the application
    
    Args:
        app_name: Application name for directory naming
        
    Returns:
        Path: User data directory path
        
    Platform conventions:
        - Linux: $XDG_DATA_HOME/app_name or ~/.local/share/app_name
        - macOS: ~/Library/Application Support/app_name  
        - Windows: %APPDATA%/app_name
    """
    system = platform.system()
    
    if system == "Linux":
        # XDG Base Directory Specification
        xdg_data_home = os.getenv("XDG_DATA_HOME")
        if xdg_data_home:
            return Path(xdg_data_home) / app_name
        else:
            return Path.home() / ".local" / "share" / app_name
            
    elif system == "Darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / app_name
        
    elif system == "Windows":
        appdata = os.getenv("APPDATA")
        if appdata:
            return Path(appdata) / app_name
        else:
            # Fallback to user profile
            return Path.home() / "AppData" / "Roaming" / app_name
            
    else:
        # Fallback for unknown systems
        return Path.home() / f".{app_name}"


def get_user_cache_dir(app_name: str = "mcp-assoc-memory") -> Path:
    """
    Get OS-appropriate user cache directory for the application
    
    Args:
        app_name: Application name for directory naming
        
    Returns:
        Path: User cache directory path
    """
    system = platform.system()
    
    if system == "Linux":
        xdg_cache_home = os.getenv("XDG_CACHE_HOME") 
        if xdg_cache_home:
            return Path(xdg_cache_home) / app_name
        else:
            return Path.home() / ".cache" / app_name
            
    elif system == "Darwin":  # macOS
        return Path.home() / "Library" / "Caches" / app_name
        
    elif system == "Windows":
        localappdata = os.getenv("LOCALAPPDATA")
        if localappdata:
            return Path(localappdata) / app_name
        else:
            return Path.home() / "AppData" / "Local" / app_name
            
    else:
        # Fallback for unknown systems  
        return Path.home() / f".cache-{app_name}"


def resolve_data_path(
    configured_path: str, 
    default_subdir: str = "", 
    use_workspace_if_relative: bool = True
) -> Path:
    """
    Resolve data path with workspace pollution avoidance
    
    Args:
        configured_path: Path from configuration (may be relative or absolute)
        default_subdir: Subdirectory within user data dir if using defaults
        use_workspace_if_relative: If True, relative paths use workspace; if False, use user data dir
        
    Returns:
        Path: Resolved absolute path
        
    Logic:
        1. If configured_path is absolute, use as-is
        2. If configured_path looks like a workspace-relative path (starts with 'data/', './data/'), 
           convert to user data directory equivalent  
        3. If configured_path is other relative path and use_workspace_if_relative=True, 
           use workspace-relative
        4. Otherwise use user data directory
    """
    path = Path(configured_path)
    
    # If absolute path, use as-is
    if path.is_absolute():
        return path
        
    # Check if this looks like a workspace data path
    path_str = str(path)
    if (path_str.startswith("data/") or 
        path_str.startswith("./data/") or 
        path_str == "data"):
        
        # Convert workspace data path to user data directory
        user_data_dir = get_user_data_dir()
        
        if path_str.startswith("data/"):
            subpath = path_str[5:]  # Remove "data/" prefix
        elif path_str.startswith("./data/"):
            subpath = path_str[7:]  # Remove "./data/" prefix
        else:  # path_str == "data"
            subpath = ""
            
        if subpath:
            return user_data_dir / subpath
        else:
            return user_data_dir / default_subdir if default_subdir else user_data_dir
    
    # For other relative paths
    if use_workspace_if_relative:
        # Use workspace-relative (existing behavior)
        return Path.cwd() / path
    else:
        # Use user data directory
        user_data_dir = get_user_data_dir()
        return user_data_dir / path


def ensure_directory(path: Path) -> Path:
    """
    Ensure directory exists, creating parent directories as needed
    
    Args:
        path: Directory path to ensure
        
    Returns:
        Path: The ensured directory path
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_default_database_path() -> str:
    """
    Get default database path that avoids workspace pollution
    
    Returns:
        str: Default database path
    """
    return str(resolve_data_path("data/memory.db", "memory.db"))


def get_default_chroma_path() -> str:
    """
    Get default ChromaDB path that avoids workspace pollution
    
    Returns:
        str: Default ChromaDB path
    """
    return str(resolve_data_path("data/chroma_db", "chroma_db"))


def get_default_data_dir() -> str:
    """
    Get default data directory that avoids workspace pollution
    
    Returns:
        str: Default data directory path
    """
    return str(resolve_data_path("data", ""))


def get_default_graph_path() -> str:
    """
    Get default graph store path that avoids workspace pollution
    
    Returns:
        str: Default graph store path
    """
    return str(resolve_data_path("data/memory_graph.pkl", "memory_graph.pkl"))


# Environment variable names for path overrides
ENV_DATABASE_PATH = "MCP_DATABASE_PATH"
ENV_CHROMA_PATH = "MCP_CHROMA_PATH" 
ENV_DATA_DIR = "MCP_DATA_DIR"
ENV_GRAPH_PATH = "MCP_GRAPH_PATH"