# Sample Memory Data

This directory contains sample memory exports that demonstrate the MCP Associative Memory Server functionality.

## Files

### `sample-memories.json`

A compressed JSON export containing 28 curated memories that showcase various features of the associative memory system:

**Content Categories:**
- **Technical Knowledge** (4 memories): Programming languages, AI/ML concepts, cooking science, learning theory
- **Development Records** (24 memories): Project implementation details, design decisions, configuration updates, internationalization work, bug fixes, and feature implementations

**Key Features Demonstrated:**
- ✅ **Scope Organization**: Hierarchical memory organization (`tech/`, `work/`, `lifestyle/`, `philosophy/`)
- ✅ **Metadata Support**: Rich metadata including tags, categories, timestamps
- ✅ **Search Optimization**: Examples of search strategy improvements and threshold tuning
- ✅ **CRUD Operations**: Memory creation, updates, and management workflows
- ✅ **File Synchronization**: Export/import functionality for cross-environment portability
- ✅ **Internationalization**: English-only content for international accessibility

**Technical Details:**
- **Format Version**: 1.0
- **Compression**: gzip (base64-encoded)
- **Memory Count**: 28 memories
- **File Size**: ~17KB (compressed), ~43KB (uncompressed)
- **Export Date**: 2025-07-10

## Usage

### Import Sample Data

```bash
# Using MCP tools (recommended)
# Use memory_import tool with file_path="examples/sample-data/sample-memories.json"

# Or via direct server interaction
curl -X POST http://localhost:8000/mcp/tools/memory_import \
  -H "Content-Type: application/json" \
  -d '{
    "request": {
      "file_path": "examples/sample-data/sample-memories.json",
      "merge_strategy": "skip_duplicates"
    }
  }'
```

### Explore Sample Content

Once imported, you can explore the sample memories:

```bash
# Browse memory organization
# Use memory_search with query="Python programming"
# Use scope_list to see hierarchical organization
# Use memory_discover_associations to explore connections
```

## Content Safety

This sample data contains only:
- ✅ **Public technical knowledge** (programming concepts, best practices)
- ✅ **Development insights** (architecture decisions, implementation patterns)
- ✅ **Configuration examples** (similarity thresholds, model settings)
- ✅ **Workflow documentation** (development processes, testing strategies)

**No sensitive information:**
- ❌ No personal data or credentials
- ❌ No API keys or secrets
- ❌ No private business information
- ❌ No user-specific content

## Educational Value

This sample dataset is ideal for:
- **Learning** the associative memory system capabilities
- **Testing** search and association features
- **Demonstrating** real-world usage patterns
- **Prototyping** new features or integrations
- **Training** on scope organization best practices

## Contributing

If you want to contribute additional sample memories:
1. Ensure content is publicly shareable
2. Follow scope organization patterns
3. Include appropriate metadata and tags
4. Test export/import functionality
5. Update this README with new content descriptions
