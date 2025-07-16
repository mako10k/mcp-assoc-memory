# OpenAI Embedding Service Testing Guide

This document explains how to test the OpenAI based embedding feature, how it coexists with the local SentenceTransformer implementation and notes on configuration for easier switching.

## 1. Verifying OpenAI embedding support

1. Install the `openai` package:
   ```bash
   pip install openai
   ```
2. Set the environment variable `OPENAI_API_KEY` with a valid API key.
3. Run a short test script to ensure embeddings can be generated:
   ```bash
   python - <<'PY'
   from mcp_assoc_memory.core.embedding_service import OpenAIEmbeddingService
   import asyncio, os
   service = OpenAIEmbeddingService(api_key=os.environ['OPENAI_API_KEY'])
   print(asyncio.run(service.get_embedding('test'))[:5])
   PY
   ```
   If the key is valid and outbound network access is allowed, a list of floating-point values should be printed. Otherwise an error will be raised.

## 2. Code review checklist

- The module `src/mcp_assoc_memory/core/embedding_service.py` defines `OpenAIEmbeddingService` and `SentenceTransformerEmbeddingService`.
- The helper `create_embedding_service()` uses the configuration section `embedding.provider` to decide which implementation to instantiate.
- Ensure the server initialisation uses this factory so that configuration can toggle providers. At the moment `server.py` directly instantiates `SentenceTransformerEmbeddingService`, ignoring the provider setting.
- Logging of errors from the OpenAI API should be clear and include the error code for troubleshooting.

## 3. Switching between OpenAI and local embeddings

The active provider can be selected in `config.json` or via environment variables:

```json
{
  "embedding": {
    "provider": "openai",             // or "sentence_transformer" or "mock"
    "api_key": "<your key>",
    "model": "text-embedding-3-small"
  }
}
```

Environment variables override the configuration file. For example:

```bash
export EMBEDDING_PROVIDER=sentence_transformer
export SENTENCE_TRANSFORMER_MODEL=all-MiniLM-L6-v2
```

When running the server, confirm the logs mention which service has been selected.

## 4. Configuration improvements

- Use `create_embedding_service()` in `server.py` to respect the `embedding.provider` option.
- Document all embedding related environment variables in `.env.example` for clarity.
- Consider adding a CLI flag `--embedding-provider` to make switching easier during testing.

Keeping these points in mind will make it simpler to validate OpenAI functionality and seamlessly switch between remote and local embeddings.
