from __future__ import annotations

from fastapi import APIRouter, Query

from app.schemas.common import PeriodEnum
from app.schemas.dispatch import DispatchOptimizeRequest, DispatchOptimizeResponse, DispatchStatusResponse
from app.services.mock_data import build_dispatch_optimize_response, build_dispatch_status


router = APIRouter()


@router.get(
    "/dispatch/status",
    response_model=DispatchStatusResponse,
    summary="Get Dispatch Status / 获取调度供需状态",
    description="Return per-site supply and demand status for the selected period. Current response is mock data. / 返回指定时段各站点供需状态，当前为占位数据。",
)
def get_dispatch_status(period: PeriodEnum = Query(..., description="Dispatch period: morning, noon, evening. / 调度时段：morning、noon、evening。")) -> DispatchStatusResponse:
    return DispatchStatusResponse(**build_dispatch_status(period))


@router.post(
    "/dispatch/optimize",
    response_model=DispatchOptimizeResponse,
    summary="Optimize Dispatch Routes / 调度路径优化",
    description="Run the dispatch optimization stub and optionally return a process run id for visualization. / 运行调度优化占位逻辑，并可返回过程可视化所需的运行 ID。",
)
def optimize_dispatch(payload: DispatchOptimizeRequest) -> DispatchOptimizeResponse:
    return DispatchOptimizeResponse(**build_dispatch_optimize_response(payload.period, payload.algorithm_type, payload.include_process))
