# 项目主程序文件详解

## 项目架构概览

```
多源标准下载系统
│
├── 入口层
│   └── desktop_app.py              # 精简入口，仅负责启动
│
├── 应用层
│   └── app/
│       └── desktop_app_impl.py    # 完整的 PySide 桌面应用实现（2617行）
│
├── 核心层
│   └── core/
│       ├── aggregated_downloader.py  # 聚合下载器，管理多个源（349行）
│       ├── models.py                 # 数据模型定义
│       └── loader.py                 # 源加载器
│
├── 源层
│   └── sources/
│       ├── gbw.py                  # GB/T 网源（416行）
│       ├── by.py                   # BY 源（标院内网）
│       ├── zby.py                  # ZBY 源（正规宝）
│       ├── zby_playwright.py        # ZBY Playwright 实现
│       ├── gbw_download.py          # GBW 下载和 OCR
│       └── http_search.py           # HTTP 搜索工具
│
├── API 层
│   └── api/                        # 统一 API 框架（新增）
│       ├── models.py               # API 数据模型
│       ├── base.py                 # API 基础接口
│       ├── by_api.py               # BY API 包装
│       ├── zby_api.py              # ZBY API 包装
│       ├── gbw_api.py              # GBW API 包装
│       ├── router.py               # API 路由器
│       └── __init__.py             # 包导出
│
└── 配置和样式
    ├── ui_styles.py                # UI 样式定义
    ├── requirements.txt            # 依赖列表
    └── requirements_win7.txt       # Win7 特定依赖
```

## 详细文件说明

### 1. 入口层

#### desktop_app.py (33 行)
**职责**：项目的启动入口

```python
# 关键功能：
- _bootstrap_sys_path()  : 配置 Python 路径和 ppllocr 依赖
- main()               : 加载并执行实际的应用实现
```

**特点**：
- 极简设计，仅负责环境配置和委托给 impl
- 便于打包和维护

### 2. 应用层

#### app/desktop_app_impl.py (2617 行)
**职责**：完整的 PySide/PySide2 桌面应用实现

**核心类**：

1. **PasswordDialog** (密码验证对话框)
   - 每日安全验证机制
   - 密码：当日日期反转后的前 6 位
   - 支持 5 次错误尝试

2. **MainWindow** (主窗口)
   - 左侧：搜索框 + 结果表格
   - 右侧：实时日志展示
   - 底部：进度条和统计信息

3. **WorkerThread** (后台线程)
   - 异步搜索和下载
   - 使用 Qt 信号与 UI 通信
   - 支持进度回调

**主要功能**：
- 搜索标准（支持多源并行搜索）
- 选择并下载标准
- 批量下载功能
- 实时日志显示
- 源健康检查

**关键设计**：
```python
# 线程管理
WorkerThread 用于后台操作，避免阻塞 UI

# 缓存机制
_AD_CACHE: 缓存 AggregatedDownloader 实例

# 兼容性处理
支持 PySide6 和 PySide2
兼容不同的 Qt API（exec vs exec_）
```

### 3. 核心层

#### core/aggregated_downloader.py (349 行)
**职责**：聚合多个源，提供统一的搜索和下载接口

**核心类**：

1. **SourceHealth** (源健康状态)
   ```python
   - name          : 源名称
   - available     : 是否可用
   - error         : 错误信息
   - response_time : 响应时间
   ```

2. **AggregatedDownloader** (聚合下载器)
   
   **主要方法**：
   ```python
   __init__()                    : 初始化并加载所有源
   search(keyword, source=None)  : 搜索标准
   download(std, source=None)    : 下载标准
   check_source_health()         : 检查源健康状态
   get_available_sources()       : 获取可用源列表
   ```
   
   **关键特性**：
   - 自动去重：相同标准号只保留一条，合并多源信息
   - 源优先级：GBW > BY > ZBY
   - 健康检查缓存（60 秒有效期）
   - 灵活的源启用控制

**去重逻辑**：
```python
_norm_std_no()  : 规范化标准号（去除空格、斜杠等）
_merge_items()  : 合并去重，保留多源元数据
```

### 4. 源层

#### sources/gbw.py (416 行)
**职责**：GB/T 网（国家标准信息公共服务平台）源

**类**：GBWSource

**主要方法**：
```python
search(keyword)         : 搜索标准
download(std_no, dir)   : 下载标准 PDF

_parse_std_code()       : 解析标准编号（处理 HTML）
_clean_text()           : 清理 HTML 标签
```

**特点**：
- HTTP 直接访问，速度快
- 包含 OCR 识别的验证码处理
- 保留所有标准的元数据

#### sources/by.py (292 行)
**职责**：BY 源（标院内网系统）

**特点**：
- 需要内网访问权限
- 支持部门选择
- 用户认证机制

#### sources/zby.py (803 行)
**职责**：ZBY 源（正规宝）

