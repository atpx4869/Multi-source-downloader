import React from 'react';
import { Table, Tag, Button, Space, Checkbox, Typography } from 'antd';
import { DownloadOutlined } from '@ant-design/icons';

const { Text } = Typography;

const ResultTable = ({
    results,
    loading,
    selectedItems,
    onSelectionChange,
    onDownload
}) => {
    const columns = [
        {
            title: '标准信息',
            key: 'info',
            render: (record) => (
                <div>
                    {/* 第一行：标准号 + 时间信息 */}
                    <div style={{ marginBottom: 6 }}>
                        <Text strong style={{ fontSize: 16, marginRight: 12 }}>
                            {record.std_no}
                        </Text>
                        {record.cached && (
                            <Tag color="orange" style={{ marginRight: 8 }}>
                                💾 已缓存
                            </Tag>
                        )}
                        <Space size={4}>
                            {record.publish_date && (
                                <Tag color="blue">📅 发布: {record.publish_date}</Tag>
                            )}
                            {record.implement_date && (
                                <Tag color="cyan">⚡ 实施: {record.implement_date}</Tag>
                            )}
                            {record.status && (
                                <Tag color={record.status === '现行' ? 'green' : 'red'}>
                                    ● {record.status}
                                </Tag>
                            )}
                            <Tag>{record.source}</Tag>
                        </Space>
                    </div>
                    {/* 第二行：标准名称 */}
                    <div>
                        <Text style={{ color: '#666' }}>
                            {record.name}
                        </Text>
                    </div>
                </div>
            ),
        },
        {
            title: '操作',
            key: 'action',
            width: 120,
            render: (record) => (
                <Button
                    type="primary"
                    icon={<DownloadOutlined />}
                    onClick={() => onDownload(record)}
                    disabled={!record.has_pdf}
                >
                    下载
                </Button>
            ),
        },
    ];

    const rowSelection = {
        selectedRowKeys: selectedItems.map(item => item.std_no),
        onChange: (selectedRowKeys, selectedRows) => {
            onSelectionChange(selectedRows);
        },
        getCheckboxProps: (record) => ({
            disabled: !record.has_pdf,
        }),
    };

    return (
        <Table
            rowSelection={rowSelection}
            columns={columns}
            dataSource={results}
            loading={loading}
            rowKey="std_no"
            pagination={{
                pageSize: 20,
                showSizeChanger: true,
                showTotal: (total) => `共 ${total} 条结果`,
                pageSizeOptions: ['10', '20', '50', '100'],
            }}
            size="middle"
            style={{
                background: 'white',
                borderRadius: 8,
            }}
        />
    );
};

export default ResultTable;
