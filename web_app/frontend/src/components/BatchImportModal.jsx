import React, { useState } from 'react';
import { Modal, Input, Button, Table, Tag, Space, message, Divider } from 'antd';
import { batchAPI } from '../api/client';

const { TextArea } = Input;

const BatchImportModal = ({ visible, onCancel, onImport }) => {
    const [inputText, setInputText] = useState('');
    const [loading, setLoading] = useState(false);
    const [resolveResults, setResolveResults] = useState([]);
    const [selectedRowKeys, setSelectedRowKeys] = useState([]);

    // 解析输入文本
    const handleResolve = async () => {
        if (!inputText.trim()) {
            message.warning('请输入要导入的标准号');
            return;
        }

        setLoading(true);
        try {
            // 分割输入文本：换行、逗号、分号
            const ids = inputText.split(/[\n\r,，;；、]+/).map(id => id.trim()).filter(id => id);
            const uniqueIds = Array.from(new Set(ids));

            const response = await batchAPI.resolve(uniqueIds);
            setResolveResults(response.results);

            // 默认选中所有解析成功的项
            const successKeys = response.results
                .filter(r => r.status === 'success')
                .map((_, index) => index);
            setSelectedRowKeys(successKeys);

            message.success(`解析完成，共找到 ${successKeys.length} 个匹配项`);
        } catch (error) {
            console.error('解析失败:', error);
            message.error('解析失败: ' + error.message);
        } finally {
            setLoading(false);
        }
    };

    // 执行导入
    const handleConfirmImport = () => {
        const selectedItems = selectedRowKeys.map(key => resolveResults[key].resolved).filter(item => item);
        if (selectedItems.length === 0) {
            message.warning('请至少选择一个有效的标准进行下载');
            return;
        }

        onImport(selectedItems);
        // 重置状态
        setInputText('');
        setResolveResults([]);
        setSelectedRowKeys([]);
    };

    const columns = [
        {
            title: '输入标准号',
            dataIndex: 'input_id',
            key: 'input_id',
        },
        {
            title: '解析结果',
            dataIndex: 'resolved',
            key: 'std_no',
            render: (resolved) => resolved ? resolved.std_no : '-',
        },
        {
            title: '名称',
            dataIndex: 'resolved',
            key: 'std_name',
            render: (resolved) => resolved ? resolved.name : '-',
            ellipsis: true,
        },
        {
            title: '状态',
            key: 'status',
            render: (_, record) => {
                if (record.status === 'error') return <Tag color="error">解析错误</Tag>;
                if (record.status === 'not_found' || !record.resolved) return <Tag color="default">未找到</Tag>;

                const statusText = record.resolved.status || '';
                const hasPdf = record.resolved.has_pdf !== false;

                return (
                    <Space size={4}>
                        {statusText.includes('现行') ? <Tag color="success">现行</Tag> :
                            statusText.includes('废止') ? <Tag color="error">废止</Tag> :
                                <Tag color="warning">{statusText || '未知'}</Tag>}
                        {!hasPdf && <Tag color="default">🚫 无文本</Tag>}
                    </Space>
                );
            },
        },
        {
            title: '来源',
            dataIndex: 'resolved',
            key: 'source',
            render: (resolved) => {
                if (!resolved) return '-';
                const sources = resolved.sources || [resolved.source];
                return (
                    <Space size={2} wrap>
                        {sources.map(src => (
                            <Tag key={src} color="blue" style={{ marginRight: 0 }}>{src}</Tag>
                        ))}
                    </Space>
                );
            },
        },
    ];

    return (
        <Modal
            title="📦 批量导入标准号"
            open={visible}
            onCancel={onCancel}
            width={800}
            footer={[
                <Button key="cancel" onClick={onCancel}>取消</Button>,
                <Button
                    key="resolve"
                    type="primary"
                    ghost
                    loading={loading}
                    onClick={handleResolve}
                >
                    🔍 开始解析
                </Button>,
                <Button
                    key="import"
                    type="primary"
                    disabled={selectedRowKeys.length === 0}
                    onClick={handleConfirmImport}
                >
                    🚀 确认导入并下载 ({selectedRowKeys.length} 项)
                </Button>,
            ]}
        >
            <div style={{ marginBottom: 16 }}>
                <div style={{ marginBottom: 8, color: '#666' }}>
                    请输入标准号列表（支持换行、逗号或分号分割）：
                </div>
                <TextArea
                    rows={6}
                    placeholder="例如：&#10;GB/T 3324-2024&#10;GB/T 3325&#10;GB/T 10357.1"
                    value={inputText}
                    onChange={e => setInputText(e.target.value)}
                />
                <div style={{ marginTop: 4, fontSize: '12px', color: '#999' }}>
                    * 对于不带年号的标准号，系统将自动匹配现行版本或最新年份版本。
                </div>
            </div>

            {resolveResults.length > 0 && (
                <>
                    <Divider orientation="left">解析结果预审</Divider>
                    <Table
                        dataSource={resolveResults}
                        columns={columns}
                        rowKey={(_, index) => index}
                        pagination={false}
                        scroll={{ y: 300 }}
                        rowSelection={{
                            selectedRowKeys,
                            onChange: (keys) => setSelectedRowKeys(keys),
                            getCheckboxProps: (record) => ({
                                disabled: record.status !== 'success' || !record.resolved,
                            }),
                        }}
                        size="small"
                    />
                </>
            )}
        </Modal>
    );
};

export default BatchImportModal;
