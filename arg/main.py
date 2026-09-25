# main.py
import tkinter as tk
from tkinter import scrolledtext, font
import json
import os
import sys
import re

from terminal import TerminalEngine
from window_manager import WindowManager
from cases import case00

CASES = [case00]

class SystemPauseApp:
    def __init__(self, root):
        self.root = root
        self.root.title('System "pause"')
        self.root.geometry('800x600')
        self.root.configure(bg='black')
        self.root.resizable(True, True)
        
        self.settings_file = 'settings.json'
        self.load_settings()
        
        self.window_manager = WindowManager(root)
        
        self.container = tk.Frame(root, bg='black')
        self.container.pack(fill='both', expand=True)
        
        self.current_page = None
        self.terminal_engine = None
        
        self.show_main_menu()
    
    def load_settings(self):
        default = {
            'resolution': '800x600',
            'duck_enabled': True,
            'typing_speed': 40,
            'arg_mode': 'whatever',
            'arg_path': None
        }
        try:
            with open(self.settings_file, 'r') as f:
                self.settings = json.load(f)
        except:
            self.settings = default
            self.save_settings()
    
    def save_settings(self):
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f, indent=2)
    
    def clear_container(self):
        if self.current_page:
            self.current_page.destroy()
            self.current_page = None
    
    def switch_page(self, page_class, *args):
        self.clear_container()
        page = page_class(self.container, self, *args)
        page.pack(fill='both', expand=True)
        self.current_page = page
    
    def show_main_menu(self):
        self.switch_page(MainMenu)
    
    def show_settings(self):
        self.switch_page(SettingsPage)
    
    def start_game(self):
        """启动游戏"""
        self.switch_page(TerminalPage)
        self.current_page.load_case(CASES[0])
    
    def confirm_quit(self):
        def do_quit():
            self.close_dialog()
            self.window_manager.close_all()
            self.root.quit()
        self.show_custom_dialog(
            title='确认退出',
            message='当前进度将会被自动保存。',
            buttons=[('退出', do_quit), ('取消', lambda: self.close_dialog())]
        )
    
    def show_custom_dialog(self, title, message, buttons, width=400, height=160):
        overlay = tk.Frame(self.root, bg='black')
        overlay.place(x=0, y=0, relwidth=1, relheight=1)
        try:
            overlay.attributes('-alpha', 0.7)
        except:
            pass
        dialog = tk.Frame(overlay, bg='black', highlightbackground='white',
                          highlightcolor='white', highlightthickness=1)
        dialog.place(relx=0.5, rely=0.5, anchor='center', width=width, height=height)
        tk.Label(dialog, text=title, fg='white', bg='black',
                 font=('Consolas', 12, 'bold')).pack(pady=(15, 5))
        tk.Label(dialog, text=message, fg='white', bg='black',
                 font=('Consolas', 10), justify='center').pack(pady=(0, 15))
        btn_frame = tk.Frame(dialog, bg='black')
        btn_frame.pack()
        for text, cmd in buttons:
            btn = tk.Label(btn_frame, text=f'[ {text} ]', fg='white', bg='black',
                           font=('Consolas', 10), cursor='hand2')
            btn.pack(side='left', padx=15)
            btn.bind('<Enter>', lambda e, b=btn: b.config(fg='black', bg='white'))
            btn.bind('<Leave>', lambda e, b=btn: b.config(fg='white', bg='black'))
            btn.bind('<Button-1>', lambda e, c=cmd: c())
        self._current_dialog = overlay
    
    def close_dialog(self):
        if hasattr(self, '_current_dialog') and self._current_dialog:
            self._current_dialog.destroy()
            self._current_dialog = None


