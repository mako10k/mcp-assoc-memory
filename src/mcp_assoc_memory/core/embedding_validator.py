"""
Embedding Provider Compatibility Validator

Ensures data integrity by preventing incompatible embedding provider changes.
Different embedding providers create incompatible vector spaces that would
corrupt similarity calculations and search results.
"""

import json
from datetime import datetime
from typing import Any, Dict, Optional

from ..config import get_config
from ..storage.metadata_store import SQLiteMetadataStore
from ..utils.logging import get_memory_logger

logger = get_memory_logger(__name__)


class EmbeddingCompatibilityError(RuntimeError):
    """Raised when embedding provider change would corrupt existing data"""

    pass


class EmbeddingValidator:
    """Validates embedding provider compatibility to prevent data corruption"""

    def __init__(self, metadata_store: SQLiteMetadataStore):
        self.metadata_store = metadata_store

    async def validate_embedding_compatibility(self) -> None:
        """
        Validates that current embedding configuration is compatible with stored data.
        Raises EmbeddingCompatibilityError if incompatible change detected.
        """
        current_config = self._get_current_embedding_config()
        stored_config = await self._get_stored_embedding_config()

        # Mask sensitive data for logging
        current_safe = {k: ("***MASKED***" if "key" in k.lower() else v) for k, v in current_config.items()}
        stored_safe = (
            {k: ("***MASKED***" if "key" in k.lower() else v) for k, v in stored_config.items()}
            if stored_config
            else None
        )
        logger.info(f"Validating embedding compatibility: current={current_safe}, stored={stored_safe}")

        if stored_config is None:
            # First run - store current configuration
            await self._store_embedding_config(current_config)
            logger.info("First run detected - storing embedding configuration")
            return

        # Check for incompatible changes
        compatibility_issues = self._check_compatibility(stored_config, current_config)

        if compatibility_issues:
            error_msg = self._build_error_message(stored_config, current_config, compatibility_issues)
            logger.error(f"EMBEDDING PROVIDER COMPATIBILITY ERROR: {error_msg}")
            raise EmbeddingCompatibilityError(error_msg)

        # Update configuration if minor changes
        if stored_config != current_config:
            await self._store_embedding_config(current_config)
            logger.info("Embedding configuration updated (compatible change)")

    def _get_current_embedding_config(self) -> Dict[str, Any]:
        """Get current embedding configuration from config"""
        config = get_config()
        embedding_config = config.embedding  # Use dataclass directly

        # Convert provider to standardized format for validation
        provider = embedding_config.provider
        if provider == "local":
            provider = "sentence_transformer"  # Normalize for compatibility checking

        return {
            "provider": provider,
            "model": embedding_config.model,
            "dimensions": "auto",  # Will be determined by actual embedding service
            "config_hash": self._calculate_config_hash({"provider": provider, "model": embedding_config.model}),
        }

    async def _get_stored_embedding_config(self) -> Optional[Dict[str, Any]]:
        """Get stored embedding configuration from database"""
        try:
            provider = await self.metadata_store.get_system_setting("embedding_provider")
            if provider is None:
                return None

            model = await self.metadata_store.get_system_setting("embedding_model")
            dimensions = await self.metadata_store.get_system_setting("embedding_dimensions")
            config_hash = await self.metadata_store.get_system_setting("embedding_config_hash")

            return {
                "provider": provider,
                "model": model or "unknown",
                "dimensions": dimensions or "auto",
                "config_hash": config_hash or "unknown",
            }
        except Exception as e:
            logger.error(f"Failed to get stored embedding config: {e}")
            return None

    async def _store_embedding_config(self, config: Dict[str, Any]) -> None:
        """Store embedding configuration to database"""
        try:
            await self.metadata_store.set_system_setting("embedding_provider", config["provider"])
            await self.metadata_store.set_system_setting("embedding_model", config["model"])
            await self.metadata_store.set_system_setting("embedding_dimensions", str(config["dimensions"]))
            await self.metadata_store.set_system_setting("embedding_config_hash", config["config_hash"])
            await self.metadata_store.set_system_setting("embedding_last_updated", datetime.utcnow().isoformat())

            logger.info(f"Stored embedding configuration: {config}")
        except Exception as e:
            logger.error(f"Failed to store embedding config: {e}")
            raise

    def _check_compatibility(self, stored: Dict[str, Any], current: Dict[str, Any]) -> list[str]:
        """Check for compatibility issues between stored and current configs"""
        issues = []

        # Provider change is always incompatible
        if stored["provider"] != current["provider"]:
            issues.append(f"Provider changed from '{stored['provider']}' to '{current['provider']}'")

        # Model change within same provider is incompatible
        if stored["provider"] == current["provider"] and stored["model"] != current["model"]:
            issues.append(f"Model changed from '{stored['model']}' to '{current['model']}'")

        return issues

    def _calculate_config_hash(self, config: Dict[str, Any]) -> str:
        """Calculate hash of configuration for change detection"""
        import hashlib

        # Only include settings that affect vector compatibility
        relevant_config = {"provider": config.get("provider", "mock"), "model": config.get("model", "unknown")}

        config_str = json.dumps(relevant_config, sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()[:16]

    def _build_error_message(self, stored: Dict[str, Any], current: Dict[str, Any], issues: list[str]) -> str:
        """Build detailed error message with migration instructions"""
        issue_list = "\\n  - ".join(issues)

        return f"""
Embedding provider configuration change detected that would corrupt existing vectors:
  - {issue_list}

This would cause:
  • Incorrect similarity calculations
  • Wrong search results
  • Corrupted memory associations

To safely change embedding providers:
  1. Export your data: memory_sync(operation='export', file_path='backup.json')
  2. Clear vector database: Delete data/chroma_db/ directory
  3. Clear system settings: Delete data/memory.db or reset database
  4. Restart with new provider configuration
  5. Re-import data: memory_sync(operation='import', file_path='backup.json')

Current config: {current}
Stored config:  {stored}
"""

    async def force_reset_configuration(self) -> None:
        """Force reset embedding configuration (for migrations/debugging)"""
        try:
            await self.metadata_store.delete_system_setting("embedding_provider")
            await self.metadata_store.delete_system_setting("embedding_model")
            await self.metadata_store.delete_system_setting("embedding_dimensions")
            await self.metadata_store.delete_system_setting("embedding_config_hash")
            await self.metadata_store.delete_system_setting("embedding_last_updated")

            logger.warning("Embedding configuration forcefully reset")
        except Exception as e:
            logger.error(f"Failed to reset embedding configuration: {e}")
            raise