**特点**：
- 支持 standardId 直接访问优化
- 既有 HTTP 也有 Playwright 实现
- 处理 SPA 动态页面加载

**关键改进**：
- 使用正确的 URL：`/standardDetail?standardId=...`
- 网络请求监听捕获 immdoc UUID
- 支持页面滚动触发资源加载

#### sources/zby_playwright.py
**职责**：ZBY 的 Playwright 实现

**特点**：
- 动态页面处理
- 请求监听和截获
- UUID 自动提取

#### sources/gbw_download.py
**职责**：GBW 下载和 OCR 处理

**功能**：
- 验证码识别（PPLCOR 引擎）
- 图片下载和合成
- PDF 生成

#### sources/http_search.py
**职责**：HTTP 搜索工具函数库

**提供**：
- API 调用包装
- 响应解析
- 数据提取

### 5. API 层（新增）

#### api/ 包
**职责**：提供统一的 API 接口

**文件说明**：

1. **api/models.py** - 数据模型
   - SourceType, DownloadStatus 枚举
   - StandardInfo, SearchResponse, DownloadResponse
   - SourceHealth, HealthResponse

2. **api/base.py** - 基础接口
   - BaseSourceAPI 抽象类
   - 定义所有源必须实现的方法

3. **api/*_api.py** - 源实现
   - BYSourceAPI, ZBYSourceAPI, GBWSourceAPI
   - 统一接口的具体实现

4. **api/router.py** - API 路由器
   - APIRouter 类
   - 管理多个源，提供编排功能

### 6. 数据模型

#### core/models.py
```python
@dataclass
class Standard:
    std_no            : str           # 标准编号
    name              : str           # 标准名称
    publish           : str           # 发布日期
    implement         : str           # 实施日期
    status            : str           # 状态
    has_pdf           : bool          # 是否有 PDF
    source_meta       : Dict          # 源特定元数据
    sources           : List[str]     # 来源列表
    
    def display_label() : str         # 显示标签
    def filename()      : str         # 文件名
```

## 工作流程

### 搜索流程

```
用户输入关键词
    ↓
MainWindow.search_button_clicked()
    ↓
WorkerThread.run() 执行搜索
    ↓
AggregatedDownloader.search()
    ├─ GBWSource.search()     (并行)
    ├─ BYSource.search()      (并行)
    └─ ZBYSource.search()     (并行)
    ↓
_merge_items() 去重合并
    ↓
工作线程发送信号给 UI
    ↓
MainWindow 更新表格显示
```

### 下载流程

```
用户选择标准并点击下载
    ↓
MainWindow.download_button_clicked()
    ↓
WorkerThread.run() 执行下载
    ↓
选择源 (优先级: GBW > BY > ZBY)
    ↓
SourceAPI.download()
    ├─ 搜索标准获取信息
    ├─ 构建下载 URL
    ├─ 下载资源
    └─ 生成 PDF
    ↓
保存到 output_dir
    ↓
工作线程发送完成信号
    ↓
MainWindow 更新日志和状态
```

## 关键特性

### 1. 多源聚合
- 自动搜索所有可用源
- 结果去重合并
- 智能源选择

### 2. 线程管理
- 后台异步搜索和下载
- UI 线程安全
- 进度实时反馈

### 3. 健康检查
- 定期检查源可用性
- 60 秒缓存机制
- 自动故障转移

### 4. 密码保护
- 每日验证机制
- 日期反转算法
- 5 次错误限制

### 5. 日志系统
- 实时日志显示
- 详细的操作记录
- 敏感信息脱敏

### 6. 错误处理
- 完善的异常捕获
- 详细的错误信息
- 失败重试机制

## 技术栈

| 层面 | 技术 | 说明 |
|------|------|------|
| UI | PySide6/PySide2 | Qt 框架（支持 Win7） |
| 线程 | QThread | Qt 线程管理 |
| HTTP | requests | HTTP 客户端 |
| 动态渲染 | Playwright | 浏览器自动化 |
| OCR | PPLCOR | 本地验证码识别 |
| 数据处理 | pandas | 数据表格处理 |
| 文档 | PDF, PIL | PDF 和图片处理 |

## 扩展点

### 添加新源
1. 在 `sources/` 创建新源类
2. 在 `api/` 创建对应的 API 包装
3. 在 `AggregatedDownloader` 中注册

### 修改 UI
1. 编辑 `app/desktop_app_impl.py`
2. 修改 `ui_styles.py` 中的样式

### 添加新功能
1. 在 `WorkerThread` 中实现
2. 通过信号与 UI 通信

## 总结

这是一个**分层、模块化、高可扩展**的项目：

- **入口层**：极简启动
- **应用层**：完整的 UI 实现
- **核心层**：多源管理和聚合
- **源层**：具体的数据源实现
- **API 层**：统一接口（新增）

系统设计清晰，便于维护和扩展。已经为桌面应用和 Web 应用的开发做好了充分准备。
