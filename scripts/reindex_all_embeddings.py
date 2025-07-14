import asyncio

from mcp_assoc_memory.config import Config
from mcp_assoc_memory.core.embedding_service import create_embedding_service
from mcp_assoc_memory.storage.metadata_store import SQLiteMetadataStore
from mcp_assoc_memory.storage.vector_store import ChromaVectorStore


async def reindex_all_embeddings():
    config = Config.load()
    metadata_store = SQLiteMetadataStore(config.database.path)
    vector_store = ChromaVectorStore(persist_directory=config.storage.data_dir + "/chroma_db")
    embedding_service = create_embedding_service(config.embedding.__dict__)

    print("全記憶のembedding再計算・ベクトルストア再投入を開始します...")
    memories = await metadata_store.get_memories_by_scope(None)
    print(f"対象件数: {len(memories)}")
    updated = 0
    for mem in memories:
        embedding = await embedding_service.get_embedding(mem.content)
        if embedding is not None:
            await vector_store.store_embedding(mem.id, embedding, mem.to_dict())
            updated += 1
            print(f"[OK] {mem.id} : embedding再保存")
        else:
            print(f"[NG] {mem.id} : embedding生成失敗")
    print(f"完了: {updated}/{len(memories)} 件 embedding再投入")


if __name__ == "__main__":
    asyncio.run(reindex_all_embeddings())
