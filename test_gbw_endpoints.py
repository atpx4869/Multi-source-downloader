"""
测试 GBW 下载端点
"""
import requests

hcno = "96019B083A5A59FC7F84895DFFE7500B"

# 尝试不同的端点
endpoints = [
    f"https://openstd.samr.gov.cn/bzgk/servlet/Download?HCNO={hcno}",
    f"https://openstd.samr.gov.cn/bzgk/std/download?hcno={hcno}",
    f"https://openstd.samr.gov.cn/bzgk/attachment/download?hcno={hcno}",
    f"https://openstd.samr.gov.cn/servlet/Download?HCNO={hcno}",
    f"https://openstd.samr.gov.cn/download?hcno={hcno}",
    f"https://std.samr.gov.cn/servlet/Download?HCNO={hcno}",
    f"https://std.samr.gov.cn/gb/search/gcDown?hcno={hcno}",
]

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
})

for url in endpoints:
    try:
        print(f"\n尝试: {url}")
        r = session.get(url, timeout=10, allow_redirects=True)
        print(f"  状态码: {r.status_code}")
        print(f"  Content-Type: {r.headers.get('content-type', 'N/A')}")
        print(f"  Content-Length: {len(r.content)} bytes")
        
        # 检查是否是 PDF
        if r.content[:4] == b'%PDF':
            print(f"  ✓ 这是一个 PDF 文件!")
            with open("test_gbw_download.pdf", "wb") as f:
                f.write(r.content)
            print(f"  已保存到 test_gbw_download.pdf")
            break
        else:
            print(f"  ✗ 不是 PDF (前4字节: {r.content[:20]})")
    except Exception as e:
        print(f"  错误: {e}")
