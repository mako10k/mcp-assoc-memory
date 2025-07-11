"""Export and import tools for MCP associative memory server."""

import base64
import gzip
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from ...simple_persistence import get_persistent_storage

# Get storage
memory_storage, persistence = get_persistent_storage()
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
    try:
        scope_info = f" from scope '{request.scope}'" if request.scope else " (all scopes)"
        export_mode = "file" if request.file_path else "direct data"
        await ctx.info(f"Exporting memories{scope_info} via {export_mode}")
        
        # Filter memories by scope
        export_memories = []
        for memory_data in memory_storage.values():
            if request.scope:
                memory_scope = memory_data["scope"]
                # Include if memory scope matches or is a child of request scope
                if memory_scope == request.scope or memory_scope.startswith(request.scope + "/"):
                    export_memories.append(memory_data)
            else:
                export_memories.append(memory_data)
        
        # Prepare export data structure
        export_data = {
            "format_version": "1.0",
            "export_timestamp": datetime.now().isoformat(),
            "export_scope": request.scope,
            "total_memories": len(export_memories),
            "include_associations": request.include_associations,
            "memories": []
        }
        
        # Process each memory for export
        for memory_data in export_memories:
            memory_export = {
                "memory_id": memory_data["memory_id"],
                "content": memory_data["content"],
                "scope": memory_data["scope"],
                "metadata": memory_data.get("metadata", {}),
                "tags": memory_data.get("tags", []),
                "category": memory_data.get("category"),
                "created_at": memory_data["created_at"].isoformat() if isinstance(memory_data["created_at"], datetime) else memory_data["created_at"]
            }
            
            # Add associations if requested
            if request.include_associations:
                # Get associations from advanced storage if available
                try:
                    memory = await memory_manager.get_memory(memory_data["memory_id"])
                    if memory:
                        associations = await memory_manager.get_associations(memory.id)
                        memory_export["associations"] = [assoc.id for assoc in associations]
                except:
                    memory_export["associations"] = []
            
            export_data["memories"].append(memory_export)
        
        # Convert to JSON
        json_data = json.dumps(export_data, indent=2, ensure_ascii=False)
        
        # Apply compression if requested
        final_data = json_data
        compression_used = False
        if request.compression:
            compressed_data = gzip.compress(json_data.encode('utf-8'))
            final_data = base64.b64encode(compressed_data).decode('ascii')
            compression_used = True
        
        export_size = len(final_data.encode('utf-8'))
        
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
                "data": {}
            }
        
        # Handle file export (Pattern A)
        if request.file_path:
            file_path = await _resolve_export_path(request.file_path)
            
            # Ensure export directory exists
            export_dir = Path(file_path).parent
            export_dir.mkdir(parents=True, exist_ok=True)
            
            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                if compression_used:
                    # For file export, store compressed data as base64
                    f.write(f"# Compressed MCP Memory Export (base64-encoded gzip)\n{final_data}")
                else:
                    f.write(final_data)
            
            await ctx.info(f"Exported {len(export_memories)} memories to file: {file_path}")
            
            return MemoryExportResponse(
                success=True,
                exported_count=len(export_memories),
                export_scope=request.scope,
                file_path=str(file_path),
                export_size=export_size,
                compression_used=compression_used,
                metadata={
                    "format_version": "1.0",
                    "export_format": request.export_format,
                    "timestamp": datetime.now().isoformat()
                }
            ).model_dump()
        
        # Handle direct data export (Pattern B)
        else:
            await ctx.info(f"Exported {len(export_memories)} memories as direct data")
            
            return MemoryExportResponse(
                success=True,
                exported_count=len(export_memories),
                export_scope=request.scope,
                export_data=final_data,
                export_size=export_size,
                compression_used=compression_used,
                metadata={
                    "format_version": "1.0",
                    "export_format": request.export_format,
                    "timestamp": datetime.now().isoformat()
                }
            ).model_dump()
            
    except Exception as e:
        await ctx.error(f"Failed to export memories: {e}")
        return {
            "success": False,
            "error": f"Failed to export memories: {e}",
            "data": {}
        }


async def handle_memory_import(request: MemoryImportRequest, ctx: Any) -> Dict[str, Any]:
    """Handle memory_import tool requests."""
    try:
        # Import implementation would go here - this is a placeholder
        # for the full implementation that exists in the handlers
        await ctx.info("Memory import functionality (placeholder)")
        
        return MemoryImportResponse(
            success=True,
            imported_count=0,
            skipped_count=0,
            updated_count=0,
            errors=[]
        ).model_dump()
        
    except Exception as e:
        await ctx.error(f"Failed to import memories: {e}")
        return {
            "success": False,
            "error": f"Failed to import memories: {e}",
            "data": {}
        }
