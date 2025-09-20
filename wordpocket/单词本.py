import json
import tkinter as tk
from doctest import master
from tkinter import messagebox


class VocabularyBook:
    def __init__(self, master):
        self.master = master
        master.title("本地单词本 v1.0")
        
        # 初始化界面
        self.create_widgets()
        # 加载词典数据
        self.load_dictionary()
    
    def create_widgets(self):
        """创建界面组件"""
        # 输入区域
        self.input_frame = tk.Frame(self.master)
        self.input_frame.pack(pady=10)
        
        self.lbl_word = tk.Label(self.input_frame, text="输入单词:")
        self.lbl_word.pack(side=tk.LEFT)
        
        self.entry_word = tk.Entry(self.input_frame, width=30)
        self.entry_word.pack(side=tk.LEFT, padx=5)
        self.entry_word.bind("<Return>", lambda event: self.search_word())  # 回车触发查询
        
        self.btn_search = tk.Button(self.input_frame, text="查询", command=self.search_word)
        self.btn_search.pack(side=tk.LEFT)
        
        # 结果显示区域
        self.result_text = tk.Text(self.master, width=50, height=10, wrap=tk.WORD)
        self.result_text.pack(padx=10, pady=5)
        
        # 操作按钮
        self.btn_frame = tk.Frame(self.master)
        self.btn_frame.pack(pady=5)
        
        self.btn_add = tk.Button(self.btn_frame, text="添加单词", command=self.add_word_window)
        self.btn_add.pack(side=tk.LEFT, padx=5)
        
        self.btn_save = tk.Button(self.btn_frame, text="保存数据", command=self.save_dictionary)
        self.btn_save.pack(side=tk.LEFT)
    
    def load_dictionary(self):
        """加载本地词典"""
        try:
            with open('dictionary.json', 'r', encoding='utf-8') as f:
                self.dictionary = json.load(f)
        except FileNotFoundError:
            self.dictionary = {}
            messagebox.showwarning("警告", "未找到词典文件，已创建空词典")
    
    def save_dictionary(self):
        """保存词典数据"""
        with open('dictionary.json', 'w', encoding='utf-8') as f:
            json.dump(self.dictionary, f, ensure_ascii=False, indent=2)
        messagebox.showinfo("提示", "数据保存成功！")
    
    def search_word(self):
        """查询单词"""
        word = self.entry_word.get().strip().lower()
        self.result_text.delete(1.0, tk.END)  # 清空结果
        
        if not word:
            messagebox.showwarning("提示", "请输入要查询的单词")
            return
        
        if word in self.dictionary:
            result = f"{word} 的音标及释义：\n{self.dictionary[word]}"
        else:
            result = f"未找到 {word} 的释义"
        
        self.result_text.insert(tk.END, result)
        self.entry_word.delete(0, tk.END)  # 清空输入框
    
    def add_word_window(self):
        """弹出添加单词窗口"""
        self.add_win = tk.Toplevel()
        self.add_win.title("添加新词")
        
        # 输入组件
        tk.Label(self.add_win, text="英文单词:").grid(row=0, column=0, padx=5, pady=5)
        self.entry_new_word = tk.Entry(self.add_win, width=25)
        self.entry_new_word.grid(row=0, column=1)
        
        tk.Label(self.add_win, text="中文释义:").grid(row=1, column=0, padx=5, pady=5)
        self.entry_definition = tk.Entry(self.add_win, width=25)
        self.entry_definition.grid(row=1, column=1)
        
        btn_confirm = tk.Button(self.add_win, text="确认添加",
                                command=self.confirm_add_word)
        btn_confirm.grid(row=2, columnspan=2, pady=10)
    
    def confirm_add_word(self):
        """确认添加新词"""
        word = self.entry_new_word.get().strip().lower()
        definition = self.entry_definition.get().strip()
        
        if not word or not definition:
            messagebox.showwarning("警告", "单词和释义都不能为空")
            return
        
        try:
            if self.dictionary[word]:
                messagebox.showerror('错误', f'单词 {word} 已存在释义')
                self.add_win.destroy()
        except KeyError:
            self.dictionary[word] = definition
            self.add_win.destroy()
            messagebox.showinfo("提示", f"成功添加单词: {word}")


if __name__ == "__main__":
    root = tk.Tk()
    app = VocabularyBook(root)
    root.mainloop()