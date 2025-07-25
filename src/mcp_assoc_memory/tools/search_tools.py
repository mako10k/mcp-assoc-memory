"""
Search and web fetch tools with direct associative memory integration

CRITICAL ISSUE: The current implementation fails to meet the core purpose of associative memory.

Problem: Google search results and WebFetch content are stored in memory but cannot be
reliably found through semantic search later. This violates the fundamental expectation
that "saved information should be discoverable when needed."

Core Requirements NOT MET:
1. Saved information must be findable through meaningful semantic search
2. Related information should automatically connect to each other
3. Users should be able to recall "that information I saw before"

The current implementation is merely a storage function, not true associative memory
that provides searchability, discoverability, and memory recall support.

TODO: Verify search performance, validate association functionality, test real usage scenarios
"""

import json
import logging
import asyncio
import aiohttp
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlencode, urlparse
import os
import re

from mcp.types import TextContent, Tool
from mcp_assoc_memory.config import get_config
from mcp_assoc_memory.core.singleton_memory_manager import get_memory_manager
from mcp_assoc_memory.core.session_manager import SessionManager

logger = logging.getLogger(__name__)


class SearchError(Exception):
    """Search-related errors"""
    pass


class FetchError(Exception):
    """Fetch-related errors"""
    pass


async def google_search_and_store(
    query: str,
    scope: Optional[str] = None,
    language: Optional[str] = None,
    region: Optional[str] = None,
    num_results: Optional[int] = None,
    start_index: Optional[int] = None,
    image_search: Optional[bool] = None,
    image_size: Optional[str] = None,
    image_type: Optional[str] = None,
    image_color: Optional[str] = None,
    store_individual_results: bool = True,
    store_summary: bool = True
) -> Dict[str, Any]:
    """
    Execute Google search and store results in associative memory
    
    Args:
        query: Search query
        scope: Target scope (default: session scope)
        language: Language for search results (ISO 639-1)
        region: Region for search results (ISO 3166-1 alpha-2)
        num_results: Number of results (1-10, default: 10)
        start_index: Starting index for results
        image_search: Enable image search mode
        image_size: Image size filter (small, medium, large)
        image_type: Image type filter (clipart, photo, lineart)
        image_color: Image color filter (black, white, red, blue, green, yellow)
        store_individual_results: Store each result as separate memory
        store_summary: Store search summary
    
    Returns:
        Dict with search results and memory storage info
    """
    # Validate inputs
    if not query or not query.strip():
        raise SearchError("Query parameter is required and must be a non-empty string")
    
    if num_results and (num_results < 1 or num_results > 10):
        raise SearchError("num_results must be between 1 and 10")
    
    if start_index and (start_index < 1 or start_index > 100 - (num_results or 10)):
        raise SearchError("start_index must be between 1 and (100 - num_results)")
    
    # Get API credentials
    google_api_key = os.getenv("GOOGLE_API_KEY")
    google_cx = os.getenv("GOOGLE_CX")
    
    if not google_api_key or not google_cx:
        raise SearchError("Google API key or CX is not set in environment variables")
    
    # Build search URL
    params = {
        "q": query,
        "key": google_api_key,
        "cx": google_cx,
    }
    
    if language:
        params["lr"] = f"lang_{language}"
    if region:
        params["cr"] = f"country{region}"
    if num_results:
        params["num"] = str(num_results)
    if start_index:
        params["start"] = str(start_index)
    if image_search:
        params["searchType"] = "image"
    if image_size:
        params["imgSize"] = image_size
    if image_type:
        params["imgType"] = image_type
    if image_color:
        params["imgColorType"] = image_color
    
    search_url = f"https://www.googleapis.com/customsearch/v1?{urlencode(params)}"
    
    # Execute search
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(search_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise SearchError(f"Google API error {response.status}: {error_text}")
                
                data = await response.json()
        except asyncio.TimeoutError:
            raise SearchError("Search request timed out")
        except aiohttp.ClientError as e:
            raise SearchError(f"Network error during search: {str(e)}")
    
    # Validate response
    if not data.get("items") or not isinstance(data["items"], list):
        if data.get("searchInformation", {}).get("totalResults") == "0":
            raise SearchError("No results found for the query")
        
        if spelling_suggestion := data.get("spelling", {}).get("correctedQuery"):
            raise SearchError(f"No results found. Did you mean: {spelling_suggestion}?")
        
        raise SearchError("Invalid response format from Google API")
    
    # Prepare scope
    if not scope:
        session_manager = SessionManager()
        current_session = session_manager.get_current_session()
        scope = f"session/{current_session}"
    
    # Get memory manager
    memory_manager = await get_memory_manager()
    if memory_manager is None:
        raise SearchError("Memory manager not initialized")
    stored_memories = []
    search_id = hashlib.md5(f"{query}_{datetime.now().isoformat()}".encode()).hexdigest()[:12]
    
    try:
        # Store individual results if requested
        if store_individual_results:
            for i, item in enumerate(data["items"]):
                result_content = f"Google Search Result #{i+1} for '{query}'\n\n"
                result_content += f"Title: {item.get('title', 'No title')}\n"
                result_content += f"URL: {item.get('link', 'No URL')}\n"
                result_content += f"Snippet: {item.get('snippet', 'No snippet')}\n"
                
                if item.get('displayLink'):
                    result_content += f"Display URL: {item['displayLink']}\n"
                
                # Store raw data as metadata
                metadata = {
                    "search_id": search_id,
                    "search_query": query,
                    "result_index": i + 1,
                    "result_type": "individual",
                    "url": item.get('link'),
                    "title": item.get('title'),
                    "source": "google_search",
                    "timestamp": datetime.now().isoformat(),
                    "raw_data": json.dumps(item)
                }
                
                memory_id = await memory_manager.store_memory(
                    content=result_content,
                    scope=scope,
                    metadata=metadata,
                    tags=["google_search", "search_result", query.lower().replace(" ", "_")]
                )
                
                stored_memories.append({
                    "memory_id": memory_id,
                    "type": "individual_result",
                    "index": i + 1,
                    "title": item.get('title'),
                    "url": item.get('link')
                })
        
        # Store search summary if requested
        if store_summary:
            summary_content = f"Google Search Summary: '{query}'\n\n"
            summary_content += f"Search performed at: {datetime.now().isoformat()}\n"
            summary_content += f"Total results found: {len(data['items'])}\n"
            summary_content += f"Search ID: {search_id}\n\n"
            
            summary_content += "Results Overview:\n"
            for i, item in enumerate(data["items"]):
                summary_content += f"{i+1}. {item.get('title', 'No title')}\n"
                summary_content += f"   URL: {item.get('link', 'No URL')}\n"
                summary_content += f"   Snippet: {item.get('snippet', 'No snippet')[:100]}...\n\n"
            
            # Summary metadata
            summary_metadata = {
                "search_id": search_id,
                "search_query": query,
                "result_count": len(data["items"]),
                "result_type": "summary",
                "source": "google_search",
                "timestamp": datetime.now().isoformat(),
                "search_parameters": {
                    "language": language,
                    "region": region,
                    "num_results": num_results,
                    "start_index": start_index,
                    "image_search": image_search
                }
            }
            
            summary_memory_id = await memory_manager.store_memory(
                content=summary_content,
                scope=scope,
                metadata=summary_metadata,
                tags=["google_search", "search_summary", query.lower().replace(" ", "_")]
            )
            
            stored_memories.append({
                "memory_id": summary_memory_id,
                "type": "search_summary",
                "result_count": len(data["items"])
            })
        
        logger.info(f"Google search completed and stored: {len(stored_memories)} memories created for query '{query}'")
        
        return {
            "success": True,
            "search_id": search_id,
            "query": query,
            "result_count": len(data["items"]),
            "scope": scope,
            "stored_memories": stored_memories,
            "summary": f"Successfully executed Google search for '{query}' and stored {len(stored_memories)} memories in scope '{scope}'"
        }
        
    except Exception as e:
        logger.error(f"Error storing search results: {str(e)}")
        raise SearchError(f"Failed to store search results in memory: {str(e)}")


async def fetch_url_and_store(
    url: str,
    scope: Optional[str] = None,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 30,
    include_response_headers: bool = True,
    max_content_size: int = 1024 * 1024,  # 1MB default
    store_metadata_separately: bool = True
) -> Dict[str, Any]:
    """
    Fetch URL content and store in associative memory
    
    Args:
        url: Target URL to fetch
        scope: Target scope (default: session scope)
        method: HTTP method (default: GET)
        headers: Custom HTTP headers
        timeout: Request timeout in seconds
        include_response_headers: Include response headers in metadata
        max_content_size: Maximum content size to fetch
        store_metadata_separately: Store metadata as separate memory
    
    Returns:
        Dict with fetch results and memory storage info
    """
    # Validate URL
    try:
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise FetchError("Invalid URL format")
    except Exception as e:
        raise FetchError(f"Invalid URL: {str(e)}")
    
    # Prepare scope
    if not scope:
        session_manager = SessionManager()
        current_session = session_manager.get_current_session()
        scope = f"session/{current_session}"
    
    # Execute fetch
    fetch_id = hashlib.md5(f"{url}_{datetime.now().isoformat()}".encode()).hexdigest()[:12]
    
    async with aiohttp.ClientSession() as session:
        try:
            request_headers = headers or {}
            async with session.request(
                method, 
                url, 
                headers=request_headers,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                
                # Get response info
                status_code = response.status
                status_text = response.reason or "Unknown"
                response_headers = dict(response.headers) if include_response_headers else {}
                content_type = response.headers.get('content-type', 'unknown')
                content_length = response.headers.get('content-length')
                
                # Read content with size limit
                content_bytes = await response.read()
                if len(content_bytes) > max_content_size:
                    content_bytes = content_bytes[:max_content_size]
                    content_truncated = True
                else:
                    content_truncated = False
                
                # Decode content
                try:
                    if 'text' in content_type.lower() or 'json' in content_type.lower() or 'xml' in content_type.lower():
                        content_text = content_bytes.decode('utf-8', errors='replace')
                    else:
                        content_text = f"[Binary content - {len(content_bytes)} bytes, content-type: {content_type}]"
                except Exception:
                    content_text = f"[Could not decode content - {len(content_bytes)} bytes]"
                
        except asyncio.TimeoutError:
            raise FetchError(f"Request to {url} timed out after {timeout} seconds")
        except aiohttp.ClientError as e:
            raise FetchError(f"Network error fetching {url}: {str(e)}")
    
    # Get memory manager
    memory_manager = await get_memory_manager()
    if memory_manager is None:
        raise FetchError("Memory manager not initialized")
    stored_memories = []
    
    try:
        # Store main content
        main_content = f"Web Fetch Result: {url}\n\n"
        main_content += f"Fetched at: {datetime.now().isoformat()}\n"
        main_content += f"HTTP Status: {status_code} {status_text}\n"
        main_content += f"Content Type: {content_type}\n"
        main_content += f"Content Length: {content_length or 'Unknown'}\n"
        if content_truncated:
            main_content += f"Content Truncated: Yes (max size: {max_content_size} bytes)\n"
        main_content += f"Fetch ID: {fetch_id}\n\n"
        main_content += "Content:\n"
        main_content += "=" * 50 + "\n"
        main_content += content_text
        
        # Main content metadata
        main_metadata = {
            "fetch_id": fetch_id,
            "url": url,
            "method": method,
            "status_code": status_code,
            "status_text": status_text,
            "content_type": content_type,
            "content_length": content_length,
            "content_size": len(content_bytes),
            "content_truncated": content_truncated,
            "source": "web_fetch",
            "timestamp": datetime.now().isoformat()
        }
        
        if include_response_headers:
            main_metadata["response_headers"] = response_headers
        
        # Clean URL for tags
        url_domain = parsed_url.netloc.replace("www.", "")
        url_tags = ["web_fetch", "url_content", url_domain.replace(".", "_")]
        
        main_memory_id = await memory_manager.store_memory(
            content=main_content,
            scope=scope,
            metadata=main_metadata,
            tags=url_tags
        )
        
        stored_memories.append({
            "memory_id": main_memory_id,
            "type": "main_content",
            "url": url,
            "status_code": status_code,
            "content_size": len(content_bytes)
        })
        
        # Store metadata separately if requested
        if store_metadata_separately and response_headers:
            metadata_content = f"HTTP Response Metadata for: {url}\n\n"
            metadata_content += f"Fetch ID: {fetch_id}\n"
            metadata_content += f"Request Method: {method}\n"
            metadata_content += f"Status: {status_code} {status_text}\n"
            metadata_content += f"Fetched at: {datetime.now().isoformat()}\n\n"
            
            metadata_content += "Response Headers:\n"
            metadata_content += "=" * 30 + "\n"
            for header_name, header_value in response_headers.items():
                metadata_content += f"{header_name}: {header_value}\n"
            
            if request_headers:
                metadata_content += "\nRequest Headers:\n"
                metadata_content += "=" * 30 + "\n"
                for header_name, header_value in request_headers.items():
                    metadata_content += f"{header_name}: {header_value}\n"
            
            metadata_metadata = {
                "fetch_id": fetch_id,
                "url": url,
                "method": method,
                "result_type": "metadata",
                "source": "web_fetch",
                "timestamp": datetime.now().isoformat(),
                "response_headers": response_headers,
                "request_headers": request_headers
            }
            
            metadata_memory_id = await memory_manager.store_memory(
                content=metadata_content,
                scope=scope,
                metadata=metadata_metadata,
                tags=url_tags + ["http_metadata"]
            )
            
            stored_memories.append({
                "memory_id": metadata_memory_id,
                "type": "http_metadata",
                "url": url
            })
        
        logger.info(f"URL fetch completed and stored: {len(stored_memories)} memories created for {url}")
        
        return {
            "success": True,
            "fetch_id": fetch_id,
            "url": url,
            "status_code": status_code,
            "status_text": status_text,
            "content_type": content_type,
            "content_size": len(content_bytes),
            "content_truncated": content_truncated,
            "scope": scope,
            "stored_memories": stored_memories,
            "summary": f"Successfully fetched {url} (status: {status_code}) and stored {len(stored_memories)} memories in scope '{scope}'"
        }
        
    except Exception as e:
        logger.error(f"Error storing fetch results: {str(e)}")
        raise FetchError(f"Failed to store fetch results in memory: {str(e)}")


# Tool definitions
GOOGLE_SEARCH_AND_STORE_TOOL = Tool(
    name="google-search-and-store",
    description="Execute Google search and store results directly in associative memory with session scope by default",
    inputSchema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query to perform"
            },
            "scope": {
                "type": "string",
                "description": "Target scope for storing memories (default: current session scope)"
            },
            "language": {
                "type": "string",
                "enum": ["en", "ja", "es", "fr", "de", "zh", "ru", "ar", "pt", "it"],
                "description": "Language for search results (ISO 639-1 codes)"
            },
            "region": {
                "type": "string", 
                "enum": ["US", "JP", "ES", "FR", "DE", "CN", "RU", "AR", "BR", "IT"],
                "description": "Region for search results (ISO 3166-1 alpha-2 codes)"
            },
            "num_results": {
                "type": "integer",
                "minimum": 1,
                "maximum": 10,
                "description": "Number of search results to return (1-10, default: 10)"
            },
            "start_index": {
                "type": "integer",
                "minimum": 1,
                "description": "Starting index for search results"
            },
            "image_search": {
                "type": "boolean",
                "description": "Enable image search mode"
            },
            "image_size": {
                "type": "string",
                "enum": ["small", "medium", "large"],
                "description": "Image size filter for image search"
            },
            "image_type": {
                "type": "string",
                "enum": ["clipart", "photo", "lineart"],
                "description": "Image type filter for image search"
            },
            "image_color": {
                "type": "string",
                "enum": ["black", "white", "red", "blue", "green", "yellow"],
                "description": "Image color filter for image search"
            },
            "store_individual_results": {
                "type": "boolean",
                "description": "Store each search result as separate memory (default: true)"
            },
            "store_summary": {
                "type": "boolean", 
                "description": "Store search summary (default: true)"
            }
        },
        "required": ["query"]
    }
)

