# MCP Associative Memory Server - AI Development Agent Documentation

## Project Overview

This project is an associative memory MCP server for LLMs. It provides a knowledge management system that considers memory domains (Global/User/Project/Session) and supports three transport methods: STDIO, HTTP, and SSE.

## Information for AI Development Agents

### Development Guidelines

When developing this project, please follow these guidelines:

📋 **[GitHub Copilot Development Rules](../../.github/copilot-instructions.md)**
- TypeScript conventions
- Architecture guidelines
- Testing strategy
- Security considerations
- Performance optimization
- MCP specification compliance

### Project Structure

For detailed project structure, refer to the following documents:

- **[Project Structure](../architecture/PROJECT_STRUCTURE.md)** - Directory structure and file organization
- **[Specifications](../specifications/SPECIFICATION.md)** - API specifications and feature details
- **[Architecture](../architecture/ARCHITECTURE.md)** - System design and components
- **[Memory Domains](../specifications/MEMORY_DOMAINS.md)** - Domain design and management strategy

### Technology Stack

- **Core Technology**: TypeScript, Node.js
- **Database**: SQLite (development), PostgreSQL (production)
- **Protocol**: Model Context Protocol (MCP)
- **Transport**: STDIO, HTTP, SSE
- **Testing**: Jest
- **Development Tools**: ESLint, Prettier, TypeScript

### Main Components

1. **Transport Layer** - Communication layer supporting STDIO/HTTP/SSE
2. **Core Engine** - Core functionality for associative memory
3. **Storage Layer** - Data persistence and query processing
4. **Domain Manager** - Memory domain management
5. **Auth Layer** - Authentication and authorization processing

### Memory Domains

| Domain | Description | Use Cases |
|---------|-------------|-----------|
| Global | System-wide memory | General knowledge, constant information |
| User | User-specific memory | Personal settings, learning data |
| Project | Project-specific memory | Project information, code context |
| Session | Session-specific memory | Temporary conversation state |

### API Design Patterns

```typescript
// Integrated tool design using subcommand approach
interface MemoryTool {
  action: 'store' | 'search' | 'get' | 'get_related' | 'update' | 'delete';
  memory_id?: string;
  content?: string;
  query?: string;
  domain?: MemoryDomain;
  // ...other parameters
}

interface UserTool {
  action: 'get_current' | 'get_projects' | 'get_sessions' | 'create_session' | 'switch_session' | 'end_session';
  session_name?: string;
  session_id?: string;
  include_stats?: boolean;
}

// Provide all functionality with 7 main tools
const tools = [
  'memory',          // Basic memory operations
  'memory_manage',   // Memory management and statistics
  'search',          // Advanced search
  'project',         // Project management
  'user',           // User and session management
  'visualize',      // Visualization and analysis
  'admin'           // System administration
];
```

### Development Considerations

1. **Type Safety**
   - Proper type annotations for all functions and classes
   - Use strict TypeScript configuration

2. **Error Handling**
   - Use custom error classes
   - Return appropriate error responses

3. **Test-Driven Development**
   - Create test cases before feature implementation
   - Implement unit, integration, and E2E tests

4. **Performance Considerations**
   - Optimize database indexes
   - Implement caching strategies

5. **Security**
   - Thorough input validation
   - Proper implementation of authentication and authorization

### Development Flow

1. **Requirements Review** - Review specifications and architecture documents
2. **Design** - Interface design and type definitions
3. **Implementation** - Development following TDD principles
4. **Testing** - Execute various tests and quality checks
5. **Review** - Code review and quality verification

### Debugging and Troubleshooting

- **Log Configuration**: Use structured logging
- **Health Checks**: Monitor system status
- **Performance Monitoring**: Metrics collection and analysis

### Related Materials

**📝 Note**: Implementation plans and development checklists have been moved to the associative memory system. Use memory search to find current development status and tasks.

- **[Technical Considerations](../technical/TECHNICAL_CONSIDERATIONS.md)** - Technical considerations
- **[Transport Configuration](../configuration/TRANSPORT_CONFIG.md)** - Configuration for various startup methods
- **[Authentication Strategy](../security/AUTHENTICATION_STRATEGY.md)** - Authentication system design

### Support

For questions or issues during development, please refer to:

1. Existing documentation (links above)
2. GitHub Copilot development rules
3. MCP specifications
4. TypeScript official documentation

---

**Important**: This project is under active development. When adding new features or modifying existing ones, be sure to update related documentation as well.
