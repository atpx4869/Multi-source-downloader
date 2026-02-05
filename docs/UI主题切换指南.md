# UI主题切换指南

本项目提供了三种现代化UI主题，您可以根据个人喜好选择：

## 🎨 可用主题

### 1. **原始主题** (`ui_styles.py`)
- **风格**: 经典浅色，商务风格
- **特点**: 稳重、专业、适合办公环境
- **主色**: 蓝色 (#34c2db)
- **适合**: 长时间办公使用

### 2. **深色主题** (`ui_styles_dark.py`) ⭐ 推荐
- **风格**: 现代深色，科技感
- **特点**: 护眼、炫酷、渐变效果
- **主色**: 紫蓝渐变 (#667eea → #764ba2)
- **适合**: 夜间使用、减少眼睛疲劳
- **特色**: 
  - 紫蓝渐变按钮
  - 深色背景保护视力
  - 现代化圆角设计
  - 悬停动画效果

### 3. **扁平化主题** (`ui_styles_flat.py`)
- **风格**: 活力扁平化，清新明快
- **特点**: 色彩鲜明、简洁大方
- **主色**: 珊瑚红 (#ff6b6b)
- **适合**: 追求视觉冲击力
- **特色**:
  - 大圆角设计
  - 鲜艳配色
  - 扁平化风格
  - 清新简洁

---

## 🔧 如何切换主题

### 方法1: 修改导入语句（推荐）

编辑 `app/desktop_app_impl.py`，找到第128行：

```python
# 当前导入
from app import ui_styles
```

**切换到深色主题**：
```python
from app import ui_styles_dark as ui_styles
```

**切换到扁平化主题**：
```python
from app import ui_styles_flat as ui_styles
```

### 方法2: 创建配置文件

创建 `config/ui_theme.json`：

```json
{
  "theme": "dark",
  "options": ["default", "dark", "flat"]
}
```

然后在程序启动时读取配置（需要修改代码）。

---

## 📸 主题预览对比

| 特性 | 原始主题 | 深色主题 ⭐ | 扁平化主题 |
|------|---------|-----------|-----------|
| 背景色 | 浅灰 | 深灰黑 | 极浅灰 |
| 主色调 | 蓝色 | 紫蓝渐变 | 珊瑚红 |
| 圆角大小 | 4px | 8px | 12px |
| 护眼程度 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| 视觉冲击 | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 专业感 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 现代感 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 🎯 推荐使用场景

### 深色主题 - 最推荐 ⭐⭐⭐⭐⭐
- ✅ 夜间工作
- ✅ 长时间使用
- ✅ 追求科技感
- ✅ 保护视力

### 扁平化主题
- ✅ 白天使用
- ✅ 追求活力
- ✅ 年轻化风格
- ✅ 演示展示

### 原始主题
- ✅ 商务办公
- ✅ 保守稳重
- ✅ 传统审美

---

## 💡 快速切换脚本

创建 `scripts/切换主题.bat`：

```batch
@echo off
echo 请选择主题:
echo 1. 原始主题
echo 2. 深色主题 (推荐)
echo 3. 扁平化主题
set /p choice=请输入数字 (1-3): 

if "%choice%"=="1" (
    echo 切换到原始主题...
    powershell -Command "(gc app\desktop_app_impl.py) -replace 'from app import ui_styles.*', 'from app import ui_styles' | Out-File -encoding UTF8 app\desktop_app_impl.py"
)
if "%choice%"=="2" (
    echo 切换到深色主题...
    powershell -Command "(gc app\desktop_app_impl.py) -replace 'from app import ui_styles.*', 'from app import ui_styles_dark as ui_styles' | Out-File -encoding UTF8 app\desktop_app_impl.py"
)
if "%choice%"=="3" (
    echo 切换到扁平化主题...
    powershell -Command "(gc app\desktop_app_impl.py) -replace 'from app import ui_styles.*', 'from app import ui_styles_flat as ui_styles' | Out-File -encoding UTF8 app\desktop_app_impl.py"
)

echo 主题切换完成！请重启应用查看效果。
pause
```

---

## 🔥 推荐配置

**个人使用推荐**：深色主题
- 护眼效果最好
- 现代化设计
- 渐变效果炫酷
- 适合长时间使用

**演示展示推荐**：扁平化主题
- 视觉冲击力强
- 色彩鲜明
- 更有活力

---

## 📝 自定义主题

如果你想创建自己的主题，可以：

1. 复制任一主题文件
2. 修改颜色定义部分
3. 保存为 `ui_styles_custom.py`
4. 导入使用

**颜色工具推荐**：
- [Coolors.co](https://coolors.co/) - 配色方案生成
- [Adobe Color](https://color.adobe.com/) - 专业配色
- [Material Design Colors](https://materialui.co/colors) - Material配色

---

**立即体验深色主题，让你的应用更加炫酷！** 🚀
