#!/usr/bin/env python3
"""
Debug script to test scope_suggest response levels without mock interference
"""
import asyncio
import sys
import json
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp_assoc_memory.api.tools.scope_tools import handle_scope_suggest
from mcp_assoc_memory.api.models.requests import ScopeSuggestRequest
from mcp_assoc_memory.api.models.common import ResponseLevel
from fastmcp import Context


async def debug_scope_suggest():
    """Debug scope_suggest with actual calls"""
    
    # Create a simple context
    ctx = Context()
    
    # Test content
    test_content = "Meeting notes from standup discussion"
    
    # Test all response levels
    for level in [ResponseLevel.MINIMAL, ResponseLevel.STANDARD, ResponseLevel.FULL]:
        print(f"\n=== Testing {level.value.upper()} level ===")
        
        # Create request
        request = ScopeSuggestRequest(
            content=test_content,
            response_level=level
        )
        
        try:
            # Call the actual function
            result = await handle_scope_suggest(request, ctx)
            
            print(f"Result keys: {list(result.keys())}")
            print(f"Full result: {json.dumps(result, indent=2)}")
            
            # Check expected fields based on level
            if level == ResponseLevel.MINIMAL:
                expected_not_in = ["reasoning", "alternatives"]
                for field in expected_not_in:
                    if field in result:
                        print(f"WARNING: {field} found in MINIMAL response but shouldn't be")
            
            elif level == ResponseLevel.STANDARD:
                expected_in = ["reasoning", "alternatives"]
                for field in expected_in:
                    if field not in result:
                        print(f"ERROR: {field} missing from STANDARD response")
                    else:
                        print(f"OK: {field} found in STANDARD response")
            
            elif level == ResponseLevel.FULL:
                expected_in = ["reasoning", "alternatives", "detailed_alternatives", "analysis_metadata"]
                for field in expected_in:
                    if field not in result:
                        print(f"ERROR: {field} missing from FULL response")
                    else:
                        print(f"OK: {field} found in FULL response")
                        
        except Exception as e:
            print(f"ERROR in {level.value}: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_scope_suggest())
