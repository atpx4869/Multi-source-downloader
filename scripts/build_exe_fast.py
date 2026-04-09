"""
PyInstaller 快速打包脚本 - 目录模式（1-2分钟完成）
"""
import os
import sys
import subprocess
import shutil

# 修复 Windows 终端编码
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def clean_build():
    """清理之前的构建"""
    dirs_to_clean = ['build', 'dist']
    
    for d in dirs_to_clean:
        if os.path.exists(d):
            shutil.rmtree(d, ignore_errors=True)
            print(f"✓ 清理目录: {d}")

def build_exe_fast():
    """快速构建（目录模式）"""
    print("\n" + "="*70)
    print("⚡ 快速打包模式（目录版，1-2分钟完成）")
    print("="*70 + "\n")
    
    # 使用更简洁的参数
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--noconfirm',
        '--windowed',                      # 无控制台
        '--name=MultiSourceDownloader',
        '--icon=app.ico',
        
        # 只收集核心模块
        '--hidden-import=PySide6.QtCore',
        '--hidden-import=PySide6.QtGui',
        '--hidden-import=PySide6.QtWidgets',
        
        # 数据文件
        '--add-data=config;config',
        
        # 主程序
        'desktop_app.py'
    ]
    
    print("执行命令:")
    print(' '.join(cmd))
    print("\n" + "-"*70 + "\n")
    
    try:
        subprocess.run(cmd, check=True)
        
        print("\n" + "="*70)
        print("✅ 打包成功！")
        print("="*70)
        
        exe_path = os.path.join('dist', 'MultiSourceDownloader', 'MultiSourceDownloader.exe')
        if os.path.exists(exe_path):
            print("\n📦 生成的程序：")
            print("   位置: dist\\MultiSourceDownloader\\")
            print("   启动: dist\\MultiSourceDownloader\\MultiSourceDownloader.exe")
            print("\n💡 整个 dist\\MultiSourceDownloader 文件夹就是你的应用")
            print("   可以压缩后分发给用户")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print("\n❌ 打包失败")
        print(f"错误代码: {e.returncode}")
        return False

def main():
    print("="*70)
    print("Multi-Source Downloader - 快速打包工具")
    print("="*70)
    
    clean_build()
    
    print("\n🔨 开始快速打包（预计 1-2 分钟）...")
    success = build_exe_fast()
    
    if success:
        print("\n" + "="*70)
        print("✅ 完成！")
        print("="*70)
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()
