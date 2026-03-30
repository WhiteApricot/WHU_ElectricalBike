from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "FastAPI backend skeleton for the WHU campus electrical bike WebGIS project. "
        "Current phase focuses on backend framework, local file storage, and mock responses for algorithm endpoints.\n\n"
        "武汉大学校园电单车 WebGIS 系统后端基础框架。"
        "当前阶段重点为后端基础环境、本地文件存储，以及算法接口的占位返回。"
    ),
    openapi_tags=[
        {"name": "system", "description": "System and health endpoints / 系统与健康检查接口"},
        {"name": "campus", "description": "Campus spatial base data endpoints / 校园空间基础数据接口"},
        {"name": "demand", "description": "Demand heatmap endpoints / 停车需求与热力图接口"},
        {"name": "siting", "description": "Siting and evaluation endpoints / 智能选址与交互评估接口"},
        {"name": "dispatch", "description": "Dispatch and route planning endpoints / 动态调度与路径规划接口"},
        {"name": "analysis", "description": "Analysis and metrics endpoints / 分析与图表接口"},
        {"name": "scheme", "description": "Scheme persistence endpoints / 方案存储管理接口"},
        {"name": "export", "description": "Scheme export endpoints / 方案导出接口"},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_allow_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/", summary="Root / 根路径", tags=["system"])
def read_root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "api_prefix": settings.api_prefix,
        "storage_backend": settings.storage_backend,
    }


@app.get("/health", summary="Health Check / 健康检查", tags=["system"])
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "version": settings.app_version,
        "storage_backend": settings.storage_backend,
    }
