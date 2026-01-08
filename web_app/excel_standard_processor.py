#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel标准号处理工具
功能：
1. 读取Excel中的标准号
2. 如果不带年代号，返回现行标准的完整编号和名称
3. 如果带年代号，返回该标准的名称
"""
import re
import sys
from pathlib import Path
from typing import Tuple, Optional
import pandas as pd

# 添加项目路径（项目根目录）
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from api import APIRouter, SourceType


class StandardProcessor:
    """标准号处理器"""
    
    def __init__(self):
        """初始化"""
        self.router = APIRouter()
        # 标准号正则：匹配 GB/T 3324 或 GB/T 3324-2024
        self.pattern = re.compile(r'^([A-Z/]+\s*\d+)(?:-(\d{4}))?$', re.IGNORECASE)
    
    def has_year(self, std_no: str) -> bool:
        """
        判断标准号是否带年代号
        
        Args:
            std_no: 标准号
            
        Returns:
            bool: True表示带年代号
        """
        std_no = std_no.strip()
        match = self.pattern.match(std_no)
        if not match:
            return False
        return match.group(2) is not None
    
    def normalize_std_no(self, std_no: str) -> str:
        """
        标准化标准号格式（去除多余空格等）
        
        Args:
            std_no: 原始标准号
            
        Returns:
            str: 标准化后的标准号
        """
        # 去除首尾空格
        std_no = std_no.strip()
        # 统一空格：GB/T 3324 或 GB/T3324 统一为 GB/T 3324
        std_no = re.sub(r'([A-Z/]+)\s*(\d+)', r'\1 \2', std_no, flags=re.IGNORECASE)
        return std_no
    
    def search_current_standard(self, base_std_no: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        搜索现行标准
        
        Args:
            base_std_no: 基础标准号（不带年代号）
            
        Returns:
            Tuple[标准号, 标准名称, 错误信息]
        """
        print(f"  🔍 搜索标准: {base_std_no}")
        
        # 尝试从多个源搜索
        results = self.router.search_all(base_std_no, limit=50)
        
        # 收集所有结果
        all_standards = []
        for source_type, response in results.items():
            if response.error:
                print(f"    ⚠️  {source_type.value} 搜索失败: {response.error}")
                continue
            
            if response.count > 0:
                print(f"    ✓ {source_type.value} 找到 {response.count} 个结果")
                all_standards.extend(response.standards)
        
        if not all_standards:
            return None, None, "未找到任何结果"
        
        # 筛选现行标准
        current_standards = [
            std for std in all_standards 
            if std.status and '现行' in std.status
        ]
        
        if not current_standards:
            # 如果没有明确标记为现行的，尝试找年份最新的
            print(f"    ⚠️  未找到明确标记为'现行'的标准，尝试查找最新版本...")
            
            # 提取带年份的标准
            year_standards = []
            for std in all_standards:
                match = re.search(r'-(\d{4})$', std.std_no)
                if match:
                    year = int(match.group(1))
                    year_standards.append((std, year))
            
            if year_standards:
                # 按年份排序，取最新的
                year_standards.sort(key=lambda x: x[1], reverse=True)
                latest_std = year_standards[0][0]
                print(f"    ✓ 找到最新版本: {latest_std.std_no} ({year_standards[0][1]}年)")
                return latest_std.std_no, latest_std.name, None
            else:
                return None, None, "未找到现行标准"
        
        # 如果有多个现行标准，选择年份最新的
        if len(current_standards) > 1:
            # 提取年份并排序
            year_standards = []
            for std in current_standards:
                match = re.search(r'-(\d{4})$', std.std_no)
                if match:
                    year = int(match.group(1))
                    year_standards.append((std, year))
            
            if year_standards:
                year_standards.sort(key=lambda x: x[1], reverse=True)
                latest_std = year_standards[0][0]
                print(f"    ✓ 找到现行标准: {latest_std.std_no}")
                return latest_std.std_no, latest_std.name, None
        
        # 返回找到的现行标准
        std = current_standards[0]
        print(f"    ✓ 找到现行标准: {std.std_no}")
        return std.std_no, std.name, None
    
    def get_standard_name(self, std_no: str) -> Tuple[Optional[str], Optional[str]]:
        """
        获取指定标准号的名称
        
        Args:
            std_no: 标准号（带年代号）
            
        Returns:
            Tuple[标准名称, 错误信息]
        """
        print(f"  🔍 查询标准: {std_no}")
        
        results = self.router.search_all(std_no, limit=10)
        
        # 收集所有结果
        all_standards = []
        for source_type, response in results.items():
            if response.error:
                print(f"    ⚠️  {source_type.value} 搜索失败: {response.error}")
                continue
            
            if response.count > 0:
                print(f"    ✓ {source_type.value} 找到 {response.count} 个结果")
                all_standards.extend(response.standards)
        
        if not all_standards:
            return None, "未找到标准"
        
        # 精确匹配标准号
        for std in all_standards:
            if std.std_no == std_no or std.std_no.replace(' ', '') == std_no.replace(' ', ''):
                print(f"    ✓ 找到标准名称: {std.name}")
                return std.name, None
        
        # 如果没有精确匹配，返回第一个结果
        std = all_standards[0]
        print(f"    ⚠️  未找到精确匹配，返回: {std.std_no} - {std.name}")
        return std.name, None
    
    def process_standard(self, std_no: str) -> Tuple[str, str, str]:
        """
        处理单个标准号
        
        Args:
            std_no: 标准号
            
        Returns:
            Tuple[完整标准号, 标准名称, 状态信息]
        """
        if not std_no or pd.isna(std_no):
            return "", "", "空值"
        
        std_no = self.normalize_std_no(str(std_no))
        print(f"\n处理标准号: {std_no}")
        
        # 判断是否带年代号
        if self.has_year(std_no):
            # 带年代号，直接查询名称
            print(f"  → 检测到带年代号，直接查询标准名称")
            name, error = self.get_standard_name(std_no)
            if error:
                return std_no, "", f"查询失败: {error}"
            return std_no, name or "", "成功"
        else:
            # 不带年代号，查找现行标准
            print(f"  → 检测到不带年代号，查找现行标准")
            full_std_no, name, error = self.search_current_standard(std_no)
            if error:
                return std_no, "", f"查询失败: {error}"
            return full_std_no or std_no, name or "", "成功"
    
    def process_excel(
        self, 
        input_file: str, 
        output_file: str = None,
        std_no_col: str = 'A',
        start_row: int = 2,
        result_col_no: str = 'B',
        result_col_name: str = 'C'
    ):
        """
        处理Excel文件
        
        Args:
            input_file: 输入Excel文件路径
            output_file: 输出Excel文件路径（默认为输入文件名_结果.xlsx）
            std_no_col: 标准号所在列（如'A'）
            start_row: 开始行（默认第2行，第1行为表头）
            result_col_no: 结果标准号列（默认'B'）
            result_col_name: 结果标准名称列（默认'C'）
        """
        print(f"\n{'='*60}")
        print(f"📁 读取Excel文件: {input_file}")
        print(f"{'='*60}")
        
        # 读取Excel
        try:
            df = pd.read_excel(input_file)
        except Exception as e:
            print(f"❌ 读取Excel失败: {e}")
            return
        
        # 列索引转换
        col_idx = ord(std_no_col.upper()) - ord('A')
        result_idx_no = ord(result_col_no.upper()) - ord('A')
        result_idx_name = ord(result_col_name.upper()) - ord('A')
        
        # 确保结果列存在
        while len(df.columns) <= max(result_idx_no, result_idx_name):
            df[f'新列{len(df.columns)}'] = ''
        
        col_names = list(df.columns)
        if len(col_names) > result_idx_no:
            result_col_no_name = col_names[result_idx_no]
        else:
            result_col_no_name = f'完整标准号'
            
        if len(col_names) > result_idx_name:
            result_col_name_name = col_names[result_idx_name]
        else:
            result_col_name_name = f'标准名称'
        
        print(f"\n配置:")
        print(f"  标准号列: {std_no_col} (列索引 {col_idx})")
        print(f"  开始行: {start_row}")
        print(f"  结果标准号列: {result_col_no}")
        print(f"  结果标准名称列: {result_col_name}")
        print(f"\n开始处理...")
        
        # 处理每一行
        success_count = 0
        fail_count = 0
        
        for idx in range(start_row - 1, len(df)):
            row_num = idx + 1
            
            if col_idx >= len(df.columns):
                print(f"\n行 {row_num}: ⚠️  列索引超出范围")
                continue
            
            std_no = df.iloc[idx, col_idx]
            
            if pd.isna(std_no) or str(std_no).strip() == '':
                print(f"\n行 {row_num}: ⏭️  空值，跳过")
                continue
            
            # 处理标准号
            full_std_no, name, status = self.process_standard(str(std_no))
            
            # 写入结果
            df.iloc[idx, result_idx_no] = full_std_no
            df.iloc[idx, result_idx_name] = name
            
            if "成功" in status:
                success_count += 1
                print(f"  ✅ 行 {row_num} 处理成功")
            else:
                fail_count += 1
                print(f"  ❌ 行 {row_num} 处理失败: {status}")
        
        # 保存结果
        if output_file is None:
            input_path = Path(input_file)
            output_file = input_path.parent / f"{input_path.stem}_结果{input_path.suffix}"
        
        print(f"\n{'='*60}")
        print(f"💾 保存结果到: {output_file}")
        
        try:
            df.to_excel(output_file, index=False)
            print(f"✅ 保存成功!")
        except Exception as e:
            print(f"❌ 保存失败: {e}")
            return
        
        # 统计
        print(f"\n{'='*60}")
        print(f"📊 处理统计:")
        print(f"  成功: {success_count}")
        print(f"  失败: {fail_count}")
        print(f"  总计: {success_count + fail_count}")
        print(f"{'='*60}\n")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Excel标准号处理工具')
    parser.add_argument('input', help='输入Excel文件路径')
    parser.add_argument('-o', '--output', help='输出Excel文件路径（默认为输入文件名_结果.xlsx）')
    parser.add_argument('-c', '--column', default='A', help='标准号所在列（默认A列）')
    parser.add_argument('-s', '--start-row', type=int, default=2, help='开始行号（默认第2行）')
    parser.add_argument('--result-no-col', default='B', help='结果标准号列（默认B列）')
    parser.add_argument('--result-name-col', default='C', help='结果标准名称列（默认C列）')
    
    args = parser.parse_args()
    
    processor = StandardProcessor()
    processor.process_excel(
        input_file=args.input,
        output_file=args.output,
        std_no_col=args.column,
        start_row=args.start_row,
        result_col_no=args.result_no_col,
        result_col_name=args.result_name_col
    )


if __name__ == '__main__':
    # 如果没有命令行参数，提供交互式界面
    if len(sys.argv) == 1:
        print("\n" + "="*60)
        print("Excel标准号处理工具".center(60))
        print("="*60 + "\n")
        
        input_file = input("请输入Excel文件路径: ").strip().strip('"')
        std_no_col = input("标准号所在列（默认A列）: ").strip() or 'A'
        start_row = input("开始行号（默认第2行）: ").strip() or '2'
        
        processor = StandardProcessor()
        processor.process_excel(
            input_file=input_file,
            std_no_col=std_no_col,
            start_row=int(start_row)
        )
        
        input("\n按回车键退出...")
    else:
        main()
