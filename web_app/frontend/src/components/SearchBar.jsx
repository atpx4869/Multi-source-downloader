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
            <h1 style={{
                color: 'white',
                fontSize: 24,
                fontWeight: 'bold',
                textAlign: 'center',
                marginBottom: 12
            }}>
                标准文献检索系统
            </h1>
            <Space.Compact style={{ width: '100%' }}>
                <Input
                    size="large"
                    placeholder="🔍 输入标准号或关键词..."
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onPressEnter={handleSearch}
                    style={{ fontSize: 16 }}
                />
                <Button
                    type="primary"
                    size="large"
                    icon={<SearchOutlined />}
                    loading={loading}
                    onClick={handleSearch}
                    style={{
                        background: '#5a67d8',
                        borderColor: '#5a67d8',
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
