import os
import sys
import json
import asyncio
from typing import Dict, Any
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
import uvicorn
from contextlib import asynccontextmanager
import subprocess
import threading
import queue
import select

# 導入您的 MCP 服務器
from src.main import RedisMCPServer
from src.common.config import set_redis_config_from_cli

class MCPHTTPWrapper:
    def __init__(self):
        self.app = FastAPI(title="Redis MCP Server", version="0.2.0")
        self.setup_routes()
        self.setup_redis_config()
        
    def setup_redis_config(self):
        """從環境變量設置 Redis 配置"""
        config = {}
        
        # 從環境變量讀取 Redis 配置
        if os.getenv('REDIS_HOST'):
            config['host'] = os.getenv('REDIS_HOST')
        if os.getenv('REDIS_PORT'):
            config['port'] = int(os.getenv('REDIS_PORT'))
        if os.getenv('REDIS_DB'):
            config['db'] = int(os.getenv('REDIS_DB', '0'))
        if os.getenv('REDIS_USERNAME'):
            config['username'] = os.getenv('REDIS_USERNAME')
        if os.getenv('REDIS_PASSWORD') or os.getenv('REDIS_PWD'):
            config['password'] = os.getenv('REDIS_PASSWORD') or os.getenv('REDIS_PWD')
        if os.getenv('REDIS_SSL'):
            config['ssl'] = os.getenv('REDIS_SSL').lower() == 'true'
            
        # 如果有 Redis URL，使用它
        if os.getenv('REDIS_URL'):
            from src.common.config import parse_redis_uri
            try:
                config = parse_redis_uri(os.getenv('REDIS_URL'))
            except Exception as e:
                print(f"Error parsing Redis URL: {e}", file=sys.stderr)
        
        if config:
            set_redis_config_from_cli(config)
            print(f"Redis config set: {config}", file=sys.stderr)
    
    def setup_routes(self):
        @self.app.get("/")
        async def root():
            return {"message": "Redis MCP Server is running", "version": "0.2.0"}
        
        @self.app.get("/health")
        async def health():
            return {"status": "healthy", "service": "redis-mcp-server"}
        
        @self.app.post("/mcp")
        async def mcp_endpoint(request: Request):
            """處理 MCP 協議請求"""
            try:
                # 獲取請求體
                body = await request.body()
                
                # 創建 MCP 服務器進程
                process = subprocess.Popen(
                    [sys.executable, "-c", """
import sys
import os
sys.path.insert(0, '/app')
from src.main import main
main()
"""],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd='/app'
                )
                
                # 發送請求到 MCP 服務器
                stdout, stderr = process.communicate(input=body.decode())
                
                if process.returncode != 0:
                    print(f"MCP process error: {stderr}", file=sys.stderr)
                    raise HTTPException(status_code=500, detail="MCP server error")
                
                # 返回響應
                return JSONResponse(content=json.loads(stdout) if stdout.strip() else {})
                
            except json.JSONDecodeError:
                # 如果不是 JSON，返回純文本
                return {"response": stdout}
            except Exception as e:
                print(f"MCP endpoint error: {e}", file=sys.stderr)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/mcp")
        async def mcp_get():
            """GET 請求返回 MCP 服務器信息"""
            return {
                "name": "redis-mcp-server",
                "version": "0.2.0",
                "protocol": "mcp",
                "capabilities": [
                    "redis_operations",
                    "key_management",
                    "data_structures",
                    "pub_sub",
                    "streams"
                ]
            }

def main():
    # 設置環境變量
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8080))
    
    print(f"Starting HTTP server on {host}:{port}", file=sys.stderr)
    
    # 創建包裝器
    wrapper = MCPHTTPWrapper()
    
    # 運行服務器
    uvicorn.run(
        wrapper.app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main()
