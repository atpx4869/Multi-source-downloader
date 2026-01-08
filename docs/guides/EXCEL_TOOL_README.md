# Excel标准号处理工具使用说明

## 功能说明

这个工具可以批量处理Excel中的标准号：

1. **不带年代号** (如 `GB/T 3324`)
   - 自动查询现行标准
   - 返回完整标准号 (如 `GB/T 3324-2024`)
   - 返回标准名称

2. **带年代号** (如 `GB/T 3325-2024`)
   - 直接返回该标准号
   - 查询并返回标准名称

## 安装依赖

```bash
pip install pandas openpyxl
```

## 使用方法

### 方法1：交互式运行

在项目根目录运行脚本，按提示输入：

```bash
python web_app/excel_standard_processor.py
```

然后按提示输入：
- Excel文件路径
- 标准号所在列（如 A、B、C等）
- 开始处理的行号（第1行通常是表头，所以默认从第2行开始）

### 方法2：命令行参数

```bash
python web_app/excel_standard_processor.py <输入文件> [选项]
```

**参数说明：**

- `input`: 输入Excel文件路径（必需）
- `-o, --output`: 输出文件路径（可选，默认为 `输入文件名_结果.xlsx`）
- `-c, --column`: 标准号所在列（可选，默认 `A`）
- `-s, --start-row`: 开始行号（可选，默认 `2`）
- `--result-no-col`: 结果标准号写入的列（可选，默认 `B`）
- `--result-name-col`: 结果标准名称写入的列（可选，默认 `C`）

**示例：**

```bash
# 处理标准.xlsx，标准号在A列，从第2行开始
python web_app/excel_standard_processor.py 标准.xlsx

# 指定输出文件
python web_app/excel_standard_processor.py 标准.xlsx -o 处理结果.xlsx

# 标准号在C列，从第3行开始
python web_app/excel_standard_processor.py 标准.xlsx -c C -s 3

# 结果写入E列和F列
python web_app/excel_standard_processor.py 标准.xlsx --result-no-col E --result-name-col F
```

### 方法3：在Python代码中使用

```python
from web_app.excel_standard_processor import StandardProcessor

processor = StandardProcessor()

# 处理Excel文件
processor.process_excel(
    input_file='标准.xlsx',
    output_file='结果.xlsx',
    std_no_col='A',      # 标准号在A列
    start_row=2,         # 从第2行开始
    result_col_no='B',   # 完整标准号写入B列
    result_col_name='C'  # 标准名称写入C列
)

# 或者单独处理标准号
std_no, name, status = processor.process_standard("GB/T 3324")
print(f"标准号: {std_no}")
print(f"名称: {name}")
print(f"状态: {status}")
```

## Excel文件格式

### 输入格式示例

| A列-标准号 |
|-----------|
| GB/T 3324 |
| GB/T 3325-2024 |
| GB 50010 |
| GB 50011-2010 |

### 输出格式示例

| A列-标准号 | B列-完整标准号 | C列-标准名称 |
|-----------|--------------|-------------|
| GB/T 3324 | GB/T 3324-2024 | 木家具通用技术条件 |
| GB/T 3325-2024 | GB/T 3325-2024 | 金属家具通用技术条件 |
| GB 50010 | GB 50010-2010 | 混凝土结构设计规范 |
| GB 50011-2010 | GB 50011-2010 | 建筑抗震设计规范 |

## 注意事项

1. **Excel格式**：支持 `.xlsx` 和 `.xls` 格式
2. **表头**：默认第1行为表头，从第2行开始处理数据
3. **列名**：使用字母表示列（A, B, C...）
4. **网络连接**：需要联网查询标准信息
5. **处理速度**：每个标准需要查询API，处理时间较长，请耐心等待
6. **结果保存**：默认保存为 `原文件名_结果.xlsx`

## 功能特点

✅ 自动识别是否带年代号
✅ 智能查找现行标准
✅ 多源查询（BY、ZBY、GBW）
✅ 精确匹配标准名称
✅ 详细的处理日志
✅ 错误处理和统计

## 示例输出

```
============================================================
📁 读取Excel文件: 标准.xlsx
============================================================

配置:
  标准号列: A (列索引 0)
  开始行: 2
  结果标准号列: B
  结果标准名称列: C

开始处理...

处理标准号: GB/T 3324
  → 检测到不带年代号，查找现行标准
  🔍 搜索标准: GB/T 3324
    ✓ ZBY 找到 5 个结果
    ✓ 找到现行标准: GB/T 3324-2024
  ✅ 行 2 处理成功

处理标准号: GB/T 3325-2024
  → 检测到带年代号，直接查询标准名称
  🔍 查询标准: GB/T 3325-2024
    ✓ ZBY 找到 1 个结果
    ✓ 找到标准名称: 金属家具通用技术条件
  ✅ 行 3 处理成功

============================================================
💾 保存结果到: 标准_结果.xlsx
✅ 保存成功!

============================================================
📊 处理统计:
  成功: 2
  失败: 0
  总计: 2
============================================================
```

## 故障排除

**问题1：找不到模块**
```
ModuleNotFoundError: No module named 'pandas'
```
解决：安装依赖 `pip install pandas openpyxl`

**问题2：未找到标准**
- 检查标准号格式是否正确
- 尝试手动在源网站搜索确认标准是否存在
- 某些行业标准可能数据源不全

**问题3：处理速度慢**
- 这是正常的，每个标准需要查询多个数据源
- 可以减少查询的数据源来提速（修改代码中的源配置）

## 技术支持

如有问题，请查看：
- API文档：`API_GUIDE.md`
- 项目说明：`README.md`
