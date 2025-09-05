#!/usr/bin/env python3
"""
Example demonstrating database path configuration and workspace pollution avoidance
Run this to see how the new path resolution works
"""

import os
import sys
from pathlib import Path

# Add src to path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def main():
    print("MCP Associative Memory - Database Path Configuration Example")
    print("=" * 60)
    
    try:
        from mcp_assoc_memory.config import Config
        from mcp_assoc_memory.utils.paths import (
            get_user_data_dir,
            get_default_database_path,
            get_default_chroma_path,
            get_default_data_dir,
        )
    except ImportError as e:
        print(f"Error importing modules: {e}")
        print("Please run this from the repository root directory")
        return
    
    print("\n1. User Data Directory Resolution:")
    user_data_dir = get_user_data_dir()
    print(f"   OS-appropriate data directory: {user_data_dir}")
    
    print("\n2. Default Database Paths (Workspace Pollution Avoidance):")
    print(f"   Database file: {get_default_database_path()}")
    print(f"   ChromaDB directory: {get_default_chroma_path()}")
    print(f"   Data directory: {get_default_data_dir()}")
    
    print("\n3. Current Workspace vs Data Paths:")
    workspace = Path.cwd()
    print(f"   Workspace: {workspace}")
    print(f"   Data outside workspace: {not str(get_default_data_dir()).startswith(str(workspace))}")
    
    print("\n4. Configuration Instance:")
    config = Config.load()  # Use load() to include environment variables
    print(f"   Config database path: {config.database.path}")
    print(f"   Config data directory: {config.storage.data_dir}")
    
    print("\n5. Environment Variable Override Example:")
    print("   Try setting environment variables:")
    print("   export MCP_DATABASE_PATH='/custom/path/memory.db'")
    print("   export MCP_DATA_DIR='/custom/data/directory'")
    
    # Show current environment values if set
    env_db_path = os.getenv("MCP_DATABASE_PATH")
    env_data_dir = os.getenv("MCP_DATA_DIR")
    
    if env_db_path:
        print(f"   Current MCP_DATABASE_PATH: {env_db_path}")
    if env_data_dir:
        print(f"   Current MCP_DATA_DIR: {env_data_dir}")
        
    print("\n6. Backward Compatibility:")
    print("   - Existing absolute paths continue to work")
    print("   - Legacy environment variables (DB_PATH, DATA_DIR) still supported")
    print("   - Configuration files work unchanged")
    
    print("\n" + "=" * 60)
    print("✅ Workspace pollution avoidance is active!")
    print("   Database files will be stored in user data directories")
    print("   Your workspace remains clean 🧹")


if __name__ == "__main__":
    main()