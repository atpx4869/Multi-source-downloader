import React from 'react';
import { Card, List, Typography, Empty } from 'antd';
import { ClockCircleOutlined, SearchOutlined } from '@ant-design/icons';

const { Text } = Typography;

const HistoryPanel = ({ history, onHistoryClick }) => {
    return (
        <Card
            title={<><ClockCircleOutlined /> 历史记录</>}
            size="small"
            style={{ marginBottom: 16 }}
            styles={{ body: { maxHeight: 300, overflow: 'auto' } }}
        >
            {history.length === 0 ? (
                <Empty description="暂无搜索历史" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            ) : (
                <List
                    size="small"
                    dataSource={history}
                    renderItem={(item) => (
                        <List.Item
                            style={{ cursor: 'pointer', padding: '8px 0' }}
                            onClick={() => onHistoryClick(item.query)}
                        >
                            <Text ellipsis style={{ fontSize: 13, display: 'flex', alignItems: 'center', gap: 4 }}>
                                <SearchOutlined style={{ color: '#bfbfbf' }} /> {item.query}
                            </Text>
                            <Text type="secondary" style={{ fontSize: 12, marginLeft: 8 }}>
                                {item.time}
                            </Text>
                        </List.Item>
                    )}
                />
            )}
        </Card>
    );
};

export default HistoryPanel;
