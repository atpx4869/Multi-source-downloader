import React from 'react';
import { Card, Radio, Typography } from 'antd';
import { FilterOutlined } from '@ant-design/icons';

const { Text } = Typography;

const FilterPanel = ({ standardTypeFilter, onStandardTypeChange, standardTypes }) => {
    // 获取所有类型并按数量排序
    const sortedTypes = Object.entries(standardTypes)
        .filter(([key]) => key !== 'all')
        .sort((a, b) => b[1] - a[1]);

    return (
        <Card
            title={<><FilterOutlined /> 筛选</>}
            size="small"
        >
            <div style={{ marginBottom: 12 }}>
                <Text style={{ fontSize: 12, display: 'block', marginBottom: 8 }}>标准类型</Text>
                <Radio.Group
                    value={standardTypeFilter}
                    onChange={(e) => onStandardTypeChange(e.target.value)}
                    style={{ width: '100%', display: 'flex', flexWrap: 'wrap', gap: '6px' }}
                >
                    <Radio.Button
                        value="all"
                        style={{
                            fontSize: 12
                        }}
                    >
                        全部 ({standardTypes.all || 0})
                    </Radio.Button>
                    {sortedTypes.map(([type, count]) => (
                        <Radio.Button
                            key={type}
                            value={type}
                            style={{
                                fontSize: 12
                            }}
                        >
                            {type} ({count})
                        </Radio.Button>
                    ))}
                </Radio.Group>
            </div>
        </Card>
    );
};

export default FilterPanel;
