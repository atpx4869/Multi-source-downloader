# 搜索性能优化方案分析

## 当前瓶颈诊断

```
原方案：搜1(1s) → 搜2(1s) → 搜3(1s) ... → 搜10(1s) = 10秒
当前方案：搜1(1s) → 搜2(1s) → 搜3(1s) ... → 搜10(1s) = 10秒
         ↓下载 ↓下载    ↓下载
         (搜索和下载都是串行的)
```

**瓶颈：搜索是串行的，每个搜索1秒，N个文件就要N秒。**

---

## 优化方案对比

### 方案A：搜索并发化 ⭐⭐⭐⭐⭐ 推荐
```
搜1 ┐
搜2 ├─ 3个搜索线程并发 = 3.3秒（10个文件）
搜3 ├─ 比串行快3倍
...

总耗时对比：
- 当前：10秒搜 + 17秒下 = 27秒
- 优化：3.3秒搜 + 17秒下 = 20.3秒（提升33%）
```

**实现方式：**
```python
# 创建搜索队列和worker
search_queue = queue.Queue()
result_queue = queue.Queue()

# N个搜索worker线程
SearchWorker1 → 从search_queue取关键词 → 搜索 → 放入result_queue
SearchWorker2 → 从search_queue取关键词 → 搜索 → 放入result_queue
SearchWorker3 → 从search_queue取关键词 → 搜索 → 放入result_queue

# 主线程：放入搜索队列，收集结果后放入下载队列
```

**优点：**
- ✅ 实现简单（类似DownloadWorker）
- ✅ 无需改变整体架构
- ✅ 效果明显（3-5倍搜索加速）
- ✅ 内存占用低

**缺点：**
- ⚠️ 需要控制并发数（3-5个），防止源限流
- ⚠️ 结果顺序乱，需要额外处理

---

### 方案B：搜索超时 ⭐⭐⭐
```
当前搜索会等所有源都返回，如果某个源慢就拖累整体
改为：某个源找到 → 立即返回，不等其他源

例如：GBW快速返回(0.3s) → 立即提交下载，不等ZBY(1.5s)
```

**实现方式：**
```python
# 在搜索时设置超时
def search(keyword, timeout=2.0):
    # 用threading.Event控制
    best_result = None
    first_found = threading.Event()
    
    def gbw_search():
        nonlocal best_result
        result = gbw_source.search(keyword)
        if result:
            best_result = result
            first_found.set()  # 标记已找到
    
    gbw_thread = threading.Thread(target=gbw_search)
    gbw_thread.start()
    first_found.wait(timeout=timeout)  # 最多等2秒
    return best_result
```

**优点：**
- ✅ 代码改动小
- ✅ 优先返回快速源（通常是GBW/BY）
- ✅ 自动降低慢源的影响

**缺点：**
- ❌ 可能漏掉某些源的结果
- ⚠️ 需要调整timeout参数

---

### 方案C：缓存优化 ⭐⭐⭐
```
如果批量下载中有重复或相似的标准号，缓存可大幅提速

例如：GB/T 3324-2024 搜索过 → 缓存结果
      再来 GB/T 3324 → 直接用缓存，不重新搜
```

**实现方式：**
```python
# 搜索前规范化关键词，建立缓存键
def normalize_std_no(std_no):
    return re.sub(r'\s+', '', std_no).upper()

# 搜索时检查缓存
key = normalize_std_no(std_id)
if key in search_cache:
    return search_cache[key]

# 否则搜索并缓存
result = client.search(std_id)
search_cache[key] = result
```

**优点：**
- ✅ 实现简单（字典缓存）
- ✅ 对批量相似的标准号效果好
- ✅ 不增加网络请求

**缺点：**
- ❌ 只有重复时才有效
- ⚠️ 内存占用

---

### 方案D：优先级搜索 ⭐⭐⭐⭐
```
当前搜索策略：GBW → BY → ZBY（都要搜一遍）

优化策略：
- 如果GBW快速找到 → 用GBW结果，不搜BY/ZBY
- 如果GBW没找到 → 才搜BY
- 如果BY没找到 → 才搜ZBY
```

