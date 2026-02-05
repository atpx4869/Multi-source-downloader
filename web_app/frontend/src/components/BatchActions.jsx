import React from 'react';
import { Space, Button, Typography, Checkbox } from 'antd';
import { DownloadOutlined, ExportOutlined } from '@ant-design/icons';

const { Text } = Typography;

const BatchActions = ({ selectedCount, onBatchDownload, onSelectAll, selectAll }) => {
    return (
        <div style={{
            marginBottom: 16,
            padding: '12px 16px',
            background: '#f7fafc',
            borderRadius: 8,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
        }}>
            <Space>
                <Checkbox
                    checked={selectAll}
                    onChange={(e) => onSelectAll(e.target.checked)}
                >
                    全选
                </Checkbox>
                <Text type="secondary">
                    已选 <Text strong>{selectedCount}</Text> 项
                </Text>
            </Space>

            <Space>
                <Button
                    type="primary"
                    icon={<DownloadOutlined />}
                    disabled={selectedCount === 0}
                    onClick={onBatchDownload}
                    style={{
                        background: selectedCount > 0 ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' : undefined,
                        border: 'none'
                    }}
                >
                    批量下载 ({selectedCount})
                </Button>
            </Space>
        </div>
    );
};

export default BatchActions;
