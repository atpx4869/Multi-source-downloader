import React, { useState, useRef, useEffect } from 'react';
import { Card, Typography } from 'antd';
import {
    SearchOutlined,
    DownloadOutlined,
    CheckCircleOutlined,
    CloseCircleOutlined,
    WarningOutlined,
    InfoCircleOutlined
} from '@ant-design/icons';

const { Text } = Typography;

const LogPanel = ({ logs, title = "操作日志" }) => {
    const logEndRef = useRef(null);

    // 自动滚动到底部
    useEffect(() => {
        logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [logs]);

    const getLogColor = (log) => {
        if (log.type === 'error') return 'var(--ant-color-error)';
        if (log.type === 'success') return 'var(--ant-color-success)';
        if (log.type === 'warning') return 'var(--ant-color-warning)';
        return 'var(--ant-color-text-secondary)';
    };

    const getLogIcon = (log) => {
        if (log.type === 'search') return <SearchOutlined />;
        if (log.type === 'download') return <DownloadOutlined />;
        if (log.type === 'success') return <CheckCircleOutlined />;
        if (log.type === 'error') return <CloseCircleOutlined />;
        if (log.type === 'warning') return <WarningOutlined />;
        return <InfoCircleOutlined />;
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
                background: 'var(--ant-color-bg-layout)',
                padding: 8,
                borderRadius: 4,
                fontFamily: 'Consolas, Monaco, monospace',
                fontSize: 12
            }}>
                {logs.length === 0 ? (
                    <Text type="secondary" style={{ fontSize: 12 }}>暂无日志</Text>
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
                            <Text style={{ color: getLogColor(log), fontSize: 12 }}>
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
