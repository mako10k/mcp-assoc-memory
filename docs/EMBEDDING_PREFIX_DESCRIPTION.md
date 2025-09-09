# Prefix-Based Description from Embeddings

This note describes a simple technique for generating a short text continuation that begins with a fixed prefix and summarizes the content represented by an embedding vector.  It does **not** require any special training – we combine vector search with a language model to guess the next few words.

## Prerequisites

- Python 3.10+
- Installed packages:
    - mcp-assoc-memory (this repository)
    - chromadb
    - An embedding backend and credentials if needed (e.g., OpenAI)

Install minimal dependencies:

```bash
pip install -r requirements.txt
```

Note: If you use OpenAI for embeddings, set the environment variable `OPENAI_API_KEY` or pass it explicitly in the config shown below.

## Concept

1. **Create embeddings** for a set of reference snippets (e.g., short descriptions of known file types or documents).
2. **Store each embedding** along with the text you want to output when that embedding is matched.  A lightweight vector store such as ChromaDB works well.
3. **At query time**, compute the embedding for the target content and look up the most similar reference entry.
4. **Append the matched text** to your prefix.  Optionally send the combined string to an LLM to rephrase or extend it.

This effectively produces the continuation _prefix + description_.  For example:

```
Prefix: "このファイルの種類は"
Vector: (embedding of an XML file)
→ Matched reference text: "XMLです"
→ Result: "このファイルの種類は XMLです"
```

## Minimal Example (Async)

```python
import asyncio
from mcp_assoc_memory.core.embedding_service import create_embedding_service
from mcp_assoc_memory.core.singleton_memory_manager import SingletonMemoryManager


async def main() -> None:
    # Initialize services
    embedding_service = create_embedding_service({
        "embedding": {"service": "openai", "api_key": "YOUR_OPENAI_KEY"}
    })
    manager = SingletonMemoryManager.create(embedding_service=embedding_service)

    # 1. Store reference embeddings with labels
    xml_text = "XMLです"
    xml_vec = await embedding_service.get_embedding("<sample xml></sample>")
    await manager.vector_store.upsert("xml_label", xml_vec, metadata={"label": xml_text})

    # 2. Query with new content
    file_content = "<?xml version='1.0'?><root/>"
    file_vec = await embedding_service.get_embedding(file_content)
    results = await manager.vector_store.query(file_vec, top_k=1)
    label = results[0].metadata["label"]

    prefix = "このファイルの種類は"
    result = f"{prefix} {label}"
    print(result)  # => "このファイルの種類は XMLです"


if __name__ == "__main__":
    asyncio.run(main())
```

You can optionally pass `result` to an LLM if you want a longer or more natural explanation.  This workflow keeps the prefix fixed and uses embeddings purely for retrieval of the appropriate continuation text.
