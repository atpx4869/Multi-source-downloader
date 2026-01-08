#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
标准号处理Web应用
基于Flask的Web界面，用于批量处理Excel中的标准号
"""
import os
import sys
import uuid
import time
import threading
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, send_file, jsonify
from werkzeug.utils import secure_filename
import pandas as pd

# 项目根目录（上一级）
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from api import APIRouter, SourceType
from web_app.excel_standard_processor import StandardProcessor

# 路径配置（使用绝对路径，防止工作目录变化）
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / 'uploads'
RESULT_FOLDER = BASE_DIR / 'results'

app = Flask(__name__, template_folder=str(BASE_DIR / 'templates'))
app.secret_key = 'multi-source-downloader-secret-key-2026'
app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER)
app.config['RESULT_FOLDER'] = str(RESULT_FOLDER)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# 确保上传和结果目录存在
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
RESULT_FOLDER.mkdir(parents=True, exist_ok=True)

# 存储处理任务的状态
tasks = {}


class ProcessTask:
    """处理任务"""
    def __init__(self, task_id):
        self.task_id = task_id
        self.status = 'pending'  # pending, processing, completed, failed
        self.progress = 0
        self.total = 0
        self.current_row = 0
        self.success_count = 0
        self.fail_count = 0
        self.logs = []
        self.result_file = None
        self.error = None
        self.start_time = time.time()
        self.end_time = None
    
    def add_log(self, message):
        """添加日志"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.logs.append(f"[{timestamp}] {message}")
    
    def to_dict(self):
        """转换为字典"""
        elapsed = time.time() - self.start_time
        if self.end_time:
            elapsed = self.end_time - self.start_time
        
        return {
            'task_id': self.task_id,
            'status': self.status,
            'progress': self.progress,
            'total': self.total,
            'current_row': self.current_row,
            'success_count': self.success_count,
            'fail_count': self.fail_count,
            'logs': self.logs[-10:],  # 只返回最近10条日志
            'result_file': self.result_file,
            'error': self.error,
            'elapsed_time': round(elapsed, 1)
        }


def allowed_file(filename):
    """检查文件类型"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'xlsx', 'xls'}


def process_excel_task(task_id, input_file, std_no_col, start_row, result_col_no, result_col_name):
    """后台处理Excel任务"""
    task = tasks.get(task_id)
    if not task:
        return
    
    try:
        task.status = 'processing'
        task.add_log(f"开始处理文件: {os.path.basename(input_file)}")
        
        # 读取Excel
        df = pd.read_excel(input_file)
        task.add_log(f"成功读取Excel文件，共 {len(df)} 行")
        
        # 列索引转换
        col_idx = ord(std_no_col.upper()) - ord('A')
        result_idx_no = ord(result_col_no.upper()) - ord('A')
        result_idx_name = ord(result_col_name.upper()) - ord('A')
        
        # 确保结果列存在
        while len(df.columns) <= max(result_idx_no, result_idx_name):
            df[f'新列{len(df.columns)}'] = ''
        
        # 计算总数
        task.total = len(df) - (start_row - 1)
        task.add_log(f"配置: 标准号列={std_no_col}, 开始行={start_row}")
        task.add_log(f"需要处理 {task.total} 行数据")
        
        # 创建处理器
        processor = StandardProcessor()
        
        # 处理每一行
        for idx in range(start_row - 1, len(df)):
            row_num = idx + 1
            task.current_row = row_num
            
            if col_idx >= len(df.columns):
                task.add_log(f"行 {row_num}: 列索引超出范围，跳过")
                continue
            
            std_no = df.iloc[idx, col_idx]
            
            if pd.isna(std_no) or str(std_no).strip() == '':
                task.add_log(f"行 {row_num}: 空值，跳过")
                task.progress = idx - start_row + 2
                continue
            
            task.add_log(f"处理行 {row_num}: {std_no}")
            
            # 处理标准号
            try:
                full_std_no, name, status = processor.process_standard(str(std_no))
                
                # 写入结果
                df.iloc[idx, result_idx_no] = full_std_no
                df.iloc[idx, result_idx_name] = name
                
                if "成功" in status:
                    task.success_count += 1
                    task.add_log(f"  ✅ 成功: {full_std_no}")
                else:
                    task.fail_count += 1
                    task.add_log(f"  ❌ 失败: {status}")
            except Exception as e:
                task.fail_count += 1
                task.add_log(f"  ❌ 错误: {str(e)}")
            
            task.progress = idx - start_row + 2
        
        # 保存结果
        result_filename = f"result_{task_id}.xlsx"
        result_path = RESULT_FOLDER / result_filename
        df.to_excel(result_path, index=False)
        
        task.result_file = result_filename
        task.status = 'completed'
        task.end_time = time.time()
        task.add_log(f"✅ 处理完成！成功 {task.success_count} 个，失败 {task.fail_count} 个")
        
    except Exception as e:
        task.status = 'failed'
        task.error = str(e)
        task.end_time = time.time()
        task.add_log(f"❌ 处理失败: {str(e)}")


@app.route('/')
def index():
    """首页"""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """上传文件"""
    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': '只支持 .xlsx 和 .xls 格式'}), 400
    
    # 保存文件
    task_id = str(uuid.uuid4())
    filename = secure_filename(file.filename)
    filepath = UPLOAD_FOLDER / f"{task_id}_{filename}"
    file.save(filepath)
    
    # 获取参数
    std_no_col = request.form.get('std_no_col', 'A').upper()
    start_row = int(request.form.get('start_row', 2))
    result_col_no = request.form.get('result_col_no', 'B').upper()
    result_col_name = request.form.get('result_col_name', 'C').upper()
    
    # 创建任务
    task = ProcessTask(task_id)
    tasks[task_id] = task
    
    # 启动后台处理
    thread = threading.Thread(
        target=process_excel_task,
        args=(task_id, filepath, std_no_col, start_row, result_col_no, result_col_name)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'task_id': task_id,
        'message': '文件上传成功，开始处理'
    })


@app.route('/status/<task_id>')
def get_status(task_id):
    """获取任务状态"""
    task = tasks.get(task_id)
    if not task:
        return jsonify({'error': '任务不存在'}), 404
    
    return jsonify(task.to_dict())


@app.route('/download/<task_id>')
def download_result(task_id):
    """下载结果文件"""
    task = tasks.get(task_id)
    if not task or not task.result_file:
        return jsonify({'error': '结果文件不存在'}), 404
    
    result_path = RESULT_FOLDER / task.result_file
    if not result_path.exists():
        return jsonify({'error': '文件已被删除'}), 404
    
    return send_file(
        result_path,
        as_attachment=True,
        download_name=f"标准号处理结果_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    )


@app.route('/api/search', methods=['POST'])
def api_search():
    """API: 搜索单个标准"""
    data = request.get_json()
    std_no = data.get('std_no', '').strip()
    
    if not std_no:
        return jsonify({'error': '标准号不能为空'}), 400
    
    try:
        processor = StandardProcessor()
        full_std_no, name, status = processor.process_standard(std_no)
        
        return jsonify({
            'std_no': std_no,
            'full_std_no': full_std_no,
            'name': name,
            'status': status
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health')
def health_check():
    """健康检查"""
    try:
        router = APIRouter()
        health = router.check_health()
        return jsonify(health.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("\n" + "="*60)
    print("标准号处理Web应用".center(60))
    print("="*60)
    print("\n🚀 启动服务器...")
    print("📍 访问地址: http://127.0.0.1:5000")
    print("🔧 按 Ctrl+C 停止服务\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
