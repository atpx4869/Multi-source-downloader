# -*- coding: utf-8 -*-
"""
标准查新 API 路由
"""
import os
import uuid
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(prefix="/standard-check", tags=["标准查新"])

# 服务实例，由 main.py 注入
_service = None

def set_service(service):
    """设置服务实例"""
    global _service
    _service = service


@router.post("/upload")
async def upload_and_process(
    file: UploadFile = File(...),
    sources: str = Form(default="ZBY"),
    std_column: Optional[str] = Form(default=None)
):
    """
    上传文件并开始处理
    
    - **file**: Excel/CSV/TXT 文件
    - **sources**: 数据源列表，逗号分隔（如 "ZBY,BY,GBW"）
    - **std_column**: 标准号列名（可选，自动识别）
    """
    if _service is None:
        raise HTTPException(status_code=500, detail="服务未初始化")
    
    # 验证文件类型
    allowed_extensions = ['.xlsx', '.xls', '.csv', '.txt']
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"不支持的文件类型: {file_ext}，支持: {', '.join(allowed_extensions)}"
        )
    
    # 保存上传的文件
    upload_dir = Path(__file__).parent.parent.parent / 'uploads'
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    temp_filename = f"{uuid.uuid4()}{file_ext}"
    temp_path = upload_dir / temp_filename
    
    try:
        content = await file.read()
        with open(temp_path, 'wb') as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")
    
    # 解析数据源
    source_list = [s.strip() for s in sources.split(',') if s.strip()]
    if not source_list:
        source_list = ['ZBY']
    
    # 创建任务
    task_id = _service.create_task()
    
    # 在后台处理
    _service.process_file(
        task_id=task_id,
        file_path=str(temp_path),
        sources=source_list,
        std_column=std_column
    )
    
    return {
        'task_id': task_id,
        'message': '任务已创建，正在处理中...',
        'filename': file.filename
    }


@router.get("/status/{task_id}")
async def get_status(task_id: str):
    """
    获取任务状态
    
    - **task_id**: 任务ID
    """
    if _service is None:
        raise HTTPException(status_code=500, detail="服务未初始化")
    
    task = _service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return task.to_dict()


@router.get("/download/{task_id}")
async def download_result(task_id: str):
    """
    下载处理结果
    
    - **task_id**: 任务ID
    """
    if _service is None:
        raise HTTPException(status_code=500, detail="服务未初始化")
    
    task = _service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task.status != 'completed':
        raise HTTPException(status_code=400, detail="任务未完成")
    
    if not task.result_file:
        raise HTTPException(status_code=404, detail="结果文件不存在")
    
    result_path = _service.result_dir / task.result_file
    if not result_path.exists():
        raise HTTPException(status_code=404, detail="结果文件不存在")
    
    return FileResponse(
        path=str(result_path),
        filename=task.result_file,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


@router.get("/download-csv/{task_id}")
async def download_result_csv(task_id: str):
    """
    下载处理结果（CSV格式）
    
    - **task_id**: 任务ID
    """
    if _service is None:
        raise HTTPException(status_code=500, detail="服务未初始化")
    
    task = _service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task.status != 'completed':
        raise HTTPException(status_code=400, detail="任务未完成")
    
    if task.result_df is None:
        raise HTTPException(status_code=404, detail="结果数据不存在")
    
    # 生成 CSV 文件
    csv_filename = task.result_file.replace('.xlsx', '.csv') if task.result_file else f"结果_{task_id}.csv"
    csv_path = _service.result_dir / csv_filename
    
    task.result_df.to_csv(str(csv_path), index=False, encoding='utf-8-sig')
    
    return FileResponse(
        path=str(csv_path),
        filename=csv_filename,
        media_type='text/csv'
    )
