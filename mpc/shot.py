#!/usr/bin/env python3
"""
shot.py - 单人开发者的时间机器工具
基于 mpc 实现的极简版本控制，无需 add/commit/merge/branch
"""

import argparse
import os
import sys
import json
import hashlib
import shutil
import subprocess
import tempfile
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 尝试导入 mpc 的核心模块
try:
    from mpc.core import Packer, Unpacker, Lister
except ImportError:
    print("错误: 未找到 mpc 模块，请确保 mpc 已安装或在 PYTHONPATH 中")
    sys.exit(1)


class Shot:
    """shot 核心管理类"""
    
    def __init__(self, repo_path: Optional[str] = None, list_mode: bool = False):
        """
        初始化 shot 仓库
        Args:
            repo_path: 指定存档根路径，默认使用 ~/.shot/ 或 SHOT_PATH 环境变量
            list_mode: 列表模式，不初始化项目相关路径
        """
        # 确定基础存档目录
        if repo_path:
            self.base_dir = Path(repo_path).expanduser().resolve()
        elif os.environ.get("SHOT_PATH"):
            self.base_dir = Path(os.environ["SHOT_PATH"]).expanduser().resolve()
        else:
            self.base_dir = Path.home() / ".shot"
        
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # 列表模式：只需要基础目录
        if list_mode:
            self.shot_dir = self.base_dir
            self.timeline_file = None
            self.ignore_file = None
            self.current_link = None
            self.timeline = []
            self.ignore_patterns = []
            self.work_dir = None
            return
        
        # 正常模式：确定工作目录和项目目录
        self.work_dir = self._find_project_root()
        self.project_id = self._get_project_id()
        self.shot_dir = self.base_dir / self.project_id
        self.shot_dir.mkdir(parents=True, exist_ok=True)
        
        self.timeline_file = self.shot_dir / "timeline.json"
        self.ignore_file = self.shot_dir / ".shotignore"
        self.current_link = self.shot_dir / "current"
        
        # 需要保留的文件/目录（不会被删除）
        self.preserved_items = {".shotignore", ".shot_root", ".shci", ".git"}
        
        # 加载时间线
        self.timeline = self._load_timeline()
        
        # 加载忽略规则
        self.ignore_patterns = self._load_ignore_patterns()
    
    def _find_project_root(self) -> Path:
        """向上查找包含 .shot_root 标记文件的目录，否则返回当前目录"""
        current = Path.cwd()
        for parent in [current] + list(current.parents):
            if (parent / ".shot_root").exists():
                return parent
        return current
    
    def _get_project_id(self) -> str:
        """
        根据项目路径生成唯一标识符
        使用项目根目录的绝对路径的 hash
        """
        # 使用项目根目录的绝对路径生成 hash
        abs_path = self.work_dir.resolve()
        path_hash = hashlib.sha256(str(abs_path).encode()).hexdigest()[:8]
        
        # 同时使用目录名作为可读前缀
        project_name = self.work_dir.name
        
        # 清理项目名中的非法字符
        project_name = re.sub(r'[<>:"/\\|?*]', '_', project_name)
        
        return f"{project_name}_{path_hash}"
    
    def _load_timeline(self) -> List[Dict]:
        """加载时间线 JSON"""
        if self.timeline_file and self.timeline_file.exists():
            try:
                with open(self.timeline_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []
    
    def _save_timeline(self):
        """保存时间线 JSON"""
        if self.timeline_file:
            with open(self.timeline_file, 'w', encoding='utf-8') as f:
                json.dump(self.timeline, f, indent=2, ensure_ascii=False)
    
    def _load_ignore_patterns(self) -> List[str]:
        """加载 .shotignore 忽略规则（自动检测编码）"""
        patterns = []
        # 默认忽略
        default_ignores = [".shot/", ".shot_root", "*.mpc", "__pycache__/", ".git/"]
        patterns.extend(default_ignores)
        
        def read_ignore_file(filepath: Path):
            """尝试用不同编码读取文件"""
            if not filepath.exists():
                return []
            for encoding in ['utf-8', 'gbk', 'utf-8-sig', 'latin-1']:
                try:
                    with open(filepath, 'r', encoding=encoding) as f:
                        lines = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
                    return lines
                except (UnicodeDecodeError, UnicodeError):
                    continue
            return []
        
        # 用户自定义忽略（项目级）
        if self.ignore_file:
            patterns.extend(read_ignore_file(self.ignore_file))
        
        # 全局忽略（可选）
        global_ignore = self.base_dir / ".shotignore"
        patterns.extend(read_ignore_file(global_ignore))
        
        return patterns

    def _should_ignore(self, path: Path) -> bool:
        """检查路径是否应被忽略"""
        if not self.work_dir:
            return False
        try:
            rel_path = str(path.relative_to(self.work_dir)).replace('\\', '/')
        except ValueError:
            return False
        
        for pattern in self.ignore_patterns:
            # 处理目录模式（以 / 结尾）
            if pattern.endswith('/'):
                # 匹配任意深度的该目录
                if pattern in rel_path or rel_path.startswith(pattern) or rel_path.endswith(pattern):
                    return True
                # 如果当前路径就是这个目录本身
                if rel_path == pattern.rstrip('/'):
                    return True
            # 处理通配符
            elif '*' in pattern:
                # 简单的通配符匹配（转为正则）
                import re
                regex = pattern.replace('.', r'\.').replace('*', '[^/]*')
                if re.search(regex, rel_path):
                    return True
            # 精确匹配或前缀匹配
            else:
                if rel_path == pattern or rel_path.startswith(pattern + '/'):
                    return True
                # 匹配任意深度的文件名
                if '/' + pattern in rel_path or rel_path.endswith('/' + pattern):
                    return True
        
        return False
    
    def _clear_work_dir(self):
        """清空工作目录（保留特定文件）"""
        if not self.work_dir:
            return
        for item in self.work_dir.iterdir():
            if item.name not in self.preserved_items:
                try:
                    if item.is_file() or item.is_symlink():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
                except Exception as e:
                    print(f"警告: 无法删除 {item}: {e}")
    
    def _generate_hash(self) -> str:
        """生成基于时间戳和内容的短哈希"""
        timestamp = datetime.now().isoformat()
        return hashlib.sha256(timestamp.encode()).hexdigest()[:8]
    
    def _get_archive_path(self, hash_id: str) -> Path:
        """获取存档文件路径"""
        return self.shot_dir / f"{hash_id}.mpc"
    
    def _get_current_hash(self) -> Optional[str]:
        """获取当前指向的哈希"""
        if self.current_link and self.current_link.exists():
            try:
                return self.current_link.read_text().strip()
            except IOError:
                return None
        return None
    
    def _set_current_hash(self, hash_id: str):
        """设置当前指向的哈希"""
        if self.current_link:
            self.current_link.write_text(hash_id)
    
    def status(self, detail: bool = False) -> int:
        """
        显示当前工作区状态（与最后一次 shot 的差异）
        Returns:
            0: 无变化, 1: 有变化, 2: 无任何历史
        """
        last_hash = self._get_current_hash()
        if not last_hash or last_hash not in [e['hash'] for e in self.timeline]:
            print("未找到任何历史记录，请先运行 'shot push'")
            return 2
        
        # 获取最后一次存档
        last_archive = self._get_archive_path(last_hash)
        if not last_archive.exists():
            print(f"警告: 存档文件 {last_archive} 不存在")
            return 2
        
        # 解压到临时目录进行比较
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            try:
                unpacker = Unpacker(str(last_archive), password="", show_progress=False)
                unpacker.unpack(str(tmp_path))
            except Exception as e:
                print(f"解压失败: {e}")
                return 2
            
            # 比较差异
            changed = []
            new = []
            deleted = []
            
            # 递归比较文件
            for current_file in self.work_dir.rglob('*'):
                if current_file.is_file() and not self._should_ignore(current_file):
                    if current_file.name in self.preserved_items:
                        continue
                    try:
                        rel = current_file.relative_to(self.work_dir)
                        tmp_file = tmp_path / rel
                        if not tmp_file.exists():
                            new.append(str(rel))
                        else:
                            if current_file.stat().st_size != tmp_file.stat().st_size:
                                changed.append(str(rel))
                            elif current_file.read_bytes() != tmp_file.read_bytes():
                                changed.append(str(rel))
                    except ValueError:
                        continue
            
            # 查找被删除的文件
            for tmp_file in tmp_path.rglob('*'):
                if tmp_file.is_file():
                    try:
                        rel = tmp_file.relative_to(tmp_path)
                        if not (self.work_dir / rel).exists():
                            deleted.append(str(rel))
                    except ValueError:
                        continue
            
            if not changed and not new and not deleted:
                print("工作区与最后一次存档一致")
                return 0
            
            print(f"自 {last_hash} 以来的变更:")
            if detail or changed:
                print(f"\n  修改 ({len(changed)}):")
                for f in changed[:20]:
                    print(f"    • {f}")
                if len(changed) > 20:
                    print(f"    ... 还有 {len(changed)-20} 个文件")
            
            if detail or new:
                print(f"\n  新增 ({len(new)}):")
                for f in new[:20]:
                    print(f"    + {f}")
                if len(new) > 20:
                    print(f"    ... 还有 {len(new)-20} 个文件")
            
            if detail or deleted:
                print(f"\n  删除 ({len(deleted)}):")
                for f in deleted[:20]:
                    print(f"    - {f}")
                if len(deleted) > 20:
                    print(f"    ... 还有 {len(deleted)-20} 个文件")
            
            return 1
    
    def push(self, message: str = "") -> str:
        """
        保存当前工作区状态
        Returns:
            生成的哈希值
        """
        # 生成哈希
        hash_id = self._generate_hash()
        archive_path = self._get_archive_path(hash_id)
        
        # 使用 mpc 打包
        try:
            packer = Packer(
                name=str(self.work_dir),
                mode="dir",
                compress=True,
                compression_algorithm="zstd",
                encrypt=False,
                password="",
                show_progress=True
            )
            packer.pack(str(archive_path))
        except Exception as e:
            print(f"打包失败: {e}")
            return ""
        
        # 记录时间线
        entry = {
            "hash": hash_id,
            "time": datetime.now().isoformat(),
            "message": message or f"自动存档 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "work_dir": str(self.work_dir)
        }
        self.timeline.append(entry)
        self._save_timeline()
        self._set_current_hash(hash_id)
        
        print(f"已保存状态: {hash_id}")
        if message:
            print(f"  备注: {message}")
        
        # 触发 CI（如果存在 .shci）
        self._run_ci("push")
        
        return hash_id
    
    def _run_ci(self, event: str):
        """运行 .shci 中的脚本"""
        shci_file = self.work_dir / ".shci"
        if not shci_file.exists():
            return
        
        print(f"\n检测到 .shci 文件，正在触发 {event} 事件...")
        try:
            content = shci_file.read_text()
            lines = content.split('\n')
            execute = False
            for line in lines:
                if line.strip().startswith(f"on {event}"):
                    execute = True
                    continue
                if execute and line.strip().startswith("on "):
                    break
                if execute and line.strip() and not line.strip().startswith('#'):
                    print(f"  > {line.strip()}")
                    os.system(line.strip())
        except Exception as e:
            print(f"CI 执行失败: {e}")
    
    def history(self, limit: int = 20):
        """显示历史记录"""
        if not self.timeline:
            print("无历史记录")
            return
        
        print(f"\n项目: {self.work_dir.name}")
        print(f"最近 {min(limit, len(self.timeline))} 条记录:\n")
        print(f"{'哈希':<10} {'时间':<25} {'备注'}")
        print("-" * 60)
        
        for entry in reversed(self.timeline[-limit:]):
            time_str = entry['time'][:19]
            msg = entry['message'][:40]
            print(f"{entry['hash']:<10} {time_str:<25} {msg}")
    
    def undo(self, hash_id: str, force: bool = False) -> bool:
        """
        恢复到指定哈希状态
        Args:
            hash_id: 目标哈希值
            force: 是否强制覆盖（不检查未提交变更）
        Returns:
            是否成功
        """
        # 检查哈希是否存在
        if hash_id not in [e['hash'] for e in self.timeline]:
            print(f"错误: 未找到哈希 {hash_id}")
            return False
        
        # 检查是否有未提交变更
        if not force:
            status_code = self.status(detail=False)
            if status_code == 1:
                print("检测到未提交的变更，请使用 --force 强制覆盖")
                return False
        
        archive_path = self._get_archive_path(hash_id)
        if not archive_path.exists():
            print(f"错误: 存档文件 {archive_path} 不存在")
            return False
        
        # 记录当前状态到 redo（如果存在）
        current_hash = self._get_current_hash()
        if current_hash:
            redo_file = self.shot_dir / "redo_target"
            redo_file.write_text(current_hash)
        
        # 解压覆盖工作区
        try:
            print(f"正在恢复到 {hash_id}...")
            
            # 先清空工作目录（保留特殊文件）
            self._clear_work_dir()
            
            # 使用绝对路径
            archive_abs = archive_path.resolve()
            work_abs = self.work_dir.resolve()
            
            # 直接解压到工作目录
            unpacker = Unpacker(str(archive_abs), password="", show_progress=True)
            unpacker.unpack(str(work_abs))
            
            # 更新当前指向
            self._set_current_hash(hash_id)
            
            print(f"已恢复到 {hash_id}")
            return True
            
        except Exception as e:
            print(f"恢复失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def redo(self) -> bool:
        """
        撤销最后一次 undo（重新打包当前状态）
        Returns:
            是否成功
        """
        redo_file = self.shot_dir / "redo_target"
        if not redo_file.exists():
            print("没有可重做的操作")
            return False
        
        target_hash = redo_file.read_text().strip()
        if target_hash not in [e['hash'] for e in self.timeline]:
            print(f"错误: 目标哈希 {target_hash} 无效")
            return False
        
        # 先清空工作目录
        print("正在清空工作目录...")
        self._clear_work_dir()
        
        # 恢复到目标状态
        print(f"正在恢复到 {target_hash}...")
        success = self.undo(target_hash, force=True)
        
        if success:
            redo_file.unlink()
            print("重做完成")
            return True
        return False
    
    def open_saving_dir(self):
        """打开当前项目的存档目录（文件管理器）"""
        if not self.shot_dir.exists():
            print(f"存档目录不存在: {self.shot_dir}")
            return False
        
        print(f"正在打开存档目录: {self.shot_dir}")
        
        if sys.platform == 'win32':
            os.startfile(str(self.shot_dir))
        elif sys.platform == 'darwin':
            subprocess.run(['open', str(self.shot_dir)])
        else:
            subprocess.run(['xdg-open', str(self.shot_dir)])
        
        return True
    
    def list_projects(self):
        """列出所有项目"""
        if not self.base_dir.exists():
            print("未找到任何项目")
            return
        
        projects = []
        for item in self.base_dir.iterdir():
            if item.is_dir():
                timeline_file = item / "timeline.json"
                if timeline_file.exists():
                    try:
                        with open(timeline_file, 'r', encoding='utf-8') as f:
                            timeline = json.load(f)
                            last_time = timeline[-1]['time'] if timeline else "无记录"
                            count = len(timeline)
                        projects.append({
                            "name": item.name,
                            "count": count,
                            "last": last_time[:19] if last_time != "无记录" else "无记录"
                        })
                    except:
                        pass
        
        if not projects:
            print("未找到任何项目")
            return
        
        print(f"\n存档根目录: {self.base_dir}")
        print(f"{'项目':<50} {'存档数':<8} {'最后存档时间'}")
        print("-" * 80)
        for p in sorted(projects, key=lambda x: x['last'], reverse=True):
            print(f"{p['name']:<50} {p['count']:<8} {p['last']}")
    
    def tool(self, delete_versions: List[str] = None, 
             change_saving_path: str = None,
             init_ignore: bool = False,
             open_saving_dir: bool = False):
        """
        工具命令
        Args:
            delete_versions: 要删除的哈希列表
            change_saving_path: 更改存档根路径
            init_ignore: 初始化 .shotignore
            open_saving_dir: 打开存档目录
        """
        if open_saving_dir:
            self.open_saving_dir()
            return
        
        if change_saving_path:
            new_base = Path(change_saving_path).expanduser().resolve()
            new_base.mkdir(parents=True, exist_ok=True)
            
            old_project_dir = self.shot_dir
            new_project_dir = new_base / self.project_id
            
            if old_project_dir.exists() and old_project_dir != new_project_dir:
                print(f"移动项目存档从 {old_project_dir} 到 {new_project_dir}")
                shutil.copytree(old_project_dir, new_project_dir)
                shutil.rmtree(old_project_dir)
            
            print(f"存档根路径已更改为: {new_base}")
            print("提示: 请设置环境变量 SHOT_PATH 以持久化此设置")
            return
        
        if init_ignore:
            ignore_path = self.shot_dir / ".shotignore"
            if not ignore_path.exists():
                sample_content = """# shot 忽略文件示例（项目级）
# 每行一个模式，支持通配符 *

# 临时文件
*.tmp
*.swp
*.pyc
__pycache__/

# 依赖目录
node_modules/
.venv/
env/

# IDE 配置
.vscode/
.idea/

# 系统文件
.DS_Store
Thumbs.db

# 其他存档
*.mpc
"""
                ignore_path.write_text(sample_content)
                print(f"已创建项目忽略文件: {ignore_path}")
            else:
                print(f"项目忽略文件已存在: {ignore_path}")
            return
        
        if delete_versions:
            for hash_id in delete_versions:
                if hash_id == self._get_current_hash():
                    print(f"不能删除当前指向的版本: {hash_id}")
                    continue
                
                self.timeline = [e for e in self.timeline if e['hash'] != hash_id]
                archive_path = self._get_archive_path(hash_id)
                if archive_path.exists():
                    archive_path.unlink()
                    print(f"已删除版本: {hash_id}")
                else:
                    print(f"存档文件不存在: {hash_id}")
            
            self._save_timeline()
            print("历史记录已更新")


def main():
    parser = argparse.ArgumentParser(
        prog="shot",
        description="shot - 单人开发者的时间机器工具",
        epilog="示例:\n"
               "  shot push -m \"完成了登录功能\"\n"
               "  shot status -d\n"
               "  shot history\n"
               "  shot projects\n"
               "  shot undo a1b2c3d4\n"
               "  shot redo\n"
               "  shot tool --open-saving-dir\n"
               "  shot tool --change-saving-path D:/my_shots"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    status_parser = subparsers.add_parser("status", help="显示工作区状态")
    status_parser.add_argument("-d", "--detail", action="store_true", help="显示详细变更列表")
    
    push_parser = subparsers.add_parser("push", help="保存当前状态")
    push_parser.add_argument("-m", "--message", type=str, default="", help="备注信息")
    
    history_parser = subparsers.add_parser("history", help="显示历史记录")
    history_parser.add_argument("-n", "--limit", type=int, default=20, help="显示条数")
    
    subparsers.add_parser("projects", help="列出所有项目")
    
    undo_parser = subparsers.add_parser("undo", help="恢复到指定版本")
    undo_parser.add_argument("hash", type=str, help="目标哈希值")
    undo_parser.add_argument("-f", "--force", action="store_true", help="强制覆盖未提交变更")
    
    subparsers.add_parser("redo", help="撤销最后一次 undo")
    
    tool_parser = subparsers.add_parser("tool", help="工具集")
    tool_parser.add_argument("-dl", "--delete-history-versions", nargs="+", help="删除指定版本")
    tool_parser.add_argument("-sav", "--change-saving-path", type=str, help="更改存档根路径")
    tool_parser.add_argument("-ig", "--init-ignore", action="store_true", help="初始化项目忽略文件")
    tool_parser.add_argument("-osav", "--open-saving-dir", action="store_true", help="打开当前项目的存档目录")
    
    args = parser.parse_args()
    
    # 无命令时默认执行 push
    if not args.command:
        shot = Shot()
        shot.push()
        return
    
    # projects 命令使用列表模式
    if args.command == "projects":
        shot = Shot(list_mode=True)
        shot.list_projects()
        return
    
    shot = Shot()
    
    if args.command == "status":
        shot.status(detail=args.detail)
    elif args.command == "push":
        shot.push(message=args.message)
    elif args.command == "history":
        shot.history(limit=args.limit)
    elif args.command == "undo":
        shot.undo(args.hash, force=args.force)
    elif args.command == "redo":
        shot.redo()
    elif args.command == "tool":
        shot.tool(
            delete_versions=args.delete_history_versions,
            change_saving_path=args.change_saving_path,
            init_ignore=args.init_ignore,
            open_saving_dir=args.open_saving_dir
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()