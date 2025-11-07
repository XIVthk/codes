import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
import os
import threading
import requests
import time
from tkinter import font


class ValueSystemEditor:
    """值系统编辑器 - 提供用户友好的界面来管理游戏值和条件"""
    
    def __init__(self, parent):
        self.parent = parent
        self.frame = ttk.Frame(parent)
        
        # 存储数据
        self.set_values = {}
        self.change_values = {}
        self.conditional_next = []
        
        self.create_ui()
    
    def create_ui(self):
        # 值系统主框架
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建Notebook来组织不同功能
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # 游戏值管理选项卡
        values_frame = ttk.Frame(notebook)
        notebook.add(values_frame, text="游戏值管理")
        self.create_values_tab(values_frame)
        
        # 条件跳转选项卡
        conditions_frame = ttk.Frame(notebook)
        notebook.add(conditions_frame, text="条件跳转")
        self.create_conditions_tab(conditions_frame)
        
        # 选项条件选项卡
        options_frame = ttk.Frame(notebook)
        notebook.add(options_frame, text="选项条件")
        self.create_options_tab(options_frame)
    
    def create_values_tab(self, parent):
        # 设置值框架
        set_frame = ttk.LabelFrame(parent, text="设置游戏值")
        set_frame.pack(fill=tk.X, pady=5, padx=5)
        
        # 当前值显示
        current_frame = ttk.Frame(set_frame)
        current_frame.pack(fill=tk.X, pady=5)
        ttk.Label(current_frame, text="当前游戏值:").pack(side=tk.LEFT)
        self.current_values_label = ttk.Label(current_frame, text="{}", foreground="blue")
        self.current_values_label.pack(side=tk.LEFT, padx=5)
        
        # 添加新值
        add_frame = ttk.Frame(set_frame)
        add_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(add_frame, text="变量名:").pack(side=tk.LEFT)
        self.var_name_entry = ttk.Entry(add_frame, width=15)
        self.var_name_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(add_frame, text="值:").pack(side=tk.LEFT)
        self.var_value_entry = ttk.Entry(add_frame, width=10)
        self.var_value_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(add_frame, text="添加/修改", command=self.add_set_value).pack(side=tk.LEFT, padx=5)
        
        # 设置值列表
        list_frame = ttk.Frame(set_frame)
        list_frame.pack(fill=tk.X, pady=5)
        
        columns = ("name", "value")
        self.set_values_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=4)
        self.set_values_tree.heading("name", text="变量名")
        self.set_values_tree.heading("value", text="值")
        self.set_values_tree.column("name", width=150)
        self.set_values_tree.column("value", width=100)
        
        self.set_values_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 设置值操作按钮
        set_buttons_frame = ttk.Frame(set_frame)
        set_buttons_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(set_buttons_frame, text="删除选中", command=self.delete_set_value).pack(side=tk.LEFT, padx=2)
        ttk.Button(set_buttons_frame, text="清空所有", command=self.clear_set_values).pack(side=tk.LEFT, padx=2)
        
        # 改变值框架
        change_frame = ttk.LabelFrame(parent, text="改变游戏值")
        change_frame.pack(fill=tk.X, pady=5, padx=5)
        
        # 操作类型选择
        op_frame = ttk.Frame(change_frame)
        op_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(op_frame, text="变量名:").pack(side=tk.LEFT)
        self.change_var_entry = ttk.Entry(op_frame, width=15)
        self.change_var_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(op_frame, text="操作:").pack(side=tk.LEFT)
        self.operation_var = tk.StringVar(value="增加")
        ttk.Combobox(op_frame, textvariable=self.operation_var,
                     values=["增加", "减少", "设置为", "乘以", "除以"], width=8, state="readonly").pack(side=tk.LEFT, padx=5)
        
        ttk.Label(op_frame, text="数值:").pack(side=tk.LEFT)
        self.change_value_entry = ttk.Entry(op_frame, width=10)
        self.change_value_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(op_frame, text="添加操作", command=self.add_change_value).pack(side=tk.LEFT, padx=5)
        
        # 改变值列表
        change_list_frame = ttk.Frame(change_frame)
        change_list_frame.pack(fill=tk.X, pady=5)
        
        change_columns = ("variable", "operation", "value")
        self.change_values_tree = ttk.Treeview(change_list_frame, columns=change_columns, show="headings", height=4)
        self.change_values_tree.heading("variable", text="变量名")
        self.change_values_tree.heading("operation", text="操作")
        self.change_values_tree.heading("value", text="数值")
        self.change_values_tree.column("variable", width=120)
        self.change_values_tree.column("operation", width=80)
        self.change_values_tree.column("value", width=80)
        
        self.change_values_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 改变值操作按钮
        change_buttons_frame = ttk.Frame(change_frame)
        change_buttons_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(change_buttons_frame, text="删除选中", command=self.delete_change_value).pack(side=tk.LEFT, padx=2)
        ttk.Button(change_buttons_frame, text="清空所有", command=self.clear_change_values).pack(side=tk.LEFT, padx=2)
    
    def create_conditions_tab(self, parent):
        # 条件跳转框架
        cond_frame = ttk.LabelFrame(parent, text="条件跳转设置")
        cond_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)
        
        # 添加新条件
        new_cond_frame = ttk.Frame(cond_frame)
        new_cond_frame.pack(fill=tk.X, pady=5)
        
        # 条件变量
        var_frame = ttk.Frame(new_cond_frame)
        var_frame.pack(fill=tk.X, pady=2)
        ttk.Label(var_frame, text="检查变量:").pack(side=tk.LEFT)
        self.cond_var_entry = ttk.Entry(var_frame, width=15)
        self.cond_var_entry.pack(side=tk.LEFT, padx=5)
        
        # 条件类型
        type_frame = ttk.Frame(new_cond_frame)
        type_frame.pack(fill=tk.X, pady=2)
        ttk.Label(type_frame, text="条件类型:").pack(side=tk.LEFT)
        self.cond_type_var = tk.StringVar(value="大于")
        cond_combo = ttk.Combobox(type_frame, textvariable=self.cond_type_var,
                                  values=["大于", "大于等于", "等于", "小于", "小于等于", "不等于"],
                                  width=10, state="readonly")
        cond_combo.pack(side=tk.LEFT, padx=5)
        
        # 条件值
        value_frame = ttk.Frame(new_cond_frame)
        value_frame.pack(fill=tk.X, pady=2)
        ttk.Label(value_frame, text="比较值:").pack(side=tk.LEFT)
        self.cond_value_entry = ttk.Entry(value_frame, width=10)
        self.cond_value_entry.pack(side=tk.LEFT, padx=5)
        
        # 目标节点
        target_frame = ttk.Frame(new_cond_frame)
        target_frame.pack(fill=tk.X, pady=2)
        ttk.Label(target_frame, text="目标节点:").pack(side=tk.LEFT)
        self.cond_target_entry = ttk.Entry(target_frame, width=20)
        self.cond_target_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(new_cond_frame, text="添加条件跳转", command=self.add_conditional_next).pack(pady=5)
        
        # 条件列表
        list_frame = ttk.Frame(cond_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        cond_columns = ("condition", "target")
        self.conditional_tree = ttk.Treeview(list_frame, columns=cond_columns, show="headings", height=6)
        self.conditional_tree.heading("condition", text="条件")
        self.conditional_tree.heading("target", text="目标节点")
        self.conditional_tree.column("condition", width=250)
        self.conditional_tree.column("target", width=150)
        
        self.conditional_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 条件操作按钮
        cond_buttons_frame = ttk.Frame(cond_frame)
        cond_buttons_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(cond_buttons_frame, text="删除选中", command=self.delete_conditional).pack(side=tk.LEFT, padx=2)
        ttk.Button(cond_buttons_frame, text="清空所有", command=self.clear_conditionals).pack(side=tk.LEFT, padx=2)
    
    def create_options_tab(self, parent):
        # 选项条件说明
        desc_frame = ttk.Frame(parent)
        desc_frame.pack(fill=tk.X, pady=10, padx=5)
        
        desc_text = (
            "选项条件设置说明：\n"
            "在编辑选项时，可以为每个选项添加显示条件。\n"
            "只有满足条件的选项才会在游戏中显示给玩家。\n"
            "条件格式与条件跳转相同。"
        )
        desc_label = ttk.Label(desc_frame, text=desc_text, foreground="blue")
        desc_label.pack(anchor=tk.W)
        
        # 示例
        example_frame = ttk.LabelFrame(parent, text="条件示例")
        example_frame.pack(fill=tk.X, pady=5, padx=5)
        
        examples = [
            "health > 50      - 生命值大于50时显示",
            "level >= 5       - 等级大于等于5时显示",
            "has_key == true  - 拥有钥匙时显示",
            "coins < 100      - 金币少于100时显示"
        ]
        
        for example in examples:
            ttk.Label(example_frame, text=example, font=("SimHei", 9)).pack(anchor=tk.W, pady=2)
    
    def add_set_value(self):
        """添加设置值"""
        var_name = self.var_name_entry.get().strip()
        var_value = self.var_value_entry.get().strip()
        
        if not var_name:
            messagebox.showwarning("警告", "请输入变量名")
            return
        
        if not var_value:
            messagebox.showwarning("警告", "请输入变量值")
            return
        
        # 尝试转换为数字，如果失败则保持字符串
        try:
            if '.' in var_value:
                value = float(var_value)
            else:
                value = int(var_value)
        except ValueError:
            # 检查是否是布尔值
            if var_value.lower() in ['true', 'false']:
                value = var_value.lower() == 'true'
            else:
                value = var_value  # 保持为字符串
        
        self.set_values[var_name] = value
        self.update_set_values_display()
        
        # 清空输入框
        self.var_name_entry.delete(0, tk.END)
        self.var_value_entry.delete(0, tk.END)
    
    def delete_set_value(self):
        """删除选中的设置值"""
        selection = self.set_values_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个值")
            return
        
        for item in selection:
            var_name = self.set_values_tree.item(item)["values"][0]
            if var_name in self.set_values:
                del self.set_values[var_name]
        
        self.update_set_values_display()
    
    def clear_set_values(self):
        """清空所有设置值"""
        if messagebox.askyesno("确认", "确定要清空所有设置值吗？"):
            self.set_values = {}
            self.update_set_values_display()
    
    def update_set_values_display(self):
        """更新设置值显示"""
        # 更新树形视图
        self.set_values_tree.delete(*self.set_values_tree.get_children())
        for var_name, value in self.set_values.items():
            self.set_values_tree.insert("", tk.END, values=(var_name, value))
        
        # 更新当前值标签
        self.current_values_label.config(text=str(self.set_values))
    
    def add_change_value(self):
        """添加改变值操作"""
        var_name = self.change_var_entry.get().strip()
        operation = self.operation_var.get()
        value_str = self.change_value_entry.get().strip()
        
        if not var_name:
            messagebox.showwarning("警告", "请输入变量名")
            return
        
        if not value_str:
            messagebox.showwarning("警告", "请输入数值")
            return
        
        # 转换数值
        try:
            if '.' in value_str:
                value = float(value_str)
            else:
                value = int(value_str)
        except ValueError:
            messagebox.showerror("错误", "数值必须是数字")
            return
        
        # 映射操作到引擎格式
        op_map = {
            "增加": "add",
            "减少": "sub",
            "设置为": "set",
            "乘以": "mul",
            "除以": "div"
        }
        
        op_key = op_map.get(operation, "add")
        
        # 添加到改变值字典
        if var_name not in self.change_values:
            self.change_values[var_name] = {}
        
        self.change_values[var_name][op_key] = value
        self.update_change_values_display()
        
        # 清空输入框
        self.change_var_entry.delete(0, tk.END)
        self.change_value_entry.delete(0, tk.END)
    
    def delete_change_value(self):
        """删除选中的改变值"""
        selection = self.change_values_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个操作")
            return
        
        for item in selection:
            values = self.change_values_tree.item(item)["values"]
            var_name = values[0]
            
            if var_name in self.change_values:
                del self.change_values[var_name]
        
        self.update_change_values_display()
    
    def clear_change_values(self):
        """清空所有改变值"""
        if messagebox.askyesno("确认", "确定要清空所有改变值操作吗？"):
            self.change_values = {}
            self.update_change_values_display()
    
    def update_change_values_display(self):
        """更新改变值显示"""
        self.change_values_tree.delete(*self.change_values_tree.get_children())
        
        op_display_map = {
            "add": "增加",
            "sub": "减少",
            "set": "设置为",
            "mul": "乘以",
            "div": "除以"
        }
        
        for var_name, operations in self.change_values.items():
            for op, value in operations.items():
                display_op = op_display_map.get(op, op)
                self.change_values_tree.insert("", tk.END, values=(var_name, display_op, value))
    
    def add_conditional_next(self):
        """添加条件跳转"""
        var_name = self.cond_var_entry.get().strip()
        cond_type = self.cond_type_var.get()
        value_str = self.cond_value_entry.get().strip()
        target = self.cond_target_entry.get().strip()
        
        if not all([var_name, cond_type, value_str, target]):
            messagebox.showwarning("警告", "请填写所有条件字段")
            return
        
        # 转换条件值
        try:
            if '.' in value_str:
                cond_value = float(value_str)
            else:
                cond_value = int(value_str)
        except ValueError:
            # 如果是字符串（如true/false），保持原样
            if value_str.lower() in ['true', 'false']:
                cond_value = value_str.lower() == 'true'
            else:
                cond_value = value_str
        
        # 映射条件类型到引擎格式
        cond_map = {
            "大于": "gt",
            "大于等于": "gte",
            "等于": "eq",
            "小于": "lt",
            "小于等于": "lte",
            "不等于": "ne"
        }
        
        cond_key = cond_map.get(cond_type, "eq")
        
        # 创建条件字典
        condition = {
            "conditions": {
                var_name: {cond_key: cond_value}
            },
            "next": target
        }
        
        self.conditional_next.append(condition)
        self.update_conditional_display()
        
        # 清空输入框
        self.cond_var_entry.delete(0, tk.END)
        self.cond_value_entry.delete(0, tk.END)
        self.cond_target_entry.delete(0, tk.END)
    
    def delete_conditional(self):
        """删除选中的条件"""
        selection = self.conditional_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个条件")
            return
        
        # 从后往前删除，避免索引问题
        for item in reversed(selection):
            index = self.conditional_tree.index(item)
            if 0 <= index < len(self.conditional_next):
                self.conditional_next.pop(index)
        
        self.update_conditional_display()
    
    def clear_conditionals(self):
        """清空所有条件"""
        if messagebox.askyesno("确认", "确定要清空所有条件跳转吗？"):
            self.conditional_next = []
            self.update_conditional_display()
    
    def update_conditional_display(self):
        """更新条件显示"""
        self.conditional_tree.delete(*self.conditional_tree.get_children())
        
        cond_display_map = {
            "gt": ">",
            "gte": ">=",
            "eq": "==",
            "lt": "<",
            "lte": "<=",
            "ne": "!="
        }
        
        for cond in self.conditional_next:
            conditions = cond.get("conditions", {})
            target = cond.get("next", "")
            
            condition_texts = []
            for var_name, cond_dict in conditions.items():
                for op, value in cond_dict.items():
                    display_op = cond_display_map.get(op, op)
                    condition_texts.append(f"{var_name} {display_op} {value}")
            
            condition_display = " 且 ".join(condition_texts)
            self.conditional_tree.insert("", tk.END, values=(condition_display, target))
    
    def get_data(self):
        """获取所有数据"""
        return {
            "set_values": self.set_values,
            "change_values": self.change_values,
            "conditional_next": self.conditional_next
        }
    
    def set_data(self, data):
        """设置数据"""
        self.set_values = data.get("set_values", {})
        self.change_values = data.get("change_values", {})
        self.conditional_next = data.get("conditional_next", [])
        
        self.update_set_values_display()
        self.update_change_values_display()
        self.update_conditional_display()
    
    def pack(self, **kwargs):
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        self.frame.grid(**kwargs)


class OptionEditor:
    """选项编辑器 - 支持条件设置"""
    
    def __init__(self, parent, title, option_data=None):
        self.parent = parent
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("600x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.option_data = option_data or {"text": "", "next": ""}
        self.conditions = self.option_data.get("conditions", {})
        
        self.create_ui()
    
    def create_ui(self):
        frame = ttk.Frame(self.dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 选项文本
        ttk.Label(frame, text="选项文本:").pack(anchor=tk.W, pady=5)
        self.text_entry = ttk.Entry(frame)
        self.text_entry.pack(fill=tk.X, pady=5)
        self.text_entry.insert(0, self.option_data.get("text", ""))
        
        # 目标节点
        ttk.Label(frame, text="目标节点:").pack(anchor=tk.W, pady=5)
        self.next_entry = ttk.Entry(frame)
        self.next_entry.pack(fill=tk.X, pady=5)
        self.next_entry.insert(0, self.option_data.get("next", ""))
        
        # 条件设置
        cond_frame = ttk.LabelFrame(frame, text="显示条件（可选）")
        cond_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 条件变量
        var_frame = ttk.Frame(cond_frame)
        var_frame.pack(fill=tk.X, pady=2)
        ttk.Label(var_frame, text="检查变量:").pack(side=tk.LEFT)
        self.cond_var_entry = ttk.Entry(var_frame, width=15)
        self.cond_var_entry.pack(side=tk.LEFT, padx=5)
        
        # 条件类型
        type_frame = ttk.Frame(cond_frame)
        type_frame.pack(fill=tk.X, pady=2)
        ttk.Label(type_frame, text="条件类型:").pack(side=tk.LEFT)
        self.cond_type_var = tk.StringVar(value="大于")
        cond_combo = ttk.Combobox(type_frame, textvariable=self.cond_type_var,
                                  values=["大于", "大于等于", "等于", "小于", "小于等于", "不等于"],
                                  width=10, state="readonly")
        cond_combo.pack(side=tk.LEFT, padx=5)
        
        # 条件值
        value_frame = ttk.Frame(cond_frame)
        value_frame.pack(fill=tk.X, pady=2)
        ttk.Label(value_frame, text="比较值:").pack(side=tk.LEFT)
        self.cond_value_entry = ttk.Entry(value_frame, width=10)
        self.cond_value_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(cond_frame, text="添加条件", command=self.add_condition).pack(pady=5)
        
        # 现有条件列表
        list_frame = ttk.Frame(cond_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.conditions_tree = ttk.Treeview(list_frame, columns=("condition",), show="headings", height=4)
        self.conditions_tree.heading("condition", text="条件")
        self.conditions_tree.column("condition", width=400)
        self.conditions_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 条件操作按钮
        cond_buttons_frame = ttk.Frame(cond_frame)
        cond_buttons_frame.pack(fill=tk.X, pady=5)
        ttk.Button(cond_buttons_frame, text="删除条件", command=self.delete_condition).pack()
        
        # 加载现有条件
        self.load_existing_conditions()
        
        # 按钮
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="取消", command=self.dialog.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="确定", command=self.save).pack(side=tk.RIGHT, padx=5)
    
    def load_existing_conditions(self):
        """加载现有条件"""
        for var_name, cond_dict in self.conditions.items():
            for op, value in cond_dict.items():
                # 映射操作符到显示文本
                op_map = {
                    "gt": ">", "gte": ">=", "eq": "==",
                    "lt": "<", "lte": "<=", "ne": "!="
                }
                display_op = op_map.get(op, op)
                condition_text = f"{var_name} {display_op} {value}"
                self.conditions_tree.insert("", tk.END, values=(condition_text,))
    
    def add_condition(self):
        """添加条件"""
        var_name = self.cond_var_entry.get().strip()
        cond_type = self.cond_type_var.get()
        value_str = self.cond_value_entry.get().strip()
        
        if not all([var_name, cond_type, value_str]):
            messagebox.showwarning("警告", "请填写所有条件字段")
            return
        
        # 转换条件值
        try:
            if '.' in value_str:
                cond_value = float(value_str)
            else:
                cond_value = int(value_str)
        except ValueError:
            # 如果是字符串（如true/false），保持原样
            if value_str.lower() in ['true', 'false']:
                cond_value = value_str.lower() == 'true'
            else:
                cond_value = value_str
        
        # 映射条件类型到引擎格式
        cond_map = {
            "大于": "gt",
            "大于等于": "gte",
            "等于": "eq",
            "小于": "lt",
            "小于等于": "lte",
            "不等于": "ne"
        }
        
        cond_key = cond_map.get(cond_type, "eq")
        
        # 添加到条件字典
        if var_name not in self.conditions:
            self.conditions[var_name] = {}
        
        self.conditions[var_name][cond_key] = cond_value
        
        # 更新显示
        op_map = {
            "gt": ">", "gte": ">=", "eq": "==",
            "lt": "<", "lte": "<=", "ne": "!="
        }
        display_op = op_map.get(cond_key, cond_key)
        condition_text = f"{var_name} {display_op} {cond_value}"
        self.conditions_tree.insert("", tk.END, values=(condition_text,))
        
        # 清空输入框
        self.cond_var_entry.delete(0, tk.END)
        self.cond_value_entry.delete(0, tk.END)
    
    def delete_condition(self):
        """删除选中的条件"""
        selection = self.conditions_tree.selection()
        if not selection:
            return
        
        # 从后往前删除
        for item in reversed(selection):
            condition_text = self.conditions_tree.item(item)["values"][0]
            # 解析条件文本获取变量名
            parts = condition_text.split()
            if len(parts) >= 3:
                var_name = parts[0]
                if var_name in self.conditions:
                    del self.conditions[var_name]
            
            self.conditions_tree.delete(item)
    
    def save(self):
        """保存选项"""
        text = self.text_entry.get().strip()
        next_node = self.next_entry.get().strip()
        
        if not text or not next_node:
            messagebox.showwarning("警告", "请填写选项文本和目标节点")
            return
        
        self.result = {
            "text": text,
            "next": next_node
        }
        
        if self.conditions:
            self.result["conditions"] = self.conditions
        
        self.dialog.destroy()


class AIStoryEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AI辅助故事编辑器 - 无限选项版")
        self.geometry("1200x800")
        self.configure(bg="#f0f0f0")
        
        # 确保中文显示正常
        self.default_font = font.nametofont("TkDefaultFont")
        self.default_font.configure(family="SimHei", size=10)
        self.option_add("*Font", self.default_font)
        
        # 故事数据 - 兼容游戏引擎格式
        self.story_data = {}
        self.current_file = None
        self.current_node = None
        self.recent_files = []
        
        # AI配置
        self.api_key = "sk-X3urrsXJnilZTHCqHSfJXjUqANDr1HpmvKg8rbq4okYA8Tem"
        self.api_url = "https://api.moonshot.cn/v1"
        self.model_name = "moonshot-v1-8k"
        
        # 游戏引擎兼容设置
        self.advanced_settings = {
            "background": "",
            "sound": "",
            "display_mode": "dialog",
            "expression": "default",
            "bg_color": "",
            "text_color": "",
            "ending": ""
        }
        
        # 选项管理
        self.options = []
        
        # AI格式标签说明
        self.format_tags = (
            "支持的格式标签：\n"
            "- [br]：强制换行（必须使用）\n"
            "- [b][/b]：蓝色文字\n"
            "- [r][/r]：红色文字\n"
            "- [g][/g]：绿色文字\n"
            "- [y][/y]：黄色文字\n"
            "- [i][/i]：斜体\n"
            "- [m][/m]：心理标记\n"
            "生成内容时必须使用这些标签，尤其是[br]换行！"
        )
        
        self.system_hints = (
            "你是一个故事创作助手，帮助用户创作引人入胜的故事内容。\n"
            f"重要格式规则：\n{self.format_tags}\n"
            "生成内容时必须严格遵循这些格式。"
        )
        
        self.story_context = ""
        self.last_ai_response = ""
        
        # 创建界面
        self.create_ui()
        self.load_hints()
        self.load_recent_files()
        
        # 自动保存
        self.auto_save_interval = 5
        self.last_save_time = time.time()
        self.start_auto_save()
    
    def start_auto_save(self):
        """启动自动保存计时器"""
        self.check_auto_save()
    
    def check_auto_save(self):
        """检查是否需要自动保存"""
        current_time = time.time()
        if (current_time - self.last_save_time) > self.auto_save_interval * 60:
            if self.story_data and self.current_file:
                try:
                    with open(self.current_file, 'w', encoding='utf-8') as f:
                        json.dump(self.story_data, f, ensure_ascii=False, indent=2)
                    self.status_bar.config(text=f"已自动保存到: {os.path.basename(self.current_file)}")
                    self.last_save_time = current_time
                except:
                    pass
        
        self.after(60000, self.check_auto_save)
    
    def load_recent_files(self):
        """加载最近文件列表"""
        try:
            if os.path.exists("recent_files.json"):
                with open("recent_files.json", 'r', encoding='utf-8') as f:
                    self.recent_files = json.load(f)
        except:
            self.recent_files = []
    
    def save_recent_files(self):
        """保存最近文件列表"""
        if self.current_file and self.current_file not in self.recent_files:
            self.recent_files.insert(0, self.current_file)
            if len(self.recent_files) > 10:
                self.recent_files = self.recent_files[:10]
            
            try:
                with open("recent_files.json", 'w', encoding='utf-8') as f:
                    json.dump(self.recent_files, f, ensure_ascii=False, indent=2)
            except:
                pass
    
    def load_hints(self):
        """加载hints.txt文件内容"""
        try:
            if os.path.exists("hints.txt"):
                with open("hints.txt", 'r', encoding='utf-8') as f:
                    user_hints = f.read().strip()
                self.system_hints = f"{user_hints}\n\n{self.system_hints}"
                self.status_bar.config(text="已加载故事设定提示(hints.txt)")
            else:
                self.status_bar.config(text="未找到hints.txt，使用默认系统提示")
        except Exception as e:
            self.status_bar.config(text=f"读取hints.txt失败: {str(e)}")
    
    def update_story_context(self):
        """更新故事上下文"""
        if not self.story_data:
            self.story_context = "这是一个新故事，尚未有内容。"
            return
        
        context_parts = ["当前故事内容：\n"]
        for node_id, node_data in self.story_data.items():
            context_parts.append(f"【{node_id}】")
            context_parts.append(f"说话人: {node_data.get('name', '未知')}")
            context_parts.append(f"内容: {node_data.get('text', '无').replace('[br]', ' ')}")
            
            # 兼容游戏引擎的字段
            if "background" in node_data:
                context_parts.append(f"背景: {node_data['background']}")
            if "sound" in node_data:
                context_parts.append(f"音效: {node_data['sound']}")
            if "display_mode" in node_data:
                context_parts.append(f"显示模式: {node_data['display_mode']}")
            if "expression" in node_data:
                context_parts.append(f"表情: {node_data['expression']}")
            if "ending" in node_data:
                context_parts.append(f"结局: {node_data['ending']}")
            
            # 值系统字段
            if "set_values" in node_data:
                context_parts.append(f"设置值: {node_data['set_values']}")
            if "change_values" in node_data:
                context_parts.append(f"改变值: {node_data['change_values']}")
            if "conditional_next" in node_data:
                context_parts.append(f"条件跳转: {len(node_data['conditional_next'])}个条件")
            
            if "next" in node_data:
                context_parts.append(f"下一段: {node_data['next']}")
            elif "options" in node_data:
                options_text = []
                for i, opt in enumerate(node_data['options']):
                    option_text = f"{i + 1}. {opt['text']} -> {opt['next']}"
                    if "conditions" in opt:
                        option_text += f" [条件: {opt['conditions']}]"
                    options_text.append(option_text)
                context_parts.append(f"选项: {'; '.join(options_text)}")
            
            context_parts.append("---")
        
        self.story_context = "\n".join(context_parts)[:3000]
    
    def create_ui(self):
        # 创建样式
        self.style = ttk.Style()
        self.style.configure("TButton", padding=5)
        self.style.configure("TLabelFrame", padding=10)
        self.style.configure("Header.TLabel", font=("SimHei", 12, "bold"))
        
        # 顶部工具栏
        toolbar = ttk.Frame(self, padding=5)
        toolbar.pack(fill=tk.X)
        
        # 文件操作按钮
        file_frame = ttk.Frame(toolbar)
        file_frame.pack(side=tk.LEFT)
        
        ttk.Button(file_frame, text="新建", command=self.new_project).pack(side=tk.LEFT, padx=2)
        
        # 最近文件下拉菜单
        self.recent_menu = tk.Menu(file_frame, tearoff=0)
        self.recent_button = ttk.Button(file_frame, text="最近文件")
        self.recent_button.pack(side=tk.LEFT, padx=2)
        self.recent_button.bind("<Button-1>", self.show_recent_files)
        
        ttk.Button(file_frame, text="打开", command=self.open_project).pack(side=tk.LEFT, padx=2)
        ttk.Button(file_frame, text="保存", command=self.save_project).pack(side=tk.LEFT, padx=2)
        ttk.Button(file_frame, text="预览", command=self.preview_story).pack(side=tk.LEFT, padx=2)
        
        # 分隔线
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # 编辑工具按钮
        edit_frame = ttk.Frame(toolbar)
        edit_frame.pack(side=tk.LEFT)
        
        # 添加"添加节点"按钮
        ttk.Button(edit_frame, text="添加节点", command=self.add_node).pack(side=tk.LEFT, padx=2)
        ttk.Button(edit_frame, text="复制节点", command=self.duplicate_node).pack(side=tk.LEFT, padx=2)
        ttk.Button(edit_frame, text="删除节点", command=self.delete_node).pack(side=tk.LEFT, padx=2)
        
        # 分隔线
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # AI相关按钮
        ai_frame = ttk.Frame(toolbar)
        ai_frame.pack(side=tk.LEFT)
        
        ttk.Button(ai_frame, text="AI刷新上下文", command=self.refresh_ai_context).pack(side=tk.LEFT, padx=2)
        ttk.Button(ai_frame, text="查看历史", command=self.show_ai_history).pack(side=tk.LEFT, padx=2)
        
        # API设置按钮
        ttk.Button(toolbar, text="AI设置", command=self.show_ai_settings).pack(side=tk.RIGHT, padx=2)
        
        # 主内容区 - 使用PanedWindow
        main_paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 左侧节点列表面板
        left_frame = ttk.Frame(main_paned, width=250)
        main_paned.add(left_frame, weight=1)
        
        ttk.Label(left_frame, text="故事节点列表", style="Header.TLabel").pack(anchor=tk.W, pady=5)
        
        # 节点搜索框
        search_frame = ttk.Frame(left_frame)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(search_frame, text="搜索:").pack(side=tk.LEFT)
        self.node_search = ttk.Entry(search_frame)
        self.node_search.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.node_search.bind("<KeyRelease>", self.filter_nodes)
        
        # 节点列表
        self.node_listbox = tk.Listbox(left_frame)
        self.node_listbox.pack(fill=tk.BOTH, expand=True, padx=5)
        self.node_listbox.bind('<Double-1>', lambda e: self.navigate_to_selected_node())
        
        # 滚动条
        scrollbar = ttk.Scrollbar(self.node_listbox, orient=tk.VERTICAL, command=self.node_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.node_listbox.config(yscrollcommand=scrollbar.set)
        
        # 右侧编辑面板
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=3)
        
        # 创建右侧内容的Notebook（选项卡）
        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 基本设置选项卡
        self.basic_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.basic_frame, text="基本设置")
        
        # 高级设置选项卡
        self.advanced_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.advanced_frame, text="高级设置")
        
        # 值系统选项卡 - 使用新的用户友好界面
        self.values_editor = ValueSystemEditor(self.notebook)
        self.notebook.add(self.values_editor.frame, text="值系统和条件")
        
        # 填充基本设置选项卡
        self.create_basic_tab()
        
        # 填充高级设置选项卡
        self.create_advanced_tab()
        
        # 底部导航
        nav_frame = ttk.Frame(self)
        nav_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=5, padx=5)
        
        ttk.Button(nav_frame, text="← 上一个节点", command=self.prev_node).pack(side=tk.LEFT)
        ttk.Button(nav_frame, text="保存当前节点", command=self.save_current_node).pack(side=tk.RIGHT)
        
        # 状态栏
        status_frame = ttk.Frame(self)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_bar = ttk.Label(status_frame, text="就绪 - 请新建或打开项目", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # AI状态标签
        self.ai_status = ttk.Label(status_frame, text="", foreground="blue", width=30)
        self.ai_status.pack(side=tk.RIGHT)
        
        # 初始化界面状态
        self.update_flow_controls()
        self.update_node_list()
    
    def create_basic_tab(self):
        """创建基本设置选项卡"""
        # 当前节点显示
        ttk.Label(self.basic_frame, text="当前节点:", style="Header.TLabel").pack(anchor=tk.W)
        node_header_frame = ttk.Frame(self.basic_frame)
        node_header_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.node_label = ttk.Label(node_header_frame, text="(未选择节点)", font=("SimHei", 12, "bold"))
        self.node_label.pack(side=tk.LEFT)
        
        ttk.Button(node_header_frame, text="重命名", command=self.rename_node).pack(side=tk.RIGHT)
        
        # 说话人
        speaker_frame = ttk.Frame(self.basic_frame)
        speaker_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(speaker_frame, text="说话人:").pack(side=tk.LEFT)
        self.speaker_entry = ttk.Entry(speaker_frame)
        self.speaker_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # AI辅助按钮 - 生成说话人建议
        ttk.Button(speaker_frame, text="AI建议", command=self.ai_suggest_speaker).pack(side=tk.LEFT, padx=5)
        
        # 对话内容
        dialog_frame = ttk.LabelFrame(self.basic_frame, text="对话内容")
        dialog_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 文本格式工具栏
        format_frame = ttk.Frame(dialog_frame)
        format_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(format_frame, text="蓝色", command=lambda: self.add_text_style('b')).pack(side=tk.LEFT, padx=2)
        ttk.Button(format_frame, text="红色", command=lambda: self.add_text_style('r')).pack(side=tk.LEFT, padx=2)
        ttk.Button(format_frame, text="绿色", command=lambda: self.add_text_style('g')).pack(side=tk.LEFT, padx=2)
        ttk.Button(format_frame, text="黄色", command=lambda: self.add_text_style('y')).pack(side=tk.LEFT, padx=2)
        ttk.Button(format_frame, text="斜体", command=lambda: self.add_text_style('i')).pack(side=tk.LEFT, padx=2)
        ttk.Button(format_frame, text="心理", command=lambda: self.add_text_style('m')).pack(side=tk.LEFT, padx=2)
        ttk.Button(format_frame, text="换行", command=lambda: self.insert_newline()).pack(side=tk.LEFT, padx=2)
        
        # 格式提示标签
        ttk.Label(dialog_frame, text="格式说明：使用按钮添加样式标签，换行必须用[br]！", foreground="gray").pack(
            anchor=tk.W, padx=5)
        
        # AI辅助按钮 - 生成对话
        ttk.Button(dialog_frame, text="AI生成", command=self.ai_generate_dialog).pack(anchor=tk.W, pady=(0, 5), padx=5)
        
        self.dialog_text = scrolledtext.ScrolledText(dialog_frame, height=12, wrap=tk.WORD)
        self.dialog_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        # AI生成提示
        prompt_frame = ttk.Frame(dialog_frame)
        prompt_frame.pack(fill=tk.X, pady=(0, 5), padx=5)
        
        ttk.Label(prompt_frame, text="生成提示:").pack(side=tk.LEFT)
        self.ai_prompt_entry = ttk.Entry(prompt_frame)
        self.ai_prompt_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.ai_prompt_entry.insert(0, "生成一段关于冒险开始的对话，使用[br]换行")
        
        # 剧情走向控制
        control_frame = ttk.LabelFrame(self.basic_frame, text="剧情走向")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 剧情类型选择
        self.flow_type = tk.StringVar(value="continue")
        flow_frame = ttk.Frame(control_frame)
        flow_frame.pack(fill=tk.X, pady=5)
        
        ttk.Radiobutton(flow_frame, text="继续到下一段",
                        variable=self.flow_type, value="continue",
                        command=self.update_flow_controls).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(flow_frame, text="给出选择分支",
                        variable=self.flow_type, value="branch",
                        command=self.update_flow_controls).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(flow_frame, text="故事结束",
                        variable=self.flow_type, value="end",
                        command=self.update_flow_controls).pack(side=tk.LEFT, padx=10)
        
        # AI辅助按钮 - 生成剧情走向
        ttk.Button(flow_frame, text="AI生成剧情", command=self.ai_generate_plot).pack(side=tk.RIGHT, padx=10)
        
        # 下一段设置 (默认显示)
        self.next_frame = ttk.Frame(control_frame)
        self.next_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(self.next_frame, text="下一段标题:").pack(side=tk.LEFT)
        self.next_node_entry = ttk.Entry(self.next_frame, width=15)
        self.next_node_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(self.next_frame, text="创建并跳转",
                   command=self.create_next_node).pack(side=tk.LEFT)
        
        # 分支选项设置 (默认隐藏)
        self.branch_frame = ttk.Frame(control_frame)
        
        # 选项管理框架
        options_management_frame = ttk.LabelFrame(self.branch_frame, text="选项管理")
        options_management_frame.pack(fill=tk.X, pady=5, padx=5)
        
        # 选项列表
        options_list_frame = ttk.Frame(options_management_frame)
        options_list_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(options_list_frame, text="当前选项:").pack(anchor=tk.W)
        
        # 选项列表框
        listbox_frame = ttk.Frame(options_management_frame)
        listbox_frame.pack(fill=tk.X, pady=5)
        
        self.options_listbox = tk.Listbox(listbox_frame, height=6)
        self.options_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.options_listbox.bind('<Double-1>', self.edit_option)
        
        # 选项列表滚动条
        listbox_scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.options_listbox.yview)
        listbox_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.options_listbox.config(yscrollcommand=listbox_scrollbar.set)
        
        # 选项操作按钮
        options_buttons_frame = ttk.Frame(options_management_frame)
        options_buttons_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(options_buttons_frame, text="添加选项", command=self.add_option).pack(side=tk.LEFT, padx=2)
        ttk.Button(options_buttons_frame, text="编辑选项", command=self.edit_option).pack(side=tk.LEFT, padx=2)
        ttk.Button(options_buttons_frame, text="删除选项", command=self.delete_option).pack(side=tk.LEFT, padx=2)
        ttk.Button(options_buttons_frame, text="上移选项", command=self.move_option_up).pack(side=tk.LEFT, padx=2)
        ttk.Button(options_buttons_frame, text="下移选项", command=self.move_option_down).pack(side=tk.LEFT, padx=2)
        
        # AI辅助按钮 - 生成分支选项
        ttk.Button(self.branch_frame, text="AI生成选项", command=self.ai_generate_options).pack(anchor=tk.CENTER,
                                                                                                pady=5)
    
    def create_advanced_tab(self):
        """创建高级设置选项卡（游戏引擎兼容）"""
        # 背景设置
        bg_frame = ttk.LabelFrame(self.advanced_frame, text="背景设置")
        bg_frame.pack(fill=tk.X, pady=5, padx=5)
        
        ttk.Label(bg_frame, text="背景图片:").pack(anchor=tk.W, pady=2)
        bg_input_frame = ttk.Frame(bg_frame)
        bg_input_frame.pack(fill=tk.X, pady=2)
        
        self.bg_entry = ttk.Entry(bg_input_frame)
        self.bg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(bg_input_frame, text="浏览", command=self.browse_background).pack(side=tk.RIGHT)
        
        # 音效设置
        sound_frame = ttk.LabelFrame(self.advanced_frame, text="音效设置")
        sound_frame.pack(fill=tk.X, pady=5, padx=5)
        
        ttk.Label(sound_frame, text="音效文件:").pack(anchor=tk.W, pady=2)
        sound_input_frame = ttk.Frame(sound_frame)
        sound_input_frame.pack(fill=tk.X, pady=2)
        
        self.sound_entry = ttk.Entry(sound_input_frame)
        self.sound_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(sound_input_frame, text="浏览", command=self.browse_sound).pack(side=tk.RIGHT)
        
        # 显示模式设置
        display_frame = ttk.LabelFrame(self.advanced_frame, text="显示模式")
        display_frame.pack(fill=tk.X, pady=5, padx=5)
        
        self.display_mode = tk.StringVar(value="dialog")
        ttk.Radiobutton(display_frame, text="对话框模式",
                        variable=self.display_mode, value="dialog").pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(display_frame, text="全屏文字模式",
                        variable=self.display_mode, value="fullscreen").pack(anchor=tk.W, pady=2)
        
        # 全屏模式颜色设置
        color_frame = ttk.LabelFrame(self.advanced_frame, text="全屏模式颜色设置")
        color_frame.pack(fill=tk.X, pady=5, padx=5)
        
        # 背景颜色
        bg_color_frame = ttk.Frame(color_frame)
        bg_color_frame.pack(fill=tk.X, pady=2)
        ttk.Label(bg_color_frame, text="背景颜色 (RGB):").pack(side=tk.LEFT)
        self.bg_color_entry = ttk.Entry(bg_color_frame, width=15)
        self.bg_color_entry.pack(side=tk.LEFT, padx=5)
        self.bg_color_entry.insert(0, "0,0,0")
        
        # 文字颜色
        text_color_frame = ttk.Frame(color_frame)
        text_color_frame.pack(fill=tk.X, pady=2)
        ttk.Label(text_color_frame, text="文字颜色 (RGB):").pack(side=tk.LEFT)
        self.text_color_entry = ttk.Entry(text_color_frame, width=15)
        self.text_color_entry.pack(side=tk.LEFT, padx=5)
        self.text_color_entry.insert(0, "255,255,255")
        
        # 角色表情设置
        expression_frame = ttk.LabelFrame(self.advanced_frame, text="角色表情")
        expression_frame.pack(fill=tk.X, pady=5, padx=5)
        
        ttk.Label(expression_frame, text="表情:").pack(anchor=tk.W, pady=2)
        self.expression_entry = ttk.Entry(expression_frame)
        self.expression_entry.pack(fill=tk.X, pady=2)
        self.expression_entry.insert(0, "default")
        
        # 结局设置
        ending_frame = ttk.LabelFrame(self.advanced_frame, text="结局设置")
        ending_frame.pack(fill=tk.X, pady=5, padx=5)
        
        ttk.Label(ending_frame, text="结局名称:").pack(anchor=tk.W, pady=2)
        self.ending_entry = ttk.Entry(ending_frame)
        self.ending_entry.pack(fill=tk.X, pady=2)
        
        # 提示信息
        hint_label = ttk.Label(self.advanced_frame,
                               text="提示：这些设置用于与游戏引擎兼容，如果不需要可以留空",
                               foreground="gray")
        hint_label.pack(anchor=tk.W, pady=10, padx=5)
    
    def browse_background(self):
        """浏览背景图片"""
        filename = filedialog.askopenfilename(
            title="选择背景图片",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp"), ("All files", "*.*")]
        )
        if filename:
            self.bg_entry.delete(0, tk.END)
            self.bg_entry.insert(0, os.path.basename(filename))
    
    def browse_sound(self):
        """浏览音效文件"""
        filename = filedialog.askopenfilename(
            title="选择音效文件",
            filetypes=[("Sound files", "*.wav *.mp3 *.ogg"), ("All files", "*.*")]
        )
        if filename:
            self.sound_entry.delete(0, tk.END)
            self.sound_entry.insert(0, os.path.basename(filename))
    
    def add_text_style(self, style):
        """在文本中添加样式标签"""
        try:
            start_idx = self.dialog_text.index(tk.SEL_FIRST)
            end_idx = self.dialog_text.index(tk.SEL_LAST)
            
            selected_text = self.dialog_text.get(start_idx, end_idx)
            
            self.dialog_text.delete(start_idx, end_idx)
            self.dialog_text.insert(start_idx, f"[{style}]{selected_text}[/{style}]")
            
            new_end_idx = f"{start_idx}+{len(f'[{style}]{selected_text}[/{style}]')}c"
            self.dialog_text.tag_add(tk.SEL, start_idx, new_end_idx)
            self.dialog_text.mark_set(tk.INSERT, new_end_idx)
        
        except tk.TclError:
            current_pos = self.dialog_text.index(tk.INSERT)
            self.dialog_text.insert(current_pos, f"[{style}][/{style}]")
            self.dialog_text.mark_set(tk.INSERT, f"{current_pos}+{len(style) + 2}c")
    
    def insert_newline(self):
        """插入换行标记"""
        current_pos = self.dialog_text.index(tk.INSERT)
        self.dialog_text.insert(current_pos, "[br]")
        self.dialog_text.mark_set(tk.INSERT, f"{current_pos}+4c")
    
    def filter_nodes(self, event=None):
        """根据搜索框内容过滤节点列表"""
        search_text = self.node_search.get().lower()
        self.update_node_list(search_text)
    
    def update_node_list(self, filter_text=None):
        """更新节点列表"""
        self.node_listbox.delete(0, tk.END)
        if not self.story_data:
            return
        
        nodes = sorted(self.story_data.keys())
        
        for node in nodes:
            if filter_text and filter_text.lower() not in node.lower():
                continue
            
            self.node_listbox.insert(tk.END, node)
            
            if node == self.current_node:
                self.node_listbox.itemconfig(tk.END, bg="#a0cfff")
    
    def navigate_to_selected_node(self):
        """导航到列表中选中的节点"""
        selection = self.node_listbox.curselection()
        if selection:
            node_id = self.node_listbox.get(selection[0])
            self.navigate_to_node(node_id)
    
    def add_node(self):
        """添加新节点"""
        # 获取新节点名称
        new_node_name = tk.simpledialog.askstring("添加节点", "请输入新节点名称:")
        
        if not new_node_name or not new_node_name.strip():
            return
        
        new_node_name = new_node_name.strip()
        
        # 检查节点是否已存在
        if new_node_name in self.story_data:
            messagebox.showerror("错误", f"节点 '{new_node_name}' 已存在")
            return
        
        # 创建新节点数据
        self.story_data[new_node_name] = {
            "name": "",
            "text": ""
        }
        
        # 更新节点列表
        self.update_node_list()
        
        # 导航到新节点
        self.navigate_to_node(new_node_name)
        
        self.status_bar.config(text=f"已创建新节点: {new_node_name}")
    
    def rename_node(self):
        """重命名当前节点"""
        if not self.current_node:
            messagebox.showwarning("警告", "请先选择一个节点")
            return
        
        new_name = tk.simpledialog.askstring("重命名节点", "请输入新的节点名称:", initialvalue=self.current_node)
        if new_name and new_name.strip() and new_name != self.current_node:
            new_name = new_name.strip()
            
            if new_name in self.story_data:
                messagebox.showerror("错误", f"节点 '{new_name}' 已存在")
                return
            
            self.story_data[new_name] = self.story_data[self.current_node]
            del self.story_data[self.current_node]
            
            for node_id, node_data in self.story_data.items():
                if "next" in node_data and node_data["next"] == self.current_node:
                    node_data["next"] = new_name
                elif "options" in node_data:
                    for option in node_data["options"]:
                        if option.get("next") == self.current_node:
                            option["next"] = new_name
                elif "conditional_next" in node_data:
                    for cond in node_data["conditional_next"]:
                        if cond.get("next") == self.current_node:
                            cond["next"] = new_name
            
            self.navigate_to_node(new_name)
            self.status_bar.config(text=f"节点已重命名为: {new_name}")
    
    def duplicate_node(self):
        """复制当前节点"""
        if not self.current_node or self.current_node not in self.story_data:
            messagebox.showwarning("警告", "请先选择一个节点")
            return
        
        new_name = f"{self.current_node}_copy"
        counter = 1
        
        while new_name in self.story_data:
            counter += 1
            new_name = f"{self.current_node}_copy{counter}"
        
        self.story_data[new_name] = dict(self.story_data[self.current_node])
        
        self.update_node_list()
        self.navigate_to_node(new_name)
        self.status_bar.config(text=f"已复制节点: {new_name}")
    
    def delete_node(self):
        """删除当前节点"""
        if not self.current_node or self.current_node not in self.story_data:
            messagebox.showwarning("警告", "请先选择一个节点")
            return
        
        if len(self.story_data) <= 1:
            messagebox.showwarning("警告", "不能删除最后一个节点")
            return
        
        if messagebox.askyesno("确认删除",
                               f"确定要删除节点 '{self.current_node}' 吗？\n这将同时删除所有指向该节点的引用。"):
            next_node = None
            for node in self.story_data.keys():
                if node != self.current_node:
                    next_node = node
                    break
            
            for node_id, node_data in self.story_data.items():
                if "next" in node_data and node_data["next"] == self.current_node:
                    del node_data["next"]
                elif "options" in node_data:
                    new_options = [opt for opt in node_data["options"] if opt.get("next") != self.current_node]
                    if new_options:
                        node_data["options"] = new_options
                    else:
                        del node_data["options"]
                elif "conditional_next" in node_data:
                    new_conditional = [cond for cond in node_data["conditional_next"] if
                                       cond.get("next") != self.current_node]
                    if new_conditional:
                        node_data["conditional_next"] = new_conditional
                    else:
                        del node_data["conditional_next"]
            
            del self.story_data[self.current_node]
            
            if next_node:
                self.navigate_to_node(next_node)
            else:
                self.current_node = None
                self.node_label.config(text="(未选择节点)")
            
            self.update_node_list()
            self.status_bar.config(text=f"已删除节点: {self.current_node}")
    
    def show_recent_files(self, event):
        """显示最近文件菜单"""
        self.recent_menu.delete(0, tk.END)
        
        if not self.recent_files:
            self.recent_menu.add_command(label="没有最近文件", state=tk.DISABLED)
        else:
            for file_path in self.recent_files[:10]:
                display_name = os.path.basename(file_path)
                self.recent_menu.add_command(
                    label=display_name,
                    command=lambda fp=file_path: self.open_recent_file(fp)
                )
            self.recent_menu.add_separator()
            self.recent_menu.add_command(label="清除列表", command=self.clear_recent_files)
        
        self.recent_menu.post(event.x_root, event.y_root)
    
    def open_recent_file(self, file_path):
        """打开最近的文件"""
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.story_data = json.load(f)
                
                self.current_file = file_path
                start_node = "start" if "start" in self.story_data else next(iter(self.story_data.keys()))
                self.navigate_to_node(start_node)
                self.title(f"AI辅助故事编辑器 - {os.path.basename(file_path)}")
                self.status_bar.config(text=f"已打开文件: {file_path}")
                self.update_story_context()
                self.update_node_list()
                
                if file_path in self.recent_files:
                    self.recent_files.remove(file_path)
                self.recent_files.insert(0, file_path)
                self.save_recent_files()
            
            except Exception as e:
                messagebox.showerror("错误", f"打开文件失败: {str(e)}")
        else:
            messagebox.showerror("错误", f"文件不存在: {file_path}")
            self.recent_files.remove(file_path)
            self.save_recent_files()
    
    def clear_recent_files(self):
        """清除最近文件列表"""
        self.recent_files = []
        self.save_recent_files()
    
    def update_flow_controls(self):
        """根据剧情类型显示相应的控件"""
        flow_type = self.flow_type.get()
        
        if flow_type == "continue":
            self.next_frame.pack(fill=tk.X, pady=5)
            self.branch_frame.pack_forget()
        elif flow_type == "branch":
            self.next_frame.pack_forget()
            self.branch_frame.pack(fill=tk.X, pady=5)
        elif flow_type == "end":
            self.next_frame.pack_forget()
            self.branch_frame.pack_forget()
    
    def update_options_listbox(self):
        """更新选项列表框显示"""
        self.options_listbox.delete(0, tk.END)
        for i, option in enumerate(self.options):
            display_text = f"{i + 1}. {option.get('text', '')} -> {option.get('next', '')}"
            if "conditions" in option:
                display_text += f" [条件]"
            self.options_listbox.insert(tk.END, display_text)
    
    def add_option(self):
        """添加新选项"""
        dialog = OptionEditor(self, "添加选项")
        self.wait_window(dialog.dialog)
        if dialog.result:
            self.options.append(dialog.result)
            self.update_options_listbox()
    
    def edit_option(self, event=None):
        """编辑选中的选项"""
        selection = self.options_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个选项")
            return
        
        index = selection[0]
        option = self.options[index]
        
        dialog = OptionEditor(self, "编辑选项", option)
        self.wait_window(dialog.dialog)
        if dialog.result:
            self.options[index] = dialog.result
            self.update_options_listbox()
    
    def delete_option(self):
        """删除选中的选项"""
        selection = self.options_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个选项")
            return
        
        index = selection[0]
        
        if messagebox.askyesno("确认删除", "确定要删除这个选项吗？"):
            self.options.pop(index)
            self.update_options_listbox()
    
    def move_option_up(self):
        """将选中的选项上移"""
        selection = self.options_listbox.curselection()
        if not selection or selection[0] == 0:
            return
        
        index = selection[0]
        self.options[index], self.options[index - 1] = self.options[index - 1], self.options[index]
        self.update_options_listbox()
        self.options_listbox.select_set(index - 1)
    
    def move_option_down(self):
        """将选中的选项下移"""
        selection = self.options_listbox.curselection()
        if not selection or selection[0] == len(self.options) - 1:
            return
        
        index = selection[0]
        self.options[index], self.options[index + 1] = self.options[index + 1], self.options[index]
        self.update_options_listbox()
        self.options_listbox.select_set(index + 1)
    
    def save_current_node(self):
        """保存当前节点的数据（包含高级设置和值系统）"""
        if not self.current_node:
            messagebox.showwarning("警告", "请先选择一个节点")
            return
        
        speaker = self.speaker_entry.get().strip()
        dialog = self.dialog_text.get(1.0, tk.END).strip().replace("\n", "[br]")
        
        if not dialog:
            messagebox.showwarning("警告", "对话内容不能为空")
            return
        
        # 创建节点数据（兼容游戏引擎格式）
        node_data = {
            "name": speaker,
            "text": dialog
        }
        
        # 添加高级设置字段
        bg = self.bg_entry.get().strip()
        if bg:
            node_data["background"] = bg
        
        sound = self.sound_entry.get().strip()
        if sound:
            node_data["sound"] = sound
        
        display_mode = self.display_mode.get()
        if display_mode != "dialog":
            node_data["display_mode"] = display_mode
        
        expression = self.expression_entry.get().strip()
        if expression and expression != "default":
            node_data["expression"] = expression
        
        bg_color = self.bg_color_entry.get().strip()
        if bg_color and bg_color != "0,0,0":
            node_data["bg_color"] = bg_color
        
        text_color = self.text_color_entry.get().strip()
        if text_color and text_color != "255,255,255":
            node_data["text_color"] = text_color
        
        ending = self.ending_entry.get().strip()
        if ending:
            node_data["ending"] = ending
        
        # 添加值系统字段（从新的编辑器获取）
        values_data = self.values_editor.get_data()
        if values_data["set_values"]:
            node_data["set_values"] = values_data["set_values"]
        if values_data["change_values"]:
            node_data["change_values"] = values_data["change_values"]
        if values_data["conditional_next"]:
            node_data["conditional_next"] = values_data["conditional_next"]
        
        # 根据剧情类型添加相应数据
        flow_type = self.flow_type.get()
        if flow_type == "continue":
            next_node = self.next_node_entry.get().strip()
            if next_node:
                node_data["next"] = next_node
        elif flow_type == "branch":
            if self.options:
                import copy
                node_data["options"] = copy.deepcopy(self.options)
        elif flow_type == "end":
            node_data["ending"] = ending if ending else True
        
        # 保存节点
        self.story_data[self.current_node] = node_data
        self.status_bar.config(text=f"已保存节点: {self.current_node}")
        self.update_node_list()
        
        # 更新故事上下文
        self.update_story_context()
    
    def create_next_node(self):
        """创建下一个节点并跳转"""
        if not self.current_node:
            messagebox.showwarning("警告", "请先选择一个节点")
            return
        
        self.save_current_node()
        
        next_node = self.next_node_entry.get().strip()
        if not next_node:
            messagebox.showwarning("警告", "请输入下一段标题")
            return
        
        if next_node not in self.story_data:
            self.story_data[next_node] = {
                "name": "",
                "text": ""
            }
        
        self.navigate_to_node(next_node)
        self.next_node_entry.delete(0, tk.END)
    
    def create_branches(self):
        """创建分支节点"""
        if not self.current_node:
            messagebox.showwarning("警告", "请先选择一个节点")
            return
        
        self.save_current_node()
        
        # 创建分支节点（如果不存在）
        for option in self.options:
            next_node = option.get("next", "").strip()
            if next_node and next_node not in self.story_data:
                self.story_data[next_node] = {"name": "", "text": ""}
        
        self.update_node_list()
        messagebox.showinfo("成功", "分支节点已创建")
    
    def navigate_to_node(self, node_id):
        """导航到指定节点（加载高级设置和值系统）"""
        if not self.story_data or node_id not in self.story_data:
            messagebox.showerror("错误", f"节点 '{node_id}' 不存在")
            return
        
        if self.current_node and self.current_node in self.story_data:
            self.save_current_node()
        
        self.current_node = node_id
        node_data = self.story_data[node_id]
        
        self.node_label.config(text=node_id)
        self.speaker_entry.delete(0, tk.END)
        self.speaker_entry.insert(0, node_data.get("name", ""))
        
        self.dialog_text.delete(1.0, tk.END)
        self.dialog_text.insert(1.0, node_data.get("text", "").replace("[br]", "\n"))
        
        # 加载高级设置
        self.bg_entry.delete(0, tk.END)
        self.bg_entry.insert(0, node_data.get("background", ""))
        
        self.sound_entry.delete(0, tk.END)
        self.sound_entry.insert(0, node_data.get("sound", ""))
        
        self.display_mode.set(node_data.get("display_mode", "dialog"))
        
        self.expression_entry.delete(0, tk.END)
        self.expression_entry.insert(0, node_data.get("expression", "default"))
        
        self.bg_color_entry.delete(0, tk.END)
        self.bg_color_entry.insert(0, node_data.get("bg_color", "0,0,0"))
        
        self.text_color_entry.delete(0, tk.END)
        self.text_color_entry.insert(0, node_data.get("text_color", "255,255,255"))
        
        self.ending_entry.delete(0, tk.END)
        self.ending_entry.insert(0, node_data.get("ending", ""))
        
        # 加载值系统数据到新编辑器
        values_data = {
            "set_values": node_data.get("set_values", {}),
            "change_values": node_data.get("change_values", {}),
            "conditional_next": node_data.get("conditional_next", [])
        }
        self.values_editor.set_data(values_data)
        
        # 加载选项 - 深拷贝选项列表
        import copy
        self.options = copy.deepcopy(node_data.get("options", []))
        self.update_options_listbox()
        
        # 设置剧情类型
        if "ending" in node_data and node_data["ending"]:
            if isinstance(node_data["ending"], str) and node_data["ending"]:
                self.flow_type.set("end")
            elif node_data["ending"] is True:
                self.flow_type.set("end")
        elif "options" in node_data and len(node_data["options"]) > 0:
            self.flow_type.set("branch")
        else:
            self.flow_type.set("continue")
            self.next_node_entry.delete(0, tk.END)
            self.next_node_entry.insert(0, node_data.get("next", ""))
        
        self.update_flow_controls()
        self.status_bar.config(text=f"已加载节点: {node_id}")
        self.update_node_list()
        
        for i, node in enumerate(sorted(self.story_data.keys())):
            if node == node_id:
                self.node_listbox.see(i)
                break
    
    def prev_node(self):
        """跳转到上一个节点"""
        if not self.current_node:
            messagebox.showinfo("提示", "请先选择一个节点")
            return
        
        prev_nodes = []
        for node_id, node_data in self.story_data.items():
            if "next" in node_data and node_data["next"] == self.current_node:
                prev_nodes.append(node_id)
            elif "options" in node_data:
                for option in node_data["options"]:
                    if option.get("next") == self.current_node:
                        prev_nodes.append(node_id)
            elif "conditional_next" in node_data:
                for cond in node_data["conditional_next"]:
                    if cond.get("next") == self.current_node:
                        prev_nodes.append(node_id)
        
        if not prev_nodes:
            messagebox.showinfo("提示", "没有找到上一个节点")
            return
        elif len(prev_nodes) == 1:
            self.navigate_to_node(prev_nodes[0])
        else:
            self.show_node_choice_dialog("选择上一个节点", prev_nodes)
    
    def show_node_choice_dialog(self, title, nodes):
        """显示节点选择对话框"""
        dialog = tk.Toplevel(self)
        dialog.title(title)
        dialog.geometry("300x300")
        dialog.transient(self)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="请选择节点:").pack(anchor=tk.W, pady=(0, 10))
        
        listbox = tk.Listbox(frame)
        listbox.pack(fill=tk.BOTH, expand=True)
        for node in nodes:
            listbox.insert(tk.END, node)
        
        scrollbar = ttk.Scrollbar(listbox, orient=tk.VERTICAL, command=listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        listbox.config(yscrollcommand=scrollbar.set)
        
        def on_select():
            selection = listbox.curselection()
            if selection:
                node_id = listbox.get(selection[0])
                dialog.destroy()
                self.navigate_to_node(node_id)
        
        ttk.Button(frame, text="确定", command=on_select).pack(pady=10)
        listbox.bind('<Double-1>', lambda e: on_select())
    
    def new_project(self, show_welcome=True):
        """创建新项目"""
        if self.story_data and messagebox.askyesno("保存", "是否保存当前项目？"):
            self.save_project()
        
        self.story_data = {
            "start": {
                "name": "旁白",
                "text": "欢迎来到这个故事。[br]请开始你的冒险吧！[br][m]这是一个自定义标记示例[/m]",
                "display_mode": "dialog"
            }
        }
        self.current_file = None
        self.options = []  # 清空选项
        self.navigate_to_node("start")
        self.title("AI辅助故事编辑器 - 无限选项版")
        
        if show_welcome:
            messagebox.showinfo("欢迎",
                                "新故事已创建！\n\n"
                                "新增功能：\n"
                                "- 支持无限数量的选项\n"
                                "- 选项可以添加、编辑、删除和重新排序\n"
                                "- 更直观的选项管理界面\n"
                                "- 完整的条件判断和值系统")
        
        self.update_story_context()
    
    def open_project(self):
        """打开现有项目"""
        if self.story_data and messagebox.askyesno("保存", "是否保存当前项目？"):
            self.save_project()
        
        filename = filedialog.askopenfilename(
            title="打开故事文件",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    self.story_data = json.load(f)
                
                self.current_file = filename
                start_node = "start" if "start" in self.story_data else next(iter(self.story_data.keys()))
                self.navigate_to_node(start_node)
                self.title(f"AI辅助故事编辑器 - {os.path.basename(filename)}")
                self.status_bar.config(text=f"已打开文件: {filename}")
                
                self.save_recent_files()
                self.update_story_context()
                self.ai_status.config(text="已加载故事内容到AI上下文", foreground="green")
                self.after(5000, lambda: self.ai_status.config(text=""))
            
            except Exception as e:
                messagebox.showerror("错误", f"打开文件失败: {str(e)}")
                if not self.story_data:
                    self.new_project(show_welcome=False)
    
    def save_project(self):
        """保存项目"""
        if self.current_node:
            self.save_current_node()
        
        if self.current_file:
            try:
                with open(self.current_file, 'w', encoding='utf-8') as f:
                    json.dump(self.story_data, f, ensure_ascii=False, indent=2)
                self.status_bar.config(text=f"已保存到: {self.current_file}")
                self.last_save_time = time.time()
                self.save_recent_files()
            except Exception as e:
                messagebox.showerror("错误", f"保存文件失败: {str(e)}")
        else:
            self.save_project_as()
    
    def save_project_as(self):
        """另存为新项目"""
        filename = filedialog.asksaveasfilename(
            title="保存故事文件",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            self.current_file = filename
            self.save_project()
            self.title(f"AI辅助故事编辑器 - {os.path.basename(filename)}")
    
    def preview_story(self):
        """简单预览故事（显示高级设置和值系统信息）"""
        if not self.story_data:
            messagebox.showinfo("提示", "没有故事内容可预览")
            return
        
        if self.current_node:
            self.save_current_node()
        
        preview = tk.Toplevel(self)
        preview.title("故事预览（无限选项版）")
        preview.geometry("900x700")
        preview.transient(self)
        
        text_area = scrolledtext.ScrolledText(preview, wrap=tk.WORD)
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_area.config(state=tk.DISABLED)
        
        text_area.config(state=tk.NORMAL)
        text_area.insert(tk.END, "故事节点预览（无限选项版）:\n\n")
        
        for node_id, node_data in self.story_data.items():
            text_area.insert(tk.END, f"【{node_id}】\n")
            text_area.insert(tk.END, f"说话人: {node_data.get('name', '未知')}\n")
            text_area.insert(tk.END, f"内容: {node_data.get('text', '无').replace('[br]', '\n')}\n")
            
            advanced_fields = []
            if "background" in node_data:
                advanced_fields.append(f"背景: {node_data['background']}")
            if "sound" in node_data:
                advanced_fields.append(f"音效: {node_data['sound']}")
            if "display_mode" in node_data:
                advanced_fields.append(f"显示模式: {node_data['display_mode']}")
            if "expression" in node_data:
                advanced_fields.append(f"表情: {node_data['expression']}")
            if "bg_color" in node_data:
                advanced_fields.append(f"背景颜色: {node_data['bg_color']}")
            if "text_color" in node_data:
                advanced_fields.append(f"文字颜色: {node_data['text_color']}")
            if "ending" in node_data:
                advanced_fields.append(f"结局: {node_data['ending']}")
            
            # 值系统字段
            if "set_values" in node_data:
                advanced_fields.append(f"设置值: {node_data['set_values']}")
            if "change_values" in node_data:
                advanced_fields.append(f"改变值: {node_data['change_values']}")
            if "conditional_next" in node_data:
                advanced_fields.append(f"条件跳转: {len(node_data['conditional_next'])}个")
            
            if advanced_fields:
                text_area.insert(tk.END, "高级设置: " + ", ".join(advanced_fields) + "\n")
            
            if "next" in node_data:
                text_area.insert(tk.END, f"下一段: {node_data['next']}\n")
            elif "options" in node_data:
                text_area.insert(tk.END, f"选项 ({len(node_data['options'])}个):\n")
                for i, option in enumerate(node_data['options']):
                    option_text = f"  {i + 1}. {option['text']} -> {option['next']}"
                    if "conditions" in option:
                        option_text += f" [条件: {option['conditions']}]"
                    text_area.insert(tk.END, option_text + "\n")
            
            text_area.insert(tk.END, "\n" + "-" * 70 + "\n\n")
        
        text_area.config(state=tk.DISABLED)
        
        ttk.Button(preview, text="关闭预览", command=preview.destroy).pack(pady=10)
    
    def show_ai_settings(self):
        """显示AI设置对话框"""
        dialog = tk.Toplevel(self)
        dialog.title("AI设置")
        dialog.geometry("450x300")
        dialog.transient(self)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="API密钥:", font=("SimHei", 10, "bold")).pack(anchor=tk.W, pady=5)
        self.api_key_entry = ttk.Entry(frame, show="*")
        self.api_key_entry.pack(fill=tk.X, pady=5)
        self.api_key_entry.insert(0, self.api_key)
        
        ttk.Label(frame, text="API地址:", font=("SimHei", 10, "bold")).pack(anchor=tk.W, pady=5)
        self.api_url_entry = ttk.Entry(frame)
        self.api_url_entry.pack(fill=tk.X, pady=5)
        self.api_url_entry.insert(0, self.api_url)
        
        ttk.Label(frame, text="模型名称:", font=("SimHei", 10, "bold")).pack(anchor=tk.W, pady=5)
        self.model_name_entry = ttk.Entry(frame)
        self.model_name_entry.pack(fill=tk.X, pady=5)
        self.model_name_entry.insert(0, self.model_name)
        
        ttk.Label(frame, text="提示: 可使用OpenAI API或兼容的API（如Moonshot）", foreground="gray").pack(anchor=tk.W,
                                                                                                       pady=5)
        
        def save_settings():
            self.api_key = self.api_key_entry.get().strip()
            self.api_url = self.api_url_entry.get().strip()
            self.model_name = self.model_name_entry.get().strip() or "moonshot-v1-8k"
            dialog.destroy()
        
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=10)
        
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="保存", command=save_settings).pack(side=tk.RIGHT, padx=5)
    
    def refresh_ai_context(self):
        """刷新AI上下文"""
        if self.current_node:
            self.save_current_node()
        self.update_story_context()
        self.ai_status.config(text="AI上下文已刷新", foreground="green")
        self.after(3000, lambda: self.ai_status.config(text=""))
    
    def show_ai_history(self):
        """显示AI历史记录"""
        if not self.last_ai_response:
            messagebox.showinfo("AI历史", "暂无AI交互记录")
            return
        
        dialog = tk.Toplevel(self)
        dialog.title("AI历史记录")
        dialog.geometry("600x400")
        dialog.transient(self)
        
        text_area = scrolledtext.ScrolledText(dialog, wrap=tk.WORD)
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_area.insert(tk.END, "最后一次AI响应:\n\n")
        text_area.insert(tk.END, self.last_ai_response)
        text_area.config(state=tk.DISABLED)
        
        ttk.Button(dialog, text="关闭", command=dialog.destroy).pack(pady=10)
    
    def ai_suggest_speaker(self):
        """AI生成说话人建议"""
        if not self.api_key:
            messagebox.showwarning("警告", "请先在AI设置中填写API密钥")
            return
        
        if not self.current_node:
            messagebox.showwarning("警告", "请先选择一个节点")
            return
        
        current_text = self.dialog_text.get(1.0, tk.END).strip()[:200]
        
        prompt = f"根据以下故事内容，建议一个合适的说话人名称（只需返回名称，不要解释）：{current_text}"
        
        self.ai_status.config(text="AI正在生成说话人建议...")
        threading.Thread(target=self._call_ai_api, args=(prompt, "speaker")).start()
    
    def ai_generate_dialog(self):
        """AI生成对话内容"""
        if not self.api_key:
            messagebox.showwarning("警告", "请先在AI设置中填写API密钥")
            return
        
        if not self.current_node:
            messagebox.showwarning("警告", "请先选择一个节点")
            return
        
        prompt_text = self.ai_prompt_entry.get().strip()
        if not prompt_text:
            messagebox.showwarning("警告", "请输入生成提示")
            return
        
        speaker = self.speaker_entry.get().strip() or "未知角色"
        
        prompt = (
            f"请为'{speaker}'生成一段对话，要求：{prompt_text}。\n"
            f"必须严格遵循以下格式规则：\n"
            f"{self.format_tags}\n"
            "只返回对话内容，不要添加解释。换行必须用[br]！"
        )
        
        self.ai_status.config(text="AI正在生成对话内容...")
        threading.Thread(target=self._call_ai_api, args=(prompt, "dialog")).start()
    
    def ai_generate_options(self):
        """AI生成分支选项"""
        if not self.api_key:
            messagebox.showwarning("警告", "请先在AI设置中填写API密钥")
            return
        
        if not self.current_node:
            messagebox.showwarning("警告", "请先选择一个节点")
            return
        
        current_text = self.dialog_text.get(1.0, tk.END).strip()[:300]
        
        prompt = (
            f"根据以下故事内容，生成多个可能的选择分支，用于推动剧情发展。\n"
            f"每个选项包含选项文本和下一步节点名称。选项文本中需要换行时必须用[br]。\n"
            f"格式：选项文本->节点名称（每行一个选项）\n"
            f"故事内容：{current_text}"
        )
        
        self.ai_status.config(text="AI正在生成分支选项...")
        threading.Thread(target=self._call_ai_api, args=(prompt, "options")).start()
    
    def ai_generate_plot(self):
        """AI生成剧情走向建议"""
        if not self.api_key:
            messagebox.showwarning("警告", "请先在AI设置中填写API密钥")
            return
        
        if not self.current_node:
            messagebox.showwarning("警告", "请先选择一个节点")
            return
        
        current_text = self.dialog_text.get(1.0, tk.END).strip()[:300]
        
        prompt = (
            f"根据以下故事内容，建议一个合适的剧情走向，包括下一步的节点标题和简要描述。\n"
            f"描述中需要换行时必须用[br]。\n"
            f"只需返回节点标题和描述，用->分隔。\n"
            f"故事内容：{current_text}"
        )
        
        self.ai_status.config(text="AI正在生成剧情走向...")
        threading.Thread(target=self._call_ai_api, args=(prompt, "plot")).start()
    
    def _call_ai_api(self, prompt, result_type):
        """调用AI API并处理结果"""
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            messages = [
                {"role": "system", "content": self.system_hints},
                {"role": "user", "content": f"当前故事进度：{self.story_context}"},
                {"role": "user", "content": prompt}
            ]
            
            data = {
                "model": self.model_name,
                "messages": messages,
                "temperature": 0.7
            }
            
            response = requests.post(f"{self.api_url}/chat/completions", headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            ai_content = result["choices"][0]["message"]["content"].strip()
            self.last_ai_response = ai_content
            
            self._handle_ai_result(ai_content, result_type)
        
        except Exception as e:
            error_msg = str(e)
            self.after(0, lambda: self.ai_status.config(text=f"AI调用失败: {error_msg}", foreground="red"))
        finally:
            self.after(5000, lambda: self.ai_status.config(text=""))
    
    def _handle_ai_result(self, content, result_type):
        """处理AI返回的结果"""
        if result_type == "speaker":
            self.after(0, lambda: self.speaker_entry.delete(0, tk.END))
            self.after(0, lambda: self.speaker_entry.insert(0, content))
            self.after(0, lambda: self.ai_status.config(text="AI已生成说话人建议", foreground="green"))
        
        elif result_type == "dialog":
            self.after(0, lambda: self.dialog_text.delete(1.0, tk.END))
            self.after(0, lambda: self.dialog_text.insert(1.0, content))
            self.after(0, lambda: self.ai_status.config(text="AI已生成对话内容", foreground="green"))
        
        elif result_type == "options":
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            new_options = []
            
            for line in lines:
                if "->" in line:
                    parts = line.split("->", 1)
                    if len(parts) == 2:
                        new_options.append({"text": parts[0].strip(), "next": parts[1].strip()})
            
            if new_options:
                self.options = new_options
                self.update_options_listbox()
                self.after(0, lambda: self.ai_status.config(text=f"AI已生成{len(new_options)}个分支选项",
                                                            foreground="green"))
            else:
                self.after(0, lambda: self.ai_status.config(text="AI未能生成有效选项", foreground="orange"))
        
        elif result_type == "plot":
            if "->" in content:
                parts = content.split("->", 1)
                if len(parts) == 2:
                    node_title = parts[0].strip()
                    description = parts[1].strip()
                    
                    self.after(0, lambda: self.next_node_entry.delete(0, tk.END))
                    self.after(0, lambda: self.next_node_entry.insert(0, node_title))
                    
                    current_dialog = self.dialog_text.get(1.0, tk.END).strip()
                    if not current_dialog:
                        self.after(0, lambda: self.dialog_text.delete(1.0, tk.END))
                        self.after(0, lambda: self.dialog_text.insert(1.0, description))
            
            self.after(0, lambda: self.ai_status.config(text="AI已生成剧情走向建议", foreground="green"))


# 解决Python 3.10以下版本没有simpledialog的问题
try:
    from tkinter import simpledialog
except ImportError:
    import tkinter.simpledialog as simpledialog

if __name__ == "__main__":
    app = AIStoryEditor()
    app.mainloop()