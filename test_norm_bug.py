
import re

def _norm_std_no_buggy(std_no: str) -> str:
    # 统一去掉空白和常见分隔符，避免名称差异造成重复
    # This is what's currently in aggregated_downloader.py
    return re.sub(r"[\\s/\\-–—_:：]+", "", std_no or "").lower()

def _norm_std_no_fixed(std_no: str) -> str:
    # Proper whitespace and separator removal
    return re.sub(r"[\s/\-–—_:：]+", "", std_no or "").lower()

test_cases = [
    "GB/T 25686-2018",
    "GB / T 25686-2018",
    "GB/T  25686 - 2018",
    "gb/t256862018"
]

print("Buggy implementation results:")
for tc in test_cases:
    print(f"'{tc}' -> '{_norm_std_no_buggy(tc)}'")

print("\nFixed implementation results:")
for tc in test_cases:
    print(f"'{tc}' -> '{_norm_std_no_fixed(tc)}'")
