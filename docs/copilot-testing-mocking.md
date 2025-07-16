# Copilot Testing and Mocking Guidelines

## Principles
- Mock at the correct layer: external dependencies only
- Keep business logic fully testable
- Never mock too high-level to avoid losing test coverage

## Proper Mocking Layers

### ✅ Correct Mocking (Low-Level Dependencies)
```python
class OpenAIEmbeddingService:
    async def _get_client(self):
        if is_test_mode:
            return MockOpenAIClient()  # Mock external API only
        else:
            return openai.AsyncOpenAI(api_key=self.api_key)
    
    def __init__(self, api_key: str):
        # This validation logic IS tested
        if not api_key.startswith('sk-'):
            raise ValueError("Invalid API key")
```

**What gets tested:**
- ✅ Configuration validation
- ✅ Error handling logic
- ✅ Service selection logic
- ✅ Business rules

**What gets mocked:**
- ❌ External API calls only

### ❌ Incorrect Mocking (High-Level Services)
```python
def create_embedding_service():
    if is_test_mode:
        return MockEmbeddingService()  # WRONG - too high level
    else:
        return OpenAIEmbeddingService()
```

**Problems:**
- ❌ Configuration validation NOT tested
- ❌ Error handling NOT tested  
- ❌ Service selection logic NOT tested
- ❌ No coverage of actual implementation

## Implementation Guidelines

### 1. Identify External Dependencies
Mock these:
- API calls (`openai.AsyncOpenAI`)
- File system operations
- Network requests
- Database connections
- System calls

### 2. Keep Internal Logic Testable
Test these:
- Configuration parsing and validation
- Error handling and propagation
- Business logic and rules
- Service selection algorithms
- Data transformation

### 3. Test Mode Detection Pattern
```python
# Correct: At dependency injection level
async def _get_external_dependency(self):
    if is_test_mode():
        return MockExternalService()
    return RealExternalService()

# Wrong: At service creation level
def create_service():
    if is_test_mode():
        return MockService()  # Defeats testing purpose
    return RealService()
```

## Example: Embedding Service Architecture

### Current Correct Implementation
```python
OpenAIEmbeddingService.__init__():
    # ✅ Validation logic tested
    if not api_key.startswith('sk-'):
        raise ValueError()

OpenAIEmbeddingService._get_client():
    # ✅ Mock only external API
    if test_mode:
        return MockOpenAIClient()
    return openai.AsyncOpenAI()
```

### Previous Incorrect Implementation
```python
create_embedding_service():
    # ❌ High-level mock prevents testing
    if test_mode:
        return MockEmbeddingService()
    return OpenAIEmbeddingService()
```

## Benefits of Correct Mocking

1. **Full Test Coverage**: Business logic gets tested
2. **Real Validation**: Configuration and error handling verified
3. **Isolated External Deps**: Network/API failures don't break tests
4. **Maintainable**: Changes to business logic are caught by tests

## Common Mistakes

### Mistake 1: Service-Level Mocking
- **Problem**: `create_service() → MockService` 
- **Solution**: `service._get_dependency() → MockDependency`

### Mistake 2: Test Mode in Factory
- **Problem**: Factory returns different classes based on test mode
- **Solution**: Same class, different dependencies

### Mistake 3: Over-Mocking
- **Problem**: Mocking internal methods and business logic
- **Solution**: Mock only external I/O and network calls

## Related Guidelines
- For error handling: see [copilot-error-handling.md](copilot-error-handling.md)
- For decision making: see [copilot-decision.md](copilot-decision.md)
- For SDK usage: see [copilot-sdk.md](copilot-sdk.md)
