"""
测试真正的 GBW 下载端点
"""
import requests

hcno = "96019B083A5A59FC7F84895DFFE7500B"

# 用户提供的真实下载 URL
download_url = f"http://c.gb688.cn/bzgk/gb/showGb?type=download&hcno={hcno}"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
})

print(f"测试下载 URL: {download_url}")
try:
    r = session.get(download_url, timeout=10, allow_redirects=True)
    print(f"状态码: {r.status_code}")
    print(f"Content-Type: {r.headers.get('content-type', 'N/A')}")
    print(f"Content-Length: {len(r.content)} bytes")
    print(f"URL after redirects: {r.url}")
    
    # 保存响应以便检查
    with open("gbw_download_response.html", "wb") as f:
        f.write(r.content)
    print(f"响应已保存到 gbw_download_response.html")
    
    # 检查是否是 PDF
    if r.content[:4] == b'%PDF':
        print(f"✓ 这是一个 PDF 文件!")
        with open("test_gbw_final.pdf", "wb") as f:
            f.write(r.content)
        print(f"PDF 已保存到 test_gbw_final.pdf")
    else:
        print(f"✗ 不是 PDF，可能是验证码页面")
        print(f"前100字节: {r.content[:100]}")
        
except Exception as e:
    print(f"错误: {e}")
