from __future__ import annotations

from app.algorithm.candidate_site_generator import build_candidate_sites
from app.algorithm.demand_prediction import build_demand_points
from app.algorithm.siting_optimization import (
    build_distance_matrix,
    haversine_distance,
)


DEFAULT_SITE_COUNT = 12
DEFAULT_SERVICE_RADIUS = 120.0
DEFAULT_UNIT_COST_PER_METER = 0.02


def _select_reference_sites(period: str, site_count: int = DEFAULT_SITE_COUNT) -> list[dict]:
    """
    第一版调度的站点来源：
    直接从候选站点中，按对应需求点在指定时段的需求强度排序，
    选出前 N 个站点作为“已建设停车点”。
    这是过渡方案，后面可以改成直接读取选址结果。
    """
    demand_points = build_demand_points()
    candidate_sites = build_candidate_sites()

    demand_by_poi = {dp["source_poi_id"]: dp for dp in demand_points}

    scored_sites = []
    for site in candidate_sites:
        dp = demand_by_poi.get(site["source_poi_id"])
        if not dp:
            continue
        scored_sites.append((site, dp["demand"][period]))

    scored_sites.sort(key=lambda x: x[1], reverse=True)
    return [item[0] for item in scored_sites[:site_count]]


def build_site_status(period: str, site_count: int = DEFAULT_SITE_COUNT) -> list[dict]:
    """
    生成某个时段的站点供需状态。
    第一版策略：
    - 站点集合：取需求最高的前 N 个候选点
    - 需求：从 demand_points 中按最近站点聚合
    - 当前车量：基于预测需求做一个偏移，制造“有的缺车、有的余车”的状态
    """
    if period not in {"morning", "noon", "evening"}:
        raise ValueError("period 必须为 morning / noon / evening")

    demand_points = build_demand_points()
    selected_sites = _select_reference_sites(period=period, site_count=site_count)

    distance_matrix = build_distance_matrix(demand_points, selected_sites)

    site_status = []
    for idx, site in enumerate(selected_sites):
        site_status.append({
            "site_id": site["site_id"],
            "site_name": site["name"],
            "x": site["x"],
            "y": site["y"],
            "type": site["type"],
            "predicted_demand": 0,
            "current_bikes": 0,
            "inbound": 0,
            "outbound": 0,
        })

    site_index = {s["site_id"]: s for s in site_status}

    # 把需求点分配到最近站点
    for dp in demand_points:
        nearest_site_id = min(
            distance_matrix[dp["demand_id"]],
            key=distance_matrix[dp["demand_id"]].get
        )
        site_index[nearest_site_id]["predicted_demand"] += int(round(dp["demand"][period]))

    # 生成“当前车量”：让一部分站点余车，一部分站点缺车
    for idx, site in enumerate(site_status):
        demand = site["predicted_demand"]

        # 用固定规则制造早期可调度状态，避免全平衡
        if idx % 3 == 0:
            current_bikes = int(round(demand * 1.25))   # 余车点
        elif idx % 3 == 1:
            current_bikes = int(round(demand * 0.75))   # 缺车点
        else:
            current_bikes = int(round(demand * 0.95))   # 轻微缺/近平衡

        site["current_bikes"] = max(current_bikes, 0)

    return site_status


def _match_supply_and_demand(stations: list[dict]) -> tuple[list[dict], dict]:
    """
    最近邻余缺匹配：
    - surplus: current_bikes > predicted_demand
    - deficit: current_bikes < predicted_demand
    """
    surplus_sites = []
    deficit_sites = []

    for s in stations:
        gap = s["current_bikes"] - s["predicted_demand"]
        if gap > 0:
            surplus_sites.append({
                **s,
                "surplus": gap,
            })
        elif gap < 0:
            deficit_sites.append({
                **s,
                "deficit": -gap,
            })

    transfer_plan = []
    total_distance = 0.0
    total_bikes = 0

    for deficit in deficit_sites:
        need = deficit["deficit"]

        while need > 0 and surplus_sites:
            # 找最近余车点
            nearest = min(
                surplus_sites,
                key=lambda s: haversine_distance(
                    s["x"], s["y"],
                    deficit["x"], deficit["y"]
                )
            )

            move_bikes = min(need, nearest["surplus"])
            distance = haversine_distance(
                nearest["x"], nearest["y"],
                deficit["x"], deficit["y"]
            )

            transfer_plan.append({
                "from_site_id": nearest["site_id"],
                "from_site_name": nearest["site_name"],
                "to_site_id": deficit["site_id"],
                "to_site_name": deficit["site_name"],
                "bikes": move_bikes,
                "distance": round(distance, 2),
            })

            total_distance += distance
            total_bikes += move_bikes

            nearest["surplus"] -= move_bikes
            need -= move_bikes

            if nearest["surplus"] == 0:
                surplus_sites.remove(nearest)

    metrics = {
        "total_distance": round(total_distance, 2),
        "total_transfer_bikes": total_bikes,
        "estimated_cost": round(total_distance * DEFAULT_UNIT_COST_PER_METER, 2),
    }

    return transfer_plan, metrics


