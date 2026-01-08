# Standard Downloader (标准下载器)

多源标准文献的聚合搜索与下载工具，提供桌面应用、统一 API、Web 界面和 Excel 批处理能力，兼容 Windows 7 及以上环境。

## 主要能力

- 多源聚合：统一封装 GBW、BY、ZBY 等数据源，支持优先级与健康检查。
- 桌面应用：PySide 桌面端，支持并行搜索、批量下载、日志与配置 UI。
- API/SDK：`APIRouter` 提供搜索、下载、健康检查的统一接口，支持 JSON 序列化。
- Web 工具：Flask 界面上传 Excel 批量处理标准号，返回结果文件。
- 批处理脚本：命令行 Excel 标准号清洗与补全，可单独调用。

## 环境与安装

- Python 3.8+（Win7 建议 `requirements_win7.txt`）
- 安装依赖：`pip install -r requirements_win7.txt`
- Playwright（如使用 ZBY 动态源）：`playwright install chromium`

## 快速开始

- 桌面应用：`python desktop_app.py`（详情见 [docs/guides/LOCAL_RUN_GUIDE.md](docs/guides/LOCAL_RUN_GUIDE.md)）
- API 示例：`python examples/api_demo.py`（接口说明见 [docs/api/API_GUIDE.md](docs/api/API_GUIDE.md)）
- Web 应用：`python web_app/web_app.py`（操作指南 [web_app/WEB_APP_GUIDE.md](web_app/WEB_APP_GUIDE.md)）
- Excel 批处理脚本：`python web_app/excel_standard_processor.py <输入文件>`（用法见 [docs/guides/EXCEL_TOOL_README.md](docs/guides/EXCEL_TOOL_README.md)）

## 目录速览

- API 与数据模型：[api](api) · 路由器在 [api/router.py](api/router.py)
- 桌面应用实现：[app/desktop_app_impl.py](app/desktop_app_impl.py)
- 核心聚合逻辑：[core](core)
- 数据源实现：[sources](sources)
- Web 应用与批处理脚本：[web_app](web_app)
- 配置与说明：配置文档在 [config](config)
- 文档归档：API/指南/报告在 [docs](docs)

## 文档索引

- API： [docs/api/API_GUIDE.md](docs/api/API_GUIDE.md) · [docs/api/API_ARCHITECTURE.md](docs/api/API_ARCHITECTURE.md)
- 指南： [docs/guides/LOCAL_RUN_GUIDE.md](docs/guides/LOCAL_RUN_GUIDE.md) · [docs/guides/PERFORMANCE_OPTIMIZATION.md](docs/guides/PERFORMANCE_OPTIMIZATION.md) · [docs/guides/PROJECT_STRUCTURE.md](docs/guides/PROJECT_STRUCTURE.md) · [docs/guides/EXCEL_TOOL_README.md](docs/guides/EXCEL_TOOL_README.md)
- 报告： [docs/reports/API_SUMMARY.md](docs/reports/API_SUMMARY.md) · [docs/reports/COMPLETION_REPORT.md](docs/reports/COMPLETION_REPORT.md)
- 配置体系： [config/API_CONFIG_GUIDE.md](config/API_CONFIG_GUIDE.md) · [config/ARCHITECTURE_GUIDE.md](config/ARCHITECTURE_GUIDE.md) · [config/IMPLEMENTATION_SUMMARY.md](config/IMPLEMENTATION_SUMMARY.md)
- Web 应用： [web_app/WEB_APP_GUIDE.md](web_app/WEB_APP_GUIDE.md)

## 典型场景

- 本地桌面检索与批量下载：直接运行桌面端，选择源与并行配置。
- 后端集成：通过 `APIRouter` 或封装的 `APIClient` 统一访问多个源，返回 JSON。
- 批量清洗 Excel：命令行或 Web 上传 Excel，补全标准号和名称，生成结果文件。

## 常用命令速查

- 安装依赖：`pip install -r requirements_win7.txt`
- 桌面应用：`python desktop_app.py`
- API 演示：`python examples/api_demo.py`
- Web 应用：`python web_app/web_app.py`
- Excel 批处理：`python web_app/excel_standard_processor.py --help`
