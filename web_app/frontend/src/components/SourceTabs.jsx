import React from 'react';
import { Tabs } from 'antd';

const SourceTabs = ({ activeSource, onChange, sourceCounts }) => {
    const items = [
        {
            key: 'all',
            label: `全部 ${sourceCounts.all > 0 ? `(${sourceCounts.all})` : ''}`,
        },
        {
            key: 'ZBY',
            label: `ZBY ${sourceCounts.ZBY > 0 ? `(${sourceCounts.ZBY})` : ''}`,
        },
        {
            key: 'GBW',
            label: `GBW ${sourceCounts.GBW > 0 ? `(${sourceCounts.GBW})` : ''}`,
        },
        {
            key: 'BY',
            label: `BY ${sourceCounts.BY > 0 ? `(${sourceCounts.BY})` : ''}`,
        },
    ];

    return (
        <Tabs
            activeKey={activeSource}
            items={items}
            onChange={onChange}
            size="large"
            style={{ marginBottom: 16 }}
        />
    );
};

export default SourceTabs;