class MainMenu(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg='black')
        self.app = app
        
        sys_ascii = [
            "███████╗██╗   ██╗███████╗",
            "██╔════╝╚██╗ ██╔╝██╔════╝",
            "███████╗ ╚████╔╝ ███████╗",
            "╚════██║  ╚██╔╝  ╚════██║",
            "███████║   ██║   ███████║",
            "╚══════╝   ╚═╝   ╚══════╝"
        ]
        for i, line in enumerate(sys_ascii):
            lbl = tk.Label(self, text=line, fg='white', bg='black',
                           font=('Consolas', 16), justify='left')
            lbl.place(x=50, y=30 + i * 22)
        
        pause_lbl = tk.Label(self, text='"pause"', fg='white', bg='black',
                             font=('Consolas', 14))
        pause_lbl.place(x=50, y=30 + len(sys_ascii) * 22 + 10)
        
        menu_items = [
            ('Play', self.app.start_game),
            ('Settings', self.app.show_settings),
            ('Quit', self.app.confirm_quit)
        ]
        for idx, (text, cmd) in enumerate(menu_items):
            lbl = tk.Label(self, text=text, fg='white', bg='black',
                           font=('Consolas', 11), cursor='hand2')
            lbl.place(x=50, y=220 + idx * 30)
            lbl.bind('<Enter>', lambda e, l=lbl: l.config(fg='black', bg='white'))
            lbl.bind('<Leave>', lambda e, l=lbl: l.config(fg='white', bg='black'))
            lbl.bind('<Button-1>', lambda e, c=cmd: c())
        
        ver_lbl = tk.Label(self, text='v1.0  |  Windows 10+',
                           fg='#666666', bg='black',
                           font=('Consolas', 9))
        ver_lbl.place(x=50, y=420)


class SettingsPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg='black')
        self.app = app
        self.expanded_state = {}
        self.section_widgets = {}
        self.build_ui()
    
    def build_ui(self):
        y = 20
        back = tk.Label(self, text='< back', fg='white', bg='black',
                        font=('Consolas', 11), cursor='hand2')
        back.place(x=30, y=y)
        back.bind('<Enter>', lambda e: back.config(fg='black', bg='white'))
        back.bind('<Leave>', lambda e: back.config(fg='white', bg='black'))
        back.bind('<Button-1>', lambda e: self.app.show_main_menu())
        y += 50
        
        sections_data = [
            {'id': 'resolution', 'label': '分辨率 / Resolution',
             'options': ['800x600', '1024x768', '1280x720', '1366x768', '1920x1080'],
             'selected': self.app.settings.get('resolution', '800x600'), 'locked': False},
            {'id': 'duck', 'label': '启用鸭子 / Duck',
             'options': ['ON', 'OFF'],
             'selected': 'ON' if self.app.settings.get('duck_enabled', True) else 'OFF', 'locked': False},
            {'id': 'speed', 'label': '打字流速 / Typing Speed',
             'options': ['慢', '中', '快'],
             'selected': {80: '慢', 40: '中', 15: '快'}.get(self.app.settings.get('typing_speed', 40), '中'),
             'locked': False},
            {'id': 'language', 'label': '语言 / Language',
             'options': ['中文', 'English'], 'selected': '中文', 'locked': True},
            {'id': 'arg', 'label': 'ARG文件生成 / File Generation',
             'options': ['Whatever', 'Reject'],
             'selected': 'Reject' if self.app.settings.get('arg_mode') == 'reject' else 'Whatever',
             'locked': False}
        ]
        
        for section_data in sections_data:
            section_id = section_data['id']
            section_data['expanded'] = self.expanded_state.get(section_id, False)
            y = self.render_section(section_data, y)
        
        reset_btn = tk.Label(self, text='[ 恢复默认 ]', fg='white', bg='black',
                             font=('Consolas', 10), cursor='hand2')
        reset_btn.place(x=30, y=y + 10)
        reset_btn.bind('<Enter>', lambda e: reset_btn.config(fg='black', bg='white'))
        reset_btn.bind('<Leave>', lambda e: reset_btn.config(fg='white', bg='black'))
        reset_btn.bind('<Button-1>', lambda e: self.reset_defaults())
    
    def render_section(self, section_data, y):
        section_id = section_data['id']
        is_expanded = section_data.get('expanded', False)
        is_locked = section_data.get('locked', False)
        label = section_data['label']
        options = section_data['options']
        selected = section_data['selected']
        
        symbol = 'v' if is_expanded else '>'
        color = '#444444' if is_locked else 'white'
        title_lbl = tk.Label(self, text=f'{symbol} {label}', fg=color, bg='black',
                             font=('Consolas', 11), cursor='arrow' if is_locked else 'hand2')
        title_lbl.place(x=30, y=y)
        self.section_widgets[f'{section_id}_title'] = title_lbl
        y += 25
        
        sep_lbl = tk.Label(self, text='─────────────────────', fg='#333333', bg='black',
                           font=('Consolas', 10))
        sep_lbl.place(x=30, y=y)
        self.section_widgets[f'{section_id}_sep'] = sep_lbl
        y += 25
        
        option_widgets = []
        if is_expanded and not is_locked:
            for opt in options:
                is_selected = (opt == selected)
                opt_lbl = tk.Label(self, text=f'  {opt}', 
                                   fg='white' if is_selected else '#666666',
                                   bg='black', font=('Consolas', 10),
                                   cursor='hand2')
                opt_lbl.place(x=40, y=y)
                opt_lbl.bind('<Button-1>', lambda e, s=section_data, o=opt, l=opt_lbl: 
                             self.select_option(s, o, l))
                opt_lbl.bind('<Enter>', lambda e, l=opt_lbl, sel=is_selected: 
                             self.on_option_hover(l, True, sel))
                opt_lbl.bind('<Leave>', lambda e, l=opt_lbl, sel=is_selected: 
                             self.on_option_hover(l, False, sel))
                option_widgets.append(opt_lbl)
                y += 22
            
            if section_id == 'arg':
                mode = self.app.settings.get('arg_mode', 'whatever')
                path = self.app.settings.get('arg_path', '')
                if mode == 'whatever':
                    info = '文件将散布于系统各目录中。'
                else:
                    display_path = path if len(path) <= 30 else path[:27] + '...'
                    info = f'生成目录: {display_path}'
                info_lbl = tk.Label(self, text=f'  {info}', fg='#888888', bg='black',
                                    font=('Consolas', 9))
                info_lbl.place(x=40, y=y)
                option_widgets.append(info_lbl)
                y += 22
        
        self.section_widgets[f'{section_id}_options'] = option_widgets
        self.section_widgets[f'{section_id}_data'] = section_data
        
        if not is_locked:
            title_lbl.bind('<Button-1>', lambda e, sid=section_id: self.toggle_section(sid))
        
        return y + 10
    
    def on_option_hover(self, label, enter, was_selected):
        if enter:
            label.config(fg='black', bg='white')
        else:
            if was_selected:
                label.config(fg='white', bg='black')
            else:
                label.config(fg='#666666', bg='black')
    
    def toggle_section(self, section_id):
        self.expanded_state[section_id] = not self.expanded_state.get(section_id, False)
        data = self.section_widgets.get(f'{section_id}_data')
        if data:
            data['expanded'] = self.expanded_state[section_id]
            title_lbl = self.section_widgets.get(f'{section_id}_title')
            if title_lbl:
                symbol = 'v' if self.expanded_state[section_id] else '>'
                title_lbl.config(text=f'{symbol} {data["label"]}')
        self.redraw()
    
    def redraw(self):
        for widget in self.winfo_children():
            widget.destroy()
        self.build_ui()
    
    def select_option(self, section_data, option, label):
        section_id = section_data['id']
        
        if section_id == 'duck' and option == 'OFF':
            current = self.app.settings.get('duck_enabled', True)
            if current:
                self.app.show_custom_dialog(
                    title='⚠ 警告',
                    message='关闭这个选项会让游戏变得极其难！\n确实要关闭？',
                    buttons=[
                        ('是', lambda: self.confirm_duck_off()),
                        ('否', lambda: self.app.close_dialog())
                    ]
                )
                return
        
        if section_id == 'arg' and option == 'Reject':
            current_mode = self.app.settings.get('arg_mode', 'whatever')
            if current_mode != 'reject':
                self.app.show_custom_dialog(
                    title='⚠ 警告',
                    message='所有 ARG 文件将生成在您指定的目录中。\n这将降低游戏体验，部分沉浸感将丢失。',
                    buttons=[
                        ('选择目录', lambda: self.select_arg_directory()),
                        ('取消', lambda: self.app.close_dialog())
                    ]
                )
                return
        
        self.apply_option(section_id, option)
    
    def apply_option(self, section_id, option):
        if section_id == 'resolution':
            self.app.settings['resolution'] = option
            self.app.root.geometry(option)
        elif section_id == 'duck':
            self.app.settings['duck_enabled'] = (option == 'ON')
        elif section_id == 'speed':
            speed_map = {'慢': 80, '中': 40, '快': 15}
            self.app.settings['typing_speed'] = speed_map.get(option, 40)
        elif section_id == 'arg':
            mode = 'whatever' if option == 'Whatever' else 'reject'
            self.app.settings['arg_mode'] = mode
            if mode == 'whatever':
                self.app.settings['arg_path'] = None
        self.app.save_settings()
        self.redraw()
    
    def confirm_duck_off(self):
        self.app.close_dialog()
        self.app.settings['duck_enabled'] = False
        self.app.save_settings()
        self.redraw()
    
    def select_arg_directory(self):
        self.app.close_dialog()
        from tkinter import filedialog
        dir_path = filedialog.askdirectory(title="选择 ARG 文件生成目录")
        if dir_path:
            self.app.settings['arg_mode'] = 'reject'
            self.app.settings['arg_path'] = dir_path
            self.app.save_settings()
            self.redraw()
        else:
            self.app.settings['arg_mode'] = 'whatever'
            self.app.settings['arg_path'] = None
            self.app.save_settings()
            self.redraw()
    
    def reset_defaults(self):
        self.app.settings = {
            'resolution': '800x600',
            'duck_enabled': True,
            'typing_speed': 40,
            'arg_mode': 'whatever',
            'arg_path': None
        }
        self.app.save_settings()
        self.app.root.geometry('800x600')
        self.redraw()


class TerminalPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg='black')
        self.app = app
        
        self.terminal_text = tk.Text(
            self, bg='black', fg='white',
            font=('Consolas', 10),
            insertbackground='white',
            wrap='char',
            relief='flat',
            highlightthickness=0,
            borderwidth=0,
            state='normal'
        )
        self.terminal_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.terminal_text.bind('<Return>', self.on_enter)
        self.terminal_text.bind('<BackSpace>', self.on_backspace)
        self.terminal_text.bind('<Key>', self.on_key)
        
        self.input_start_index = None
        self.prompt = "> "
        self.input_callback = None
        self.pending_input = False
        
        self.char_queue = []
        self.typing_timer = None
        self.typing_speed = self.app.settings.get('typing_speed', 40)
        self.is_typing = False
        
        self.subterm_queue = []
        self.subterm_typing_timer = None
        self.subterm_is_typing = False
        self.subterm_text = None
        self.subterm_pending = []
        
        self.command_history = []
        self.history_index = -1
        self.history_temp = ""
        
        self.tab_matches = []
        self.tab_index = -1
        self.tab_base = ""
        
        self.terminal = TerminalEngine(
            output_callback=self.out,
            input_callback=self.get_input,
            subterm_callback=self.subterm_out
        )
        self.terminal.set_window_manager(app.window_manager)
        
        self.after(100, self.init_terminal)
    
    def set_subterm_text(self, text_widget):
        self.subterm_text = text_widget
        if self.subterm_pending:
            for text, style in self.subterm_pending:
                self._subterm_out_immediate(text, style)
            self.subterm_pending.clear()
    
    def init_terminal(self):
        pass
    
    def out(self, text, style=None):
        if not text.endswith("\n"):
            text += "\n"
        fragments = self._parse_tags(text)
        for frag_text, frag_style in fragments:
            if frag_text:
                self.char_queue.append(('fragment', frag_text, frag_style))
        if not self.is_typing:
            self._type_next_char()
    
    def subterm_out(self, text, style=None):
        if self.app.window_manager:
            widget = self.app.window_manager.get_widget('subterm')
            if widget:
                self.subterm_text = widget
                # 如果窗口还没显示，先显示
                if not self.app.window_manager.get_window('subterm').winfo_ismapped():
                    self.app.window_manager.show_window('subterm')
        
        if self.subterm_text is None:
            self.subterm_pending.append((text, style))
            return
        
        if self.subterm_pending:
            for pending_text, pending_style in self.subterm_pending:
                self._subterm_out_immediate(pending_text, pending_style)
            self.subterm_pending.clear()
        
        self._subterm_out_immediate(text, style)
    
    def _subterm_out_immediate(self, text, style=None):
        if not self.subterm_text:
            return
        if not text.endswith("\n"):
            text += "\n"
        fragments = self._parse_tags(text)
        for frag_text, frag_style in fragments:
            if frag_text:
                self.subterm_queue.append(('fragment', frag_text, frag_style))
        if not self.subterm_is_typing:
            self._subterm_type_next_char()
    
    def _parse_tags(self, text):
        import re
        fragments = []
        current_style = None
        current_text = ""
        pattern = r'(</?[bB]>|</?[iI]>|<color=[^>]+>|</color>)'
        parts = re.split(pattern, text)
        for part in parts:
            if not part:
                continue
            if part == '<b>' or part == '<B>':
                if current_text:
                    fragments.append((current_text, current_style))
                    current_text = ""
                current_style = 'bold'
            elif part == '</b>' or part == '</B>':
                if current_text:
                    fragments.append((current_text, current_style))
                    current_text = ""
                current_style = None
            elif part == '<i>' or part == '<I>':
                if current_text:
                    fragments.append((current_text, current_style))
                    current_text = ""
                current_style = 'italic'
            elif part == '</i>' or part == '</I>':
                if current_text:
                    fragments.append((current_text, current_style))
                    current_text = ""
                current_style = None
            elif part.startswith('<color=') and part.endswith('>'):
                if current_text:
                    fragments.append((current_text, current_style))
                    current_text = ""
                color = part[7:-1]
                current_style = ('color', color)
            elif part == '</color>':
                if current_text:
                    fragments.append((current_text, current_style))
                    current_text = ""
                current_style = None
            else:
                current_text += part
        if current_text:
            fragments.append((current_text, current_style))
        return fragments
    
    def _type_next_char(self):
        if not self.char_queue:
            self.is_typing = False
            self._check_pending_input()
            return
        self.is_typing = True
        item = self.char_queue.pop(0)
        if isinstance(item, tuple) and item[0] == 'fragment':
            _, text, style = item
            remaining = []
            while self.char_queue:
                remaining.append(self.char_queue.pop(0))
            chars = [('char', ch, style) for ch in text]
            self.char_queue.extend(chars)
            self.char_queue.extend(remaining)
            self.typing_timer = self.after(0, self._type_next_char)
            return
        if isinstance(item, tuple) and item[0] == 'char':
            _, ch, style = item
            self._insert_char(ch, style)
        else:
            self._insert_char(item, None)
        delay = max(1, int(self.typing_speed * 0.5))
        self.typing_timer = self.after(delay, self._type_next_char)
    
    def _insert_char(self, ch, style=None):
        self.terminal_text.config(state='normal')
        if style == 'bold':
            self.terminal_text.insert('end', ch, ('bold',))
            self.terminal_text.tag_config('bold', font=('Consolas', 10, 'bold'))
        elif style == 'italic':
            self.terminal_text.insert('end', ch, ('italic',))
            self.terminal_text.tag_config('italic', font=('Consolas', 10, 'italic'))
        elif isinstance(style, tuple) and style[0] == 'color':
            color = style[1]
            self.terminal_text.insert('end', ch, (f'color_{color}',))
            self.terminal_text.tag_config(f'color_{color}', foreground=color)
        else:
            self.terminal_text.insert('end', ch)
        self.terminal_text.see('end')
        self.terminal_text.config(state='normal')
    
    def _subterm_type_next_char(self):
        if not self.subterm_queue:
            self.subterm_is_typing = False
            self._check_pending_input()
            return
        self.subterm_is_typing = True
        item = self.subterm_queue.pop(0)
        if isinstance(item, tuple) and item[0] == 'fragment':
            _, text, style = item
            remaining = []
            while self.subterm_queue:
                remaining.append(self.subterm_queue.pop(0))
            chars = [('char', ch, style) for ch in text]
            self.subterm_queue.extend(chars)
            self.subterm_queue.extend(remaining)
            self.subterm_typing_timer = self.after(0, self._subterm_type_next_char)
            return
        if isinstance(item, tuple) and item[0] == 'char':
            _, ch, style = item
            self._subterm_insert_char(ch, style)
        else:
            self._subterm_insert_char(item, None)
        self.subterm_typing_timer = self.after(self.typing_speed, self._subterm_type_next_char)
    
    def _subterm_insert_char(self, ch, style=None):
        self.subterm_text.config(state='normal')
        if style == 'bold':
            self.subterm_text.insert('end', ch, ('sub_bold',))
            self.subterm_text.tag_config('sub_bold', font=('Consolas', 10, 'bold'))
        elif style == 'italic':
            self.subterm_text.insert('end', ch, ('sub_italic',))
            self.subterm_text.tag_config('sub_italic', font=('Consolas', 10, 'italic'))
        elif isinstance(style, tuple) and style[0] == 'color':
            color = style[1]
            self.subterm_text.insert('end', ch, (f'sub_color_{color}',))
            self.subterm_text.tag_config(f'sub_color_{color}', foreground=color)
        else:
            self.subterm_text.insert('end', ch)
        self.subterm_text.see('end')
        self.subterm_text.config(state='disabled')
    
    def _check_pending_input(self):
        if self.is_typing or self.subterm_is_typing:
            return
        if self.pending_input and self.input_callback:
            self.pending_input = False
            self.show_prompt()
    
    def show_prompt(self):
        if self.terminal and self.terminal.vfs:
            cwd = self.terminal.vfs.cwd
            if cwd == "/":
                prompt = "/> "
            else:
                prompt = f"{cwd}> "
        else:
            prompt = "> "
        self.terminal_text.insert('end', prompt)
        self.input_start_index = self.terminal_text.index('end-1c')
        self.terminal_text.mark_set('insert', 'end')
        self.terminal_text.see('end')
    
    def get_input(self, callback):
        if self.is_typing or self.subterm_is_typing:
            self.pending_input = True
            self.input_callback = callback
            return
        self.input_callback = callback
        self.show_prompt()
    
    # ========== 输入区域辅助方法 ==========
    
    def _get_input_text(self):
        """获取当前输入区域的文本（不含提示符）"""
        if not self.input_start_index:
            return ""
        start = self.input_start_index
        end = self.terminal_text.index('end-1c')
        if self.terminal_text.compare(start, '>=', end):
            return ""
        return self.terminal_text.get(start, end)
    
    def _set_input_text(self, text, cursor_pos=None):
        """
        设置输入区域的文本，并可选设置光标位置
        cursor_pos: 光标在文本中的偏移（0=开头），None 表示末尾
        """
        if not self.input_start_index:
            return
        start = self.input_start_index
        end = self.terminal_text.index('end-1c')
        self.terminal_text.delete(start, end)
        self.terminal_text.insert(start, text)
        if cursor_pos is None:
            cursor_pos = len(text)
        pos_index = f"{start}+{cursor_pos}c"
        self.terminal_text.mark_set('insert', pos_index)
        self.terminal_text.see('insert')
    
    def _clear_input(self):
        """清除当前输入"""
        self._set_input_text("", 0)
    
    def _insert_text_at_input(self, text):
        """在输入位置插入文本（替换当前输入，光标在末尾）"""
        self._set_input_text(text, len(text))
    
    # ========== 命令历史 ==========
    
    def _history_up(self):
        """上一条历史命令"""
        if not self.command_history:
            return
        if self.history_index == -1:
            self.history_temp = self._get_input_text()
            self.history_index = len(self.command_history) - 1
        elif self.history_index > 0:
            self.history_index -= 1
        else:
            return
        self._apply_history()
    
    def _history_down(self):
        """下一条历史命令"""
        if self.history_index == -1:
            return
        if self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self._apply_history()
        else:
            self.history_index = -1
            self._set_input_text(self.history_temp if hasattr(self, 'history_temp') else "", len(self.history_temp) if hasattr(self, 'history_temp') else 0)
    
    def _apply_history(self):
        """应用历史命令到输入"""
        if 0 <= self.history_index < len(self.command_history):
            cmd = self.command_history[self.history_index]
            self._set_input_text(cmd, len(cmd))
    
    # ========== Tab 补全 ==========
    
    def _tab_complete(self):
        """Tab 补全"""
        if self.is_typing or self.subterm_is_typing:
            return
        
        current = self._get_input_text()
        
        if not current:
            matches = self._get_command_matches("")
            if matches:
                self.tab_matches = matches
                self.tab_index = -1
                self.tab_base = ""
                self._cycle_completion()
            return
        
        parts = current.split()
        
        if len(parts) == 1:
            cmd = parts[0]
            if current != self.tab_base or self.tab_index == -1:
                matches = self._get_command_matches(cmd)
                if matches:
                    self.tab_matches = matches
                    self.tab_index = -1
                    self.tab_base = current
                else:
                    self.tab_matches = []
            self._cycle_completion()
        else:
            cmd = parts[0]
            last_arg = parts[-1]
            if current != self.tab_base or self.tab_index == -1:
                matches = self._get_path_matches(cmd, last_arg)
                if matches:
                    self.tab_matches = matches
                    self.tab_index = -1
                    self.tab_base = current
                else:
                    self.tab_matches = []
            self._cycle_completion()
    
    def _get_command_matches(self, prefix):
        """获取匹配前缀的命令列表"""
        commands = ['ls', 'cd', 'open', 'execute', 'play', 'pwd', 'help', 'echo', 'clear', 'exit']
        if not prefix:
            return commands
        prefix_lower = prefix.lower()
        return [cmd for cmd in commands if cmd.startswith(prefix_lower)]
    
    def _get_path_matches(self, cmd, prefix):
        """获取匹配前缀的路径列表（cd 只补全目录）"""
        if not self.terminal or not self.terminal.vfs:
            return []
        
        cwd = self.terminal.vfs.cwd
        node, _, _ = self.terminal.vfs.resolve_path(cwd)
        if not node or not isinstance(node, dict):
            return []
        
        entries = list(node.keys())
        prefix_lower = prefix.lower()
        matches = []
        for name in entries:
            if name.lower().startswith(prefix_lower):
                child = node.get(name)
                is_dir = isinstance(child, dict) and 'content' not in child and 'function' not in child
                
                if cmd == 'cd' and not is_dir:
                    continue
                
                if is_dir:
                    matches.append(name + '/')
                else:
                    matches.append(name)
        
        matches.sort()
        return matches
    
    def _cycle_completion(self):
        """轮换补全匹配"""
        if not self.tab_matches:
            return
        
        self.tab_index = (self.tab_index + 1) % len(self.tab_matches)
        completion = self.tab_matches[self.tab_index]
        
        current = self._get_input_text()
        if not current:
            new_text = completion
        elif len(current.split()) == 1:
            new_text = completion
        else:
            parts = current.split()
            parts[-1] = completion
            new_text = " ".join(parts)
        
        self._set_input_text(new_text, len(new_text))
        self.tab_base = new_text
    
    # ========== 键盘事件 ==========
    
    def on_key(self, event):
        if self.is_typing or self.subterm_is_typing:
            return "break"
        
        keysym = event.keysym
        
        if keysym == 'Up':
            self._history_up()
            self.tab_matches = []
            return "break"
        
        if keysym == 'Down':
            self._history_down()
            self.tab_matches = []
            return "break"
        
        if keysym == 'Tab':
            self._tab_complete()
            return "break"
        
        if len(event.char) > 0 and event.char.isprintable():
            self.tab_matches = []
            self.tab_index = -1
            self.tab_base = ""
            
            text = self._get_input_text()
            cursor_index = self.terminal_text.index('insert')
            start = self.input_start_index
            
            if self.terminal_text.compare(cursor_index, '<', start):
                offset = len(text)
            else:
                try:
                    offset = int(cursor_index.split('.')[1]) - int(start.split('.')[1])
                except:
                    offset = len(text)
                if offset < 0:
                    offset = 0
                if offset > len(text):
                    offset = len(text)
            
            new_text = text[:offset] + event.char + text[offset:]
            self._set_input_text(new_text, offset + 1)
            return "break"
        
        return
    
    def on_backspace(self, event):
        if self.is_typing or self.subterm_is_typing:
            return "break"
        
        self.tab_matches = []
        self.tab_index = -1
        self.tab_base = ""
        
        text = self._get_input_text()
        if not text:
            return "break"
        
        cursor_index = self.terminal_text.index('insert')
        start = self.input_start_index
        
        if self.terminal_text.compare(cursor_index, '<=', start):
            return "break"
        
        try:
            offset = int(cursor_index.split('.')[1]) - int(start.split('.')[1])
        except:
            offset = len(text)
        if offset < 0:
            offset = 0
        if offset > len(text):
            offset = len(text)
        
        if offset == 0:
            return "break"
        
        new_text = text[:offset-1] + text[offset:]
        self._set_input_text(new_text, offset - 1)
        return "break"
    
    def on_enter(self, event):
        if self.is_typing or self.subterm_is_typing:
            return "break"
        
        # 获取当前输入行（包含提示符）
        start = self.input_start_index
        if start is None:
            return "break"
        end = self.terminal_text.index('end-1c')
        full_line = self.terminal_text.get(start, end)  # 包含提示符和命令
        
        # 获取命令文本（不含提示符）
        cmd = self._get_input_text().strip()
        
        # 清除输入区域（删除提示符和命令）
        self._clear_input()
        
        # 回显整行到终端（作为历史记录）
        self.terminal_text.insert('end', full_line + '\n')
        self.terminal_text.see('end')
        
        # 记录历史
        if cmd:
            self.command_history.append(cmd)
            if len(self.command_history) > 100:
                self.command_history.pop(0)
            self.history_index = -1
        
        # 清空补全状态
        self.tab_matches = []
        self.tab_index = -1
        self.tab_base = ""
        
        # 如果有回调（案件等待输入），优先处理
        if self.input_callback:
            cb = self.input_callback
            self.input_callback = None
            cb(cmd)
            return "break"
        
        # 交给终端引擎处理
        self.terminal.handle_input(cmd)
        
        if not self.terminal.is_running():
            self.app.show_main_menu()
            return "break"
        
        self.show_prompt()
        return "break"

    def load_case(self, case_module):
        self.terminal._page = self
        self.terminal.start_case(case_module)


if __name__ == '__main__':
    root = tk.Tk()
    app = SystemPauseApp(root)
    root.mainloop()