**实现方式：**
```python
def smart_search(keyword):
    # 优先级顺序：GBW > BY > ZBY
    for source in [gbw, by, zby]:
        try:
            result = source.search(keyword, timeout=2.0)
            if result:
                return result  # 找到就返回，不搜其他源
        except:
            continue
    return None
```

**优点：**
- ✅ 代码改动小
- ✅ 充分利用源的快速性
- ✅ 减少网络请求数

**缺点：**
- ⚠️ 可能漏掉其他源的结果
- ⚠️ 需要调整优先级

---

### 方案E：异步搜索+边搜边下 ⭐⭐⭐⭐⭐ 终极优化
```
不等所有搜索完成就开始下载

搜索线程：搜1 → 下队 → 搜2 → 下队 → 搜3 → 下队
          |← 仅3秒 →|
                        |
下载线程：(并发执行)←──┘
         可以在第1个搜完时就开始下载，不用等全部搜完
```

**当前方案vs终极方案：**
```
当前方案：[搜索阶段]10秒 → [下载阶段]17秒 = 27秒
终极方案：[搜索+下载并行] ≈ max(10秒, 17秒) = 17秒
```

**实现：**
```python
# 搜索线程搜到1个就立即入下载队列
# 下载线程立即开始下载
# 完全重叠执行
```

这就是我之前说的"方案2的真实面目"。

---

## 推荐方案组合

**立即实施：方案A + 方案D**
- 搜索并发（3个线程）
- 优先级搜索（找到就返回）
- **预期效果：10秒 → 2-3秒（5-10倍加速！）**
- **工作量：2-3小时**

**配合优化 B + C**
- 搜索超时（2秒内未找到则放弃）
- 搜索缓存（相同关键词不重复搜）
- **额外效果：再提升10-20%**

---

## 性能预测

假设10个标准号，每个搜索1秒

| 方案 | 搜索耗时 | 下载耗时 | 总耗时 | vs原始 |
|------|---------|---------|--------|--------|
| **原始** | 10秒 | 17秒(串) | 60秒 | 1x |
| **当前** | 10秒 | 17秒(3并发) | 27秒 | 2.2x |
| **+方案A** | 3.3秒 | 17秒 | 20.3秒 | **2.9x** ⚡⚡ |
| **+A+D** | 1.5秒 | 17秒 | 18.5秒 | **3.2x** ⚡⚡⚡ |
| **+A+D+B** | 1.5秒 | 17秒 | 18.5秒 | **3.2x** |
| **理论极限** | 3.3秒 | 3.3秒(重叠) | 3.3秒 | **18x** 🚀 |

---

## 建议

**短期（立即）：实施方案A + 方案D**
```python
# 方案A：创建3个搜索worker线程
# 方案D：改搜索策略为优先级+超时

代码量：~150行
时间：2小时
效果：5-10倍搜索加速
总耗时：27秒 → 18-20秒
```

**中期（后续）：优化方案B + C**
```python
# 添加搜索超时和缓存
额外改进：10-20%
```

**长期（可选）：回到方案E真正的方案2**
```python
# 如果搜索还是主瓶颈，考虑异步搜索+边搜边下
# 但当前方案A已经足够好了
```

---

## 快速实施指南（方案A）

```python
# 1. 创建SearchWorker类（类似DownloadWorker）
class SearchWorker(threading.Thread):
    def __init__(self, search_queue, result_queue):
        self.search_queue = search_queue
        self.result_queue = result_queue
    
    def run(self):
        while True:
            task = self.search_queue.get()
            if task is None:
                break
            std_id, idx = task
            result = client.search(std_id)  # 搜索
            self.result_queue.put((std_id, idx, result))

# 2. 改造BatchDownloadThread.run()
# 创建3个SearchWorker
# 放入search_queue
# 从result_queue收集结果后放入download_queue
```

---

## Q&A

**Q: 为什么不用更多搜索线程？**
A: 3-5个最优。太多会被源限流、IP禁用。

**Q: 如果源限流怎么办？**
A: 可添加延迟控制，或动态调整worker数。

**Q: 搜索并发会漏结果吗？**
A: 不会。每个搜索是独立的，不互相影响。

**Q: 优先级搜索会有问题吗？**
A: 可能漏掉其他源的结果，但通常GBW/BY已经够好。
   如果需要完整结果，改为timeout等待而非立即返回。
