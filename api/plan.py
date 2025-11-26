"""
方案生成 API 路由
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from unified_pr_system import UnifiedPRSystem

router = APIRouter()

# 全局系统实例
_system: Optional[UnifiedPRSystem] = None

def get_system() -> UnifiedPRSystem:
    """获取系统实例"""
    global _system
    if _system is None:
        _system = UnifiedPRSystem()
    return _system

class EnterpriseInfo(BaseModel):
    enterprise_name: str
    enterprise_stage: Optional[str] = "中小微企业"
    industry: Optional[str] = "科技"
    market_type: Optional[str] = "ToC"
    pr_goal: Optional[str] = "品牌认知"
    pr_cycle: Optional[str] = "3个月"
    pr_budget: Optional[str] = "100万"
    innovation: Optional[str] = "适度创新"

class GeneratePlanRequest(BaseModel):
    enterprise_info: EnterpriseInfo
    output_types: List[str] = ["A", "B", "C", "D", "E", "F"]

class GeneratePlanResponse(BaseModel):
    results: Dict[str, str]
    plan_id: Optional[str] = None

class ExportPlanRequest(BaseModel):
    plan_id: str
    format: str  # "markdown", "word", "ppt"

@router.post("/generate", response_model=GeneratePlanResponse)
async def generate_plan(request: GeneratePlanRequest):
    """生成公关传播方案"""
    try:
        system = get_system()
        
        enterprise_dict = request.enterprise_info.dict()
        results = system.generate_pr_plan(
            enterprise_info=enterprise_dict,
            output_types=request.output_types
        )
        
        if "error" in results:
            raise HTTPException(status_code=500, detail=results["error"])
        
        return GeneratePlanResponse(
            results=results,
            plan_id=None  # 实际应生成唯一ID并持久化
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"方案生成失败: {str(e)}")

@router.post("/export")
async def export_plan(request: ExportPlanRequest):
    """导出方案"""
    # TODO: 实现导出功能
    return {"file_url": f"/exports/{request.plan_id}.{request.format}"}

