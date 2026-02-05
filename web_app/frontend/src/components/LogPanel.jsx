import React, { useState, useRef, useEffect } from 'react';
import { Card, List, Tag, Typography, Button } from 'antd';
import { ClearOutlined } from '@ant-design/icons';

const { Text } = Typography;

const LogPanel = ({ logs, title = "操作日志" }) => {
    const logEndRef = useRef(null);

    // 自动滚动到底部
    useEffect(() => {
        logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [logs]);

    const getLogColor = (log) => {
        if (log.type === 'error') return '#ff4d4f';
        if (log.type === 'success') return '#52c41a';
        if (log.type === 'warning') return '#faad14';
        return '#666';
    };

    const getLogIcon = (log) => {
        if (log.type === 'search') return '🔍';
        if (log.type === 'download') return '📥';
        if (log.type === 'success') return '✓';
        if (log.type === 'error') return '✗';
        if (log.type === 'warning') return '⚠';
        return '•';
    };

    return (
        <Card
            title={title}
            size="small"
            style={{ marginBottom: 16 }}
        >
            <div style={{
                height: 350,
                overflow: 'auto',
                background: '#fafafa',
                padding: 8,
                borderRadius: 4,
                fontFamily: 'Consolas, Monaco, monospace',
                fontSize: 11
            }}>
                {logs.length === 0 ? (
                    <Text type="secondary" style={{ fontSize: 11 }}>暂无日志</Text>
                ) : (
                    logs.map((log, index) => (
                        <div
                            key={index}
                            style={{
                                marginBottom: 3,
                                color: getLogColor(log),
                                lineHeight: '1.4'
                            }}
                        >
                            <Text style={{ color: getLogColor(log), fontSize: 11 }}>
                                {getLogIcon(log)} [{log.time}] {log.message}
                            </Text>
                        </div>
                    ))
                )}
                <div ref={logEndRef} />
            </div>
        </Card>
    );
};

export default LogPanel;
