# -*- coding: utf-8 -*-
"""
桌面原型 - PySide6

功能：
- 左侧：搜索输入、结果表（可选择行）
- 右侧：实时日志（自动滚动）
- 后台线程执行搜索与下载，使用信号回写 UI
- 优化：先搜索ZBY快速返回，后台补充GBW/BY

运行：
    pip install PySide6 pandas
    python desktop_app.py

打包（示例）：
    pip install pyinstaller
    pyinstaller --onefile desktop_app.py

说明：本文件复用仓库内 `core.AggregatedDownloader` 的接口（确保项目根路径已加入 sys.path）。
"""
from __future__ import annotations

import sys
import os
import json
from pathlib import Path
from datetime import datetime
import re
from typing import List, Dict, Optional, Any
import queue
import threading
import time

project_root = Path(__file__).parent.parent  # 项目根目录（上两级）
sys.path.insert(0, str(project_root))

# Add ppllocr path for development mode
ppllocr_path = project_root / "ppllocr" / "ppllocr-main"
if ppllocr_path.exists():
    sys.path.insert(0, str(ppllocr_path))

# Ensure the local "sources" package is discovered by PyInstaller
# Some imports are dynamic in the codebase; this explicit import helps
# PyInstaller include the package into the frozen bundle.
try:
    import sources  # type: ignore
    # also import common submodules so PyInstaller includes them
    try:
        import sources.gbw  # type: ignore
    except Exception:
        pass
    try:
        import sources.by  # type: ignore
    except Exception:
        pass
    try:
        import sources.zby  # type: ignore
    except Exception:
        pass
except Exception:
    pass

import traceback
import pandas as pd

# 导入 API 配置
from core.api_config import get_api_config
from core.cache_manager import get_cache_manager

try:
    from PySide6 import QtCore, QtWidgets, QtGui
    PYSIDE_VER = 6
except ImportError:
    try:
        from PySide2 import QtCore, QtWidgets, QtGui
        PYSIDE_VER = 2
    except ImportError:
        raise ImportError("Neither PySide6 nor PySide2 is installed.")

# 兼容性处理：Qt5 使用 exec_()，Qt6 使用 exec()
if PYSIDE_VER == 2:
    if not hasattr(QtWidgets.QApplication, 'exec'):
        QtWidgets.QApplication.exec = QtWidgets.QApplication.exec_
    if not hasattr(QtWidgets.QDialog, 'exec'):
        QtWidgets.QDialog.exec = QtWidgets.QDialog.exec_
    if not hasattr(QtCore.QCoreApplication, 'exec'):
        QtCore.QCoreApplication.exec = QtCore.QCoreApplication.exec_


def _ensure_qt_platform_plugin_path():
    """在某些环境（尤其路径包含中文/打包环境）下，Qt 可能找不到 windows 平台插件。

    显式设置 QT_QPA_PLATFORM_PLUGIN_PATH / QT_PLUGIN_PATH 并追加 library path，
    以避免报错：Could not find the Qt platform plugin "windows".
    """
    try:
        # 不要在模块顶层强依赖某个 PySide 版本
        if PYSIDE_VER == 2:
            import PySide2 as _pyside  # type: ignore
        else:
            import PySide6 as _pyside  # type: ignore
        pyside_dir = Path(_pyside.__file__).resolve().parent
        plugins_dir = pyside_dir / "plugins"
        platforms_dir = plugins_dir / "platforms"
        if not platforms_dir.exists():
            return

        # 若环境变量未设置或指向无效路径，则覆盖
        cur_platforms = os.environ.get("QT_QPA_PLATFORM_PLUGIN_PATH")
        if not cur_platforms or not Path(cur_platforms).exists():
            os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(platforms_dir)

        cur_plugins = os.environ.get("QT_PLUGIN_PATH")
        if not cur_plugins or not Path(cur_plugins).exists():
            os.environ["QT_PLUGIN_PATH"] = str(plugins_dir)

        # 追加到 Qt 的 libraryPaths（需要在创建 QApplication 之前调用）
        try:
            QtCore.QCoreApplication.addLibraryPath(str(plugins_dir))
        except Exception:
            pass
    except Exception:
        return


_ensure_qt_platform_plugin_path()

from app import ui_styles

# 规范号规范化正则（复用以避免在循环中重复编译）
_STD_NO_RE = re.compile(r"[\s/\-–—_:：]+")
import threading

# 缓存 AggregatedDownloader 实例以减少重复初始化开销
_AD_CACHE: dict = {}
_AD_CACHE_LOCK = threading.Lock()

def get_aggregated_downloader(enable_sources=None, output_dir=None):
    """返回一个复用的 AggregatedDownloader 实例（按 enable_sources+output_dir 缓存）。
    如果 AggregatedDownloader 未导入或无法实例化，则返回 None 或抛出原始异常。
    """
    if output_dir is None:
        output_dir = "downloads"
    key = (tuple(enable_sources) if enable_sources else None, output_dir)
    with _AD_CACHE_LOCK:
        inst = _AD_CACHE.get(key)
        if inst is not None:
            return inst

        # 延迟导入 core.AggregatedDownloader，若不可用则返回 None
        try:
            from core import AggregatedDownloader
        
            try:
                inst = AggregatedDownloader(enable_sources=enable_sources, output_dir=output_dir)
            except Exception:
                # 打印详细 traceback 以便诊断初始化失败原因
                print("[get_aggregated_downloader] AggregatedDownloader init failed:")
                traceback.print_exc()
                return None
        except Exception:
            print("[get_aggregated_downloader] import/core failure:")
            traceback.print_exc()
            return None

        _AD_CACHE[key] = inst
        return inst

try:
    from core import AggregatedDownloader
    from core import natural_key
    from core.models import Standard
    from core.smart_search import StandardSearchMerger
except Exception:
    AggregatedDownloader = None
    Standard = None


# ==================== 密码验证模块 ====================

def get_today_password() -> str:
    """获取今日密码：日期反转后取6位"""
    today = datetime.now().strftime("%Y%m%d")  # 如 20251216
    return today[::-1][:6]  # 反转后取前6位: 61215202 -> 612152


def get_auth_file() -> Path:
    """获取验证记录文件路径"""
    return Path(__file__).parent / ".auth_cache"


def is_authenticated_today() -> bool:
    """检查今天是否已验证过"""
    auth_file = get_auth_file()
    if not auth_file.exists():
        return False
    try:
        data = json.loads(auth_file.read_text(encoding="utf-8"))
        last_auth_date = data.get("date", "")
        today = datetime.now().strftime("%Y%m%d")
        return last_auth_date == today
    except Exception:
        return False


def save_auth_record():
    """保存今日验证记录"""
    auth_file = get_auth_file()
    # 确保目录存在
    auth_file.parent.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y%m%d")
    auth_file.write_text(json.dumps({"date": today}), encoding="utf-8")


class PasswordDialog(QtWidgets.QDialog):
    """密码验证对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("安全验证")
        self.setFixedSize(360, 260)
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        self.setup_ui()
        self.attempts = 0
        self.max_attempts = 5
        # 设置对话框为模态且置顶
        self.setModal(True)
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        
    def setup_ui(self):
        self.setStyleSheet(ui_styles.DIALOG_STYLE)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(30, 20, 30, 20)
        
        # 顶部标题栏 - 居中布局
        header = QtWidgets.QWidget()
        header.setStyleSheet("""
            QWidget {
                background-color: #34c2db;
                border-radius: 8px;
            }
        """)
        header.setFixedHeight(55)
        header_layout = QtWidgets.QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # 居中容器
        center_widget = QtWidgets.QWidget()
        center_widget.setStyleSheet("background: transparent;")
        center_layout = QtWidgets.QHBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(8)
        
        icon_label = QtWidgets.QLabel("🔐")
        icon_label.setStyleSheet("font-size: 24px; background: transparent;")
        center_layout.addWidget(icon_label)
        
        title = QtWidgets.QLabel("标准文献检索系统")
        title.setStyleSheet("""
            font-size: 15px;
            font-weight: bold;
            color: white;
            background: transparent;
        """)
        center_layout.addWidget(title)
        
        header_layout.addStretch()
        header_layout.addWidget(center_widget)
        header_layout.addStretch()
        
        layout.addWidget(header)
        
        # 提示文字 - 确保完整显示
        subtitle = QtWidgets.QLabel("请输入6位数字密码以继续使用")
        subtitle.setAlignment(QtCore.Qt.AlignCenter)
        subtitle.setFixedHeight(30)
        subtitle.setStyleSheet("""
            font-size: 12px;
            color: #666;
        """)
        layout.addWidget(subtitle)
        
        # 密码输入框 - 使用星号显示
        self.pwd_input = QtWidgets.QLineEdit()
        self.pwd_input.setPlaceholderText("******")
        self.pwd_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.pwd_input.setMaxLength(6)
        self.pwd_input.setAlignment(QtCore.Qt.AlignCenter)
        self.pwd_input.setFixedHeight(50)
        self.pwd_input.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 2px solid #34c2db;
                border-radius: 8px;
                padding: 8px 15px;
                font-size: 18px;
                font-weight: bold;
                font-family: Arial;
                letter-spacing: 10px;
                color: #333;
                lineedit-password-character: 42;
            }
            QLineEdit:focus {
                border-color: #346edb;
            }
        """)
        self.pwd_input.returnPressed.connect(self.verify_password)
        layout.addWidget(self.pwd_input)
        
        # 提示信息
        self.msg_label = QtWidgets.QLabel("")
        self.msg_label.setAlignment(QtCore.Qt.AlignCenter)
        self.msg_label.setStyleSheet("""
            font-size: 11px;
            color: #e74c3c;
            min-height: 16px;
        """)
        layout.addWidget(self.msg_label)
        
        # 确认按钮
        self.btn_confirm = QtWidgets.QPushButton("确 认")
        self.btn_confirm.setCursor(QtCore.Qt.PointingHandCursor)
        self.btn_confirm.setFixedHeight(38)
        self.btn_confirm.setStyleSheet(ui_styles.BTN_PRIMARY_STYLE)
        self.btn_confirm.clicked.connect(self.verify_password)
        layout.addWidget(self.btn_confirm)
        
        # 底部提示
        hint = QtWidgets.QLabel("仅限内部使用 · 密码每日更新")
        hint.setAlignment(QtCore.Qt.AlignCenter)
        hint.setStyleSheet("""
            font-size: 10px;
            color: #aaa;
            padding-top: 5px;
        """)
        layout.addWidget(hint)
    
    def showEvent(self, event):
        """窗口显示时自动焦点到输入框"""
        try:
            super().showEvent(event)
            # 延迟设置焦点，确保窗口完全显示
            QtCore.QTimer.singleShot(100, self._set_focus)
        except Exception as e:
            print(f"❌ showEvent 错误: {e}")
    
    def _set_focus(self):
        """设置焦点到输入框"""
        try:
            self.pwd_input.setFocus()
            self.pwd_input.selectAll()
            print("[DEBUG] 焦点已设置到输入框")
        except Exception as e:
            print(f"❌ 设置焦点失败: {e}")
    
    def verify_password(self):
        """验证密码"""
        try:
            entered = self.pwd_input.text().strip()
            correct = get_today_password()
            
            print(f"[DEBUG] 输入长度: {len(entered)}, 期望长度: {len(correct)}")  # 调试
            
            if entered == correct:
                save_auth_record()
                self.accept()
            else:
                self.attempts += 1
                remaining = self.max_attempts - self.attempts
                
                if remaining <= 0:
                    QtWidgets.QMessageBox.critical(self, "验证失败", "密码错误次数过多，程序将退出。")
                    self.reject()
                else:
                    self.msg_label.setText(f"❌ 密码错误，还剩 {remaining} 次机会")
                    self.pwd_input.clear()
                    self.pwd_input.setFocus()
        except Exception as e:
            print(f"❌ 密码验证错误: {e}")
            import traceback
            traceback.print_exc()
            QtWidgets.QMessageBox.critical(self, "错误", f"验证过程出错：{str(e)}")
            self.reject()
    
    def shake_animation(self):
        """窗口抖动效果"""
        original_pos = self.pos()
        
        animation = QtCore.QPropertyAnimation(self, b"pos")
        animation.setDuration(300)
        animation.setLoopCount(1)
        
        animation.setKeyValueAt(0, original_pos)
        animation.setKeyValueAt(0.1, original_pos + QtCore.QPoint(10, 0))
        animation.setKeyValueAt(0.2, original_pos + QtCore.QPoint(-10, 0))
        animation.setKeyValueAt(0.3, original_pos + QtCore.QPoint(8, 0))
        animation.setKeyValueAt(0.4, original_pos + QtCore.QPoint(-8, 0))
        animation.setKeyValueAt(0.5, original_pos + QtCore.QPoint(5, 0))
        animation.setKeyValueAt(0.6, original_pos + QtCore.QPoint(-5, 0))
        animation.setKeyValueAt(0.7, original_pos + QtCore.QPoint(3, 0))
        animation.setKeyValueAt(0.8, original_pos + QtCore.QPoint(-3, 0))
        animation.setKeyValueAt(1, original_pos)
        
        animation.start()
        # 保持动画对象引用
        self._shake_anim = animation


