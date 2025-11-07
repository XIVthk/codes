from datetime import datetime
import os
import tkinter as tk
from tkinter import ttk
import sys
import subprocess
from SQL import readable_sqltest_report
from check_port import check_port
from check_port import IPV4 as IP
import re
import threading
from pathlib import Path


class Terminal:
    def __init__(self):
        self.root = tk.Tk()

        if sys.platform.startswith('win'):
            self.whereami = "C:\\Users\\" + os.getlogin()
        else:
            self.whereami = os.path.expanduser("~")

        self.TYPING_ABLE = tk.BooleanVar()
        self.TYPING_ABLE.set(True)

        self.SYSCHECK = tk.BooleanVar()
        self.SYSCHECK.set(True)

        self.SELFECHO = tk.BooleanVar()
        self.SELFECHO.set(True)

        self.ALWAYSECHO = tk.BooleanVar()
        self.ALWAYSECHO.set(False)

        self.timestr = tk.StringVar(value="%Y/%m/%d %H:%M:%S")
        
        self.root.option_add("*Font", "Consolas 10")
        self.root.option_add("*Background", "#000000")
        self.root.option_add("*Foreground", "#00BFFF")

        self.setup_win()
    
    def setup_win(self):
        self.root.title("Terminal")
        self.root.geometry("1200x800")
        self.root.attributes("-fullscreen", True)
        self.root.bind("<Escape>", lambda e: self.root.attributes("-fullscreen", False))
        self.root.bind("<F11>", lambda e: self.toggle_fullscreen())
        self.root.configure(bg="#000000")
        self.root.resizable(True, True)
        
        self.fix_platform_styles()
        
        self.setup_style()
        self.basic_widgits()
        self.create_settings_window()
        self.root.mainloop()
    
    def fix_platform_styles(self):
        if sys.platform.startswith('win'):
            self.root.option_add("*TButton*borderWidth", 1)
        elif sys.platform.startswith('darwin'):
            self.root.option_add("*TButton*highlightThickness", 0)
        else:
            self.root.option_add("*TButton*relief", tk.FLAT)
    
    def toggle_fullscreen(self):
        is_fullscreen = self.root.attributes("-fullscreen")
        self.root.attributes("-fullscreen", not is_fullscreen)
    
    def setup_style(self):
        style = ttk.Style()
        
        style.theme_use('alt')  
        
        style.configure("Dark.TFrame", background="#000000")
        
        style.configure(
            "TButton",
            background="#000000",
            foreground="#00BFFF",
            borderwidth=1,
            focusthickness=0,
            focuscolor="none",
            font=("Consolas", 11),
            padding=5
        )

        style.map("TButton", 
                  background=[('active', '#2A2A2A'), ('pressed', '#1A1A1A')],
                  foreground=[('active', "#1E90FF"), ('pressed', "#00FFFF")]
        )
        
        style.configure(
            'Terminal.TEntry',
            fieldbackground="#000000",
            foreground="#00BFFF",
            insertcolor="#00BFFF",
            borderwidth=0,
            focusthickness=0,
            padding=8,
            font=("Consolas", 14)
        )
        
        style.configure(
            "Terminal.TLabel",
            background="#000000",
            foreground="#00BFFF",
            font=("Consolas", 16, "bold")
        )
        
        style.configure(
            "Sidebar.TLabel",
            background="#000000",
            foreground="#00BFFF",
            font=("Consolas", 12, "italic"),
            padding=5
        )

        style.configure(
            "TNotebook",
            background="#000000",
            borderwidth=0,
            highlightthickness=0,
            tabmargin=0,
            padding=0
        )

        style.configure(
            "TNotebook.Tab",
            font=("Consolas", 10),
            foreground="#00BFFF",
            background="#000000",
            padding=[10, 5],
            borderwidth=0
        )

        style.map(
            "TNotebook.Tab",
            foreground=[("selected", "#1E90FF")],
            background=[("selected", "#2A2A2A")],
            borderwidth=[("selected", 0)]
        )
    
    def create_settings_window(self):
        self.settings_window = tk.Frame(
            self.root,
            bg="#333333",
            bd=2,
            relief=tk.SOLID
        )
        self.settings_window.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=400, height=400)
        self.settings_window.lower()

        title_bar = tk.Frame(
            self.settings_window,
            bg="#222222",
            height=30
        )
        title_bar.pack(fill=tk.X)

        title_label = tk.Label(
            title_bar,
            text="Settings",
            bg="#222222",
            fg="#00BFFF",
            font=("Consolas", 14, "bold")
        )
        title_label.pack(side=tk.LEFT, padx=10, pady=5)

        close_button = tk.Button(
            title_bar,
            text="x",
            bg="#222222",
            fg="#FFFFFF",
            bd=0,
            width=3,
            font=("Consolas", 14, "bold"),
            command=lambda: self.settings_window.lower()
        )
        close_button.pack(side=tk.RIGHT, padx=5, pady=3)

        content = tk.Frame(
            self.settings_window,
            bg="#333333"
        )
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        typing_frame = tk.Frame(content, bg="#333333")
        typing_frame.pack(fill=tk.X, pady=(10, 0))

        typing_label = tk.Label(
            typing_frame,
            text="Typing Animation:",
            bg="#333333",
            fg="#00BFFF",
            font=("Consolas", 12)
        )
        typing_label.pack(side=tk.LEFT, padx=(0, 10))

        tk.Radiobutton(
            typing_frame,
            text="On",
            variable=self.TYPING_ABLE,
            value=True,
            bg="#333333",
            fg="#00BFFF",
            selectcolor="#555555",
            font=("Consolas", 12)
        ).pack(side=tk.LEFT, padx=(0, 20))

        tk.Radiobutton(
            typing_frame,
            text="Off",
            variable=self.TYPING_ABLE,
            value=False,
            bg="#333333",
            fg="#00BFFF",
            selectcolor="#555555",
            font=("Consolas", 12)
        ).pack(side=tk.LEFT)

        syscheck_frame = tk.Frame(content, bg="#333333")
        syscheck_frame.pack(fill=tk.X, pady=(10, 0))

        syscheck_label = tk.Label(
            syscheck_frame,
            text="Sys CMD Check:",
            bg="#333333",
            fg="#00BFFF",
            font=("Consolas", 12)
        )
        syscheck_label.pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Radiobutton(
            syscheck_frame,
            text="On",
            variable=self.SYSCHECK,
            value=True,
            bg="#333333",
            fg="#00BFFF",
            selectcolor="#555555",
            font=("Consolas", 12)
        ).pack(side=tk.LEFT, padx=(0, 20))

        tk.Radiobutton(
            syscheck_frame,
            text="Off",
            variable=self.SYSCHECK,
            value=False,
            bg="#333333",
            fg="#00BFFF",
            selectcolor="#555555",
            font=("Consolas", 12)
        ).pack(side=tk.LEFT)

        self.selfecho_frame = tk.Frame(content, bg="#333333")
        self.selfecho_frame.pack(fill=tk.X, pady=(10, 0))

        selfecho_label = tk.Label(
            self.selfecho_frame,
            text="Self Echo:",
            bg="#333333",
            fg="#00BFFF",
            font=("Consolas", 12)
        )
        selfecho_label.pack(side=tk.LEFT, padx=(0, 10))

        tk.Radiobutton(
            self.selfecho_frame,
            text="On",
            variable=self.SELFECHO,
            value=True,
            bg="#333333",
            fg="#00BFFF",
            selectcolor="#555555",
            font=("Consolas", 12)
        ).pack(side=tk.LEFT, padx=(0, 20))

        tk.Radiobutton(
            self.selfecho_frame,
            text="Off",
            variable=self.SELFECHO,
            value=False,
            bg="#333333",
            fg="#00BFFF",
            selectcolor="#555555",
            font=("Consolas", 12)
        ).pack(side=tk.LEFT)

        alwaysecho_frame = tk.Frame(content, bg="#333333")
        alwaysecho_frame.pack(fill=tk.X, pady=(10, 0))

        alwaysecho_label = tk.Label(
            alwaysecho_frame,
            text="Always Echo:",
            bg="#333333",
            fg="#00BFFF",
            font=("Consolas", 12)
        )
        alwaysecho_label.pack(side=tk.LEFT, padx=(0, 10))

        tk.Radiobutton(
            alwaysecho_frame,
            text="On",
            variable=self.ALWAYSECHO,
            value=True,
            bg="#333333",
            fg="#00BFFF",
            selectcolor="#555555",
            font=("Consolas", 12)
        ).pack(side=tk.LEFT, padx=(0, 20))

        tk.Radiobutton(
            alwaysecho_frame,
            text="Off",
            variable=self.ALWAYSECHO,
            value=False,
            bg="#333333",
            fg="#00BFFF",
            selectcolor="#555555",
            font=("Consolas", 12)
        ).pack(side=tk.LEFT)

        tk.Label(content, text="Time Format:", bg="#333333", fg="#00BFFF", font=("Consolas", 12)).pack(fill=tk.X, pady=(10, 0))
        self.time_format_entry = ttk.Entry(
            content,
            style="Terminal.TEntry",
            font=("Consolas", 12)
        )
        self.time_format_entry.insert(0, self.timestr.get())
        self.time_format_entry.pack(fill=tk.X, pady=(0, 10))

        tk.Button(content, text="Save Settings", command=self.save_settings).pack(fill=tk.X, pady=(10, 0))

    def save_settings(self):
        try:
            datetime.now().strftime(self.time_format_entry.get())
            self.show_message("Success", "Settings saved successfully.")
        except ValueError:
            self.show_message("Error", "Invalid time format. Please use the format like \"%Y/%m/%d %H:%M:%S\".", is_error=True)
            return
        self.timestr.set(self.time_format_entry.get())
        self.settings_window.lower()
    
    def show_message(self, title, message, is_error=False):
        if hasattr(self, 'msg_window') and self.msg_window.winfo_exists():
            self.msg_window.destroy()
        
        self.msg_window = tk.Frame(
            self.root,
            bg="#333333",
            bd=2,
            relief=tk.SOLID
        )
        self.msg_window.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=400, height=150)
        self.msg_window.lift()
        
        title_bar = tk.Frame(
            self.msg_window,
            bg="#222222",
            height=30
        )
        title_bar.pack(fill=tk.X)
        
        title_label = tk.Label(
            title_bar,
            text=title,
            bg="#222222",
            fg="#FF6347" if is_error else "#00BFFF",
            font=("Consolas", 12, "bold")
        )
        title_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        close_btn = tk.Button(
            title_bar,
            text="x",
            bg="#222222",
            fg="#FFFFFF",
            bd=0,
            width=3,
            font=("Consolas", 10),
            command=lambda: self.msg_window.destroy()
        )
        close_btn.pack(side=tk.RIGHT, padx=5, pady=3)
        
        content_frame = tk.Frame(
            self.msg_window,
            bg="#333333"
        )
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        message_label = tk.Label(
            content_frame,
            text=message,
            bg="#333333",
            fg="#00BFFF",
            font=("Consolas", 12),
            wraplength=350,
            justify=tk.LEFT
        )
        message_label.pack(expand=True)
        
        btn_frame = tk.Frame(
            self.msg_window,
            bg="#333333"
        )
        btn_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ok_btn = ttk.Button(
            btn_frame,
            text="OK",
            command=lambda: self.msg_window.destroy()
        )
        ok_btn.pack(side=tk.RIGHT)

    def draw_sidebar(self):
        setting_btn = ttk.Button(
            self.sidebar,
            text="Settings",
            command=lambda: self.settings_window.lift(),
            style="Sidebar.TLabel"
        )
        setting_btn.pack(fill=tk.X, pady=(0, 15))

        form_notebook = ttk.Notebook(self.sidebar)
        form_notebook.pack(fill=tk.X, pady=(0, 15))

        # ======= Check Port Form =======
        check_form = ttk.Frame(
            form_notebook,
            style="Dark.TFrame"
        )
        form_notebook.add(check_form, text="Check Port")

        check_input_frame = ttk.Frame(check_form, style="Dark.TFrame")
        check_input_frame.pack(fill=tk.X, padx=10, pady=10)
        
        check_input_frame.columnconfigure(0, weight=0)
        check_input_frame.columnconfigure(1, weight=1)

        ttk.Label(check_input_frame, text="IP Address:", style="Sidebar.TLabel").grid(
            row=0, column=0, sticky=tk.W, pady=(0, 5), padx=(0, 10))
        self.ip_entry = ttk.Entry(check_input_frame, style="Terminal.TEntry")
        self.ip_entry.grid(row=0, column=1, sticky=tk.EW, pady=(0, 5))
        self.ip_entry.insert(0, "127.0.0.1")

        ttk.Label(check_input_frame, text="Port(s):", style="Sidebar.TLabel").grid(
            row=1, column=0, sticky=tk.W, pady=(5, 5), padx=(0, 10))
        self.port_entry = ttk.Entry(check_input_frame, style="Terminal.TEntry")
        self.port_entry.grid(row=1, column=1, sticky=tk.EW, pady=(5, 5))
        self.port_entry.insert(0, ":65535")
        
        ttk.Label(check_input_frame, text="e.g. 80,443-445,:1000", 
                style="Sidebar.TLabel", foreground="#888888").grid(
            row=2, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))

        options_frame = ttk.Frame(check_input_frame, style="Dark.TFrame")
        options_frame.grid(row=3, column=0, columnspan=2, sticky=tk.EW, pady=5)
        options_frame.columnconfigure(1, weight=1)
        options_frame.columnconfigure(3, weight=1)

        ttk.Label(options_frame, text="Max Workers:", style="Sidebar.TLabel").grid(
            row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.max_workers_entry = ttk.Entry(options_frame, style="Terminal.TEntry", width=10)
        self.max_workers_entry.grid(row=0, column=1, sticky=tk.EW, padx=(0, 10))
        self.max_workers_entry.insert(0, "50")

        ttk.Label(options_frame, text="Timeout:", style="Sidebar.TLabel").grid(
            row=1, column=0, sticky=tk.W, padx=(0, 5))
        self.timeout_entry = ttk.Entry(options_frame, style="Terminal.TEntry", width=10)
        self.timeout_entry.grid(row=1, column=1, sticky=tk.EW)
        self.timeout_entry.insert(0, "1")

        check_gen_btn = ttk.Button(
            check_form,
            text="Generate Check Command",
            command=self.generate_check_command
        )
        check_gen_btn.pack(fill=tk.X, padx=10, pady=10)

        # ======= SQL Attack Form =======
        sql_form = ttk.Frame(
            form_notebook,
            style="Dark.TFrame"
        )
        form_notebook.add(sql_form, text="SQL Attack")

        sql_input_frame = ttk.Frame(sql_form, style="Dark.TFrame")
        sql_input_frame.pack(fill=tk.X, padx=10, pady=10)

        sql_input_frame.columnconfigure(0, weight=0)
        sql_input_frame.columnconfigure(1, weight=1)

        ttk.Label(sql_input_frame, text="Target: ", style="Sidebar.TLabel").grid(
            row=0, column=0, sticky=tk.W, pady=(0, 5), padx=(0, 10))
        self.target_entry = ttk.Entry(sql_input_frame, style="Terminal.TEntry")
        self.target_entry.grid(row=0, column=1, sticky=tk.EW, pady=(0, 5))

        ttk.Label(sql_input_frame, text="Param(s):", style="Sidebar.TLabel").grid(
            row=1, column=0, sticky=tk.W, pady=(0, 5), padx=(0, 10))
        self.param_entry = ttk.Entry(sql_input_frame, style="Terminal.TEntry")
        self.param_entry.grid(row=1, column=1, sticky=tk.EW, pady=(0, 5))

        ttk.Label(sql_input_frame, text="Payload(s):", style="Sidebar.TLabel").grid(
            row=2, column=0, sticky=tk.W, pady=(0, 5), padx=(0, 10))
        self.payload_entry = ttk.Entry(sql_input_frame, style="Terminal.TEntry")
        self.payload_entry.grid(row=2, column=1, sticky=tk.EW, pady=(0, 5))

        sql_gen_btn = ttk.Button(
            sql_form,
            text="Generate sql command",
            command=self.generate_sql_command
        )
        sql_gen_btn.pack(fill=tk.X, padx=10, pady=10)

        # ======= Other Buttons =======
        history_saving_btn = ttk.Button(
            self.sidebar,
            text="Save History",
            command=self.run_save
        )
        history_saving_btn.pack(fill=tk.X, padx=10, pady=10)

    
    def generate_check_command(self):
        ip_str = self.ip_entry.get().strip()
        if not ip_str:
            self.show_message("Error", "Please enter an IP address or hostname.", True)
            return
        port_str = self.port_entry.get().strip()
        if not port_str:
            self.show_message("Error", "Please enter at least one port number.", True)
            return
        try:
            ip_obj = IP(ip_str)
        except Exception as e:
            self.show_message("Error", f"Invalid IP address or hostname: {str(e)}", True)
            return
        
        ports = [p.strip() for p in port_str.split(",") if p.strip()]
        if not ports:
            self.show_message("Error", "Please enter valid port numbers.", True)
            return
        
        port_part = f"[{','.join(ports)}]"
        
        args = []
        max_workers = self.max_workers_entry.get().strip()
        if max_workers:
            try:
                int(max_workers)
                args.append(f"-m={max_workers}")
            except ValueError:
                self.show_message("Error", "Max workers must be an integer.", True)
                return
        
        timeout = self.timeout_entry.get().strip()
        if timeout:
            try:
                float(timeout)
                args.append(f"-t={timeout}")
            except ValueError:
                self.show_message("Error", "Timeout must be a number.", True)
                return
        
        args_str = " " + " ".join(args) if args else ""
        full_command = f"check {str(ip_obj)}{port_part}{args_str}"
        
        self.cmd_entry.delete(0, tk.END)
        self.cmd_entry.insert(0, full_command)
    
    def generate_sql_command(self):
        # sql <hostname> <-pr=> <-pld=>
        target_str = self.target_entry.get().strip()
        param_str = self.param_entry.get().strip()
        payload_str = self.payload_entry.get().strip()
        
        if not all([target_str, param_str, payload_str]):
            self.show_message("Error", "Please fill out all fields.", True)
            return
        
        params = [p.strip() for p in param_str.split(",")]
        payloads = [p.strip() for p in payload_str.split(",")]
        if not all([params, payloads]):
            self.show_message("Error", "Please provide at least one parameter and one payload.", True)
            return
        
        cmd = f"sql {target_str} -pr={param_str} -pld={payload_str}"
        self.cmd_entry.delete(0, tk.END)
        self.cmd_entry.insert(0, cmd)
        

    
    def basic_widgits(self):
        
        self.main_frame = ttk.Frame(self.root, style="Dark.TFrame")
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        self.sidebar = ttk.Frame(self.main_frame, width=220, style="Dark.TFrame")
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
        self.sidebar.pack_propagate(False)
        
        self.terminal_container = ttk.Frame(self.main_frame, style="Dark.TFrame")
        self.terminal_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.tools_label = ttk.Label(
            self.sidebar,
            text="TOOLS",
            style="Sidebar.TLabel",
            font=("Consolas", 20, "bold")
        )
        self.tools_label.pack(fill=tk.X, pady=(0, 15))
        self.draw_sidebar()

        self.time_label = ttk.Label(
            self.terminal_container,
            text=datetime.now().strftime(self.timestr.get()),
            style="Terminal.TLabel",
            font=("Consolas", 12)
        )
        self.time_label.pack(pady=(0, 10), anchor=tk.W)
        
        self.terminal_output = tk.Text(
            self.terminal_container,
            bg="#000000",
            fg="#00BFFF",
            insertbackground="#00BFFF",
            selectbackground="#1E90FF",
            font=('Consolas', 12),
            wrap=tk.WORD,
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0,
            state=tk.DISABLED
        )
        self.terminal_output.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.cmd_frame = ttk.Frame(self.terminal_container, style="Dark.TFrame")
        self.cmd_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.prompt_label = ttk.Label(
            self.cmd_frame,
            text="~$ ",
            style="Terminal.TLabel",
            font=("Consolas", 14)
        )
        self.prompt_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.cmd_entry = ttk.Entry(
            self.cmd_frame,
            style="Terminal.TEntry",
            font=("Consolas", 14)
        )
        self.cmd_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
        self.cmd_entry.focus_set()
        
        self.cmd_entry.bind("<Return>", lambda e: self.entry_enter())
        
        self.time_label.after(1000, self.update_time)
        
    def update_time(self):
        self.time_label.config(text=datetime.now().strftime(self.timestr.get()))
        self.time_label.after(1000, self.update_time)
        
    def entry_enter(self):
        cmd = self.cmd_entry.get().strip()
        self.cmd_entry.delete(0, tk.END)
        if cmd:
            if self.SELFECHO.get():
                self.terminal_output.config(state=tk.NORMAL)
                self.terminal_output.insert(tk.END, f"{self.whereami.replace(os.getlogin(), "*")} ~$ {cmd}\n")
                self.terminal_output.config(state=tk.DISABLED)
            if not self.ALWAYSECHO.get():
                self.exec_cmd(cmd)
            else:
                self.exec_cmd(f"sys: echo {cmd}" if self.SYSCHECK.get() else f"echo {cmd}")

    def ins_txt(self, text: str, total_time=2):
        if not text:
            return
        
        current_typing_state = self.TYPING_ABLE.get()
        if not current_typing_state:
            self.terminal_output.config(state=tk.NORMAL)
            self.terminal_output.insert(tk.END, text)
            self.terminal_output.config(state=tk.DISABLED)
            self.terminal_output.see(tk.END)
            return
        
        original_return_bind = self.cmd_entry.bind("<Return>")
        self.cmd_entry.unbind("<Return>")
        
        typing_interrupted = [False]
        min_interval = 0.01
        char_count = len(text)
        interval = max(total_time / char_count, min_interval)
        
        def end_typing(event=None):
            typing_interrupted[0] = True
            return "break"
        
        bind_id = self.root.bind("<Control-c>", end_typing, add='+')
        
        def insert_next_char(index=0):
            nonlocal bind_id, original_return_bind
            
            if typing_interrupted[0]:
                self.terminal_output.config(state=tk.NORMAL)
                self.terminal_output.insert(tk.END, text[index:])
                self.terminal_output.config(state=tk.DISABLED)
            elif index < char_count:
                self.terminal_output.config(state=tk.NORMAL)
                self.terminal_output.insert(tk.END, text[index])
                self.terminal_output.config(state=tk.DISABLED)
                self.terminal_output.see(tk.END)
                self.root.after(int(interval * 100), insert_next_char, index + 1)
            else:
                if bind_id is not None:
                    self.cmd_entry.bind("<Return>", original_return_bind)
                    self.root.unbind("<Control-c>", bind_id)
                    bind_id = None
                return
            
            if (index == char_count - 1 or typing_interrupted[0]) and bind_id is not None:
                self.cmd_entry.bind("<Return>", original_return_bind)
                self.root.unbind("<Control-c>", bind_id)
                bind_id = None
                self.terminal_output.see(tk.END)
        
        insert_next_char()


    def exec_cmd(self, cmd):
        clears = ["clear", "cls", "clearscreen"]
        exits = ["exit", "quit", "bye"]
        
        if not cmd:
            return
        if cmd in clears:
            self.terminal_output.config(state=tk.NORMAL)
            self.terminal_output.delete(1.0, tk.END)
            self.terminal_output.config(state=tk.DISABLED)
            return
        if cmd in exits:
            self.root.destroy()
        
        if re.match(r"^help.*?", cmd):
            self.ins_txt(self.help_cmd(cmd))
            self.terminal_output.see(tk.END)
        
        elif re.match(r"^check (\d+\.){3}\d+\[((\d+)?(:\d+)?(-\d+)?(~\d+)?(,)?)*?(\d+)?\]( --maxworkers=\d+)?( -m=\d+)?( --timeout=\d+(\.\d+)?)?( -t=\d+(\.\d+)?)?$", cmd):
            self.thread = threading.Thread(target=self.run_check, args=(cmd,))
            self.thread.daemon = True
            self.thread.start()
            self.terminal_output.see(tk.END)
        
        elif cmd == "check --default" or cmd == "check -d":
            self.thread = threading.Thread(target=self.run_check, args=(cmd,))
            self.thread.daemon = True
            self.thread.start()
            self.terminal_output.see(tk.END)

        elif cmd == "savehistory":
            self.thread = threading.Thread(target=self.run_save)
            self.thread.daemon = True
            self.thread.start()
        
        elif re.match(r"^sql .*? (--params=(\[)?.*?(\])?)?(-pr=(\[)?.*?(\])?)?(--payloads=(\[)?.*?(\])?)?(-pld=(\[)?.*?(\])?)?$", cmd):
            self.thread = threading.Thread(target=self.run_sql, args=(cmd,))
            self.thread.daemon = True
            self.thread.start()
            self.terminal_output.see(tk.END)
        
        elif cmd == "nonsyscheck":
            if self.SYSCHECK.get():
                self.SYSCHECK.set(False)
                self.ins_txt("/// SYSCHECK DISABLED - syscheck disabled\n")
            else:
                self.ins_txt("/// SYSCHECK IS disabled - no need to disable\n")
        
        elif cmd == "onsyscheck":
            if not self.SYSCHECK.get():
                self.SYSCHECK.set(True)
                self.ins_txt("/// SYSCHECK ENABLED - syscheck enabled\n")
            else:
                self.ins_txt("/// SYSCHECK IS enabled - no need to enable\n")


        elif (cmd.startswith("sys:") if self.SYSCHECK.get() else True):
            origin_cmd = cmd[4:].strip() if self.SYSCHECK.get() else cmd

            if origin_cmd.lower() == "echo off":
                if self.SELFECHO.get():
                    self.SELFECHO.set(False)
                    self.ins_txt("/// ECHO OFF - echo if off\n")
                else:
                    self.ins_txt("/// ECHO IS off - no need to turn off\n")
                return

            elif origin_cmd.lower() == "echo on":
                if not self.SELFECHO.get():
                    self.SELFECHO.set(True)
                    self.ins_txt("/// ECHO ON - echo if on\n")
                else:
                    self.ins_txt("/// ECHO IS on - no need to turn on\n")
                return
            
            if origin_cmd.lower() == "echo":
                self.ins_txt(f"/// ECHO is {'on' if self.SELFECHO.get() else 'off'}\n")
                return
            
            if origin_cmd.startswith("echo "):
                self.ins_txt(f"{origin_cmd[5:]}\n")
                return

            cmd_parser = SysCommandParse(origin_cmd.strip(), self.whereami)
            if cmd_parser.error:
                self.ins_txt(f"{cmd_parser.error}\n")
            elif cmd_parser.non_return:
                pass
            else:
                self.ins_txt(f"{cmd_parser.result}\n")
            if cmd_parser.new_whereami != self.whereami:
                self.whereami = cmd_parser.new_whereami
                self.ins_txt(f"CD: {self.whereami}\n")
            self.terminal_output.see(tk.END)
            return
        
        else:
            self.ins_txt(f"Invalid Command: {cmd}\n")
    
    @staticmethod
    def help_cmd(cmd):
        if cmd == "help":
            return(
            "help command usage: help (command name)\n\n"
            "commands:\n"
            "    1. help - show this help message\n"
            "    2. clear/cls/clearscreen - clear the terminal output\n"
            "    3. exit/quit/bye - close the terminal\n"
            "    4. check - scan ports with slower speed\n"
            "    5. scan - scan ports with faster speed (nmap)\n"
            "    6. sql - inject sql\n"
            "    7. sys: - run system command\n"
            )
        elif cmd.startswith("help (") or cmd.startswith("help("):
            help_cmd = cmd.split("(")[-1].split(")")[0]
            match help_cmd:
                case "check":
                    return (
                    "check command usage: check xxx.xxx.xxx.xxx[ports] <--maxworkers=> <-m=> <--timeout=> <-t=>\n"
                    "--maxworkers= / -m= -> max workers to scan ports\n"
                    "--timeout= / -t= -> timeout for each port\n\n"
                    "example:\n"
                    "    check 127.0.0.1[22,23,25,80,443] --maxworkers=50 --timeout=1\n"
                    "    check 127.0.0.1[:1000,1001-1005,10000] -m=2000 -t=0.5\n"
                    )
                case "sql":
                    return (
                    "sql command usage: sql <url> <--params=> <-pr=> <--payloads=> <-pld=>\n"
                    "--params= / -pr= -> params to use in sql injection\n"
                    "--payloads= / -pld= -> payloads to use in sql injection\n\n"
                    "example:\n"
                    "    sql \"http://testphp.vulnweb.com/artists.php\" --params=[\"id\"] --payloads=[\"' or 1='1\"]\n"
                    "    sql \"http://testphp.vulnweb.com/artists.php\" -pr=id -pld=\"' or 1='1\"\n"
                    )
                case "sys:":
                    return (
                    "System command usage: sys: <command>\n"
                    "run system command\n\n"
                    "example:\n"
                    "    sys: cd..\n"
                    "    sys: ipconfig\n"
                    )
                case "sys":
                    return (
                    "System command usage: sys: <command>\n"
                    "run system command\n\n"
                    "example:\n"
                    "    sys cd..\n"
                    "    sys ipconfig\n"
                    )

    def add_dot(self, marker_pos: str):
        if self.dots['running']:
            self.terminal_output.config(state=tk.NORMAL)
            self.terminal_output.insert(marker_pos + f"+{self.dots['count']}c", ".")
            self.terminal_output.config(state=tk.DISABLED)
            self.terminal_output.see(tk.END)
            self.dots['count'] += 1
            self.root.after(1000, lambda: self.add_dot(marker_pos))
    
    @staticmethod
    def scan(cmd):
        # TODO: use nmap to scan ports
        pass

    def run_check(self, cmd):
        start_time = datetime.now()
        self.terminal_output.config(state=tk.NORMAL)
        self.terminal_output.insert(tk.END, "Check")
        self.terminal_output.see(tk.END)
        marker_pos = self.terminal_output.index(tk.END)
        self.terminal_output.config(state=tk.DISABLED)
        
        self.dots = {
            'count': 0,
            'running': True
        }
        
        self.root.after(0, lambda: self.add_dot(marker_pos))
        
        try:
            result = self.check(cmd)
        except Exception as e:
            result = str(e)
        finally:
            end_time = datetime.now()
            elapsed = (end_time - start_time).total_seconds()
            elapsed_str = f" {int(elapsed)}s" if elapsed.is_integer() else f" {elapsed:.1f}s"
            
            self.dots['running'] = False
            self.terminal_output.config(state=tk.NORMAL)
            self.terminal_output.insert(marker_pos + f"+{self.dots['count']}c", elapsed_str + "\n")
            self.terminal_output.config(state=tk.DISABLED)
            
            self.terminal_output.after(0, lambda: self.ins_txt(f"{result}\n"))
            self.terminal_output.after(0, lambda: self.terminal_output.see(tk.END))

    @staticmethod
    def check(cmd):
        if any([int(num) > 65535 for num in re.findall(r"\d+", cmd)]):
            return "Error: Port number must be between 0 and 65535."
        if not cmd == "check --default" and not cmd == "check -d":
            command = cmd.split("check ")[-1]
            ip, part2 = command.split("[")
            ports, args = part2.split("]")
            pts = ports.split(",")
            checking = []
        else:
            ip = "127.0.0.1"
            pts = [":65535"]
            checking = []
            args = []
        def _check(port: str) -> list | int:
            tokens = ["-", "~", ":"]
            if port.isdigit():
                return int(port)
            try:
                for token in tokens:
                    if token in port:
                        parts = port.split(token)
                        start = parts[0] if parts[0] else "1"
                        end = parts[1] if len(parts) > 1 and parts[1] else start
                        return list(range(int(start), int(end) + 1))
            except:
                return None
        for port in pts:
            p = _check(port)
            if p:
                if isinstance(p, list):
                    checking.extend(p)
                else:
                    checking.append(p)
        
        max_workers = 2000 if cmd == "check --default" or cmd == "check -d" else 50
        timeout = 0.5 if cmd == "check --default" or cmd == "check -d" else 1
        if args:
            args = args[1:].split(" ")
            for arg in args:
                if arg.startswith("--maxworkers=") or arg.startswith("-m="):
                    max_workers = int(arg.split("=")[-1])
                elif arg.startswith("--timeout=") or arg.startswith("-t="):
                    timeout = float(arg.split("=")[-1])

        
        
        
        port_status = check_port(ip, checking, max_workers=max_workers, timeout=timeout)
        result = [(p, "OPEN") for p, pb in port_status.items() if pb]
        rtn = f"{len(result)} OPEN PORTS FOUND at IP: {ip}\n"
        rtn += "  PORT  |  STATUS  "
        for port, status in result:
            rtn += f"\n{port:^8}|   {status}   "
        if len(result) == 0:
            rtn = "No OPEN ports found."
        return rtn

    def run_sql(self, cmd):
        start_time = datetime.now()
        self.terminal_output.config(state=tk.NORMAL)
        self.terminal_output.insert(tk.END, "SQL Analyzing")
        self.terminal_output.see(tk.END)
        marker_pos = self.terminal_output.index(tk.END)
        self.terminal_output.config(state=tk.DISABLED)
        
        self.dots = {
            'count': 0,
            'running': True
        }
        
        self.root.after(0, lambda: self.add_dot(marker_pos))
        
        try:
            result = self.sql(cmd)
        except Exception as e:
            result = str(e)
        finally:
            end_time = datetime.now()
            elapsed = (end_time - start_time).total_seconds()
            elapsed_str = f" {int(elapsed)}s" if elapsed.is_integer() else f" {elapsed:.1f}s"
            
            self.dots['running'] = False
            self.terminal_output.config(state=tk.NORMAL)
            self.terminal_output.insert(marker_pos + f"+{self.dots['count']}c", elapsed_str + "\n")
            self.terminal_output.config(state=tk.DISABLED)
            
            self.terminal_output.after(0, lambda: self.ins_txt(f"{result}\n"))
            self.terminal_output.after(0, lambda: self.terminal_output.see(tk.END))
    
    @staticmethod
    def sql(cmd):
        command = cmd.split("sql ")[-1]
        
        url_match = re.search(r'^"([^"]+)"|\'([^\']+)\'|(\S+)', command)
        if not url_match:
            return "Error: Invalid URL format"
        
        url = url_match.group(1) or url_match.group(2) or url_match.group(3)
        
        params = []
        payloads = []
        
        params_match = re.search(r'(?:--params=|-pr=)(\[[^\]]+\]|"[^"]+"|\'[^\']+\'|\S+)', command)
        if params_match:
            params_str = params_match.group(1)
            if params_str.startswith('[') and params_str.endswith(']'):
                params_str = params_str[1:-1]
            elif params_str.startswith('"') and params_str.endswith('"'):
                params_str = params_str[1:-1]
            elif params_str.startswith("'") and params_str.endswith("'"):
                params_str = params_str[1:-1]
            
            params = [p.strip() for p in params_str.split(',') if p.strip()]
        
        payloads_match = re.search(r'(?:--payloads=|-pld=)(\[[^\]]+\]|"[^"]+"|\'[^\']+\'|\S+)', command)
        if payloads_match:
            payloads_str = payloads_match.group(1)
            if payloads_str.startswith('[') and payloads_str.endswith(']'):
                payloads_str = payloads_str[1:-1]
            elif payloads_str.startswith('"') and payloads_str.endswith('"'):
                payloads_str = payloads_str[1:-1]
            elif payloads_str.startswith("'") and payloads_str.endswith("'"):
                payloads_str = payloads_str[1:-1]
            
            payloads = [p.strip() for p in payloads_str.split(',') if p.strip()]
        
        if not params:
            return "Error: No parameters specified"
        if not payloads:
            return "Error: No payloads specified"
        
        try:
            result = readable_sqltest_report(url, params, *payloads)
            return result
        except Exception as e:
            return f"Error executing SQL test: {str(e)}"
    
    def run_save(self):
        self.terminal_output.config(state=tk.NORMAL)
        self.terminal_output.insert(tk.END, "Saving")
        self.terminal_output.see(tk.END)
        marker_pos = self.terminal_output.index(tk.END)
        self.terminal_output.config(state=tk.DISABLED)
        
        self.dots = {
            'count': 0,
            'running': True
        }
        
        self.root.after(0, lambda: self.add_dot(marker_pos))

        self.save_history()
        self.dots['running'] = False

    def save_history(self):
        filename = os.path.join(os.path.dirname(__file__), datetime.now().strftime("%Y%m%d%H%M%S_History") + ".txt")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(self.terminal_output.get("1.0", tk.END))
            f.write(f"\n{datetime.now().strftime(self.timestr.get())}")
        self.terminal_output.config(state=tk.NORMAL)
        self.terminal_output.insert(tk.END, f"\nSaved to \\{filename}\n")
        self.terminal_output.config(state=tk.DISABLED)
        self.terminal_output.after(0, lambda: self.terminal_output.see(tk.END))

class SysCommandParse:
    def __init__(self, cmd: str, whereami: str):
        self.cmd = cmd
        self.whereami = whereami
        self.non_return = False
        self.result = None
        self.new_whereami = whereami
        self.error = None
        self.parse()
    
    def parse(self):
        if self.cmd == "cd":
            self.new_whereami = os.path.expanduser("~")
            self.non_return = True
            return
        if self.cmd == "cd.":
            self.non_return = True
            return
        if self.cmd == "cd..":
            self.cmd = "cd .."
        if self.cmd == "cd ..":
            if re.match(r"^[A-Z]:\\$", self.whereami) or re.match(r"^/home/$", self.whereami):
                self.result = "CD: Non master dir - \"..\""
                return
        
        if self.cmd.startswith("cd "):
            target = self.cmd[3:].strip()
            if os.path.isabs(target):
                self.new_whereami = target
            else:
                self.new_whereami = os.path.join(self.whereami, target)
            self.new_whereami = os.path.normpath(self.new_whereami)
            if not os.path.exists(self.new_whereami):
                self.error = f"CDError: Dir not found - \"{self.new_whereami.replace(os.getlogin(), "*")}\""
                self.new_whereami = self.whereami
            else:
                self.non_return = True
            return
        
        elif self.cmd == "ls":
            try:
                items = os.listdir(self.whereami)
                self.result = f"/// {self.whereami.replace(os.getlogin(), "*")}\n"
                self.result += "ITEM                    |TYPE    |SIZE        \n"
                for item in items:
                    size = int(os.stat(os.path.join(self.whereami, item)).st_size)
                    if size == 0: size = "EMPTY"
                    elif size >= 1024: size = f"{size / 1024:.2f} KB"
                    elif size >= 1024 * 1024: size = f"{size / (1024 * 1024):.2f} MB"
                    elif size >= 1024 * 1024 * 1024: size = f"{size / (1024 * 1024 * 1024):.2f} GB"
                    else: size = f"{size} BYTES"
                    isdir = "DIR " if os.path.isdir(os.path.join(self.whereami, item)) else "FILE"

                    self.result += (f"\n{item:<24}|{isdir:<8}|{size}\n")
            except Exception as e:
                self.error = f"LSError: {str(e)}"
                return
        
        elif self.cmd.startswith("cat "):
            file = os.path.join(self.whereami, self.cmd[4:].strip())
            self.result = f"/// {file.replace(os.getlogin(), "*")}\n"
            formats = [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".wav", ".mp3", ".mp4", ".ini", ".lnk"]
            try:
                if not os.path.exists(file):
                    self.error = f"CATError: File not found - \"{self.cmd[4:].strip().replace(os.getlogin(), "*")}\""
                    return
                for hint in formats:
                    if file.endswith(hint):
                        self.result += Path(file).read_bytes()
                        return
                content = Path(file).read_text(encoding="utf-8")
                self.result += content
            except Exception as e:
                self.error = f"CATError: {str(e)}"
                return
        
        elif self.cmd.startswith("rm "):
            file = os.path.join(self.whereami, self.cmd[3:].strip())
            try:
                os.remove(file)
                self.result = f"/// {file.replace(os.getlogin(), "*")} removed"
            except Exception as e:
                self.error = f"RMError: {str(e)}"
                return
        
        elif self.cmd.startswith("del "):
            file = os.path.join(self.whereami, self.cmd[4:].strip())
            try:
                os.remove(file)
                self.result = f"/// {file.replace(os.getlogin(), "*")} deleted"
            except Exception as e:
                self.error = f"DELError: {str(e)}"
                return
        
        elif self.cmd.startswith("mkdir "):
            dir = os.path.join(self.whereami, self.cmd[6:].strip())
            try:
                os.mkdir(dir)
                self.result = f"/// {dir.replace(os.getlogin(), "*")} created"
            except Exception as e:
                self.error = f"MKDIRError: {str(e)}"
                return
        
        elif self.cmd.startswith("touch "):
            file = os.path.join(self.whereami, self.cmd[6:].strip())
            try:
                with open(file, "w") as f:
                    f.write("")
                self.result = f"/// {file.replace(os.getlogin(), "*")} created"
            except Exception as e:
                self.error = f"TOUCHError: {str(e)}"
                return
        
        else:
            try:
                cmds = self.cmd.split(" ")
                self.result = subprocess.run(cmds,
                                             cwd=self.whereami, 
                                             check=True, 
                                             capture_output=True, 
                                             text=True).stdout
            except Exception as e:
                self.error = f"CMDError: {str(e)}"
                return
            

if __name__ == "__main__":
    terminal = Terminal()
