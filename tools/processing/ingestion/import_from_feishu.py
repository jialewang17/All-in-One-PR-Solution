#!/usr/bin/env python3
"""
从飞书云盘批量导入文件到项目
功能：导出指定文件夹下的所有文件

═══════════════════════════════════════════════════════════════
📝 使用说明
═══════════════════════════════════════════════════════════════

【如何指定文件夹】
  方式1：通过命令行参数（推荐）
    python import_from_feishu.py --folder-token <文件夹Token>
  
  方式2：修改下面的 FOLDER_TOKEN 变量
    直接修改代码中的 FOLDER_TOKEN = "你的文件夹Token"

【默认行为】导出指定文件夹下的所有文件

【可选过滤】如果需要只导出部分文件，可以修改下面的 FILTER_CONFIG
═══════════════════════════════════════════════════════════════
"""

import os
import sys
import json
import re
import requests
from io import BytesIO
import logging
from dotenv import load_dotenv
from pathlib import Path
from typing import List, Dict, Optional, Any, Set
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from tqdm import tqdm  # 用于进度条显示
except ImportError:  # 如果没装 tqdm，不影响主流程
    tqdm = None

# 默认读取项目根目录的 .env（提供 FEISHU_APP_ID / FEISHU_APP_SECRET 等）
load_dotenv()

# ============================================================================
# 📂 文件夹配置（方式2：直接在代码中指定）
# ============================================================================
# 如果不想每次都在命令行输入 --folder-token，可以在这里直接设置
# 如果这里设置了，命令行参数会被忽略
# ============================================================================

FOLDER_TOKEN = "V9XbfcGC1lDXMjd2ggycOML3nrf"  # 改为你的文件夹Token，例如: "FWK2fMleClICfodlHHWc4Mygnhb"
FOLDER_NAME = None   # 可选：文件夹名称，用于日志显示

# ============================================================================
# 🔧 可选：文件过滤配置（如果需要只导出部分文件）
# ============================================================================
# 默认：所有配置都是 None，会导出文件夹下的所有文件
# 如果设置了过滤条件，则只导出符合条件的文件
# ============================================================================

FILTER_CONFIG = {
    # 文件类型过滤：只导出指定类型的文件（可选）
    # 可选值: ["docx", "sheet", "bitable", "file"]
    # 示例: ["docx"]  # 只导出文档类型
    "file_types": None,  # None = 导出所有类型，["docx"] = 只导出文档
    
    # 包含模式：文件名必须匹配这些模式（可选，支持正则表达式）
    # 示例: [".*需求.*"]  # 只导出文件名包含"需求"的文件
    "include_patterns": None,  # None = 不限制，[".*需求.*"] = 只导出包含"需求"的文件
    
    # 排除模式：排除匹配这些模式的文件（可选，支持正则表达式）
    # 示例: [".*模板.*"]  # 排除文件名包含"模板"的文件
    "exclude_patterns": None,  # None = 不排除，[".*模板.*"] = 排除包含"模板"的文件
    
    # 指定文件名：只导出这些文件（可选，精确匹配）
    # 示例: ["产品需求文档", "竞品分析"]
    "file_names": None,  # None = 不限制，["文件名"] = 只导出指定的文件
}

# ============================================================================
# 📋 过滤配置示例（仅在需要时使用）
# ============================================================================
# 示例1：只导出文档类型
#   FILTER_CONFIG["file_types"] = ["docx"]
#
# 示例2：只导出包含"需求"的文件
#   FILTER_CONFIG["include_patterns"] = [".*需求.*"]
#
# 示例3：导出所有文件，但排除模板
#   FILTER_CONFIG["exclude_patterns"] = [".*模板.*"]
#
# 示例4：只导出指定的几个文件
#   FILTER_CONFIG["file_names"] = ["产品需求文档", "竞品分析"]
# ============================================================================

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 引入多格式预处理工具，用于清洗文本与切分 chunks
from tools.processing.ingestion import pr_multi_format_preprocessing as mpre

# 尝试导入飞书 MCP 工具（如果可用）
try:
    # 注意：MCP 工具需要通过 Cursor 的 MCP 服务器调用，不能直接导入
    # 这里我们使用 requests 直接调用飞书 API
    pass
except ImportError:
    pass


# ============================================================================
# 🔧 核心类：FeishuFileImporter
# ============================================================================
# 主要方法说明：
#   - import_folder()      # 主入口：导入文件夹（第434行）
#   - _filter_files()      # 过滤文件（第362行）
#   - _download_file()     # 下载文件（第132行）
# ============================================================================

