# MCP Response Architecture Specification

## Overview
This document defines the standardized response architecture for MCP Associative Memory Server tools.

## Architecture Principles

### 1. Unified Response Generation
- **MCPResponseBase**: Abstract base class with unified response generation method
- **Derived Classes**: Tool-specific response classes inheriting from MCPResponseBase
- **Unified Tool Layer**: Common response generation layer that calls abstract methods consistently
- **No Individual Adjustments**: Individual tool output adjustments are prohibited

### 2. Response Class Hierarchy
```
MCPResponseBase (Abstract)
├── MemoryStoreResponse
├── MemorySearchResponse
├── MemoryGetResponse
├── MemoryUpdateResponse
├── MemoryDeleteResponse
├── MemoryMoveResponse
└── ... (other tool responses)
```

### 3. Implementation Requirements

#### MCPResponseBase (Abstract Base Class)
- Contains abstract method for unified response generation
- Method signature: `to_response_dict(self, level: str = "minimal", **kwargs) -> Dict[str, Any]`
- Supported levels: `"minimal"`, `"standard"`, `"full"`

#### Derived Classes
- Must contain ALL attributes needed for maximum response
- Must implement the abstract `to_response_dict` method
- Implementation handles different output levels based on `level` parameter

#### Unified Tool Response Layer
- Common layer that calls `to_response_dict()` consistently
- No individual tool-specific output adjustments
- Uniform response generation across all tools

## Response Levels

### Minimal (`level="minimal"`)
- Essential fields only: `success`, `memory_id`, `created_at`
- Used as default for optimal token usage
- Excludes input parameter echoing unless modified by system

### Standard (`level="standard"`)
- Includes message and basic metadata
- Moderate verbosity for debugging

### Full (`level="full"`)
- Complete response with all available data
- Used for detailed debugging or rich client interfaces

## Implementation Rules

1. **No Direct Tool Adjustments**: Individual tools must NOT adjust their own output
2. **Unified Generation**: All responses generated through `to_response_dict()` method
3. **Consistent Interface**: Same method signature across all derived classes
4. **Level-Based Output**: Output content controlled solely by `level` parameter
5. **Future-Proof**: Architecture supports adding new response levels without breaking changes

## Migration Guidelines

1. Update `MCPResponseBase` to abstract class with `to_response_dict()` method
2. Refactor all derived classes to implement the abstract method
3. Remove existing `to_minimal_dict()` and `to_lightweight_dict()` methods
4. Update tool layer to use unified response generation
5. Test all tools with different response levels

## Benefits

- **Consistency**: Uniform response format across all tools
- **Maintainability**: Single point of response logic per tool type
- **Flexibility**: Easy to add new response levels
- **Performance**: Optimized token usage with minimal responses
- **Debugging**: Rich responses available when needed

---

**Status**: Draft - Ready for implementation
**Last Updated**: 2025-07-14
**Author**: GitHub Copilot (per user requirements)
