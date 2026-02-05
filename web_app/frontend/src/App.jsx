import React, { useState } from 'react';
import { Layout, message } from 'antd';
import SearchBar from './components/SearchBar';
import SourceTabs from './components/SourceTabs';
import BatchActions from './components/BatchActions';
import ResultTable from './components/ResultTable';
import BatchDownloadModal from './components/BatchDownloadModal';
import LogPanel from './components/LogPanel';
import HistoryPanel from './components/HistoryPanel';
import FeaturesPanel from './components/FeaturesPanel';
import SettingsPanel from './components/SettingsPanel';
import FilterPanel from './components/FilterPanel';
import { searchAPI, downloadAPI } from './api/client';
import './App.css';

const { Header, Content } = Layout;

function App() {
  const [loading, setLoading] = useState(false);
  const [activeSource, setActiveSource] = useState('all');
  const [searchResults, setSearchResults] = useState({});
  const [displayResults, setDisplayResults] = useState([]);
  const [selectedItems, setSelectedItems] = useState([]);
  const [selectAll, setSelectAll] = useState(false);
  const [showBatchModal, setShowBatchModal] = useState(false);
  const [downloadQueue, setDownloadQueue] = useState([]);
  const [sourceCounts, setSourceCounts] = useState({
    all: 0,
    ZBY: 0,
    GBW: 0,
    BY: 0,
  });
  const [logs, setLogs] = useState([]);
  const [searchHistory, setSearchHistory] = useState([]);
  const [openAfterDownload, setOpenAfterDownload] = useState(false); // 下载后打开设置
  const [standardTypeFilter, setStandardTypeFilter] = useState('all'); // 标准类型筛选
  const [standardTypes, setStandardTypes] = useState({ all: 0 }); // 标准类型统计

  // 提取标准类型（GB、GB/T、QB/T等）
  const extractStandardType = (std_no) => {
    if (!std_no) return '其他';
    // 匹配 GB、GB/T、QB/T、DB、HG/T 等格式
    const match = std_no.match(/^([A-Z]+(?:\/[A-Z]+)?)/);
    return match ? match[1] : '其他';
  };

  // 计算标准类型统计
  const calculateStandardTypes = (results) => {
    const types = { all: results.length };
    results.forEach(item => {
      const type = extractStandardType(item.std_no);
      types[type] = (types[type] || 0) + 1;
    });
    return types;
  };

  // 添加日志
  const addLog = (message, type = 'info') => {
    const time = new Date().toLocaleTimeString('zh-CN');
    setLogs(prev => [...prev, { time, message, type }]);
  };

  // 添加搜索历史
  const addSearchHistory = (query) => {
    const time = new Date().toLocaleTimeString('zh-CN');
    setSearchHistory(prev => {
      const newHistory = [{ query, time }, ...prev.slice(0, 9)]; // 保留最近10条
      return newHistory;
    });
  };

  // 搜索处理
  const handleSearch = async (query) => {
    setLoading(true);
    setSelectedItems([]);
    setSelectAll(false);
    addLog(`开始搜索: ${query}`, 'search');
    addSearchHistory(query);

    try {
      const results = await searchAPI.searchAll(query);
      setSearchResults(results);

      // 计算各源的结果数量
      const counts = {
        all: 0,
        ZBY: results.ZBY?.count || 0,
        GBW: results.GBW?.count || 0,
        BY: results.BY?.count || 0,
      };
      counts.all = counts.ZBY + counts.GBW + counts.BY;
      setSourceCounts(counts);

      // 合并所有源的结果
      const allResults = [];
      Object.values(results).forEach((sourceResult) => {
        if (sourceResult.items) {
          allResults.push(...sourceResult.items);
        }
      });

      // 检查缓存状态
      console.log('开始检查缓存，结果数量:', allResults.length);
      const resultsWithCache = await Promise.all(
        allResults.map(async (item) => {
          try {
            const url = `http://localhost:8000/api/download/check-cache/${encodeURIComponent(item.std_no)}`;
            console.log('检查缓存 URL:', url);
            const response = await fetch(url);
            const cacheData = await response.json();
            console.log(`${item.std_no} 缓存状态:`, cacheData);
            return { ...item, cached: cacheData.cached };
          } catch (error) {
            console.error(`检查缓存失败 ${item.std_no}:`, error);
            return { ...item, cached: false };
          }
        })
      );

      console.log('缓存检查完成，结果:', resultsWithCache.map(r => ({ std_no: r.std_no, cached: r.cached })));

      // 计算标准类型统计
      const types = calculateStandardTypes(resultsWithCache);
      setStandardTypes(types);
      setStandardTypeFilter('all'); // 重置筛选

      setDisplayResults(resultsWithCache);
      addLog(`搜索完成: 找到 ${resultsWithCache.length} 条结果 (ZBY:${counts.ZBY}, GBW:${counts.GBW}, BY:${counts.BY})`, 'success');
      message.success(`找到 ${resultsWithCache.length} 条结果`);
    } catch (error) {
      addLog(`搜索失败: ${error.message}`, 'error');
      message.error('搜索失败: ' + error.message);
      setSearchResults({});
      setDisplayResults([]);
    } finally {
      setLoading(false);
    }
  };

  // 切换数据源
  const handleSourceChange = (source) => {
    setActiveSource(source);
    setSelectedItems([]);
    setSelectAll(false);

    if (source === 'all') {
      const allResults = [];
      Object.values(searchResults).forEach((sourceResult) => {
        if (sourceResult.items) {
          allResults.push(...sourceResult.items);
        }
      });
      setDisplayResults(allResults);
    } else {
      const sourceResult = searchResults[source];
      setDisplayResults(sourceResult?.items || []);
    }
  };

  // 选择变更
  const handleSelectionChange = (selected) => {
    setSelectedItems(selected);
    setSelectAll(selected.length === displayResults.filter(r => r.has_pdf).length);
  };

  // 全选/取消全选
  const handleSelectAll = (checked) => {
    setSelectAll(checked);
    if (checked) {
      const allSelectableItems = displayResults.filter(r => r.has_pdf);
      setSelectedItems(allSelectableItems);
    } else {
      setSelectedItems([]);
    }
  };

  // 标准类型筛选
  const handleStandardTypeChange = (type) => {
    setStandardTypeFilter(type);
    setSelectedItems([]);
    setSelectAll(false);

    // 获取当前数据源的所有结果
    let sourceResults = [];
    if (activeSource === 'all') {
      Object.values(searchResults).forEach((sourceResult) => {
        if (sourceResult.items) {
          sourceResults.push(...sourceResult.items);
        }
      });
    } else {
      const sourceResult = searchResults[activeSource];
      sourceResults = sourceResult?.items || [];
    }

    // 应用标准类型筛选
    if (type === 'all') {
      setDisplayResults(sourceResults);
    } else {
      const filtered = sourceResults.filter(item => extractStandardType(item.std_no) === type);
      setDisplayResults(filtered);
    }
  };

  // 触发浏览器下载
  const triggerBrowserDownload = async (filename) => {
    try {
      // 从静态文件目录下载
      const apiBase = 'http://localhost:8000';
      const url = `${apiBase}/downloads/${encodeURIComponent(filename)}`;

      // 使用 fetch + blob 方式强制下载，避免浏览器直接打开 PDF
      const response = await fetch(url);
      const blob = await response.blob();

      // 创建 blob URL
      const blobUrl = window.URL.createObjectURL(blob);

      // 触发下载
      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      // 清理 blob URL
      window.URL.revokeObjectURL(blobUrl);

      // 如果设置了"下载后打开"，则在新标签页打开
      if (openAfterDownload) {
        setTimeout(() => {
          window.open(url, '_blank');
        }, 500); // 延迟500ms，确保下载已开始
      }
    } catch (e) {
      console.error('触发浏览器下载失败:', e);
    }
  };

  // 单个下载
  const handleDownload = async (record) => {
    addLog(`开始下载: ${record.std_no} (${record.source})`, 'download');
    try {
      message.loading({ content: `正在下载 ${record.std_no}...`, key: record.std_no });
      const result = await downloadAPI.download(record.source, record.std_no);

      if (result.status === 'success') {
        addLog(`下载成功: ${record.std_no} -> ${result.filename}`, 'success');
        message.success({ content: `下载成功: ${result.filename}`, key: record.std_no });
        // 触发浏览器下载
        triggerBrowserDownload(result.filename);
      } else {
        addLog(`下载失败: ${record.std_no} - ${result.error}`, 'error');
        message.error({ content: `下载失败: ${result.error}`, key: record.std_no });
      }
    } catch (error) {
      addLog(`下载错误: ${record.std_no} - ${error.message}`, 'error');
      message.error({ content: `下载错误: ${error.message}`, key: record.std_no });
    }
  };

  // 批量下载
  const handleBatchDownload = async () => {
    if (selectedItems.length === 0) {
      message.warning('请先选择要下载的标准');
      return;
    }

    addLog(`开始批量下载: ${selectedItems.length} 个文件`, 'download');

    const queue = selectedItems.map(item => ({
      std_no: item.std_no,
      name: item.name,
      source: item.source,
      status: 'pending',
      progress: 0,
    }));

    setDownloadQueue(queue);
    setShowBatchModal(true);

    for (let i = 0; i < queue.length; i++) {
      const item = queue[i];

      setDownloadQueue(prev => {
        const newQueue = [...prev];
        newQueue[i] = { ...newQueue[i], status: 'downloading', progress: 0 };
        return newQueue;
      });

      try {
        const result = await downloadAPI.download(item.source, item.std_no);

        if (result.status === 'success') {
          addLog(`批量下载成功: ${item.std_no}`, 'success');
          setDownloadQueue(prev => {
            const newQueue = [...prev];
            newQueue[i] = { ...newQueue[i], status: 'success', progress: 100 };
            return newQueue;
          });
          // 触发浏览器下载
          triggerBrowserDownload(result.filename);
        } else {
          addLog(`批量下载失败: ${item.std_no} - ${result.error}`, 'error');
          setDownloadQueue(prev => {
            const newQueue = [...prev];
            newQueue[i] = {
              ...newQueue[i],
              status: 'error',
              error: result.error || '下载失败'
            };
            return newQueue;
          });
        }
      } catch (error) {
        addLog(`批量下载错误: ${item.std_no} - ${error.message}`, 'error');
        setDownloadQueue(prev => {
          const newQueue = [...prev];
          newQueue[i] = {
            ...newQueue[i],
            status: 'error',
            error: error.message
          };
          return newQueue;
        });
      }
    }

    const successCount = queue.filter(q => q.status === 'success').length;
    addLog(`批量下载完成: 成功 ${successCount}/${queue.length}`, 'success');
    message.success('批量下载完成');
  };

  return (
    <Layout style={{ minHeight: '100vh', width: '100%' }}>
      {/* 顶部搜索栏 */}
      <Header style={{
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        padding: '16px 24px',
        height: 'auto'
      }}>
        <SearchBar onSearch={handleSearch} loading={loading} />
      </Header>

      {/* 主内容区 - 三栏布局（自适应宽度） */}
      <Content style={{ padding: '16px 8px', background: '#f0f2f5', width: '100%' }}>
        <div className="main-content-row" style={{ gap: '12px' }}>
          {/* 左侧栏：历史记录 + 待做功能（固定宽度280px） */}
          <div className="sidebar-left">
            <HistoryPanel
              history={searchHistory}
              onHistoryClick={handleSearch}
            />
            <FeaturesPanel />
          </div>

          {/* 中间栏：搜索结果（自适应宽度） */}
          <div className="content-center">
            {displayResults.length > 0 && (
              <>
                <SourceTabs
                  activeSource={activeSource}
                  onChange={handleSourceChange}
                  sourceCounts={sourceCounts}
                />

                <BatchActions
                  selectedCount={selectedItems.length}
                  onBatchDownload={handleBatchDownload}
                  onSelectAll={handleSelectAll}
                  selectAll={selectAll}
                />

                <ResultTable
                  results={displayResults}
                  loading={loading}
                  selectedItems={selectedItems}
                  onSelectionChange={handleSelectionChange}
                  onDownload={handleDownload}
                />
              </>
            )}

            {!loading && displayResults.length === 0 && (
              <div style={{
                textAlign: 'center',
                padding: '100px 0',
                background: 'white',
                borderRadius: 8,
                color: '#999'
              }}>
                <p style={{ fontSize: 18 }}>请输入关键词开始搜索</p>
              </div>
            )}
          </div>

          {/* 右侧栏：筛选 + 日志 + 设置（固定宽度280px） */}
          <div className="sidebar-right">
            <FilterPanel
              standardTypeFilter={standardTypeFilter}
              onStandardTypeChange={handleStandardTypeChange}
              standardTypes={standardTypes}
            />
            <LogPanel logs={logs} title="日志" />
            <SettingsPanel
              openAfterDownload={openAfterDownload}
              onOpenAfterDownloadChange={setOpenAfterDownload}
            />
          </div>
        </div>
      </Content>

      <BatchDownloadModal
        visible={showBatchModal}
        onClose={() => setShowBatchModal(false)}
        downloadQueue={downloadQueue}
      />
    </Layout>
  );
}

export default App;
