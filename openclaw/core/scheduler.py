# core/scheduler.py
import time
import threading
from datetime import datetime, timedelta
from typing import Callable, Dict, Any
import json

class ScheduledTask:
    """单个定时任务"""
    def __init__(self, name: str, interval_minutes: int, prompt: str, tags: list = None):
        self.name = name
        self.interval = timedelta(minutes=interval_minutes)
        self.prompt = prompt
        self.tags = tags or []
        self.last_run = None
        self.enabled = True
    
    def should_run(self, now: datetime) -> bool:
        """检查现在是否该运行"""
        if not self.enabled:
            return False
        if self.last_run is None:
            return True
        return now - self.last_run >= self.interval

class Scheduler:
    def __init__(self, ai, memory=None):
        """
        Args:
            ai: 你的AI实例（必须有ask_with_tools方法）
            memory: 记忆系统（可选）
        """
        self.ai = ai
        self.memory = memory
        self.tasks: Dict[str, ScheduledTask] = {}
        self.running = False
        self.thread = None
        self.tools = []  # 会在外面设置
    
    def add_task(self, name: str, interval_minutes: int, prompt: str, tags: list = None):
        """添加一个定时任务"""
        self.tasks[name] = ScheduledTask(name, interval_minutes, prompt, tags)
        print(f"✅ 已添加定时任务: {name} (每{interval_minutes}分钟)")
    
    def remove_task(self, name: str):
        """删除任务"""
        if name in self.tasks:
            del self.tasks[name]
            print(f"🗑️ 已删除任务: {name}")
    
    def start(self):
        """启动调度器（在后台线程运行）"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        print("⏰ 调度器已启动")
    
    def stop(self):
        """停止调度器"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        print("⏹️ 调度器已停止")
    
    def _run_loop(self):
        """后台循环"""
        while self.running:
            try:
                now = datetime.now()
                
                # 检查每个任务
                for task in self.tasks.values():
                    if task.should_run(now):
                        self._execute_task(task)
                        task.last_run = now
                
                # 每分钟检查一次
                time.sleep(60)
                
            except Exception as e:
                print(f"❌ 调度器错误: {e}")
                time.sleep(60)
    
    def _execute_task(self, task: ScheduledTask):
        """执行单个任务"""
        print(f"🤖 [定时任务: {task.name}] 开始执行...")
        
        # 构造提示词（可以加上记忆）
        prompt = task.prompt
        if self.memory:
            # 搜索相关记忆
            memories = []
            for tag in task.tags:
                memories.extend(self.memory.search(tag))
            if memories:
                prompt += f"\n\n相关记忆:\n" + "\n".join(memories[:3])
        
        # 让AI思考
        result = self.ai.ask_with_tools(prompt, self.tools)
        
        # 处理结果
        if isinstance(result, list):
            print(f"🔧 [定时任务: {task.name}] 调用了 {len(result)} 个工具")
        else:
            print(f"💬 [定时任务: {task.name}] {result[:100]}...")
            
            # 存进记忆
            if self.memory and len(result) > 20:
                self.memory.save(
                    content=f"【定时任务:{task.name}】\n{result}",
                    tags=task.tags + ["auto"]
                )
    
    def list_tasks(self) -> list:
        """列出所有任务"""
        return [
            {
                "name": t.name,
                "interval": t.interval.total_seconds() / 60,
                "prompt": t.prompt,
                "last_run": t.last_run.isoformat() if t.last_run else None,
                "enabled": t.enabled
            }
            for t in self.tasks.values()
        ]

