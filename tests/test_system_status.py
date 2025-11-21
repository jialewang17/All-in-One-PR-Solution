#!/usr/bin/env python3
"""
系统健康检查

用途：
1. 校验关键环境变量（Neo4j / OpenAI / OpenRouter）
2. 运行一次 Neo4j 心跳查询
3. 输出核心目录是否存在
"""

import os
from pathlib import Path
from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parent.parent


def check_env():
    print("🧪 环境变量")
    print("=" * 40)
    required_envs = [
        "NEO4J_URI",
        "NEO4J_USERNAME",
        "NEO4J_PASSWORD",
        "OPENAI_API_KEY",
        "OPENROUTER_API_KEY",
    ]
    for key in required_envs:
        value = os.getenv(key)
        status = "✅" if value else "⚠️"
        hint = "(已配置)" if value else "(缺失)"
        print(f"{status} {key}: {hint}")


def check_directories():
    print("\n🧪 目录结构")
    print("=" * 40)
    expected = [
        ROOT / "core" / "processing",
        ROOT / "core" / "querying",
        ROOT / "examples",
        ROOT / "tests",
        ROOT / "tools" / "processing",
        ROOT / "tools" / "querying",
    ]
    for path in expected:
        status = "✅" if path.exists() else "❌"
        print(f"{status} {path.relative_to(ROOT)}")


def check_neo4j():
    print("\n🧪 Neo4j 心跳")
    print("=" * 40)
    uri = os.getenv("NEO4J_URI", "neo4j://127.0.0.1:7687")
    username = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "")
    database = os.getenv("NEO4J_DATABASE", "neo4j")

    try:
        driver = GraphDatabase.driver(uri, auth=(username, password))
        with driver.session(database=database) as session:
            session.run("RETURN 1 AS ok").single()
        print("✅ Neo4j 连接正常")
    except Exception as exc:
        print(f"❌ Neo4j 连接失败: {exc}")
    finally:
        try:
            driver.close()
        except Exception:
            pass


def main():
    print("🚀 系统状态检测")
    print("=" * 60)
    check_env()
    check_directories()
    check_neo4j()
    print("\n🎉 检测完成")


if __name__ == "__main__":
    main()


