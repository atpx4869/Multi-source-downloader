# API 接口使用指南

## 概述

本项目提供了一个统一的 API 接口框架，用于访问三个标准源：
- **BY**: 标院内网系统
- **ZBY**: 正规宝
- **GBW**: GB/T 网

## 快速开始

### 基础用法

```python
from api import APIRouter, SourceType

# 创建路由器
router = APIRouter()

# 搜索标准
results = router.search_all("GB/T 3324-2024", limit=5)

# 从特定源下载
response = router.download(
    SourceType.ZBY,
    "GB/T 3324-2024",
    output_dir="downloads"
)

# 检查源的健康状态
health = router.check_health()
```

## API 文档

### APIRouter

主要的路由类，用于管理和编排多个源。

#### 初始化

```python
router = APIRouter(
    output_dir: str = "downloads",
    enable_sources: Optional[List[str]] = None
)
```

参数：
- `output_dir`: 下载文件的输出目录
- `enable_sources`: 启用的源列表，如 `["BY", "ZBY", "GBW"]`，默认为全部

#### 搜索功能

##### 在单个源中搜索

```python
response = router.search_single(
    source: SourceType,
    query: str,
    limit: int = 100
) -> SearchResponse
```

示例：
```python
response = router.search_single(SourceType.ZBY, "GB/T 3324-2024")
print(f"找到 {response.count} 个结果")
for std in response.standards:
    print(f"  {std.std_no}: {std.name}")
```

##### 在所有源中搜索

```python
results = router.search_all(
    query: str,
    limit: int = 100
) -> Dict[SourceType, SearchResponse]
```

示例：
```python
results = router.search_all("GB/T 3324")
for source_type, response in results.items():
    print(f"{source_type.value}: {response.count} 个结果")
```

### 下载功能

##### 从指定源下载

```python
response = router.download(
    source: SourceType,
    std_no: str,
    output_dir: Optional[str] = None,
    progress_callback: Optional[Callable] = None
) -> DownloadResponse
```

参数：
- `source`: 源类型
- `std_no`: 标准编号
- `output_dir`: 输出目录（可选，默认使用初始化时的目录）
- `progress_callback`: 进度回调函数，接收日志消息

示例：
```python
def on_progress(msg):
    print(f"进度: {msg}")

response = router.download(
    SourceType.ZBY,
    "GB/T 3324-2024",
    progress_callback=on_progress
)

if response.status == DownloadStatus.SUCCESS:
    print(f"下载完成: {response.filepath}")
else:
    print(f"下载失败: {response.error}")
```

##### 从第一个可用的源下载

```python
response = router.download_first_available(
    std_no: str,
    output_dir: Optional[str] = None,
    progress_callback: Optional[Callable] = None
) -> DownloadResponse
```

自动按优先级（GBW > BY > ZBY）尝试各源。

示例：
```python
response = router.download_first_available("GB/T 3324-2024")
if response.status == DownloadStatus.SUCCESS:
    print(f"从 {response.source.value} 下载成功")
```

### 健康检查

```python
health = router.check_health() -> HealthResponse
```

示例：
```python
health = router.check_health()
if health.all_healthy:
    print("所有源都可用")
else:
    for source_health in health.sources:
        if not source_health.available:
            print(f"{source_health.source.value}: {source_health.error}")
```

## 数据模型

### SourceType（枚举）

源类型：`BY`, `ZBY`, `GBW`

### DownloadStatus（枚举）

下载状态：
- `SUCCESS`: 成功
- `FAILED`: 失败
- `IN_PROGRESS`: 进行中
- `NOT_FOUND`: 未找到
- `ERROR`: 错误

### StandardInfo

标准信息模型：
```python
@dataclass
class StandardInfo:
    std_no: str                    # 标准编号
    name: str                      # 标准名称
    source: SourceType             # 源
    has_pdf: bool                  # 是否有PDF
    publish_date: Optional[str]    # 发布日期
    implement_date: Optional[str]  # 实施日期
    status: Optional[str]          # 状态
    source_meta: Dict              # 源特定的元数据
```

