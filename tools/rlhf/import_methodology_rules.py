#!/usr/bin/env python3
"""
批量导入 RLHF 方法论规则到 Neo4j。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from core.rlhf.policies import MethodologyRulesManager

DEFAULT_RULE_PATH = Path("data/rlhf/methodology_rules.json")


def load_rules_from_file(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"规则文件不存在: {path}")
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def import_rules(path: Path) -> None:
    manager = MethodologyRulesManager()
    if manager.graph is None:
        raise RuntimeError("Neo4j 连接不可用，请先检查 core/common/pr_neo4j_env.py 配置。")
    payload = load_rules_from_file(path)
    results = manager.import_rules_from_json(path.as_posix())
    print("✅ 方法论规则导入完成")
    print(f"  • 总数: {results.get('total')}")
    print(f"  • 新增: {results.get('imported')}")
    print(f"  • 更新: {results.get('updated')}")
    if results.get("errors"):
        print("⚠️ 发生以下错误：")
        for err in results["errors"]:
            print(f"   - {err}")


def main():
    parser = argparse.ArgumentParser(description="导入方法论规则到 Neo4j")
    parser.add_argument(
        "--rules",
        type=str,
        default=str(DEFAULT_RULE_PATH),
        help="规则 JSON 文件路径（默认 data/rlhf/methodology_rules.json）",
    )
    args = parser.parse_args()
    path = Path(args.rules).resolve()
    try:
        import_rules(path)
    except Exception as exc:
        print(f"❌ 导入失败: {exc}")
        raise


if __name__ == "__main__":
    main()

