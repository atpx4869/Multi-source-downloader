import React, { useState } from 'react';
import { Input, Button, Space } from 'antd';
import { SearchOutlined } from '@ant-design/icons';

const SearchBar = ({ onSearch, loading }) => {
    const [query, setQuery] = useState('');

    const handleSearch = () => {
        if (query.trim()) {
            onSearch(query.trim());
        }
    };

    return (
        <div>
            <Space.Compact style={{ width: '100%' }}>
                <Input
                    size="large"
                    placeholder="输入标准号或关键词..."
                    prefix={<SearchOutlined style={{ color: '#bfbfbf' }} />}
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onPressEnter={handleSearch}
                    style={{ fontSize: 16 }}
                />
                <Button
                    type="primary"
                    size="large"
                    loading={loading}
                    onClick={handleSearch}
                    style={{
                        minWidth: 100
                    }}
                >
                    搜索
                </Button>
            </Space.Compact>
        </div>
    );
};

export default SearchBar;
