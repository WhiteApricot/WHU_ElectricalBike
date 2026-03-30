# WHU Electrical Bike Backend

本仓库已经补充了一套可运行的 FastAPI 后端基础环境，用于武汉大学校园电单车 WebGIS 系统的后端联调与后续算法接入。

当前阶段目标：

- 搭建统一的 FastAPI 服务入口
- 挂出接口文档中已有的后端接口
- 直接复用本地校园 GeoJSON 数据
- 为尚未实现的算法接口提供结构正确的 mock/stub 返回
- 补充本地方案存储接口，便于联调与后续扩展
- 方便前端先行联调，后续再逐步替换为真实算法服务

## 当前能力

- FastAPI 应用基础启动
- 统一使用 `/api` 路由前缀
- 健康检查接口：`GET /health`
- 校园基础空间数据接口读取本地 GeoJSON
- 热力图、选址、评估、调度、分析、导出接口已注册
- 新增方案保存、列表、详情、删除接口
- 算法相关接口目前返回占位结果，便于前端调试
- `/docs` 文档中的接口摘要与说明已补充中英文

## 运行方式

安装依赖：

```bash
pip install -r requirements.txt
```

启动服务：

```bash
python run.py
```

启动后可访问：

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/redoc`
- `http://127.0.0.1:8000/health`

## 已注册接口

- `GET /api/campus/base-data`
- `GET /api/demand/heatmap`
- `POST /api/siting/optimize`
- `POST /api/siting/evaluate`
- `GET /api/dispatch/status`
- `POST /api/dispatch/optimize`
- `GET /api/analysis/metrics`
- `GET /api/schemes`
- `POST /api/schemes`
- `GET /api/schemes/{scheme_id}`
- `DELETE /api/schemes/{scheme_id}`
- `POST /api/export/scheme`

说明：

- 基础空间数据接口读取 `whu_spatial_data` 下的本地 GeoJSON
- 算法相关接口仍为 mock/stub，占位但格式可用于联调
- 方案存储接口使用本地文件保存到 `whu_spatial_data/schemes`
- 方案存储层已抽象出仓储接口，后续可迁移到数据库

## 本次后端文件结构

```text
WHU_ElectricalBike/
├─ app/
│  ├─ __init__.py
│  ├─ main.py
│  ├─ api/
│  │  ├─ __init__.py
│  │  ├─ router.py
│  │  └─ endpoints/
│  │     ├─ __init__.py
│  │     ├─ analysis.py
│  │     ├─ campus.py
│  │     ├─ demand.py
│  │     ├─ dispatch.py
│  │     ├─ export.py
│  │     ├─ scheme.py
│  │     └─ siting.py
│  ├─ core/
│  │  ├─ __init__.py
│  │  └─ config.py
│  ├─ schemas/
│  │  ├─ __init__.py
│  │  ├─ analysis.py
│  │  ├─ campus.py
│  │  ├─ common.py
│  │  ├─ demand.py
│  │  ├─ dispatch.py
│  │  ├─ export.py
│  │  ├─ scheme.py
│  │  └─ siting.py
│  └─ services/
│     ├─ __init__.py
│     ├─ data_loader.py
│     ├─ mock_data.py
│     └─ scheme_storage.py
├─ requirements.txt
├─ run.py
└─ README.md
```

## 各文件作用与待开发内容

### 根目录文件

#### `requirements.txt`

当前作用：

- 定义后端运行所需的基础依赖
- 目前包含 `fastapi`、`uvicorn`、`pydantic`

后续待开发：

- 如果后端后续引入数据库、日志、GIS 计算或任务队列，需要在这里补充依赖
- 例如 `sqlalchemy`、`geoalchemy2`、`geopandas`、`celery`、`redis` 等

#### `run.py`

当前作用：

- 本地开发启动入口
- 使用 `uvicorn` 启动 `app.main:app`

后续待开发：

