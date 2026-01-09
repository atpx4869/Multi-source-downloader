# -*- coding: utf-8 -*-
"""
ZBY 搜索冒烟测试：
- 直接运行以验证 ZBYSource.search 在当前环境可用
- 可通过命令行参数传入标准号列表
示例：
  python examples/zby_search_smoke.py QB/T 2359-2019 GB/T 7714-2015
"""
import sys
from pathlib import Path

# 添加项目根目录到 sys.path，确保可导入 'sources'
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# 避免因系统代理影响请求
import os
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''

from sources.zby import ZBYSource

DEFAULT_SAMPLES = [
    "GB/T 7714-2015",
    "QB/T 2359-2019",
    "QB/T 4839-2015",
]


def main(args):
    keywords = args if args else DEFAULT_SAMPLES
    src = ZBYSource(output_dir=Path("downloads"))
    print(f"Base URL: {src.base_url}")
    print(f"Allow Playwright: {src.allow_playwright}")
    print("开始搜索：", ", ".join(keywords))
    for kw in keywords:
        try:
            rows = src.search(kw)
            print(f"\n关键词: {kw} -> 结果数: {len(rows)}")
            for i, r in enumerate(rows[:5], 1):
                print(f"  [{i}] {r.std_no} | {r.name} | pub={r.publish} | impl={r.implement} | status={r.status} | has_pdf={r.has_pdf}")
        except Exception as e:
            print(f"关键词 {kw} 搜索异常: {e}")


if __name__ == "__main__":
    main(sys.argv[1:])
