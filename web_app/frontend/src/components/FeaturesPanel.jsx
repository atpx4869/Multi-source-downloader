import React from 'react';
import { Card, List, Typography, Tag } from 'antd';
import { ThunderboltOutlined } from '@ant-design/icons';

const { Text } = Typography;

const FeaturesPanel = () => {
    const features = [
        { name: '批量下载', status: 'active', color: 'green' },
        { name: '导出Excel', status: 'planned', color: 'blue' },
        { name: '高级筛选', status: 'planned', color: 'blue' },
        { name: '收藏夹', status: 'planned', color: 'blue' },
    ];

    return (
        <Card
            title={<><ThunderboltOutlined /> 待做功能</>}
            size="small"
            bodyStyle={{ maxHeight: 200, overflow: 'auto' }}
        >
            <List
                size="small"
                dataSource={features}
                renderItem={(item) => (
                    <List.Item style={{ padding: '6px 0' }}>
                        <Text style={{ fontSize: 13 }}>{item.name}</Text>
                        <Tag color={item.color} style={{ fontSize: 11 }}>
                            {item.status === 'active' ? '已启用' : '计划中'}
                        </Tag>
                    </List.Item>
                )}
            />
        </Card>
    );
};

export default FeaturesPanel;
