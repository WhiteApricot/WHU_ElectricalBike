from __future__ import annotations


def evaluate_manual_sites(current_sites: list) -> dict:
    """人工选址评估入口函数。

    预期功能：
    - 接收前端当前手动调整后的停车点列表。
    - 重新计算覆盖范围、覆盖率、平均步行距离、均衡性等指标。
    - 返回与人工选址评估接口兼容的结果。

    输入参数：
    - `current_sites: list`
      当前停车点列表。
      列表元素应与 `SiteInput` 结构兼容，建议至少包含：
      - `site_id`
      - `name`
      - `latitude`
      - `longitude`
      - `capacity`

    返回值格式：
    - 返回 `dict`
    - 字段应与 `SitingEvaluateResponse` 兼容，至少包含：
      - `status: str`
      - `evaluated_sites_count: int`
      - `coverage_areas: GeoJSON FeatureCollection`
      - `global_metrics: dict`
    """
    raise NotImplementedError('人工选址评估逻辑尚未实现。')
