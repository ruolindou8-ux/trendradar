import re
import json
from fastapi import FastAPI, HTTPException
from .db import read_report

app = FastAPI(title="TrendRadar Plugin API")


@app.get("/")
async def root():
    return {
        "message": "TrendRadar Plugin API is running.",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }


def parse_report_text(raw_text: str):
    items = []
    current_source = None
    current_source_name = None

    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue

        # 来源行：toutiao | 今日头条
        source_match = re.match(r"^([a-zA-Z0-9_]+)\s*\|\s*(.+)$", line)
        if source_match:
            current_source = source_match.group(1).strip()
            current_source_name = source_match.group(2).strip()
            continue

        # 新闻行：1. 标题 [URL:https://...]
        item_match = re.match(r"^(\d+)\.\s*(.*?)\s*\[URL:(https?://.+?)\]\s*$", line)
        if item_match:
            items.append({
                "source": current_source,
                "source_name": current_source_name,
                "rank": int(item_match.group(1)),
                "title": item_match.group(2).strip(),
                "url": item_match.group(3).strip()
            })

    return items


def extract_content(report):
    # 如果 report 本身是字符串，先尝试按 JSON 解析
    if isinstance(report, str):
        try:
            report = json.loads(report)
        except Exception:
            return report

    # report = {"file_name": "...", "content": "..."}
    if isinstance(report, dict):
        content = report.get("content")
        if isinstance(content, str):
            return content

        # report = {"code":200, "message":"success", "data": {...}}
        data = report.get("data")
        if isinstance(data, str):
            return data
        if isinstance(data, dict):
            content = data.get("content")
            if isinstance(content, str):
                return content

    return ""


@app.get("/reports/latest")
async def get_latest_report():
    try:
        report = read_report()

        if not report:
            raise HTTPException(
                status_code=404,
                detail="未找到报告文件，请检查 output 目录"
            )

        raw_text = extract_content(report)
        if not raw_text:
            return []

        items = parse_report_text(raw_text)
        return items

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"[ERROR] 接口异常: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"服务器内部错误: {str(e)}"
        )
