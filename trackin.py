import tkinter as tk
from tkinter import messagebox
import json
from datetime import datetime
import platform


class Hello:
    def __init__(self, root):
        self.root = root
        self.root.title("Keep it.")
        self.setup_fullscreen()
        self.configure_styles()
        self.setup_ui()
        self.load_questions()
        self.bind_hotkeys()
        self.show_next_question()
    
    def setup_fullscreen(self):
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg='black')
        self.root.bind('<Escape>', self.exit_fullscreen)
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        self.locked = True
    
    def configure_styles(self):
        self.BG_COLOR = 'black'
        self.TEXT_COLOR = 'white'
        self.OPTION_BG_COLOR = 'white'
        self.OPTION_FG_COLOR = 'black'
        self.text_font = ('Microsoft YaHei', 28)
        self.option_font = ('Microsoft YaHei', 20)
        self.prompt_font = ('Microsoft YaHei', 24)
    
    def setup_ui(self):
        self.main_frame = tk.Frame(self.root, bg=self.BG_COLOR)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(self.main_frame, bg=self.BG_COLOR, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.options_frame = tk.Frame(self.main_frame, bg=self.BG_COLOR)
        self.options_frame.pack(side=tk.BOTTOM, pady=50)
        self.current_text_id = None
        self.prompt_id = None
        self.time_id = None
        self.text_x = self.screen_width // 2
        self.text_y = self.screen_height // 2
    
    def load_questions(self):
        self.questions = [
            {
                "id": "q1",
                "options": ["Hello.", "Who are you?"],
                "text": "Hello."
            }
        ]
        self.current_question_index = 0
        self.answers = {}
    
    def bind_hotkeys(self):
        self.root.bind('<Control-c>', lambda e: 'break')
        if platform.system() == "Windows":
            try:
                import win32gui
                def disable_alt_f4(hwnd, ctx):
                    import win32con
                    win32gui.EnableMenuItem(
                        win32gui.GetSystemMenu(hwnd, False),
                        win32con.SC_CLOSE,
                        win32con.MF_GRAYED
                    )
                    return True
                self.root.after(100, lambda: win32gui.EnumWindows(disable_alt_f4, None))
            except ImportError:
                print("Warning: Can't import 'win32gui'，Alt+F4 will be available")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def on_close(self):
        if not self.locked:
            self.root.destroy()
    
    def show_next_question(self):
        if self.current_question_index < len(self.questions):
            question = self.questions[self.current_question_index]
            self.canvas.delete("all")
            for widget in self.options_frame.winfo_children():
                widget.destroy()
            self.display_text(question['text'])
            if question['options']:
                self.after_text_displayed = lambda: self.display_options(question['options'], question['id'])
                self.root.bind('<Return>', lambda e: 'break')
            else:
                self.after_text_displayed = lambda: self.root.bind('<Return>', lambda event: self.next_question())
        else:
            self.show_complete_message()
    
    def display_text(self, text):
        self.displayed_text = ""
        self.text_to_display = text
        self.display_text_index = 0
        self.canvas.delete("all")
        self.current_text_id = None
        self.prompt_id = None
        self.update_text_display()
    
    def update_text_display(self):
        if self.current_question_index >= len(self.questions):
            return
        
        if self.display_text_index < len(self.text_to_display):
            self.displayed_text += self.text_to_display[self.display_text_index]
            self.display_text_index += 1
            
            if self.current_text_id:
                self.canvas.delete(self.current_text_id)
            
            self.current_text_id = self.canvas.create_text(
                self.text_x, self.text_y,
                text=self.displayed_text,
                font=self.text_font,
                fill=self.TEXT_COLOR,
                justify=tk.CENTER
            )
            
            self.root.after(50, self.update_text_display)
        else:
            self.add_prompt()
            
            if self.after_text_displayed:
                self.after_text_displayed()
                self.after_text_displayed = None
    
    
    def adjust_prompt_position(self):
        if self.current_question_index != 0 or not self.time_id:
            return
        
        bbox = self.canvas.bbox(self.time_id)
        if not bbox:
            return
        
        x = bbox[2] + 30
        y = bbox[3] + 20
        
        if self.prompt_id:
            self.canvas.coords(self.prompt_id, x, y)
        else:
            self.prompt_id = self.canvas.create_text(
                x, y,
                text="[Enter]",
                font=self.prompt_font,
                fill=self.TEXT_COLOR
            )


    def add_prompt(self):
        if self.current_question_index >= len(self.questions):
            bbox = self.canvas.bbox(self.current_text_id)
            if bbox:
                x = bbox[2] + 30
                y = bbox[3] + 10
                self.prompt_id = self.canvas.create_text(x, y, text="[ESC]", font=self.prompt_font, fill=self.TEXT_COLOR)
                self.locked = False
                self.root.unbind('<Return>')
        elif self.current_question_index == 0:
            pass
        else:
            bbox = self.canvas.bbox(self.current_text_id)
            if bbox:
                x = bbox[2] + 30
                y = bbox[3] + 10
                current_question = self.questions[self.current_question_index]
                if not current_question.get('options'):
                    self.prompt_id = self.canvas.create_text(x, y, text="[Enter]", font=self.prompt_font, fill=self.TEXT_COLOR)
    

    def display_options(self, options, question_id):
        for widget in self.options_frame.winfo_children():
            widget.destroy()
        button_frame = tk.Frame(self.options_frame, bg=self.BG_COLOR)
        button_frame.pack(expand=True)
        for i, option_text in enumerate(options):
            option_btn = tk.Button(
                button_frame,
                text=f"[{i+1}] {option_text}",
                bg=self.OPTION_BG_COLOR,
                fg=self.OPTION_FG_COLOR,
                font=self.option_font,
                width=15,
                height=2,
                relief=tk.RAISED,
                bd=3,
                command=lambda opt=option_text, qid=question_id: self.select_option(opt, qid)
            )
            option_btn.pack(side=tk.LEFT, padx=20, pady=10)
    
    def select_option(self, option, question_id):
        self.answers[question_id] = option
        for widget in self.options_frame.winfo_children():
            if isinstance(widget, tk.Frame):
                for btn in widget.winfo_children():
                    btn.config(state=tk.DISABLED)
        self.canvas.delete("all")
        selected_text = f"You have chosen: {option}"
        self.current_text_id = self.canvas.create_text(
            self.text_x, self.text_y,
            text=selected_text,
            font=self.text_font,
            fill=self.TEXT_COLOR,
            justify=tk.CENTER
        )
        self.root.after(2000, self.next_question)
    
    def next_question(self):
        self.root.unbind('<Return>')
        self.current_question_index += 1
        self.show_next_question()
    
    def show_complete_message(self):
        self.canvas.delete("all")
        self.current_text_id = self.canvas.create_text(
            self.text_x, self.text_y,
            text="Press ESC.",
            font=self.text_font,
            fill=self.TEXT_COLOR,
            justify=tk.CENTER
        )
        self.add_prompt()
    
    def exit_fullscreen(self, event=None):
        if not self.locked:
            self.root.attributes('-fullscreen', False)
            self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    root.option_add("*Font", ("Microsoft YaHei", 12))
    try:
        import win32gui
    except ImportError:
        print("Warning: Can't import 'win32gui'，Alt+F4 will be available")
        print("Disable Alt+F4? Please install pywin32: pip install pywin32")
    app = Hello(root)
    root.mainloop()    