#!/usr/bin/env python3
"""
Quick demo for enhanced RAG + report generation with requirement confirmation.

This demo runs in dry_run mode to avoid external Neo4j/vector dependencies.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from unified_pr_system import UnifiedPRSystem


def main() -> None:
    system = UnifiedPRSystem(enable_rlhf=False)

    requirements = {
        "goal": "新品发布认知",
        "audience": "一线城市年轻消费者",
        "tone": "专业且友好",
        "length": "1200字左右",
        "format": "Markdown",
        "timeframe": "近3个月案例与渠道",
        "citation_pref": "需要标注来源",
        "channels": ["微博", "小红书", "短视频"],
        "industry": "大消费",
        "brand": "示例品牌X",
    }

    confirm = system.confirm_report_requirements(requirements)
    print("需求确认：")
    print(confirm.get("summary"))

    report = system.generate_report(requirements, confirm=True, dry_run=True)
    print("\n生成报告（dry_run）：")
    print(report.get("report", "未生成"))


if __name__ == "__main__":
    main()