- 可补充开发环境/生产环境配置切换
- 可增加端口、host、reload 等环境变量控制

#### `README.md`

当前作用：

- 说明项目用途、启动方式、目录结构与当前实现状态

后续待开发：

- 接入真实算法后补充请求示例、响应示例、部署方式、联调说明

### `app` 包

#### `app/__init__.py`

当前作用：

- 将 `app` 目录标记为 Python 包

后续待开发：

- 一般不需要额外逻辑，保持为空即可

#### `app/main.py`

当前作用：

- 创建 FastAPI 应用实例
- 注册 CORS 中间件
- 注册统一 `/api` 路由前缀
- 提供根路径 `/` 和健康检查 `/health`
- 配置 OpenAPI 标签与中英文接口说明

后续待开发：

- 增加统一异常处理
- 增加日志中间件、请求追踪、鉴权中间件
- 增加生命周期事件，例如模型预热、数据库连接初始化

### `app/core`

#### `app/core/__init__.py`

当前作用：

- 标记 `core` 为包

后续待开发：

- 无特殊需求时保持为空

#### `app/core/config.py`

当前作用：

- 集中管理应用名称、版本、路由前缀、数据目录、方案存储目录等基础配置
- 明确当前存储后端为本地文件，便于后续迁移数据库

后续待开发：

- 可改造成读取 `.env` 的配置系统
- 可加入数据库连接、Redis、文件存储、日志等级等配置项

### `app/api`

#### `app/api/__init__.py`

当前作用：

- 标记 `api` 为包

后续待开发：

- 一般无需修改

#### `app/api/router.py`

当前作用：

- 聚合所有业务路由
- 统一挂载校园数据、需求热力图、选址、调度、分析、方案存储、导出接口

后续待开发：

- 如果接口继续增多，可以按业务域继续细分

### `app/api/endpoints`

#### `app/api/endpoints/__init__.py`

当前作用：

- 标记 `endpoints` 为包

后续待开发：

- 一般无需修改

#### `app/api/endpoints/campus.py`

当前作用：

- 提供校园基础空间数据接口
- 调用本地 GeoJSON 数据加载服务

后续待开发：

- 可增加图层筛选、字段精简、空间范围裁剪
- 可增加简化模式，避免大 GeoJSON 一次性返回过大

#### `app/api/endpoints/demand.py`

当前作用：

- 提供需求热力图接口
- 当前按 `period` 返回 mock 热力点

后续待开发：

- 对接真实需求预测或历史轨迹分析结果
- 结合时间、日期、天气等条件输出动态热力数据

#### `app/api/endpoints/siting.py`

当前作用：

- 提供智能选址接口与人工选址评估接口
- 当前返回可视化需要的占位 GeoJSON 和指标数据

后续待开发：

- 对接 GA、PSO、ACO、NSGA-II 等真实选址算法
- 输出真实停车点、覆盖圈、覆盖率、平均步行距离等指标
- 为人工选址评估补充实时重算逻辑

#### `app/api/endpoints/dispatch.py`

当前作用：

- 提供调度状态查询和调度优化接口
- 当前返回模拟供需状态、模拟调度路径与指标

后续待开发：

- 对接需求预测模型
- 对接车辆调度路径优化算法
- 输出真实调度路线、转运方案、效率指标

#### `app/api/endpoints/analysis.py`

当前作用：

- 提供分析图表数据接口
- 当前返回 mock 图表数据结构

后续待开发：

- 基于真实选址/调度方案生成统计分析结果
- 按方案 ID 查询历史分析结果

#### `app/api/endpoints/scheme.py`

当前作用：

- 提供方案列表、保存、详情、删除接口
- 当前采用本地文件存储方案数据
- 为未来迁移数据库保留了统一仓储层入口

后续待开发：

- 增加方案更新接口
- 增加按类型、名称、日期筛选
- 与分析、导出、前端历史记录联动

#### `app/api/endpoints/export.py`

当前作用：

