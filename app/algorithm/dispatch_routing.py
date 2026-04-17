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

#GA参数
GA_POPULATION_SIZE = 40
GA_GENERATIONS = 80
GA_MUTATION_RATE = 0.15
GA_ELITE_SIZE = 4
UNMET_PENALTY_PER_BIKE = 50.0

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


def _prepare_supply_and_deficit(stations: list[dict]) -> tuple[list[dict], list[dict]]:
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

    return surplus_sites, deficit_sites


def _decode_dispatch_order(
    deficit_order: list[int],
    surplus_sites: list[dict],
    deficit_sites: list[dict],
) -> tuple[list[dict], dict]:
    """
    根据“缺车点处理顺序”解码出完整调度方案。
    这是 GA 的核心解码器。
    """
    working_surplus = [
        {**s, "surplus": int(s["surplus"])}
        for s in surplus_sites
    ]

    transfer_plan = []
    total_distance = 0.0
    total_bikes = 0
    unmet_bikes = 0

    for deficit_idx in deficit_order:
        deficit = deficit_sites[deficit_idx]
        need = int(deficit["deficit"])

        while need > 0 and any(s["surplus"] > 0 for s in working_surplus):
            available_surplus = [s for s in working_surplus if s["surplus"] > 0]

            # 这里不是纯最近邻，而是让解码器在当前状态下动态选择
            chosen = min(
                available_surplus,
                key=lambda s: haversine_distance(
                    s["x"], s["y"],
                    deficit["x"], deficit["y"]
                )
            )

            move_bikes = min(need, chosen["surplus"])
            distance = haversine_distance(
                chosen["x"], chosen["y"],
                deficit["x"], deficit["y"]
            )

            transfer_plan.append({
                "from_site_id": chosen["site_id"],
                "from_site_name": chosen["site_name"],
                "to_site_id": deficit["site_id"],
                "to_site_name": deficit["site_name"],
                "bikes": move_bikes,
                "distance": round(distance, 2),
            })

            total_distance += distance
            total_bikes += move_bikes
            chosen["surplus"] -= move_bikes
            need -= move_bikes

        if need > 0:
            unmet_bikes += need

    estimated_cost = total_distance * DEFAULT_UNIT_COST_PER_METER
    fitness = -(total_distance + estimated_cost + unmet_bikes * UNMET_PENALTY_PER_BIKE)

    metrics = {
        "total_distance": round(total_distance, 2),
        "total_transfer_bikes": int(total_bikes),
        "estimated_cost": round(estimated_cost, 2),
        "unmet_bikes": int(unmet_bikes),
        "fitness": round(fitness, 4),
    }

    return transfer_plan, metrics


def _initialize_dispatch_population(deficit_count: int, population_size: int) -> list[list[int]]:
    import random

    base = list(range(deficit_count))
    population = []

    for _ in range(population_size):
        chromosome = base[:]
        random.shuffle(chromosome)
        population.append(chromosome)

    return population


def _tournament_select(scored_population: list[tuple[list[int], float]], k: int = 3) -> list[int]:
    import random

    group = random.sample(scored_population, min(k, len(scored_population)))
    group.sort(key=lambda x: x[1], reverse=True)
    return group[0][0][:]


def _order_crossover(parent1: list[int], parent2: list[int]) -> list[int]:
    import random

    n = len(parent1)
    if n <= 1:
        return parent1[:]

    left = random.randint(0, n - 1)
    right = random.randint(left, n - 1)

    child = [-1] * n
    child[left:right + 1] = parent1[left:right + 1]

    fill_values = [x for x in parent2 if x not in child]
    fill_idx = 0
    for i in range(n):
        if child[i] == -1:
            child[i] = fill_values[fill_idx]
            fill_idx += 1

    return child


def _mutate_order(chromosome: list[int], mutation_rate: float) -> list[int]:
    import random

    chromosome = chromosome[:]
    if len(chromosome) <= 1:
        return chromosome

    if random.random() < mutation_rate:
        i, j = random.sample(range(len(chromosome)), 2)
        chromosome[i], chromosome[j] = chromosome[j], chromosome[i]

    return chromosome


