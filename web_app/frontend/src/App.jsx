import React, { useState, useMemo } from 'react';
import { Layout, message } from 'antd';
import SearchBar from './components/SearchBar';
import SourceTabs from './components/SourceTabs';
import BatchActions from './components/BatchActions';
import ResultTable from './components/ResultTable';
import BatchDownloadModal from './components/BatchDownloadModal';
import LogPanel from './components/LogPanel';
import HistoryPanel from './components/HistoryPanel';
import ToolsPanel from './components/ToolsPanel';
import BatchImportModal from './components/BatchImportModal';
import SettingsPanel from './components/SettingsPanel';
import FilterPanel from './components/FilterPanel';
import StandardCheckPage from './components/StandardCheckPage';
import ExcelCompletionPage from './components/ExcelCompletionPage';
import { searchAPI, downloadAPI } from './api/client';
import './App.css';

const { Header, Content } = Layout;

// 提取标准类型（GB、GB/T、QB/T等） - 移至外部以保持引用稳定
const extractStandardType = (std_no) => {
  if (!std_no) return '其他';
  // 匹配 GB、GB/T、QB/T、DB、HG/T 等格式
  const StringStdNo = String(std_no);
  const match = StringStdNo.match(/^([A-Z]+(?:\/[A-Z]+)?)/);
  return match ? match[1] : '其他';
};

