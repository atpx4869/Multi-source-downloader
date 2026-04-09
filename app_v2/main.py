# -*- coding: utf-8 -*-
"""
全新应用入口 - V2版本
完全独立，不依赖旧代码
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from PySide6 import QtWidgets
except ImportError:
    from PySide2 import QtWidgets

from app_v2.ui.password_dialog import ModernPasswordDialog
from app_v2.ui.main_window import ModernMainWindow


def main():
    """主函数"""
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # 密码验证
    password = ModernPasswordDialog.get_password()
    if not password:
        print("用户取消登录")
        return 0
    
    print("密码验证成功，启动主窗口...")
    
    # 创建主窗口
    window = ModernMainWindow()
    window.show()
    
    # 确保窗口显示
    window.raise_()
    window.activateWindow()
    
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
