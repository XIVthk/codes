import re
import os
from vfs import VFS

class TerminalEngine:
    def __init__(self, output_callback, input_callback, subterm_callback=None):
        self.out = output_callback
        self.get_input = input_callback
        self.subterm = subterm_callback
        self.window_manager = None
        self.cwd = "/"
        self.current_case = None
        self.running = False
        self.input_prompt = "> "
        self.input_callback = None
        self.vfs = None
        self._page = None
    
    def set_window_manager(self, wm):
        self.window_manager = wm
    
    def create_window(self, name, title, geometry, widget_type, **kwargs):
        if self.window_manager:
            return self.window_manager.create_window(name, title, geometry, widget_type, **kwargs)
        return None
    
    def close_window(self, name):
        if self.window_manager:
            self.window_manager.close_window(name)
    
    def show_window(self, name):
        if self.window_manager:
            self.window_manager.show_window(name)
    
    def hide_window(self, name):
        if self.window_manager:
            self.window_manager.hide_window(name)
    
    def subterm_bg(self, text):
        """修改 subterm 窗口的背景文字"""
        if self.window_manager:
            self.window_manager.set_bg_text('subterm', text)
    
    def start_case(self, case_module):
        self.current_case = case_module.Case(self)
        self.vfs = VFS(self.current_case.fs)
        self.cwd = getattr(self.current_case, 'cwd', '/')
        self.vfs.cwd = self.cwd
        self.vfs.current_node = self.vfs._get_node(self.cwd)
        self.running = True
        self.current_case.on_start()
    
    def handle_input(self, cmd_str):
        if not self.running:
            return
        
        parts = cmd_str.strip().split()
        if not parts:
            return
        
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        flags = []
        clean_args = []
        for arg in args:
            if arg.startswith("-"):
                flags.append(arg)
            else:
                clean_args.append(arg)
        
        builtin_result = self.builtin_command(cmd, clean_args, flags)
        if builtin_result is not None:
            if builtin_result:
                self.out(builtin_result)
            return
        
        vfs_result = self.vfs_command(cmd, clean_args, flags)
        if vfs_result is not None:
            if vfs_result:
                if isinstance(vfs_result, str) and vfs_result.startswith("__ENCRYPTED__:"):
                    self._handle_encrypted(vfs_result, cmd, clean_args, flags)
                    return
                
                if cmd in ["cd", "play"]:
                    self.out(f"< {vfs_result}")
                elif cmd == "execute":
                    if "\n" in vfs_result and "[stdout:" in vfs_result:
                        self.out(vfs_result)
                    else:
                        self.out(f"< {vfs_result}")
                elif cmd == "open":
                    self.out(vfs_result)
                else:
                    self.out(vfs_result)
            return
        
        if self.current_case and hasattr(self.current_case, 'handle_command'):
            case_result = self.current_case.handle_command(cmd, clean_args, flags)
            if case_result is not None:
                if case_result:
                    self.out(case_result)
                return
        
        self.out(f"未知命令: {cmd}。输入 help 查看可用命令。")
    
    def _handle_encrypted(self, vfs_result, cmd, args, flags):
        """处理加密目录"""
        _, path, original_cmd = vfs_result.split(":", 2)
        
        def on_password_submitted(password):
            if self.vfs.unlock_directory(path, password):
                self.out("解锁成功。")
                self.window_manager.close_window('password_input')
                # 重新执行原命令
                if original_cmd == "ls":
                    result = self.vfs.ls(path)
                    if result:
                        self.out(result)
                elif original_cmd == "cd":
                    result = self.vfs.cd(path)
                    if result:
                        self.out(f"< {result}")
                elif original_cmd == "open":
                    result = self.vfs.open(path, flags)
                    if result:
                        self.out(result)
                elif original_cmd == "execute":
                    result = self.vfs.execute(path, args, flags)
                    if result:
                        self.out(result)
            else:
                self.out("密码错误。")
                self.window_manager.close_window('password_input')
        
        self.create_window(
            name='password_input',
            title='输入密码',
            geometry='400x180',
            widget_type='entry',
            label=f'请输入密码以访问 {path}：',
            button_text='确认',
            callback=on_password_submitted
        )
        self.show_window('password_input')
    
    def builtin_command(self, cmd, args, flags):
        if cmd == "help":
            return """可用命令:
  help              - 显示帮助
  echo <text>       - 回显文本
  clear             - 清屏
  exit              - 返回主菜单
  ls [path]         - 列出目录内容
  cd <path>         - 切换目录
  open <file>       - 打开文件
  execute <file>    - 执行可执行文件
  play <file>       - 播放音频文件
  pwd               - 显示当前路径"""
        elif cmd == "echo":
            return " ".join(args) if args else ""
        elif cmd == "clear":
            self.out("\033[2J\033[H")
            return None
        elif cmd == "exit":
            self.running = False
            return "退出游戏..."
        else:
            return None
    
    def vfs_command(self, cmd, args, flags):
        if not self.vfs:
            return None
        
        if cmd == "ls":
            path = args[0] if args else "."
            return self.vfs.ls(path)
        elif cmd == "cd":
            if not args:
                return "cd: 需要指定路径"
            return self.vfs.cd(args[0])
        elif cmd == "open":
            if not args:
                return "open: 需要指定文件路径"
            admin = "-a" in flags or "--admin" in flags
            return self.vfs.open(args[0], admin)
        elif cmd == "execute":
            if not args:
                return "execute: 需要指定文件路径"
            admin = "-a" in flags or "--admin" in flags
            return self.vfs.execute(args[0], args[1:], flags)
        elif cmd == "play":
            if not args:
                return "play: 需要指定文件路径"
            admin = "-a" in flags or "--admin" in flags
            return self.vfs.play(args[0], flags)
        elif cmd == "pwd":
            return self.vfs.pwd()
        else:
            return None
    
    def set_prompt(self, prompt):
        self.input_prompt = prompt
    
    def is_running(self):
        return self.running