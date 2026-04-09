import React from 'react';
import { Card, Typography, Empty } from 'antd';
import { ClockCircleOutlined, SearchOutlined } from '@ant-design/icons';

const { Text } = Typography;

const HistoryPanel = ({ history, onHistoryClick }) => {
    return (
        <Card
            title={<><ClockCircleOutlined /> 历史记录</>}
            size="small"
            style={{ marginBottom: 16 }}
            styles={{ body: { maxHeight: 300, overflow: 'auto', padding: 0 } }}
        >
            {history.length === 0 ? (
                <div style={{ padding: '16px 0' }}>
                    <Empty description="暂无搜索历史" image={Empty.PRESENTED_IMAGE_SIMPLE} />
                </div>
            ) : (
                <div style={{ padding: '8px 12px' }}>
                    {history.map((item, index) => (
                        <div
                            key={index}
                            style={{ 
                                cursor: 'pointer', 
                                padding: '8px 0',
                                borderBottom: index < history.length - 1 ? '1px solid #f0f0f0' : 'none',
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center'
                            }}
                            onClick={() => onHistoryClick(item.query)}
                        >
                            <Text ellipsis style={{ fontSize: 13, display: 'flex', alignItems: 'center', gap: 4 }}>
                                <SearchOutlined style={{ color: '#bfbfbf' }} /> {item.query}
                            </Text>
                            <Text type="secondary" style={{ fontSize: 12, marginLeft: 8 }}>
                                {item.time}
                            </Text>
                        </div>
                    ))}
                </div>
            )}
        </Card>
    );
};

export default HistoryPanel;
