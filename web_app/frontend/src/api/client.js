import axios from 'axios';
import { message } from 'antd';

// API基础URL (使用环境变量，支持生产环境部署)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

// 创建axios实例
const apiClient = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json',
    },
});

// 添加请求拦截器 - 记录请求详情
apiClient.interceptors.request.use(request => {
    console.log(`[>> API Request] ${request.method.toUpperCase()} ${request.url}`, request.params || request.data || {});
    return request;
}, error => {
    console.error('[API Request Error]', error);
    message.error('网络请求发送失败，请检查网络连接');
    return Promise.reject(error);
});

// 添加响应拦截器 - 记录响应详情
apiClient.interceptors.response.use(response => {
    console.log(`[<< API Response] ${response.status} ${response.config.url}`, response.data);
    return response;
}, error => {
    if (error.response) {
        // 请求已发出，服务器响应状态码不在 2xx 范围
        console.error(`[API Error Response] ${error.response.status} ${error.config.url}`, error.response.data);
        const errorMsg = error.response.data?.detail || error.response.data?.error || `服务器错误 (${error.response.status})`;
        message.error(errorMsg);
    } else if (error.request) {
        // 请求已发出，但没有收到响应
        console.error('[API No Response]', error.request);
        message.error('服务器无响应，请检查后台服务是否启动或网络状态');
    } else {
        // 发送请求时触发了错误
        console.error('[API Error Setup]', error.message);
        message.error(`请求错误: ${error.message}`);
    }
    return Promise.reject(error);
});

// 搜索API
export const searchAPI = {
    // 搜索所有数据源
    searchAll: async (query, sources = null, limit = 100, timeout = 15) => {
        const params = { q: query, limit, timeout };
        if (sources && sources.length > 0) {
            params.sources = sources;
        }
        const response = await apiClient.get('/search/', { params });
        return response.data;
    },

    // 搜索单个数据源
    searchSingle: async (source, query, limit = 100, timeout = 15) => {
        const response = await apiClient.get(`/search/${source}`, {
            params: { q: query, limit, timeout },
        });
        return response.data;
    },

    // 搜索第一个可用源
    searchFirstAvailable: async (query, limit = 100, timeout = 15) => {
        const response = await apiClient.get('/search/first/available', {
            params: { q: query, limit, timeout },
        });
        return response.data;
    },
};

// 下载API
export const downloadAPI = {
    // 从指定源下载
    download: async (source, stdNo) => {
        const response = await apiClient.post(`/download/${source}/${stdNo}`);
        return response.data;
    },

    // 从第一个可用源下载
    downloadFirstAvailable: async (stdNo) => {
        const response = await apiClient.post(`/download/first/${stdNo}`);
        return response.data;
    },
};

// 健康检查API
export const healthAPI = {
    // 检查所有数据源健康状态
    checkHealth: async () => {
        const response = await apiClient.get('/health/');
        return response.data;
    },

    // Ping检查
    ping: async () => {
        const response = await apiClient.get('/health/ping');
        return response.data;
    },
};

// 标准查新API
export const standardCheckAPI = {
    // 上传文件并开始处理
    upload: async (file, sources = ['ZBY'], stdColumn = null) => {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('sources', sources.join(','));
        if (stdColumn) {
            formData.append('std_column', stdColumn);
        }
        const response = await apiClient.post('/standard-check/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return response.data;
    },

    // 获取任务状态
    getStatus: async (taskId) => {
        const response = await apiClient.get(`/standard-check/status/${taskId}`);
        return response.data;
    },

    // 下载Excel结果
    getDownloadUrl: (taskId) => {
        return `${API_BASE_URL}/standard-check/download/${taskId}`;
    },

    // 下载CSV结果
    getDownloadCSVUrl: (taskId) => {
        return `${API_BASE_URL}/standard-check/download-csv/${taskId}`;
    },
};

// 批量操作API
export const batchAPI = {
    // 解析标准号列表
    resolve: async (stdIds) => {
        const response = await apiClient.post('/batch/resolve', stdIds);
        return response.data;
    },
};

export default apiClient;
