"""Export and import tools for MCP associative memory server."""

import base64
import gzip
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from ...core.singleton_memory_manager import get_or_create_memory_manager
from ..models.requests import MemoryExportRequest, MemoryImportRequest
from ..models.responses import MemoryExportResponse, MemoryImportResponse


async def _resolve_export_path(file_path: str) -> Path:
    """Resolve export file path with proper validation."""
    path = Path(file_path)

    # If it's a relative path, make it relative to the data directory
    if not path.is_absolute():
        data_dir = Path("data/exports")
        data_dir.mkdir(parents=True, exist_ok=True)
        path = data_dir / path

    return path


async def handle_memory_export(request: MemoryExportRequest, ctx: Any) -> Dict[str, Any]:
    """Handle memory_export tool requests."""
    # Contract Programming: ctx MUST be provided for proper logging and error handling
    assert ctx is not None, "Context object is required for export operations"
    assert hasattr(ctx, "info"), f"Context object missing required 'info' method: {type(ctx)}"
    assert hasattr(ctx, "error"), f"Context object missing required 'error' method: {type(ctx)}"

    try:
        scope_info = f" from scope '{request.scope}'" if request.scope else " (all scopes)"
        export_mode = "file" if request.file_path else "direct data"

        await ctx.info(f"Exporting memories{scope_info} via {export_mode}")

        # Get memory manager instance
        memory_manager = await get_or_create_memory_manager()

        if not memory_manager:
            return {"error": "Memory manager not available", "export_count": 0}

        # Get all memories using the same method as memory_list_all
        # TODO: PERFORMANCE OPTIMIZATION - For large datasets, this should be implemented
        # as a streaming approach to avoid loading all memories into memory at once.
        # Consider implementing: async generator + streaming JSON writer pattern
        # to process memories one-by-one and write directly to file/response stream.
        all_memory_objects = await memory_manager.metadata_store.get_all_memories(limit=10000)

        # Filter memories by scope if specified
        export_memories = []
        for memory in all_memory_objects:
            if not memory:
                continue

            if request.scope:
                # Include if memory scope matches or is a child of request scope
                memory_scope = memory.scope if hasattr(memory, "scope") else ""
                if memory_scope == request.scope or memory_scope.startswith(request.scope + "/"):
                    export_memories.append(memory)
            else:
                export_memories.append(memory)

        # Prepare export data structure
        export_data: Dict[str, Any] = {
            "format_version": "1.0",
            "export_timestamp": datetime.now().isoformat(),
            "export_scope": request.scope,
            "total_memories": len(export_memories),
            "include_associations": request.include_associations,
            "memories": [],
        }

        # Process each memory for export
        # TODO: MEMORY EFFICIENCY - Current implementation loads all export data into memory.
        # For production use with large datasets, implement streaming JSON serialization:
        # 1. Write JSON header to file/stream first
        # 2. Process memories one-by-one and append to JSON array
        # 3. Close JSON structure and file handle
        # This avoids potential memory exhaustion with large memory collections.
        for memory in export_memories:
            # Contract Programming: Memory objects MUST have required attributes
            assert hasattr(memory, "id"), f"Memory object missing required 'id' attribute: {type(memory)}"
            assert hasattr(memory, "content"), f"Memory object missing required 'content' attribute: {type(memory)}"
            assert hasattr(memory, "scope"), f"Memory object missing required 'scope' attribute: {type(memory)}"

            memory_export = {
                "memory_id": memory.id,
                "content": memory.content,
                "scope": memory.scope,
                "metadata": memory.metadata if hasattr(memory, "metadata") else {},
                "tags": memory.tags if hasattr(memory, "tags") else [],
                "category": memory.category if hasattr(memory, "category") else None,
                "created_at": memory.created_at.isoformat()
                if hasattr(memory, "created_at") and memory.created_at
                else "",
                "updated_at": memory.updated_at.isoformat()
                if hasattr(memory, "updated_at") and memory.updated_at
                else "",
            }

            # Add associations if requested
            if request.include_associations:
                # Contract Programming: Memory object MUST have valid id attribute
                assert hasattr(memory, "id"), f"Memory object missing required 'id' attribute: {type(memory)}"
                assert memory.id, f"Memory object has empty/null id: {memory.id}"

                # Get associations from memory manager - if this fails, export should fail
                try:
                    associations = await memory_manager.get_associations(memory.id, limit=10)
                    memory_export["associations"] = [assoc.id for assoc in associations] if associations else []
                except Exception as e:
                    # Association retrieval failure is a critical error, not a fallback case
                    raise RuntimeError(f"Failed to retrieve associations for memory {memory.id}: {e}")
            else:
                memory_export["associations"] = []

            memories_list = export_data["memories"]
            if isinstance(memories_list, list):
                memories_list.append(memory_export)

        # Convert to JSON
        json_data = json.dumps(export_data, indent=2, ensure_ascii=False)

        # Apply compression if requested
        final_data = json_data
        compression_used = False
        if request.compression:
            compressed_data = gzip.compress(json_data.encode("utf-8"))
            final_data = base64.b64encode(compressed_data).decode("ascii")
            compression_used = True

        export_size = len(final_data.encode("utf-8"))

        # Check size limits (use fallback values if config not properly loaded)
        try:
            # Use default limit of 100MB for export size
            max_size_mb = 100  # Default 100MB limit
        except AttributeError:
            max_size_mb = 100  # Default 100MB limit

        if export_size > max_size_mb * 1024 * 1024:
            return {
                "success": False,
                "error": f"Export size ({export_size / 1024 / 1024:.1f}MB) exceeds limit ({max_size_mb}MB)",
                "data": {},
            }

        # Handle file export (Pattern A)
        if request.file_path:
            file_path = await _resolve_export_path(request.file_path)

            # Ensure export directory exists
            export_dir = Path(file_path).parent
            export_dir.mkdir(parents=True, exist_ok=True)

            # Write to file
            with open(file_path, "w", encoding="utf-8") as f:
                if compression_used:
                    # For file export, store compressed data as base64
                    f.write(f"# Compressed MCP Memory Export (base64-encoded gzip)\n{final_data}")
                else:
                    f.write(final_data)

            await ctx.info(f"Exported {len(export_memories)} memories to file: {file_path}")

            return MemoryExportResponse(
                success=True,
                message=f"Exported {len(export_memories)} memories to file",
                data={
                    "scope": request.scope,
                    "export_size": export_size,
                    "compression_used": compression_used,
                    "format_version": "1.0",
                    "export_format": request.export_format,
                    "timestamp": datetime.now().isoformat(),
                },
                file_path=str(file_path),
                exported_count=len(export_memories),
                export_format=request.export_format,
            ).model_dump()

        # Handle direct data export (Pattern B)
        else:
            await ctx.info(f"Exported {len(export_memories)} memories as direct data")

            return MemoryExportResponse(
                success=True,
                message=f"Exported {len(export_memories)} memories as direct data",
                data={
                    "scope": request.scope,
                    "export_size": export_size,
                    "compression_used": compression_used,
                    "format_version": "1.0",
                    "export_format": request.export_format,
                    "timestamp": datetime.now().isoformat(),
                },
                export_data=final_data,
                exported_count=len(export_memories),
                export_format=request.export_format,
            ).model_dump()

    except Exception as e:
        error_msg = f"Failed to export memories: {e}"
        await ctx.error(error_msg)
        # Return proper MCP error response instead of silent success
        return {"success": False, "error": error_msg, "exported_count": 0, "data": {}}


async def handle_memory_import(request: MemoryImportRequest, ctx: Any) -> Dict[str, Any]:
    """Handle memory_import tool requests."""
    # Contract Programming: ctx MUST be provided for proper logging and error handling
    assert ctx is not None, "Context object is required for import operations"
    assert hasattr(ctx, "info"), f"Context object missing required 'info' method: {type(ctx)}"
    assert hasattr(ctx, "error"), f"Context object missing required 'error' method: {type(ctx)}"

    try:
        # Import implementation would go here - this is a placeholder
        # for the full implementation that exists in the handlers
        await ctx.info("Memory import functionality (placeholder)")

        return MemoryImportResponse(
            success=True,
            message="Memory import functionality (placeholder)",
            data={"operation": "import_placeholder", "timestamp": datetime.now().isoformat()},
            imported_count=0,
            skipped_count=0,
            error_count=0,
            import_summary={},
        ).model_dump()

    except Exception as e:
        error_msg = f"Failed to import memories: {e}"
        await ctx.error(error_msg)
        # Return proper MCP error response instead of silent success
        return {"success": False, "error": error_msg, "imported_count": 0, "data": {}}
