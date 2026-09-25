# desktop.py
from datetime import datetime
import tkinter as tk
from tkinter import ttk


class VirtualDesktop:
    def __init__(self):
        self.root = tk.Tk()
        self.start_menu_visible = False
        self.setup_window()
    
    def setup_window(self):
        self.root.attributes("-fullscreen", True)
        
        self.setup_style()
        self.setup_desktop()
        self.setup_taskbar()
        self.setup_widgets()
        self.root.mainloop()
    
    def setup_style(self):
        self.style = ttk.Style()
        self.style.theme_use("alt")

        self.style.configure("Taskbar.TFrame", background="gray")

        self.style.configure("DarkButton.TButton",
                             background="#2A2A2A",
                             foreground="#00BFFF",
                             borderwidth=0,
                             highlightthickness=0,
                             padding=5,
                             font=("Consolas", 11))
        
        self.style.map("DarkButton.TButton", 
                  background=[('active', '#2A2A2A'), ('pressed', '#1A1A1A')],
                  foreground=[('active', "#1E90FF"), ('pressed', "#00FFFF")]
        )
    
    def setup_desktop(self):
        self.canvas = tk.Canvas(self.root, bg="black", borderwidth=0, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

    def setup_taskbar(self):
        self.taskbar = tk.Frame(self.root, bg="#2A2A2A", height=40, borderwidth=0, highlightthickness=0)
        self.taskbar.pack(side=tk.BOTTOM, fill=tk.X)

        self.start_btn = ttk.Button(self.taskbar, text="START", style="DarkButton.TButton", 
                                   width=8, takefocus=False, command=self.toggle_start_menu)
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.clock = tk.Label(self.taskbar, bg="#2A2A2A", fg="white", font=("Consolas", 12))
        self.clock.pack(side=tk.RIGHT)
        self.update_clock()

    def setup_widgets(self):
        """Placeholder for desktop icons/widgets"""
        pass

    def update_clock(self):
        now = datetime.now()
        self.clock.config(text=now.strftime("%H:%M\n%Y/%m/%d"))
        self.root.after(1000, self.update_clock)
    
    def toggle_start_menu(self):
        if self.start_menu_visible:
            self.close_start_menu()
        else:
            self.show_start_menu()
    
    def show_start_menu(self):
        self.start_menu_visible = True
        self.start_menu = tk.Frame(self.canvas, bg="#2A2A2A", height=700, width=500, 
                                   borderwidth=0, highlightthickness=0)
        self.start_menu.place(relx=0, rely=1, anchor=tk.SW)
        self.draw_start_menu()
    
    def draw_start_menu(self):
        self.shutdown_btn = ttk.Button(self.start_menu, text="SHUTDOWN", 
                                      style="DarkButton.TButton", width=8, 
                                      takefocus=False, command=self.shutdown)
        self.shutdown_btn.pack(side=tk.BOTTOM, padx=5, pady=5)
        
        # 可以在这里添加更多开始菜单内容
        # 比如：程序列表、最近文档等

    def close_start_menu(self):
        self.start_menu_visible = False
        self.start_menu.place_forget()

    def shutdown(self):
        self.root.destroy()


if __name__ == "__main__":
    VirtualDesktop()