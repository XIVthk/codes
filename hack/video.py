import tkinter as tk
from tkinter import ttk
import sys

class Story:
    def __init__(self):
        self.root = tk.Tk()

        self.TYPING_ABLE = tk.BooleanVar(value=True)
        
        self.root.option_add("*Font", "Consolas 10")
        self.root.option_add("*Background", "#000000")
        self.root.option_add("*Foreground", "#00BFFF")

        self.setup_win()

    
    def setup_win(self):
        self.root.geometry("1200x800")
        self.root.attributes("-fullscreen", True)
        self.root.bind("<Escape>", lambda e: self.root.attributes("-fullscreen", False))
        self.root.bind("<F11>", lambda e: self.toggle_fullscreen())
        self.root.configure(bg="#000000")
        self.root.resizable(True, True)
        
        self.fix_platform_styles()
        
        self.setup_style()
        self.basic_widgits()
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
        
        style.configure("Dark.TFrame", 
                       background="#000000")
        
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

    
    def basic_widgits(self):
        
        self.main_frame = ttk.Frame(self.root, style="Dark.TFrame")
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        self.terminal_container = ttk.Frame(self.main_frame, style="Dark.TFrame")
        self.terminal_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
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
        
        self.cmd_entry = ttk.Entry(
            self.cmd_frame,
            style="Terminal.TEntry",
            font=("Consolas", 14)
        )
        self.cmd_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
        self.cmd_entry.focus_set()
        
        self.cmd_entry.bind("<Return>", lambda e: self.entry_enter())
        
    def entry_enter(self):
        cmd = self.cmd_entry.get().strip()
        self.cmd_entry.delete(0, tk.END)
        self.terminal_output.config(state=tk.NORMAL)
        self.ins_txt(f"{cmd[5:]}\n")
        self.terminal_output.config(state=tk.DISABLED)

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
                if text[index] == "\n":
                    self.root.after(1200, insert_next_char, index + 1)
                else:
                    self.root.after(int(interval * 900), insert_next_char, index + 1)
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

if __name__ == "__main__":
    story = Story()
