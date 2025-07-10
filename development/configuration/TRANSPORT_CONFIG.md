# マルチトランスポート設定例

## development.json（開発環境）

```json
{
  "transports": {
    "stdio": {
      "enabled": true
    },
    "http": {
      "enabled": true,
      "host": "localhost",
      "port": 8000,
      "auth_type": "none",
      "cors": {
        "allowed_origins": ["http://localhost:3000", "http://localhost:5173"],
        "allowed_methods": ["GET", "POST", "OPTIONS"]
      }
    },
    "sse": {
      "enabled": true,
      "host": "localhost", 
      "port": 8001,
      "max_connections": 10,
      "heartbeat_interval": 30
    }
  },
  "embedding": {
    "provider": "sentence_transformers",
    "model": "all-MiniLM-L6-v2",
    "batch_size": 50
  },
  "storage": {
    "vector_db": {
      "type": "chroma",
      "persist_directory": "./data/dev/chroma"
    },
    "metadata_db": {
      "type": "sqlite",
      "path": "./data/dev/metadata.db"
    },
    "graph_store": {
      "type": "networkx",
      "persist_path": "./data/dev/graph.pkl"
    }
  },
  "memory": {
    "default_importance": 0.5,
    "similarity_threshold": 0.6,
    "max_associations_per_memory": 5,
    "auto_association_threshold": 0.7
  },
  "log_level": "DEBUG"
}
```

## production.json（本番環境）

```json
{
  "transports": {
    "stdio": {
      "enabled": false
    },
    "http": {
      "enabled": true,
      "host": "0.0.0.0",
      "port": 8000,
      "auth_type": "jwt",
      "cors": {
        "allowed_origins": [
          "https://yourdomain.com",
          "https://app.yourdomain.com"
        ],
        "allowed_methods": ["GET", "POST"]
      }
    },
    "sse": {
      "enabled": true,
      "host": "0.0.0.0",
      "port": 8001,
      "max_connections": 1000,
      "heartbeat_interval": 60
    }
  },
  "embedding": {
    "provider": "openai",
    "model": "text-embedding-3-small",
    "api_key": "${OPENAI_API_KEY}",
    "batch_size": 100
  },
  "storage": {
    "vector_db": {
      "type": "chroma",
      "persist_directory": "/app/data/chroma"
    },
    "metadata_db": {
      "type": "sqlite",
      "path": "/app/data/metadata.db"
    },
    "graph_store": {
      "type": "networkx",
      "persist_path": "/app/data/graph.pkl"
    }
  },
  "memory": {
    "default_importance": 0.5,
    "similarity_threshold": 0.7,
    "max_associations_per_memory": 10,
    "auto_association_threshold": 0.8
  },
  "log_level": "INFO"
}
```

## docker-compose.yml（マルチトランスポート対応）

```yaml
version: '3.8'

services:
  mcp-assoc-memory:
    build: .
    ports:
      - "8000:8000"  # HTTP
      - "8001:8001"  # SSE
    environment:
      - TRANSPORT=http,sse
      - ENVIRONMENT=production
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - JWT_SECRET=${JWT_SECRET}
    volumes:
      - ./data:/app/data
      - ./config:/app/config
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # STDIO専用サービス（デスクトップアプリ用）
  mcp-assoc-memory-stdio:
    build: .
    environment:
      - TRANSPORT=stdio
      - ENVIRONMENT=development
    volumes:
      - ./data:/app/data
      - ./config:/app/config
    profiles:
      - stdio
    restart: "no"
```

## 使用例

### 1. 開発時（すべての通信方式）
```bash
# すべてのトランスポートで起動
python -m mcp_assoc_memory.main --transport all

# 特定のポートで起動
python -m mcp_assoc_memory.main --transport http,sse --http-port 8080 --sse-port 8081
```

### 2. Claude Desktop用（STDIO）
```bash
# STDIOのみで起動
python -m mcp_assoc_memory.main --transport stdio
```

### 3. Webアプリ用（HTTP）
```bash
# HTTPのみで起動
python -m mcp_assoc_memory.main --transport http --http-port 8000
```

### 4. リアルタイムWebアプリ用（SSE）
```bash
# SSEのみで起動
python -m mcp_assoc_memory.main --transport sse --sse-port 8001
```

### 5. Docker起動例
```bash
# HTTP + SSE
docker run -p 8000:8000 -p 8001:8001 -e TRANSPORT=http,sse mcp-assoc-memory

# STDIO（インタラクティブ）
docker run -it mcp-assoc-memory --transport stdio
```

## クライアント実装例

### HTTP クライアント
```python
import httpx
import json

class MCPHTTPClient:
    def __init__(self, base_url: str, api_key: str = None):
        self.base_url = base_url
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["X-API-Key"] = api_key
    
    async def store_memory(self, content: str, domain: str = "user", **kwargs):
        request = {
            "jsonrpc": "2.0",
            "method": "tools/store_memory_with_domain",
            "params": {"content": content, "domain": domain, **kwargs},
            "id": 1
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/mcp",
                json=request,
                headers=self.headers
            )
            return response.json()
```

### SSE クライアント
```javascript
class MCPSSEClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
        this.ws = null;
    }
    
    connect() {
        this.ws = new WebSocket(`${this.baseUrl}/sse`);
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'heartbeat') {
                console.log('Heartbeat received');
            } else {
                this.handleResponse(data);
            }
        };
    }
    
    async storeMemory(content, domain = 'user', options = {}) {
        const request = {
            jsonrpc: "2.0",
            method: "tools/store_memory_with_domain",
            params: { content, domain, ...options },
            id: Date.now()
        };
        
        this.ws.send(JSON.stringify(request));
    }
}
```
