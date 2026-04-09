import React, { useState, useRef, useCallback } from 'react';
import {
    Card,
    Upload,
    Button,
    Progress,
    Space,
    message,
    Tag,
    Typography,
    Row,
    Col,
    Alert,
    Table,
    Flex
} from 'antd';
import {
    UploadOutlined,
    CloudUploadOutlined,
    DownloadOutlined,
    ReloadOutlined,
    FileExcelOutlined,
    CheckCircleOutlined,
    CloseCircleOutlined,
    SyncOutlined,
    ArrowLeftOutlined
} from '@ant-design/icons';

const { Text } = Typography;
const { Dragger } = Upload;

// API 基础 URL
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

const ExcelCompletionPage = ({ onBack }) => {
    const [file, setFile] = useState(null);
    const [uploading, setUploading] = useState(false);
    const [taskId, setTaskId] = useState(null);
    const [taskStatus, setTaskStatus] = useState(null);
    const pollIntervalRef = useRef(null);

    // 文件上传配置
    const uploadProps = {
        name: 'file',
        multiple: false,
        accept: '.xlsx,.xls,.csv,.txt',
        beforeUpload: (file) => {
            setFile(file);
            return false; // 阻止自动上传
        },
        onRemove: () => {
            setFile(null);
        },
        fileList: file ? [file] : [],
    };

    // 开始处理
    const handleStartProcess = async () => {
        if (!file) {
            message.warning('请先选择文件');
            return;
        }

        setUploading(true);
        setTaskStatus(null);

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch(`${API_BASE}/excel-completion/upload`, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '上传失败');
            }

            const data = await response.json();
            setTaskId(data.task_id);
            message.success('任务已创建，开始处理...');

            // 开始轮询状态
            startPolling(data.task_id);
        } catch (error) {
            message.error(`处理失败: ${error.message}`);
            setUploading(false);
        }
    };

    // 开始轮询
    const startPolling = useCallback((taskId) => {
        if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
        }

        pollIntervalRef.current = setInterval(async () => {
            try {
                const response = await fetch(`${API_BASE}/excel-completion/status/${taskId}`);
                if (!response.ok) throw new Error('获取状态失败');

                const status = await response.json();
                setTaskStatus(status);

                if (status.status === 'completed' || status.status === 'failed') {
                    clearInterval(pollIntervalRef.current);
                    pollIntervalRef.current = null;
                    setUploading(false);

                    if (status.status === 'completed') {
                        message.success('处理完成！');
                    } else {
                        message.error(`处理失败: ${status.error}`);
                    }
                }
            } catch (error) {
                console.error('轮询失败:', error);
            }
        }, 1000);
    }, []);

    // 下载结果
    const handleDownloadExcel = () => {
        if (!taskId) return;
        window.open(`${API_BASE}/excel-completion/download/${taskId}`, '_blank');
    };

    const handleDownloadCSV = () => {
        if (!taskId) return;
        window.open(`${API_BASE}/excel-completion/download-csv/${taskId}`, '_blank');
    };

    // 重置
    const handleReset = () => {
        if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
        }
        setFile(null);
        setTaskId(null);
        setTaskStatus(null);
        setUploading(false);
    };

    return (
        <div style={{ padding: '24px', background: 'var(--ant-color-bg-layout)', minHeight: '100vh', boxSizing: 'border-box' }}>
            <Card
                title={
                    <Space>
                        {onBack && (
                            <Button
                                type="text"
                                icon={<ArrowLeftOutlined />}
                                onClick={onBack}
                                style={{ marginRight: 8 }}
                            >
                                返回搜索
                            </Button>
                        )}
                        <FileExcelOutlined style={{ fontSize: 20, color: 'var(--ant-color-success)' }} />
                        <span>Excel 导出 - 标准号补全</span>
                    </Space>
                }
                style={{ marginBottom: 16 }}
            >
                {/* 文件上传区 */}
                <Row gutter={16}>
                    <Col span={16}>
                        <Dragger {...uploadProps} style={{ marginBottom: 16 }}>
                            <p className="ant-upload-drag-icon">
                                <CloudUploadOutlined style={{ color: 'var(--ant-color-primary)', fontSize: 48 }} />
                            </p>
                            <p className="ant-upload-text">点击或拖拽文件到这里</p>
                            <p className="ant-upload-hint">
                                支持 Excel (.xlsx, .xls)、CSV、TXT 文件
                            </p>
                        </Dragger>
                    </Col>
                    <Col span={8}>
                        <Flex vertical gap="small" style={{ width: '100%' }}>
                            <Button
                                type="primary"
                                icon={<UploadOutlined />}
                                onClick={handleStartProcess}
                                loading={uploading}
                                disabled={!file}
                                block
                                size="large"
                            >
                                开始补全
                            </Button>
                            <Button
                                icon={<ReloadOutlined />}
                                onClick={handleReset}
                                block
                            >
                                重置
                            </Button>
                        </Flex>
                    </Col>
                </Row>

                {/* 功能说明 */}
                <Alert
                    message="功能说明"
                    description={
                        <ul style={{ margin: 0, paddingLeft: 20 }}>
                            <li>自动识别标准号列（第一列或包含"标准号"的列）</li>
                            <li>将不完整标准号（如 "GB 50325"）补全为完整格式（如 "GB 50325-2020"）</li>
                            <li>自动获取标准名称</li>
                            <li>结果导出为带格式的 Excel 文件</li>
                        </ul>
                    }
                    type="info"
                    showIcon
                    style={{ marginTop: 16 }}
                />
            </Card>

            {/* 处理进度 */}
            {taskStatus && (
                <Card
                    title={
                        <Space>
                            {taskStatus.status === 'processing' && <SyncOutlined spin />}
                            {taskStatus.status === 'completed' && <CheckCircleOutlined style={{ color: '#52c41a' }} />}
                            {taskStatus.status === 'failed' && <CloseCircleOutlined style={{ color: '#ff4d4f' }} />}
                            <span>处理进度</span>
                        </Space>
                    }
                    style={{ marginBottom: 16 }}
                >
                    <Row gutter={16} style={{ marginBottom: 16 }}>
                        <Col span={15}>
                            <Progress
                                percent={taskStatus.progress}
                                status={
                                    taskStatus.status === 'failed' ? 'exception' :
                                        taskStatus.status === 'completed' ? 'success' : 'active'
                                }
                            />
                        </Col>
                        <Col span={9}>
                            <Space size="large">
                                <Text>当前: {taskStatus.current_row}/{taskStatus.total}</Text>
                                <Text type="success">成功: {taskStatus.success_count}</Text>
                                <Text type="danger">失败: {taskStatus.fail_count}</Text>
                                <Text type="secondary">耗时: {taskStatus.elapsed_time}s</Text>
                            </Space>
                        </Col>
                    </Row>

                    {/* 日志 */}
                    <Card
                        title="处理日志"
                        size="small"
                        style={{ maxHeight: 200, overflow: 'auto' }}
                        styles={{ body: { padding: '8px 12px' } }}
                    >
                        {taskStatus.logs?.map((log, index) => (
                            <div key={index} style={{ fontFamily: 'monospace', fontSize: 12, padding: '2px 0' }}>
                                {log}
                            </div>
                        ))}
                    </Card>

                    {/* 下载按钮 */}
                    {taskStatus.status === 'completed' && (
                        <Space style={{ marginTop: 16 }}>
                            <Button
                                type="primary"
                                icon={<DownloadOutlined />}
                                onClick={handleDownloadExcel}
                                style={{
                                    background: '#52c41a',
                                    borderColor: '#52c41a'
                                }}
                            >
                                下载 Excel
                            </Button>
                            <Button
                                icon={<DownloadOutlined />}
                                onClick={handleDownloadCSV}
                            >
                                下载 CSV
                            </Button>
                        </Space>
                    )}
                </Card>
            )}
        </div>
    );
};

export default ExcelCompletionPage;