### SearchResponse

搜索响应模型：
```python
@dataclass
class SearchResponse:
    source: SourceType             # 源
    query: str                     # 搜索词
    count: int                     # 找到的标准数量
    standards: List[StandardInfo]  # 搜索结果
    error: Optional[str]           # 错误信息
    elapsed_time: float            # 耗时（秒）
```

### DownloadResponse

下载响应模型：
```python
@dataclass
class DownloadResponse:
    source: SourceType             # 源
    std_no: str                    # 标准编号
    status: DownloadStatus         # 状态
    filepath: Optional[str]        # 本地文件路径
    filename: Optional[str]        # 文件名
    file_size: int                 # 文件大小（字节）
    error: Optional[str]           # 错误信息
    logs: List[str]                # 日志消息
    elapsed_time: float            # 耗时（秒）
```

### SourceHealth

源健康状态：
```python
@dataclass
class SourceHealth:
    source: SourceType             # 源
    available: bool                # 是否可用
    response_time: float           # 响应时间（毫秒）
    error: Optional[str]           # 错误信息
    last_check: float              # 最后检查时间戳
```

## JSON 序列化

所有响应对象都可以转换为 JSON：

```python
response = router.search_single(SourceType.BY, "GB")
json_data = response.to_dict()

import json
print(json.dumps(json_data, ensure_ascii=False, indent=2))
```

## 示例

运行完整的演示脚本：

```bash
python examples/api_demo.py
```

输出内容：
1. 在各个源中搜索标准
2. 检查各源的健康状态
3. 展示统一的 JSON 响应格式

## 为后续应用做准备

这个 API 框架为以下应用做好了准备：

### 桌面应用

使用 PyQt/PySide 构建 GUI，调用 APIRouter 的方法处理用户请求。

### Web API

使用 FastAPI 或 Flask 包装 APIRouter 的方法，提供 RESTful API：

```python
from fastapi import FastAPI
from api import APIRouter, SourceType

app = FastAPI()
router = APIRouter()

@app.get("/search/{source}")
def search(source: str, q: str, limit: int = 100):
    try:
        source_type = SourceType[source.upper()]
        response = router.search_single(source_type, q, limit)
        return response.to_dict()
    except Exception as e:
        return {"error": str(e)}

@app.post("/download/{source}")
def download(source: str, std_no: str):
    try:
        source_type = SourceType[source.upper()]
        response = router.download(source_type, std_no)
        return response.to_dict()
    except Exception as e:
        return {"error": str(e)}

@app.get("/health")
def health_check():
    response = router.check_health()
    return response.to_dict()
```

## 注意事项

1. **初始化延迟**: 首次创建 APIRouter 时，各源会被初始化，可能需要几秒钟。
2. **网络连接**: 所有操作都需要网络连接。
3. **认证**: BY 源需要内网访问权限。
4. **性能**: ZBY 源需要使用 Playwright 进行动态页面加载，比 HTTP 请求慢。
5. **错误处理**: 始终检查 `response.error` 和 `response.status` 来处理错误。

## 扩展

添加新的源：

1. 在 `sources/` 目录创建新的源实现
2. 在 `api/` 目录创建对应的 API 包装类（继承 `BaseSourceAPI`）
3. 在 `APIRouter` 的 `__init__` 中注册新的源

示例：
```python
class NewSourceAPI(BaseSourceAPI):
    source_type = SourceType.NEW_SOURCE
    
    def search(self, query: str, limit: int = 100) -> SearchResponse:
        # 实现搜索逻辑
        pass
    
    def download(self, std_no: str, output_dir: str, progress_callback) -> DownloadResponse:
        # 实现下载逻辑
        pass
    
    def check_health(self) -> SourceHealth:
        # 实现健康检查逻辑
        pass
```
