# api/db.py 最终适配版（适配你的真实目录结构）
import json
from pathlib import Path
from typing import List, Dict, Optional

# 项目根目录
PROJECT_ROOT = Path("/home/admin/trendradar")
# 报告根目录
REPORT_PATH = PROJECT_ROOT / "output"

# 读取最新报告（适配html/txt子目录）
def read_report(date_dir: str = None, report_name: str = None) -> Optional[Dict]:
    try:
        # 1. 检查output目录
        if not REPORT_PATH.exists():
            print(f"[ERROR] 报告目录不存在: {REPORT_PATH}")
            return None
        
        # 2. 获取最新日期目录
        if not date_dir:
            date_dirs = sorted([d.name for d in REPORT_PATH.iterdir() if d.is_dir()], reverse=True)
            if not date_dirs:
                print(f"[ERROR] output目录下无日期文件夹: {REPORT_PATH}")
                return None
            date_dir = date_dirs[0]
        
        date_path = REPORT_PATH / date_dir
        if not date_path.exists():
            print(f"[ERROR] 日期目录不存在: {date_path}")
            return None
        
        # 🔥 关键修复：适配你的html/txt子目录，优先找txt里的文件
        txt_path = date_path / "txt"
        if txt_path.exists():
            # 从txt目录找最新的文件
            reports = sorted(txt_path.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True)
        else:
            # 从html目录找
            html_path = date_path / "html"
            reports = sorted(html_path.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True) if html_path.exists() else []
        
        if not reports:
            print(f"[ERROR] {date_path} 目录下无报告文件")
            return None
        
        # 3. 读取最新文件
        report_path = reports[0]
        if not report_path.exists():
            print(f"[ERROR] 报告文件不存在: {report_path}")
            return None
        
        # 4. 读取文件内容（适配txt/json等格式）
        if report_path.suffix == ".json":
            with open(report_path, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            # 非json文件，直接返回文本内容
            with open(report_path, "r", encoding="utf-8") as f:
                return {
                    "file_name": report_path.name,
                    "content": f.read(),
                    "date": date_dir
                }
    except Exception as e:
        print(f"[ERROR] 读取报告失败: {str(e)}")
        return None
