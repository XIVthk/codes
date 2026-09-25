# window_manager.py
import tkinter as tk
from tkinter import ttk

class WindowManager:
    def __init__(self, root):
        self.root = root
        self.windows = {}
    
    def create_window(self, name, title, geometry, widget_type, **kwargs):
        if name in self.windows:
            self.close_window(name)
        
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry(geometry)
        win.configure(bg='black')
        win.transient(self.root)
        win.withdraw()
        
        widget = None
        callback = kwargs.get('callback')
        
        if widget_type == 'text':
            widget = self._create_text(win)
        elif widget_type == 'entry':
            widget = self._create_entry(win, kwargs.get('label', ''), kwargs.get('button_text', '确认'), callback)
        elif widget_type == 'button':
            widget = self._create_buttons(win, kwargs.get('options', []), callback)
        elif widget_type == 'progress':
            widget = self._create_progress(win, kwargs.get('label', '处理中...'))
        elif widget_type == 'label':
            widget = self._create_label(win, kwargs.get('text', ''))
        else:
            widget = tk.Frame(win, bg='black')
            widget.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.windows[name] = {
            'window': win,
            'widget': widget,
            'type': widget_type
        }
        
        win.update_idletasks()
        return win
    
    def _create_text(self, parent):
        """创建只读 Text"""
        text = tk.Text(
            parent, bg='black', fg='white',
            font=('Consolas', 10),
            wrap='char',
            relief='flat',
            highlightthickness=0,
            borderwidth=0,
            state='disabled'
        )
        text.pack(fill='both', expand=True, padx=10, pady=10)
        return text
    
    def _create_entry(self, parent, label_text, button_text, callback):
        frame = tk.Frame(parent, bg='black')
        frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        label = tk.Label(frame, text=label_text, fg='white', bg='black',
                         font=('Consolas', 11))
        label.pack(pady=(20, 10))
        
        entry = tk.Entry(frame, bg='black', fg='white',
                         font=('Consolas', 10),
                         insertbackground='white',
                         relief='flat', highlightthickness=1,
                         highlightcolor='white', highlightbackground='white')
        entry.pack(fill='x', pady=10)
        entry.focus_set()
        
        def on_confirm():
            value = entry.get().strip()
            if callback:
                callback(value)
        
        btn = tk.Label(frame, text=f'[ {button_text} ]', fg='white', bg='black',
                       font=('Consolas', 10), cursor='hand2')
        btn.pack(pady=10)
        btn.bind('<Enter>', lambda e: btn.config(fg='black', bg='white'))
        btn.bind('<Leave>', lambda e: btn.config(fg='white', bg='black'))
        btn.bind('<Button-1>', lambda e: on_confirm())
        entry.bind('<Return>', lambda e: on_confirm())
        
        return {'frame': frame, 'entry': entry, 'button': btn}
    
    def _create_buttons(self, parent, options, callback):
        frame = tk.Frame(parent, bg='black')
        frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        widgets = []
        for opt in options:
            btn = tk.Label(frame, text=f'[ {opt} ]', fg='white', bg='black',
                           font=('Consolas', 10), cursor='hand2')
            btn.pack(pady=5)
            btn.bind('<Enter>', lambda e, b=btn: b.config(fg='black', bg='white'))
            btn.bind('<Leave>', lambda e, b=btn: b.config(fg='white', bg='black'))
            btn.bind('<Button-1>', lambda e, o=opt: callback(o) if callback else None)
            widgets.append(btn)
        
        return {'frame': frame, 'buttons': widgets}
    
    def _create_progress(self, parent, label_text):
        frame = tk.Frame(parent, bg='black')
        frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        label = tk.Label(frame, text=label_text, fg='white', bg='black',
                         font=('Consolas', 11))
        label.pack(pady=(20, 10))
        
        progress = ttk.Progressbar(frame, mode='indeterminate', length=300)
        progress.pack(pady=20)
        progress.start(50)
        
        return {'frame': frame, 'progress': progress}
    
    def _create_label(self, parent, text):
        label = tk.Label(parent, text=text, fg='white', bg='black',
                         font=('Consolas', 14))
        label.pack(fill='both', expand=True, padx=10, pady=10)
        return label
    
    def close_window(self, name):
        if name in self.windows:
            self.windows[name]['window'].destroy()
            del self.windows[name]
    
    def show_window(self, name):
        if name in self.windows:
            self.windows[name]['window'].deiconify()
            self.windows[name]['window'].lift()
    
    def hide_window(self, name):
        if name in self.windows:
            self.windows[name]['window'].withdraw()
    
    def focus_window(self, name):
        if name in self.windows:
            self.windows[name]['window'].focus_force()
    
    def get_widget(self, name):
        if name in self.windows:
            return self.windows[name]['widget']
        return None
    
    def get_window(self, name):
        if name in self.windows:
            return self.windows[name]['window']
        return None
    
    def close_all(self):
        for name in list(self.windows.keys()):
            self.close_window(name)