# Contributing to MCP Associative Memory Server

Thank you for your interest in contributing to the MCP Associative Memory Server! This document provides guidelines and instructions for contributing to the project.

## 🚀 Quick Start

1. **Fork** the repository on GitHub
2. **Clone** your fork locally
3. **Create** a new branch for your feature/fix
4. **Make** your changes following our guidelines
5. **Test** your changes thoroughly
6. **Submit** a pull request

## 📋 Development Setup

### Prerequisites
- Python 3.10 or higher
- Git
- Virtual environment tool (venv/conda)

### Installation
```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/mcp-assoc-memory.git
cd mcp-assoc-memory

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install in development mode
pip install -e .
```

### Development Tools
```bash
# Run linting
python scripts/smart_lint.py

# Run tests
pytest tests/ -v

# Run with coverage
pytest --cov=src --cov-report=html

# Start MCP server
./scripts/mcp_server_daemon.sh start
```

## 🎯 Contribution Areas

### High Priority
- **Performance Optimization**: Query response time improvements
- **Enhanced Error Handling**: Better user feedback for edge cases
- **Documentation**: Examples, tutorials, integration guides

### Medium Priority
- **Search UX**: Scope suggestions, search statistics
- **Testing**: Integration and end-to-end test coverage
- **Tool Extensions**: New MCP tool implementations

### Always Welcome
- **Bug Fixes**: Any bug reports or fixes
- **Documentation**: Improvements to clarity and completeness
- **Examples**: Usage examples and integration patterns

## 📝 Code Guidelines

### Python Style
- **PEP 8 Compliance**: Follow Python style guidelines
- **Type Hints**: All functions must have type annotations
- **Docstrings**: Use Google-style docstrings
- **Line Length**: Maximum 120 characters

### MCP Tool Development
- **Mode-based Dispatch**: Use `mode` parameter for operation branching
- **Response Consistency**: Follow MCP JSON-RPC response format
- **Error Handling**: Use shared `errorResponse()` helper
- **Response Levels**: Support minimal/standard/full response levels

### Testing Requirements
- **Unit Tests**: All new functions must have unit tests
- **Integration Tests**: MCP tool functionality tests
- **Type Safety**: Pass mypy type checking
- **Coverage**: Maintain or improve test coverage

## 🔧 Development Workflow

### Branch Naming
- `feature/description` - New features
- `fix/description` - Bug fixes  
- `docs/description` - Documentation updates
- `refactor/description` - Code improvements

### Commit Messages
```
type(scope): brief description

Detailed explanation of changes (if needed)

- Bullet points for multiple changes
- Reference issues: Fixes #123
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

### Pull Request Process

1. **Pre-submission Checklist**:
   - [ ] All tests pass (`pytest tests/`)
   - [ ] Type checking passes (`mypy src/`)
   - [ ] Linting passes (`python scripts/smart_lint.py`)
   - [ ] Documentation updated (if applicable)
   - [ ] CHANGELOG.md updated (for user-facing changes)

2. **PR Description Template**:
   ```markdown
   ## Summary
   Brief description of changes

   ## Changes
   - List of specific changes
   - Impact on existing functionality
   - New features added

   ## Testing
   - Tests added/modified
   - Manual testing performed
   - Performance impact (if any)

   ## Documentation
   - Documentation updates
   - Examples added/updated
   ```

3. **Review Process**:
   - Automated CI checks must pass
   - Code review by maintainers
   - Address feedback and iterate
   - Final approval and merge

## 🧪 Testing Guidelines

### Test Structure
```
tests/
├── unit/                 # Unit tests
├── integration/          # Integration tests
├── api/                  # MCP tool tests
├── e2e/                  # End-to-end tests
└── conftest.py          # Test configuration
```

### Writing Tests
```python
# Unit test example
def test_response_builder_minimal():
    builder = ResponseBuilder(level="minimal")
    result = builder.build_response(data={"key": "value"})
    assert result["success"] is True
    assert "key" in result

# Integration test example
@pytest.mark.integration
async def test_memory_store_integration():
    response = await memory_store_handler({
        "content": "test content",
        "response_level": "standard"
    })
    assert response["success"] is True
```

### Running Tests
```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# Specific test file
pytest tests/api/tools/test_memory_store.py -v

# With coverage
pytest --cov=src tests/
```

## 🐛 Bug Reports

### Before Reporting
1. **Search existing issues** for similar problems
2. **Test with latest version** if possible
3. **Gather debug information** (logs, error messages)

### Bug Report Template
```markdown
## Bug Description
Clear description of the issue

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: [e.g., Ubuntu 22.04]
- Python: [e.g., 3.10.12]
- MCP Server Version: [e.g., 1.1.0]

## Additional Context
- Log files
- Error messages
- Screenshots (if applicable)
```

## 💡 Feature Requests

### Feature Request Template
```markdown
## Feature Description
Clear description of the proposed feature

## Use Case
Why is this feature needed?
What problem does it solve?

## Proposed Solution
How should this feature work?
Any specific implementation ideas?

## Alternatives Considered
Other approaches you've thought about

## Additional Context
Any other relevant information
```

## 📚 Documentation

### Documentation Types
- **API Reference**: Tool parameters and responses
- **User Guides**: How-to guides and tutorials
- **Developer Docs**: Architecture and implementation details
- **Examples**: Code samples and integration patterns

### Writing Guidelines
- **Clear and Concise**: Easy to understand language
- **Code Examples**: Practical, working examples
- **Cross-references**: Link to related documentation
- **Keep Updated**: Update docs with code changes

## 🏆 Recognition

Contributors are recognized in:
- **README.md**: Contributors section
- **CHANGELOG.md**: Feature acknowledgments
- **GitHub**: Contributor metrics and recognition

## 📞 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and ideas
- **Documentation**: Check existing docs first
- **Code Review**: Learn from PR feedback

## 📜 Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold this code.

## 📄 License

By contributing, you agree that your contributions will be licensed under the same [MIT License](LICENSE) that covers the project.

---

Thank you for contributing to the MCP Associative Memory Server! Your help makes this project better for everyone. 🙏
