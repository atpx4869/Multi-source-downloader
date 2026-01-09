#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试优化后的识别逻辑
- 显示源速度测试结果
- 展示优先级搜索过程
- 对比优化前后的性能
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from web_app.excel_standard_processor import StandardProcessor


def test_optimized_recognition():
    """测试优化后的识别逻辑"""
    
    processor = StandardProcessor()
    
    print("\n" + "="*70)
    print("🚀 优化识别逻辑测试")
    print("="*70)
    
    # 测试用例
    test_cases = [
        ("GB/T 3324", "不带年代号（查找现行）"),
        ("GB/T 3324-2024", "带年代号（查询名称）"),
        ("GB/T 8948-2025", "带年代号（查询名称）"),
        ("QB/T 5353-2018", "带年代号（行标）"),
        ("GB/T 38465-2020", "带年代号（查询名称）"),
    ]
    
    for std_no, description in test_cases:
        print(f"\n{'─'*70}")
        print(f"📋 测试: {std_no} ({description})")
        print(f"{'─'*70}")
        
        try:
            full_std_no, name, status = processor.process_standard(std_no)
            
            print(f"\n✅ 识别结果:")
            print(f"   标准号: {full_std_no}")
            print(f"   名称:   {name[:50]}..." if len(name) > 50 else f"   名称:   {name}")
            print(f"   状态:   {status}")
            
        except Exception as e:
            print(f"\n❌ 识别失败: {e}")
    
    print(f"\n{'='*70}")
    print("✨ 测试完成")
    print(f"{'='*70}")
    
    # 显示速度统计
    if processor.source_speeds:
        print(f"\n📊 源速度统计:")
        print(f"{'─'*70}")
        for source_type, speed in sorted(processor.source_speeds.items(), 
                                         key=lambda x: x[1] if x[1] != float('inf') else 9999):
            if speed == float('inf'):
                status = "❌ 未启用"
            else:
                status = f"✓ {speed:.2f}s"
            print(f"  {source_type.value:4s}: {status}")
        
        print(f"\n🎯 优先级顺序（从快到慢）:")
        for i, st in enumerate(processor.source_order, 1):
            speed = processor.source_speeds[st]
            if speed != float('inf'):
                print(f"  {i}. {st.value} ({speed:.2f}s)")


if __name__ == '__main__':
    test_optimized_recognition()