FETCH_URL_AND_STORE_TOOL = Tool(
    name="fetch-url-and-store", 
    description="Fetch web content and store directly in associative memory with session scope by default",
    inputSchema={
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "format": "uri",
                "description": "Target URL to fetch"
            },
            "scope": {
                "type": "string",
                "description": "Target scope for storing memories (default: current session scope)"
            },
            "method": {
                "type": "string",
                "enum": ["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"],
                "description": "HTTP method (default: GET)"
            },
            "headers": {
                "type": "object",
                "additionalProperties": {"type": "string"},
                "description": "Custom HTTP headers"
            },
            "timeout": {
                "type": "integer",
                "minimum": 1,
                "maximum": 300,
                "description": "Request timeout in seconds (default: 30)"
            },
            "include_response_headers": {
                "type": "boolean",
                "description": "Include response headers in metadata (default: true)"
            },
            "max_content_size": {
                "type": "integer",
                "minimum": 1024,
                "maximum": 10485760,
                "description": "Maximum content size to fetch in bytes (default: 1MB)"
            },
            "store_metadata_separately": {
                "type": "boolean",
                "description": "Store HTTP metadata as separate memory (default: true)"
            }
        },
        "required": ["url"]
    }
)


# Tool handlers
async def handle_google_search_and_store(params: Dict[str, Any]) -> List[TextContent]:
    """Handle google-search-and-store tool request"""
    try:
        result = await google_search_and_store(**params)
        
        response_text = "✅ Google Search and Storage Completed\n\n"
        response_text += f"Query: {result['query']}\n"
        response_text += f"Results found: {result['result_count']}\n"
        response_text += f"Storage scope: {result['scope']}\n"
        response_text += f"Search ID: {result['search_id']}\n\n"
        
        response_text += "Stored Memories:\n"
        for memory in result['stored_memories']:
            response_text += f"- {memory['type']}: {memory['memory_id']}\n"
            if memory['type'] == 'individual_result':
                response_text += f"  Title: {memory['title']}\n"
                response_text += f"  URL: {memory['url']}\n"
        
        response_text += f"\n{result['summary']}"
        
        return [TextContent(type="text", text=response_text)]
        
    except SearchError as e:
        error_msg = f"❌ Google Search Error: {str(e)}"
        logger.error(error_msg)
        return [TextContent(type="text", text=error_msg)]
    except Exception as e:
        error_msg = f"❌ Unexpected error during Google search: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return [TextContent(type="text", text=error_msg)]


