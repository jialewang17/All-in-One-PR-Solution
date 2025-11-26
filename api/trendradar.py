"""
TrendRadar 议题追踪 API 路由
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 导入 TrendRadar 模块（将在下一步创建）
try:
    from core.trendradar.scheduler import TrendRadarScheduler
    from core.trendradar.bilibili_crawler import BilibiliCrawler
    from core.trendradar.ai_topic_filter import AITopicFilter
except ImportError:
    TrendRadarScheduler = None
    BilibiliCrawler = None
    AITopicFilter = None

router = APIRouter()

# 全局实例
_scheduler: Optional[TrendRadarScheduler] = None

def get_scheduler() -> TrendRadarScheduler:
    """获取调度器实例"""
    global _scheduler
    if _scheduler is None and TrendRadarScheduler:
        _scheduler = TrendRadarScheduler()
    return _scheduler

class BilibiliUp(BaseModel):
    uid: str
    name: str
    avatar: Optional[str] = None
    description: Optional[str] = None
    follower_count: Optional[int] = None

class AITopic(BaseModel):
    id: str
    title: str
    source: str
    source_id: str
    relevance_score: float
    hot_score: float
    publish_time: datetime
    summary: Optional[str] = None
    tags: List[str] = []

class AddUpRequest(BaseModel):
    uid: str
    name: Optional[str] = None

class ConfigRequest(BaseModel):
    keywords: List[str]
    crawl_interval: int = 3600

@router.get("/ups")
async def list_ups():
    """获取 Up主列表"""
    scheduler = get_scheduler()
    if not scheduler:
        return {"ups": []}
    
    try:
        ups = scheduler.list_ups()
        return {"ups": [BilibiliUp(**up) for up in ups]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取 Up主列表失败: {str(e)}")

@router.post("/ups", response_model=BilibiliUp)
async def add_up(request: AddUpRequest):
    """添加 Up主"""
    scheduler = get_scheduler()
    if not scheduler:
        raise HTTPException(status_code=501, detail="TrendRadar 模块未实现")
    
    try:
        up = scheduler.add_up(request.uid, request.name)
        return BilibiliUp(**up)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加 Up主失败: {str(e)}")

@router.delete("/ups/{uid}")
async def delete_up(uid: str):
    """删除 Up主"""
    scheduler = get_scheduler()
    if not scheduler:
        raise HTTPException(status_code=501, detail="TrendRadar 模块未实现")
    
    try:
        success = scheduler.remove_up(uid)
        if not success:
            raise HTTPException(status_code=404, detail="Up主未找到")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除 Up主失败: {str(e)}")

@router.get("/topics")
async def list_topics(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    filter: Optional[str] = None
):
    """获取议题列表"""
    scheduler = get_scheduler()
    if not scheduler:
        return {"topics": [], "total": 0}
    
    try:
        # 解析 filter JSON
        filter_dict = {}
        if filter:
            import json
            filter_dict = json.loads(filter)
        
        topics, total = scheduler.list_topics(page, limit, filter_dict)
        return {
            "topics": [AITopic(**topic) for topic in topics],
            "total": total,
            "page": page,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取议题列表失败: {str(e)}")

@router.get("/topics/{topic_id}")
async def get_topic(topic_id: str):
    """获取议题详情"""
    scheduler = get_scheduler()
    if not scheduler:
        raise HTTPException(status_code=404, detail="议题未找到")
    
    try:
        topic = scheduler.get_topic(topic_id)
        if not topic:
            raise HTTPException(status_code=404, detail="议题未找到")
        
        related = scheduler.get_related_topics(topic_id)
        return {
            "topic": AITopic(**topic),
            "related": [AITopic(**t) for t in related]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取议题详情失败: {str(e)}")

@router.get("/trends")
async def get_trends(period: str = Query("week", regex="^(day|week|month)$")):
    """获取趋势分析"""
    scheduler = get_scheduler()
    if not scheduler:
        return {"trends": []}
    
    try:
        trends = scheduler.get_trends(period)
        return {"trends": trends}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取趋势分析失败: {str(e)}")

@router.post("/config")
async def update_config(request: ConfigRequest):
    """更新配置"""
    scheduler = get_scheduler()
    if not scheduler:
        raise HTTPException(status_code=501, detail="TrendRadar 模块未实现")
    
    try:
        scheduler.update_config(
            keywords=request.keywords,
            crawl_interval=request.crawl_interval
        )
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")

@router.get("/report")
async def generate_report():
    """生成报告"""
    scheduler = get_scheduler()
    if not scheduler:
        raise HTTPException(status_code=501, detail="TrendRadar 模块未实现")
    
    try:
        report = scheduler.generate_report()
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成报告失败: {str(e)}")