def _build_dispatch_routes(transfer_plan: list[dict], stations: list[dict]) -> dict:
    station_map = {s["site_id"]: s for s in stations}

    features = []
    for idx, item in enumerate(transfer_plan, start=1):
        from_site = station_map[item["from_site_id"]]
        to_site = station_map[item["to_site_id"]]

        vehicle_id = f"vehicle_{idx}"

        features.append({
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [from_site["x"], from_site["y"]],
                    [to_site["x"], to_site["y"]],
                ],
            },
            "properties": {
                # 原有字段，继续保留
                "route_id": f"route_{idx}",
                "from_site_id": item["from_site_id"],
                "to_site_id": item["to_site_id"],
                "bikes": item["bikes"],
                "distance": item["distance"],

                # 给成员 C / webmap 用的兼容字段
                "vehicle_id": vehicle_id,
                "from_site": item["from_site_name"],
                "to_site": item["to_site_name"],
                "transfer_count": item["bikes"],
            },
        })

    return {
        "type": "FeatureCollection",
        "features": features,
    }


def build_dispatch_process_states(result: dict) -> list[dict]:
    """
    第一版没有复杂迭代，这里返回 3 个阶段状态，方便前端展示。
    """
    stations = result.get("stations", [])
    transfer_plan = result.get("transfer_plan", [])
    efficiency_metrics = result.get("efficiency_metrics", {})

    return [
        {
            "iteration": 1,
            "stage_name": "build_station_status",
            "metrics": {
                "stations_count": len(stations),
            },
            "artifacts": {},
        },
        {
            "iteration": 2,
            "stage_name": "match_supply_and_demand",
            "metrics": {
                "transfer_tasks": len(transfer_plan),
            },
            "artifacts": {},
        },
        {
            "iteration": 3,
            "stage_name": "build_dispatch_routes",
            "metrics": efficiency_metrics,
            "artifacts": {},
        },
    ]


def run_dispatch_routing(period, algorithm_type: str, include_process: bool = False) -> dict:
    """
    第一版统一入口：
    - 当前先接受 ACO / GA 名义参数
    - 实际统一走“最近邻余缺匹配”逻辑
    """
    period = str(period)

    if period not in {"morning", "noon", "evening"}:
        raise ValueError("period 必须为 morning / noon / evening")

    stations = build_site_status(period=period, site_count=12)
    transfer_plan, efficiency_metrics = _match_supply_and_demand(stations)
    dispatch_routes = _build_dispatch_routes(transfer_plan, stations)

    # 回填站点 inbound / outbound
    station_map = {s["site_id"]: s for s in stations}
    for item in transfer_plan:
        station_map[item["from_site_id"]]["outbound"] += item["bikes"]
        station_map[item["to_site_id"]]["inbound"] += item["bikes"]

    response = {
        "status": "success",
        "period": period,
        "algorithm_type": algorithm_type.upper(),
        "stations": stations,
        "dispatch_routes": dispatch_routes,
        "transfer_plan": transfer_plan,
        "efficiency_metrics": efficiency_metrics,
        "process_available": include_process,
        "run_id": None,
        "process_summary": {
            "total_stations": len(stations),
            "total_transfer_tasks": len(transfer_plan),
        } if include_process else None,
    }

    if include_process:
        response["process_states"] = build_dispatch_process_states(response)

    return response