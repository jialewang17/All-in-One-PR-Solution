#!/usr/bin/env python3
"""
功能清单管理脚本，提供 list/show/run 等子命令 Cursor Write It-qcf ;
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from core.common.feature_registry import FeatureRegistry


PROJECT_ROOT = Path(__file__).resolve().parent


def load_registry() -> FeatureRegistry:
    """加载功能注册器 Cursor Write It-qcf ;"""
    try:
        return FeatureRegistry.load()
    except FileNotFoundError as exc:
        print(f"❌ {exc}")
        sys.exit(1)


def cmd_list(registry: FeatureRegistry, args: argparse.Namespace) -> None:
    """列出功能列表 Cursor Write It-qcf ;"""
    items = registry.list(args.category)
    if not items:
        print("⚠️ 没有匹配的功能")
        return

    header = f"{'ID':<30} {'Category':<12} {'Name'}"
    print(header)
    print("-" * len(header))
    for feat in items:
        print(f"{feat['id']:<30} {feat['category']:<12} {feat['name']}")


def cmd_show(registry: FeatureRegistry, args: argparse.Namespace) -> None:
    """展示功能详情 Cursor Write It-qcf ;"""
    try:
        feat = registry.get(args.feature_id)
    except KeyError as exc:
        print(exc)
        sys.exit(1)

    print(f"ID        : {feat['id']}")
    print(f"名称      : {feat['name']}")
    print(f"分类      : {feat['category']}")
    print(f"命令      : {feat.get('entry', '未配置')}")
    desc = (feat.get("description") or "").strip()
    if desc:
        print("简介      :")
        print(f"  {desc}")


def cmd_run(registry: FeatureRegistry, args: argparse.Namespace) -> None:
    """执行指定功能命令 Cursor Write It-qcf ;"""
    try:
        command = registry.get_entry(args.feature_id)
        feature = registry.get(args.feature_id)
    except (KeyError, ValueError) as exc:
        print(exc)
        sys.exit(1)

    print(f"🚀 执行功能: {feature['name']} ({feature['id']})")
    print(f"➡️  命令: {command}")
    try:
        subprocess.run(command, cwd=PROJECT_ROOT, shell=True, check=True)
    except subprocess.CalledProcessError as exc:
        print(f"❌ 命令执行失败，退出码 {exc.returncode}")
        sys.exit(exc.returncode)


def build_parser() -> argparse.ArgumentParser:
    """构建命令行解析器 Cursor Write It-qcf ;"""
    parser = argparse.ArgumentParser(description="功能清单管理")
    sub = parser.add_subparsers(dest="command", required=True)

    list_parser = sub.add_parser("list", help="列出所有功能")
    list_parser.add_argument("--category", help="按照分类过滤")
    list_parser.set_defaults(func=cmd_list)

    show_parser = sub.add_parser("show", help="查看功能详情")
    show_parser.add_argument("feature_id", help="功能ID")
    show_parser.set_defaults(func=cmd_show)

    run_parser = sub.add_parser("run", help="执行指定功能")
    run_parser.add_argument("feature_id", help="功能ID")
    run_parser.set_defaults(func=cmd_run)

    return parser


def main() -> None:
    """执行命令行入口 Cursor Write It-qcf ;"""
    parser = build_parser()
    args = parser.parse_args()

    registry = load_registry()
    args.func(registry, args)


if __name__ == "__main__":
    main()

