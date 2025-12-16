# 32bit & 64bit 双架构构建指南

## 工作流更新

GitHub Actions 工作流已更新为支持同时构建 32 位和 64 位版本。

### 修复内容

✅ **升级弃用的 Actions**
- `actions/upload-artifact@v3` → `actions/upload-artifact@v4`
- `actions/checkout@v3` → `actions/checkout@v4`
- 使用最新的 `actions/download-artifact@v4`

✅ **矩阵构建配置**
- 同时构建 32 位版本（x86）
- 同时构建 64 位版本（x64）
- 分别生成独立的安装程序

### 构建输出

每个版本发布会生成 4 个文件：

```
Releases/
├── Installer-32bit.exe    # 32 位安装程序
├── app-32bit.exe          # 32 位免安装版
├── Installer-64bit.exe    # 64 位安装程序
└── app-64bit.exe          # 64 位免安装版
```

### 发布流程

#### 快速发布新版本

```bash
# 方式1：创建并推送标签
git tag -a v1.0.1 -m "Release v1.0.1 - 32bit and 64bit"
git push origin v1.0.1

# GitHub Actions 自动：
# 1. 并行构建 32 位版本
# 2. 并行构建 64 位版本
# 3. 创建 Release 并上传全部文件
```

#### 手动触发（用于测试）

在 GitHub 网页上：
1. 打开 Actions 标签页
2. 选择 "Build Windows Installer" 工作流
3. 点击 "Run workflow" 按钮
4. 选择 main 分支
5. 点击 "Run workflow"

### 工作流详解

```yaml
strategy:
  matrix:
    python-arch: [x86, x64]  # 矩阵：32位和64位
    
# 结果：
# Job 1: build (x86 - 32bit)  ┐
# Job 2: build (x64 - 64bit)  ├─ 并行执行
#                             ┘
# Job 3: create-release       └─ 等待上述完成后执行
```

### 用户下载指南

用户根据系统选择下载对应版本：

**32 位系统用户：**
- 下载 `Installer-32bit.exe` 或 `app-32bit.exe`

**64 位系统用户：**
- 下载 `Installer-64bit.exe` 或 `app-64bit.exe`（推荐）

**如何判断系统位数？**
- Windows 设置 → 系统 → 关于
- 查看"系统类型"

### 故障排除

**如果构建失败：**

1. 检查 Actions 日志
2. 查看是否有编码问题
3. 确认 NSIS 安装成功
4. 检查 Python 依赖

**常见错误：**

| 错误 | 解决方案 |
|------|---------|
| `ModuleNotFoundError` | 检查 requirements.txt |
| `NSIS not found` | 检查 Chocolatey 可用性 |
| `Permission denied` | 工作流权限自动处理 |
| 编码问题 | 使用 `-Encoding UTF8` |

### 版本标签命名

推荐使用语义化版本：

```
v1.0.0  - 首个发布
v1.0.1  - 补丁更新
v1.1.0  - 功能更新
v2.0.0  - 重大更新
```

### 实时查看构建

https://github.com/atpx4869/Multi-source-downloader/actions

---

**现在每次发布只需创建一个标签，GitHub 就会自动生成 4 个版本的安装程序！** 🚀
