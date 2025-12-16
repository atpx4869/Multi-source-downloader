# -*- coding: utf-8 -*-
"""
PyInstaller build configuration script
"""

import os
import sys
import subprocess
from pathlib import Path


def build_app():
    """Build executable"""
    
    project_root = Path(__file__).parent
    dist_dir = project_root / "dist"
    build_dir = project_root / "build"
    
    print("=" * 60)
    print("Building application...")
    print("=" * 60)
    
    # Get architecture from environment
    arch = os.environ.get('PYINSTALLER_ARCH', '64bit')
    app_name = f"app-{arch}"
    
    # PyInstaller arguments
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        f"--name={app_name}",
        "--add-data=core:core",
        "--add-data=sources:sources",
        "--add-data=ppllocr:ppllocr",
        "--hidden-import=core",
        "--hidden-import=core.models",
        "--hidden-import=core.aggregated_downloader",
        "--hidden-import=sources",
        "--hidden-import=sources.gbw",
        "--hidden-import=sources.by",
        "--hidden-import=sources.zby",
        "--hidden-import=ppllocr",
        "--hidden-import=ppllocr.inference",
        "--hidden-import=onnxruntime",
        "--hidden-import=requests",
        "--hidden-import=pandas",
        "--hidden-import=PySide6",
        "--collect-all=streamlit",
        "--collect-all=pandas",
        "--collect-all=PySide6",
        "--exclude-module=tests",
        "--exclude-module=pytest",
        "--clean",
        "--noconfirm",
        str(project_root / "desktop_app.py"),
    ]
    
    print(f"Running: {' '.join(cmd)}\n")
    print(f"Architecture: {arch}\n")
    
    try:
        result = subprocess.run(cmd, cwd=str(project_root), check=True)
        
        if result.returncode == 0:
            exe_path = dist_dir / f"{app_name}.exe"
            if exe_path.exists():
                file_size_mb = exe_path.stat().st_size / (1024*1024)
                print("\n" + "=" * 60)
                print("Build successful!")
                print(f"Executable: {exe_path}")
                print(f"File size: {file_size_mb:.1f} MB")
                print(f"Architecture: {arch}")
                print("=" * 60 + "\n")
                return True
        else:
            print(f"Build failed, return code: {result.returncode}")
            return False
            
    except Exception as e:
        print(f"Build error: {e}")
        return False


if __name__ == "__main__":
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    success = build_app()
    sys.exit(0 if success else 1)