def _run_dispatch_genetic_algorithm(surplus_sites: list[dict], deficit_sites: list[dict]) -> dict:
    if not deficit_sites:
        return {
            "best_order": [],
            "transfer_plan": [],
            "metrics": {
                "total_distance": 0.0,
                "total_transfer_bikes": 0,
                "estimated_cost": 0.0,
                "unmet_bikes": 0,
                "fitness": 0.0,
            },
            "iterations": [],
        }

    population = _initialize_dispatch_population(
        deficit_count=len(deficit_sites),
        population_size=GA_POPULATION_SIZE,
    )

    best_order = None
    best_transfer_plan = []
    best_metrics = None
    best_fitness = float("-inf")
    iterations = []

    for generation in range(GA_GENERATIONS):
        scored_population = []

        for chromosome in population:
            transfer_plan, metrics = _decode_dispatch_order(
                deficit_order=chromosome,
                surplus_sites=surplus_sites,
                deficit_sites=deficit_sites,
            )
            fitness = metrics["fitness"]
            scored_population.append((chromosome, fitness, transfer_plan, metrics))

        scored_population.sort(key=lambda x: x[1], reverse=True)

        if scored_population[0][1] > best_fitness:
            best_order = scored_population[0][0][:]
            best_transfer_plan = scored_population[0][2]
            best_metrics = scored_population[0][3]
            best_fitness = scored_population[0][1]

        iterations.append({
            "generation": generation + 1,
            "best_fitness": round(scored_population[0][1], 4),
            "total_distance": scored_population[0][3]["total_distance"],
            "unmet_bikes": scored_population[0][3]["unmet_bikes"],
        })

        next_population = [item[0][:] for item in scored_population[:GA_ELITE_SIZE]]

        while len(next_population) < GA_POPULATION_SIZE:
            parent1 = _tournament_select([(x[0], x[1]) for x in scored_population])
            parent2 = _tournament_select([(x[0], x[1]) for x in scored_population])

            child = _order_crossover(parent1, parent2)
            child = _mutate_order(child, GA_MUTATION_RATE)
            next_population.append(child)

        population = next_population

    return {
        "best_order": best_order or [],
        "transfer_plan": best_transfer_plan,
        "metrics": best_metrics or {
            "total_distance": 0.0,
            "total_transfer_bikes": 0,
            "estimated_cost": 0.0,
            "unmet_bikes": 0,
            "fitness": 0.0,
        },
        "iterations": iterations,
    }


def _match_supply_and_demand(stations: list[dict]) -> tuple[list[dict], dict, list[dict]]:
    """
    GA 版调度优化：
    - 染色体：缺车点处理顺序
    - 解码：按顺序从余车点分配车辆
    """
    surplus_sites, deficit_sites = _prepare_supply_and_deficit(stations)

    ga_result = _run_dispatch_genetic_algorithm(
        surplus_sites=surplus_sites,
        deficit_sites=deficit_sites,
    )

    transfer_plan = ga_result["transfer_plan"]
    metrics = {
        "total_distance": ga_result["metrics"]["total_distance"],
        "total_transfer_bikes": ga_result["metrics"]["total_transfer_bikes"],
        "estimated_cost": ga_result["metrics"]["estimated_cost"],
        "unmet_bikes": ga_result["metrics"]["unmet_bikes"],
    }

    return transfer_plan, metrics, ga_result["iterations"]


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
    iterations = result.get("iterations", [])

    if iterations:
        return [
            {
                "iteration": item["generation"],
                "stage_name": f'generation_{item["generation"]}',
                "metrics": {
                    "best_fitness": item["best_fitness"],
                    "total_distance": item["total_distance"],
                    "unmet_bikes": item["unmet_bikes"],
                },
                "artifacts": {},
            }
            for item in iterations
        ]

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
    algorithm_type = str(algorithm_type).upper()

    if period not in {"morning", "noon", "evening"}:
        raise ValueError("period 必须为 morning / noon / evening")

    if algorithm_type != "GA":
        raise ValueError("当前正式实现仅支持 GA，ACO 暂未实现")

    stations = build_site_status(period=period, site_count=12)
    transfer_plan, efficiency_metrics, iterations = _match_supply_and_demand(stations)
    dispatch_routes = _build_dispatch_routes(transfer_plan, stations)

    # 回填站点 inbound / outbound
    station_map = {s["site_id"]: s for s in stations}
    for item in transfer_plan:
        station_map[item["from_site_id"]]["outbound"] += item["bikes"]
        station_map[item["to_site_id"]]["inbound"] += item["bikes"]

    response = {
        "status": "success",
        "period": period,
        "algorithm_type": algorithm_type,
        "stations": stations,
        "dispatch_routes": dispatch_routes,
        "transfer_plan": transfer_plan,
        "efficiency_metrics": efficiency_metrics,
        "iterations": iterations,
        "process_available": include_process,
        "run_id": None,
        "process_summary": {
            "total_generations": len(iterations),
            "total_stations": len(stations),
            "total_transfer_tasks": len(transfer_plan),
        } if include_process else None,
    }

    if include_process:
        response["process_states"] = build_dispatch_process_states(response)

    return response