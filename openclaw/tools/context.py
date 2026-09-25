#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目上下文组件
=======================
说明：
    该组件提供了项目上下文的管理，包括文件树生成。
    工作状态: Working
"""
import os
import platform
import subprocess

class ProjectContexter:
    def __init__(self, whereami: str, exclude_dirs: list[str] = None, max_depth: int = 4):
        self.current_path = whereami
        self.exclude_dirs = exclude_dirs or ['.git', '__pycache__', 'node_modules', '.idea', '.vscode', 'venv']
        self.max_depth = max_depth
        
        self.look_around()
    
    def look_around(self) -> None:
        info = {
            "where_am_i": self.current_path,
            "whats_here": self._see_files(),
            "recent_changes": self._see_changes(),
            "git_status": self._see_git(),
            "os": self._get_os_info()
        }
        self.project_info = info
        return info
    
    def _see_files(self) -> str:
        return self._generate_file_tree(self.current_path)
    
    def _generate_file_tree(self, root_path: str, prefix: str = "", depth: int = 0, is_last: bool = True) -> str:
        if depth > self.max_depth:
            return ""
            
        base_name = os.path.basename(root_path)
        if base_name.startswith('.') and base_name not in ['.', '..']:
            return ""
            
        if depth == 0:
            line = f"{base_name}/\n"
        else:
            connector = "└── " if is_last else "├── "
            line = f"{prefix}{connector}{base_name}"
            if os.path.isdir(root_path):
                line += "/"
            line += "\n"
        
        result = [line]
        
        if os.path.isdir(root_path) and base_name not in self.exclude_dirs:
            try:
                items = os.listdir(root_path)
                items.sort()
                dirs = [item for item in items if os.path.isdir(os.path.join(root_path, item)) 
                       and not item.startswith('.') and item not in self.exclude_dirs]
                files = [item for item in items if os.path.isfile(os.path.join(root_path, item)) 
                        and not item.startswith('.')]
                sorted_items = dirs + files
                
                for i, item in enumerate(sorted_items):
                    item_path = os.path.join(root_path, item)
                    is_last_item = (i == len(sorted_items) - 1)
                    new_prefix = prefix + ("    " if is_last else "│   ")
                    
                    child_tree = self._generate_file_tree(
                        item_path, new_prefix, depth + 1, is_last_item
                    )
                    if child_tree:
                        result.append(child_tree)
                        
            except PermissionError:
                error_line = prefix + ("    " if is_last else "│   ") + "└── [Permission Denied]\n"
                result.append(error_line)
        
        return "".join(result)
    
    def get_simple_tree(self) -> str:
        tree_lines = [f"{os.path.basename(self.current_path)}/\n"]
        
        def _build_simple(path: str, prefix: str = "", is_last: bool = True):
            try:
                items = sorted(os.listdir(path))
                dirs = [d for d in items if os.path.isdir(os.path.join(path, d)) 
                       and not d.startswith('.') and d not in self.exclude_dirs]
                files = [f for f in items if os.path.isfile(os.path.join(path, f)) 
                        and not f.startswith('.')]
                
                all_items = dirs + files
                
                for i, item in enumerate(all_items):
                    item_path = os.path.join(path, item)
                    connector = "└── " if i == len(all_items) - 1 else "├── "
                    is_directory = os.path.isdir(item_path)
                    
                    line = f"{prefix}{connector}{item}"
                    if is_directory:
                        line += "/"
                    tree_lines.append(line + "\n")
                    
                    if is_directory:
                        new_prefix = prefix + ("    " if i == len(all_items) - 1 else "│   ")
                        _build_simple(item_path, new_prefix, i == len(all_items) - 1)
                        
            except PermissionError:
                tree_lines.append(prefix + "└── [Permission Denied]\n")
        
        _build_simple(self.current_path)
        return "".join(tree_lines)
    
    def _see_changes(self) -> str:
        try:
            result = subprocess.run(
                ['git', 'log', '--oneline', '-5'],
                capture_output=True, text=True, cwd=self.current_path
            )
            if result.returncode == 0:
                return result.stdout.strip() or "No recent changes found"
        except:
            pass
        return "Git not available or no changes"
    
    def _see_git(self) -> str:
        try:
            result = subprocess.run(
                ['git', 'status', '--short'],
                capture_output=True, text=True, cwd=self.current_path
            )
            if result.returncode == 0:
                return result.stdout.strip() or "Working directory clean"
        except:
            pass
        return "Not a git repository or git not available"
        
    def _get_os_info(self) -> str:
        p = platform.system()
        return f"OS: {p}"
    
    def display_project_context(self) -> None:
        return f"""
==================================================
项目上下文信息
==================================================
操作系统: {self.project_info['os']}
当前位置: {self.project_info['where_am_i']}

文件结构:
{self.project_info['whats_here']}

最近更改:
{self.project_info['recent_changes']}

Git状态:
{self.project_info['git_status']}
==================================================
        """



if __name__ == "__main__":
    context = ProjectContexter()
    
    print(context.display_project_context())