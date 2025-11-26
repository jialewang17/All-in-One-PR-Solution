"""
笔记管理 API 路由（sanhu_vault 双向同步）
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 导入 vault 模块（将在下一步创建）
try:
    from core.knowledge.vault_sync import VaultSyncManager
    from core.knowledge.vault_writer import VaultWriter
except ImportError:
    # 如果模块不存在，使用占位实现
    VaultSyncManager = None
    VaultWriter = None

router = APIRouter()

# 全局实例
_sync_manager: Optional[VaultSyncManager] = None
_writer: Optional[VaultWriter] = None

def get_sync_manager() -> VaultSyncManager:
    """获取同步管理器实例"""
    global _sync_manager
    if _sync_manager is None and VaultSyncManager:
        _sync_manager = VaultSyncManager()
    return _sync_manager

def get_writer() -> VaultWriter:
    """获取写入器实例"""
    global _writer
    if _writer is None and VaultWriter:
        _writer = VaultWriter()
    return _writer

class VaultNote(BaseModel):
    id: str
    title: str
    path: str
    content: Optional[str] = None
    tags: List[str] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    word_count: Optional[int] = None
    links: List[str] = []

class CreateNoteRequest(BaseModel):
    title: str
    content: str
    path: str
    tags: Optional[List[str]] = []

class UpdateNoteRequest(BaseModel):
    content: str

class SyncStatus(BaseModel):
    syncing: bool
    last_sync: Optional[datetime] = None
    file_count: int = 0

@router.get("/status", response_model=SyncStatus)
async def get_sync_status():
    """获取同步状态"""
    manager = get_sync_manager()
    if not manager:
        return SyncStatus(syncing=False, file_count=0)
    
    try:
        status = manager.get_status()
        return SyncStatus(**status)
    except Exception as e:
        return SyncStatus(syncing=False, file_count=0)

@router.post("/sync")
async def trigger_sync():
    """手动触发全量同步"""
    manager = get_sync_manager()
    if not manager:
        raise HTTPException(status_code=501, detail="Vault 同步模块未实现")
    
    try:
        result = await manager.full_sync()
        return {"success": True, "message": "同步完成", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")

@router.get("/files")
async def list_files():
    """列出所有已索引文件"""
    manager = get_sync_manager()
    if not manager:
        return {"files": []}
    
    try:
        files = manager.list_files()
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件列表失败: {str(e)}")

@router.get("/notes/{note_id}", response_model=VaultNote)
async def get_note(note_id: str):
    """获取笔记内容"""
    manager = get_sync_manager()
    if not manager:
        raise HTTPException(status_code=404, detail="笔记未找到")
    
    try:
        note = manager.get_note(note_id)
        if not note:
            raise HTTPException(status_code=404, detail="笔记未找到")
        return VaultNote(**note)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取笔记失败: {str(e)}")

@router.post("/notes", response_model=VaultNote)
async def create_note(request: CreateNoteRequest):
    """创建新笔记"""
    writer = get_writer()
    if not writer:
        raise HTTPException(status_code=501, detail="Vault 写入模块未实现")
    
    try:
        note = writer.create_note(
            title=request.title,
            content=request.content,
            path=request.path,
            tags=request.tags or []
        )
        return VaultNote(**note)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建笔记失败: {str(e)}")

@router.put("/notes/{note_id}", response_model=VaultNote)
async def update_note(note_id: str, request: UpdateNoteRequest):
    """更新笔记"""
    writer = get_writer()
    if not writer:
        raise HTTPException(status_code=501, detail="Vault 写入模块未实现")
    
    try:
        note = writer.update_note(note_id, request.content)
        if not note:
            raise HTTPException(status_code=404, detail="笔记未找到")
        return VaultNote(**note)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新笔记失败: {str(e)}")

@router.delete("/notes/{note_id}")
async def delete_note(note_id: str):
    """删除笔记"""
    writer = get_writer()
    if not writer:
        raise HTTPException(status_code=501, detail="Vault 写入模块未实现")
    
    try:
        success = writer.delete_note(note_id)
        if not success:
            raise HTTPException(status_code=404, detail="笔记未找到")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除笔记失败: {str(e)}")

@router.get("/search")
async def search_notes(q: str):
    """搜索笔记"""
    manager = get_sync_manager()
    if not manager:
        return {"results": []}
    
    try:
        results = manager.search(q)
        return {"results": [VaultNote(**r) for r in results]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