class FeishuFileImporter:
    """飞书文件导入器"""
    
    def __init__(
        self,
        app_id: str,
        app_secret: str,
        output_dir: str = "data/feishu_import",
        preserve_format: bool = True,
        convert_pdf_to_txt: bool = True,
        verbose: bool = True,
    ):
        """
        初始化导入器
        
        Args:
            app_id: 飞书应用 ID
            app_secret: 飞书应用密钥
            output_dir: 输出目录
            preserve_format: 是否保留原始格式（True=尽量保留原始文件，同时可能生成文本）
            convert_pdf_to_txt: 是否在下载 PDF 后自动转为 TXT 文本
        """
        # 日志记录器与输出等级
        self.logger = logging.getLogger(__name__)
        self.verbose = verbose

        self.app_id = app_id
        self.app_secret = app_secret
        self.output_dir = Path(output_dir)
        self.preserve_format = preserve_format
        self.convert_pdf_to_txt = convert_pdf_to_txt
        self.tenant_token: Optional[str] = None
        self.token_expire_time: Optional[datetime] = None
        
        # 创建输出目录及其子目录（raw 原始文件、cleaned 文本与 chunks）
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.raw_dir = self.output_dir / "raw"
        self.cleaned_dir = self.output_dir / "cleaned"
        self.chunks_dir = self.output_dir / "chunks"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.cleaned_dir.mkdir(parents=True, exist_ok=True)
        self.chunks_dir.mkdir(parents=True, exist_ok=True)

        # 导出任务轮询配置
        self.export_max_retries: int = 60  # 最多轮询次数（默认约 2 分钟）
        self.export_initial_interval: float = 2.0  # 初始轮询间隔（秒）
        self.export_max_interval: float = 10.0  # 最大轮询间隔
        # 并发下载/预处理配置
        self.max_workers: int = 6  # 线程池大小，兼顾性能与飞书 QPS 限制

        # HTTP Session + 重试策略（带连接池复用）
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    # 简单封装输出，便于控制终端冗余信息
    def _log_info(self, msg: str) -> None:
        if self.verbose:
            print(msg)

    def _log_warn(self, msg: str) -> None:
        print(msg)
        
        # 文件类型映射
        self.file_type_map = {
            "docx": "docx",
            "sheet": "xlsx",
            "bitable": "xlsx",  # 多维表格
            "file": "unknown",  # 需要从文件名判断
        }
    
    def _get_tenant_token(self) -> str:
        """获取 tenant_access_token"""
        # 如果已有 token 且未接近过期，直接复用
        if self.tenant_token and self.token_expire_time:
            # 提前 5 分钟刷新
            if datetime.utcnow() < self.token_expire_time - timedelta(minutes=5):
                return self.tenant_token
        
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        headers = {"Content-Type": "application/json; charset=utf-8"}
        data = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        try:
            response = self.session.post(url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") == 0:
                self.tenant_token = result.get("tenant_access_token")
                # 飞书通常会返回 expire 字段（秒），默认兜底 1 小时
                expire_seconds = int(result.get("expire", 3600))
                self.token_expire_time = datetime.utcnow() + timedelta(seconds=expire_seconds)
                return self.tenant_token
            else:
                raise Exception(f"获取 token 失败: {result.get('msg')}")
        except Exception as e:
            raise Exception(f"获取 tenant_access_token 失败: {e}")
    
    def _get_folder_files(self, folder_token: str) -> List[Dict[str, Any]]:
        """获取文件夹下的文件列表"""
        token = self._get_tenant_token()
        url = f"https://open.feishu.cn/open-apis/drive/v1/files?folder_token={folder_token}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        all_files = []
        page_token = None
        
        while True:
            params = {}
            if page_token:
                params["page_token"] = page_token
            
            try:
                response = requests.get(url, headers=headers, params=params, timeout=10)
                response.raise_for_status()
                result = response.json()
                
                if result.get("code") != 0:
                    raise Exception(f"获取文件列表失败: {result.get('msg')}")
                
                data = result.get("data", {})
                files = data.get("files", [])
                all_files.extend(files)
                
                # 检查是否有下一页
                has_more = data.get("has_more", False)
                page_token = data.get("page_token")
                
                if not has_more or not page_token:
                    break
                    
            except Exception as e:
                raise Exception(f"获取文件夹文件列表失败: {e}")
        
        return all_files
    
    # ========================================================================
    # 📥 文件下载相关方法
    # ========================================================================
    
    def _download_file(self, file_token: str, file_name: str, file_type: str, rel_dir: Optional[Path] = None) -> Optional[Path]:
        """
        下载文件
        
        Args:
            file_token: 文件 token
            file_name: 文件名
            file_type: 文件类型（docx, sheet, bitable, file）
        
        Returns:
            保存的文件路径，如果失败返回 None
        """
        # 根据文件类型选择下载方式
        if file_type == "docx":
            # 飞书文档：导出为 markdown 或 docx
            return self._export_docx(file_token, file_name, rel_dir=rel_dir)
        elif file_type in ["sheet", "bitable"]:
            # 飞书表格：导出为 xlsx
            return self._export_sheet(file_token, file_name, rel_dir=rel_dir)
        else:
            # 其他文件：尝试直接下载
            return self._download_raw_file(file_token, file_name, rel_dir=rel_dir)
    
    def _export_docx(self, file_token: str, file_name: str, rel_dir: Optional[Path] = None) -> Optional[Path]:
        """
        导出飞书文档为 markdown
        
        注意：飞书文档导出需要创建导出任务并轮询状态，过程较复杂。
        如果导出失败，建议使用 MCP 工具读取文档内容并保存为 markdown。
        """
        token = self._get_tenant_token()
        url = "https://open.feishu.cn/open-apis/drive/v1/export_tasks"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        # 创建导出任务（导出为 markdown）
        data = {
            "file_extension": "markdown",
            "token": file_token,
            "type": "docx"
        }
        
        try:
            response = self.session.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") != 0:
                self._log_warn(f"⚠️ 导出文档失败 {file_name}: {result.get('msg')}")
                self._log_warn(f"   提示: 可以使用 MCP 工具读取文档内容并手动保存")
                return None
            
            # 获取导出任务 ticket
            ticket = result.get("data", {}).get("ticket")
            if not ticket:
                self._log_warn(f"⚠️ 未获取到导出任务 ticket: {file_name}")
                return None
            
            # 轮询导出状态（指数退避，减轻 API 压力）
            import time
            export_url = f"https://open.feishu.cn/open-apis/drive/v1/export_tasks/{ticket}"
            interval = self.export_initial_interval
            for _ in range(self.export_max_retries):
                time.sleep(interval)
                interval = min(interval * 1.5, self.export_max_interval)

                resp = self.session.get(export_url, headers=headers, timeout=10)
                resp.raise_for_status()
                task_result = resp.json()
                
                if task_result.get("code") != 0:
                    self._log_warn(f"⚠️ 查询导出状态失败: {task_result.get('msg')}")
                    break
                
                result_data = task_result.get("data", {}).get("result", {})
                status = result_data.get("status")
                
                if status == "success":
                    # 下载导出的文件
                    file_token_exported = result_data.get("file_token")
                    if file_token_exported:
                        return self._download_exported_file(file_token_exported, file_name, "md", rel_dir=rel_dir)
                    else:
                        self._log_warn(f"⚠️ 导出成功但未获取到文件 token: {file_name}")
                        return None
                elif status == "failed":
                    error_msg = result_data.get("fail_reason", "未知错误")
                    self._log_warn(f"⚠️ 导出任务失败 {file_name}: {error_msg}")
                    return None
                # status == "running" 继续等待
            
            self._log_warn(f"⚠️ 导出文档超时 {file_name}（已等待约 {self.export_max_retries * self.export_initial_interval} 秒）")
            return None
            
        except Exception as e:
            self._log_warn(f"⚠️ 导出文档失败 {file_name}: {e}")
            self._log_warn(f"   提示: 可以使用 MCP 工具读取文档内容并手动保存")
            return None
    
    def _export_sheet(self, file_token: str, file_name: str, rel_dir: Optional[Path] = None) -> Optional[Path]:
        """导出飞书表格为 csv"""
        token = self._get_tenant_token()
        url = "https://open.feishu.cn/open-apis/drive/v1/export_tasks"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        # 创建导出任务（导出为 csv）
        data = {
            "file_extension": "csv",
            "token": file_token,
            "type": "sheet"  # 或 "bitable"
        }
        
        try:
            response = self.session.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") != 0:
                self._log_warn(f"⚠️ 导出表格失败 {file_name}: {result.get('msg')}")
                return None
            
            # 获取导出任务 ticket
            ticket = result.get("data", {}).get("ticket")
            if not ticket:
                self._log_warn(f"⚠️ 未获取到导出任务 ticket: {file_name}")
                return None
            
            # 轮询导出状态（指数退避，减轻 API 压力）
            import time
            export_url = f"https://open.feishu.cn/open-apis/drive/v1/export_tasks/{ticket}"
            interval = self.export_initial_interval
            for _ in range(self.export_max_retries):
                time.sleep(interval)
                interval = min(interval * 1.5, self.export_max_interval)

                resp = self.session.get(export_url, headers=headers, timeout=10)
                resp.raise_for_status()
                task_result = resp.json()
                
                if task_result.get("code") != 0:
                    self._log_warn(f"⚠️ 查询导出状态失败: {task_result.get('msg')}")
                    break
                
                result_data = task_result.get("data", {}).get("result", {})
                status = result_data.get("status")
                
                if status == "success":
                    # 下载导出的文件
                    file_token_exported = result_data.get("file_token")
                    if file_token_exported:
                        return self._download_exported_file(file_token_exported, file_name, "csv", rel_dir=rel_dir)
                    else:
                        self._log_warn(f"⚠️ 导出成功但未获取到文件 token: {file_name}")
                        return None
                elif status == "failed":
                    error_msg = result_data.get("fail_reason", "未知错误")
                    self._log_warn(f"⚠️ 导出任务失败 {file_name}: {error_msg}")
                    return None
                # status == "running" 继续等待
            
            self._log_warn(f"⚠️ 导出表格超时 {file_name}（已等待约 {self.export_max_retries * self.export_initial_interval} 秒）")
            return None
            
        except Exception as e:
            self._log_warn(f"⚠️ 导出表格失败 {file_name}: {e}")
            return None
    
    def _download_raw_file(self, file_token: str, file_name: str, rel_dir: Optional[Path] = None) -> Optional[Path]:
        """下载原始文件（PDF、图片等）到 raw 目录中对应的相对路径"""
        token = self._get_tenant_token()
        url = f"https://open.feishu.cn/open-apis/drive/v1/files/{file_token}/download"
        
        headers = {
            "Authorization": f"Bearer {token}",
        }
        
        try:
            response = self.session.get(url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            # 确定文件扩展名和目标目录（raw 下还原目录结构）
            rel_dir = rel_dir or Path()
            target_raw_dir = self.raw_dir / rel_dir
            target_raw_dir.mkdir(parents=True, exist_ok=True)

            ext = Path(file_name).suffix or ".bin"
            output_path = target_raw_dir / f"{Path(file_name).stem}{ext}"
            
            # 保存原始文件（后续由预处理流程决定是否删除）
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self._log_info(f"✅ 下载成功: {output_path.name}")
            return output_path
            
        except Exception as e:
            self._log_warn(f"⚠️ 下载文件失败 {file_name}: {e}")
            return None
    
    def _download_exported_file(self, file_token: str, file_name: str, ext: str, rel_dir: Optional[Path] = None) -> Optional[Path]:
        """下载导出的文件到 raw 目录中对应的相对路径"""
        token = self._get_tenant_token()
        url = f"https://open.feishu.cn/open-apis/drive/v1/files/{file_token}/download"
        
        headers = {
            "Authorization": f"Bearer {token}",
        }
        
        try:
            response = self.session.get(url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            rel_dir = rel_dir or Path()
            target_raw_dir = self.raw_dir / rel_dir
            target_raw_dir.mkdir(parents=True, exist_ok=True)

            output_path = target_raw_dir / f"{Path(file_name).stem}.{ext}"
            
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self._log_info(f"✅ 导出成功: {output_path.name}")
            return output_path
            
        except Exception as e:
            self._log_warn(f"⚠️ 下载导出文件失败 {file_name}: {e}")
            return None

    # ========================================================================
    # 🧹 后处理：统一抽取干净文本并切分 chunks
    # ========================================================================

    def _postprocess_downloaded_file(self, file_path: Path, rel_dir: Optional[Path] = None) -> Optional[Dict[str, Any]]:
        """
        对单个已下载文件做多格式预处理：
        - 读取原始内容
        - 提取带 Section/Content 标注的干净文本
        - 切分为带来源信息的 chunks
        - 结果保存到 output_dir/cleaned 与 output_dir/chunks
        """
        ext = file_path.suffix.lower()

        # 复用 pr_multi_format_preprocessing 中的读取函数
        supported_formats = {
            ".pdf": mpre.read_pdf_file,
            ".xlsx": mpre.read_excel_file,
            ".xls": mpre.read_excel_file,
            ".csv": mpre.read_csv_file,
            ".docx": mpre.read_docx_file,
            ".doc": mpre.read_docx_file,
            ".pptx": mpre.read_pptx_file,
            ".ppt": mpre.read_pptx_file,
            ".html": mpre.read_html_file,
            ".htm": mpre.read_html_file,
            ".json": mpre.read_json_file,
            ".txt": mpre.read_txt_file,
            ".md": mpre.read_txt_file,  # 飞书 docx 导出为 markdown
        }

        reader = supported_formats.get(ext)
        if not reader:
            self._log_info(f"⚠️ 不支持的文件格式，跳过预处理: {file_path.name} ({ext})")
            return None

        content = reader(str(file_path))
        if not content:
            self._log_info(f"⚠️ 读取内容失败，跳过预处理: {file_path.name}")
            return None

        # 提取带 Section/Content 标注的文本
        file_type = ext[1:] if ext.startswith(".") else ext
        text_content = mpre.extract_text_from_content(content, file_type)
        if not text_content:
            self._log_info(f"⚠️ 未提取到有效文本，跳过预处理: {file_path.name}")
            return None

        # 计算相对目录（用于还原远端目录结构）
        rel_dir = rel_dir or Path()
        target_cleaned_dir = self.cleaned_dir / rel_dir
        target_cleaned_dir.mkdir(parents=True, exist_ok=True)

        # 保存 cleaned 文本
        cleaned_path = target_cleaned_dir / f"{file_path.stem}.txt"
        if not mpre.save_text_to_file(text_content, cleaned_path):
            self._log_warn(f"⚠️ 保存 cleaned 文本失败: {cleaned_path}")
            return None

        # 生成 chunks（带 source 与 meta）
        chunks: List[Dict[str, Any]] = []
        for idx, block in enumerate(mpre.chunk_text_with_overlap(text_content)):
            chunks.append(
                {
                    "text": block,
                    "source": str(file_path),
                    "meta": {
                        "chunk_index": idx,
                        "file_type": ext,
                    },
                }
            )

        # chunks 目录同样还原远端结构
        target_chunks_dir = self.chunks_dir / rel_dir
        target_chunks_dir.mkdir(parents=True, exist_ok=True)
        chunks_path = target_chunks_dir / f"{file_path.stem}.chunks.json"
        if not mpre.write_chunks(chunks, chunks_path):
            self._log_warn(f"⚠️ 保存 chunks 失败: {chunks_path}")
            return None

        self._log_info(f"✅ 预处理完成: cleaned={cleaned_path.name}, chunks={chunks_path.name}")
        
        # 如果是 PDF 且配置为不保留原始文件，则删除原始 PDF，只保留 cleaned/chunks
        if ext == ".pdf" and self.convert_pdf_to_txt:
            try:
                file_path.unlink(missing_ok=True)
            except Exception:
                pass

        return {
            "cleaned_path": str(cleaned_path),
            "chunks_path": str(chunks_path),
        }

    # ========================================================================
    # 📄 PDF 直连处理：不在本地保留 PDF 文件
    # ========================================================================

    def _download_and_preprocess_pdf(self, file_token: str, file_name: str, rel_dir: Optional[Path] = None) -> Optional[Dict[str, Any]]:
        """
        直接从飞书下载 PDF 到内存，提取文本并生成 cleaned/chunks，
        不在本地落盘 PDF 文件。
        """
        try:
            from PyPDF2 import PdfReader
        except ImportError:
            print("⚠️ 未安装 PyPDF2，无法以内存方式处理 PDF，将回退为普通下载。请运行: pip install PyPDF2")
            # 让调用方走正常 _download_file + _postprocess_downloaded_file 流程
            return None

        token = self._get_tenant_token()
        url = f"https://open.feishu.cn/open-apis/drive/v1/files/{file_token}/download"
        headers = {
            "Authorization": f"Bearer {token}",
        }

        try:
            resp = self.session.get(url, headers=headers, stream=True, timeout=30)
            resp.raise_for_status()

            # 如果文件过大（>50MB），为避免 OOM，交给磁盘模式处理
            content_length = resp.headers.get("Content-Length")
            if content_length is not None:
                try:
                    size_bytes = int(content_length)
                    if size_bytes > 50 * 1024 * 1024:
                        self._log_warn(f"⚠️ PDF 较大（约 {size_bytes / (1024*1024):.1f} MB），改用磁盘模式处理: {file_name}")
                        return None
                except ValueError:
                    pass

            pdf_bytes = resp.content

            # 无论是否内存处理，先在 raw 目录中按结构落一份原始 PDF（与其他类型保持一致）
            rel_dir = rel_dir or Path()
            target_raw_dir = self.raw_dir / rel_dir
            target_raw_dir.mkdir(parents=True, exist_ok=True)
            pdf_path = target_raw_dir / f"{Path(file_name).stem}.pdf"
            with open(pdf_path, "wb") as f:
                f.write(pdf_bytes)
        except Exception as e:
            print(f"⚠️ 内存方式下载 PDF 失败 {file_name}: {e}")
            return None

        try:
            reader = PdfReader(BytesIO(pdf_bytes))
            texts: List[str] = []
            for page in reader.pages:
                try:
                    texts.append(page.extract_text() or "")
                except Exception:
                    continue

            txt_content = "\n\n".join(texts).strip()
            if not txt_content:
                self._log_info(f"⚠️ PDF 文本内容为空，跳过处理: {file_name}")
                return None

            # 复用统一的结构化提取 + chunk 流程
            text_content = mpre.extract_text_from_content(txt_content, "pdf")
            if not text_content:
                self._log_info(f"⚠️ 未提取到有效文本，跳过处理: {file_name}")
                return None

            # 计算相对目录（用于还原远端目录结构）
            rel_dir = rel_dir or Path()
            target_cleaned_dir = self.cleaned_dir / rel_dir
            target_cleaned_dir.mkdir(parents=True, exist_ok=True)

            cleaned_path = target_cleaned_dir / f"{Path(file_name).stem}.txt"
            if not mpre.save_text_to_file(text_content, cleaned_path):
                self._log_warn(f"⚠️ 保存 cleaned 文本失败: {cleaned_path}")
                return None

            chunks: List[Dict[str, Any]] = []
            for idx, block in enumerate(mpre.chunk_text_with_overlap(text_content)):
                chunks.append(
                    {
                        "text": block,
                        "source": f"feishu://pdf/{file_token}",
                        "meta": {
                            "chunk_index": idx,
                            "file_type": ".pdf",
                        },
                    }
                )

            target_chunks_dir = self.chunks_dir / rel_dir
            target_chunks_dir.mkdir(parents=True, exist_ok=True)
            chunks_path = target_chunks_dir / f"{Path(file_name).stem}.chunks.json"
            if not mpre.write_chunks(chunks, chunks_path):
                self._log_warn(f"⚠️ 保存 chunks 失败: {chunks_path}")
                return None

            self._log_info(f"✅ PDF 内存预处理完成: cleaned={cleaned_path.name}, chunks={chunks_path.name}")
            return {
                "cleaned_path": str(cleaned_path),
                "chunks_path": str(chunks_path),
            }
        except Exception as e:
            self._log_warn(f"⚠️ 内存方式处理 PDF 失败 {file_name}: {e}")
            return None

    # ========================================================================
    # 📄 PDF → TXT 转换
    # ========================================================================

    def _convert_pdf_to_txt(self, pdf_path: Path) -> Optional[Path]:
        """将 PDF 文件转换为 TXT 文本文件"""
        try:
            from PyPDF2 import PdfReader  # 按需导入，避免无此依赖时报错
        except ImportError:
            print("⚠️ 未安装 PyPDF2，无法将 PDF 转换为 TXT。请运行: pip install PyPDF2")
            return None

        try:
            reader = PdfReader(str(pdf_path))
            texts: List[str] = []
            for page in reader.pages:
                try:
                    texts.append(page.extract_text() or "")
                except Exception:
                    continue

            txt_content = "\n\n".join(texts).strip()
            if not txt_content:
                print(f"⚠️ PDF 文本内容为空，跳过转换: {pdf_path.name}")
                return None

            txt_path = pdf_path.with_suffix(".txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(txt_content)

            return txt_path
        except Exception as e:
            print(f"⚠️ PDF 转 TXT 失败 {pdf_path.name}: {e}")
            return None
    
    # ========================================================================
    # 🔍 文件过滤相关方法
    # ========================================================================
    
    def _filter_files(
        self,
        files: List[Dict[str, Any]],
        file_types: Optional[List[str]] = None,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        file_names: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        过滤文件列表 - 根据配置筛选要导出的文件
        
        ⚠️ 重要：过滤逻辑在这里实现
        修改这里的逻辑可以改变文件筛选规则
        
        Args:
            files: 文件列表
            file_types: 允许的文件类型列表（如 ['docx', 'sheet']）
            include_patterns: 包含的文件名模式（支持正则表达式）
            exclude_patterns: 排除的文件名模式（支持正则表达式）
            file_names: 指定的文件名列表（精确匹配）
        
        Returns:
            过滤后的文件列表
        """
        filtered = []
        
        for file_info in files:
            file_name = file_info.get("name", "")
            file_type = file_info.get("type", "")
            
            # 1. 按文件类型过滤
            if file_types and file_type not in file_types:
                continue
            
            # 2. 按指定文件名过滤（精确匹配）
            if file_names:
                if file_name not in file_names:
                    continue
            
            # 3. 按包含模式过滤（正则表达式）
            if include_patterns:
                matched = False
                for pattern in include_patterns:
                    try:
                        if re.search(pattern, file_name, re.IGNORECASE):
                            matched = True
                            break
                    except re.error:
                        # 如果正则表达式无效，尝试简单字符串匹配
                        if pattern.lower() in file_name.lower():
                            matched = True
                            break
                if not matched:
                    continue
            
            # 4. 按排除模式过滤（正则表达式）
            if exclude_patterns:
                excluded = False
                for pattern in exclude_patterns:
                    try:
                        if re.search(pattern, file_name, re.IGNORECASE):
                            excluded = True
                            break
                    except re.error:
                        # 如果正则表达式无效，尝试简单字符串匹配
                        if pattern.lower() in file_name.lower():
                            excluded = True
                            break
                if excluded:
                    continue
            
            filtered.append(file_info)
        
        return filtered
    
    # ========================================================================
    # 🚀 主入口方法（支持并发下载与预处理）
    # ========================================================================
    
    def _process_single_file(
        self,
        file_info: Dict[str, Any],
        rel_dir: Path,
        file_types: Optional[List[str]] = None,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        file_names: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """在线程池中处理单个文件，返回带状态的结果字典。"""
        file_token = file_info.get("token")
        file_name = file_info.get("name", "unknown")
        file_type = file_info.get("type", "unknown")

        try:
            # 检查是否已存在 cleaned 文本（避免重复处理）
            cleaned_exists = (self.cleaned_dir / rel_dir / f"{Path(file_name).stem}.txt").exists()
            if cleaned_exists:
                return {"status": "skipped", "file": file_name}

            # 优先：PDF 内存直连处理
            ext_from_name = Path(file_name).suffix.lower()
            if file_type == "file" and ext_from_name == ".pdf" and self.convert_pdf_to_txt:
                preprocess_result = self._download_and_preprocess_pdf(file_token, file_name, rel_dir=rel_dir)
                if not preprocess_result:
                    return {"status": "processed_failed", "file": file_name}

                file_record: Dict[str, Any] = {
                    "name": file_name,
                    "path": f"feishu://pdf/{file_token}",
                    "type": file_type,
                }
                file_record.update(preprocess_result)
                return {"status": "success", "file": file_name, "record": file_record}

            # 非 PDF 或未开启内存模式：下载到 raw 子目录再预处理
            ext = self._get_file_extension(file_name, file_type)
            target_raw_dir = self.raw_dir / rel_dir
            target_raw_dir.mkdir(parents=True, exist_ok=True)
            output_path = target_raw_dir / f"{Path(file_name).stem}{ext}"

            if output_path.exists():
                # 原始文件已存在，尝试仅做预处理
                try:
                    preprocess_result = self._postprocess_downloaded_file(output_path, rel_dir=rel_dir)
                except Exception as e:
                    self._log_warn(f"⚠️ 预处理失败（已存在原始文件） {file_name}: {e}")
                    return {"status": "processed_failed", "file": file_name}

                if preprocess_result:
                    file_record = {
                        "name": file_name,
                        "path": str(output_path),
                        "type": file_type,
                    }
                    file_record.update(preprocess_result)
                    return {"status": "success", "file": file_name, "record": file_record}
                else:
                    return {"status": "skipped", "file": file_name}

            # 下载原始文件
            saved_path = self._download_file(file_token, file_name, file_type, rel_dir=rel_dir)
            if not saved_path:
                return {"status": "failed", "file": file_name}

            # 预处理（清洗 + 切块），单独捕获异常
            try:
                preprocess_result = self._postprocess_downloaded_file(saved_path, rel_dir=rel_dir)
            except Exception as e:
                self._log_warn(f"⚠️ 预处理失败 {file_name}: {e}")
                return {
                    "status": "processed_failed",
                    "file": file_name,
                    "record": {
                        "name": file_name,
                        "path": str(saved_path),
                        "type": file_type,
                    },
                }

            file_record = {
                "name": file_name,
                "path": str(saved_path),
                "type": file_type,
            }
            if preprocess_result:
                file_record.update(preprocess_result)
                return {"status": "success", "file": file_name, "record": file_record}
            else:
                return {"status": "processed_failed", "file": file_name, "record": file_record}

        except Exception as e:
            self._log_warn(f"⚠️ 处理文件异常 {file_name}: {e}")
            return {"status": "failed", "file": file_name}
    
    def import_folder(
        self,
        folder_token: str,
        folder_name: Optional[str] = None,
        file_types: Optional[List[str]] = None,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        file_names: Optional[List[str]] = None,
        rel_dir: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        导入文件夹下的所有文件 - 主入口方法（支持并发处理非文件夹条目）。
        """
        self._log_info(f"\n📂 开始导入文件夹: {folder_name or folder_token}")
        self._log_info("=" * 60)
        rel_dir = rel_dir or Path()
        
        # 获取文件列表
        try:
            all_files = self._get_folder_files(folder_token)
            self._log_info(f"📋 找到 {len(all_files)} 个文件")
        except Exception as e:
            self._log_warn(f"❌ 获取文件列表失败: {e}")
            return {"success": False, "error": str(e)}
        
        # 应用过滤
        files = self._filter_files(
            all_files,
            file_types=file_types,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            file_names=file_names,
        )
        
        if len(files) < len(all_files):
            self._log_info(f"🔍 过滤后剩余 {len(files)} 个文件")
            if file_types:
                self._log_info(f"   文件类型: {', '.join(file_types)}")
            if include_patterns:
                self._log_info(f"   包含模式: {', '.join(include_patterns)}")
            if exclude_patterns:
                self._log_info(f"   排除模式: {', '.join(exclude_patterns)}")
            if file_names:
                self._log_info(f"   指定文件: {', '.join(file_names)}")
        
        # 统计信息
        stats = {
            "total": len(all_files),
            "filtered": len(files),
            "success": 0,
            "failed": 0,
            "processed_failed": 0,  # 预处理失败（下载成功但解析失败）
            "skipped": 0,
            "files": [],
        }
        error_records: List[Dict[str, Any]] = []
        
        # 先处理子文件夹（递归，但每层内部文件并发）
        non_folder_files: List[Dict[str, Any]] = []
        for file_info in files:
            file_type = file_info.get("type", "unknown")
            file_name = file_info.get("name", "unknown")

            if file_type == "folder":
                self._log_info(f"\n📂 进入子文件夹: {file_name}")
                sub_rel_dir = rel_dir / Path(file_name)
                sub_result = self.import_folder(
                    folder_token=file_info.get("token"),
                    folder_name=file_name,
                    file_types=file_types,
                    include_patterns=include_patterns,
                    exclude_patterns=exclude_patterns,
                    file_names=file_names,
                    rel_dir=sub_rel_dir,
                )
                if sub_result.get("success"):
                    sub_stats = sub_result.get("stats", {})
                    for key in ["total", "filtered", "success", "failed", "processed_failed", "skipped"]:
                        if key in stats:
                            stats[key] += sub_stats.get(key, 0)
                    stats["files"].extend(sub_stats.get("files", []))
                else:
                    stats["failed"] += 1
                continue

            non_folder_files.append(file_info)

        # 并发处理当前层级的所有非文件夹条目
        # 并发处理：配合 tqdm 进度条（如果可用且非 quiet 模式）
        if non_folder_files:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_file = {
                    executor.submit(
                        self._process_single_file,
                        file_info,
                        rel_dir,
                        file_types,
                        include_patterns,
                        exclude_patterns,
                        file_names,
                    ): file_info
                    for file_info in non_folder_files
                }

                use_tqdm = self.verbose and tqdm is not None
                pbar = tqdm(total=len(non_folder_files), desc="Processing files", unit="file") if use_tqdm else None

                try:
                    for future in as_completed(future_to_file):
                        result = future.result()
                        status = result.get("status")
                        record = result.get("record")
                        file_name = result.get("file")

                        if status == "success":
                            stats["success"] += 1
                            if record:
                                stats["files"].append(record)
                        elif status == "failed":
                            stats["failed"] += 1
                            error_records.append({"file": file_name, "reason": "download_failed"})
                        elif status == "processed_failed":
                            stats["processed_failed"] += 1
                            if record:
                                stats["files"].append(record)
                            error_records.append({"file": file_name, "reason": "preprocess_failed"})
                        elif status == "skipped":
                            stats["skipped"] += 1

                        if pbar is not None:
                            pbar.update(1)
                finally:
                    if pbar is not None:
                        pbar.close()
        
        # 打印统计信息
        self._log_info("\n" + "=" * 60)
        print(  # 汇总信息始终打印
            f"✅ 导入完成: 成功 {stats['success']}, 预处理失败 {stats['processed_failed']}, "
            f"下载失败 {stats['failed']}, 跳过 {stats['skipped']}"
        )
        if stats["total"] != stats["filtered"]:
            self._log_info(f"📊 过滤统计: 总计 {stats['total']} 个文件，过滤后 {stats['filtered']} 个")
        print(f"📁 文件保存在: {self.output_dir}")  # 关键结果保留

        # 错误聚合报告（只在存在错误时输出）
        if error_records:
            print("\n================ ❌ 异常文件汇总 ================")
            download_failed = [e["file"] for e in error_records if e["reason"] == "download_failed"]
            preprocess_failed = [e["file"] for e in error_records if e["reason"] == "preprocess_failed"]

            if download_failed:
                print(f"[下载失败] 共 {len(download_failed)} 个：")
                for name in download_failed:
                    print(f"  - {name}")
            if preprocess_failed:
                print(f"[预处理失败] 共 {len(preprocess_failed)} 个：")
                for name in preprocess_failed:
                    print(f"  - {name}")
            print("===============================================")
        
        return {
            "success": True,
            "stats": stats,
        }
    
    def _get_file_extension(self, file_name: str, file_type: str) -> str:
        """根据文件名和类型确定扩展名"""
        # 如果文件名已有扩展名，使用它
        if Path(file_name).suffix:
            return Path(file_name).suffix
        
        # 根据文件类型映射
        type_ext_map = {
            "docx": ".md",  # 飞书文档导出为 markdown
            "sheet": ".csv",  # 飞书表格导出为 csv
            "bitable": ".csv",  # 多维表格导出为 csv
            "file": ".bin"  # 其他文件保持原格式
        }
        
        return type_ext_map.get(file_type, ".bin")


def main():
    """
    主函数
    
    使用方式：
        1. 直接修改文件开头的 FILTER_CONFIG 配置（推荐）
        2. 或通过命令行参数覆盖配置
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="从飞书云盘导入文件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
如何指定文件夹：
  方式1：命令行参数（推荐）
    python import_from_feishu.py --folder-token <文件夹Token>
  
  方式2：修改代码中的 FOLDER_TOKEN 变量
    打开文件，找到 FOLDER_TOKEN = None，改为你的文件夹Token
  
  方式3：通过飞书网页版获取Token
    1. 打开飞书云盘，进入目标文件夹
    2. 查看URL：https://xxx.feishu.cn/drive/folder/xxxxxxxxxxxxx
    3. URL中的 xxxxxxxxxxxxx 就是文件夹Token

示例：
  # 基本用法（导出所有文件）
  python import_from_feishu.py --folder-token FWK2fMleClICfodlHHWc4Mygnhb
  
  # 只导出文档类型
  python import_from_feishu.py --folder-token <Token> --file-types docx
  
提示：
  💡 如果代码中设置了 FOLDER_TOKEN，命令行参数会被忽略
        """
    )
    parser.add_argument(
        "--folder-token",
        required=FOLDER_TOKEN is None,  # 如果代码中已设置，则命令行参数可选
        default=FOLDER_TOKEN,
        help="飞书文件夹 token（如果代码中已设置 FOLDER_TOKEN，此参数可选）"
    )
    parser.add_argument(
        "--folder-name",
        default=FOLDER_NAME,
        help="文件夹名称（可选，用于日志显示）"
    )
    parser.add_argument(
        "--output-dir",
        default="data/feishu_import",
        help="输出目录（默认: data/feishu_import）"
    )
    parser.add_argument(
        "--app-id",
        help="飞书应用 ID（如果不提供，从环境变量读取）"
    )
    parser.add_argument(
        "--app-secret",
        help="飞书应用密钥（如果不提供，从环境变量读取）"
    )
    parser.add_argument(
        "--file-types",
        nargs="+",
        choices=["docx", "sheet", "bitable", "file"],
        help="指定要导出的文件类型（可多选：docx sheet bitable file）"
    )
    parser.add_argument(
        "--include",
        nargs="+",
        help="包含的文件名模式（支持正则表达式，可多个）"
    )
    parser.add_argument(
        "--exclude",
        nargs="+",
        help="排除的文件名模式（支持正则表达式，可多个）"
    )
    parser.add_argument(
        "--files",
        nargs="+",
        help="指定要导出的文件名列表（精确匹配，可多个）"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="安静模式：减少逐文件日志输出，只显示汇总与错误信息"
    )
    
    args = parser.parse_args()
    
    # 获取文件夹Token（优先使用代码中的配置）
    folder_token = FOLDER_TOKEN or args.folder_token
    folder_name = FOLDER_NAME or args.folder_name
    
    if not folder_token:
        print("❌ 错误: 需要指定文件夹Token")
        print("   方式1: 通过命令行参数 --folder-token <Token>")
        print("   方式2: 修改代码中的 FOLDER_TOKEN 变量")
        print("   方式3: 通过飞书网页版获取Token（查看URL中的folder参数）")
        return 1
    
    # 获取应用凭证
    app_id = args.app_id or os.getenv("FEISHU_APP_ID")
    app_secret = args.app_secret or os.getenv("FEISHU_APP_SECRET")
    
    if not app_id or not app_secret:
        print("❌ 错误: 需要提供 FEISHU_APP_ID 和 FEISHU_APP_SECRET")
        print("   方式1: 通过命令行参数 --app-id 和 --app-secret")
        print("   方式2: 通过环境变量 FEISHU_APP_ID 和 FEISHU_APP_SECRET")
        return 1
    
    # 使用 FILTER_CONFIG 作为默认值，命令行参数可以覆盖
    file_types = args.file_types or FILTER_CONFIG["file_types"]
    include_patterns = args.include or FILTER_CONFIG["include_patterns"]
    exclude_patterns = args.exclude or FILTER_CONFIG["exclude_patterns"]
    file_names = args.files or FILTER_CONFIG["file_names"]
    
    # 显示使用的配置
    print("=" * 60)
    print("📋 导出配置:")
    has_filter = any([file_types, include_patterns, exclude_patterns, file_names])
    if has_filter:
        print("   🔍 已设置过滤条件，将只导出符合条件的文件:")
        if file_types:
            print(f"      - 文件类型: {file_types}")
        if include_patterns:
            print(f"      - 包含模式: {include_patterns}")
        if exclude_patterns:
            print(f"      - 排除模式: {exclude_patterns}")
        if file_names:
            print(f"      - 指定文件: {file_names}")
    else:
        print("   ✅ 未设置过滤条件，将导出文件夹下的所有文件")
    print("=" * 60)
    if has_filter:
        print("💡 提示: 要导出所有文件，请将 FILTER_CONFIG 中的所有值设为 None")
    print()
    
    # 创建导入器
    importer = FeishuFileImporter(
        app_id=app_id,
        app_secret=app_secret,
        output_dir=args.output_dir,
        preserve_format=True,
        convert_pdf_to_txt=True,
        verbose=not args.quiet,
    )
    
    # 执行导入
    result = importer.import_folder(
        folder_token=folder_token,
        folder_name=folder_name,
        file_types=file_types,
        include_patterns=include_patterns,
        exclude_patterns=exclude_patterns,
        file_names=file_names,
        rel_dir=None,
    )
    
    if result["success"]:
        print("\n💡 下一步:")
        print("   1. 检查导入的文件")
        print("   2. 运行处理脚本: python tools/processing/ingestion/pr_multi_format_preprocessing.py")
        return 0
    else:
        print(f"\n❌ 导入失败: {result.get('error')}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

