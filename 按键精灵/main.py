import compiler as c
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import threading
import sys
from io import StringIO

class LineNumbers(tk.Canvas):
    """行号显示组件"""
    def __init__(self, parent, text_widget, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.text_widget = text_widget
        self.text_widget.bind('<KeyRelease>', self.redraw)
        self.text_widget.bind('<MouseWheel>', self.redraw)
        self.text_widget.bind('<Button-1>', self.redraw)
        self.text_widget.bind('<Configure>', self.redraw)
        self.redraw()
        
    def redraw(self, event=None):
        self.delete("all")
        i = self.text_widget.index("@0,0")
        while True:
            dline = self.text_widget.dlineinfo(i)
            if dline is None:
                break
            y = dline[1]
            line_num = str(i).split(".")[0]
            self.create_text(2, y, anchor="nw", text=line_num, 
                           fill="#858585", font=("Consolas", 11))
            i = self.text_widget.index(f"{i}+1line")

class IDE:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("IDE")
        self.root.geometry("900x700")
        
        # 设置主题色
        self.bg_color = "#1e1e1e"        # 深黑背景
        self.fg_color = "#d4d4d4"        # 浅灰文字
        self.keyword_color = "#6bb2f0"    # 浅蓝关键词
        self.string_color = "#ce9178"     # 橙色字符串
        self.comment_color = "#6a9955"    # 绿色注释
        self.number_color = "#b5cea8"     # 数字颜色
        self.output_bg = "#252526"        # 输出区域背景
        self.menu_bg = "#2d2d2d"          # 菜单背景色
        self.menu_fg = "#ffffff"          # 菜单文字颜色
        
        # 设置 ttk 样式
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background=self.bg_color, borderwidth=0, relief='flat')
        style.configure('TLabel', background=self.bg_color, foreground=self.fg_color, borderwidth=0)
        style.configure('TButton', background='#3c3c3c', foreground=self.fg_color, borderwidth=0, focuscolor='none')
        style.map('TButton', background=[('active', '#4c4c4c')])
        
        # 创建自定义菜单栏（使用 Frame 模拟）
        self.create_menu()
        
        # 创建主框架
        main_frame = ttk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 编辑区
        self.create_editor(main_frame)
        
        # 按钮区域
        self.create_buttons(main_frame)
        
        # 输出区域
        self.create_output(main_frame)
        
        # 绑定快捷键
        self.root.bind('<F5>', lambda e: self.run_script())
        self.root.bind('<Control-s>', lambda e: self.save_file())
        
        # 配置滚动条样式 - 隐藏滚轮（变黑）
        self.configure_scrollbars()
        
    def configure_scrollbars(self):
        """配置滚动条样式，让滚轮变黑"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 垂直滚动条样式
        style.configure("Vertical.TScrollbar",
                       background="#2d2d2d",
                       troughcolor=self.bg_color,
                       bordercolor=self.bg_color,
                       arrowcolor="#808080",
                       relief="flat")
        style.map("Vertical.TScrollbar",
                 background=[('active', '#3d3d3d'), ('pressed', '#4d4d4d')])
        
        # 水平滚动条样式
        style.configure("Horizontal.TScrollbar",
                       background="#2d2d2d",
                       troughcolor=self.bg_color,
                       bordercolor=self.bg_color,
                       arrowcolor="#808080",
                       relief="flat")
        style.map("Horizontal.TScrollbar",
                 background=[('active', '#3d3d3d'), ('pressed', '#4d4d4d')])
        
    def create_menu(self):
        """创建自定义菜单栏（用 Frame + Label 模拟）"""
        # 菜单容器
        menu_frame = tk.Frame(self.root, bg=self.menu_bg, height=25)
        menu_frame.pack(fill=tk.X, side=tk.TOP)
        menu_frame.pack_propagate(False)
        
        # 文件菜单
        file_label = tk.Label(menu_frame, text="文件", bg=self.menu_bg, 
                             fg=self.menu_fg, font=("微软雅黑", 10), cursor="hand2")
        file_label.pack(side=tk.LEFT, padx=(10, 5), pady=2)
        
        # 绑定点击事件
        file_label.bind('<Button-1>', self.show_file_menu)
        
        # 运行菜单
        run_label = tk.Label(menu_frame, text="运行", bg=self.menu_bg, 
                            fg=self.menu_fg, font=("微软雅黑", 10), cursor="hand2")
        run_label.pack(side=tk.LEFT, padx=5, pady=2)
        run_label.bind('<Button-1>', self.show_run_menu)
        
        # 右键菜单 - 文件
        self.file_menu = tk.Menu(self.root, tearoff=0, 
                                bg=self.menu_bg, fg=self.menu_fg,
                                activebackground='#3d3d3d', 
                                activeforeground='#ffffff',
                                borderwidth=0)
        self.file_menu.add_command(label="新建", command=self.new_file)
        self.file_menu.add_command(label="打开", command=self.open_file)
        self.file_menu.add_command(label="保存", command=self.save_file)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="退出", command=self.root.quit)
        
        # 右键菜单 - 运行
        self.run_menu = tk.Menu(self.root, tearoff=0,
                               bg=self.menu_bg, fg=self.menu_fg,
                               activebackground='#3d3d3d',
                               activeforeground='#ffffff',
                               borderwidth=0)
        self.run_menu.add_command(label="执行脚本 (F5)", command=self.run_script)
        
    def show_file_menu(self, event):
        """显示文件菜单"""
        x = event.widget.winfo_rootx()
        y = event.widget.winfo_rooty() + event.widget.winfo_height()
        self.file_menu.post(x, y)
        
    def show_run_menu(self, event):
        """显示运行菜单"""
        x = event.widget.winfo_rootx()
        y = event.widget.winfo_rooty() + event.widget.winfo_height()
        self.run_menu.post(x, y)
        
    def create_editor(self, parent):
        # 编辑区框架
        editor_frame = ttk.Frame(parent)
        editor_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 标签
        label = tk.Label(editor_frame, text="脚本编辑区", anchor=tk.W,
                        bg=self.bg_color, fg=self.fg_color, bd=0)
        label.pack(fill=tk.X, pady=(0, 2))
        
        # 文本编辑器容器
        text_container = ttk.Frame(editor_frame)
        text_container.pack(fill=tk.BOTH, expand=True)
        
        # 文本编辑器
        self.text = scrolledtext.ScrolledText(
            text_container,
            wrap=tk.NONE,
            font=("Consolas", 11),
            bg=self.bg_color,
            fg=self.fg_color,
            insertbackground="white",
            selectbackground="#264f78",
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0,
            padx=5
        )
        self.text.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 行号显示
        self.line_numbers = LineNumbers(text_container, self.text,
                                       width=40, bg=self.bg_color,
                                       highlightthickness=0, borderwidth=0)
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        
        # 配置标签样式
        self.text.tag_configure("keyword", foreground=self.keyword_color)
        self.text.tag_configure("string", foreground=self.string_color)
        self.text.tag_configure("comment", foreground=self.comment_color)
        self.text.tag_configure("number", foreground=self.number_color)
        
        # 绑定事件
        self.text.bind('<KeyRelease>', self.on_key_release)
        self.text.bind('<MouseWheel>', lambda e: self.line_numbers.redraw())
        
    def create_buttons(self, parent):
        # 按钮框架
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="运行 (F5)", command=self.run_script).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="清空输出", command=self.clear_output).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="保存 (Ctrl+S)", command=self.save_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="清空编辑器", command=self.clear_editor).pack(side=tk.LEFT, padx=2)
        
    def create_output(self, parent):
        # 输出框架
        output_frame = ttk.Frame(parent)
        output_frame.pack(fill=tk.BOTH, expand=False, padx=5, pady=5)
        
        # 标签
        label = tk.Label(output_frame, text="输出", anchor=tk.W,
                        bg=self.bg_color, fg=self.fg_color, bd=0)
        label.pack(fill=tk.X, pady=(0, 2))
        
        # 输出文本框
        self.output = scrolledtext.ScrolledText(
            output_frame,
            height=10,
            font=("Consolas", 10),
            bg=self.output_bg,
            fg=self.fg_color,
            wrap=tk.WORD,
            state=tk.DISABLED,
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0
        )
        self.output.pack(fill=tk.BOTH, expand=True)
        
    def on_key_release(self, event):
        """实时语法高亮"""
        if event and event.keysym in ("Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R"):
            return
            
        # 保存光标位置
        cursor_pos = self.text.index(tk.INSERT)
        
        # 清除所有标签
        for tag in self.text.tag_names():
            if tag not in ("sel", "keyword", "string", "comment", "number"):
                self.text.tag_delete(tag)
        
        content = self.text.get("1.0", tk.END)
        lines = content.split('\n')
        
        # 逐行处理
        line_start = 1
        for line in lines:
            self.highlight_line(line_start, line)
            line_start += 1
        
        # 恢复光标位置
        self.text.mark_set(tk.INSERT, cursor_pos)
        # 更新行号
        self.line_numbers.redraw()
        
    def highlight_line(self, line_num, line):
        """高亮单行"""
        if not line.strip():
            return
            
        # 处理注释
        comment_pos = line.find('#')
        if comment_pos != -1:
            self.text.tag_add("comment", 
                            f"{line_num}.{comment_pos}", 
                            f"{line_num}.end")
            line = line[:comment_pos]
        
        # 分割单词
        words = line.split()
        pos = 0
        for word in words:
            # 查找单词位置
            start_pos = line.find(word, pos)
            if start_pos == -1:
                continue
            end_pos = start_pos + len(word)
            pos = end_pos
            
            # 检查是否为关键词
            if word.upper() in c.KEYWORDS:
                self.text.tag_add("keyword", 
                                f"{line_num}.{start_pos}", 
                                f"{line_num}.{end_pos}")
            # 检查是否为数字
            elif word.replace('.', '').replace('-', '').isdigit():
                self.text.tag_add("number", 
                                f"{line_num}.{start_pos}", 
                                f"{line_num}.{end_pos}")
            # 检查是否为字符串
            elif (word.startswith('"') and word.endswith('"')) or \
                 (word.startswith("'") and word.endswith("'")):
                self.text.tag_add("string", 
                                f"{line_num}.{start_pos}", 
                                f"{line_num}.{end_pos}")
        
    def run_script(self):
        """运行脚本"""
        code = self.text.get("1.0", tk.END)
        self.output.config(state=tk.NORMAL)
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, "运行中...\n")
        self.output.config(state=tk.DISABLED)
        
        # 在新线程中运行
        thread = threading.Thread(target=self._run_script, args=(code,))
        thread.daemon = True
        thread.start()
        
    def _run_script(self, code):
        """实际运行脚本的线程函数"""
        try:
            old_stdout = sys.stdout
            sys.stdout = StringIO()
            
            try:
                actions = c.compile_code(code)
                c.run(actions)
                output = sys.stdout.getvalue()
            finally:
                sys.stdout = old_stdout
            
            self.output.config(state=tk.NORMAL)
            self.output.delete("1.0", tk.END)
            self.output.insert(tk.END, output if output else "执行完成，无输出\n")
            self.output.config(state=tk.DISABLED)
            
        except Exception as e:
            self.output.config(state=tk.NORMAL)
            self.output.delete("1.0", tk.END)
            self.output.insert(tk.END, f"错误：{str(e)}\n")
            self.output.config(state=tk.DISABLED)
            
    def clear_output(self):
        self.output.config(state=tk.NORMAL)
        self.output.delete("1.0", tk.END)
        self.output.config(state=tk.DISABLED)
        
    def clear_editor(self):
        self.text.delete("1.0", tk.END)
        self.line_numbers.redraw()
        
    def new_file(self):
        self.clear_editor()
        self.clear_output()
        
    def open_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("脚本文件", "*.sc"), ("所有文件", "*.*")]
        )
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.text.delete("1.0", tk.END)
            self.text.insert(tk.END, content)
            self.on_key_release(None)
            
    def save_file(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".sc",
            filetypes=[("脚本文件", "*.sc"), ("所有文件", "*.*")]
        )
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                content = self.text.get("1.0", tk.END)
                f.write(content)
            self.output.config(state=tk.NORMAL)
            self.output.insert(tk.END, f"已保存到 {file_path}\n")
            self.output.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = IDE(root)
    root.mainloop()