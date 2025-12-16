# Standard Downloader

A desktop application for downloading Chinese standard documents from multiple sources.

## Download

Get the latest release from [GitHub Releases](https://github.com/atpx4869/Multi-source-downloader/releases):

- **StandardDownloader-x64.exe** - For 64-bit Windows (recommended)
- **StandardDownloader-x86.exe** - For 32-bit Windows

## Features

- Multi-source aggregation (GBW, BY, ZBY)
- Batch download support
- Export to CSV
- Real-time download logs
- Source connectivity detection

## Requirements

- Windows 10 or later
- No Python installation required

## Build from Source

```bash
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --onefile --windowed desktop_app.py
```

## License

MIT

## 项目结构

```
.
├── desktop_app.py          # 主应用（PySide6 GUI）
├── core/                   # 核心业务逻辑
│   ├── __init__.py
│   ├── aggregated_downloader.py    # 多源聚合下载器
│   ├── by_download.py      # BY 源下载模块
│   ├── by_source.py        # BY 源连接模块
│   ├── gbw_download.py     # GBW 源下载模块
│   ├── gbw_source.py       # GBW 源连接模块
│   ├── standard_downloader.py      # 标准下载基类
│   ├── zby_download.py     # ZBY 源下载模块
│   └── zby_source.py       # ZBY 源连接模块
├── ppllocr/                # OCR 支持库
├── requirements.txt        # Python 依赖
├── README.md              # 本文件
└── README_DESKTOP.md      # 桌面应用详细说明
```

## 核心特性

### 📊 多源聚合
- **GBW**：国家标准官方库
- **BY**：内部系统数据源
- **ZBY**：标准云开放平台

### 🔗 源连通性检测
- 自动检测各数据源可用状态
- 实时显示源连通情况
- 搜索时智能跳过不可用源

### 💻 现代化界面
- PySide6 跨平台 GUI
- 实时日志面板
- 快速路径设置
- 搜索结果 CSV 导出

## 技术栈

- **GUI 框架**：PySide6（Qt6 Python 绑定）
- **数据处理**：pandas
- **并发处理**：Python threading + Qt signals/slots
- **网络请求**：requests, urllib3
- **OCR 支持**：ppllocr

## 依赖

```bash
pip install -r requirements.txt
```

## 许可证

MIT License - 详见 LICENSE 文件（如存在）