def check_password() -> bool:
    """检查密码验证，返回是否通过"""
    try:
        print("[DEBUG] 开始密码验证...")
        
        if is_authenticated_today():
            print("[DEBUG] 今日已验证过，跳过密码验证")
            return True
        
        print("[DEBUG] 创建密码对话框...")
        dialog = PasswordDialog()
        
        print("[DEBUG] 显示密码对话框...")
        result = dialog.exec()
        
        print(f"[DEBUG] 对话框返回结果: {result}")
        success = result == QtWidgets.QDialog.Accepted
        print(f"[DEBUG] 密码验证{'成功' if success else '失败'}")
        return success
    except Exception as e:
        print(f"❌ check_password 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


# ==================== 搜索下载模块 ====================


class SearchThread(QtCore.QThread):
    """渐进式搜索线程 - 并行搜索所有源，先搜出来的先显示"""
    partial_results = QtCore.Signal(str, list)  # source_name, rows - 单个源的结果
    all_completed = QtCore.Signal()  # 所有源搜索完成
    log = QtCore.Signal(str)
    error = QtCore.Signal(str)
    progress = QtCore.Signal(int, int, str)  # current, total, message

    def __init__(self, keyword: str, sources: Optional[List[str]] = None, page: int = 1, page_size: int = 20, output_dir: str = "downloads"):
        super().__init__()
        self.keyword = keyword
        self.sources = sources or ["GBW", "BY", "ZBY"]
        self.page = page
        self.page_size = page_size
        self.output_dir = output_dir

    def run(self):
        try:
            if AggregatedDownloader is None:
                self.log.emit("AggregatedDownloader 未找到，无法执行搜索（请确认项目结构）")
                self.all_completed.emit()
                return
            
            self.log.emit(f"🔍 开始智能搜索: {self.keyword}")
            self.progress.emit(0, 100, "正在搜索...")
            
            import time
            from core.enhanced_search import EnhancedSmartSearcher
            
            # 定义结果回调 - 查到一条显示一条
            result_count = 0
            def on_result_callback(source_name: str, results_batch: list):
                nonlocal result_count
                if results_batch:
                    # 转换结果为显示格式
                    rows = []
                    for item in results_batch:
                        rows.append({
                            "std_no": item['std_no'],
                            "name": item['name'],
                            "publish": item['publish'],
                            "implement": item['implement'],
                            "status": item['status'],
                            "replace_std": item['replace_std'],
                            "has_pdf": item['has_pdf'],
                            "sources": item['sources'],
                            "obj": item['obj'],
                        })
                    
                    # 立即发送这一批结果到 UI
                    self.partial_results.emit(source_name, rows)
                    result_count += len(rows)
                    
                    # 更新进度
                    source_display = {
                        "ZBY": "ZBY 数据源",
                        "GBW": "GBW 数据源",
                        "BY": "BY 数据源",
                        "MERGED": "合并结果"
                    }.get(source_name, source_name)
                    self.log.emit(f"   📥 收到 {source_display} 的 {len(rows)} 条结果（累计: {result_count} 条）")
            
            # 使用流式搜索 - 支持多线程、容错、自动降级、实时显示
            start_time = time.time()
            metadata = EnhancedSmartSearcher.search_with_callback(
                self.keyword,
                AggregatedDownloader(),
                self.output_dir,
                on_result=on_result_callback
            )
            elapsed = time.time() - start_time
            
            # 日志反馈
            if metadata['is_gb_standard']:
                self.log.emit(f"   📊 GB/T 标准检测：启用多源并行搜索")
            else:
                self.log.emit(f"   📊 非 GB 标准：优先使用 ZBY")
            
            self.log.emit(f"   🔗 使用的数据源: {', '.join(metadata['sources_used'])}")
            
            if metadata['has_fallback']:
                self.log.emit(f"   ⚠️  主源无结果，已自动切换到备用源: {metadata['fallback_source']}")
            
            # 搜索完成
            if metadata['total_results'] > 0:
                self.log.emit(f"   ✅ 搜索完成: 共找到 {metadata['total_results']} 条结果，耗时 {elapsed:.2f}秒")
            else:
                self.log.emit(f"   ℹ️  未找到匹配的标准")
            
            self.progress.emit(100, 100, "搜索完成")
            self.all_completed.emit()
            
        except Exception as e:
            tb = traceback.format_exc()
            self.log.emit(f"❌ 搜索出错: {e}")
            self.log.emit(tb)
            self.error.emit(tb)
            self.progress.emit(0, 100, "搜索失败")
            self.all_completed.emit()
            self.progress.emit(0, 100, "搜索失败")
            self.all_completed.emit()


class BackgroundSearchThread(QtCore.QThread):
    """后台搜索线程 - 静默搜索GBW/BY，补充数据"""
    log = QtCore.Signal(str)
    finished = QtCore.Signal(dict)  # 返回 {std_no_normalized: Standard} 缓存
    progress = QtCore.Signal(str)  # 状态文本

    def __init__(self, keyword: str, sources: List[str], page: int = 1, page_size: int = 20, output_dir: str = "downloads"):
        super().__init__()
        self.keyword = keyword
        self.sources = sources  # 要搜索的源，如 ["GBW", "BY"]
        self.page = page
        self.page_size = page_size
        self.output_dir = output_dir

    def run(self):
        cache = {}
        try:
            if AggregatedDownloader is None or not self.sources:
                self.finished.emit(cache)
                return

            self.progress.emit(f"后台加载中: {', '.join(self.sources)}...")
            self.log.emit(f"🔄 后台开始搜索: {', '.join(self.sources)}")

            for src_name in self.sources:
                try:
                    self.log.emit(f"   ↳ 正在搜索 {src_name}...")
                    try:
                        client = get_aggregated_downloader(enable_sources=[src_name], output_dir=self.output_dir)
                    except Exception as e:
                        self.log.emit(f"   ✗ 创建 AggregatedDownloader 失败: {e}")
                        continue
                    if client is None:
                        self.log.emit(f"   ✗ AggregatedDownloader 未就绪: {src_name}")
                        continue
                    config = get_api_config()
                    items = client.search(self.keyword, parallel=config.parallel_search, page=int(self.page), page_size=int(self.page_size))
                    
                    for it in items:
                        # 使用完整标准号归一化作为 key（包含年份），确保同一标准号只出现一次
                        key = StandardSearchMerger._normalize_std_no(it.std_no or "")
                        if key not in cache:
                            cache[key] = {}

                        # 按源存储 Standard 对象，便于后续精确合并与优先级判断
                        s_name = it.sources[0] if it.sources else src_name
                        cache[key][s_name] = it
                    
                    self.log.emit(f"   ✅ {src_name} 完成: {len(items)} 条")
                except Exception as e:
                    self.log.emit(f"   ✗ {src_name} 失败: {str(e)[:50]}")

            self.progress.emit("后台加载完成")
            self.log.emit(f"✅ 后台搜索完成: 共缓存 {len(cache)} 条补充数据")
            
        except Exception as e:
            tb = traceback.format_exc()
            self.log.emit(f"❌ 后台搜索出错: {e}")
            self.log.emit(tb)
            self.progress.emit("后台加载失败")
        
        self.finished.emit(cache)


class SearchWorker(threading.Thread):
    """后台搜索worker线程，从队列中取关键词并执行搜索"""
    
    def __init__(self, search_queue: queue.Queue, result_queue: queue.Queue, worker_id: int, 
                 enable_sources: List[str] = None, log_signal=None):
        super().__init__(daemon=True)
        self.search_queue = search_queue
        self.result_queue = result_queue
        self.worker_id = worker_id
        self.enable_sources = enable_sources
        self.log_signal = log_signal  # QtCore.Signal(str)
        self.client = None  # 延迟初始化，在 run() 中创建一次
        self.config = None

    def _emit_log(self, msg: str):
        """发送日志信号"""
        if self.log_signal:
            self.log_signal.emit(msg)

    def run(self):
        """从队列中取关键词并搜索"""
        # 一次性创建 client 和 config，在整个循环中复用（性能优化）
        try:
            self.client = get_aggregated_downloader(enable_sources=self.enable_sources, output_dir="downloads")
            self.config = get_api_config()
        except Exception as e:
            self._emit_log(f"❌ [SearchWorker-{self.worker_id}] 初始化失败: {e}")
            return

        while True:
            try:
                # 从队列中取任务，超时5秒
                task = self.search_queue.get(timeout=5)
                
                # 如果收到哨兵值（None），表示搜索完成
                if task is None:
                    break
                
                std_id, idx = task
                
                try:
                    # 清理关键词
                    search_key = re.sub(r'\s+', ' ', std_id)
                    
                    # 优先级搜索策略（方案D）：BY > GBW > ZBY
                    # 在搜索时优先级搜索，找到就返回，不等其他源
                    results = None
                    
                    # 尝试按优先级搜索
                    for source_name in ["BY", "GBW", "ZBY"]:
                        try:
                            # 调用聚合下载器的搜索，使用缓存的config
                            results = self.client.search(search_key, parallel=self.config.parallel_search)
                            
                            if results:
                                break
                        except Exception:
                            continue
                    
                    # 如果主搜索没找到，尝试部分关键词
                    if not results and '-' in search_key:
                        try:
                            short_key = search_key.split('-')[0].strip()
                            results = self.client.search(short_key, parallel=self.config.parallel_search)
                        except Exception:
                            pass
                    
                    # 放入结果队列
                    self.result_queue.put((std_id, idx, results))
                    
                except Exception as e:
                    self._emit_log(f"   ❌ [SearchWorker-{self.worker_id}] 搜索失败: {std_id} - {str(e)[:50]}")
                    self.result_queue.put((std_id, idx, None))
                finally:
                    self.search_queue.task_done()
                    
            except queue.Empty:
                continue
            except Exception as e:
                self._emit_log(f"❌ [SearchWorker-{self.worker_id}] 异常: {str(e)[:80]}")
                break


class DownloadErrorClassifier:
    """P2: 下载错误分类器（独立可复用）"""
    
    @staticmethod
    def classify(error_msg: str, logs: list) -> str:
        """
        错误分类：区分网络错误(重试)、源不可用(跳过)、无标准(记录)
        
        返回值:
        - "network": 网络错误，可重试
        - "not_found": 源不可用，跳过
        - "no_standard": 无标准，记录失败
        - "corrupted": 文件损坏
        - "unknown": 未知错误
        """
        error_msg_lower = error_msg.lower()
        logs_str = " ".join(logs or []).lower()
        
        # 网络错误（包括超时）
        if any(k in error_msg_lower for k in 
               ["timeout", "超时", "连接", "网络", "connection", "timed out", "reset"]):
            return "network"
        
        # 源不可用
        if any(k in error_msg_lower or k in logs_str for k in 
               ["403", "404", "源不可用", "无法访问", "unavailable"]):
            return "not_found"
        
        # 无标准
        if any(k in error_msg_lower or k in logs_str for k in 
               ["未找到", "not found", "无此标准", "no standard"]):
            return "no_standard"
        
        # 文件损坏
        if any(k in error_msg_lower or k in logs_str for k in 
               ["损坏", "corrupt", "checksum", "crc"]):
            return "corrupted"
        
        return "unknown"


class DownloadWorker(threading.Thread):
    """后台下载worker线程，从队列中取任务并执行下载"""
    
    def __init__(self, download_queue: queue.Queue, worker_id: int, output_dir: str = "downloads", 
                 enable_sources: List[str] = None, log_signal=None, progress_signal=None, 
                 prefer_order: List[str] = None, failure_callback=None):
        super().__init__(daemon=True)
        self.download_queue = download_queue
        self.worker_id = worker_id
        self.output_dir = output_dir
        self.enable_sources = enable_sources
        self.log_signal = log_signal  # QtCore.Signal(str)
        self.progress_signal = progress_signal  # QtCore.Signal(int, int, str)
        self.prefer_order = prefer_order  # 下载源优先级
        self.failure_callback = failure_callback  # P1: 失败回调函数(std_id, reason, error_type)
        self.download_count = 0
        self.success_count = 0
        self.fail_count = 0
        self.cache_manager = get_cache_manager()
        self.client = None  # 延迟初始化，在 run() 中创建一次
        self.current_std_no = ""  # 记录当前正在下载的标准号

    def _emit_log(self, msg: str):
        """发送日志信号"""
        if self.log_signal:
            self.log_signal.emit(msg)

    def _emit_progress(self, success: int, fail: int, msg: str):
        """发送进度信号"""
        if self.progress_signal:
            self.progress_signal.emit(success, fail, msg)

    def run(self):
        """从队列中取任务并下载"""
        # 一次性创建 client，在整个循环中复用（性能优化）
        try:
            self.client = get_aggregated_downloader(enable_sources=self.enable_sources, output_dir=self.output_dir)
        except Exception as e:
            self._emit_log(f"❌ [Worker-{self.worker_id}] 初始化下载器失败: {e}")
            return

        while True:
            try:
                # 从队列中取任务，超时5秒
                task = self.download_queue.get(timeout=5)
                
                # 如果收到哨兵值（None），表示下载完成
                if task is None:
                    summary = f"✅ [Worker-{self.worker_id}] 完成"
                    if self.success_count > 0:
                        summary += f" 成功{self.success_count}个"
                    if self.fail_count > 0:
                        summary += f" 失败{self.fail_count}个"
                    self._emit_log(summary)
                    break
                
                std_id, best_match = task
                self.download_count += 1
                
                # 记录当前处理的标准号（用于进度显示）
                self.current_std_no = getattr(best_match, 'std_no', std_id)[:30]
                
                # 智能重试策略：区分错误类型
                self._download_with_retry(best_match)
                
                self.download_queue.task_done()
                    
            except queue.Empty:
                continue
            except Exception as e:
                self._emit_log(f"❌ [Worker-{self.worker_id}] 异常: {str(e)[:80]}")
                break
        
        # Worker退出时清理资源（防止Playwright残留进程报错）
        try:
            if hasattr(self, 'client') and self.client:
                # 尝试关闭Playwright资源
                for src in self.client.sources:
                    if hasattr(src, 'close'):
                        try:
                            src.close()
                        except Exception:
                            pass
        except Exception:
            pass

    def _download_with_retry(self, best_match):
        """
        带智能重试的下载逻辑
        - 网络错误：重试2次
        - 源不可用：跳过该源
        - 无标准：直接记录失败
        - 单标准超时：20秒强制中断（正常2-10秒，异常快速识别）
        """
        import time
        import threading
        
        max_retries = 2
        retry_delay = 2
        download_success = False
        last_error = None
        download_timeout = 20  # 单标准下载最长20秒（正常2-10秒，多源尝试12-20秒）
        
        for attempt in range(1, max_retries + 1):
            try:
                # 使用超时线程执行下载（防止卡死）
                result_container = {"path": None, "logs": [], "error": None}
                
                def _do_download():
                    try:
                        path, logs = self.client.download(best_match, prefer_order=self.prefer_order)
                        result_container["path"] = path
                        result_container["logs"] = logs
                    except Exception as e:
                        result_container["error"] = e
                
                download_thread = threading.Thread(target=_do_download, daemon=True)
                download_thread.start()
                download_thread.join(timeout=download_timeout)
                
                # 检查是否超时
                if download_thread.is_alive():
                    # 超时了，线程还在运行（可能卡在Playwright）
                    error_type = "network"
                    last_error = f"下载超时({download_timeout}s)"
                    self._emit_log(f"   ⏱️  [Worker-{self.worker_id}] 下载超时({download_timeout}s)，强制中断")
                    
                    # 重新创建client，避免Playwright状态污染
                    try:
                        self.client = get_aggregated_downloader(
                            enable_sources=self.enable_sources, 
                            output_dir=self.output_dir
                        )
                        self._emit_log(f"   🔄 [Worker-{self.worker_id}] 已重建下载器（清理可能的残留状态）")
                    except Exception as e:
                        self._emit_log(f"   ⚠️  [Worker-{self.worker_id}] 重建下载器失败: {str(e)[:50]}")
                    
                    if attempt < max_retries:
                        self._emit_log(f"   ⚠️  [Worker-{self.worker_id}] 第{attempt}次超时，{retry_delay}秒后重试...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        break
                
                # 检查下载结果
                if result_container["error"]:
                    raise result_container["error"]
                
                path = result_container["path"]
                logs = result_container["logs"]
                
                if path:
                    # 成功下载
                    is_cached = "[OK] 缓存命中" in " ".join(logs or [])
                    success_src = "缓存"
                    
                    if not is_cached:
                        # 从logs中提取源名称
                        for line in reversed(logs or []):
                            if "成功 ->" in line:
                                success_src = line.split(":")[0].strip()
                                break
                    
                    # 恢复日志输出，让用户看到进度（重要！）
                    if is_cached:
                        self._emit_log(f"   💾 [Worker-{self.worker_id}] 缓存命中")
                    else:
                        # 只显示标准号前缀和源，避免过长
                        std_short = getattr(best_match, 'std_no', '')[:20]
                        self._emit_log(f"   ✅ [Worker-{self.worker_id}] {std_short} [{success_src}]")
                    
                    # 写入下载历史
                    try:
                        size_bytes = os.path.getsize(path) if os.path.exists(path) else 0
                        self.cache_manager.save_download_record(
                            std_no=getattr(best_match, "std_no", ""),
                            std_name=getattr(best_match, "name", getattr(best_match, "std_name", "")) or "",
                            source=success_src,
                            file_path=path,
                            file_size=size_bytes
                        )
                    except Exception:
                        pass  # 静默忽略历史记录错误

                    self.success_count += 1
                    download_success = True
                    return
                else:
                    # 下载返回None，判断错误类型
                    error_msg = " ".join(logs[-3:]) if logs else "未知错误"
                    error_type = DownloadErrorClassifier.classify(error_msg, logs)
                    
                    if error_type == "network" and attempt < max_retries:
                        # 网络错误 → 重试
                        self._emit_log(f"   ⚠️  [Worker-{self.worker_id}] 第{attempt}次网络错误，{retry_delay}秒后重试...")
                        time.sleep(retry_delay)
                        continue
                    elif error_type == "source_unavailable":
                        # 源不可用 → 跳过，标记失败
                        self._emit_log(f"   ❌ [Worker-{self.worker_id}] 源不可用或限制访问，放弃")
                        last_error = error_msg
                        break
                    elif error_type == "not_found":
                        # 无此标准 → 直接失败，不重试
                        # 如果来自GBW且标记为有PDF，执行"延迟验证"
                        self._emit_log(f"   ❌ [Worker-{self.worker_id}] 标准不存在或已删除，放弃")
                        
                        # 尝试回溯并更新GBW缓存（延迟验证）
                        if "GBW" in error_msg or "GBW" in str(logs):
                            self._emit_log(f"   🔄 [Worker-{self.worker_id}] 执行延迟验证：标记GBW中的此项为误判")
                            try:
                                # 直接访问类变量更新缓存（所有实例共享）
                                from sources.gbw import GBWSource
                                # 尝试多种方式获取item_id
                                item_id = None
                                if hasattr(best_match, 'source_meta') and best_match.source_meta:
                                    item_id = best_match.source_meta.get('id')
                                if not item_id:
                                    item_id = getattr(best_match, 'gb_id', None) or getattr(best_match, 'id', None)
                                
                                if item_id:
                                    GBWSource._pdf_check_cache[item_id] = False
                                    self._emit_log(f"      ✓ 缓存已更新: {item_id[:16]}...")
                                else:
                                    self._emit_log(f"      ⚠️  无法获取item_id，跳过缓存更新")
                            except Exception as e:
                                self._emit_log(f"      ⚠️  缓存更新失败: {str(e)[:50]}")
                        
                        last_error = error_msg
                        break
                    elif error_type == "corrupted":
                        # 文件损坏 → 删除后重试
                        if attempt < max_retries:
                            self._emit_log(f"   ⚠️  [Worker-{self.worker_id}] 文件损坏，{retry_delay}秒后重试...")
                            time.sleep(retry_delay)
                            continue
                    else:
                        # 未知错误 → 重试
                        if attempt < max_retries:
                            self._emit_log(f"   ⚠️  [Worker-{self.worker_id}] 第{attempt}次下载失败，{retry_delay}秒后重试...")
                            time.sleep(retry_delay)
                            continue
                        else:
                            last_error = error_msg
                            break
                    
            except Exception as e:
                error_type = DownloadErrorClassifier.classify(str(e), [])
                
                if error_type == "network" and attempt < max_retries:
                    self._emit_log(f"   ⚠️  [Worker-{self.worker_id}] 第{attempt}次异常（网络），{retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                    continue
                else:
                    self._emit_log(f"   ❌ [Worker-{self.worker_id}] 下载异常: {str(e)[:60]}")
                    last_error = str(e)[:100]
                    break
        
        # 所有尝试都失败
        if not download_success:
            error_type = DownloadErrorClassifier.classify(last_error or "", [])
            self._emit_log(f"   ❌ [Worker-{self.worker_id}] 下载失败: {last_error or '未知原因'}")
            self.fail_count += 1
            
            # P1: 回调失败信息给 BatchDownloadThread
            if self.failure_callback:
                std_id = getattr(best_match, 'std_no', '') or getattr(best_match, 'id', '')
                self.failure_callback(std_id, last_error or '未知原因', error_type)


class FailedItem:
    """失败项结构化数据类"""
    def __init__(self, std_id: str, reason: str, error_type: str = "unknown"):
        self.std_id = std_id
        self.reason = reason
        self.error_type = error_type  # "not_found", "network_error", "source_unavailable", "unknown"
        self.timestamp = None
    
    def to_dict(self):
        """转为字典便于序列化"""
        return {
            'std_id': self.std_id,
            'reason': self.reason,
            'error_type': self.error_type,
            'timestamp': self.timestamp
        }


class BatchDownloadThread(QtCore.QThread):
    log = QtCore.Signal(str)
    finished = QtCore.Signal(int, int, list)  # success, fail, failed_list
    progress = QtCore.Signal(int, int, str)  # current, total, message

    def __init__(self, std_ids: List[str], output_dir: str = "downloads", enable_sources: List[str] = None, 
                 num_workers: int = 3):
        super().__init__()
        self.std_ids = std_ids
        self.output_dir = output_dir
        self.enable_sources = enable_sources
        self.num_workers = num_workers  # 下载worker线程数
        self._stop_requested = False
        self.failed_items = []  # P1: 结构化存储失败项

    def stop(self):
        """停止批量下载任务"""
        self._stop_requested = True
        self.log.emit("⏳ 正在请求停止批量下载任务...")
    
    def export_failed_to_csv(self, filepath: str) -> bool:
        """P1: 导出失败项到 CSV 文件"""
        if not self.failed_items:
            return False
        
        try:
            import csv
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['标准号', '失败原因', '错误类型'])
                for item in self.failed_items:
                    if isinstance(item, FailedItem):
                        writer.writerow([item.std_id, item.reason, item.error_type])
                    else:
                        # 兼容旧格式（字符串）
                        writer.writerow([str(item), '未知', 'unknown'])
            return True
        except Exception as e:
            print(f"导出失败: {e}")
            return False
    
    def get_failed_std_ids(self) -> List[str]:
        """P1: 获取失败的标准号列表，用于重试"""
        failed_ids = []
        for item in self.failed_items:
            if isinstance(item, FailedItem):
                failed_ids.append(item.std_id)
            else:
                # 兼容旧格式
                failed_ids.append(str(item).split(' ')[0])
        return failed_ids

    def run(self):
        """
        批量下载主流程：流水线优化 + 智能重试策略
        - 搜索和下载并行进行：边搜边下（不等搜索全部完成）
        - 智能重试：区分错误类型，网络错误重试，源不可用跳过
        - 性能提升：15-20% 加速，关键路径优化
        """
        import time
        start_time = time.time()
        
        # 1. 初始化资源和队列
        total, failed_list, search_queue, result_queue, download_queue = self._initialize_resources()
        
        # 2. 启动搜索和下载 Worker 线程
        search_workers, download_workers, num_search_workers = self._start_workers(
            search_queue, result_queue, download_queue
        )
        
        # 3. 执行搜索流水线（并行搜索和收集）
        search_count, search_fail = self._execute_search_pipeline(
            search_queue, result_queue, download_queue, search_workers, failed_list
        )
        
        # 4. 执行下载流水线（监控下载进度）
        total_success, total_fail, worker_stats = self._execute_download_pipeline(
            download_queue, download_workers, search_count
        )
        
        # 5. 生成并输出最终统计结果
        total_elapsed = time.time() - start_time
        self._generate_summary(
            total, search_count, search_fail, total_success, total_fail, 
            total_elapsed, worker_stats, failed_list
        )
        
        # 发送完成信号
        self.finished.emit(total_success, total_fail, failed_list)
    
    def _initialize_resources(self):
        """初始化批量下载所需的资源和队列"""
        total = len(self.std_ids)
        failed_list = []
        
        # 创建队列
        search_queue = queue.Queue()
        result_queue = queue.Queue()
        download_queue = queue.Queue(maxsize=200)
        
        return total, failed_list, search_queue, result_queue, download_queue
    
    def _start_workers(self, search_queue, result_queue, download_queue):
        """启动搜索和下载 Worker 线程"""
        # 启动搜索 workers
        num_search_workers = 5
        search_workers = []
        for i in range(num_search_workers):
            worker = SearchWorker(
                search_queue=search_queue,
                result_queue=result_queue,
                worker_id=i + 1,
                enable_sources=self.enable_sources,
                log_signal=self.log
            )
            worker.start()
            search_workers.append(worker)
        
        # 启动下载 workers
        prefer_order = ["BY", "GBW", "ZBY"]
        actual_download_workers = max(3, min(self.num_workers, num_search_workers + 2))
        
        # P1: 定义失败回调函数，收集详细失败信息
        def on_download_failed(std_id: str, reason: str, error_type: str):
            """下载失败时的回调，记录到 failed_items"""
            failed_item = FailedItem(std_id, reason, error_type)
            self.failed_items.append(failed_item)
        
        download_workers = []
        for i in range(actual_download_workers):
            worker = DownloadWorker(
                download_queue=download_queue,
                worker_id=i + 1,
                output_dir=self.output_dir,
                enable_sources=self.enable_sources,
                log_signal=self.log,
                progress_signal=None,
                prefer_order=prefer_order,
                failure_callback=on_download_failed  # P1: 传入失败回调
            )
            worker.start()
            download_workers.append(worker)
        
        return search_workers, download_workers, num_search_workers
    
    def _execute_search_pipeline(self, search_queue, result_queue, download_queue, 
                                 search_workers, failed_list):
        """执行搜索流水线：并行搜索和收集结果"""
        import threading
        import time
        
        self.log.emit("🚀 [方案1+3] 启动流水线：边搜边下，智能重试")
        self.log.emit(f"   🔍 搜索线程数: {len(search_workers)}   ⬇️  下载线程数: {self.num_workers}")
        
        total = len(self.std_ids)
        num_search_workers = len(search_workers)
        search_count = 0
        search_fail = 0
        
        # 线程1：持续放入搜索任务
        def enqueue_searches():
            for idx, std_id in enumerate(self.std_ids, start=1):
                if self._stop_requested:
                    self.log.emit("🛑 用户取消了批量下载任务")
                    break

                std_id = std_id.strip().replace('\xa0', ' ').replace('\u3000', ' ')
                if not std_id:
                    continue

                if idx <= 5 or idx % 10 == 0:
                    self.progress.emit(idx, total, f"[入队] ({idx}/{total}): {std_id}")
                
                try:
                    search_queue.put((std_id, idx), timeout=5)
                except queue.Full:
                    self.log.emit(f"⚠️ 搜索队列已满，等待...")
                    search_queue.put((std_id, idx))
            
            for _ in range(num_search_workers):
                search_queue.put(None)
        
        # 线程2：实时收集结果并入队下载
        def collect_and_enqueue():
            nonlocal search_count, search_fail
            
            remaining = len([s for s in self.std_ids if s.strip()])
            collected = 0
            start_time = time.time()
            last_progress_time = start_time
            current_std_id = ""  # 记录当前处理的标准号
            
            timeout_count = 0  # 连续超时计数器
            dynamic_timeout = 30  # 默认超时时间
            while collected < remaining:
                try:
                    # 动态超时：基于待处理数，最少30秒，最多60秒
                    pending = remaining - collected
                    dynamic_timeout = max(30, min(60, pending * 3))
                    
                    std_id, idx, results = result_queue.get(timeout=dynamic_timeout)
                    timeout_count = 0  # 重置超时计数
                    collected += 1
                    processed = collected
                    current_std_id = std_id  # 更新当前处理的标准号
                    
                    # 更新进度：搜索进度从 0-50%，显示当前标准号
                    progress = int(collected / remaining * 50)
                    elapsed = int(time.time() - start_time)
                    est_total = int(elapsed * remaining / max(1, collected))
                    eta = est_total - elapsed
                    
                    # 改进的进度信息：包含标准号、已耗时、预计总耗时
                    progress_msg = f"[搜索中] {collected}/{remaining} | 当前: {std_id[:25]} | 耗时: {elapsed}s | 预计: {est_total}s"
                    self.progress.emit(progress, 100, progress_msg)
                    
                    if not results:
                        self.log.emit(f"❌ [{collected}/{remaining}] 未找到: {std_id}")
                        search_fail += 1
                        # P1: 结构化记录失败项
                        failed_item = FailedItem(std_id, "未找到标准", "not_found")
                        failed_list.append(failed_item)
                        result_queue.task_done()
                        continue
                    
                    search_count += 1
                    
                    # 寻找最匹配的项
                    best_match = results[0]
                    clean_id = std_id.replace(" ", "").upper()
                    for r in results:
                        if r.std_no.replace(" ", "").upper() == clean_id:
                            best_match = r
                            break
                    
                    self.log.emit(f"✅ [{collected}/{remaining}] {best_match.std_no}")
                    
                    # 🚀 立即放入下载队列（流水线！边搜边下）
                    try:
                        download_queue.put((std_id, best_match), timeout=5)
                    except queue.Full:
                        self.log.emit(f"   ⚠️ 下载队列已满，等待...")
                        download_queue.put((std_id, best_match))
                    
                    result_queue.task_done()
                        
                except queue.Empty:
                    timeout_count += 1
                    elapsed = int(time.time() - start_time)
                    pending = remaining - collected
                    
                    # 第1次超时：打印日志，继续等待
                    if timeout_count == 1:
                        self.log.emit(f"⏳ 搜索响应缓慢 - 已收集 {collected}/{remaining}，正在等待搜索结果...")
                    # 第2次超时：增加日志详度
                    elif timeout_count == 2:
                        self.log.emit(f"⚠️ 搜索响应非常缓慢 ({dynamic_timeout}s超时)，已收集 {collected}/{remaining} | 耗时 {elapsed}s")
                        self.log.emit(f"   可能原因：网络延迟、API限速、或大量搜索结果需要处理")
                    # 第3次超时：检查是否应该放弃
                    elif timeout_count >= 3:
                        # 检查搜索workers是否还活跃
                        active_searchers = sum(1 for w in search_workers if w.is_alive())
                        if active_searchers == 0:
                            self.log.emit(f"ℹ️ 所有搜索线程已完成，但还有 {pending} 个结果未收集，请继续等待...")
                            # 再等一次，给搜索结果一个机会
                            if timeout_count == 4:
                                self.log.emit(f"❌ 搜索结果队列为空，放弃等待剩余 {pending} 个结果")
                                break
                        else:
                            self.log.emit(f"⏳ 还有 {active_searchers} 个搜索线程在工作，待收集 {pending} 个结果，继续等待...")
                    
                    # 继续等待而不是直接break
                    time.sleep(1)
                    
                except Exception as e:
                    self.log.emit(f"❌ 收集结果出错: {str(e)[:80]}")
        
        # 并行运行搜索和收集线程
        enqueue_thread = threading.Thread(target=enqueue_searches, daemon=True)
        collect_thread = threading.Thread(target=collect_and_enqueue, daemon=True)
        
        enqueue_thread.start()
        collect_thread.start()
        enqueue_thread.join()
        collect_thread.join()
        
        return search_count, search_fail
    
    def _execute_download_pipeline(self, download_queue, download_workers, search_count):
        """执行下载流水线：监控下载进度直到完成"""
        import time
        
        self.log.emit(f"──────────────────────────────────────")
        self.log.emit(f"🔍 搜索阶段完成！共找到 {search_count} 个标准")
        self.log.emit(f"⏳ 正在下载 {search_count} 个文件（{self.num_workers} 线程并发）...")
        
        # 通知下载 workers 停止
        for _ in range(self.num_workers):
            download_queue.put(None)
        
        # 监控下载进度
        download_start_time = time.time()
        last_downloaded_count = 0
        download_no_progress_count = 0
        
        while any(w.is_alive() for w in download_workers):
            current_downloaded = sum(w.success_count + w.fail_count for w in download_workers)
            download_total = search_count
            
            # 检测是否卡住（30秒内无进度）
            if current_downloaded == last_downloaded_count:
                download_no_progress_count += 1
            else:
                download_no_progress_count = 0
                last_downloaded_count = current_downloaded
            
            if download_total > 0:
                download_progress = int(50 + (current_downloaded / max(1, download_total) * 50))
                elapsed_download = int(time.time() - download_start_time)
                
                # 计算下载速度和ETA
                if elapsed_download > 0:
                    download_speed = current_downloaded / elapsed_download
                    remaining_downloads = download_total - current_downloaded
                    eta_download = int(remaining_downloads / max(0.1, download_speed))
                else:
                    eta_download = 0
                
                # 显示每个worker的状态：包含当前标准号
                worker_details = []
                stuck_workers = []
                for w in download_workers:
                    std_info = f"{w.current_std_no[:15]}" if w.current_std_no else "空闲"
                    worker_details.append(f"W{w.worker_id}:{std_info}({w.success_count}✅/{w.fail_count}❌)")
                    # 检测卡住的worker（30秒无进度且在处理任务）
                    if download_no_progress_count >= 60 and w.current_std_no and elapsed_download > 30:
                        stuck_workers.append(f"Worker-{w.worker_id}: {w.current_std_no}")
                
                worker_status = " | ".join(worker_details)
                
                msg = f"[下载中] {current_downloaded}/{download_total} | {elapsed_download}s | 预计{eta_download}s | {worker_status}"
                self.progress.emit(download_progress, 100, msg)
                
                # 检测卡住情况并诊断
                if download_no_progress_count == 30:
                    self.log.emit(f"⚠️ 检测到下载进度停顿 (30秒无新完成)")
                    self.log.emit(f"   当前进度: {current_downloaded}/{download_total}")
                    self.log.emit(f"   活跃Worker: {sum(1 for w in download_workers if w.is_alive())}/{len(download_workers)}")
                    for w in download_workers:
                        if w.current_std_no:
                            self.log.emit(f"   Worker-{w.worker_id} 正在处理: {w.current_std_no}")
                
                if download_no_progress_count == 60:
                    self.log.emit(f"❌ 下载可能已卡住 (60秒无新完成)")
                    if stuck_workers:
                        self.log.emit(f"   卡住的Worker任务:")
                        for task in stuck_workers:
                            self.log.emit(f"     • {task}")
                    self.log.emit(f"   建议：检查网络连接或对应下载源是否可用")
            
            time.sleep(0.5)
        
        # 等待所有 worker 完全结束并收集统计
        total_success = 0
        total_fail = 0
        worker_stats = []
        for worker in download_workers:
            worker.join()
            total_success += worker.success_count
            total_fail += worker.fail_count
            worker_stats.append((worker.worker_id, worker.success_count, worker.fail_count))
        
        return total_success, total_fail, worker_stats
    
    def _generate_summary(self, total, search_count, search_fail, total_success, 
                         total_fail, total_elapsed, worker_stats, failed_list):
        """生成并输出批量下载的最终统计结果"""
        self.progress.emit(100, 100, f"[完成] 耗时: {total_elapsed:.1f}秒")
        
        self.log.emit(f"──────────────────────────────────────")
        self.log.emit(f"📊 📊 📊 批量下载完成统计 📊 📊 📊")
        self.log.emit(f"──────────────────────────────────────")
        self.log.emit(f"🔍 搜索阶段: {search_count}/{total} 成功，{search_fail} 失败")
        self.log.emit(f"⬇️  下载阶段: {total_success} 成功，{total_fail} 失败")
        self.log.emit(f"📈 总成功率: {total_success/(max(1, total_success+total_fail))*100:.1f}%")
        self.log.emit(f"⏱️  总耗时: {total_elapsed:.1f}秒")
        self.log.emit(f"👷 Worker详情:")
        for worker_id, success, fail in worker_stats:
            rate = success / max(1, success + fail) * 100
            self.log.emit(f"   Worker-{worker_id}: ✅ {success} | ❌ {fail} ({rate:.0f}%)")
        
        # P1: 显示结构化的失败信息
        if failed_list:
            self.log.emit(f"📋 失败的标准 (前10个):")
            for item in failed_list[:10]:
                # 兼容旧的字符串格式和新的 FailedItem 对象
                if isinstance(item, FailedItem):
                    self.log.emit(f"   • {item.std_id} - {item.reason} [{item.error_type}]")
                else:
                    self.log.emit(f"   • {item}")
            if len(failed_list) > 10:
                self.log.emit(f"   ... 还有 {len(failed_list) - 10} 个失败")
            
            # P1: 按错误类型统计
            if self.failed_items:
                error_counts = {}
                for item in self.failed_items:
                    error_counts[item.error_type] = error_counts.get(item.error_type, 0) + 1
                
                self.log.emit(f"📊 失败原因统计:")
                for error_type, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
                    type_name = {
                        "network": "网络错误",
                        "not_found": "源不可用/标准不存在",
                        "no_standard": "无此标准",
                        "corrupted": "文件损坏",
                        "unknown": "未知错误"
                    }.get(error_type, error_type)
                    self.log.emit(f"   • {type_name}: {count} 个")
        
        self.log.emit(f"──────────────────────────────────────")




class DownloadThread(QtCore.QThread):
    log = QtCore.Signal(str)
    finished = QtCore.Signal(int, int)
    progress = QtCore.Signal(int, int, str)  # current, total, message

    def __init__(self, items: List[dict], output_dir: str = "downloads", background_cache: dict = None, parallel: bool = False, max_workers: int = 3, prefer_order: Optional[List[str]] = None):
        super().__init__()
        self.items = items
        self.output_dir = output_dir
        self.background_cache = background_cache or {}
        self.parallel = parallel  # 是否并行下载
        self.max_workers = max_workers  # 并行下载的线程数
        self.prefer_order = prefer_order  # 手动指定下载优先级
        self._lock = None  # 线程锁（并行模式使用）
        self._stop_requested = False

    def stop(self):
        """停止下载"""
        self._stop_requested = True

    def _download_single(self, idx: int, it: dict, total: int) -> Tuple[bool, str, Optional[str]]:
        """
        下载单个文件
        
        Returns:
            (success, std_no, error_msg)
        """
        std_no = it.get("std_no")
        
        try:
            # 获取原始对象
            obj = it.get("obj")

            # 使用复用的 AggregatedDownloader 实例以提升性能
            try:
                client = get_aggregated_downloader(enable_sources=None, output_dir=self.output_dir)
            except Exception as e:
                return False, std_no, f"创建下载器失败: {str(e)[:100]}"

            try:
                path, logs = client.download(obj, prefer_order=self.prefer_order)
            except Exception as e:
                tb = traceback.format_exc()
                return False, std_no, f"{str(e)[:100]}"

            if path:
                success_src = "未知"
                try:
                    for line in reversed(logs or []):
                        if "成功 ->" in line:
                            success_src = line.split(":")[0].strip()
                            break
                except Exception:
                    pass
                return True, std_no, f"✅ [{success_src}] -> {path}"
            else:
                return False, std_no, "所有来源均未成功"
                
        except Exception as e:
            return False, std_no, f"异常: {str(e)[:100]}"

    def run(self):
        success = 0
        fail = 0
        total = len(self.items)
        
        if not self.parallel:
            # 串行下载（原逻辑，安全但慢）
            for idx, it in enumerate(self.items, start=1):
                if self._stop_requested:
                    self.log.emit("🛑 用户取消下载")
                    break
                
                std_no = it.get("std_no")
                self.progress.emit(idx, total, f"正在下载: {std_no}")
                self.log.emit(f"📥 [{idx}/{total}] 开始下载: {std_no}")
                
                ok, _, msg = self._download_single(idx, it, total)
                if ok:
                    self.log.emit(f"   {msg}")
                    success += 1
                else:
                    self.log.emit(f"   ❌ 下载失败: {std_no} - {msg}")
                    fail += 1
        else:
            # 并行下载（推荐，性能提升 2-3 倍）
            import concurrent.futures
            import threading
            
            self._lock = threading.Lock()
            completed = 0
            
            def download_task(idx_item):
                """并行下载任务"""
                idx, it = idx_item
                if self._stop_requested:
                    return False, it.get("std_no"), "用户取消"
                
                std_no = it.get("std_no")
                
                # 线程安全地更新进度
                with self._lock:
                    nonlocal completed
                    completed += 1
                    self.progress.emit(completed, total, f"正在下载: {std_no}")
                    self.log.emit(f"📥 [{completed}/{total}] 开始下载: {std_no}")
                
                return self._download_single(idx, it, total)
            
            # 使用线程池并行下载
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = [executor.submit(download_task, (i+1, item)) for i, item in enumerate(self.items)]
                
                # 等待所有任务完成
                for future in concurrent.futures.as_completed(futures):
                    try:
                        ok, std_no, msg = future.result()
                        with self._lock:
                            if ok:
                                self.log.emit(f"   {msg}")
                                success += 1
                            else:
                                self.log.emit(f"   ❌ 下载失败: {std_no} - {msg}")
                                fail += 1
                    except Exception as exc:
                        with self._lock:
                            self.log.emit(f"   ❌ 下载任务异常: {exc}")
                            fail += 1

        self.progress.emit(total, total, "下载完成")
        self.finished.emit(success, fail)


class SourceHealthThread(QtCore.QThread):
    """在后台检查数据源连通性并通过信号返回结果"""
    finished = QtCore.Signal(dict)
    error = QtCore.Signal(str)

    def __init__(self, force: bool = False, parent=None):
        super().__init__(parent)
        self.force = force

    def run(self):
        try:
            try:
                client = get_aggregated_downloader(enable_sources=["GBW", "BY", "ZBY"], output_dir=None)
            except Exception:
                import traceback as _tb
                self.error.emit(_tb.format_exc())
                return
            if client is None:
                self.error.emit("AggregatedDownloader 未就绪")
                return
            health_status = client.check_source_health(force=self.force)
            self.finished.emit(health_status)
        except Exception:
            import traceback
            self.error.emit(traceback.format_exc())


class StandardTableModel(QtCore.QAbstractTableModel):
    """简单的表格模型，替代 QTableWidget 用于更高效渲染和批量操作"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: List[dict] = []
        # 列顺序：选中、序号、标准号、名称、发布日期、实施日期、状态、来源、文本
        self._headers = ["选中", "序号", "标准号", "名称", "发布日期", "实施日期", "状态", "来源", "文本"]

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._items)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self._headers)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None
        r = index.row(); c = index.column()
        item = self._items[r]
        if role == QtCore.Qt.DisplayRole:
            if c == 0:
                return "●" if item.get("_selected") else ""
            if c == 1:
                return str(item.get("_display_idx", r + 1))
            if c == 2:
                return item.get("std_no", "")
            if c == 3:
                return item.get("name", "")
            if c == 4:
                return item.get("publish", "")
            if c == 5:
                return item.get("implement", "")
            if c == 6:
                return item.get("status", "")
            if c == 7:
                # 显示来源（优先使用合并后的 _display_source）
                disp = item.get('_display_source') or (item.get('sources')[0] if item.get('sources') else None)
                return disp or ""
            if c == 8:
                return "✓" if item.get("has_pdf") else "-"
        
        # 背景色：根据不同条件设置颜色
        if role == QtCore.Qt.BackgroundRole:
            if c == 0 and item.get("_selected"):
                return QtGui.QBrush(QtGui.QColor("#3498db"))
            # 状态列的颜色指示：现行=绿色，废止=红色，其他=白色
            elif c == 6:
                status = item.get("status", "").lower()
                if "现行" in status or "active" in status or "有效" in status:
                    return QtGui.QBrush(QtGui.QColor("#d4edda"))  # 浅绿色
                elif "废止" in status or "supersede" in status or "canceled" in status or "abrogated" in status:
                    return QtGui.QBrush(QtGui.QColor("#f8d7da"))  # 浅红色
                else:
                    return QtGui.QBrush(QtGui.QColor("#ffffff"))
            else:
                return QtGui.QBrush(QtGui.QColor("#ffffff"))
        
        # 文字色：选中项用白色，未选中用黑色或适应背景的颜色
        if role == QtCore.Qt.ForegroundRole:
            if c == 0 and item.get("_selected"):
                return QtGui.QBrush(QtGui.QColor("#ffffff"))
            elif c == 6:
                status = item.get("status", "").lower()
                if "现行" in status or "active" in status or "有效" in status:
                    return QtGui.QBrush(QtGui.QColor("#155724"))  # 深绿色文字
                elif "废止" in status or "supersede" in status or "canceled" in status or "abrogated" in status:
                    return QtGui.QBrush(QtGui.QColor("#721c24"))  # 深红色文字
                else:
                    return QtGui.QBrush(QtGui.QColor("#333333"))
            else:
                return QtGui.QBrush(QtGui.QColor("#333333"))  # 黑色文字
        
        # 对齐方式
        if role == QtCore.Qt.TextAlignmentRole and c == 0:
            return QtCore.Qt.AlignCenter
        
        return None

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            return self._headers[section]
        return None

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags
        flags = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        return flags

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if not index.isValid():
            return False
        return False
        return False

    def set_items(self, items: List[dict]):
        self.beginResetModel()
        self._items = []
        for i, it in enumerate(items, start=1):
            copy = dict(it)
            copy.setdefault("_selected", False)
            copy.setdefault("_display_idx", i)
            self._items.append(copy)
        self.endResetModel()

    def get_selected_items(self) -> List[dict]:
        return [it for it in self._items if it.get("_selected")]

    def set_all_selected(self, selected: bool):
        for it in self._items:
            it["_selected"] = bool(selected)
        if self._items:
            top = self.index(0, 0)
            bottom = self.index(len(self._items) - 1, 0)
            self.dataChanged.emit(top, bottom, [QtCore.Qt.BackgroundRole, QtCore.Qt.DisplayRole])


class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ 设置")
        self.setModal(True)
        self.resize(700, 600)
        self.setStyleSheet(ui_styles.DIALOG_STYLE + ui_styles.SCROLLBAR_STYLE)
        
        self.api_config = get_api_config()

        # 主布局
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # 创建滚动区域以容纳所有内容
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(15)
        
        # ========== API 模式配置 ==========
        scroll_layout.addWidget(self._create_api_section())
        
        # ========== 数据源配置 ==========
        scroll_layout.addWidget(self._create_sources_section())
        
        # ========== 搜索配置 ==========
        scroll_layout.addWidget(self._create_search_section())
        
        # ========== 性能优化 ==========
        scroll_layout.addWidget(self._create_performance_section())
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)
        
        # ========== 底部按钮 ==========
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.setSpacing(10)
        
        btn_reset = QtWidgets.QPushButton("🔄 重置默认")
        btn_reset.setMinimumWidth(100)
        btn_reset.setStyleSheet(ui_styles.BTN_SECONDARY_STYLE)
        btn_reset.setCursor(QtCore.Qt.PointingHandCursor)
        btn_reset.clicked.connect(self.on_reset_defaults)
        
        btn_ok = QtWidgets.QPushButton("✓ 保存")
        btn_ok.setMinimumWidth(100)
        btn_ok.setStyleSheet(ui_styles.BTN_PRIMARY_STYLE)
        btn_ok.setCursor(QtCore.Qt.PointingHandCursor)
        btn_ok.clicked.connect(self.accept)
        
        btn_cancel = QtWidgets.QPushButton("✕ 取消")
        btn_cancel.setMinimumWidth(100)
        btn_cancel.setStyleSheet(ui_styles.BTN_SECONDARY_STYLE)
        btn_cancel.setCursor(QtCore.Qt.PointingHandCursor)
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(btn_reset)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        main_layout.addLayout(btn_layout)
        
        self.setLayout(main_layout)
    
    def _create_section_header(self, title: str) -> QtWidgets.QWidget:
        """创建段落标题"""
        header = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(header)
        layout.setContentsMargins(0, 10, 0, 5)
        
        lbl = QtWidgets.QLabel(title)
        lbl.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 13px;")
        
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        line.setStyleSheet("color: #bdc3c7;")
        
        layout.addWidget(lbl, 0)
        layout.addWidget(line, 1)
        return header
    
    def _create_form_row(self, label: str, widget) -> QtWidgets.QWidget:
        """创建表单行"""
        row = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        lbl = QtWidgets.QLabel(label)
        lbl.setMinimumWidth(120)
        lbl.setStyleSheet("color: #34495e;")
        
        layout.addWidget(lbl, 0)
        layout.addWidget(widget, 1)
        return row
    
    def _create_api_section(self) -> QtWidgets.QGroupBox:
        """API模式配置段"""
        group = QtWidgets.QGroupBox()
        group.setStyleSheet(ui_styles.BUTTON_GROUP_STYLE + """
            QGroupBox { background-color: #f8f9fa; }
            QLabel { color: #333333; }
            QRadioButton { color: #333333; }
        """)
        layout = QtWidgets.QVBoxLayout(group)
        layout.setSpacing(12)
        
        layout.addWidget(self._create_section_header("⚙️ API 模式"))
        
        # 模式选择
        mode_layout = QtWidgets.QHBoxLayout()
        self.rb_local = QtWidgets.QRadioButton("📍 本地模式")
        self.rb_remote = QtWidgets.QRadioButton("🌐 远程模式")
        self.rb_local.setChecked(self.api_config.is_local_mode())
        self.rb_remote.setChecked(self.api_config.is_remote_mode())
        self.rb_local.setStyleSheet("color: #34495e;")
        self.rb_remote.setStyleSheet("color: #34495e;")
        self.rb_local.toggled.connect(self.on_mode_changed)
        mode_layout.addWidget(self.rb_local)
        mode_layout.addWidget(self.rb_remote)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)
        
        # 本地模式设置
        self.local_group = QtWidgets.QWidget()
        local_layout = QtWidgets.QVBoxLayout(self.local_group)
        local_layout.setContentsMargins(10, 0, 0, 0)
        local_layout.setSpacing(8)
        
        self.spin_local_timeout = QtWidgets.QSpinBox()
        self.spin_local_timeout.setValue(self.api_config.local_timeout)
        self.spin_local_timeout.setMinimum(5)
        self.spin_local_timeout.setMaximum(300)
        self.spin_local_timeout.setSuffix(" 秒")
        self.spin_local_timeout.setStyleSheet(self._get_input_style())
        local_layout.addWidget(self._create_form_row("请求超时:", self.spin_local_timeout))
        
        layout.addWidget(self.local_group)
        
        # 远程模式设置
        self.remote_group = QtWidgets.QWidget()
        remote_layout = QtWidgets.QVBoxLayout(self.remote_group)
        remote_layout.setContentsMargins(10, 0, 0, 0)
        remote_layout.setSpacing(8)
        
        self.input_remote_url = QtWidgets.QLineEdit(self.api_config.remote_base_url)
        self.input_remote_url.setPlaceholderText("http://127.0.0.1:8000")
        self.input_remote_url.setStyleSheet(self._get_input_style())
        remote_layout.addWidget(self._create_form_row("API 地址:", self.input_remote_url))
        
        self.spin_remote_timeout = QtWidgets.QSpinBox()
        self.spin_remote_timeout.setValue(self.api_config.remote_timeout)
        self.spin_remote_timeout.setMinimum(10)
        self.spin_remote_timeout.setMaximum(600)
        self.spin_remote_timeout.setSuffix(" 秒")
        self.spin_remote_timeout.setStyleSheet(self._get_input_style())
        remote_layout.addWidget(self._create_form_row("请求超时:", self.spin_remote_timeout))
        
        self.chk_verify_ssl = QtWidgets.QCheckBox("🟢 启用 SSL 验证 (HTTPS 推荐)")
        self.chk_verify_ssl.setChecked(self.api_config.verify_ssl)
        self.chk_verify_ssl.setStyleSheet(ui_styles.CACHE_CHECKBOX_STYLE)
        def update_ssl_text():
            self.chk_verify_ssl.setText("🟢 启用 SSL 验证 (HTTPS 推荐)" if self.chk_verify_ssl.isChecked() else "⚫ 启用 SSL 验证 (HTTPS 推荐)")
        self.chk_verify_ssl.toggled.connect(update_ssl_text)
        update_ssl_text()
        remote_layout.addWidget(self.chk_verify_ssl)
        
        layout.addWidget(self.remote_group)
        
        self.on_mode_changed()
        return group
    
    def _create_sources_section(self) -> QtWidgets.QGroupBox:
        """数据源配置段"""
        group = QtWidgets.QGroupBox()
        group.setStyleSheet(ui_styles.BUTTON_GROUP_STYLE + """
            QGroupBox { background-color: #f8f9fa; }
            QLabel { color: #333333; }
            QCheckBox { color: #333333; }
        """)
        layout = QtWidgets.QVBoxLayout(group)
        layout.setSpacing(10)
        
        layout.addWidget(self._create_section_header("📡 启用的数据源"))
        
        self.chk_gbw = QtWidgets.QCheckBox("🟢 GBW")
        self.chk_by = QtWidgets.QCheckBox("🟢 BY")
        self.chk_zby = QtWidgets.QCheckBox("🟢 ZBY")
        
        self.chk_gbw.setChecked("gbw" in self.api_config.enable_sources)
        self.chk_by.setChecked("by" in self.api_config.enable_sources)
        self.chk_zby.setChecked("zby" in self.api_config.enable_sources)
        
        # 添加工具提示
        self.chk_gbw.setToolTip("国家标准信息公共服务平台")
        self.chk_by.setToolTip("标院内网系统")
        self.chk_zby.setToolTip("标准云在线平台")
        
        # 添加灯泡切换功能
        def update_gbw_settings():
            self.chk_gbw.setText("🟢 GBW" if self.chk_gbw.isChecked() else "⚫ GBW")
        def update_by_settings():
            self.chk_by.setText("🟢 BY" if self.chk_by.isChecked() else "⚫ BY")
        def update_zby_settings():
            self.chk_zby.setText("🟢 ZBY" if self.chk_zby.isChecked() else "⚫ ZBY")
        self.chk_gbw.toggled.connect(update_gbw_settings)
        self.chk_by.toggled.connect(update_by_settings)
        self.chk_zby.toggled.connect(update_zby_settings)
        update_gbw_settings()
        update_by_settings()
        update_zby_settings()
        
        for chk in [self.chk_gbw, self.chk_by, self.chk_zby]:
            chk.setStyleSheet(ui_styles.CACHE_CHECKBOX_STYLE)
            layout.addWidget(chk)
        
        return group
    
    def _create_search_section(self) -> QtWidgets.QGroupBox:
        """搜索配置段"""
        group = QtWidgets.QGroupBox()
        group.setStyleSheet(ui_styles.BUTTON_GROUP_STYLE + """
            QGroupBox { background-color: #f8f9fa; }
            QLabel { color: #333333; }
            QCheckBox { color: #333333; }
        """)
        layout = QtWidgets.QVBoxLayout(group)
        layout.setSpacing(10)
        
        layout.addWidget(self._create_section_header("🔍 搜索配置"))
        
        self.spin_search_limit = QtWidgets.QSpinBox()
        self.spin_search_limit.setValue(self.api_config.search_limit)
        self.spin_search_limit.setMinimum(10)
        self.spin_search_limit.setMaximum(500)
        self.spin_search_limit.setStyleSheet(self._get_input_style())
        layout.addWidget(self._create_form_row("返回结果数:", self.spin_search_limit))
        
        self.spin_max_retries = QtWidgets.QSpinBox()
        self.spin_max_retries.setValue(self.api_config.max_retries)
        self.spin_max_retries.setMinimum(1)
        self.spin_max_retries.setMaximum(10)
        self.spin_max_retries.setStyleSheet(self._get_input_style())
        layout.addWidget(self._create_form_row("最大重试次数:", self.spin_max_retries))
        
        self.spin_retry_delay = QtWidgets.QSpinBox()
        self.spin_retry_delay.setValue(self.api_config.retry_delay)
        self.spin_retry_delay.setMinimum(1)
        self.spin_retry_delay.setMaximum(30)
        self.spin_retry_delay.setSuffix(" 秒")
        self.spin_retry_delay.setStyleSheet(self._get_input_style())
        layout.addWidget(self._create_form_row("重试延迟:", self.spin_retry_delay))
        
        return group
    
    def _create_performance_section(self) -> QtWidgets.QGroupBox:
        """性能优化段"""
        group = QtWidgets.QGroupBox()
        group.setStyleSheet(ui_styles.BUTTON_GROUP_STYLE + """
            QGroupBox { background-color: #f8f9fa; }
            QLabel { color: #333333; }
            QCheckBox { color: #333333; }
        """)
        layout = QtWidgets.QVBoxLayout(group)
        layout.setSpacing(10)
        
        layout.addWidget(self._create_section_header("⚡ 性能优化"))
        
        self.chk_parallel_search = QtWidgets.QCheckBox("🟢 启用并行搜索 (3-5倍速提升)")
        self.chk_parallel_search.setChecked(self.api_config.parallel_search)
        self.chk_parallel_search.setStyleSheet(ui_styles.CACHE_CHECKBOX_STYLE + "color: #27ae60; font-weight: bold;")
        def update_parallel_search_text():
            self.chk_parallel_search.setText("🟢 启用并行搜索 (3-5倍速提升)" if self.chk_parallel_search.isChecked() else "⚫ 启用并行搜索 (3-5倍速提升)")
        self.chk_parallel_search.toggled.connect(update_parallel_search_text)
        update_parallel_search_text()
        layout.addWidget(self.chk_parallel_search)
        
        # 下载并行配置
        download_layout = QtWidgets.QHBoxLayout()
        self.chk_parallel_download = QtWidgets.QCheckBox("🟢 启用并行下载")
        self.chk_parallel_download.setChecked(self.api_config.parallel_download)
        self.chk_parallel_download.setStyleSheet(ui_styles.CACHE_CHECKBOX_STYLE)
        def update_parallel_download_text():
            self.chk_parallel_download.setText("🟢 启用并行下载" if self.chk_parallel_download.isChecked() else "⚫ 启用并行下载")
        self.chk_parallel_download.toggled.connect(update_parallel_download_text)
        update_parallel_download_text()
        download_layout.addWidget(self.chk_parallel_download)
        
        download_layout.addSpacing(20)
        
        lbl_workers = QtWidgets.QLabel("下载线程数:")
        lbl_workers.setStyleSheet("color: #34495e;")
        download_layout.addWidget(lbl_workers)
        
        self.spin_download_workers = QtWidgets.QSpinBox()
        self.spin_download_workers.setValue(self.api_config.download_workers)
        self.spin_download_workers.setMinimum(2)
        self.spin_download_workers.setMaximum(5)
        self.spin_download_workers.setStyleSheet(self._get_input_style())
        self.spin_download_workers.setMaximumWidth(80)
        download_layout.addWidget(self.spin_download_workers)
        download_layout.addStretch()
        
        layout.addLayout(download_layout)
        
        self.chk_parallel_download.toggled.connect(self.spin_download_workers.setEnabled)
        
        return group
    
    def _get_input_style(self) -> str:
        """获取输入框样式"""
        return """
            QLineEdit, QSpinBox {
                background-color: white;
                color: #333333;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px;
            }
            QLineEdit:focus, QSpinBox:focus {
                border: 2px solid #3498db;
                background-color: white;
            }
        """
    
    def on_mode_changed(self):
        """切换 API 模式时更新 UI"""
        is_local = self.rb_local.isChecked()
        self.local_group.setEnabled(is_local)
        self.remote_group.setEnabled(not is_local)
    
    def on_reset_defaults(self):
        """重置为默认配置"""
        reply = QtWidgets.QMessageBox.question(
            self, "重置确认",
            "确定要重置所有配置为默认值吗？",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        if reply == QtWidgets.QMessageBox.Yes:
            from core.api_config import APIConfig, APIMode
            default = APIConfig()
            
            self.rb_local.setChecked(default.is_local_mode())
            self.rb_remote.setChecked(default.is_remote_mode())
            self.spin_local_timeout.setValue(default.local_timeout)
            self.input_remote_url.setText(default.remote_base_url)
            self.spin_remote_timeout.setValue(default.remote_timeout)
            self.chk_verify_ssl.setChecked(default.verify_ssl)
            self.chk_gbw.setChecked("gbw" in default.enable_sources)
            self.chk_by.setChecked("by" in default.enable_sources)
            self.chk_zby.setChecked("zby" in default.enable_sources)
            self.spin_search_limit.setValue(default.search_limit)
            self.spin_max_retries.setValue(default.max_retries)
            self.spin_retry_delay.setValue(default.retry_delay)
            self.chk_parallel_search.setChecked(default.parallel_search)
            self.chk_parallel_download.setChecked(default.parallel_download)
            self.spin_download_workers.setValue(default.download_workers)
            self.on_mode_changed()
            QtWidgets.QMessageBox.information(self, "成功", "已重置为默认配置")

    def get_settings(self):
        """获取用户配置并保存到 API 配置"""
        from core.api_config import APIMode
        
        # 构建数据源列表
        sources = []
        if self.chk_gbw.isChecked():
            sources.append("gbw")
        if self.chk_by.isChecked():
            sources.append("by")
        if self.chk_zby.isChecked():
            sources.append("zby")
        
        # 更新全局 API 配置
        config = get_api_config()
        config.mode = APIMode.LOCAL if self.rb_local.isChecked() else APIMode.REMOTE
        # 下载目录统一由主界面选择，这里不再保存
        if hasattr(self.parent(), "settings"):
            config.local_output_dir = self.parent().settings.get("output_dir", "downloads")
        else:
            config.local_output_dir = "downloads"
        config.local_timeout = self.spin_local_timeout.value()
        config.remote_base_url = self.input_remote_url.text().strip() or "http://127.0.0.1:8000"
        config.remote_timeout = self.spin_remote_timeout.value()
        config.verify_ssl = self.chk_verify_ssl.isChecked()
        config.enable_sources = sources or ["gbw", "by", "zby"]
        config.search_limit = self.spin_search_limit.value()
        config.max_retries = self.spin_max_retries.value()
        config.retry_delay = self.spin_retry_delay.value()
        config.parallel_search = self.chk_parallel_search.isChecked()
        config.parallel_download = self.chk_parallel_download.isChecked()
        config.download_workers = self.spin_download_workers.value()
        
        # 保存到文件
        config.save()
        
        # 返回兼容旧代码的结果
        return {
            "sources": [s.upper() for s in sources] or ["GBW", "BY", "ZBY"],
            "output_dir": config.local_output_dir,
            "page_size": self.spin_search_limit.value(),
        }


class BatchDownloadDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("批量下载")
        self.resize(500, 400)
        self.setModal(True)
        
        layout = QtWidgets.QVBoxLayout(self)
        
        lbl_hint = QtWidgets.QLabel("请输入标准号（每行一个，或使用逗号、空格分隔）：")
        lbl_hint.setStyleSheet("font-weight: bold; color: #333;")
        layout.addWidget(lbl_hint)
        
        self.text_edit = QtWidgets.QPlainTextEdit()
        self.text_edit.setPlaceholderText("例如：\nGB/T 3324-2024\nGB/T 3325-2024\nGB/T 10357.1-2013")
        self.text_edit.setStyleSheet("""
            QPlainTextEdit {
                border: 1px solid #3498db;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Courier New';
                font-size: 12px;
                background-color: white;
                color: #333333;
            }
            QPlainTextEdit:focus {
                border: 2px solid #3498db;
            }
        """)
        layout.addWidget(self.text_edit)
        
        lbl_note = QtWidgets.QLabel("注：程序将自动搜索每个标准号并下载第一个匹配项。")
        lbl_note.setStyleSheet("color: #666; font-size: 10px; font-style: italic;")
        layout.addWidget(lbl_note)
        
        btn_layout = QtWidgets.QHBoxLayout()
        self.btn_ok = QtWidgets.QPushButton("🚀 开始批量下载")
        self.btn_ok.setStyleSheet("""
            QPushButton {
                background-color: #51cf66;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #37b24d; }
            QPushButton:pressed { background-color: #2f8a3d; }
        """)
        self.btn_ok.clicked.connect(self.accept)
        
        self.btn_cancel = QtWidgets.QPushButton("取消")
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #eee;
                color: #333;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 10px 20px;
            }
            QPushButton:hover { background-color: #ddd; }
        """)
        self.btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_ok)
        layout.addLayout(btn_layout)

    def get_ids(self) -> List[str]:
        text = self.text_edit.toPlainText()
        # 修改正则：不再使用 \s 分割，只使用换行、逗号、分号、顿号分割
        # 这样可以保留 "GB 18584-2024" 这种中间带空格的标准号
        raw_ids = re.split(r'[\n\r,，;；、]+', text)
        # 过滤空字符串并去重
        ids = []
        seen = set()
        for i in raw_ids:
            i = i.strip()
            if i and i not in seen:
                ids.append(i)
                seen.add(i)
        return ids


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("标准下载 - 桌面版 V2.0.0")
        
        # 设置窗口图标
        try:
            import os
            icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app.ico")
            if os.path.exists(icon_path):
                self.setWindowIcon(QtGui.QIcon(icon_path))
        except Exception:
            pass
        
        self.resize(1200, 750)
        # 应用全局样式（包含对话框样式与统一的复选框样式）
        try:
            self.setStyleSheet(ui_styles.DIALOG_STYLE + getattr(ui_styles, 'CHECKBOX_STYLE', ''))
        except Exception:
            # 如果样式拼接失败，降级为仅应用对话框样式
            try:
                self.setStyleSheet(ui_styles.DIALOG_STYLE)
            except Exception:
                pass

        # 配置存储（默认值；会被持久化配置覆盖）
        self.settings = {
            "sources": ["GBW", "BY", "ZBY"],
            "output_dir": "downloads",
            "page_size": 30,  # 默认每页30条
            "use_cache": True,  # 默认使用搜索缓存
        }

        # 缓存与历史管理器（用于搜索/下载历史记录）
        self.cache_manager = get_cache_manager()

        # 持久化配置（Win7 兼容）：使用 QSettings（Windows 下为注册表；无需额外文件权限）
        self._load_persistent_settings()
        
        # 分页状态
        self.current_page = 1
        self.total_pages = 1
        # pending search rows (避免在搜索未完全结束前就更新显示)
        self._pending_search_rows = None

        # Web应用线程
        self.web_thread = None
        self.web_server_running = False
        self.web_server_event = threading.Event()  # 用于线程间信号

        # 创建菜单栏
        menubar = self.menuBar()

        central = QtWidgets.QWidget()
        central.setStyleSheet("background-color: #f8f9fa;")
        self.setCentralWidget(central)

        layout = QtWidgets.QHBoxLayout(central)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        layout.addWidget(splitter)

        # 左侧主区（搜索 + 结果）
        left = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left)

        # 搜索行
        search_row = QtWidgets.QWidget()
        sr_layout = QtWidgets.QHBoxLayout(search_row)
        sr_layout.setContentsMargins(0, 0, 0, 0)
        sr_layout.setSpacing(8)
        self.input_keyword = QtWidgets.QLineEdit()
        self.input_keyword.setPlaceholderText("输入标准号或名称（例如 GB/T 3324）")
        self.input_keyword.setStyleSheet(ui_styles.INPUT_STYLE)
        self.input_keyword.returnPressed.connect(self.on_search)
        self.btn_search = QtWidgets.QPushButton("🔍 检索")
        self.btn_search.setMinimumWidth(80)
        self.btn_search.setStyleSheet(ui_styles.BTN_PRIMARY_STYLE)
        self.btn_search.clicked.connect(self.on_search)
        self.chk_use_cache = QtWidgets.QCheckBox("🟢 使用缓存")
        self.chk_use_cache.setChecked(True)
        self.chk_use_cache.setToolTip("命中缓存时直接返回缓存结果，未命中再发起远程搜索")
        # 选中/未选中时切换灯泡颜色
        def update_cache_checkbox_text():
            self.chk_use_cache.setText("🟢 使用缓存" if self.chk_use_cache.isChecked() else "⚫ 使用缓存")
        self.chk_use_cache.toggled.connect(update_cache_checkbox_text)
        # 仅对这个复选框应用特殊样式（隐藏框体，只显示文字灯泡）
        try:
            self.chk_use_cache.setStyleSheet(ui_styles.CACHE_CHECKBOX_STYLE)
        except Exception:
            pass
        sr_layout.addWidget(self.input_keyword, 3)
        sr_layout.addWidget(self.chk_use_cache, 1)
        sr_layout.addWidget(self.btn_search, 1)
        left_layout.addWidget(search_row)

        # 路径和操作行（源选择已移到右侧）
        path_op_row = QtWidgets.QWidget()
        path_op_layout = QtWidgets.QHBoxLayout(path_op_row)
        path_op_layout.setContentsMargins(0, 0, 0, 0)
        path_op_layout.setSpacing(8)
        
        # 下载路径显示 - 放在最左边
        lbl_path = QtWidgets.QLabel("📍 路径:")
        lbl_path.setStyleSheet("font-weight: bold; color: #3498db;")
        self.lbl_download_path = QtWidgets.QLabel("downloads")
        self.lbl_download_path.setStyleSheet("color: #333; min-height: 18px;")
        self.lbl_download_path.setWordWrap(False)
        path_op_layout.addWidget(lbl_path)
        path_op_layout.addWidget(self.lbl_download_path, 1)
        
        # Excel 补全按钮
        self.btn_web_app = QtWidgets.QPushButton("📊 标准补全")
        self.btn_web_app.setMaximumWidth(70)
        self.btn_web_app.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 6px 8px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)
        self.btn_web_app.clicked.connect(self.open_excel_dialog)
        path_op_layout.addWidget(self.btn_web_app)
        
        # 标准查新按钮
        self.btn_standard_info = QtWidgets.QPushButton("🔍 标准查新")
        self.btn_standard_info.setMaximumWidth(70)
        self.btn_standard_info.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 6px 8px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
            QPushButton:pressed {
                background-color: #7d3c98;
            }
        """)
        self.btn_standard_info.clicked.connect(self.open_standard_info_dialog)
        path_op_layout.addWidget(self.btn_standard_info)
        
        # 路径选择按钮 - 宽度调小防止遮挡
        self.btn_select_path = QtWidgets.QPushButton("🔍 选路径")
        self.btn_select_path.setMaximumWidth(70)
        self.btn_select_path.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 6px 8px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #346edb;
            }
            QPushButton:pressed {
                background-color: #3445db;
            }
        """)
        self.btn_select_path.clicked.connect(self.on_select_path)
        path_op_layout.addWidget(self.btn_select_path)
        
        # 打开文件夹按钮
        self.btn_open_folder = QtWidgets.QPushButton("📁 打开")
        self.btn_open_folder.setMaximumWidth(70)
        self.btn_open_folder.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 6px 8px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #346edb;
            }
            QPushButton:pressed {
                background-color: #3445db;
            }
        """)
        self.btn_open_folder.clicked.connect(self.on_open_folder)
        path_op_layout.addWidget(self.btn_open_folder)
        
        # 导出为 CSV 按钮
        self.btn_export = QtWidgets.QPushButton("💾 导出CSV")
        self.btn_export.setMaximumWidth(75)
        self.btn_export.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 6px 8px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #346edb;
            }
            QPushButton:pressed {
                background-color: #3445db;
            }
        """)
        self.btn_export.clicked.connect(self.on_export)
        path_op_layout.addWidget(self.btn_export)

        # 下载源选择由右侧复选框控制（移除下拉框）
        
        # 队列和历史按钮已移到日志标题行
        # self.btn_queue 和 self.btn_history 现在在日志标题行创建
        
        # 设置按钮
        self.btn_settings = QtWidgets.QPushButton("⚙️ 设置")
        self.btn_settings.setMaximumWidth(70)
        self.btn_settings.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 6px 8px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
            QPushButton:pressed {
                background-color: #7d3c98;
            }
        """)
        self.btn_settings.clicked.connect(self.on_settings)
        path_op_layout.addWidget(self.btn_settings)
        
        # 批量下载按钮
        self.btn_batch_download = QtWidgets.QPushButton("🚀 批量下载")
        self.btn_batch_download.setMaximumWidth(85)
        self.btn_batch_download.setStyleSheet("""
            QPushButton {
                background-color: #00b894;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 6px 8px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #00a383;
            }
            QPushButton:pressed {
                background-color: #008f72;
            }
        """)
        self.btn_batch_download.clicked.connect(self.on_batch_download)
        path_op_layout.addWidget(self.btn_batch_download)
        
        # 声明按钮
        self.btn_disclaimer = QtWidgets.QPushButton("📋 声明")
        self.btn_disclaimer.setMaximumWidth(65)
        self.btn_disclaimer.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 6px 8px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #4e555b;
            }
        """)
        self.btn_disclaimer.clicked.connect(self.show_disclaimer)
        path_op_layout.addWidget(self.btn_disclaimer)

        # 创建源复选框（右侧区域显示）
        self.chk_gbw = QtWidgets.QCheckBox("🟢 GBW")
        self.chk_gbw.setChecked(True)
        try:
            self.chk_gbw.setStyleSheet(ui_styles.CACHE_CHECKBOX_STYLE)
        except:
            self.chk_gbw.setStyleSheet("color: #333; font-weight: bold;")
        def update_main_gbw():
            self.chk_gbw.setText("🟢 GBW" if self.chk_gbw.isChecked() else "⚫ GBW")
        self.chk_gbw.toggled.connect(update_main_gbw)
        self.chk_by = QtWidgets.QCheckBox("🟢 BY")
        self.chk_by.setChecked(True)
        try:
            self.chk_by.setStyleSheet(ui_styles.CACHE_CHECKBOX_STYLE)
        except:
            self.chk_by.setStyleSheet("color: #333; font-weight: bold;")
        def update_main_by():
            self.chk_by.setText("🟢 BY" if self.chk_by.isChecked() else "⚫ BY")
        self.chk_by.toggled.connect(update_main_by)
        self.chk_zby = QtWidgets.QCheckBox("🟢 ZBY")
        self.chk_zby.setChecked(True)
        try:
            self.chk_zby.setStyleSheet(ui_styles.CACHE_CHECKBOX_STYLE)
        except:
            self.chk_zby.setStyleSheet("color: #333; font-weight: bold;")
        def update_main_zby():
            self.chk_zby.setText("🟢 ZBY" if self.chk_zby.isChecked() else "⚫ ZBY")
        self.chk_zby.toggled.connect(update_main_zby)

        left_layout.addWidget(path_op_row)

        # 表格操作行：全选、筛选
        table_op_row = QtWidgets.QWidget()
        table_op_layout = QtWidgets.QHBoxLayout(table_op_row)
        table_op_layout.setContentsMargins(0, 4, 0, 4)
        table_op_layout.setSpacing(8)
        
        # 全选按钮
        self.btn_select_all = QtWidgets.QPushButton("☑ 全选")
        self.btn_select_all.setMaximumWidth(80)
        self.btn_select_all.setStyleSheet("""
            QPushButton {
                background-color: #6c5ce7;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 5px 10px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #5b4cdb;
            }
        """)
        self.btn_select_all.clicked.connect(self.on_select_all)
        table_op_layout.addWidget(self.btn_select_all)
        
        # 取消全选按钮
        self.btn_deselect_all = QtWidgets.QPushButton("☐ 取消")
        self.btn_deselect_all.setMaximumWidth(80)
        self.btn_deselect_all.setStyleSheet("""
            QPushButton {
                background-color: #636e72;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 5px 10px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #535c5f;
            }
        """)
        self.btn_deselect_all.clicked.connect(self.on_deselect_all)
        table_op_layout.addWidget(self.btn_deselect_all)
        
        # 分隔线
        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.VLine)
        sep.setStyleSheet("color: #ccc;")
        table_op_layout.addWidget(sep)
        
        # 筛选：仅显示有PDF
        self.chk_filter_pdf = QtWidgets.QCheckBox("⚫ 仅显示PDF")
        try:
            self.chk_filter_pdf.setStyleSheet(ui_styles.CACHE_CHECKBOX_STYLE)
        except:
            self.chk_filter_pdf.setStyleSheet("color: #333; font-weight: bold;")
        def update_pdf_filter_text():
            self.chk_filter_pdf.setText("🟢 仅显示PDF" if self.chk_filter_pdf.isChecked() else "⚫ 仅显示PDF")
        self.chk_filter_pdf.toggled.connect(update_pdf_filter_text)
        self.chk_filter_pdf.stateChanged.connect(self.on_filter_changed)
        table_op_layout.addWidget(self.chk_filter_pdf)
        
        # 分隔线
        sep2 = QtWidgets.QFrame()
        sep2.setFrameShape(QtWidgets.QFrame.VLine)
        sep2.setStyleSheet("color: #ccc;")
        table_op_layout.addWidget(sep2)
        
        # 状态筛选下拉框
        self.combo_status_filter = QtWidgets.QComboBox()
        self.combo_status_filter.addItems(["📋 全部状态", "✅ 现行有效", "📅 即将实施", "❌ 已废止", "📄 其他"])
        self.combo_status_filter.setStyleSheet("""
            QComboBox {
                background-color: #a29bfe;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 5px 12px;
                font-weight: bold;
                font-size: 10px;
                min-width: 100px;
            }
            QComboBox:hover {
                background-color: #6c5ce7;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid white;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                color: #333;
                selection-background-color: #a29bfe;
                selection-color: white;
                border: 1px solid #ddd;
                border-radius: 3px;
                padding: 4px;
            }
        """)
        self.combo_status_filter.currentIndexChanged.connect(self.on_filter_changed)
        table_op_layout.addWidget(self.combo_status_filter)
        
        # 选中数量显示
        self.lbl_selection_count = QtWidgets.QLabel("已选: 0")
        self.lbl_selection_count.setStyleSheet("color: #666; font-size: 10px;")
        table_op_layout.addStretch()
        table_op_layout.addWidget(self.lbl_selection_count)
        
        left_layout.addWidget(table_op_row)

        # 结果表 - 使用 QTableView + StandardTableModel 提升性能与可扩展性
        self.table = QtWidgets.QTableView()
        self.table_model = StandardTableModel(self)
        self.table.setModel(self.table_model)
        self.table.verticalHeader().setVisible(False)
        # 允许编辑触发（确保复选框点击可被处理）
        # 保持表格不可编辑，使用行选择来标记条目
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        
        # 设置列宽模式
        header = self.table.horizontalHeader()
        # 0:选中 - 固定宽度
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Fixed)
        self.table.setColumnWidth(0, 45)
        # 1:序号 - 固定宽度
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Fixed)
        self.table.setColumnWidth(1, 50)
        # 2:标准号 - 内容自适应
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        # 3:名称 - 自动伸缩填充剩余空间
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch)
        # 4:发布日期 - 内容自适应
        header.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeToContents)
        # 5:实施日期 - 内容自适应
        header.setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeToContents)
        # 6:状态 - 内容自适应
        header.setSectionResizeMode(6, QtWidgets.QHeaderView.ResizeToContents)
        # 7:来源 - 内容自适应
        header.setSectionResizeMode(7, QtWidgets.QHeaderView.ResizeToContents)
        # 8:文本 - 固定宽度
        header.setSectionResizeMode(8, QtWidgets.QHeaderView.Fixed)
        self.table.setColumnWidth(8, 50)

        # 美化：专业配色（深蓝头、浅灰行）
        header = self.table.horizontalHeader()
        # 将 CHECKBOX_STYLE 追加到表头和表格样式，避免局部样式覆盖全局复选框样式
        header.setStyleSheet(ui_styles.TABLE_HEADER_STYLE + getattr(ui_styles, 'CHECKBOX_STYLE', ''))
        self.table.setStyleSheet(ui_styles.TABLE_STYLE + getattr(ui_styles, 'CHECKBOX_STYLE', ''))
        # 启用交替行颜色以增强可读性（交替颜色由 TABLE_STYLE 中的 alternate-background-color 控制）
        try:
            self.table.setAlternatingRowColors(True)
        except Exception:
            pass
        # 监听模型数据变化，更新已选数量
        self.table_model.dataChanged.connect(lambda *args, **kwargs: self.update_selection_count())
        # 当用户选择行时，同步模型的 _selected 标记并刷新指示列
        self.table.selectionModel().selectionChanged.connect(self.on_table_selection_changed)
        # 右键菜单用于下载等操作
        self.table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.on_table_context_menu)
        left_layout.addWidget(self.table)
        
        # 分页控件行
        page_row = QtWidgets.QWidget()
        page_layout = QtWidgets.QHBoxLayout(page_row)
        page_layout.setContentsMargins(0, 4, 0, 4)
        page_layout.setSpacing(8)
        
        # 每页数量 - 使用下拉框替代SpinBox
        self.combo_page_size = QtWidgets.QComboBox()
        self.combo_page_size.addItems(["每页 10 条", "每页 20 条", "每页 30 条", "每页 50 条", "每页 100 条"])
        self.combo_page_size.setCurrentIndex(2)  # 默认30条
        self.combo_page_size.setStyleSheet("""
            QComboBox {
                background-color: #74b9ff;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 4px 10px;
                font-weight: bold;
                font-size: 10px;
                min-width: 90px;
            }
            QComboBox:hover {
                background-color: #0984e3;
            }
            QComboBox::drop-down {
                border: none;
                width: 18px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid white;
                margin-right: 6px;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                color: #333;
                selection-background-color: #74b9ff;
                selection-color: white;
                border: 1px solid #ddd;
                border-radius: 3px;
                padding: 4px;
            }
        """)
        self.combo_page_size.currentIndexChanged.connect(self.on_page_size_changed)
        page_layout.addWidget(self.combo_page_size)
        
        page_layout.addStretch()
        
        # 分页信息
        self.lbl_page_info = QtWidgets.QLabel("共 0 条")
        self.lbl_page_info.setStyleSheet("color: #666;")
        page_layout.addWidget(self.lbl_page_info)
        
        # 上一页
        self.btn_prev_page = QtWidgets.QPushButton("◀ 上一页")
        self.btn_prev_page.setMaximumWidth(80)
        self.btn_prev_page.setEnabled(False)
        self.btn_prev_page.setStyleSheet("""
            QPushButton {
                background-color: #74b9ff;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #0984e3;
            }
            QPushButton:disabled {
                background-color: #ddd;
                color: #999;
            }
        """)
        self.btn_prev_page.clicked.connect(self.on_prev_page)
        page_layout.addWidget(self.btn_prev_page)
        
        # 当前页/总页
        self.lbl_page_num = QtWidgets.QLabel("1 / 1")
        self.lbl_page_num.setStyleSheet("color: #333; font-weight: bold; min-width: 60px;")
        self.lbl_page_num.setAlignment(QtCore.Qt.AlignCenter)
        page_layout.addWidget(self.lbl_page_num)
        
        # 下一页
        self.btn_next_page = QtWidgets.QPushButton("下一页 ▶")
        self.btn_next_page.setMaximumWidth(80)
        self.btn_next_page.setEnabled(False)
        self.btn_next_page.setStyleSheet("""
            QPushButton {
                background-color: #74b9ff;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #0984e3;
            }
            QPushButton:disabled {
                background-color: #ddd;
                color: #999;
            }
        """)
        self.btn_next_page.clicked.connect(self.on_next_page)
        page_layout.addWidget(self.btn_next_page)
        
        # 在分页行添加下载按钮，居中显示
        page_layout.addSpacing(20)
        
        # 定义下载按钮 - 放大处理，类似键盘space
        self.btn_download = QtWidgets.QPushButton("📥 下载")
        self.btn_download.setMinimumWidth(120)
        self.btn_download.setMinimumHeight(36)
        self.btn_download.setMaximumHeight(36)
        self.btn_download.setStyleSheet("""
            QPushButton {
                background-color: #51cf66;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #37b24d;
            }
            QPushButton:pressed {
                background-color: #2f8a3d;
            }
        """)
        self.btn_download.clicked.connect(self.on_download)
        page_layout.addWidget(self.btn_download)
        page_layout.addSpacing(20)
        
        left_layout.addWidget(page_row)

        splitter.addWidget(left)

        # 右侧日志区
        right = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right)
        
        # 源选择区域（顶部）
        source_header = QtWidgets.QWidget()
        source_hdr_layout = QtWidgets.QHBoxLayout(source_header)
        source_hdr_layout.setContentsMargins(8, 6, 8, 6)
        source_hdr_layout.setSpacing(8)
        
        lbl_select = QtWidgets.QLabel("源选择:")
        lbl_select.setStyleSheet("color: #333; font-weight: bold; font-size: 11px;")
        source_hdr_layout.addWidget(lbl_select)
        
        source_hdr_layout.addWidget(self.chk_gbw)
        source_hdr_layout.addWidget(self.chk_by)
        source_hdr_layout.addWidget(self.chk_zby)
        
        # 重试按钮
        btn_retry = QtWidgets.QPushButton("🔄 重试")
        btn_retry.setMaximumWidth(65)
        btn_retry.setToolTip("重新测试数据源连通性")
        btn_retry.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 3px 6px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        btn_retry.clicked.connect(self.check_source_health)
        source_hdr_layout.addWidget(btn_retry)
        
        source_hdr_layout.addStretch()

        source_header.setStyleSheet("")
        source_header.setMinimumHeight(35)
        
        right_layout.addWidget(source_header)
        
        # 日志标题与清空按钮
        log_header = QtWidgets.QWidget()
        log_hdr_layout = QtWidgets.QHBoxLayout(log_header)
        log_hdr_layout.setContentsMargins(8, 8, 8, 8)
        lbl = QtWidgets.QLabel("📋 实时日志")
        lbl.setStyleSheet("font-weight: bold; color: #3498db; font-size: 12px;")
        btn_clear = QtWidgets.QPushButton("🗑️ 清空")
        btn_clear.setMaximumWidth(80)
        btn_clear.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: 1px solid #346edb;
                border-radius: 3px;
                padding: 4px 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3445db;
                color: white;
            }
        """)
        btn_clear.clicked.connect(self.on_clear_log)
        log_hdr_layout.addWidget(lbl)
        log_hdr_layout.addStretch()
        
        # 队列按钮
        btn_queue = QtWidgets.QPushButton("📥 队列")
        btn_queue.setMaximumWidth(85)
        btn_queue.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 6px 8px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
        """)
        btn_queue.clicked.connect(self.open_queue_dialog)
        log_hdr_layout.addWidget(btn_queue)
        
        # 历史按钮
        btn_history = QtWidgets.QPushButton("🕒 历史")
        btn_history.setMaximumWidth(85)
        btn_history.setStyleSheet("""
            QPushButton {
                background-color: #16a085;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 6px 8px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #138d75;
            }
        """)
        btn_history.clicked.connect(self.open_history_dialog)
        log_hdr_layout.addWidget(btn_history)
        
        log_hdr_layout.addWidget(btn_clear)
        right_layout.addWidget(log_header)
        
        self.log_view = QtWidgets.QTextEdit()
        self.log_view.setReadOnly(True)
        font = QtGui.QFont("Courier New", 9)
        self.log_view.setFont(font)
        self.log_view.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3e3e3e;
            }
        """)
        right_layout.addWidget(self.log_view)

        # 右侧设置最小宽度，避免分隔条初始挤压导致控件不可见
        right.setMinimumWidth(260)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([900, 360])  # 默认给右侧留出空间，保证复选框可见

        # 状态栏和进度条
        self.status = self.statusBar()
        
        # 进度条
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setMaximumHeight(16)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 8px;
                background-color: #e0e0e0;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 7px;
            }
        """)
        self.progress_bar.hide()
        self.status.addPermanentWidget(self.progress_bar)
        
        # 停止按钮
        self.btn_stop_batch = QtWidgets.QPushButton("停止")
        self.btn_stop_batch.setStyleSheet("""
            QPushButton {
                background-color: #ff6b6b;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 2px 10px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #fa5252; }
            QPushButton:disabled { background-color: #ccc; }
        """)
        self.btn_stop_batch.hide()
        self.btn_stop_batch.clicked.connect(self.on_stop_batch)
        self.status.addPermanentWidget(self.btn_stop_batch)
        
        # 后台状态标签
        self.lbl_bg_status = QtWidgets.QLabel("")
        self.lbl_bg_status.setStyleSheet("color: #666; font-size: 11px;")
        self.status.addPermanentWidget(self.lbl_bg_status)

        # 存储
        self.current_items: List[dict] = []
        self.all_items: List[dict] = []  # 完整列表，用于筛选
        self.filtered_items: List[dict] = []  # 筛选后的列表
        self.background_cache: dict = {}  # 后台搜索缓存 {std_no_normalized: Standard}
        self.last_keyword: str = ""  # 上次搜索关键词

        # 线程占位
        self.search_thread: Optional[SearchThread] = None
        self.download_thread: Optional[DownloadThread] = None
        self.bg_search_thread: Optional[BackgroundSearchThread] = None
        
        # 初始化显示
        self.update_path_display()
        self.update_source_checkboxes()
        self.check_source_health()
        try:
            self.chk_use_cache.setChecked(bool(self.settings.get("use_cache", True)))
        except Exception:
            pass
        
        # 启动下载队列处理器
        self._start_download_queue_processor()

    def _qsettings(self) -> "QtCore.QSettings":
        # 固定组织/应用名，避免因脚本路径变化导致配置丢失
        return QtCore.QSettings("StandardDownloader", "StandardDownloader")

    def _load_persistent_settings(self):
        try:
            qs = self._qsettings()
            output_dir = qs.value("output_dir", self.settings.get("output_dir", "downloads"))
            if isinstance(output_dir, str) and output_dir.strip():
                self.settings["output_dir"] = output_dir.strip()

            page_size = qs.value("page_size", self.settings.get("page_size", 30), type=int)
            try:
                page_size = int(page_size)
            except Exception:
                page_size = self.settings.get("page_size", 30)
            if page_size > 0:
                self.settings["page_size"] = page_size

            sources_val = qs.value("sources", self.settings.get("sources", ["GBW", "BY", "ZBY"]))
            sources: List[str]
            if isinstance(sources_val, str):
                # 兼容被存成 "GBW,BY,ZBY" 的情况
                sources = [s for s in (x.strip() for x in sources_val.split(',')) if s]
            elif isinstance(sources_val, (list, tuple)):
                sources = [str(x) for x in sources_val if str(x)]
            else:
                sources = list(self.settings.get("sources", ["GBW", "BY", "ZBY"]))

            # 过滤无效源
            allowed = {"GBW", "BY", "ZBY"}
            sources = [s for s in sources if s in allowed]
            if sources:
                self.settings["sources"] = sources

            use_cache_val = qs.value("use_cache", self.settings.get("use_cache", True))
            if isinstance(use_cache_val, str):
                use_cache = use_cache_val.lower() != "false"
            else:
                use_cache = bool(use_cache_val)
            self.settings["use_cache"] = use_cache
            try:
                self.chk_use_cache.setChecked(use_cache)
            except Exception:
                pass
        except Exception:
            # 读取失败则使用默认值
            return

    def _save_persistent_settings(self):
        try:
            qs = self._qsettings()
            qs.setValue("output_dir", self.settings.get("output_dir", "downloads"))
            qs.setValue("page_size", int(self.settings.get("page_size", 30)))
            qs.setValue("sources", self.settings.get("sources", ["GBW", "BY", "ZBY"]))
            qs.setValue("use_cache", bool(self.settings.get("use_cache", True)))
            qs.sync()
        except Exception:
            return

    def closeEvent(self, event):
        # 退出前尽量停止后台线程，避免 QThread 仍在运行时被析构导致崩溃/报错
        try:
            threads = []
            # 先收集显式字段引用的线程
            for attr in ("_source_health_thread", "search_thread", "download_thread", "bg_search_thread"):
                th = getattr(self, attr, None)
                if isinstance(th, QtCore.QThread):
                    threads.append(th)

            # 再收集所有子 QThread（避免覆盖引用导致漏停）
            try:
                for th in self.findChildren(QtCore.QThread):
                    threads.append(th)
            except Exception:
                pass

            # 去重
            uniq = []
            seen = set()
            for th in threads:
                try:
                    key = int(th.__hash__())
                except Exception:
                    key = id(th)
                if key in seen:
                    continue
                seen.add(key)
                uniq.append(th)

            for th in uniq:
                try:
                    if not isinstance(th, QtCore.QThread):
                        continue
                    if not th.isRunning():
                        continue
                    try:
                        th.requestInterruption()
                    except Exception:
                        pass
                    # 只有以事件循环为主的线程 quit() 才有效；仍然调用以覆盖该类线程
                    try:
                        th.quit()
                    except Exception:
                        pass
                    try:
                        th.wait(1500)
                    except Exception:
                        pass
                    # 某些线程的 run() 可能在阻塞网络 I/O，quit() 无效；为避免关闭时崩溃，必要时强制终止
                    try:
                        if th.isRunning():
                            th.terminate()
                            th.wait(1000)
                    except Exception:
                        pass
                except Exception:
                    continue
        except Exception:
            pass

        # 退出前持久化配置
        try:
            self._save_persistent_settings()
        except Exception:
            pass
        return super().closeEvent(event)

    def create_menu(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #34c2db;
                color: white;
                border-bottom: 1px solid #346edb;
            }
            QMenuBar::item:selected {
                background-color: #3445db;
            }
            QMenu {
                background-color: #34c2db;
                color: white;
            }
            QMenu::item:selected {
                background-color: #3445db;
                color: white;
            }
        """)
        
        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        action_settings = file_menu.addAction("设置(&S)")
        action_settings.triggered.connect(self.on_settings)
        file_menu.addSeparator()
        action_exit = file_menu.addAction("退出(&Q)")
        action_exit.triggered.connect(self.close)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        action_about = help_menu.addAction("关于(&A)")
        action_about.triggered.connect(self.on_about)

    def append_log(self, text: str):
        if not text:
            return
        
        # 涉及保密，脱敏处理：隐藏所有网址
        text = re.sub(r'https?://[^\s<>"]+', '[URL]', text)
        
        now = datetime.now().strftime("%H:%M:%S")
        # 根据日志内容选择颜色
        if "错误" in text or "失败" in text or "Error" in text:
            color = "#ff6b6b"  # 红色错误
        elif "完成" in text or "成功" in text or "Success" in text:
            color = "#51cf66"  # 绿色成功
        elif "搜索" in text or "下载" in text:
            color = "#4dabf7"  # 蓝色操作
        else:
            color = "#d4d4d4"  # 默认灰色
        
        log_text = f"<span style='color: #999;'>[{now}]</span> <span style='color: {color};'>{text}</span>"
        self.log_view.append(log_text)
        # 自动滚动到底部
        self.log_view.verticalScrollBar().setValue(self.log_view.verticalScrollBar().maximum())

    def on_settings(self):
        """打开设置对话框"""
        dialog = SettingsDialog(self)
        # SettingsDialog 会自动从 api_config 加载配置，无需手动设置
        
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.settings = dialog.get_settings()
            self.append_log(f"设置已更新：{self.settings}")
            self.update_path_display()
            self.check_source_health()
            self._save_persistent_settings()

    def on_clear_log(self):
        """清空日志"""
        self.log_view.clear()
        self.append_log("日志已清空")

    def on_export(self):
        """导出结果为 CSV"""
        if not self.current_items:
            msg = QtWidgets.QMessageBox(self)
            msg.setWindowTitle("提示")
            msg.setText("暂无结果可导出")
            msg.setIcon(QtWidgets.QMessageBox.Information)
            msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: white;
                }
                QPushButton {
                    min-width: 80px;
                    background-color: #34c2db;
                    color: #000000;
                    border: none;
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #2ab5cc;
                }
            """)
            msg.exec()
            return
        
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "导出结果", "", "CSV Files (*.csv);;All Files (*)"
        )
        if not path:
            return
        
        try:
            data = []
            for r in self.current_items:
                data.append({
                    "标准号": r.get("std_no"),
                    "名称": r.get("name"),
                    "发布日期": r.get("publish", ""),
                    "实施日期": r.get("implement", ""),
                    "状态": r.get("status", ""),
                    "替代标准": r.get("replace_std", ""),
                    "有文本": "是" if r.get("has_pdf") else "否",
                })
            df = pd.DataFrame(data)
            df.to_csv(path, index=False, encoding="utf-8-sig")
            self.append_log(f"已导出到: {path}")
            QtWidgets.QMessageBox.information(self, "成功", f"已导出 {len(data)} 条到:\n{path}")
        except Exception as e:
            tb = traceback.format_exc()
            self.append_log(tb)
            QtWidgets.QMessageBox.critical(self, "导出失败", str(e))

    def on_about(self):
        """关于对话框"""
        QtWidgets.QMessageBox.about(
            self,
            "关于",
            "标准下载 - 桌面版\n\n"
            "一个高效的标准文档聚合下载工具。\n\n"
            "功能：\n"
            "• 三源聚合搜索（GBW、BY、ZBY）\n"
            "• 实时日志与进度显示\n"
            "• 批量下载\n"
            "• 导出结果\n\n"
            "版本: 1.0.0"
        )

    def on_open_folder(self):
        """打开下载文件夹"""
        output_dir = self.settings.get("output_dir", "downloads")
        folder_path = Path(output_dir).resolve()
        
        # 如果文件夹不存在，创建它
        folder_path.mkdir(parents=True, exist_ok=True)
        
        try:
            if sys.platform == "win32":
                import os
                os.startfile(str(folder_path))
            elif sys.platform == "darwin":
                import subprocess
                subprocess.run(["open", str(folder_path)])
            else:
                import subprocess
                subprocess.run(["xdg-open", str(folder_path)])
            self.append_log(f"打开文件夹: {folder_path}")
        except Exception as e:
            tb = traceback.format_exc()
            self.append_log(tb)
            QtWidgets.QMessageBox.warning(self, "提示", f"无法打开文件夹: {e}")

    def open_excel_dialog(self):
        """打开 Excel 补全对话框"""
        from app.excel_dialog import ExcelDialog
        
        dialog = ExcelDialog(self)
        # 兼容 PySide2 和 PySide6
        if hasattr(dialog, 'exec'):
            dialog.exec()
        else:
            dialog.exec_()
    
    def open_standard_info_dialog(self):
        """打开标准查新对话框"""
        from app.standard_info_dialog import StandardInfoDialog
        
        dialog = StandardInfoDialog(self, parent_settings=self.settings)
        # 兼容 PySide2 和 PySide6
        if hasattr(dialog, 'exec'):
            dialog.exec()
        else:
            dialog.exec_()
    
    def open_queue_dialog(self):
        """打开下载队列管理对话框"""
        try:
            from app.queue_dialog import QueueDialog
            
            dialog = QueueDialog(self)
            # 兼容 PySide2 和 PySide6
            if hasattr(dialog, 'exec'):
                dialog.exec()
            else:
                dialog.exec_()
        except Exception as e:
            import traceback
            self.append_log(f"❌ 打开队列管理失败: {e}")
            self.append_log(traceback.format_exc())
            QtWidgets.QMessageBox.warning(self, "错误", f"无法打开队列管理:\n{e}")
    
    def open_history_dialog(self):
        """打开历史记录对话框"""
        try:
            from app.history_dialog import HistoryDialog
            
            dialog = HistoryDialog(self)
            # 兼容 PySide2 和 PySide6
            if hasattr(dialog, 'exec'):
                dialog.exec()
            else:
                dialog.exec_()
        except Exception as e:
            import traceback
            self.append_log(f"❌ 打开历史记录失败: {e}")
            self.append_log(traceback.format_exc())
            QtWidgets.QMessageBox.warning(self, "错误", f"无法打开历史记录:\n{e}")

    def _run_web_server(self):
        """在后台线程中运行Flask web服务器"""
        try:
            from web_app.web_app import app
            self.append_log("🚀 Web服务器启动...")
            # 禁用Flask日志输出到控制台，避免干扰
            import logging
            log = logging.getLogger('werkzeug')
            log.setLevel(logging.ERROR)
            
            self.web_server_running = True
            self.web_server_event.set()  # 信号：服务器已启动
            self.append_log("✓ Web服务器已启动在 http://127.0.0.1:5000")
            
            app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
        except Exception as e:
            self.append_log(f"❌ Web服务器启动失败: {e}")
            self.web_server_running = False
            if not self.web_server_event.is_set():
                self.web_server_event.set()  # 即使失败也要设置事件，避免主线程一直等待

    def update_path_display(self):
        """更新路径显示"""
        output_dir = self.settings.get("output_dir", "downloads")
        self.lbl_download_path.setText(output_dir)

    def update_source_checkboxes(self):
        """根据源的连通性更新复选框状态（在后台线程中执行）"""
        try:
            # 启动后台线程检查连通性，结果通过 `_on_source_health_result` 回调
            th = SourceHealthThread(force=False, parent=self)
            self._source_health_thread = th
            th.finished.connect(self._on_source_health_result)
            th.error.connect(lambda tb: self.append_log(f"更新源复选框失败: {tb.splitlines()[-1] if tb else '错误'}"))
            th.start()
        except Exception as e:
            self.append_log(f"更新源复选框失败: {str(e)[:40]}")

    def on_select_path(self):
        """打开文件夹选择对话框"""
        current_path = self.settings.get("output_dir", "downloads")
        folder_path = QtWidgets.QFileDialog.getExistingDirectory(
            self, "选择下载路径", current_path
        )
        if folder_path:
            self.settings["output_dir"] = folder_path
            self.update_path_display()
            self.append_log(f"下载路径已更改: {folder_path}")
            self._save_persistent_settings()

    def check_source_health(self):
        """检查源连通性，在日志中显示结果"""
        # 使用后台线程执行检查
        try:
            self.append_log("🔍 正在检测数据源连通性...")
            th = SourceHealthThread(force=False, parent=self)
            self._source_health_thread = th
            th.finished.connect(self._on_check_source_health_result)
            th.error.connect(lambda tb: self.append_log(f"❌ 连通性检测失败: {tb.splitlines()[-1] if tb else '错误'}"))
            th.start()
        except Exception as e:
            self.append_log(f"❌ 连通性检测失败: {str(e)[:40]}")

    def _start_download_queue_processor(self):
        """启动下载队列处理器"""
        try:
            from core.download_queue import get_queue_manager
            # 使用单worker避免并发冲突
            self.queue_manager = get_queue_manager(max_workers=1)
            
            # 检查是否已经启动
            if self.queue_manager.is_running():
                self.append_log("✅ 下载队列处理器已在运行")
                # 即使已经在运行，也要设置回调
                self.queue_manager.on_task_start = self._on_queue_task_start
                self.queue_manager.on_task_complete = self._on_queue_task_complete
                self.queue_manager.on_task_fail = self._on_queue_task_fail
                return
            
            # 设置回调
            self.queue_manager.on_task_start = self._on_queue_task_start
            self.queue_manager.on_task_complete = self._on_queue_task_complete
            self.queue_manager.on_task_fail = self._on_queue_task_fail
            
            # 启动队列处理（传入工作函数）
            self.queue_manager.start(self._download_worker_func)
            self.append_log("✅ 下载队列处理器已启动（单worker模式）")
        except Exception as e:
            import traceback
            self.append_log(f"❌ 启动队列处理器失败: {str(e)}")
            print(traceback.format_exc())
    
    def _download_worker_func(self, task):
        """队列工作函数：执行实际下载
        
        Args:
            task: DownloadTask 对象
            
        Returns:
            tuple: (success: bool, error_msg: str, file_path: str)
        """
        try:
            from core.models import Standard
            from core.aggregated_downloader import AggregatedDownloader
            from pathlib import Path
            
            # 从任务元数据重建 Standard 对象
            metadata = task.metadata or {}
            std = Standard(
                std_no=metadata.get("std_no", task.std_no),
                name=metadata.get("name", task.std_name),
                publish_date=metadata.get("publish", ""),
                implement_date=metadata.get("implement", ""),
                status=metadata.get("status", ""),
                sources=metadata.get("sources", []),
                has_pdf=True,
                source_meta=metadata.get("source_meta", {})
            )
            
            # 获取输出目录
            output_dir = Path(self.settings.get("output_dir", "downloads"))
            
            # 获取下载源顺序
            prefer_order = []
            if hasattr(self, 'chk_by') and self.chk_by.isChecked():
                prefer_order.append("BY")
            if hasattr(self, 'chk_gbw') and self.chk_gbw.isChecked():
                prefer_order.append("GBW")
            if hasattr(self, 'chk_zby') and self.chk_zby.isChecked():
                prefer_order.append("ZBY")
            if not prefer_order:
                prefer_order = ["BY", "GBW", "ZBY"]
            
            # 执行下载
            downloader = AggregatedDownloader(output_dir=str(output_dir), enable_sources=None)
            file_path, logs = downloader.download(std, prefer_order=prefer_order)
            
            if file_path:
                return (True, "", str(file_path))
            else:
                error_msg = "所有来源均未成功"
                if logs:
                    # 从日志中提取错误信息
                    error_lines = [line for line in logs if "失败" in line or "错误" in line]
                    if error_lines:
                        error_msg = error_lines[-1][:100]
                return (False, error_msg, "")
                
        except Exception as e:
            import traceback
            error_msg = f"{str(e)[:100]}"
            print(f"Download worker error: {traceback.format_exc()}")
            return (False, error_msg, "")
    
    def _on_queue_task_start(self, task):
        """队列任务开始回调"""
        self.append_log(f"📥 开始下载: {task.std_no} {task.std_name}")
    
    def _on_queue_task_complete(self, task):
        """队列任务完成回调"""
        self.append_log(f"✅ 下载成功: {task.std_no} -> {task.file_path}")
    
    def _on_queue_task_fail(self, task):
        """队列任务失败回调"""
        error_msg = task.error_msg if task.error_msg else "未知错误"
        self.append_log(f"❌ 下载失败: {task.std_no} - {error_msg}")

    # ========== 缓存判定与日期辅助 ==========
    def _parse_date_safe(self, value: str) -> Optional[datetime]:
        """容错解析日期，支持常见 ISO/日期格式，解析失败返回 None"""
        if not value:
            return None
        candidates = [value]
        # 兼容 "2024-12-31 00:00:00" 这样的格式
        if " " in value and "T" not in value:
            candidates.append(value.replace(" ", "T"))
        for v in candidates:
            try:
                return datetime.fromisoformat(v.strip())
            except Exception:
                continue
        return None

    def _record_is_near_abolish(self, record: dict, days: int = 180) -> bool:
        """判断单条记录是否接近作废期；缺少日期则返回 False"""
        date_keys = ["abolish", "abolish_date", "expire_date", "obsolete_date", "废止日期"]
        now = datetime.now()
        for key in date_keys:
            dt = self._parse_date_safe(record.get(key, ""))
            if not dt:
                continue
            delta = (dt - now).days
            if delta < 0:
                return True  # 已过期
            if delta <= days:
                return True
        return False

    def _should_skip_cache_for_near_abolish(self, cached_results: List[dict]) -> Optional[str]:
        """检测缓存结果里是否存在临期/已过期标准；返回提示文本或 None"""
        for rec in cached_results:
            if self._record_is_near_abolish(rec):
                std_no = rec.get("std_no", "")
                abolish_date = rec.get("abolish") or rec.get("abolish_date") or rec.get("expire_date") or rec.get("obsolete_date") or rec.get("废止日期") or ""
                return f"标准 {std_no} 将/已作废（日期: {abolish_date}），跳过缓存"
        return None

    def on_search(self):
        keyword = self.input_keyword.text().strip()
        if not keyword:
            QtWidgets.QMessageBox.warning(self, "提示", "请输入关键词")
            return
        self.btn_search.setEnabled(False)
        self.last_keyword = keyword
        self.background_cache = {}  # 清空后台缓存
        
        # 清空之前的搜索结果
        self.all_items = []
        self.current_items = []
        self.filtered_items = []
        self.table_model.set_items([])
        
        # 显示进度条
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self.status.showMessage("正在搜索...")
        
        # 获取复选框中选中的源
        sources = []
        if self.chk_gbw.isChecked():
            sources.append("GBW")
        if self.chk_by.isChecked():
            sources.append("BY")
        if self.chk_zby.isChecked():
            sources.append("ZBY")
        
        if not sources:
            QtWidgets.QMessageBox.warning(self, "提示", "请至少选择一个数据源")
            self.btn_search.setEnabled(True)
            self.progress_bar.hide()
            return
        
        # 更新设置中的源列表
        self.settings["sources"] = sources

        # 是否使用缓存
        use_cache = bool(self.chk_use_cache.isChecked())
        self.settings["use_cache"] = use_cache
        self._save_persistent_settings()
        self.append_log(f"🔍 开始搜索: {keyword} | 源: {','.join(sources)} | 使用缓存: {'是' if use_cache else '否'}")

        # 如果启用缓存，先尝试命中
        if use_cache:
            try:
                cache_results = self.cache_manager.get_search_cache(keyword, sources, page=1)
            except Exception as e:
                cache_results = None
                self.append_log(f"⚠️  读取缓存失败，将发起远程搜索: {str(e)[:80]}")

            if cache_results:
                skip_reason = self._should_skip_cache_for_near_abolish(cache_results)
                if skip_reason:
                    self.append_log(f"⚠️  缓存跳过: {skip_reason}")
                else:
                    self.append_log(f"📦 缓存命中，返回 {len(cache_results)} 条记录")
                    self.all_items = cache_results
                    self.current_page = 1
                    # 主界面搜索不进行智能过滤，直接显示缓存结果
                    # self._apply_smart_filter_for_no_year()
                    self.apply_filter()
                    self.status.showMessage(f"已从缓存加载 {len(self.all_items)} 条结果", 3000)
                    self.progress_bar.hide()
                    self.btn_search.setEnabled(True)
                    return
            else:
                self.append_log("ℹ️  缓存未命中，开始远程搜索")
        else:
            self.append_log("ℹ️  已关闭缓存，强制远程搜索")
        
        # 使用UI上的每页数量设置
        page_size = self.get_page_size()
        self.search_thread = SearchThread(
            keyword=keyword, 
            sources=sources, 
            page=1, 
            page_size=page_size,
            output_dir=self.settings.get("output_dir", "downloads")
        )
        # 连接渐进式结果信号（新）
        self.search_thread.partial_results.connect(self.on_partial_search_results)
        self.search_thread.all_completed.connect(self.on_all_search_completed)
        self.search_thread.log.connect(self.append_log)
        self.search_thread.progress.connect(self.on_search_progress)
        self.search_thread.error.connect(lambda tb: self.append_log(f"错误详情:\n{tb}"))
        self.search_thread.start()
    
    def on_search_progress(self, current: int, total: int, message: str):
        """更新搜索进度"""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.status.showMessage(message)
    
    def on_partial_search_results(self, source_name: str, rows: List[dict]):
        """处理单个源的搜索结果（渐进式显示）"""
        if not rows:
            return

        # 添加源标记：如果是 MERGED（来自流式合并），则从 sources 字段中选择最优源显示
        # 否则直接使用当前源名称
        for row in rows:
            if source_name == "MERGED":
                # 流式搜索已合并，从 sources 中选择最优源显示
                sources = row.get("sources", [])
                if sources:
                    # 按优先级选择：有 PDF 的优先，其次 BY>GBW>ZBY
                    def score_src(src):
                        score = 0
                        if row.get("has_pdf"):
                            score += 100
                        if src == "BY":
                            score += 3
                        elif src == "GBW":
                            score += 2
                        elif src == "ZBY":
                            score += 1
                        return score
                    
                    best_src = max(sources, key=score_src)
                    row['_display_source'] = best_src
                else:
                    row['_display_source'] = "MERGED"
            else:
                row['_display_source'] = source_name

        # 合并到现有结果（以完整标准号去重，保证同一标准号只显示一条）
        existing_keys = set()
        for item in self.all_items:
            std_no = item.get("std_no", "")
            key = StandardSearchMerger._normalize_std_no(std_no)
            existing_keys.add(key)

        new_items = []
        updated_items = []

        for row in rows:
            std_no = row.get("std_no", "")
            key = StandardSearchMerger._normalize_std_no(std_no)

            if key in existing_keys:
                # 已存在，更新信息（如果新源更优）
                for item in self.all_items:
                    item_key = StandardSearchMerger._normalize_std_no(item.get("std_no", ""))
                    if item_key == key:
                        # 合并源信息
                        old_obj = item.get("obj")
                        new_obj = row.get("obj")
                        if old_obj and new_obj:
                            # 合并sources
                            all_sources = set(old_obj.sources + new_obj.sources)
                            old_obj.sources = list(all_sources)
                            new_obj.sources = list(all_sources)

                            # 统一 has_pdf：任意源有文本/附件即为 True
                            has_pdf_any = bool(old_obj.has_pdf or new_obj.has_pdf)
                            item["has_pdf"] = has_pdf_any
                            old_obj.has_pdf = has_pdf_any
                            new_obj.has_pdf = has_pdf_any

                            # 选择最优显示源：先看有无 PDF，其次 BY>GBW>ZBY
                            def score_source(src, obj):
                                score = 0
                                if obj.has_pdf:
                                    score += 100
                                if src == "BY":
                                    score += 3
                                elif src == "GBW":
                                    score += 2
                                elif src == "ZBY":
                                    score += 1
                                return score

                            current_src = item.get("_display_source", "") or (old_obj.sources[0] if old_obj.sources else "")
                            best = (current_src, old_obj)

                            for cand_src, cand_obj in [(source_name, new_obj)]:
                                if score_source(cand_src, cand_obj) > score_source(best[0], best[1]):
                                    best = (cand_src, cand_obj)

                            item["_display_source"] = best[0]

                        updated_items.append(item)
                        break
            else:
                # 新增
                new_items.append(row)
                existing_keys.add(key)

        # 添加新项目
        if new_items:
            self.all_items.extend(new_items)
            self.append_log(f"   📍 {source_name} 新增 {len(new_items)} 条独有结果")

        # 重新排序和显示
        def status_sort_key(item):
            status = item.get("status", "")
            if "现行" in status:
                return 0
            elif "即将实施" in status:
                return 1
            elif "废止" in status:
                return 3
            else:
                return 2

        self.all_items.sort(key=status_sort_key)
        self.current_page = 1
        self.apply_filter()

        self.status.showMessage(f"{source_name} 完成，当前共 {len(self.all_items)} 条结果", 2000)
    
    def _apply_smart_filter_for_no_year(self):
        """智能过滤：当搜索关键词不带年代号时，只保留现行标准或最新版本"""
        self.append_log(f"   [DEBUG] 智能过滤开始: keyword='{self.last_keyword if self.last_keyword else 'None'}', items={len(self.all_items) if self.all_items else 0}")
        
        if not self.last_keyword or not self.all_items:
            self.append_log(f"   ⚠️  智能过滤跳过")
            return
        
        # 检测是否带年代号（例如 GB/T 1234-2024 或 QB/T 2280-2016）
        import re
        has_year_pattern = re.compile(r'-\d{4}$')
        keyword_has_year = bool(has_year_pattern.search(self.last_keyword.strip()))
        self.append_log(f"   [DEBUG] 关键词带年号={keyword_has_year}")
        
        if keyword_has_year:
            # 带年代号，不需要过滤
            self.append_log(f"   ℹ️  关键词带年代号，跳过智能过滤")
            return
        
        # 不带年代号，执行智能过滤
        self.append_log(f"   🔍 检测到不带年代号的搜索，自动筛选现行标准...")
        
        # 提取基础标准号（去除年代号）
        def get_base_std_no(std_no: str) -> str:
            """提取基础标准号，去除年代号"""
            cleaned = has_year_pattern.sub('', std_no).strip()
            return cleaned
        
        # 按基础标准号分组
        from collections import defaultdict
        groups = defaultdict(list)
        for item in self.all_items:
            std_no = item.get("std_no", "")
            base = get_base_std_no(std_no)
            if base:
                groups[base].append(item)
        
        # 为每组选择最佳标准（优先现行，其次最新年份）
        filtered_items = []
        for base_std_no, items in groups.items():
            if len(items) == 1:
                # 只有一个版本，直接保留
                filtered_items.append(items[0])
                continue
            
            # 优先选择"现行"标准
            current_items = [item for item in items if "现行" in item.get("status", "")]
            
            if current_items:
                # 有现行标准，选择年份最新的
                def extract_year(item):
                    std_no = item.get("std_no", "")
                    match = re.search(r'-(\d{4})$', std_no)
                    return int(match.group(1)) if match else 0
                
                current_items.sort(key=extract_year, reverse=True)
                best_item = current_items[0]
                filtered_items.append(best_item)
                
                # 记录日志
                if len(items) > 1:
                    self.append_log(f"      ✅ {base_std_no}: 保留现行标准 {best_item.get('std_no')}")
            else:
                # 没有现行标准，选择年份最新的
                def extract_year(item):
                    std_no = item.get("std_no", "")
                    match = re.search(r'-(\d{4})$', std_no)
                    return int(match.group(1)) if match else 0
                
                items.sort(key=extract_year, reverse=True)
                best_item = items[0]
                filtered_items.append(best_item)
                
                if len(items) > 1:
                    self.append_log(f"      ℹ️  {base_std_no}: 无现行标准，保留最新版本 {best_item.get('std_no')}")
        
        # 更新结果
        original_count = len(self.all_items)
        self.all_items = filtered_items
        filtered_count = len(filtered_items)
        
        if original_count > filtered_count:
            self.append_log(f"   ✅ 智能过滤完成：从 {original_count} 条结果筛选出 {filtered_count} 条现行/最新标准")
            # 重新应用过滤和排序
            self.apply_filter()

    def on_all_search_completed(self):
        """所有源搜索完成"""
        # 主界面搜索不进行智能过滤，直接显示所有搜到的结果
        # self._apply_smart_filter_for_no_year()
        
        self.btn_search.setEnabled(True)
        self.progress_bar.hide()
        self.status.showMessage(f"搜索完成，共找到 {len(self.all_items)} 条结果", 5000)
        self.append_log(f"✅ 所有数据源搜索完成，共 {len(self.all_items)} 条结果")

        # 缓存搜索结果并记录历史
        try:
            serialized = self._serialize_search_results_for_cache()
            self.cache_manager.save_search_cache(
                keyword=self.last_keyword,
                sources=self.settings.get("sources", []),
                page=1,
                results=serialized
            )
        except Exception as e:
            self.append_log(f"⚠️  缓存搜索结果失败: {str(e)[:80]}")
            try:
                self.cache_manager.db.add_search_history(
                    keyword=self.last_keyword,
                    sources=self.settings.get("sources", []),
                    result_count=len(self.all_items)
                )
            except Exception:
                pass

    
    def on_search_finished(self):
        """搜索线程结束（兼容旧版，已被 on_all_search_completed 替代）"""
        # 保留此方法以防万一，但主要逻辑已移到 on_all_search_completed
        pass

    def _serialize_search_results_for_cache(self) -> List[dict]:
        """将当前搜索结果转换为可缓存的纯数据结构（包含下载信息）"""
        serialized = []
        for item in self.all_items or []:
            obj = item.get("obj")
            sources = []
            try:
                if obj and getattr(obj, "sources", None):
                    sources = list(obj.sources)
            except Exception:
                sources = []

            if not sources:
                if isinstance(item.get("sources"), list):
                    sources = item.get("sources")
                elif isinstance(item.get("sources"), str):
                    sources = [item.get("sources")]

            # 保存完整对象信息以支持下载
            obj_data = None
            if obj:
                try:
                    obj_data = {
                        "std_no": getattr(obj, "std_no", ""),
                        "name": getattr(obj, "name", ""),
                        "publish": getattr(obj, "publish", ""),
                        "implement": getattr(obj, "implement", ""),
                        "status": getattr(obj, "status", ""),
                        "sources": list(getattr(obj, "sources", [])),
                        "has_pdf": getattr(obj, "has_pdf", False),
                        "source_meta": getattr(obj, "source_meta", {}),
                        "_class_name": obj.__class__.__name__,
                    }
                except Exception:
                    pass

            serialized.append({
                "std_no": item.get("std_no", ""),
                "name": item.get("name", ""),
                "publish": item.get("publish", ""),
                "implement": item.get("implement", ""),
                "status": item.get("status", ""),
                "has_pdf": bool(item.get("has_pdf")),
                "sources": sources,
                "_display_source": item.get("_display_source", ""),
                "_obj_data": obj_data,  # 保存对象数据用于下载
            })
        return serialized

    def on_bg_search_finished_legacy(self, cache: dict):
        """后台搜索完成（已废弃，保留以防兼容性问题）"""
        # 新版渐进式搜索已经在 on_partial_search_results 中实时合并数据
        # 此方法保留但不再使用
        pass

    def on_search_results(self, rows: List[dict]):
        # 按状态排序：现行有效 > 即将实施 > 其他
        def status_sort_key(item):
            status = item.get("status", "")
            if "现行" in status:
                return 0
            elif "即将实施" in status:
                return 1
            elif "废止" in status:
                return 3
            else:
                return 2
        
        rows.sort(key=status_sort_key)

        # 存为 pending，等待线程 finished 信号再更新界面，避免在搜索过程中部分/空结果被误显示
        self._pending_search_rows = rows
        self.status.showMessage(f"已接收 {len(rows)} 条结果，等待搜索完成...", 2000)

    def _on_source_health_result(self, health_status: dict):
        """用于 `update_source_checkboxes` 的回调，更新复选框状态"""
        try:
            for src_name, checkbox in [("GBW", self.chk_gbw), ("BY", self.chk_by), ("ZBY", self.chk_zby)]:
                health = health_status.get(src_name)
                # 默认保持可选，让用户可以手动勾选
                checkbox.setEnabled(True)
                if health is None:
                    # 无检测结果则不强制变更勾选状态
                    continue
                is_available = getattr(health, 'available', False)
                checkbox.setChecked(bool(is_available))
        except Exception as e:
            tb = traceback.format_exc()
            self.append_log(tb)

    def _on_check_source_health_result(self, health_status: dict):
        """连通性检测回调，在日志中显示结果"""
        try:
            for src in ["GBW", "BY", "ZBY"]:
                health = health_status.get(src)
                if health:
                    is_available = getattr(health, 'available', False)
                    if is_available:
                        self.append_log(f"🟢 {src} 源连通性正常")
                    else:
                        # 获取不通原因
                        error_msg = getattr(health, 'error', '')
                        reason = f" - {error_msg}" if error_msg else ""
                        self.append_log(f"🔴 {src} 源连接失败{reason}")
                else:
                    self.append_log(f"⚠️  {src} 源检测结果为空")
        except Exception as e:
            tb = traceback.format_exc()
            self.append_log(f"❌ 处理连通性结果失败: {str(e)}")
            self.append_log(tb)
    
    def apply_filter(self):
        """根据筛选条件显示数据"""
        items = self.all_items.copy()

        # PDF筛选
        if self.chk_filter_pdf.isChecked():
            items = [r for r in items if r.get("has_pdf")]

        # 状态筛选
        status_filter = self.combo_status_filter.currentText()
        if "全部" not in status_filter:
            if "现行有效" in status_filter:
                items = [r for r in items if "现行" in r.get("status", "")]
            elif "即将实施" in status_filter:
                items = [r for r in items if "即将实施" in r.get("status", "")]
            elif "已废止" in status_filter:
                items = [r for r in items if "废止" in r.get("status", "")]
            elif "其他" in status_filter:
                items = [r for r in items if not any(s in r.get("status", "") for s in ["现行", "即将实施", "废止"])]

        self.filtered_items = items

        # 计算分页
        page_size = self.get_page_size()
        total_count = len(items)
        self.total_pages = max(1, (total_count + page_size - 1) // page_size)

        # 确保当前页有效
        if self.current_page > self.total_pages:
            self.current_page = self.total_pages
        if self.current_page < 1:
            self.current_page = 1

        # 获取当前页数据并交给模型展示
        start_idx = (self.current_page - 1) * page_size
        end_idx = start_idx + page_size
        page_items = items[start_idx:end_idx]

        self.current_items = page_items

        # 将 page_items 传入模型（模型会触发刷新）
        if hasattr(self, 'table_model') and self.table_model:
            self.table_model.set_items(page_items)
        else:
            # 兼容回退到 QTableWidget（极少用）
            try:
                self.table.setRowCount(0)
                for idx, r in enumerate(page_items, start=start_idx + 1):
                    row = self.table.rowCount()
                    chk = QtWidgets.QTableWidgetItem()
                    chk.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
                    chk.setCheckState(QtCore.Qt.Unchecked)
                    self.table.setItem(row, 0, chk)
                    self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(str(idx)))
                    self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(r.get("std_no", "")))
                    self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(r.get("name", "")))
                    self.table.setItem(row, 4, QtWidgets.QTableWidgetItem(r.get("publish", "")))
                    self.table.setItem(row, 5, QtWidgets.QTableWidgetItem(r.get("implement", "")))
                    self.table.setItem(row, 6, QtWidgets.QTableWidgetItem(r.get("status", "")))
                    self.table.setItem(row, 7, QtWidgets.QTableWidgetItem("✓" if r.get("has_pdf") else "-"))
            except Exception:
                pass

        self.update_page_controls(total_count)
        self.update_selection_count()
    
    def update_page_controls(self, total_count: int):
        """更新分页控件状态"""
        self.lbl_page_info.setText(f"共 {total_count} 条")
        self.lbl_page_num.setText(f"{self.current_page} / {self.total_pages}")
        self.btn_prev_page.setEnabled(self.current_page > 1)
        self.btn_next_page.setEnabled(self.current_page < self.total_pages)
    
    def on_prev_page(self):
        """上一页"""
        if self.current_page > 1:
            self.current_page -= 1
            self.apply_filter()
    
    def on_next_page(self):
        """下一页"""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.apply_filter()
    
    def on_page_size_changed(self, index: int):
        """每页数量改变"""
        page_size = self.get_page_size()
        self.settings["page_size"] = page_size
        self.current_page = 1
        if hasattr(self, 'all_items') and self.all_items:
            self.apply_filter()
    
    def get_page_size(self) -> int:
        """从下拉框获取每页数量"""
        page_size_map = {0: 10, 1: 20, 2: 30, 3: 50, 4: 100}
        return page_size_map.get(self.combo_page_size.currentIndex(), 30)
    
    def on_filter_changed(self):
        """筛选条件改变时重新显示"""
        self.current_page = 1  # 重置到第一页
        if hasattr(self, 'all_items'):
            self.apply_filter()
    
    def on_select_all(self):
        """全选所有行"""
        if hasattr(self, 'table_model') and self.table_model:
            self.table_model.set_all_selected(True)
        else:
            for row in range(self.table.rowCount()):
                item = self.table.item(row, 0)
                if item:
                    item.setCheckState(QtCore.Qt.Checked)
        self.update_selection_count()
    
    def on_deselect_all(self):
        """取消全选"""
        if hasattr(self, 'table_model') and self.table_model:
            self.table_model.set_all_selected(False)
        else:
            for row in range(self.table.rowCount()):
                item = self.table.item(row, 0)
                if item:
                    item.setCheckState(QtCore.Qt.Unchecked)
        self.update_selection_count()

    def on_table_selection_changed(self, selected, deselected):
        """同步选择模型到项的 _selected 标记并刷新指示列"""
        try:
            sel_rows = {idx.row() for idx in self.table.selectionModel().selectedRows()}
            for i, it in enumerate(self.table_model._items):
                prev = bool(it.get("_selected"))
                now = i in sel_rows
                if prev != now:
                    it["_selected"] = now
                    idx = self.table_model.index(i, 0)
                    self.table_model.dataChanged.emit(idx, idx, [QtCore.Qt.BackgroundRole, QtCore.Qt.DisplayRole, QtCore.Qt.ForegroundRole])
        except Exception:
            pass
        self.update_selection_count()

    def on_table_context_menu(self, pos):
        """表格右键菜单：下载所选"""
        menu = QtWidgets.QMenu(self)
        act_download = menu.addAction("下载所选")
        act = menu.exec_(self.table.viewport().mapToGlobal(pos))
        if act == act_download:
            self.on_download()
    
    def update_selection_count(self):
        """更新已选数量显示"""
        count = 0
        try:
            if hasattr(self, 'table_model') and self.table_model:
                count = len(self.table_model.get_selected_items())
            else:
                for row in range(self.table.rowCount()):
                    item = self.table.item(row, 0)
                    if item and item.checkState() == QtCore.Qt.Checked:
                        count += 1
        except Exception:
            count = 0
        self.lbl_selection_count.setText(f"已选: {count}")
    
    def on_table_item_changed(self, item):
        """表格项变化时更新选中数量（仅监听第0列复选框）"""
        if item.column() == 0:
            self.update_selection_count()
    
    def on_download(self):
        selected = []
        if hasattr(self, 'table_model') and self.table_model:
            selected = self.table_model.get_selected_items()
        else:
            for row in range(self.table.rowCount()):
                item = self.table.item(row, 0)
                if item and item.checkState() == QtCore.Qt.Checked:
                    selected.append(self.current_items[row])

        if not selected:
            QtWidgets.QMessageBox.information(self, "提示", "请先选择要下载的行")
            return

        self.append_log(f"📥 准备下载 {len(selected)} 条")
        if self.background_cache:
            self.append_log(f"   ↳ 后台缓存可用: {len(self.background_cache)} 条补充数据")
        
        # 点击下载时立即清除所有选中状态，防止下次下载时误选
        if hasattr(self, 'table_model') and self.table_model:
            self.table_model.set_all_selected(False)
        else:
            for row in range(self.table.rowCount()):
                item = self.table.item(row, 0)
                if item:
                    item.setCheckState(QtCore.Qt.Unchecked)
        
        self.btn_download.setEnabled(False)
        
        # 显示进度条
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(len(selected))
        self.progress_bar.show()
        
        # 从配置获取并行下载设置
        config = get_api_config()
        output_dir = self.settings.get("output_dir", "downloads")

        # 下载源选择：由日志上方复选框决定，但始终按优先级 GBW > BY > ZBY 排序
        # 也就是说最终传入的 prefer_order 是用户勾选的子集，但按 GBW, BY, ZBY 的优先级排列
        prefer_order = []
        by_checked = getattr(self, 'chk_by', None)
        gbw_checked = getattr(self, 'chk_gbw', None)
        zby_checked = getattr(self, 'chk_zby', None)
        # 固定优先级列表
        priority = ["GBW", "BY", "ZBY"]
        # 将用户勾选映射为按优先级排序的子集
        selected_set = set()
        if gbw_checked and gbw_checked.isChecked():
            selected_set.add("GBW")
        if by_checked and by_checked.isChecked():
            selected_set.add("BY")
        if zby_checked and zby_checked.isChecked():
            selected_set.add("ZBY")
        for p in priority:
            if p in selected_set:
                prefer_order.append(p)
        if not prefer_order:
            QtWidgets.QMessageBox.information(self, "提示", "请在日志上方勾选至少一个下载源")
            self.btn_download.setEnabled(True)
            self.progress_bar.hide()
            return
        
        # 如果已有下载线程正在运行，提示并返回，避免覆盖仍在运行的 QThread 对象
        if hasattr(self, 'download_thread') and self.download_thread is not None:
            try:
                if getattr(self.download_thread, 'isRunning', lambda: False)():
                    QtWidgets.QMessageBox.information(self, "提示", "已有下载任务正在进行，请等待完成或取消后再启动新的下载。")
                    self.btn_download.setEnabled(True)
                    self.progress_bar.hide()
                    return
            except Exception:
                pass

        self.download_thread = DownloadThread(
            selected, 
            output_dir=output_dir,
            background_cache=self.background_cache,
            parallel=config.parallel_download,
            max_workers=config.download_workers,
            prefer_order=prefer_order
        )
        self.download_thread.log.connect(self.append_log)
        self.download_thread.progress.connect(self.on_download_progress)
        self.download_thread.finished.connect(self.on_download_finished)
        self.download_thread.start()
    
    def on_download_progress(self, current: int, total: int, message: str):
        """更新下载进度"""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.status.showMessage(message)

    def on_download_finished(self, success: int, fail: int):
        self.append_log(f"📊 下载结果：{success} 成功，{fail} 失败")
        self.btn_download.setEnabled(True)
        self.progress_bar.hide()
        self.status.showMessage(f"下载完成: {success} 成功, {fail} 失败", 5000)
        
        # 清理下载线程引用，确保线程对象在停止后可以安全释放
        try:
            if hasattr(self, 'download_thread') and self.download_thread is not None:
                try:
                    if getattr(self.download_thread, 'isRunning', lambda: False)():
                        # 等待短暂时间让线程退出（通常 finished 已触发，线程已停止）
                        self.download_thread.wait(2000)
                except Exception:
                    pass
                self.download_thread = None
        except Exception:
            pass

    def add_to_download_queue(self, standards: List):
        """从历史/缓存添加标准到下载队列
        
        Args:
            standards: Standard 对象列表
        """
        if not standards:
            return
        
        try:
            from core.download_queue import get_queue_manager
            queue_manager = get_queue_manager()
            
            # 批量添加任务到队列
            added_count = 0
            skipped_count = 0
            
            for std in standards:
                # 检查是否有PDF
                if not std.has_pdf:
                    skipped_count += 1
                    continue
                
                # 获取来源
                sources = std.sources if isinstance(std.sources, list) else []
                source_str = ",".join(sources[:3]) if sources else "未知"
                
                # 准备元数据
                metadata = {
                    "std_no": std.std_no,
                    "name": std.name,
                    "publish": std.publish,
                    "implement": std.implement,
                    "status": std.status,
                    "sources": sources,
                    "source_meta": std.source_meta if hasattr(std, 'source_meta') else {}
                }
                
                # 添加到队列
                task_id = queue_manager.add_task(
                    std_no=std.std_no,
                    std_name=std.name,
                    priority=5,  # 默认优先级
                    source=source_str,
                    max_retries=3,
                    metadata=metadata
                )
                added_count += 1
            
            # 显示结果消息
            if added_count > 0:
                msg = f"✅ 已添加 {added_count} 个任务到下载队列"
                if skipped_count > 0:
                    msg += f"\n⚠️ 跳过 {skipped_count} 个（无PDF）"
                self.append_log(msg)
            else:
                msg = "⚠️ 没有可添加的任务（所有标准都没有PDF）"
                self.append_log(msg)
                
        except Exception as e:
            import traceback
            error_msg = f"添加到队列失败：{str(e)}"
            self.append_log(f"❌ {error_msg}")
            print(f"Error: {error_msg}\n{traceback.format_exc()}")

    def show_disclaimer(self):
        """显示免责声明"""
        disclaimer_text = """
<h2 style='color: #e74c3c; text-align: center;'>⚠️ 免责声明 ⚠️</h2>

<h3>一、软件性质</h3>
<p>1. 本软件（"标准下载工具"）按"现状"提供，仅供<b>学习、研究和技术交流</b>使用。</p>
<p>2. 本软件为免费开源软件，开发者不提供任何形式的明示或暗示保证，包括但不限于对适用性、准确性、可靠性的保证。</p>

<h3>二、数据来源与版权</h3>
<p>1. 本软件仅提供数据<b>整合和下载功能</b>，所有标准文件数据均来源于<b>公开可访问的第三方平台</b>。</p>
<p>2. 所有标准文件的版权归<b>原始发布方和版权所有者</b>所有。</p>
<p>3. 用户下载的文件应仅用于个人学习研究，不得用于商业用途。</p>

<h3>三、使用风险与责任</h3>
<p>1. 使用本软件的<b>所有风险由用户自行承担</b>。</p>
<p>2. 开发者不对以下情况承担任何责任：</p>
<ul>
  <li>因使用或无法使用本软件而导致的任何直接或间接损失</li>
  <li>数据的准确性、完整性、时效性</li>
  <li>服务中断、数据丢失、系统故障等情况</li>
  <li>因违反法律法规或侵犯第三方权益而产生的任何纠纷</li>
</ul>

<h3>四、法律合规</h3>
<p>1. 用户必须遵守<b>中华人民共和国相关法律法规</b>，包括但不限于《著作权法》《标准化法》等。</p>
<p>2. 禁止将本软件用于任何<b>非法用途</b>或侵犯他人合法权益的行为。</p>
<p>3. 禁止将本软件用于<b>商业盈利目的</b>，包括但不限于转售、出租、提供有偿服务等。</p>

<h3>五、其他条款</h3>
<p>1. <b>使用本软件即表示您已阅读、理解并同意接受本声明的全部内容。</b></p>
<p>2. 如您不同意本声明的任何内容，请立即停止使用本软件并删除所有相关文件。</p>
<p>3. 开发者保留随时修改本声明的权利，修改后的声明将在软件更新后生效。</p>
<p>4. 本声明的解释权归软件开发者所有。</p>

<p style='margin-top: 20px; padding: 10px; background-color: #fff3cd; border-left: 4px solid #ffc107;'>
<b>📌 特别提示：</b>标准文件涉及国家规范和技术要求，建议通过官方渠道获取正式版本用于生产和认证用途。
</p>
        """
        
        # 创建自定义对话框
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("免责声明")
        dialog.resize(700, 550)
        
        # 设置窗口图标
        try:
            import os
            icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app.ico")
            if os.path.exists(icon_path):
                dialog.setWindowIcon(QtGui.QIcon(icon_path))
        except Exception:
            pass
        
        # 主布局
        layout = QtWidgets.QVBoxLayout(dialog)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 内容区域（可滚动）
        content_widget = QtWidgets.QTextEdit()
        content_widget.setReadOnly(True)
        content_widget.setHtml(disclaimer_text)
        content_widget.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: none;
                padding: 20px;
                font-family: 'Microsoft YaHei', Arial;
                font-size: 10pt;
            }
        """)
        layout.addWidget(content_widget)
        
        # 按钮区域（居中）
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.setContentsMargins(20, 20, 20, 20)
        btn_layout.addStretch()
        
        btn_ok = QtWidgets.QPushButton("✓ 我已阅读并同意")
        btn_ok.setMinimumSize(150, 45)
        btn_ok.setStyleSheet("""
            QPushButton {
                background-color: #34c2db;
                color: #000000;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #2ab5cc;
            }
        """)
        btn_ok.clicked.connect(dialog.accept)
        btn_layout.addWidget(btn_ok)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        dialog.setStyleSheet("background-color: white;")
        dialog.exec()

    def on_batch_download(self):
        """打开批量下载对话框"""
        dialog = BatchDownloadDialog(self)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            ids = dialog.get_ids()
            if not ids:
                QtWidgets.QMessageBox.information(self, "提示", "请输入至少一个标准号")
                return
            
            self.append_log(f"🚀 开始批量下载任务，共 {len(ids)} 个标准号")
            self.btn_batch_download.setEnabled(False)
            
            # 显示进度条和停止按钮
            self.progress_bar.setValue(0)
            self.progress_bar.setMaximum(len(ids))
            self.progress_bar.show()
            self.btn_stop_batch.setEnabled(True)
            self.btn_stop_batch.setText("停止")
            self.btn_stop_batch.show()
            
            output_dir = self.settings.get("output_dir", "downloads")
            enable_sources = self.settings.get("sources", ["GBW", "BY", "ZBY"])
            
            # 支持配置worker数量（默认3个）
            num_workers = self.settings.get("download_workers", 3)
            
            self.batch_thread = BatchDownloadThread(
                ids, 
                output_dir=output_dir,
                enable_sources=enable_sources,
                num_workers=num_workers
            )
            self.batch_thread.log.connect(self.append_log)
            self.batch_thread.progress.connect(self.on_download_progress)
            self.batch_thread.finished.connect(self.on_batch_download_finished)
            self.batch_thread.start()

    def on_stop_batch(self):
        """停止批量下载"""
        if hasattr(self, 'batch_thread') and self.batch_thread.isRunning():
            self.batch_thread.stop()
            self.btn_stop_batch.setEnabled(False)
            self.btn_stop_batch.setText("正在停止...")
            self.append_log("⏳ 正在请求停止批量下载任务...")

    def on_batch_download_finished(self, success: int, fail: int, failed_list: list):
        self.append_log(f"📊 批量下载任务结束")
        self.append_log(f"   ✅ 成功: {success}")
        self.append_log(f"   ❌ 失败: {fail}")
        
        if failed_list:
            self.append_log(f"📋 失败清单:")
            for item in failed_list:
                self.append_log(f"   - {item}")
        
        self.btn_batch_download.setEnabled(True)
        self.progress_bar.hide()
        self.btn_stop_batch.hide()
        self.status.showMessage(f"批量下载完成: {success} 成功, {fail} 失败", 5000)
        
        msg = f"批量下载任务已结束。\n\n成功: {success}\n失败: {fail}"
        if failed_list:
            msg += "\n\n失败清单:\n" + "\n".join(failed_list[:15])
            if len(failed_list) > 15:
                msg += f"\n... 等共 {len(failed_list)} 项"

        info_box = QtWidgets.QMessageBox(self)
        info_box.setWindowTitle("任务完成")
        info_box.setText(msg)
        info_box.setIcon(QtWidgets.QMessageBox.Information)
        info_box.setStyleSheet("""
            QMessageBox { background-color: #f5f5f5; }
            QLabel { color: #333333; font-size: 12px; }
            QPushButton { background-color: #eeeeee; color: #333333; border: 1px solid #dddddd; border-radius: 4px; padding: 6px 14px; }
            QPushButton:hover { background-color: #e0e0e0; }
        """)
        info_box.exec()


def main():
    app = QtWidgets.QApplication(sys.argv)
    
    # 密码验证（必须在 QApplication 创建后执行）
    if not check_password():
        return 0
    
    # 提前预热 OCR 模型和下载器，避免第一次下载时卡顿
    def prewarm_all():
        try:
            from sources.gbw_download import prewarm_ocr
            prewarm_ocr()
        except Exception:
            pass
        try:
            # 预热全量下载器，建立连接池
            client = get_aggregated_downloader(enable_sources=None)
            if client:
                # 尝试对主要域名进行一次 HEAD 请求以预热 TCP/SSL 连接
                for src in client.sources:
                    if src.name == "GBW":
                        try:
                            # 预热 search 域名 (支持 HTTPS)
                            src.session.head("https://std.samr.gov.cn/gb/search/gbQueryPage", timeout=5, proxies={"http": None, "https": None})
                            # 预热 download 域名 (仅支持 HTTP)
                            src.session.head("http://c.gb688.cn/bzgk/gb/showGb", timeout=5, proxies={"http": None, "https": None})
                        except Exception:
                            pass
        except Exception:
            pass
            
    threading.Thread(target=prewarm_all, daemon=True).start()
    
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
