#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为非root用户添加sudo支持的补丁脚本
在param_manager.py和safety_mechanism.py中的sysctl命令前自动添加sudo
"""
import re
import sys
from pathlib import Path

def patch_file(filepath: Path, backup: bool = True):
    """为文件中的sysctl命令添加sudo"""
    content = filepath.read_text(encoding='utf-8')
    
    # 备份原文件
    if backup:
        backup_path = filepath.with_suffix(filepath.suffix + '.bak')
        backup_path.write_text(content, encoding='utf-8')
        print(f"✅ 已备份: {backup_path}")
    
    # 替换sysctl命令（读取操作不需要sudo）
    # 只替换 sysctl -w 的情况
    pattern = r"(\['sysctl', '-w')"
    replacement = r"(['sudo', 'sysctl', '-w'"
    
    new_content = re.sub(pattern, replacement, content)
    
    if new_content != content:
        filepath.write_text(new_content, encoding='utf-8')
        print(f"✅ 已修改: {filepath}")
        return True
    else:
        print(f"ℹ️  无需修改: {filepath}")
        return False

def main():
    # 获取父目录
    current_dir = Path(__file__).parent
    parent_dir = current_dir.parent
    
    files_to_patch = [
        parent_dir / "param_manager.py",
        parent_dir / "safety_mechanism.py",
        parent_dir / "kylin_adapter.py"
    ]
    
    print("=" * 60)
    print("为sysctl命令添加sudo支持")
    print("=" * 60)
    
    patched_count = 0
    for filepath in files_to_patch:
        if filepath.exists():
            if patch_file(filepath):
                patched_count += 1
        else:
            print(f"⚠️  文件不存在: {filepath}")
    
    print("\n" + "=" * 60)
    print(f"完成！共修改 {patched_count} 个文件")
    print("=" * 60)
    print("\n提示：")
    print("1. 原文件已备份为 .bak 文件")
    print("2. 如需恢复，运行: python patch_for_sudo.py restore")
    print("3. 确保你的用户有sudo权限")
    print("4. 建议配置无密码sudo: sudo visudo")

def restore():
    """恢复原文件"""
    current_dir = Path(__file__).parent
    parent_dir = current_dir.parent
    
    backup_files = list(parent_dir.glob("*.py.bak"))
    
    if not backup_files:
        print("未找到备份文件")
        return
    
    print("=" * 60)
    print("恢复原文件")
    print("=" * 60)
    
    for backup_file in backup_files:
        original_file = backup_file.with_suffix('')
        content = backup_file.read_text(encoding='utf-8')
        original_file.write_text(content, encoding='utf-8')
        print(f"✅ 已恢复: {original_file}")
        backup_file.unlink()
        print(f"✅ 已删除备份: {backup_file}")
    
    print("\n完成！")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "restore":
        restore()
    else:
        main()

