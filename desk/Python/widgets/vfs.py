# vfs.py
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime


class VirtualNode:
    """虚拟文件系统节点基类"""
    def __init__(self, name: str, parent: Optional['VirtualFolder'] = None):
        self.name = name
        self.parent = parent
        self.created_time = datetime.now()
        self.modified_time = datetime.now()
        self.attributes: Dict[str, Any] = {}  # 扩展属性
    
    def get_path(self, separator: str = '/') -> str:
        """获取节点路径，使用自定义分隔符"""
        if self.parent is None:
            return separator  # 根目录返回分隔符
        parts = []
        current = self
        while current.parent is not None:
            parts.append(current.name)
            current = current.parent
        parts.reverse()
        return separator + separator.join(parts)
    
    def rename(self, new_name: str) -> bool:
        """重命名节点"""
        if self.parent and new_name in self.parent.children:
            return False  # 同名节点已存在
        self.name = new_name
        self.modified_time = datetime.now()
        return True


class VirtualFile(VirtualNode):
    """虚拟文件"""
    def __init__(self, name: str, parent: Optional['VirtualFolder'] = None, 
                 content: str = "", real_path: Optional[str] = None):
        super().__init__(name, parent)
        self.content = content
        self.real_path = real_path  # 如果映射到真实文件，这里存真实路径
        self.size = len(content)
    
    def read(self) -> str:
        """读取文件内容"""
        if self.real_path and os.path.exists(self.real_path):
            # 如果映射到真实文件，从真实文件读取
            with open(self.real_path, 'r', encoding='utf-8') as f:
                return f.read()
        return self.content
    
    def write(self, content: str):
        """写入文件内容"""
        self.content = content
        self.size = len(content)
        self.modified_time = datetime.now()
        
        if self.real_path:
            # 同步到真实文件
            os.makedirs(os.path.dirname(self.real_path), exist_ok=True)
            with open(self.real_path, 'w', encoding='utf-8') as f:
                f.write(content)


class VirtualFolder(VirtualNode):
    """虚拟文件夹"""
    def __init__(self, name: str, parent: Optional['VirtualFolder'] = None,
                 real_path: Optional[str] = None):
        super().__init__(name, parent)
        self.children: Dict[str, VirtualNode] = {}
        self.real_path = real_path  # 如果映射到真实文件夹
    
    def add_child(self, node: VirtualNode) -> bool:
        """添加子节点"""
        if node.name in self.children:
            return False
        node.parent = self
        self.children[node.name] = node
        self.modified_time = datetime.now()
        return True
    
    def remove_child(self, name: str) -> bool:
        """删除子节点"""
        if name not in self.children:
            return False
        del self.children[name]
        self.modified_time = datetime.now()
        return True
    
    def get_child(self, name: str) -> Optional[VirtualNode]:
        """获取子节点"""
        return self.children.get(name)
    
    def list_children(self) -> List[str]:
        """列出所有子节点名称"""
        return list(self.children.keys())
    
    def is_empty(self) -> bool:
        """判断文件夹是否为空"""
        return len(self.children) == 0


