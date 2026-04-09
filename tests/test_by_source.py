#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BY 源连通性和功能测试
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sources.by import BYSource


def test_by_availability():
    """测试 BY 源是否可用"""
    print("=" * 60)
    print("BY 源连通性测试")
    print("=" * 60)
    
    source = BYSource()
    
    # 1. 检查可用性
    print("\n1️⃣  检查内网连通性...")
    available = source.is_available()
    if available:
        print("   ✅ BY 内网可访问")
    else:
        print("   ❌ BY 内网不可访问（可能不在公司网络内）")
        print("   💡 提示：BY 源需要在公司内网才能使用")
        return False
    
    # 2. 测试登录
    print("\n2️⃣  测试内网登录...")
    try:
        login_result = source._ensure_login()
        if login_result:
            print("   ✅ 登录成功")
        else:
            print("   ❌ 登录失败")
            return False
    except Exception as e:
        print(f"   ❌ 登录异常: {e}")
        return False
    
    # 3. 测试搜索
    print("\n3️⃣  测试搜索功能...")
    try:
        results = source.search("3324")
        if results:
            print(f"   ✅ 搜索成功，找到 {len(results)} 条结果")
            for r in results[:3]:  # 显示前 3 个
                print(f"      - {r.std_no}: {r.name}")
        else:
            print("   ⚠️  搜索无结果（可能网络超时或无该标准）")
    except Exception as e:
        print(f"   ❌ 搜索异常: {e}")
        return False
    
    # 4. 测试下载
    print("\n4️⃣  测试下载功能...")
    if results:
        try:
            test_item = results[0]
            output_dir = Path("./test_by_download")
            output_dir.mkdir(exist_ok=True)
            
            result = source.download(test_item, output_dir)
            if result.success:
                print(f"   ✅ 下载成功: {result.file_path}")
            else:
                print(f"   ❌ 下载失败: {result.error}")
        except Exception as e:
            print(f"   ❌ 下载异常: {e}")
            return False
    else:
        print("   ⏭️  跳过下载测试（无搜索结果）")
    
    print("\n" + "=" * 60)
    print("✅ BY 源可用性测试完成")
    print("=" * 60)
    return True


def test_by_connection_only():
    """仅测试连接（快速）"""
    print("快速检查 BY 源连通性...")
    source = BYSource()
    
    if not source.is_available():
        print("❌ BY 内网不可访问")
        print("💡 BY 源需要在标院公司内网才能使用")
        return False
    
    print("✅ BY 内网可访问")
    
    try:
        if source._ensure_login():
            print("✅ 登录成功")
            return True
        else:
            print("❌ 登录失败（检查用户名密码）")
            return False
    except Exception as e:
        print(f"❌ 连接异常: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="BY 源测试")
    parser.add_argument("--quick", action="store_true", help="仅测试连接（快速模式）")
    args = parser.parse_args()
    
    if args.quick:
        success = test_by_connection_only()
    else:
        success = test_by_availability()
    
    sys.exit(0 if success else 1)
