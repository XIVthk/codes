import os
import re

class VFS:
    def __init__(self, fs_dict, initial_cwd="/"):
        self.root = fs_dict.get("/", {})
        self.cwd = initial_cwd
        self.current_node = self._get_node(initial_cwd)
        self.path_stack = ["/"]
        self._metadata = {}
        self._pending_encrypted_path = None  # 用于触发密码弹窗
    
    def set_metadata(self, path, metadata):
        """设置目录的元数据"""
        self._metadata[path] = metadata
    
    def get_metadata(self, path):
        """获取目录的元数据"""
        return self._metadata.get(path)
    
    def is_encrypted(self, path):
        """检查目录是否加密"""
        meta = self._metadata.get(path)
        return meta and meta.get("status") == "enc"
    
    def unlock_directory(self, path, password):
        """尝试解锁目录"""
        meta = self._metadata.get(path)
        if meta and meta.get("password") == password:
            meta["status"] = "unlocked"
            if "callback" in meta:
                meta["callback"]()
            return True
        return False
    
    def is_unlocked(self, path):
        """检查目录是否已解锁"""
        meta = self._metadata.get(path)
        return meta and meta.get("status") == "unlocked"
    
    def resolve_path(self, path):
        """解析路径，返回 (node, name, full_path)"""
        if not path:
            path = "."
        
        if path.startswith("/"):
            parts = path.split("/")
            parts = [p for p in parts if p]
            node = self.root
            full_path = "/"
        else:
            parts = path.split("/")
            parts = [p for p in parts if p]
            node = self.current_node
            full_path = self.cwd
        
        for i, part in enumerate(parts):
            if part == ".":
                continue
            elif part == "..":
                if full_path != "/":
                    full_path = os.path.dirname(full_path)
                    if full_path == "":
                        full_path = "/"
                    node = self._get_node(full_path)
                continue
            else:
                if isinstance(node, dict) and part in node:
                    full_path = os.path.join(full_path, part).replace("\\", "/")
                    node = node[part]
                else:
                    return None, None, None
        
        name = parts[-1] if parts else ""
        return node, name, full_path
    
    def _get_node(self, path):
        """根据路径获取节点"""
        if path == "/":
            return self.root
        node, _, _ = self.resolve_path(path)
        return node
    
    def ls(self, path=None):
        """列出目录内容"""
        if path is None:
            path = "."
        
        node, name, full_path = self.resolve_path(path)
        if node is None:
            return f"ls: 无法访问 '{path}': 没有那个文件或目录"
        
        if not isinstance(node, dict):
            return f"ls: '{path}' 不是目录"
        
        # ★ 检查是否加密且未解锁
        if self.is_encrypted(full_path) and not self.is_unlocked(full_path):
            return f"__ENCRYPTED__:{full_path}:ls"
        
        items = []
        items.append((".", True, 0, None))
        items.append(("..", True, 0, None))
        
        for key, value in node.items():
            if key == "__metadata__":
                continue
            if isinstance(value, dict) and "content" not in value and "function" not in value:
                # 检查子目录是否加密
                sub_path = os.path.join(full_path, key).replace("\\", "/")
                if self.is_encrypted(sub_path) and not self.is_unlocked(sub_path):
                    items.append((key, True, 0, None))
                else:
                    items.append((key, True, 0, None))
            else:
                size = 0
                timestamp = None
                if isinstance(value, dict):
                    timestamp = value.get("timestamp")
                    if "content" in value:
                        content = value["content"]
                        if isinstance(content, str):
                            size = len(content.encode('utf-8'))
                        elif isinstance(content, bytes):
                            size = len(content)
                items.append((key, False, size, timestamp))
        
        lines = []
        lines.append(" 日期         时间     类型      大小     名称")
        lines.append(" ──────────  ─────  ────────  ────────  ─────────────")
        
        for name, is_dir, size, timestamp in items:
            if timestamp:
                if isinstance(timestamp, str):
                    parts = timestamp.split()
                    if len(parts) >= 2:
                        date_str = parts[0]
                        time_str = parts[1][:5]
                    else:
                        date_str = timestamp[:10]
                        time_str = timestamp[11:16] if len(timestamp) >= 16 else "     "
                else:
                    date_str = timestamp.strftime("%Y-%m-%d")
                    time_str = timestamp.strftime("%H:%M")
            else:
                date_str = " " * 10
                time_str = " " * 5
            
            type_str = "<DIR>" if is_dir else "<FILE>"
            size_str = " " * 8 if is_dir else f"{size:>8}"
            lines.append(f"{date_str}  {time_str}    {type_str}    {size_str}    {name}")
        
        return "\n".join(lines)
    
    def cd(self, path):
        """切换目录"""
        if not path:
            return "cd: 需要指定路径"
        
        node, name, full_path = self.resolve_path(path)
        if node is None:
            return f"cd: 无法访问 '{path}': 没有那个文件或目录"
        
        if not isinstance(node, dict):
            return f"cd: '{path}' 不是目录"
        
        # ★ 检查是否加密且未解锁
        if self.is_encrypted(full_path) and not self.is_unlocked(full_path):
            return f"__ENCRYPTED__:{full_path}:cd"
        
        self.cwd = full_path
        self.current_node = node
        return f"CD: {full_path}"
    
    def open(self, path, flags=None):
        """打开文件"""
        if not path:
            return "open: 需要指定文件路径"
        
        node, name, full_path = self.resolve_path(path)
        if node is None:
            return f"open: 无法访问 '{path}': 没有那个文件或目录"
        
        # 检查父目录是否加密
        parent_path = os.path.dirname(full_path)
        if parent_path == "":
            parent_path = "/"
        if self.is_encrypted(parent_path) and not self.is_unlocked(parent_path):
            return f"__ENCRYPTED__:{parent_path}:open"
        
        if not isinstance(node, dict):
            return f"open: '{path}' 不是文件"
        
        if "content" in node:
            content = node["content"]
            lines = []
            lines.append(f"  <color=grey>[{name}]</color>")
            if isinstance(content, bytes):
                hex_str = " ".join(f"{b:02x}" for b in content[:16])
                if len(content) > 16:
                    hex_str += "..."
                lines.append(f"  {hex_str}")
            else:
                for line in content.splitlines():
                    lines.append(f"  {line}")
            lines.append(f"  <color=grey>(EOF)</color>")
            return "\n".join(lines)
        elif "function" in node:
            return f"open: '{path}' 是可执行文件，请使用 execute 命令运行"
        else:
            return f"open: '{path}' 是一个目录"
    
    def execute(self, path, args=None, flags=None):
        """执行可执行文件"""
        if not path:
            return "execute: 需要指定文件路径"
        
        node, name, full_path = self.resolve_path(path)
        if node is None:
            return f"execute: 无法访问 '{path}': 没有那个文件或目录"
        
        if not isinstance(node, dict):
            return f"execute: '{path}' 不是可执行文件"
        
        # 检查父目录是否加密
        parent_path = os.path.dirname(full_path)
        if parent_path == "":
            parent_path = "/"
        if self.is_encrypted(parent_path) and not self.is_unlocked(parent_path):
            return f"__ENCRYPTED__:{parent_path}:execute"
        
        if "function" in node:
            try:
                result = node["function"](args or [], flags or [])
                if result:
                    lines = []
                    lines.append(f"  <color=blue>[stdout: {name}]</color>")
                    for line in result.splitlines():
                        lines.append(f"  {line}")
                    lines.append(f"  <color=blue>(EOS)</color>")
                    return "\n".join(lines)
                else:
                    return f"execute: 已成功执行 {name}。"
            except Exception as e:
                return f"execute: 执行失败 - {str(e)}"
        else:
            return f"execute: '{path}' 不是可执行文件"
    
    def play(self, path, flags=None):
        """播放音频文件"""
        if not path:
            return "play: 需要指定文件路径"
        
        node, name, full_path = self.resolve_path(path)
        if node is None:
            return f"play: 无法访问 '{path}': 没有那个文件或目录"
        
        if not isinstance(node, dict):
            return f"play: '{path}' 不是音频文件"
        
        if "content" in node:
            return f"正在播放 {path} ..."
        else:
            return f"play: '{path}' 不是音频文件"
    
    def pwd(self):
        """显示当前路径"""
        return self.cwd