class VirtualFileSystem:
    """虚拟文件系统主类"""
    
    # 默认分隔符
    DEFAULT_SEPARATOR = '/'
    
    def __init__(self, separator: str = DEFAULT_SEPARATOR):
        self.separator = separator
        self.root = VirtualFolder("")  # 根文件夹无名
        self.current_folder = self.root
        self.mount_points: Dict[str, VirtualFolder] = {}  # 挂载点
        self.separator = separator
        
        # 初始化基本目录
        self._init_system_folders()
    
    def _init_system_folders(self):
        """初始化系统文件夹"""
        # 创建系统目录
        self.mkdir("system")
        self.mkdir("users")
        self.mkdir("apps")
        self.mkdir("devices")  # 虚拟设备
        
        # 创建当前用户目录
        self.mkdir("users/current")
        
        # 挂载真实目录示例（可选）
        # self.mount("C:", "C:\\", is_real=True)  # 挂载Windows C盘
    
    def parse_path(self, path: str) -> List[str]:
        """解析路径字符串，支持自定义分隔符"""
        if not path:
            return []
        
        # 处理根路径
        if path.startswith(self.separator):
            parts = path[len(self.separator):].split(self.separator)
        else:
            parts = path.split(self.separator)
        
        # 过滤空字符串
        return [p for p in parts if p]
    
    def navigate_to(self, path: str) -> Optional[VirtualFolder]:
        """导航到指定路径（返回文件夹）"""
        if path == "" or path == self.separator:
            return self.root
        
        parts = self.parse_path(path)
        current = self.root
        
        for part in parts:
            if part == "" or part == ".":
                continue
            elif part == "..":
                if current.parent:
                    current = current.parent
                continue
            
            node = current.get_child(part)
            if node is None:
                return None
            if not isinstance(node, VirtualFolder):
                return None  # 不是文件夹
            current = node
        
        return current
    
    def get_node(self, path: str) -> Optional[VirtualNode]:
        """获取指定路径的节点"""
        if path == "" or path == self.separator:
            return self.root
        
        parts = self.parse_path(path)
        filename = parts[-1]
        folder_path = self.separator.join(parts[:-1]) if len(parts) > 1 else ""
        
        folder = self.navigate_to(folder_path)
        if folder is None:
            return None
        
        return folder.get_child(filename)
    
    # ---------- 文件/文件夹操作 ----------
    
    def mkdir(self, path: str) -> bool:
        """创建文件夹"""
        parts = self.parse_path(path)
        foldername = parts[-1]
        parent_path = self.separator.join(parts[:-1]) if len(parts) > 1 else ""
        
        parent = self.navigate_to(parent_path)
        if parent is None:
            return False
        
        if foldername in parent.children:
            return False
        
        new_folder = VirtualFolder(foldername, parent)
        parent.add_child(new_folder)
        return True
    
    def create_file(self, path: str, content: str = "") -> bool:
        """创建文件"""
        parts = self.parse_path(path)
        filename = parts[-1]
        parent_path = self.separator.join(parts[:-1]) if len(parts) > 1 else ""
        
        parent = self.navigate_to(parent_path)
        if parent is None:
            return False
        
        if filename in parent.children:
            return False
        
        new_file = VirtualFile(filename, parent, content)
        parent.add_child(new_file)
        return True
    
    def delete(self, path: str) -> bool:
        """删除文件或文件夹"""
        node = self.get_node(path)
        if node is None or node.parent is None:
            return False
        
        return node.parent.remove_child(node.name)
    
    def list_dir(self, path: str = "") -> List[Dict[str, Any]]:
        """列出目录内容，返回带信息的列表"""
        folder = self.navigate_to(path) if path else self.current_folder
        
        if folder is None:
            return []
        
        result = []
        for name, node in folder.children.items():
            info = {
                'name': name,
                'type': 'folder' if isinstance(node, VirtualFolder) else 'file',
                'size': getattr(node, 'size', 0),
                'created': node.created_time,
                'modified': node.modified_time,
                'path': node.get_path(self.separator)
            }
            result.append(info)
        
        # 排序：文件夹在前，文件在后，按名称排序
        result.sort(key=lambda x: (x['type'] != 'folder', x['name']))
        return result
    
    # ---------- 路径转换 ----------
    
    def to_real_path(self, virtual_path: str) -> Optional[str]:
        """将虚拟路径转换为真实路径（如果映射了）"""
        node = self.get_node(virtual_path)
        if node and hasattr(node, 'real_path') and node.real_path:
            return node.real_path
        return None
    
    def mount(self, virtual_path: str, real_path: str) -> bool:
        """挂载真实目录到虚拟路径"""
        parts = self.parse_path(virtual_path)
        if not parts:
            return False
        
        foldername = parts[-1]
        parent_path = self.separator.join(parts[:-1]) if len(parts) > 1 else ""
        
        parent = self.navigate_to(parent_path)
        if parent is None:
            # 自动创建父目录
            self.mkdir(parent_path)
            parent = self.navigate_to(parent_path)
        
        if foldername in parent.children:
            return False
        
        # 创建映射到真实路径的虚拟文件夹
        mounted_folder = VirtualFolder(foldername, parent, real_path)
        parent.add_child(mounted_folder)
        self.mount_points[virtual_path] = mounted_folder
        return True
    
    # ---------- 序列化/反序列化 ----------
    
    def to_dict(self) -> Dict:
        """将虚拟文件系统导出为字典"""
        def _node_to_dict(node: VirtualNode) -> Dict:
            if isinstance(node, VirtualFile):
                return {
                    'type': 'file',
                    'name': node.name,
                    'content': node.content,
                    'real_path': node.real_path,
                    'created': node.created_time.isoformat(),
                    'modified': node.modified_time.isoformat()
                }
            else:  # VirtualFolder
                return {
                    'type': 'folder',
                    'name': node.name,
                    'real_path': node.real_path,
                    'children': {name: _node_to_dict(child) 
                               for name, child in node.children.items()},
                    'created': node.created_time.isoformat(),
                    'modified': node.modified_time.isoformat()
                }
        
        return {
            'separator': self.separator,
            'root': _node_to_dict(self.root),
            'mount_points': list(self.mount_points.keys())
        }
    
    def save(self, filepath: str):
        """保存虚拟文件系统到文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
    
    @classmethod
    def load(cls, filepath: str) -> 'VirtualFileSystem':
        """从文件加载虚拟文件系统"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        vfs = cls(separator=data.get('separator', cls.DEFAULT_SEPARATOR))
        
        def _dict_to_node(data: Dict, parent: Optional[VirtualFolder] = None) -> VirtualNode:
            if data['type'] == 'file':
                node = VirtualFile(
                    name=data['name'],
                    parent=parent,
                    content=data.get('content', ''),
                    real_path=data.get('real_path')
                )
            else:
                node = VirtualFolder(
                    name=data['name'],
                    parent=parent,
                    real_path=data.get('real_path')
                )
                for child_name, child_data in data.get('children', {}).items():
                    child = _dict_to_node(child_data, node)
                    node.children[child_name] = child
            
            # 恢复时间
            if 'created' in data:
                node.created_time = datetime.fromisoformat(data['created'])
            if 'modified' in data:
                node.modified_time = datetime.fromisoformat(data['modified'])
            
            return node
        
        vfs.root = _dict_to_node(data['root'])
        return vfs
    
    # ---------- 路径补全 ----------
    
    def complete_path(self, partial_path: str) -> List[str]:
        """路径自动补全"""
        if not partial_path:
            return self.list_dir_names()
        
        # 获取最后一部分
        parts = self.parse_path(partial_path)
        if not parts:
            return []
        
        last_part = parts[-1]
        parent_path = self.separator.join(parts[:-1]) if len(parts) > 1 else ""
        
        parent = self.navigate_to(parent_path)
        if parent is None:
            return []
        
        # 匹配以last_part开头的节点
        matches = []
        for name, node in parent.children.items():
            if name.startswith(last_part):
                full_path = parent_path + self.separator + name if parent_path else name
                if isinstance(node, VirtualFolder):
                    full_path += self.separator  # 文件夹加分隔符
                matches.append(full_path)
        
        return matches
    
    def list_dir_names(self, path: str = "") -> List[str]:
        """列出目录下的名称（只返回名字）"""
        folder = self.navigate_to(path) if path else self.current_folder
        if folder is None:
            return []
        return list(folder.children.keys())