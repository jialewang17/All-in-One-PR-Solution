#!/usr/bin/env python3
"""
FastAPI 应用主入口
一体化个人助理工具后端服务
"""

import os
import sys
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from contextlib import asynccontextmanager

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 导入路由
from api import knowledge, plan, vault, trendradar

# WebSocket 连接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    print("🚀 启动一体化个人助理工具后端服务...")
    yield
    # 关闭时清理
    print("✅ 服务已关闭")

# 创建 FastAPI 应用
app = FastAPI(
    title="一体化个人助理工具 API",
    description="整合知识查询、方案生成、笔记管理、TrendRadar 的一体化助理工具",
    version="1.0.0",
    lifespan=lifespan
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["知识查询"])
app.include_router(plan.router, prefix="/api/plan", tags=["方案生成"])
app.include_router(vault.router, prefix="/api/vault", tags=["笔记管理"])
app.include_router(trendradar.router, prefix="/api/trendradar", tags=["TrendRadar"])

@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "一体化个人助理工具 API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 端点用于实时通信"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # 处理 WebSocket 消息
            await manager.send_personal_message(f"Echo: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    # 从环境变量或配置文件读取端口
    port = int(os.getenv("API_PORT", 8000))
    host = os.getenv("API_HOST", "0.0.0.0")
    
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )

