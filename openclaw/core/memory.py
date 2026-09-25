# core/memory.py
import os
import time
from datetime import datetime

class Memory:
    def __init__(self, memory_dir="data/memories"):
        self.memory_dir = memory_dir
        os.makedirs(memory_dir, exist_ok=True)
    
    def save(self, content: str, tags: list = None):
        """存一条记忆"""
        # 用毫秒时间戳，避免重名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]  # 到毫秒
        filename = f"{self.memory_dir}/{timestamp}.md"
        
        # 如果文件已存在，加个随机数
        counter = 1
        while os.path.exists(filename):
            filename = f"{self.memory_dir}/{timestamp}_{counter}.md"
            counter += 1
        
        with open(filename, 'w', encoding='utf-8') as f:
            if tags:
                f.write(f"tags: {','.join(tags)}\n")
            f.write("---\n")
            f.write(content)
        
        print(f"💾 记忆已保存: {filename}")
        return filename
    
    def search(self, keyword: str) -> list:
        """搜索记忆"""
        results = []
        for f in os.listdir(self.memory_dir):
            if f.endswith('.md'):
                filepath = os.path.join(self.memory_dir, f)
                with open(filepath, 'r', encoding='utf-8') as file:
                    content = file.read()
                    if keyword in content:
                        # 去掉文件头，只保留内容
                        if '---\n' in content:
                            content = content.split('---\n', 1)[-1]
                        results.append(content)
        return results
    
    def list_all(self) -> list:
        """列出所有记忆"""
        files = sorted(os.listdir(self.memory_dir), reverse=True)
        return [f for f in files if f.endswith('.md')]