- 提供方案导出接口
- 当前支持将前端传入的方案数据导出为 CSV 或 GeoJSON

后续待开发：

- 增加更规范的导出字段映射
- 支持多种导出模板
- 支持直接导出系统内已保存的方案

### `app/schemas`

#### `app/schemas/__init__.py`

当前作用：

- 标记 `schemas` 为包

后续待开发：

- 一般无需修改

#### `app/schemas/common.py`

当前作用：

- 定义公共枚举，目前包含 `period` 和 `scheme_type`

后续待开发：

- 可补充算法类型、导出格式、状态码等通用枚举

#### `app/schemas/campus.py`

当前作用：

- 定义校园基础空间数据接口的响应模型

后续待开发：

- 如需严格校验 GeoJSON 结构，可进一步细化字段模型

#### `app/schemas/demand.py`

当前作用：

- 定义热力图接口响应模型

后续待开发：

- 可补充时间粒度、数据来源、统计区间等字段

#### `app/schemas/siting.py`

当前作用：

- 定义选址模块的请求与响应模型
- 包含站点输入、选址请求、评估请求等数据结构

后续待开发：

- 可细化站点属性、约束条件、算法参数、评估指标

#### `app/schemas/dispatch.py`

当前作用：

- 定义调度模块的请求与响应模型
- 包含站点状态、调度优化结果等结构

后续待开发：

- 可增加车辆信息、调度批次、时段预测、成本参数等字段

#### `app/schemas/analysis.py`

当前作用：

- 定义分析接口的响应模型

后续待开发：

- 可按图表类型拆分更细粒度的数据模型

#### `app/schemas/export.py`

当前作用：

- 定义导出接口请求模型
- 约束导出格式和文件名等参数

后续待开发：

- 可增加导出模板、方案类型、编码格式等控制项

#### `app/schemas/scheme.py`

当前作用：

- 定义方案保存、列表、详情、删除相关的数据模型
- 统一约束本地存储与后续数据库迁移时的数据结构

后续待开发：

- 可补充用户信息、标签、更新时间范围、方案状态等字段

### `app/services`

#### `app/services/__init__.py`

当前作用：

- 标记 `services` 为包

后续待开发：

- 一般无需修改

#### `app/services/data_loader.py`

当前作用：

- 读取 `whu_spatial_data` 下的本地 GeoJSON
- 使用缓存避免重复读取
- 为基础空间数据接口提供真实数据
- 对缺失数据文件进行基础异常提示

后续待开发：

- 增加格式错误时的异常处理
- 支持多数据源切换，例如本地文件、数据库、对象存储
- 支持数据清洗、字段过滤和坐标系检查

#### `app/services/mock_data.py`

当前作用：

- 集中管理所有占位/mock 数据
- 为热力图、选址、评估、调度、分析、导出接口生成调试用结果

后续待开发：

- 将 mock 逻辑逐步替换为真实算法服务
- 可继续拆分为 `siting_service.py`、`dispatch_service.py`、`analysis_service.py`
- 当算法接入完成后，该文件可只保留测试数据或彻底移除

#### `app/services/scheme_storage.py`

当前作用：

- 定义方案仓储抽象接口
- 实现本地文件存储版本 `FileSchemeRepository`
- 将方案保存到 `whu_spatial_data/schemes`
- 为未来替换为数据库仓储保留兼容结构

后续待开发：

- 增加方案更新能力
- 增加并发写入保护
- 将文件仓储替换或扩展为数据库仓储实现

## 当前建议的后续开发顺序

1. 将接口文档中的路径统一维护为 `/api/...`
2. 明确方案存储的数据字段规范，避免前后端联调时结构漂移
3. 将 `mock_data.py` 中的占位逻辑逐步替换为真实选址与调度服务
4. 当需要方案更新、检索、多人协作时，再引入数据库层替换文件仓储
5. 最后补充鉴权、日志、异常处理和部署配置

