# coding=utf-8
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


def get_output_dir() -> Path:
    """
    TrendRadar 输出目录。
    默认是 output，也可以用环境变量覆盖：
    TRENDRADAR_OUTPUT_DIR=/your/path/output
    """
    return Path(os.getenv("TRENDRADAR_OUTPUT_DIR", "output"))


def ensure_path_exists(path: Path, error_message: str) -> Path:
    if not path.exists():
        raise FileNotFoundError(error_message)
    return path


def html_to_text(html: str) -> str:
    """
    粗略把 HTML 转成纯文本，方便给扣子做语义读取。
    """
    text = re.sub(r"<script[\s\S]*?</script>", "", html, flags=re.IGNORECASE)
    text = re.sub(r"<style[\s\S]*?</style>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def get_latest_report_path(mode: str = "daily") -> Path:
    """
    获取最新报告路径。
    默认读：output/html/latest/daily.html
    也支持 current.html
    """
    latest_path = get_output_dir() / "html" / "latest" / f"{mode}.html"
    return ensure_path_exists(
        latest_path,
        f"没有找到最新报告文件：{latest_path}。请先确认 TrendRadar 已生成 HTML 报告。",
    )


def list_date_dirs(limit: int = 30) -> List[str]:
    """
    列出 output/html 下可用的日期目录，例如：
    2026-04-07
    2026-04-06
    """
    base = get_output_dir() / "html"
    if not base.exists():
        return []

    dates = [
        item.name
        for item in base.iterdir()
        if item.is_dir() and re.fullmatch(r"\d{4}-\d{2}-\d{2}", item.name)
    ]
    return sorted(dates, reverse=True)[:limit]


def list_reports_by_date(date: str) -> List[Dict[str, Any]]:
    """
    列出某一天的所有报告文件。
    """
    day_dir = get_output_dir() / "html" / date
    ensure_path_exists(day_dir, f"没有找到该日期目录：{day_dir}")

    reports: List[Dict[str, Any]] = []
    for file in sorted(day_dir.glob("*.html"), reverse=True):
        if file.stem == "index":
            continue
        if not re.fullmatch(r"\d{2}-\d{2}", file.stem):
            continue

        reports.append(
            {
                "date": date,
                "time": file.stem,
                "filename": file.name,
                "path": str(file),
            }
        )
    return reports


def read_report(
    date: Optional[str] = None,
    time: Optional[str] = None,
    mode: str = "daily",
) -> Dict[str, Any]:
    """
    读取报告。
    1. 如果传 date + time，则读取指定报告
    2. 否则读取 latest/daily.html 或 latest/current.html
    """
    if date and time:
        report_path = get_output_dir() / "html" / date / f"{time}.html"
        ensure_path_exists(report_path, f"没有找到报告文件：{report_path}")
    else:
        report_path = get_latest_report_path(mode=mode)

    html = report_path.read_text(encoding="utf-8", errors="ignore")
    return {
        "path": str(report_path),
        "html": html,
        "text": html_to_text(html),
    }


def search_reports(keyword: str, days: int = 7, limit: int = 20) -> List[Dict[str, Any]]:
    """
    在最近 N 天报告里搜索关键词。
    """
    keyword = keyword.strip()
    if not keyword:
        return []

    matches: List[Dict[str, Any]] = []

    for date in list_date_dirs(limit=days):
        for report in list_reports_by_date(date):
            report_path = Path(report["path"])
            html = report_path.read_text(encoding="utf-8", errors="ignore")
            text = html_to_text(html)

            if keyword.lower() in text.lower():
                match_index = text.lower().find(keyword.lower())
                start = max(0, match_index - 80)
                end = min(len(text), match_index + len(keyword) + 120)
                snippet = text[start:end]

                matches.append(
                    {
                        "date": report["date"],
                        "time": report["time"],
                        "filename": report["filename"],
                        "path": report["path"],
                        "snippet": snippet,
                    }
                )

                if len(matches) >= limit:
                    return matches

    return matches
