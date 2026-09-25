from AI import AI
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import markdown
import html
from datetime import datetime
import re
import threading
import json
import os
import requests
import json

class StreamingAI:
    """支持流式输出的AI类"""
    def __init__(self, system_prompt: str, api_key: str, base_url: str,
                 model: str = "deepseek-ai/DeepSeek-V3",
                 max_tokens: int = 1024, temperature: float = 0.7):
        self.system_prompt = system_prompt
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.history = [{"role": "system", "content": self.system_prompt}]
    
    def ask_stream(self, question: str, callback=None):
        """流式提问，通过回调函数返回每个token"""
        # 添加用户消息到历史
        self.history.append({"role": "user", "content": question})
        
        # 准备请求数据
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model,
            "messages": self.history,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream": True  # 启用流式输出
        }
        
        try:
            full_response = ""
            response = requests.post(url, headers=headers, json=data, stream=True)
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data_str = line[6:]  # 去掉'data: '前缀
                        if data_str == '[DONE]':
                            break
                        
                        try:
                            data_obj = json.loads(data_str)
                            if 'choices' in data_obj and len(data_obj['choices']) > 0:
                                delta = data_obj['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    token = delta['content']
                                    full_response += token
                                    if callback:
                                        callback(token, full_response)
                        except json.JSONDecodeError:
                            continue
            
            # 将完整回复添加到历史
            self.history.append({"role": "assistant", "content": full_response})
            return full_response
            
        except Exception as e:
            error_msg = f"请求出错: {str(e)}"
            if callback:
                callback(error_msg, error_msg)
            return error_msg
    
    def revert(self, rounds: int = 1):
        """回退指定轮数的对话"""
        if rounds <= 0 or len(self.history) <= 1:
            return
        
        # 计算要保留的消息数量（每轮对话包含user+assistant两条消息）
        keep_count = max(1, len(self.history) - rounds * 2)
        self.history = self.history[:keep_count]
    
    def clear_history(self):
        """清空历史"""
        self.history = [{"role": "system", "content": self.system_prompt}]
    
    def update_system_prompt(self, new_prompt):
        """更新系统提示"""
        self.system_prompt = new_prompt
        if self.history and self.history[0]["role"] == "system":
            self.history[0]["content"] = new_prompt
        else:
            self.history.insert(0, {"role": "system", "content": new_prompt})

class ChatManager:
    """聊天管理器，负责多个聊天的创建、保存和加载"""
    def __init__(self, data_dir="chats"):
        self.data_dir = data_dir
        self.chats = {}
        self.current_chat_id = None
        
        # 确保数据目录存在
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
    
    def create_chat(self, chat_id=None, system_prompt="你是一个智能助手"):
        """创建新聊天"""
        if chat_id is None:
            chat_id = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.chats[chat_id] = {
            "id": chat_id,
            "system_prompt": system_prompt,
            "created_at": datetime.now().isoformat(),
            "messages": [],
            "title": "新对话"
        }
        self.current_chat_id = chat_id
        return chat_id
    
    def save_chat(self, chat_id=None):
        """保存聊天到文件"""
        if chat_id is None:
            chat_id = self.current_chat_id
        
        if chat_id in self.chats:
            file_path = os.path.join(self.data_dir, f"{chat_id}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.chats[chat_id], f, ensure_ascii=False, indent=2)
    
    def load_chat(self, chat_id):
        """从文件加载聊天"""
        file_path = os.path.join(self.data_dir, f"{chat_id}.json")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                self.chats[chat_id] = json.load(f)
            self.current_chat_id = chat_id
            return self.chats[chat_id]
        return None
    
    def list_chats(self):
        """列出所有保存的聊天"""
        chats = []
        for filename in os.listdir(self.data_dir):
            if filename.endswith('.json'):
                chat_id = filename[:-5]  # 去掉.json后缀
                file_path = os.path.join(self.data_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        chat_data = json.load(f)
                        chats.append(chat_data)
                except:
                    continue
        # 按创建时间排序
        chats.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return chats
    
    def delete_chat(self, chat_id):
        """删除聊天"""
        if chat_id in self.chats:
            del self.chats[chat_id]
        
        file_path = os.path.join(self.data_dir, f"{chat_id}.json")
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False

class AItk:
    def __init__(self, system_prompt: str, api_key: str, base_url: str,
                 model: str = "deepseek-ai/DeepSeek-V3",
                 max_tokens: int = 1024, temperature: float = 0.7):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        # 初始化聊天管理器
        self.chat_manager = ChatManager()
        
        # 创建主窗口
        self.root = tk.Tk()
        self.root.title("AI 智能助手")
        self.root.geometry("1200x800")
        self.root.configure(bg="#0d1117")
        
        # 设置样式
        self.setup_styles()
        
        # 创建界面
        self.create_widgets()
        
        # 绑定事件
        self.bind_events()
        
        # 状态变量
        self.is_thinking = False
        self.editing_message_id = None
        self.selected_ai_message_id = None
        self.is_fullscreen = False
        self.current_streaming_message = None  # 当前正在流式输出的消息
        
        # 创建初始聊天
        self.create_new_chat(system_prompt)
        
        # 加载历史聊天
        self.load_chat_list()
        
        self.root.mainloop()
    
    def setup_styles(self):
        """设置界面样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 配置颜色 - 使用更现代化的配色
        self.colors = {
            "bg": "#0d1117",
            "bg_secondary": "#161b22",
            "bg_tertiary": "#21262d",
            "text_primary": "#f0f6fc",
            "text_secondary": "#8b949e",
            "accent": "#1f6feb",
            "accent_hover": "#388bfd",
            "user_msg_bg": "#1f6feb",
            "ai_msg_bg": "#21262d",
            "border": "#30363d",
            "success": "#3fb950",
            "warning": "#f85149",
            "user_markdown": "#a5d6ff",
            "typing_indicator": "#3fb950",
            "sidebar_bg": "#161b22",
            "input_bg": "#0d1117"
        }
        
        # 配置ttk样式
        style.configure("TFrame", background=self.colors["bg"])
        style.configure("TButton", 
                       background=self.colors["accent"],
                       foreground=self.colors["text_primary"],
                       borderwidth=0,
                       focuscolor="none",
                       font=("Segoe UI", 10))
        style.map("TButton",
                 background=[("active", self.colors["accent_hover"]),
                           ("pressed", self.colors["accent_hover"])])
        
        style.configure("TScrollbar",
                       background=self.colors["bg_tertiary"],
                       troughcolor=self.colors["bg_secondary"],
                       borderwidth=0,
                       arrowcolor=self.colors["text_primary"])
        
        style.configure("Treeview",
                       background=self.colors["bg_secondary"],
                       foreground=self.colors["text_primary"],
                       fieldbackground=self.colors["bg_secondary"],
                       borderwidth=0)
        style.map("Treeview", background=[('selected', self.colors["accent"])])
    
    def create_widgets(self):
        """创建界面组件"""
        # 主容器 - 分割为左侧聊天列表和右侧聊天区域
        main_frame = tk.Frame(self.root, bg=self.colors["bg"])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # 左侧聊天列表框架
        left_frame = tk.Frame(main_frame, bg=self.colors["sidebar_bg"], width=280)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=0, pady=0)
        left_frame.pack_propagate(False)  # 防止框架收缩
        
        # 聊天列表标题
        chat_list_title = tk.Label(left_frame, 
                                  text="对话记录",
                                  font=("Segoe UI", 14, "bold"),
                                  fg=self.colors["text_primary"],
                                  bg=self.colors["sidebar_bg"],
                                  pady=20)
        chat_list_title.pack(fill=tk.X)
        
        # 新聊天按钮
        new_chat_btn = ttk.Button(left_frame, 
                                 text="+ 新建对话",
                                 command=self.create_new_chat_dialog)
        new_chat_btn.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        # 聊天列表容器
        chat_list_container = tk.Frame(left_frame, bg=self.colors["sidebar_bg"])
        chat_list_container.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # 聊天列表 - 使用Frame包装Listbox以实现更好的滚动
        self.chat_list_frame = tk.Frame(chat_list_container, bg=self.colors["sidebar_bg"])
        self.chat_list_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        self.chat_listbox = tk.Listbox(self.chat_list_frame,
                                      bg=self.colors["sidebar_bg"],
                                      fg=self.colors["text_primary"],
                                      selectbackground=self.colors["accent"],
                                      selectforeground=self.colors["text_primary"],
                                      font=("Segoe UI", 11),
                                      borderwidth=0,
                                      highlightthickness=0,
                                      activestyle="none")
        self.chat_listbox.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # 右侧聊天区域
        right_frame = tk.Frame(main_frame, bg=self.colors["bg"])
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 标题栏
        title_frame = tk.Frame(right_frame, bg=self.colors["bg"])
        title_frame.pack(fill=tk.X, pady=0)
        
        self.chat_title = tk.StringVar(value="新对话")
        title_label = tk.Label(title_frame, 
                              textvariable=self.chat_title,
                              font=("Segoe UI", 16, "bold"),
                              fg=self.colors["text_primary"],
                              bg=self.colors["bg"],
                              pady=20)
        title_label.pack(side=tk.LEFT, padx=30)
        
        # 状态指示器和操作按钮
        control_frame = tk.Frame(title_frame, bg=self.colors["bg"])
        control_frame.pack(side=tk.RIGHT, padx=30)
        
        self.status_var = tk.StringVar(value="✓ 就绪")
        status_label = tk.Label(control_frame,
                               textvariable=self.status_var,
                               font=("Segoe UI", 10),
                               fg=self.colors["success"],
                               bg=self.colors["bg"])
        status_label.pack(side=tk.LEFT, padx=(0, 15))
        
        # 修改系统提示按钮
        edit_system_btn = ttk.Button(control_frame,
                                    text="修改系统提示",
                                    command=self.edit_system_prompt)
        edit_system_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 删除当前聊天按钮
        delete_chat_btn = ttk.Button(control_frame,
                                    text="删除对话",
                                    command=self.delete_current_chat)
        delete_chat_btn.pack(side=tk.LEFT)
        
        # 聊天区域
        chat_frame = tk.Frame(right_frame, bg=self.colors["bg"])
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=(0, 20))
        
        # 创建聊天显示区域 - 使用Canvas实现滚动
        self.chat_canvas = tk.Canvas(chat_frame, 
                                    bg=self.colors["bg"],
                                    highlightthickness=0,
                                    relief='flat')
        
        # 创建消息容器
        self.messages_frame = tk.Frame(self.chat_canvas, bg=self.colors["bg"])
        self.messages_window = self.chat_canvas.create_window(
            (0, 0), window=self.messages_frame, anchor="nw", width=self.chat_canvas.winfo_reqwidth()
        )
        
        # 配置Canvas滚动
        self.chat_canvas.pack(fill=tk.BOTH, expand=True)
        
        # 绑定画布大小变化
        self.messages_frame.bind("<Configure>", self.on_frame_configure)
        self.chat_canvas.bind("<Configure>", self.on_canvas_configure)
        
        # 输入区域
        input_frame = tk.Frame(right_frame, bg=self.colors["input_bg"])
        input_frame.pack(fill=tk.X, padx=30, pady=(0, 30))
        
        # 输入框
        self.input_text = tk.Text(input_frame,
                                 height=4,
                                 bg=self.colors["bg_tertiary"],
                                 fg=self.colors["text_primary"],
                                 insertbackground=self.colors["text_primary"],
                                 selectbackground=self.colors["accent"],
                                 relief="flat",
                                 borderwidth=1,
                                 font=("Segoe UI", 12),
                                 wrap=tk.WORD)
        self.input_text.pack(fill=tk.X, side=tk.LEFT, expand=True, padx=(0, 10))
        
        # 发送按钮
        self.send_button = ttk.Button(input_frame,
                                     text="发送",
                                     command=self.send_message,
                                     state="normal")
        self.send_button.pack(side=tk.RIGHT)
    
    def bind_events(self):
        """绑定事件"""
        # 回车发送（Ctrl+Enter换行）
        self.input_text.bind("<Return>", self.on_enter_pressed)
        self.input_text.bind("<Control-Return>", self.on_ctrl_enter_pressed)
        
        # 绑定鼠标滚轮到Canvas
        self.chat_canvas.bind("<MouseWheel>", self.on_mousewheel)
        
        # 绑定全屏切换
        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("<Escape>", self.exit_fullscreen)
        
        # 绑定聊天列表选择事件
        self.chat_listbox.bind("<<ListboxSelect>>", self.on_chat_selected)
        
        # 绑定聊天列表右键菜单
        self.chat_listbox.bind("<Button-3>", self.show_chat_list_context_menu)
    
    def toggle_fullscreen(self, event=None):
        """切换全屏状态"""
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes("-fullscreen", self.is_fullscreen)
        return "break"
    
    def exit_fullscreen(self, event=None):
        """退出全屏"""
        self.is_fullscreen = False
        self.root.attributes("-fullscreen", False)
        return "break"
    
    def on_enter_pressed(self, event):
        """回车键处理"""
        if not event.state & 0x4:  # 没有按Ctrl
            self.send_message()
            return "break"  # 阻止默认行为
        return None
    
    def on_ctrl_enter_pressed(self, event):
        """Ctrl+回车键处理 - 插入换行"""
        self.input_text.insert(tk.INSERT, "\n")
        return "break"
    
    def on_mousewheel(self, event):
        """鼠标滚轮滚动聊天区域"""
        # 使用Canvas的滚动方法
        self.chat_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def on_frame_configure(self, event):
        """更新画布的滚动区域"""
        self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all"))
    
    def on_canvas_configure(self, event):
        """画布大小变化时调整内部框架宽度"""
        self.chat_canvas.itemconfig(self.messages_window, width=event.width)
    
    def on_chat_selected(self, event):
        """聊天列表选择事件"""
        selection = self.chat_listbox.curselection()
        if selection:
            index = selection[0]
            chat_id = self.chat_listbox.get(index).split("|")[0].strip()
            self.load_chat(chat_id)
    
    def show_chat_list_context_menu(self, event):
        """显示聊天列表右键菜单"""
        # 获取点击的聊天项
        index = self.chat_listbox.nearest(event.y)
        if index >= 0:
            self.chat_listbox.selection_clear(0, tk.END)
            self.chat_listbox.selection_set(index)
            
            chat_id = self.chat_listbox.get(index).split("|")[0].strip()
            
            context_menu = tk.Menu(self.root, tearoff=0, 
                                 bg=self.colors["bg_tertiary"], 
                                 fg=self.colors["text_primary"],
                                 bd=0)
            
            context_menu.add_command(label="删除对话", 
                                   command=lambda: self.delete_chat(chat_id))
            context_menu.add_command(label="重命名", 
                                   command=lambda: self.rename_chat(chat_id))
            
            try:
                context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                context_menu.grab_release()
    
    def create_new_chat_dialog(self):
        """创建新聊天对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("新聊天")
        dialog.geometry("500x300")
        dialog.configure(bg=self.colors["bg"])
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 系统提示输入
        tk.Label(dialog, text="系统提示:", bg=self.colors["bg"], fg=self.colors["text_primary"], 
                font=("Segoe UI", 12)).pack(pady=(30, 10))
        
        prompt_var = tk.StringVar(value="你是一个智能助手")
        prompt_entry = tk.Text(dialog,
                              height=8,
                              bg=self.colors["bg_tertiary"],
                              fg=self.colors["text_primary"],
                              font=("Segoe UI", 11),
                              wrap=tk.WORD,
                              padx=10,
                              pady=10)
        prompt_entry.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)
        prompt_entry.insert("1.0", "你是一个智能助手")
        
        def create_chat():
            system_prompt = prompt_entry.get("1.0", tk.END).strip()
            if not system_prompt:
                system_prompt = "你是一个智能助手"
            self.create_new_chat(system_prompt)
            dialog.destroy()
        
        def cancel():
            dialog.destroy()
        
        # 按钮框架
        button_frame = tk.Frame(dialog, bg=self.colors["bg"])
        button_frame.pack(fill=tk.X, padx=30, pady=20)
        
        ttk.Button(button_frame, text="创建", command=create_chat).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(button_frame, text="取消", command=cancel).pack(side=tk.RIGHT)
        
        dialog.protocol("WM_DELETE_WINDOW", cancel)
    
    def edit_system_prompt(self):
        """编辑系统提示"""
        if not self.chat_manager.current_chat_id:
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("修改系统提示")
        dialog.geometry("500x300")
        dialog.configure(bg=self.colors["bg"])
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 系统提示输入
        tk.Label(dialog, text="系统提示:", bg=self.colors["bg"], fg=self.colors["text_primary"], 
                font=("Segoe UI", 12)).pack(pady=(30, 10))
        
        prompt_entry = tk.Text(dialog,
                              height=8,
                              bg=self.colors["bg_tertiary"],
                              fg=self.colors["text_primary"],
                              font=("Segoe UI", 11),
                              wrap=tk.WORD,
                              padx=10,
                              pady=10)
        prompt_entry.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)
        prompt_entry.insert("1.0", self.ai.system_prompt)
        
        def save_prompt():
            new_prompt = prompt_entry.get("1.0", tk.END).strip()
            if new_prompt and new_prompt != self.ai.system_prompt:
                self.ai.update_system_prompt(new_prompt)
                self.chat_manager.chats[self.chat_manager.current_chat_id]["system_prompt"] = new_prompt
                self.chat_manager.save_chat()
                messagebox.showinfo("成功", "系统提示已更新")
            dialog.destroy()
        
        def cancel():
            dialog.destroy()
        
        # 按钮框架
        button_frame = tk.Frame(dialog, bg=self.colors["bg"])
        button_frame.pack(fill=tk.X, padx=30, pady=20)
        
        ttk.Button(button_frame, text="保存", command=save_prompt).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(button_frame, text="取消", command=cancel).pack(side=tk.RIGHT)
        
        dialog.protocol("WM_DELETE_WINDOW", cancel)
    
    def delete_current_chat(self):
        """删除当前聊天"""
        if not self.chat_manager.current_chat_id:
            return
        
        chat_id = self.chat_manager.current_chat_id
        chat_title = self.chat_title.get()
        
        if messagebox.askyesno("确认删除", f"确定要删除对话 '{chat_title}' 吗？"):
            # 删除聊天
            success = self.chat_manager.delete_chat(chat_id)
            
            if success:
                # 创建新聊天
                self.create_new_chat()
                # 更新聊天列表
                self.load_chat_list()
                messagebox.showinfo("成功", "对话已删除")
            else:
                messagebox.showerror("错误", "删除对话失败")
    
    def delete_chat(self, chat_id):
        """删除指定聊天"""
        chat_data = None
        for chat in self.chat_manager.list_chats():
            if chat["id"] == chat_id:
                chat_data = chat
                break
        
        if not chat_data:
            # 检查内存中的聊天
            if chat_id in self.chat_manager.chats:
                chat_data = self.chat_manager.chats[chat_id]
        
        if chat_data:
            chat_title = chat_data.get("title", "对话")
            
            if messagebox.askyesno("确认删除", f"确定要删除对话 '{chat_title}' 吗？"):
                # 删除聊天
                success = self.chat_manager.delete_chat(chat_id)
                
                if success:
                    # 如果删除的是当前聊天，创建新聊天
                    if chat_id == self.chat_manager.current_chat_id:
                        self.create_new_chat()
                    # 更新聊天列表
                    self.load_chat_list()
                    messagebox.showinfo("成功", "对话已删除")
                else:
                    messagebox.showerror("错误", "删除对话失败")
    
    def rename_chat(self, chat_id):
        """重命名聊天"""
        chat_data = None
        for chat in self.chat_manager.list_chats():
            if chat["id"] == chat_id:
                chat_data = chat
                break
        
        if not chat_data:
            # 检查内存中的聊天
            if chat_id in self.chat_manager.chats:
                chat_data = self.chat_manager.chats[chat_id]
        
        if chat_data:
            current_title = chat_data.get("title", "对话")
            
            dialog = tk.Toplevel(self.root)
            dialog.title("重命名对话")
            dialog.geometry("400x150")
            dialog.configure(bg=self.colors["bg"])
            dialog.transient(self.root)
            dialog.grab_set()
            
            tk.Label(dialog, text="新标题:", bg=self.colors["bg"], fg=self.colors["text_primary"], 
                    font=("Segoe UI", 11)).pack(pady=(20, 10))
            
            title_var = tk.StringVar(value=current_title)
            title_entry = tk.Entry(dialog, textvariable=title_var, 
                                 bg=self.colors["bg_tertiary"], fg=self.colors["text_primary"],
                                 font=("Segoe UI", 11), width=40)
            title_entry.pack(pady=10, padx=30)
            title_entry.select_range(0, tk.END)
            title_entry.focus()
            
            def save_title():
                new_title = title_var.get().strip()
                if new_title and new_title != current_title:
                    chat_data["title"] = new_title
                    self.chat_manager.save_chat(chat_id)
                    
                    # 更新界面
                    if chat_id == self.chat_manager.current_chat_id:
                        self.chat_title.set(new_title)
                    
                    # 更新聊天列表
                    self.load_chat_list()
                    messagebox.showinfo("成功", "对话标题已更新")
                dialog.destroy()
            
            def cancel():
                dialog.destroy()
            
            # 按钮框架
            button_frame = tk.Frame(dialog, bg=self.colors["bg"])
            button_frame.pack(fill=tk.X, padx=30, pady=20)
            
            ttk.Button(button_frame, text="保存", command=save_title).pack(side=tk.RIGHT, padx=(10, 0))
            ttk.Button(button_frame, text="取消", command=cancel).pack(side=tk.RIGHT)
            
            dialog.protocol("WM_DELETE_WINDOW", cancel)
            title_entry.bind("<Return>", lambda e: save_title())
    
    def create_new_chat(self, system_prompt="你是一个智能助手"):
        """创建新聊天"""
        # 保存当前聊天
        if self.chat_manager.current_chat_id:
            self.save_current_chat()
        
        # 创建新聊天
        chat_id = self.chat_manager.create_chat(system_prompt=system_prompt)
        
        # 初始化AI - 使用支持流式的AI类
        self.ai = StreamingAI(system_prompt, self.api_key, self.base_url, 
                             self.model, self.max_tokens, self.temperature)
        
        # 更新界面
        self.clear_messages()
        self.chat_title.set("新对话")
        self.add_message("assistant", self.get_welcome_message(system_prompt), is_welcome=True)
        
        # 更新聊天列表
        self.load_chat_list()
        
        return chat_id
    
    def load_chat(self, chat_id):
        """加载聊天"""
        # 保存当前聊天
        if self.chat_manager.current_chat_id:
            self.save_current_chat()
        
        # 加载聊天数据
        chat_data = self.chat_manager.load_chat(chat_id)
        if chat_data:
            # 初始化AI - 使用支持流式的AI类
            self.ai = StreamingAI(chat_data["system_prompt"], self.api_key, self.base_url,
                                 self.model, self.max_tokens, self.temperature)
            
            # 恢复消息历史
            self.ai.history = chat_data["messages"]
            
            # 更新界面
            self.clear_messages()
            self.chat_title.set(chat_data.get("title", "对话"))
            
            # 重新渲染所有消息
            for i, msg in enumerate(self.ai.history):
                if msg["role"] == "system":
                    continue
                self.add_message(msg["role"], msg["content"], i)
    
    def save_current_chat(self):
        """保存当前聊天"""
        if self.chat_manager.current_chat_id:
            # 更新聊天数据
            self.chat_manager.chats[self.chat_manager.current_chat_id]["messages"] = self.ai.history
            
            # 设置标题（使用第一条用户消息或默认标题）
            if len(self.ai.history) > 1:
                for msg in self.ai.history:
                    if msg["role"] == "user":
                        # 截取前20个字符作为标题
                        title = msg["content"][:20] + "..." if len(msg["content"]) > 20 else msg["content"]
                        self.chat_manager.chats[self.chat_manager.current_chat_id]["title"] = title
                        self.chat_title.set(title)
                        break
            
            # 保存到文件
            self.chat_manager.save_chat()
    
    def load_chat_list(self):
        """加载聊天列表"""
        self.chat_listbox.delete(0, tk.END)
        
        # 添加内存中的聊天
        for chat_id, chat_data in self.chat_manager.chats.items():
            title = chat_data.get("title", "对话")
            self.chat_listbox.insert(tk.END, f"{chat_id} | {title}")
        
        # 添加文件中的聊天
        saved_chats = self.chat_manager.list_chats()
        for chat_data in saved_chats:
            chat_id = chat_data["id"]
            if chat_id not in self.chat_manager.chats:
                title = chat_data.get("title", "对话")
                self.chat_listbox.insert(tk.END, f"{chat_id} | {title}")
    
    def get_welcome_message(self, system_prompt):
        """获取欢迎消息"""
        return f"""# 欢迎使用 AI 智能助手

**系统提示**: {system_prompt}

## 功能说明:
- 💬 与AI进行对话交流
- 🔄 右键AI消息可重新生成
- ✏️ 右键用户消息可修改
- 📝 支持Markdown格式
- ⚡ 流式输出，实时显示AI回复
- 💾 自动保存聊天记录
- 🖥️ F11全屏，Esc退出全屏

开始您的对话吧！"""
    
    def add_message(self, role, content, message_id=None, is_welcome=False, is_streaming=False):
        """添加消息到聊天区域"""
        message_frame = tk.Frame(self.messages_frame, bg=self.colors["bg"])
        message_frame.pack(fill=tk.X, padx=0, pady=8)
        
        # 消息内容框架
        content_frame = tk.Frame(message_frame, bg=self.colors["bg"])
        
        if role == "user":
            # 用户消息 - 靠右显示
            message_frame.pack_configure(anchor="e")
            content_frame.pack(side=tk.RIGHT, padx=(100, 0))
            
            bg_color = self.colors["user_msg_bg"]
            text_color = self.colors["text_primary"]
            markdown_color = self.colors["user_markdown"]  # 用户消息的Markdown颜色
            
        else:
            # AI消息 - 靠左显示
            message_frame.pack_configure(anchor="w")
            content_frame.pack(side=tk.LEFT, padx=(0, 100))
            
            bg_color = self.colors["ai_msg_bg"] if not is_welcome else self.colors["bg_tertiary"]
            text_color = self.colors["text_primary"]
            markdown_color = self.colors["text_primary"]  # AI消息使用默认颜色
        
        # 计算消息框的高度 - 恢复上一版的逻辑
        lines = content.count('\n') + 1
        # 添加额外行数来适应Markdown格式
        lines += content.count('```') * 2  # 代码块会增加高度
        lines = max(1, min(lines, 50))  # 限制在1-50行之间
        
        # 创建消息文本区域
        msg_text = tk.Text(content_frame,
                         wrap=tk.WORD,
                         width=80,
                         height=lines,  # 根据内容设置高度
                         bg=bg_color,
                         fg=text_color,
                         font=("Segoe UI", 11),
                         relief="flat",
                         borderwidth=0,
                         padx=16,
                         pady=12,
                         selectbackground=self.colors["accent"],
                         highlightthickness=0)
        msg_text.pack(fill=tk.BOTH, expand=True)
        
        # 如果是流式输出，添加打字指示器
        if is_streaming:
            typing_indicator = tk.Label(content_frame, 
                                       text="●", 
                                       font=("Segoe UI", 12),
                                       fg=self.colors["typing_indicator"],
                                       bg=bg_color)
            typing_indicator.pack(side=tk.BOTTOM, anchor=tk.W)
            message_frame.typing_indicator = typing_indicator
        
        # 处理Markdown并插入文本
        if is_streaming:
            # 对于流式消息，先插入初始文本
            msg_text.insert("1.0", content)
        else:
            self.insert_markdown(msg_text, content, markdown_color)
        
        # 进一步调整高度以适应实际内容 - 恢复上一版的逻辑
        self.adjust_text_height(msg_text)
        
        # 如果是流式输出，设置为可编辑状态以便更新内容
        if is_streaming:
            msg_text.config(state="normal")
        else:
            # 设置为只读（除了编辑模式）
            if not (role == "user" and message_id == self.editing_message_id):
                msg_text.config(state="disabled")
        
        # 绑定滚轮事件到Canvas
        msg_text.bind("<MouseWheel>", lambda e: self.on_mousewheel(e))
        
        # 为消息添加右键菜单（非流式消息）
        if not is_streaming:
            context_menu = tk.Menu(self.root, tearoff=0, 
                                 bg=self.colors["bg_tertiary"], 
                                 fg=self.colors["text_primary"],
                                 bd=0)
            
            if role == "assistant" and not is_welcome:
                # AI消息右键菜单
                context_menu.add_command(label="重新生成", 
                                       command=lambda: self.regenerate_message(message_id))
                context_menu.add_command(label="复制文本", 
                                       command=lambda: self.copy_message_text(message_id))
                
                # 如果有代码块，添加复制代码选项
                if "```" in content:
                    context_menu.add_separator()
                    context_menu.add_command(label="复制代码", 
                                           command=lambda: self.copy_code_blocks(message_id))
            elif role == "user" and not is_welcome:
                # 用户消息右键菜单
                context_menu.add_command(label="修改问题", 
                                       command=lambda: self.edit_user_message(message_id))
                context_menu.add_command(label="复制文本", 
                                       command=lambda: self.copy_message_text(message_id))
            
            # 绑定右键事件
            msg_text.bind("<Button-3>", 
                         lambda e: self.show_context_menu(e, context_menu))
        
        # 滚动到底部
        self.scroll_to_bottom()
        
        return message_frame, msg_text
    
    def update_streaming_message(self, token, full_content):
        """更新流式消息内容"""
        if self.current_streaming_message:
            msg_frame, msg_text = self.current_streaming_message
            
            # 更新文本内容
            msg_text.delete("1.0", tk.END)
            self.insert_markdown(msg_text, full_content, self.colors["text_primary"])
            
            # 调整高度
            self.adjust_text_height(msg_text)
            
            # 滚动到底部
            self.scroll_to_bottom()
    
    def finish_streaming_message(self, full_content):
        """完成流式消息，设置为只读并添加右键菜单"""
        if self.current_streaming_message:
            msg_frame, msg_text = self.current_streaming_message
            
            # 移除打字指示器
            if hasattr(msg_frame, 'typing_indicator'):
                msg_frame.typing_indicator.destroy()
            
            # 设置为只读
            msg_text.config(state="disabled")
            
            # 添加右键菜单
            context_menu = tk.Menu(self.root, tearoff=0, 
                                 bg=self.colors["bg_tertiary"], 
                                 fg=self.colors["text_primary"],
                                 bd=0)
            
            context_menu.add_command(label="重新生成", 
                                   command=lambda: self.regenerate_message(len(self.ai.history)-1))
            context_menu.add_command(label="复制文本", 
                                   command=lambda: self.copy_message_text(len(self.ai.history)-1))
            
            if "```" in full_content:
                context_menu.add_separator()
                context_menu.add_command(label="复制代码", 
                                       command=lambda: self.copy_code_blocks(len(self.ai.history)-1))
            
            msg_text.bind("<Button-3>", 
                         lambda e: self.show_context_menu(e, context_menu))
            
            # 重置当前流式消息
            self.current_streaming_message = None
    
    def insert_markdown(self, text_widget, content, markdown_color):
        """插入Markdown格式的文本"""
        # 先清除所有已有的tag
        for tag in text_widget.tag_names():
            text_widget.tag_delete(tag)
        
        # 定义样式 - 使用传入的markdown_color
        text_widget.tag_configure("bold", font=("Segoe UI", 11, "bold"), foreground=markdown_color)
        text_widget.tag_configure("italic", font=("Segoe UI", 11, "italic"), foreground=markdown_color)
        text_widget.tag_configure("code", 
                                font=("Consolas", 10), 
                                background=self.colors["bg_secondary"],
                                foreground=markdown_color,
                                relief="flat",
                                borderwidth=0)
        text_widget.tag_configure("code_block", 
                                font=("Consolas", 10), 
                                background=self.colors["bg_secondary"],
                                foreground=markdown_color,
                                relief="flat",
                                borderwidth=0)
        text_widget.tag_configure("heading", 
                                font=("Segoe UI", 13, "bold"),
                                foreground=markdown_color)
        text_widget.tag_configure("quote",
                                foreground=markdown_color,
                                font=("Segoe UI", 11, "italic"),
                                background=self.colors["bg_secondary"])
        text_widget.tag_configure("code_lang",
                                font=("Segoe UI", 9, "italic"),
                                foreground=self.colors["text_secondary"])
        
        # 插入文本并应用标记
        lines = content.split('\n')
        in_code_block = False
        code_block_content = []
        code_lang = ""
        
        for line in lines:
            # 检查代码块开始
            if line.startswith('```'):
                if in_code_block:
                    # 结束代码块
                    if code_block_content:
                        # 如果有语言标识，先插入语言标识
                        if code_lang:
                            text_widget.insert(tk.END, f"语言: {code_lang}\n", "code_lang")
                        # 插入代码内容
                        code_text = '\n'.join(code_block_content)
                        text_widget.insert(tk.END, code_text, "code_block")
                    text_widget.insert(tk.END, '\n')
                    in_code_block = False
                    code_block_content = []
                    code_lang = ""
                else:
                    # 开始代码块
                    in_code_block = True
                    # 提取语言标识
                    lang_match = re.match(r'^```(\w+)', line)
                    code_lang = lang_match.group(1) if lang_match else ""
                    text_widget.insert(tk.END, '\n')
                continue
            
            if in_code_block:
                code_block_content.append(line)
                continue
            
            # 处理其他Markdown格式
            self.process_markdown_line(text_widget, line, markdown_color)
            text_widget.insert(tk.END, '\n')
        
        # 如果文本以代码块结束但没有闭合标签
        if in_code_block and code_block_content:
            if code_lang:
                text_widget.insert(tk.END, f"语言: {code_lang}\n", "code_lang")
            code_text = '\n'.join(code_block_content)
            text_widget.insert(tk.END, code_text, "code_block")
    
    def process_markdown_line(self, text_widget, line, markdown_color):
        """处理单行Markdown格式"""
        if line.startswith('#'):
            # 标题
            level = len(line) - len(line.lstrip('#'))
            text_widget.insert(tk.END, line.lstrip('# '), "heading")
        elif line.startswith('>'):
            # 引用
            text_widget.insert(tk.END, line.lstrip('> '), "quote")
        else:
            # 处理内联格式
            segments = re.split(r'(\*\*.*?\*\*|\*.*?\*|`.*?`)', line)
            for segment in segments:
                if segment.startswith('**') and segment.endswith('**'):
                    # 粗体
                    text_widget.insert(tk.END, segment[2:-2], "bold")
                elif segment.startswith('*') and segment.endswith('*'):
                    # 斜体
                    text_widget.insert(tk.END, segment[1:-1], "italic")
                elif segment.startswith('`') and segment.endswith('`'):
                    # 行内代码
                    text_widget.insert(tk.END, segment[1:-1], "code")
                else:
                    text_widget.insert(tk.END, segment)
    
    def adjust_text_height(self, text_widget):
        """调整文本框高度以适应内容"""
        # 更新界面以确保文本已渲染
        text_widget.update_idletasks()
        
        # 获取文本的行数（考虑自动换行）
        line_count = int(text_widget.index('end-1c').split('.')[0])
        
        # 设置合适的高度
        text_widget.config(height=line_count)
    
    def scroll_to_bottom(self):
        """滚动到底部"""
        self.chat_canvas.update_idletasks()
        self.chat_canvas.yview_moveto(1.0)
    
    def show_context_menu(self, event, menu):
        """显示右键菜单"""
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    def send_message(self):
        """发送消息"""
        message = self.input_text.get("1.0", tk.END).strip()
        if not message or self.is_thinking:
            return
        
        # 清空输入框
        self.input_text.delete("1.0", tk.END)
        
        # 添加用户消息到界面
        user_msg_id = len(self.ai.history)
        self.add_message("user", message, user_msg_id)
        
        # 禁用输入
        self.set_thinking_state(True)
        
        # 创建流式消息框
        self.current_streaming_message = self.add_message("assistant", "", is_streaming=True)
        
        # 在新线程中获取AI回复（流式）
        threading.Thread(target=self.get_ai_stream_response, args=(message,), daemon=True).start()
    
    def get_ai_stream_response(self, user_message):
        """获取AI流式回复（在线程中运行）"""
        try:
            # 使用流式API
            full_response = self.ai.ask_stream(user_message, self.stream_callback)
            
            # 流式输出完成后，更新界面
            self.root.after(0, self.finish_streaming, full_response)
            
        except Exception as e:
            error_msg = f"获取回复时出错: {str(e)}"
            self.root.after(0, self.display_error, error_msg)
    
    def stream_callback(self, token, full_content):
        """流式回调函数，在主线程中更新UI"""
        self.root.after(0, self.update_streaming_message, token, full_content)
    
    def finish_streaming(self, full_response):
        """完成流式输出"""
        self.finish_streaming_message(full_response)
        self.set_thinking_state(False)
        
        # 保存聊天
        self.save_current_chat()
    
    def display_error(self, error_msg):
        """显示错误消息"""
        if self.current_streaming_message:
            msg_frame, msg_text = self.current_streaming_message
            
            # 更新文本内容为错误消息
            msg_text.delete("1.0", tk.END)
            msg_text.insert("1.0", error_msg)
            
            # 完成流式消息
            self.finish_streaming_message(error_msg)
        
        self.set_thinking_state(False)
    
    def set_thinking_state(self, thinking):
        """设置思考状态"""
        self.is_thinking = thinking
        if thinking:
            self.status_var.set("⏳ AI正在思考...")
            self.send_button.config(state="disabled")
            self.input_text.config(state="disabled")
        else:
            self.status_var.set("✓ 就绪")
            self.send_button.config(state="normal")
            self.input_text.config(state="normal")
            self.input_text.focus()
    
    def regenerate_message(self, message_id):
        """重新生成指定的AI消息"""
        if message_id is not None:
            # 找到对应的用户消息ID
            if message_id > 0 and message_id < len(self.ai.history):
                user_msg_id = message_id - 1
                user_message = self.ai.history[user_msg_id]["content"]
                
                # 回退到用户消息
                self.ai.revert(user_msg_id // 2)
                
                # 清除界面上的所有消息，重新添加历史消息
                self.clear_messages()
                
                # 重新发送消息（使用流式）
                self.set_thinking_state(True)
                self.current_streaming_message = self.add_message("assistant", "", is_streaming=True)
                threading.Thread(target=self.get_ai_stream_response, args=(user_message,), daemon=True).start()
    
    def copy_message_text(self, message_id):
        """复制消息文本"""
        if message_id is not None and message_id < len(self.ai.history):
            message_content = self.ai.history[message_id]["content"]
            self.root.clipboard_clear()
            self.root.clipboard_append(message_content)
            self.status_var.set("✓ 文本已复制")
    
    def copy_code_blocks(self, message_id):
        """复制消息中的代码块"""
        if message_id is not None and message_id < len(self.ai.history):
            message_content = self.ai.history[message_id]["content"]
            
            # 提取所有代码块（包括语言标识）
            code_blocks = re.findall(r'```(\w+)?\n(.*?)\n```', message_content, re.DOTALL)
            if code_blocks:
                code_texts = []
                for lang, code in code_blocks:
                    if lang:
                        code_texts.append(f"# {lang}\n{code}")
                    else:
                        code_texts.append(code)
                
                code_text = '\n\n'.join(code_texts)
                self.root.clipboard_clear()
                self.root.clipboard_append(code_text)
                self.status_var.set("✓ 代码已复制")
            else:
                self.status_var.set("⚠ 未找到代码块")
    
    def edit_user_message(self, message_id):
        """编辑用户消息"""
        if message_id >= len(self.ai.history) or self.ai.history[message_id]["role"] != "user":
            return
        
        self.editing_message_id = message_id
        original_content = self.ai.history[message_id]["content"]
        
        # 创建编辑窗口
        edit_window = tk.Toplevel(self.root)
        edit_window.title("修改问题")
        edit_window.geometry("600x400")
        edit_window.configure(bg=self.colors["bg"])
        edit_window.transient(self.root)
        edit_window.grab_set()
        
        # 编辑文本框
        edit_text = tk.Text(edit_window,
                          wrap=tk.WORD,
                          bg=self.colors["bg_tertiary"],
                          fg=self.colors["text_primary"],
                          font=("Segoe UI", 11),
                          padx=10,
                          pady=10)
        edit_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        edit_text.insert("1.0", original_content)
        
        # 按钮框架
        button_frame = tk.Frame(edit_window, bg=self.colors["bg"])
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def save_edit():
            new_content = edit_text.get("1.0", tk.END).strip()
            if new_content and new_content != original_content:
                # 回退到编辑的消息之前
                round_index = (message_id - 1) // 2
                self.ai.revert(round_index)
                
                # 清除界面上的所有消息，重新添加历史消息
                self.clear_messages()
                
                # 重新发送编辑后的消息（使用流式）
                self.set_thinking_state(True)
                self.current_streaming_message = self.add_message("assistant", "", is_streaming=True)
                threading.Thread(target=self.get_ai_stream_response, args=(new_content,), daemon=True).start()
            
            edit_window.destroy()
            self.editing_message_id = None
        
        def cancel_edit():
            edit_window.destroy()
            self.editing_message_id = None
        
        ttk.Button(button_frame, text="保存", command=save_edit).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="取消", command=cancel_edit).pack(side=tk.RIGHT)
        
        edit_window.protocol("WM_DELETE_WINDOW", cancel_edit)
    
    def clear_messages(self):
        """清除所有消息显示"""
        for widget in self.messages_frame.winfo_children():
            widget.destroy()


if __name__ == "__main__":
    # 注意：请替换为你的真实API密钥
    AItk(
        system_prompt="你是一个智能助手，能够帮助用户解答问题、提供建议和协助完成各种任务。",
        api_key="sk-bsgrenbiomfmezwyiijfurpnbwssedezvobnxdyhqbiakiud",
        base_url="https://api.siliconflow.cn/v1"
    )