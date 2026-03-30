from __future__ import annotations

from fastapi import APIRouter

from app.schemas.siting import SitingEvaluateRequest, SitingEvaluateResponse, SitingOptimizeRequest, SitingOptimizeResponse
from app.services.mock_data import build_siting_evaluate_response, build_siting_optimize_response


router = APIRouter()


@router.post(
    "/siting/optimize",
    response_model=SitingOptimizeResponse,
    summary="Optimize Siting Layout / 智能选址优化",
    description="Run the siting optimization stub and optionally return a process run id for visualization. / 运行选址优化占位逻辑，并可返回过程可视化所需的运行 ID。",
)
def optimize_siting(payload: SitingOptimizeRequest) -> SitingOptimizeResponse:
    return SitingOptimizeResponse(**build_siting_optimize_response(payload.algorithm_type, payload.target_sites_count, payload.service_radius, payload.include_process))


@router.post(
    "/siting/evaluate",
    response_model=SitingEvaluateResponse,
    summary="Evaluate Manual Siting / 人工选址评估",
    description="Evaluate a manually edited siting plan and return stubbed coverage results. / 对人工编辑的选址方案进行评估，返回占位覆盖结果。",
)
def evaluate_siting(payload: SitingEvaluateRequest) -> SitingEvaluateResponse:
    return SitingEvaluateResponse(**build_siting_evaluate_response(payload.current_sites))
