# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Body
from typing import List, Optional
import asyncio
import re
from web_app.backend.services.search import SearchService

router = APIRouter(prefix="/batch", tags=["batch"])

# 全局服务实例（将在main.py中注入）
search_service: Optional[SearchService] = None

def set_service(service: SearchService):
    """设置搜索服务实例"""
    global search_service
    search_service = service

def extract_year(std_no: str) -> int:
    """从标准号中提取年份"""
    match = re.search(r'-(\d{4})$', std_no)
    return int(match.group(1)) if match else 0

@router.post("/resolve")
async def resolve_batch_standards(std_ids: List[str] = Body(...)):
    """
    将标准号列表解析为对应的最佳匹配对象
    支持逻辑：优先“现行”，其次“最新年份”
    """
    if not std_ids:
        return {"results": []}

    if not search_service:
        raise HTTPException(status_code=500, detail="Search service not initialized")
    
    async def resolve_one(std_id: str):
        std_id = std_id.strip()
        if not std_id:
            return None
            
        try:
            # 使用 SearchService 搜索所有源
            # search_all 返回 Dict[str, SearchResponse]
            results_dict = await search_service.search_all(std_id)
            
            # 合并所有源的结果
            all_items = []
            for source, response in results_dict.items():
                if response.items:
                    all_items.extend(response.items)

            if not all_items:
                return {
                    "input_id": std_id,
                    "resolved": None,
                    "status": "not_found"
                }

            # 2. 筛选并合并
            groups = {}
            for item in all_items:
                # 归约：去除空格，转大写
                key = (item.std_no or "").replace(" ", "").upper()
                if not key: continue
                
                if key not in groups:
                    groups[key] = []
                groups[key].append(item)

            # 找出最佳匹配的组
            best_key = None
            # 1. 如果有输入 ID 的精确匹配组
            clean_input = std_id.replace(" ", "").upper()
            if clean_input in groups:
                best_key = clean_input
            else:
                # 2. 否则按逻辑：优先选含有 "现行" 状态的组，再选年份最新的
                sorted_keys = list(groups.keys())
                
                def get_key_score(k):
                    group = groups[k]
                    has_current = any("现行" in (i.status or "") for i in group)
                    year = max(extract_year(i.std_no or "") for i in group)
                    has_pdf = any(i.has_pdf for i in group)
                    return (1 if has_current else 0, year, 1 if has_pdf else 0)
                
                sorted_keys.sort(key=get_key_score, reverse=True)
                best_key = sorted_keys[0]

            # 合并 best_key 组内的所有项
            group_items = groups[best_key]
            
            # 选取一个“基准”项（通常选优先级最高的源：GBW > BY > ZBY）
            source_priority = {"GBW": 3, "BY": 2, "ZBY": 1}
            group_items.sort(key=lambda x: source_priority.get(x.sources[0] if x.sources else "", 0), reverse=True)
            
            merged = group_items[0]
            all_sources = []
            all_source_meta = {}
            any_has_pdf = False
            
            for item in group_items:
                for src in item.sources:
                    if src not in all_sources:
                        all_sources.append(src)
                if item.source_meta:
                    all_source_meta.update(item.source_meta)
                if item.has_pdf:
                    any_has_pdf = True
            
            # 按照优先级排序来源
            all_sources.sort(key=lambda s: source_priority.get(s, 0), reverse=True)
            
            # 更新合并项
            merged_dict = merged.dict() if hasattr(merged, 'dict') else merged
            merged_dict['sources'] = all_sources
            merged_dict['source_meta'] = all_source_meta
            merged_dict['has_pdf'] = any_has_pdf
            # 设置首选源（用于前端下载时如果不使用/first API的情况）
            merged_dict['source'] = all_sources[0] if all_sources else "ZBY"

            return {
                "input_id": std_id,
                "resolved": merged_dict,
                "status": "success"
            }
        except Exception as e:
            return {
                "input_id": std_id,
                "resolved": None,
                "status": "error",
                "error": str(e)
            }

    # 并行处理所有 ID
    tasks = [resolve_one(sid) for sid in std_ids]
    results = await asyncio.gather(*tasks)
    
    # 过滤掉空的输入项
    final_results = [r for r in results if r is not None]
    
    return {"results": final_results}
