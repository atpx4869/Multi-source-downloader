# API 返回信息说明

## 概览
API 可以返回以下几种类型的响应信息：
1. **搜索响应** (SearchResponse) - 搜索标准号时的返回
2. **下载响应** (DownloadResponse) - 下载文件时的返回
3. **健康检查响应** (HealthResponse) - 检查源可用性时的返回

---

## 1. 搜索响应 (SearchResponse)

### 返回字段
```json
{
  "source": "GBW|BY|ZBY",                    // 搜索源
  "query": "GB/T 7714-2015",                 // 搜索词
  "count": 1,                                // 找到的标准数量
  "standards": [                             // 标准列表
    {
      "std_no": "GB/T 7714-2015",           // 标准编号
      "name": "信息与文献 参考文献著录规则", // 标准名称
      "source": "GBW",                       // 源标识
      "has_pdf": true,                       // 是否有PDF版本
      "publish_date": "2015-12-01",         // 发布日期
      "implement_date": "2016-01-01",       // 实施日期
      "status": "现行",                      // 状态 (现行/废止等)
      "source_meta": {}                      // 源特定的元数据
    }
  ],
  "error": null,                             // 错误信息（无错误时为 null）
  "elapsed_time": 0.57                       // 耗时（秒）
}
```

### 使用示例
```python
from api import APIRouter, SourceType

router = APIRouter()

# 在单个源中搜索
response = router.search_single(SourceType.GBW, "GB/T 7714-2015")
print(f"找到 {response.count} 条结果")
for std in response.standards:
    print(f"  - {std.std_no}: {std.name}")

# 在所有源中搜索
results = router.search_all("GB/T 7714-2015")
for source, response in results.items():
    print(f"{source.value}: {response.count} 条")
```

---

## 2. 下载响应 (DownloadResponse)

### 返回字段
```json
{
  "source": "GBW",                          // 下载源
  "std_no": "GB/T 7714-2015",              // 标准编号
  "status": "success|failed|progress|not_found|error",  // 下载状态
  "filepath": "/path/to/file.pdf",         // 本地文件路径
  "filename": "GB_T 7714-2015.pdf",        // 文件名
  "file_size": 1024000,                    // 文件大小（字节）
  "error": null,                           // 错误信息
  "logs": [                                // 日志消息列表
    "开始下载...",
    "✓ 下载成功"
  ],
  "progress": {                            // 下载进度（可选）
    "total_pages": 20,                     // 总页数
    "current_page": 15,                    // 当前页数
    "current_file_size": 819200            // 当前文件大小
  },
  "elapsed_time": 3.25                     // 耗时（秒）
}
```

### 下载状态枚举
- `success` - 下载成功
- `failed` - 下载失败
- `progress` - 下载进行中
- `not_found` - 未找到
- `error` - 错误

### 使用示例
```python
# 从指定源下载
response = router.download(SourceType.GBW, "GB/T 7714-2015")
if response.status == DownloadStatus.SUCCESS:
    print(f"下载完成: {response.filepath}")
    print(f"文件大小: {response.file_size} 字节")
else:
    print(f"下载失败: {response.error}")

# 从第一个可用源下载
response = router.download_first_available("GB/T 7714-2015")
```

---

## 3. 健康检查响应 (HealthResponse)

### 返回字段
```json
{
  "sources": [                              // 各源的健康状态
    {
      "source": "GBW",                      // 源名称
      "available": true,                    // 是否可用
      "response_time": 245.3,               // 响应时间（毫秒）
      "error": null,                        // 错误信息
      "last_check": 1673445621.123          // 最后检查时间戳
    },
    {
      "source": "BY",
      "available": true,
      "response_time": 312.1,
      "error": null,
      "last_check": 1673445621.456
    },
    {
      "source": "ZBY",
      "available": false,
      "response_time": 0,
      "error": "连接超时",
      "last_check": 1673445621.789
    }
  ],
  "all_healthy": false,                    // 所有源是否都健康
  "timestamp": 1673445621.123              // 检查时间
}
```

### 使用示例
```python
# 检查所有源的健康状态
health = router.check_health()

print(f"检查时间: {health.timestamp}")
print(f"全部健康: {health.all_healthy}")

for source_health in health.sources:
    status = "✓ 可用" if source_health.available else "✗ 不可用"
    print(f"{source_health.source.value}: {status} ({source_health.response_time}ms)")
    if source_health.error:
        print(f"  错误: {source_health.error}")
```

---

## 4. 标准信息 (StandardInfo)

### 字段说明
```python
std_no: str                    # 标准编号 (GB/T 3324-2024)
name: str                      # 标准名称
source: SourceType             # 源 (BY/ZBY/GBW)
has_pdf: bool                  # 是否有PDF版本
publish_date: Optional[str]    # 发布日期 (YYYY-MM-DD)
implement_date: Optional[str]  # 实施日期 (YYYY-MM-DD)
status: Optional[str]          # 状态 (现行/废止/替代等)
source_meta: Dict             # 源特定的元数据（高级用途）
```

---

## 5. 可用的 API 方法

### 搜索相关
- `search_single(source, query, limit=100)` - 在单个源中搜索
- `search_all(query, limit=100)` - 在所有源中搜索

### 下载相关
- `download(source, std_no, output_dir=None, progress_callback=None)` - 从指定源下载
- `download_first_available(std_no, output_dir=None, progress_callback=None)` - 从第一个可用源下载

### 管理相关
- `check_health()` - 检查所有源的健康状态
- `get_enabled_sources()` - 获取已启用的源列表
- `get_api(source)` - 获取指定源的 API 对象

---

## 6. 错误处理

所有响应都包含可选的 `error` 字段：
- 如果操作成功，`error` 为 `null`
- 如果操作失败，`error` 包含错误描述字符串

### 常见错误
- `源 XXX 未启用` - 指定的源没有启用
- `连接超时` - 网络连接超时
- `未找到可用的源或下载失败` - 所有源都无法完成任务
- `网络错误: ...` - 网络相关错误

---

## 7. 转换为字典

所有响应对象都可以通过 `.to_dict()` 方法转换为字典，便于序列化为 JSON：

```python
response = router.search_single(SourceType.GBW, "GB/T 7714")
json_data = response.to_dict()
import json
print(json.dumps(json_data, indent=2, ensure_ascii=False))
```

---

## 源信息

### 支持的源
| 源代码 | 源名称 | 特点 |
|--------|--------|------|
| GBW | GB/T 网 | 国标网，速度快，GB 类标准完整 |
| BY | 标院内网 | 内网系统，GB/T 和 QB/T 标准齐全 |
| ZBY | 正规宝 | 第三方服务，网络爬虫，业标准较全 |

