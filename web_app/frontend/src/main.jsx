import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import App from './App.jsx'
import './index.css'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ConfigProvider 
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: '#5a67d8',
          borderRadius: 6,
          colorBgContainer: '#ffffff',
        },
      }}
    >
      <App />
    </ConfigProvider>
  </StrictMode>,
)
