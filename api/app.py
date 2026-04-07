# coding=utf-8
from __future__ import annotations

import os
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from trendradar.api.db import (
    list_date_dirs,
    list_reports_by_date,
    read_report,
    search_reports,
)


class HealthResponse(BaseModel):
    ok: bool
    service: str


class ReportSummary(BaseModel):
    date: str
    times: List[str]


class ReportContentResponse(BaseModel):
    date: Optional[str] = None
    time: Optional[str] = None
    path: str
    content: str


class SearchResult(BaseModel):
    date: str
    time: str
    filename: str
    path: str
    snippet: str


app = FastAPI(
    title="TrendRadar Plugin API",
    description="给扣子智能体使用的 TrendRadar HTTP API",
    version="1.0.0",
)

# 为了后面调试方便，先放开 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["system"])
def root():
    return {
        "message": "TrendRadar Plugin API is running.",
        "docs": "/docs",
        "openapi": "/openapi.json",
    }


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health():
    return HealthResponse(ok=True, service="trendradar-plugin-api")


@app.get("/reports/dates", response_model=List[ReportSummary], tags=["reports"])
def get_report_dates(limit: int = Query(30, ge=1, le=365)):
    """
    获取最近有哪些日期有报告。
    """
    result: List[ReportSummary] = []
    for date in list_date_dirs(limit=limit):
        reports = list_reports_by_date(date)
        result.append(
            ReportSummary(
                date=date,
                times=[item["time"] for item in reports],
            )
        )
    return result


@app.get("/reports/latest", response_model=ReportContentResponse, tags=["reports"])
def get_latest_report(
    mode: str = Query("daily", description="daily 或 current"),
    as_text: bool = Query(True, description="true 返回纯文本，false 返回原始 HTML"),
):
    """
    获取最新报告内容。
    """
    try:
        data = read_report(mode=mode)
        return ReportContentResponse(
            path=data["path"],
            content=data["text"] if as_text else data["html"],
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.get("/reports/content", response_model=ReportContentResponse, tags=["reports"])
def get_report_content(
    date: str = Query(..., description="格式：YYYY-MM-DD"),
    time: str = Query(..., description="格式：HH-MM"),
    as_text: bool = Query(True, description="true 返回纯文本，false 返回原始 HTML"),
):
    """
    获取某一天某个时间点的报告内容。
    """
    try:
        data = read_report(date=date, time=time)
        return ReportContentResponse(
            date=date,
            time=time,
            path=data["path"],
            content=data["text"] if as_text else data["html"],
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.get("/reports/search", response_model=List[SearchResult], tags=["reports"])
def search_report_content(
    keyword: str = Query(..., description="搜索关键词"),
    days: int = Query(7, ge=1, le=365, description="搜索最近多少天"),
    limit: int = Query(20, ge=1, le=100, description="最多返回多少条"),
):
    """
    在最近 N 天报告里搜索关键词。
    """
    return [
        SearchResult(**item)
        for item in search_reports(keyword=keyword, days=days, limit=limit)
    ]


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("trendradar.api.app:app", host="0.0.0.0", port=port, reload=False)
