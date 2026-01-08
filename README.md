# Standard Downloader (标准下载器)

一款高效、安全的多源标准文档下载工具，支持国家标准、行业标准等多种来源的聚合搜索与批量下载。

## 主要特性

- **多源聚合**：集成多个权威标准平台（如 GBW, BY, ZBY 等），提供统一的搜索与下载接口。
- **批量下载**：支持标准号批量导入，具备自动识别、去重及顺序下载功能。
- **统一 API 框架**：为桌面应用、Web 服务等提供规范化的 API 接口。
- **Win7 兼容**：基于 PySide2 (Qt5) 开发，深度优化以支持 Windows 7 及以上系统。
- **隐私脱敏**：日志系统自动屏蔽敏感请求 URL，保护访问路径不被泄露。
- **本地 OCR**：内置轻量化本地 OCR 引擎，减少对外部接口的依赖，提升识别速度。
- **实时日志**：提供详细的执行日志与下载进度反馈，支持失败任务汇总。

## 快速开始

### 运行程序
1. 从 [GitHub Releases](https://github.com/atpx4869/Multi-source-downloader/releases) 下载最新的 Release 压缩包。
2. 解压后运行 `StandardDownloader.exe` 即可开始使用。

### 批量下载
点击界面上的"批量下载"按钮，在弹出的对话框中每行输入一个标准号（支持带空格的标准号，如 `GB 18584-2024`），点击"开始下载"即可。

### 使用 API 接口

本项目提供了统一的 API 接口，方便在桌面应用或 Web 服务中集成：

```python
from api import APIRouter, SourceType

# 创建路由器
router = APIRouter()

# 搜索标准
results = router.search_all("GB/T 3324-2024")

# 下载标准
response = router.download(SourceType.ZBY, "GB/T 3324-2024")

# 检查源的健康状态
health = router.check_health()
```

详细的 API 文档请查看 [API_GUIDE.md](API_GUIDE.md)

## 项目结构

```
├── sources/              # 标准源实现
│   ├── by.py             # BY 源（标院内网系统）
│   ├── zby.py            # ZBY 源（正规宝）
│   ├── gbw.py            # GBW 源（GB/T 网）
│   └── ...
├── api/                  # 统一 API 框架
│   ├── models.py         # 数据模型
│   ├── base.py           # 基础接口
│   ├── by_api.py         # BY API 包装
│   ├── zby_api.py        # ZBY API 包装
│   ├── gbw_api.py        # GBW API 包装
│   ├── router.py         # API 路由器
│   └── __init__.py
├── core/                 # 核心模块
│   ├── models.py         # 数据模型（兼容）
│   ├── aggregated_downloader.py  # 聚合下载器
│   └── ...
├── app/                  # 应用层
│   ├── desktop_app_impl.py       # 桌面应用实现
│   └── ...
├── examples/             # 示例代码
│   └── api_demo.py       # API 使用演示
├── tools/                # 工具脚本
│   └── smoke_test.py     # 源健康检查工具
├── API_GUIDE.md          # API 详细文档
└── ...
```

## 开发与构建

若需从源码构建，建议使用 Python 3.8 环境以确保最佳的系统兼容性。

```bash
# 安装依赖
pip install -r requirements_win7.txt

# 运行应用
python desktop_app.py

# 运行 API 演示
python examples/api_demo.py

# 打包 (Windows)
pyinstaller StandardDownloader_Win7.spec
```

## 隐私说明

本程序在设计上优先考虑安全性：
- **日志脱敏**：所有输出到界面的网络请求链接均已通过正则替换为 `[URL]`。
- **无追踪**：程序不收集任何用户信息，所有下载的标准文档均保存在本地 `downloads` 目录下。

## 免责声明

本工具仅供学习和研究使用。用户在使用本工具下载文档时，应遵守相关法律法规及各平台的使用协议。作者不对因使用本工具而产生的任何法律纠纷承担责任。

## 开源协议

[MIT License](LICENSE)
