import React from 'react';
import { Card, Form, Radio, Switch, Typography } from 'antd';
import { SettingOutlined } from '@ant-design/icons';

const { Text } = Typography;

const SettingsPanel = ({ openAfterDownload, onOpenAfterDownloadChange }) => {
    return (
        <Card
            title={<><SettingOutlined /> 设置</>}
            size="small"
        >
            <Form layout="vertical" size="small">
                <Form.Item label={<Text style={{ fontSize: 12 }}>默认数据源</Text>}>
                    <Radio.Group
                        defaultValue="all"
                        size="small"
                        style={{ width: '100%', display: 'flex', flexWrap: 'wrap', gap: '6px' }}
                    >
                        <Radio.Button value="all" style={{ fontSize: 12 }}>全部</Radio.Button>
                        <Radio.Button value="ZBY" style={{ fontSize: 12 }}>ZBY</Radio.Button>
                        <Radio.Button value="GBW" style={{ fontSize: 12 }}>GBW</Radio.Button>
                        <Radio.Button value="BY" style={{ fontSize: 12 }}>BY</Radio.Button>
                    </Radio.Group>
                </Form.Item>

                <Form.Item label={<Text style={{ fontSize: 12 }}>每页显示</Text>}>
                    <Radio.Group
                        defaultValue={20}
                        size="small"
                        style={{ width: '100%', display: 'flex', flexWrap: 'wrap', gap: '6px' }}
                    >
                        <Radio.Button value={10} style={{ fontSize: 12 }}>10条</Radio.Button>
                        <Radio.Button value={20} style={{ fontSize: 12 }}>20条</Radio.Button>
                        <Radio.Button value={50} style={{ fontSize: 12 }}>50条</Radio.Button>
                        <Radio.Button value={100} style={{ fontSize: 12 }}>100条</Radio.Button>
                    </Radio.Group>
                </Form.Item>

                <Form.Item label={<Text style={{ fontSize: 12 }}>下载目录</Text>}>
                    <Radio.Group
                        defaultValue="default"
                        size="small"
                        style={{ width: '100%', display: 'flex', flexWrap: 'wrap', gap: '6px' }}
                    >
                        <Radio.Button value="default" style={{ fontSize: 12 }}>默认目录</Radio.Button>
                    </Radio.Group>
                </Form.Item>

                <Form.Item label={<Text style={{ fontSize: 12 }}>下载后打开</Text>}>
                    <div>
                        <Switch
                            size="small"
                            checked={openAfterDownload}
                            onChange={onOpenAfterDownloadChange}
                        />
                        <Text style={{ fontSize: 11, marginLeft: 8, color: '#888' }}>
                            {openAfterDownload ? '下载并打开' : '仅下载'}
                        </Text>
                    </div>
                </Form.Item>
            </Form>
        </Card>
    );
};

export default SettingsPanel;
