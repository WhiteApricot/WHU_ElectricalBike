from __future__ import annotations


def predict_demand(period) -> dict:
    """需求预测算法入口函数。

    预期功能：
    - 根据时间段、历史轨迹、站点状态等信息预测各站点未来需求。
    - 优先通过 `app.algorithm.data_loader` 读取 POI、建筑、路网等基础空间数据。
    - 输出每个站点的当前车辆数、预测需求数、调入/调出建议数量。

    输入参数：
    - `period`
      预测时段。
      当前后端接口中通常为 `morning`、`noon`、`evening` 之一。
      后续也可以扩展为更完整的时间对象。

    返回值格式：
    - 返回 `dict`
    - 字段应与 `DispatchStatusResponse` 兼容，至少包含：
      - `status: str`
      - `period: str`
      - `stations: list[dict]`
    - `stations` 中每个元素建议包含：
      - `site_id`
      - `site_name`
      - `current_bikes`
      - `predicted_demand`
      - `inbound`
      - `outbound`
    """
    raise NotImplementedError('需求预测模型尚未实现。')


def build_prediction_process_states(model_output: dict) -> list[dict]:
    """将预测模型的训练过程或推理过程整理为可视化状态列表。

    预期功能：
    - 将模型训练轮次、损失值变化、时间窗口预测结果等转换为统一结构。
    - 供算法过程接口展示中间状态。

    输入参数：
    - `model_output: dict`
      预测模型内部输出结果，建议包含损失曲线、中间预测帧、阶段性指标等信息。

    返回值格式：
    - 返回 `list[dict]`
    - 每个元素建议包含：
      - `iteration: int`
      - `stage_name: str`
      - `metrics: dict`，例如损失值、准确率、误差等
      - `artifacts: dict`，例如热力图快照、时间窗预测结果
    """
    raise NotImplementedError('需求预测过程状态构建函数尚未实现。')
