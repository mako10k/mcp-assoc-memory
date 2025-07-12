"""
Simple JSON-based persistence for FastMCP memory storage
Adds file-based persistence to the current in-memory implementation
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Tuple

logger = logging.getLogger(__name__)


class SimplePersistence:
    """Simple JSON file-based persistence for memory storage"""

    def __init__(self, storage_file: str = "/workspaces/mcp-assoc-memory/data/memories.json"):
        self.storage_file = Path(storage_file)
        self.storage_file.parent.mkdir(exist_ok=True)

    def load_memories(self) -> Dict[str, Any]:
        """Load memories from JSON file"""
        if not self.storage_file.exists():
            logger.info(f"Storage file {self.storage_file} does not exist, starting with empty storage")
            return {}

        try:
            with open(self.storage_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Convert datetime strings back to datetime objects
            for memory_id, memory_data in data.items():
                if "created_at" in memory_data and isinstance(memory_data["created_at"], str):
                    memory_data["created_at"] = datetime.fromisoformat(memory_data["created_at"])

            logger.info(f"Loaded {len(data)} memories from {self.storage_file}")
            return dict(data)  # Ensure proper type casting

        except Exception as e:
            logger.error(f"Failed to load memories from {self.storage_file}: {e}")
            # Backup corrupted file
            backup_file = self.storage_file.with_suffix(".json.backup")
            if self.storage_file.exists():
                self.storage_file.rename(backup_file)
                logger.info(f"Corrupted file backed up to {backup_file}")
            return {}

    def save_memories(self, storage: Dict[str, Any]) -> bool:
        """Save memories to JSON file"""
        try:
            # Create temporary file for atomic write
            temp_file = self.storage_file.with_suffix(".json.tmp")

            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(storage, f, ensure_ascii=False, indent=2, default=str)

            # Atomic replace
            temp_file.replace(self.storage_file)

            logger.debug(f"Saved {len(storage)} memories to {self.storage_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to save memories to {self.storage_file}: {e}")
            return False

    def backup_memories(self, storage: Dict[str, Any]) -> bool:
        """Create a timestamped backup"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.storage_file.with_name(f"memories_backup_{timestamp}.json")

        try:
            with open(backup_file, "w", encoding="utf-8") as f:
                json.dump(storage, f, ensure_ascii=False, indent=2, default=str)

            logger.info(f"Created backup: {backup_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False


# Usage example for server.py integration:
def get_persistent_storage() -> Tuple[Dict[str, Any], "SimplePersistence"]:
    """Get persistent storage instance"""
    persistence = SimplePersistence()
    return persistence.load_memories(), persistence


# Integration pattern:
"""
# In server.py, replace:
memory_storage = {}

# With:
memory_storage, persistence = get_persistent_storage()

# In each tool function that modifies data, add:
persistence.save_memories(memory_storage)
"""
