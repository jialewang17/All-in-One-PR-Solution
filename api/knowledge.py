"""
知识查询 API 路由
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from unified_pr_system import UnifiedPRSystem

router = APIRouter()

# 全局系统实例（懒加载）
_system: Optional[UnifiedPRSystem] = None

def get_system() -> UnifiedPRSystem:
    """获取系统实例（单例模式）"""
    global _system
    if _system is None:
        _system = UnifiedPRSystem()
    return _system

class QueryRequest(BaseModel):
    query: str
    use_graph: bool = True

class QueryResponse(BaseModel):
    answer: str
    sources: List[dict] = []

class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str] = None

@router.post("/query", response_model=QueryResponse)
async def query_knowledge(request: QueryRequest):
    """知识查询接口"""
    try:
        system = get_system()
        answer = system.query_knowledge(request.query, use_graph=request.use_graph)
        
        # 提取来源信息（简化版，实际应从 RAG 系统获取）
        sources = []
        
        return QueryResponse(
            answer=answer,
            sources=sources
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")

@router.get("/history")
async def get_history():
    """获取查询历史（简化版，实际应持久化存储）"""
    return {"messages": []}

