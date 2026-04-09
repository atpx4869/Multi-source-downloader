import React from 'react';
import { Card, Button, Space } from 'antd';
import {
    FileSearchOutlined,
    FileExcelOutlined,
    CloudDownloadOutlined
} from '@ant-design/icons';

const ToolsPanel = ({ onStandardCheck, onExcelExport, onBatchImport }) => {
    return (
        <Card
            title={<><FileSearchOutlined /> 工具箱</>}
            size="small"
            bodyStyle={{ padding: '12px' }}
        >
            <Space direction="vertical" style={{ width: '100%' }}>
                <Button
                    type="primary"
                    icon={<FileSearchOutlined />}
                    onClick={onStandardCheck}
                    block
                >
                    标准查新
                </Button>
                <Button
                    icon={<CloudDownloadOutlined />}
                    onClick={onBatchImport}
                    block
                >
                    批量导入
                </Button>
                <Button
                    icon={<FileExcelOutlined />}
                    onClick={onExcelExport}
                    block
                >
                    Excel 导出
                </Button>
            </Space>
        </Card>
    );
};

export default ToolsPanel;
