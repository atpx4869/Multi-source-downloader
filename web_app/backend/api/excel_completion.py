"""
Excel 标准号补全 API 路由
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from typing import Optional

router = APIRouter(prefix="/excel-completion", tags=["excel-completion"])

# 服务实例（由 main.py 注入）
_service: Optional['ExcelCompletionService'] = None


def set_service(service):
    """设置服务实例"""
    global _service
    _service = service


@router.post("/upload")
async def upload_and_process(
    file: UploadFile = File(...),
    std_column: Optional[str] = None
):
    """
    上传文件并开始处理
    
    Args:
        file: 上传的文件（Excel/CSV/TXT）
        std_column: 标准号列名（可选，自动识别）
    
    Returns:
        任务信息
    """
    if not _service:
        raise HTTPException(status_code=500, detail="服务未初始化")
    
    # 验证文件类型
    allowed_extensions = {'.xlsx', '.xls', '.csv', '.txt'}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {file_ext}。支持的类型: {', '.join(allowed_extensions)}"
        )
    
    # 保存上传的文件
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    
    # 生成唯一文件名
    import uuid
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    temp_path = upload_dir / unique_filename
    
    try:
        # 保存文件
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # 创建任务
        task_id = _service.create_task()
        
        # 开始处理
        _service.process_file(
            task_id=task_id,
            file_path=str(temp_path),
            std_column=std_column
        )
        
        return {
            'task_id': task_id,
            'message': '任务已创建，正在处理中...',
            'filename': file.filename
        }
    
    except Exception as e:
        # 清理临时文件
        if temp_path.exists():
            temp_path.unlink()
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@router.get("/status/{task_id}")
async def get_status(task_id: str):
    """
    获取任务状态
    
    Args:
        task_id: 任务ID
    
    Returns:
        任务状态信息
    """
    if not _service:
        raise HTTPException(status_code=500, detail="服务未初始化")
    
    task = _service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return task.to_dict()


@router.get("/download/{task_id}")
async def download_result(task_id: str):
    """
    下载 Excel 结果
    
    Args:
        task_id: 任务ID
    
    Returns:
        Excel 文件
    """
    if not _service:
        raise HTTPException(status_code=500, detail="服务未初始化")
    
    task = _service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task.status != 'completed':
        raise HTTPException(status_code=400, detail="任务未完成")
    
    if not task.result_file or not Path(task.result_file).exists():
        raise HTTPException(status_code=404, detail="结果文件不存在")
    
    return FileResponse(
        path=task.result_file,
        filename=f"标准号补全结果_{task_id[:8]}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@router.get("/download-csv/{task_id}")
async def download_csv(task_id: str):
    """
    下载 CSV 结果
    
    Args:
        task_id: 任务ID
    
    Returns:
        CSV 文件
    """
    if not _service:
        raise HTTPException(status_code=500, detail="服务未初始化")
    
    task = _service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task.status != 'completed':
        raise HTTPException(status_code=400, detail="任务未完成")
    
    # 导出为 CSV
    csv_path = _service.export_csv(task_id)
    if not csv_path or not Path(csv_path).exists():
        raise HTTPException(status_code=500, detail="CSV 导出失败")
    
    return FileResponse(
        path=csv_path,
        filename=f"标准号补全结果_{task_id[:8]}.csv",
        media_type="text/csv"
    )
