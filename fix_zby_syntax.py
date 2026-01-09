#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复zby.py中的Python 3.10+语法"""
import re
from pathlib import Path

zby_path = Path(r'c:\Users\PengLinHao\Desktop\github项目\Multi-source-downloader\sources\zby.py')

# 读取文件
with open(zby_path, 'r', encoding='utf-8') as f:
    content = f.read()

print("开始修复zby.py中的Python 3.10+语法...")

# 替换1: 移除 for 循环中的类型注解
# for kw: str in -> for kw in
original_count = len(content)
content = re.sub(r'for\s+(\w+):\s*\w+(?:\[.*?\])?\s+in\s+', r'for \1 in ', content)
print("✓ 修复 for 循环类型注解")

# 替换2: 移除赋值语句中的复杂类型注解
# variable: Type = value -> variable = value
# 这个很复杂，所以分别处理常见的情况

# 处理 Type | None 的形式
content = re.sub(r'(\w+):\s*(?:[\w\.]+)\s*\|\s*None\s*=\s*', r'\1 = ', content)
print("✓ 修复 Type | None 类型")

# 处理 Type | Type 的形式
content = re.sub(r'(\w+):\s*(?:[\w\.]+)\s*\|\s*(?:[\w\.]+)\s*=\s*', r'\1 = ', content)
print("✓ 修复 Type | Type 类型")

# 处理普通 Type = 的形式（但保留函数定义等）
# 只处理那些看起来像变量赋值的行
lines = content.split('\n')
new_lines = []
for line in lines:
    # 如果是普通变量赋值 (以空格开头，包含 : Type =)
    if re.match(r'^\s+\w+:\s*(?:List|Dict|str|bool|int|Optional|re|Path)\[.*?\]\s*=', line):
        # 移除类型注解
        line = re.sub(r':\s*(?:List|Dict|str|bool|int|Optional|re|Path).*?\s*=\s*', ' = ', line)
    elif re.match(r'^\s+\w+:\s*(?:List|Dict|str|bool|int|Optional|re|Path)\s*=', line):
        # 移除类型注解
        line = re.sub(r':\s*(?:List|Dict|str|bool|int|Optional|re|Path)\s*=\s*', ' = ', line)
    new_lines.append(line)

content = '\n'.join(new_lines)
print("✓ 修复普通变量赋值类型注解")

# 替换3: 修复 path: Path | None 这样的变量声明（无赋值）
content = re.sub(r':\s*Path\s*\|\s*None', '', content)
content = re.sub(r':\s*Path\s*\|', '', content)
print("✓ 修复 Path | None 类型")

# 替换4: 修复 re.Any | str 这样的类型
content = re.sub(r':\s*re\.Any\s*\|\s*str', '', content)
content = re.sub(r':\s*str\s*\|\s*re\.Any', '', content)
print("✓ 修复 re.Any | str 类型")

# 替换5: 修复函数返回类型中的 | (但要小心不要修复类型注解)
# -> Path | None 改为 -> Optional[Path]
content = re.sub(r'->\s*Path\s*\|\s*None', '-> Optional[Path]', content)
content = re.sub(r'->\s*(\w+)\s*\|\s*None', r'-> Optional[\1]', content)
print("✓ 修复函数返回类型")

# 替换6: 还原 Optional 的导入（如果需要）
if 'Optional[Path]' in content and 'from typing import' in content:
    if 'Optional' not in content[:500]:  # 检查imports部分
        content = re.sub(
            r'(from typing import.*?)',
            lambda m: m.group(1) + ', Optional' if 'Optional' not in m.group(1) else m.group(1),
            content,
            count=1
        )
print("✓ 检查Optional导入")

# 验证修改了多少
new_count = len(content)
print(f"\n字符数变化: {original_count} -> {new_count}")

# 写回文件
with open(zby_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ zby.py 语法修复完成")