async def handle_fetch_url_and_store(params: Dict[str, Any]) -> List[TextContent]:
    """Handle fetch-url-and-store tool request"""
    try:
        result = await fetch_url_and_store(**params)
        
        response_text = "✅ URL Fetch and Storage Completed\n\n"
        response_text += f"URL: {result['url']}\n"
        response_text += f"Status: {result['status_code']} {result['status_text']}\n"
        response_text += f"Content Type: {result['content_type']}\n"
        response_text += f"Content Size: {result['content_size']} bytes\n"
        if result['content_truncated']:
            response_text += "⚠️ Content was truncated due to size limit\n"
        response_text += f"Storage scope: {result['scope']}\n"
        response_text += f"Fetch ID: {result['fetch_id']}\n\n"
        
        response_text += "Stored Memories:\n"
        for memory in result['stored_memories']:
            response_text += f"- {memory['type']}: {memory['memory_id']}\n"
        
        response_text += f"\n{result['summary']}"
        
        return [TextContent(type="text", text=response_text)]
        
    except FetchError as e:
        error_msg = f"❌ URL Fetch Error: {str(e)}"
        logger.error(error_msg)
        return [TextContent(type="text", text=error_msg)]
    except Exception as e:
        error_msg = f"❌ Unexpected error during URL fetch: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return [TextContent(type="text", text=error_msg)]
