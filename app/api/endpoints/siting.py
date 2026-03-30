from __future__ import annotations

from fastapi import APIRouter

from app.schemas.siting import (
    SitingEvaluateRequest,
    SitingEvaluateResponse,
    SitingOptimizeRequest,
    SitingOptimizeResponse,
)
from app.services.mock_data import (
    build_siting_evaluate_response,
    build_siting_optimize_response,
)


router = APIRouter()


@router.post(
    "/siting/optimize",
    response_model=SitingOptimizeResponse,
    summary="Optimize Siting Layout / 智能选址优化",
    description="Run the siting optimization stub and return GeoJSON-like result structures for frontend testing. / 运行选址优化占位逻辑，返回前端调试所需的 GeoJSON 结构。",
)
def optimize_siting(payload: SitingOptimizeRequest) -> SitingOptimizeResponse:
    return SitingOptimizeResponse(
        **build_siting_optimize_response(
            algorithm_type=payload.algorithm_type,
            target_sites_count=payload.target_sites_count,
            service_radius=payload.service_radius,
        )
    )


@router.post(
    "/siting/evaluate",
    response_model=SitingEvaluateResponse,
    summary="Evaluate Manual Siting / 人工选址评估",
    description="Evaluate a manually edited siting plan and return stubbed coverage results. / 对人工编辑的选址方案进行评估，返回占位覆盖结果。",
)
def evaluate_siting(payload: SitingEvaluateRequest) -> SitingEvaluateResponse:
    return SitingEvaluateResponse(**build_siting_evaluate_response(payload.current_sites))
