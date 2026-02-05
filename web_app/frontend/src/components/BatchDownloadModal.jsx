import React from 'react';
import { Modal, List, Progress, Tag, Button, Space, Typography } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined, LoadingOutlined } from '@ant-design/icons';

const { Text } = Typography;

const BatchDownloadModal = ({ visible, onClose, downloadQueue }) => {
    const getStatusIcon = (status) => {
        switch (status) {
            case 'success':
                return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
            case 'error':
                return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
            case 'downloading':
                return <LoadingOutlined />;
            default:
                return null;
        }
    };

    const getStatusTag = (item) => {
        switch (item.status) {
            case 'success':
                return <Tag color="success">✓ 完成</Tag>;
            case 'error':
                return <Tag color="error">✗ 失败</Tag>;
            case 'downloading':
                return <Progress percent={item.progress || 0} size="small" style={{ width: 100 }} />;
            case 'pending':
                return <Tag>等待中...</Tag>;
            default:
                return null;
        }
    };

    const completedCount = downloadQueue.filter(item => item.status === 'success').length;
    const failedCount = downloadQueue.filter(item => item.status === 'error').length;
    const totalCount = downloadQueue.length;

    return (
        <Modal
            title="批量下载进度"
            open={visible}
            onCancel={onClose}
            footer={[
                <Button key="close" type="primary" onClick={onClose}>
                    关闭
                </Button>
            ]}
            width={700}
        >
            <div style={{ marginBottom: 16 }}>
                <Space>
                    <Text>总计: {totalCount}</Text>
                    <Text type="success">成功: {completedCount}</Text>
                    <Text type="danger">失败: {failedCount}</Text>
                </Space>
            </div>

            <List
                dataSource={downloadQueue}
                renderItem={(item) => (
                    <List.Item>
                        <List.Item.Meta
                            avatar={getStatusIcon(item.status)}
                            title={<Text strong>{item.std_no}</Text>}
                            description={item.name}
                        />
                        <div>
                            {getStatusTag(item)}
                            {item.error && (
                                <Text type="danger" style={{ fontSize: 12, display: 'block', marginTop: 4 }}>
                                    {item.error}
                                </Text>
                            )}
                        </div>
                    </List.Item>
                )}
                style={{ maxHeight: 400, overflow: 'auto' }}
            />
        </Modal>
    );
};

export default BatchDownloadModal;
