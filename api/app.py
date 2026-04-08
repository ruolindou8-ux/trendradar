# api/app.py 中 get_latest_report 接口 最终稳定版
from fastapi import FastAPI, HTTPException
from .db import read_report  # 相对导入，正确写法

app = FastAPI(title="TrendRadar Plugin API")

# 根接口
@app.get("/")
async def root():
    return {
        "message": "TrendRadar Plugin API is running.",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }

# 最新报告接口（完整空值保护+异常捕获）
@app.get("/reports/latest")
async def get_latest_report():
    try:
        # 1. 读取报告
        report = read_report()
        
        # 2. 绝对空值判断：只要是None，直接返回404，绝不执行后续代码
        if not report:
            raise HTTPException(
                status_code=404,
                detail="未找到报告文件，请检查output目录"
            )
        
        # 3. 安全返回数据
        return {
            "code": 200,
            "message": "success",
            "data": report
        }
    except HTTPException as e:
        # 直接抛出HTTP异常，FastAPI自动处理
        raise e
    except Exception as e:
        # 捕获所有其他异常，打印日志，返回500
        print(f"[ERROR] 接口异常: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"服务器内部错误: {str(e)}"
        )