function App() {
  const [loading, setLoading] = useState(false);
  const [activeSource, setActiveSource] = useState('all');
  const [searchResults, setSearchResults] = useState({});
  const [sourceBaseResults, setSourceBaseResults] = useState([]); // 当前 Tab 下的基础结果（含缓存状态）
  const [selectedItems, setSelectedItems] = useState([]);
  const [selectAll, setSelectAll] = useState(false);
  const [showBatchModal, setShowBatchModal] = useState(false);
  const [showBatchImportModal, setShowBatchImportModal] = useState(false);
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
  const [activeTab, setActiveTab] = useState('search'); // 当前页面Tab

  // 派生显示结果
  const displayResults = useMemo(() => {
    if (!sourceBaseResults) return [];
    if (standardTypeFilter === 'all') return sourceBaseResults;
    return sourceBaseResults.filter(item => extractStandardType(item.std_no) === standardTypeFilter);
  }, [sourceBaseResults, standardTypeFilter]);


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

  // 归一化标准号以进行去重
  const normalizeStdNo = (std_no) => {
    return (std_no || '').replace(/[\s/\-–—_:：]+/g, '').toLowerCase();
  };

  // 合并搜索结果并去重
  const mergeSearchResults = (resultsDict) => {
    const mergedMap = new Map();

    // 优先级顺序：BY > GBW > ZBY
    const priority = ['BY', 'GBW', 'ZBY'];

    priority.forEach(source => {
      const sourceResult = resultsDict[source];
      if (sourceResult?.items) {
        sourceResult.items.forEach(item => {
          const key = normalizeStdNo(item.std_no);
          if (mergedMap.has(key)) {
            const existing = mergedMap.get(key);
            // 合并来源
            if (!existing.sources.includes(source)) {
              existing.sources.push(source);
            }
            // 合并 source_meta (如果需要的话)
            existing.source_meta = { ...existing.source_meta, [source]: item.source_meta };

            // 如果当前源有PDF，且现有条目没标注有PDF，则更新
            if (item.has_pdf && !existing.has_pdf) {
              existing.has_pdf = true;
            }
          } else {
            // 新条目，初始化 sources 数组
            mergedMap.set(key, {
              ...item,
              sources: [source],
              source_meta: { [source]: item.source_meta }
            });
          }
        });
      }
    });

    return Array.from(mergedMap.values());
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

      // 合并并去重所有源的结果 (用于“全部”标签)
      const currentMerged = mergeSearchResults(results || {});

      // 计算各源的结果数量
      const counts = {
        all: currentMerged.length,
        ZBY: results?.ZBY?.count || 0,
        GBW: results?.GBW?.count || 0,
        BY: results?.BY?.count || 0,
      };
      setSourceCounts(counts);

      // 并强制切换回“全部”标签页（用户新需求）
      setActiveSource('all');

      // 根据“全部”标签页显示内容
      let targetItems = currentMerged;

      // 检查当前显示结果的缓存状态
      const resultsWithCache = await Promise.all(
        targetItems.map(async (item) => {
          try {
            const url = `http://localhost:8000/api/download/check-cache/${encodeURIComponent(item.std_no)}`;
            const response = await fetch(url);
            const cacheData = await response.json();
            return { ...item, cached: cacheData.cached };
          } catch (error) {
            return { ...item, cached: false };
          }
        })
      );

      // 计算标准类型统计
      const types = calculateStandardTypes(resultsWithCache);
      setStandardTypes(types);
      setStandardTypeFilter('all');

      setSourceBaseResults(resultsWithCache);
      addLog(`搜索完成: 找到 ${currentMerged.length} 条唯一结果，当前显示 ${counts[activeSource]} 条 (${activeSource})`, 'success');
      message.success(`找到 ${counts[activeSource]} 条搜索结果`);
    } catch (error) {
      addLog(`搜索失败: ${error.message}`, 'error');
      message.error('搜索失败: ' + error.message);
      setSearchResults({});
      setSourceBaseResults([]);
    } finally {
      setLoading(false);
    }
  };

  // 切换数据源
  const handleSourceChange = async (source) => {
    setActiveSource(source);
    setSelectedItems([]);
    setSelectAll(false);
    setLoading(true);
    setStandardTypeFilter('all');

    let targetItems = [];
    if (source === 'all') {
      targetItems = mergeSearchResults(searchResults);
    } else {
      targetItems = searchResults[source]?.items || [];
    }

    // 切换时重新检查一遍缓存
    const resultsWithCache = await Promise.all(
      targetItems.map(async (item) => {
        try {
          const url = `http://localhost:8000/api/download/check-cache/${encodeURIComponent(item.std_no)}`;
          const response = await fetch(url);
          const cacheData = await response.json();
          return { ...item, cached: cacheData.cached };
        } catch (error) {
          return { ...item, cached: false };
        }
      })
    );

    // 切换时重新计算标准类型统计
    const types = calculateStandardTypes(resultsWithCache);
    setStandardTypes(types);

    setSourceBaseResults(resultsWithCache);
    setLoading(false);
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
      has_pdf: item.has_pdf,
      status: 'pending',
      progress: 0,
    }));

    setDownloadQueue(queue);
    setShowBatchModal(true);

    // 3. 执行下载循环
    const processQueue = async (queueToProcess) => {
      const failedItems = [];
      let successCount = 0;

      for (let i = 0; i < queueToProcess.length; i++) {
        const item = queueToProcess[i];

        if (item.has_pdf === false) {
          addLog(`跳过无文本标准: ${item.std_no}`, 'warning');
          setDownloadQueue(prev => {
            const newQueue = [...prev];
            newQueue[i] = { ...newQueue[i], status: 'error', error: '无文本可下载' };
            return newQueue;
          });
          failedItems.push({ std_no: item.std_no, reason: '无文本可下载' });
          continue;
        }

        setDownloadQueue(prev => {
          const newQueue = [...prev];
          newQueue[i] = { ...newQueue[i], status: 'downloading', progress: 0 };
          return newQueue;
        });

        try {
          // 使用优先下载接口，按 GBW > BY > ZBY 顺序尝试
          const result = await downloadAPI.downloadFirstAvailable(item.std_no);

          if (result.status === 'success') {
            addLog(`批量下载成功: ${item.std_no}`, 'success');
            setDownloadQueue(prev => {
              const newQueue = [...prev];
              newQueue[i] = { ...newQueue[i], status: 'success', progress: 100 };
              return newQueue;
            });
            successCount++;
            // 触发浏览器下载
            triggerBrowserDownload(result.filename);
          } else {
            const errorMsg = result.error || '下载失败';
            addLog(`批量下载失败: ${item.std_no} - ${errorMsg}`, 'error');
            setDownloadQueue(prev => {
              const newQueue = [...prev];
              newQueue[i] = {
                ...newQueue[i],
                status: 'error',
                error: errorMsg
              };
              return newQueue;
            });
            failedItems.push({ std_no: item.std_no, reason: errorMsg });
          }
        } catch (error) {
          const errorMsg = error.message || '未知错误';
          addLog(`批量下载错误: ${item.std_no} - ${errorMsg}`, 'error');
          setDownloadQueue(prev => {
            const newQueue = [...prev];
            newQueue[i] = {
              ...newQueue[i],
              status: 'error',
              error: errorMsg
            };
            return newQueue;
          });
          failedItems.push({ std_no: item.std_no, reason: errorMsg });
        }
      }

      // 4. 显示汇总报告
      if (failedItems.length > 0) {
        import('antd').then(({ Modal }) => {
          Modal.warning({
            title: '批量下载完成 (存在失败项)',
            width: 500,
            content: (
              <div>
                <p>共 {queueToProcess.length} 项，成功 <span style={{ color: 'green', fontWeight: 'bold' }}>{successCount}</span> 项，失败 <span style={{ color: 'red', fontWeight: 'bold' }}>{failedItems.length}</span> 项。</p>
                <div style={{ maxHeight: '200px', overflowY: 'auto', background: '#f5f5f5', padding: '8px', borderRadius: '4px' }}>
                  {failedItems.map((item, index) => (
                    <div key={index} style={{ marginBottom: '4px', borderBottom: '1px solid #e8e8e8', paddingBottom: '2px' }}>
                      <span style={{ fontWeight: 'bold' }}>{item.std_no}</span>: <span style={{ color: 'red' }}>{item.reason}</span>
                    </div>
                  ))}
                </div>
              </div>
            ),
          });
        });
      } else {
        message.success(`批量下载完成：全部 ${successCount} 项下载成功！`);
      }
    };

    // 启动处理
    processQueue(queue);
  };

  // 处理导入确认
  const handleImportConfirm = (items) => {
    setShowBatchImportModal(false);

    // 构造下载任务
    const queue = items.map(item => ({
      std_no: item.std_no,
      name: item.name,
      source: item.source,
      has_pdf: item.has_pdf,
      status: 'pending',
      progress: 0,
    }));

    setDownloadQueue(queue);
    setShowBatchModal(true);

    // 复用 handleBatchDownload 的内部逻辑需要提取出来
    // 这里为了避免重构太多，先临时复制逻辑，TODO: 提取公共函数
    // 实际上我们在上面 handleBatchDownload 已经重构了 processQueue 闭包，
    // 要跨函数复用，最好把 processQueue 提出来。
    // 但鉴于React组件内函数定义，我们可以把 logic 提取为组件内的一个通用函数 handleProcessQueue

    // 临时方案：再次复制 logic (为了快速响应用户)
    // 更好的方案：既然我都在改 handleBatchDownload，不如直接把 processQueue 定义在组件作用域
    // 但是 replace_file_content 只能替换片段。

    // 让我们先完成 handleBatchDownload 的替换，然后再用另一个工具调用来替换 handleImportConfirm
    // 或者我们直接在这里把 handleBatchDownload 改造成通用接受 queue 参数的函数？

    // 不，handleBatchDownload 依赖 selectedItems。 
    // 让我们先把 processQueue 逻辑提取出来，但我不能在一个 tool call 里轻松做到跨位置移动。
    // 所以我将分两步走：
    // 1. 定义一个通用的 processBatchDownload(queue) 函数在组件内（或者在 handleBatchDownload 旁边）
    // 2. 让 handleBatchDownload 和 handleImportConfirm 都调用它。

    // 让我们先修改 handleBatchDownload，把它重构为调用一个新函数 processBatchQueue
    // 然后再修改 handleImportConfirm 调用这个 processBatchQueue

    // 等等，用户现在要的是“无论是主程序 还是 批量导入下载程序”。
    // 所以我必须确保两者都覆盖。

    return (
      <Layout style={{ height: '100vh', width: '100%', overflow: 'hidden' }}>
        {/* 顶部标题栏 - 固定高度 */}
        <Header style={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          padding: '16px 24px',
          height: '64px',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          flexShrink: 0
        }}>
          <h1 style={{
            color: 'white',
            margin: 0,
            fontSize: '24px',
            fontWeight: 600
          }}>
            📚 标准文献检索系统
          </h1>
        </Header>

        {/* 根据 Tab 显示不同内容 */}
        {activeTab === 'search' ? (
          <Content style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 64px)', overflow: 'hidden' }}>
            {/* 搜索栏 - 固定高度 */}
            <div style={{
              background: 'linear-gradient(135deg, #764ba2 0%, #667eea 100%)',
              padding: '16px 24px',
              flexShrink: 0
            }}>
              <SearchBar onSearch={handleSearch} loading={loading} />
            </div>

            {/* 主内容区 - 内部三栏布局 */}
            <div style={{ flex: 1, overflow: 'hidden', background: '#f0f2f5' }}>
              <div className="main-content-row" style={{ height: '100%', display: 'flex' }}>
                {/* 左侧栏 */}
                <div className="sidebar-left">
                  <HistoryPanel
                    history={searchHistory}
                    onHistoryClick={handleSearch}
                  />
                  <ToolsPanel
                    onStandardCheck={() => setActiveTab('check')}
                    onExcelExport={() => setActiveTab('completion')}
                    onBatchImport={() => setShowBatchImportModal(true)}
                  />
                </div>

                {/* 中间栏：主要滚动区 */}
                <div className="content-center">
                  {Object.keys(searchResults).length > 0 && (
                    <div style={{ padding: '16px 8px' }}>
                      <SourceTabs
                        activeSource={activeSource}
                        onChange={handleSourceChange}
                        sourceCounts={sourceCounts}
                      />

                      {sourceBaseResults.length > 0 && (
                        <BatchActions
                          selectedCount={selectedItems.length}
                          onBatchDownload={handleBatchDownload}
                          onSelectAll={handleSelectAll}
                          selectAll={selectAll}
                        />
                      )}

                      {displayResults.length > 0 ? (
                        <ResultTable
                          results={displayResults}
                          loading={loading}
                          selectedItems={selectedItems}
                          onSelectionChange={handleSelectionChange}
                          onDownload={handleDownload}
                        />
                      ) : (
                        !loading && (
                          <div style={{
                            textAlign: 'center',
                            padding: '60px 0',
                            background: 'white',
                            borderRadius: 8,
                            color: '#999',
                            marginTop: 16
                          }}>
                            <p style={{ fontSize: 16 }}>
                              {sourceBaseResults.length > 0
                                ? `当前分类 (${standardTypeFilter}) 下没有结果`
                                : "当前数据源没有找到匹配的结果"}
                            </p>
                          </div>
                        )
                      )}
                    </div>
                  )}

                  {!loading && Object.keys(searchResults).length === 0 && (
                    <div style={{
                      textAlign: 'center',
                      padding: '100px 0',
                      margin: '16px 8px',
                      background: 'white',
                      borderRadius: 8,
                      color: '#999'
                    }}>
                      <p style={{ fontSize: 18 }}>请输入关键词开始搜索</p>
                    </div>
                  )}
                </div>

                {/* 右侧栏 */}
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
            </div>
          </Content>
        ) : activeTab === 'check' ? (
          <StandardCheckPage onBack={() => setActiveTab('search')} />
        ) : (
          <ExcelCompletionPage onBack={() => setActiveTab('search')} />
        )}

        {/* 弹窗组件移到 Layout 最外层 */}
        <BatchDownloadModal
          visible={showBatchModal}
          onClose={() => setShowBatchModal(false)}
          downloadQueue={downloadQueue}
        />

        <BatchImportModal
          visible={showBatchImportModal}
          onCancel={() => setShowBatchImportModal(false)}
          onImport={handleImportConfirm}
        />
      </Layout>
    );
  }

  export default App;
