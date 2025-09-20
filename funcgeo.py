import tkinter as tk
import re
import time
import threading
from tkinter import simpledialog, messagebox, scrolledtext
import sympy as sp
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from sympy import symbols, Eq, solve, sqrt, sin, cos, tan, cot, log, exp, I, pi
from sympy import nsolve, Polygon, Point, Segment, Line, Circle
from sympy.geometry import Triangle as SymTriangle


class GeometryApp:
    def __init__(self, master):
        self.master = master
        master.title("几何分析")
        master.geometry("1300x1000")
        
        master.attributes('-fullscreen', True)  # 全屏
        # 按ESC键退出全屏/F11进入全屏
        master.bind('<Escape>', lambda e: master.attributes('-fullscreen', False))
        master.bind('<F11>', lambda e: master.attributes('-fullscreen', True))
        
        self.font_style = ('Microsoft YaHei', 10)
        self.points = []
        self.functions = []
        self.shapes = []  # 存储图形对象
        self.x, self.y = symbols('x y')
        
        # 创建主框架
        main_frame = tk.Frame(master, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧面板 - 数据和操作
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # 点列表
        point_frame = tk.LabelFrame(left_frame, text="点列表", font=self.font_style)
        point_frame.pack(fill=tk.X, pady=(0, 5))
        
        point_control_frame = tk.Frame(point_frame)
        point_control_frame.pack(fill=tk.X, padx=5, pady=2)
        
        tk.Label(point_control_frame, text="点标签:", font=self.font_style).pack(side=tk.LEFT)
        self.point_label_var = tk.StringVar()
        self.point_label_entry = tk.Entry(point_control_frame, textvariable=self.point_label_var, width=5)
        self.point_label_entry.pack(side=tk.LEFT, padx=5)
        
        self.point_listbox = tk.Listbox(point_frame, width=30, height=8, font=self.font_style, selectmode=tk.MULTIPLE)
        self.point_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 函数列表
        func_frame = tk.LabelFrame(left_frame, text="函数列表", font=self.font_style)
        func_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.func_listbox = tk.Listbox(func_frame, width=30, height=8, font=self.font_style, selectmode=tk.MULTIPLE)
        self.func_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 图形列表
        shape_frame = tk.LabelFrame(left_frame, text="图形列表", font=self.font_style)
        shape_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.shape_listbox = tk.Listbox(shape_frame, width=30, height=8, font=self.font_style, selectmode=tk.MULTIPLE)
        self.shape_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 操作按钮框架
        btn_frame = tk.LabelFrame(left_frame, text="操作", font=self.font_style)
        btn_frame.pack(fill=tk.X, pady=5)
        
        # 第一行按钮
        btn_row1 = tk.Frame(btn_frame)
        btn_row1.pack(fill=tk.X, pady=2)
        
        btn_config_row1 = [
            ("添加点", self.add_point),
            ("添加函数", self.add_function),
            ("删除所选", self.delete_selected),
        ]
        
        for text, cmd in btn_config_row1:
            btn = tk.Button(btn_row1, text=text, command=cmd,
                            font=self.font_style, width=10, height=1)
            btn.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        
        # 第二行按钮
        btn_row2 = tk.Frame(btn_frame)
        btn_row2.pack(fill=tk.X, pady=2)
        
        btn_config_row2 = [
            ("两点距离", self.calculate_distance),
            ("直线方程", self.get_equation),
            ("求交点", self.find_intersection_menu),
        ]
        
        for text, cmd in btn_config_row2:
            btn = tk.Button(btn_row2, text=text, command=cmd,
                            font=self.font_style, width=10, height=1)
            btn.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        
        # 第三行按钮
        btn_row3 = tk.Frame(btn_frame)
        btn_row3.pack(fill=tk.X, pady=2)
        
        btn_config_row3 = [
            ("三角形面积", self.triangle_area),
            ("解未知点", self.solve_unknown_menu),
            ("创建图形", self.create_shape_menu),
        ]
        
        for text, cmd in btn_config_row3:
            btn = tk.Button(btn_row3, text=text, command=cmd,
                            font=self.font_style, width=10, height=1)
            btn.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        
        # 第四行按钮
        btn_row4 = tk.Frame(btn_frame)
        btn_row4.pack(fill=tk.X, pady=2)
        
        btn_config_row4 = [
            ("测试性质", self.test_properties),
            ("刷新图形", self.plot_all),
        ]
        
        for text, cmd in btn_config_row4:
            btn = tk.Button(btn_row4, text=text, command=cmd,
                            font=self.font_style, width=10, height=1)
            btn.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        
        # 右侧面板 - 图形和日志
        right_frame = tk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 图形框架
        plot_frame = tk.LabelFrame(right_frame, text="几何可视化", font=self.font_style)
        plot_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        self.figure = plt.Figure(figsize=(8, 6), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.ax.set_xlabel('X轴', fontsize=12)
        self.ax.set_ylabel('Y轴', fontsize=12)
        self.ax.set_title('几何图形', fontsize=14)
        self.ax.grid(True)
        
        # 日志框架
        log_frame = tk.LabelFrame(right_frame, text="操作日志", font=self.font_style)
        log_frame.pack(fill=tk.BOTH, expand=False, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, width=80, height=8, font=self.font_style)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_text.config(state=tk.DISABLED)
        
        self.plot_all()
        self.log("几何分析工具已启动")
    
    def log(self, message):
        """添加日志信息"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def plot_all(self):
        """绘制所有点、函数和图形"""
        self.ax.clear()
        
        self.ax.axhline(0, color='black', lw=0.5)
        self.ax.axvline(0, color='black', lw=0.5)
        
        # 绘制点
        if self.points:
            x_values = []
            y_values = []
            labels = []
            invalid_points = []
            
            for p in self.points:
                try:
                    x_val = complex(p['x'].evalf()).real
                    y_val = complex(p['y'].evalf()).real
                    x_values.append(float(x_val))
                    y_values.append(float(y_val))
                    labels.append(p['label'])
                except:
                    invalid_points.append(p['label'])
                    continue
            
            if x_values:
                self.ax.scatter(x_values, y_values, color='red', zorder=5)
                for i, txt in enumerate(labels):
                    self.ax.annotate(txt, (x_values[i], y_values[i]),
                                     xytext=(5, 5), textcoords='offset points')
            
            if invalid_points:
                self.log(f"警告: 以下点无法绘制: {', '.join(invalid_points)}")
        
        # 绘制函数
        for func in self.functions:
            try:
                # 处理x=常数的函数
                if func['type'] == 'x_constant':
                    x_val = float(complex(func['value'].evalf()).real)
                    self.ax.axvline(x=x_val, label=func['label'])
                    continue
                
                # 处理y=表达式的函数
                # 确定x范围
                if self.points:
                    valid_points = [p for p in self.points if not isinstance(p['x'], str)]
                    if valid_points:
                        x_vals = [complex(p['x'].evalf()).real for p in valid_points]
                        x_min, x_max = min(x_vals), max(x_vals)
                        x_range = np.linspace(x_min - 2, x_max + 2, 1000)
                    else:
                        x_range = np.linspace(-10, 10, 1000)
                else:
                    x_range = np.linspace(-10, 10, 1000)
                
                f = sp.lambdify(self.x, func['expr'], modules=['numpy'])
                y_values = f(x_range)
                y_values = np.real(y_values)
                valid = np.isfinite(y_values)
                
                # 处理不连续点
                indices = np.where(np.abs(np.diff(valid)) == 1)[0] + 1
                x_segments = np.split(x_range, indices)
                y_segments = np.split(y_values, indices)
                
                for x_seg, y_seg in zip(x_segments, y_segments):
                    valid_seg = np.isfinite(y_seg)
                    if np.any(valid_seg):
                        self.ax.plot(x_seg[valid_seg], y_seg[valid_seg],
                                     label=func['label'])
            except Exception as e:
                self.log(f"警告: 函数 {func['label']} 绘制失败: {str(e)}")
                continue
        
        # 绘制图形
        for shape in self.shapes:
            try:
                if shape['type'] == 'circle':
                    center = shape['center']
                    radius = shape['radius']
                    
                    # 绘制圆
                    cx = complex(center['x'].evalf()).real
                    cy = complex(center['y'].evalf()).real
                    r = complex(radius.evalf()).real
                    
                    circle = plt.Circle((cx, cy), r, fill=False, color='blue')
                    self.ax.add_patch(circle)
                    
                    # 标注圆心
                    self.ax.scatter([cx], [cy], color='blue')
                    self.ax.annotate(shape['label'], (cx, cy), xytext=(5, 5),
                                     textcoords='offset points', color='blue')
                
                elif shape['type'] == 'polygon':
                    points = shape['points']
                    x_vals = []
                    y_vals = []
                    
                    for p in points:
                        x_val = complex(p['x'].evalf()).real
                        y_val = complex(p['y'].evalf()).real
                        x_vals.append(x_val)
                        y_vals.append(y_val)
                    
                    # 闭合多边形
                    x_vals.append(x_vals[0])
                    y_vals.append(y_vals[0])
                    
                    self.ax.plot(x_vals, y_vals, color='green', label=shape['label'])
                    
                    # 标注多边形
                    centroid_x = sum(x_vals[:-1]) / len(x_vals[:-1])
                    centroid_y = sum(y_vals[:-1]) / len(y_vals[:-1])
                    self.ax.annotate(shape['label'], (centroid_x, centroid_y),
                                     xytext=(5, 5), textcoords='offset points', color='green')
            
            except Exception as e:
                self.log(f"警告: 图形 {shape['label']} 绘制失败: {str(e)}")
                continue
        
        self.ax.legend()
        self.ax.set_xlim(auto=True)
        self.ax.set_ylim(auto=True)
        self.ax.set_aspect('equal', adjustable='box')
        self.canvas.draw()
        self.log("图形已刷新")
    
    def parse_point_input(self, input_str):
        """解析点输入字符串，支持多种格式"""
        # 处理带标签的格式，如 A(1,2) 或 B(3, sin(10))
        label_match = re.match(r'^([A-Za-z]+)\(([^)]+)\)$', input_str)
        if label_match:
            label = label_match.group(1)
            coords_str = label_match.group(2)
            # 从输入框中获取标签（如果有）
            entry_label = self.point_label_var.get().strip()
            if entry_label:
                label = entry_label
            x_str, y_str = self.parse_coordinates(coords_str)
            return label, x_str, y_str
        
        # 处理不带标签的格式
        entry_label = self.point_label_var.get().strip()
        if not entry_label:
            # 自动生成标签
            entry_label = chr(65 + len(self.points))
        
        x_str, y_str = self.parse_coordinates(input_str)
        return entry_label, x_str, y_str
    
    def parse_coordinates(self, coord_str):
        """解析坐标字符串"""
        # 移除所有空格和中文逗号
        coord_str = coord_str.replace(" ", "").replace("，", ",")
        
        # 处理括号格式（支持中文括号）
        if (coord_str.startswith("(") and coord_str.endswith(")")) or \
                (coord_str.startswith("（") and coord_str.endswith("）")):
            coord_str = coord_str[1:-1]
        
        # 分割字符串
        parts = coord_str.split(",")
        if len(parts) != 2:
            raise ValueError("请输入两个坐标值，用逗号分隔")
        
        return parts[0], parts[1]
    
    def parse_expression(self, expr_str):
        """解析数学表达式"""
        try:
            # 替换常见函数和运算符
            expr_str = expr_str.replace('^', '**')
            expr_str = expr_str.replace('π', 'pi')
            expr_str = expr_str.replace('π', 'pi')  # 中文π
            expr_str = expr_str.replace('ｅ', 'E')  # 中文e
            
            # 处理隐式乘法
            patterns = [
                r'(\d)([a-zA-Z])',  # 数字后跟字母，如 2x -> 2*x
                r'(\d)(\()',  # 数字后跟括号，如 2(x+1) -> 2*(x+1)
                r'(\))([a-zA-Z])',  # 括号后跟字母，如 (x+1)x -> (x+1)*x
                r'(\))(\()'  # 括号后跟括号，如 (x+1)(x+2) -> (x+1)*(x+2)
            ]
            
            for pattern in patterns:
                expr_str = re.sub(pattern, r'\1*\2', expr_str)
            
            return sp.sympify(expr_str, evaluate=False)
        except Exception as e:
            raise ValueError(f"表达式解析失败: {e}\n输入的表达式: {expr_str}")
    
    def parse_selected_points(self, point_strings):
        """从字符串列表解析选中的点"""
        selected_points = []
        for ps in point_strings:
            label = re.match(r'^[A-Za-z]+', ps).group()  # 提取标签部分
            for p in self.points:
                if p['label'] == label:
                    selected_points.append(p)
                    break
        return selected_points
    
    def add_point(self):
        """添加点"""
        input_str = simpledialog.askstring("输入点坐标",
                                           "请输入点坐标（格式: x,y 或 (x,y) 或 A(x,y)）:\n支持表达式如: 2+3, sin(π/2)",
                                           parent=self.master)
        if not input_str:
            return
        
        try:
            label, x_str, y_str = self.parse_point_input(input_str)
            x = self.parse_expression(x_str)
            y = self.parse_expression(y_str)
            
            # 检查标签是否已存在
            for p in self.points:
                if p['label'] == label:
                    if not messagebox.askyesno("确认", f"点 {label} 已存在，是否替换？"):
                        return
                    # 移除已存在的点
                    self.points = [p for p in self.points if p['label'] != label]
                    # 更新列表框
                    self.point_listbox.delete(0, tk.END)
                    for p in self.points:
                        self.point_listbox.insert(tk.END, f"{p['label']}({p['x']}, {p['y']})")
                    break
            
            self.points.append({'label': label, 'x': x, 'y': y})
            self.point_listbox.insert(tk.END, f"{label}({x}, {y})")
            self.log(f"已添加点 {label}({x}, {y})")
            self.point_label_var.set("")  # 清空标签输入框
            self.plot_all()
        except Exception as e:
            messagebox.showerror("错误", f"无效输入: {e}")
    
    def add_function(self):
        """添加函数"""
        func_str = simpledialog.askstring("输入函数",
                                          "请输入函数（格式: y=表达式 或 x=常数）:\n例如: y=2*x+1, y=sin(x), x=3",
                                          parent=self.master)
        if not func_str:
            return
        
        try:
            if '=' not in func_str:
                raise ValueError("函数格式错误，应包含等号")
            
            # 分割函数名和表达式
            parts = func_str.split('=', 1)
            left_side = parts[0].strip().lower()
            expr_str = parts[1].strip()
            
            # 处理x=常数的函数
            if left_side == 'x':
                value = self.parse_expression(expr_str)
                label = f"x_eq_{len(self.functions) + 1}"
                
                self.functions.append({
                    'type': 'x_constant',
                    'label': label,
                    'value': value
                })
                self.func_listbox.insert(tk.END, f"{label}: x = {value}")
                self.log(f"已添加函数 {label}: x = {value}")
            
            # 处理y=表达式的函数
            elif left_side == 'y':
                expr = self.parse_expression(expr_str)
                label = f"f{len(self.functions) + 1}"
                
                self.functions.append({
                    'type': 'y_expression',
                    'label': label,
                    'expr': expr
                })
                self.func_listbox.insert(tk.END, f"{label}: y = {expr}")
                self.log(f"已添加函数 {label}: y = {expr}")
            
            else:
                self.log(f"警告: 函数应以'y='或'x='开头，但收到'{left_side}='")
            
            self.plot_all()
        except Exception as e:
            messagebox.showerror("错误", f"无效函数: {e}")
    
    def delete_selected(self):
        """删除所选点、函数或图形"""
        # 删除所选点
        selected_points = self.point_listbox.curselection()
        for idx in reversed(selected_points):
            point_str = self.point_listbox.get(idx)
            label = re.match(r'^[A-Za-z]+', point_str).group()
            self.points = [p for p in self.points if p['label'] != label]
            self.point_listbox.delete(idx)
            self.log(f"已删除点 {label}")
        
        # 删除所选函数
        selected_funcs = self.func_listbox.curselection()
        for idx in reversed(selected_funcs):
            func_str = self.func_listbox.get(idx)
            label = func_str.split(':')[0].strip()
            self.functions = [f for f in self.functions if f['label'] != label]
            self.func_listbox.delete(idx)
            self.log(f"已删除函数 {label}")
        
        # 删除所选图形
        selected_shapes = self.shape_listbox.curselection()
        for idx in reversed(selected_shapes):
            shape_str = self.shape_listbox.get(idx)
            label = shape_str.split('(')[0].strip()
            self.shapes = [s for s in self.shapes if s['label'] != label]
            self.shape_listbox.delete(idx)
            self.log(f"已删除图形 {label}")
        
        self.plot_all()
    
    def select_items_dialog(self, title, items, required_num, multi_select=True):
        """创建选择对话框"""
        select_win = tk.Toplevel(self.master)
        select_win.title(title)
        select_win.transient(self.master)
        select_win.grab_set()
        
        tk.Label(select_win, text=f"请选择 {required_num} 个项:",
                 font=self.font_style).pack(padx=10, pady=5)
        
        listbox = tk.Listbox(select_win, selectmode=tk.MULTIPLE if multi_select else tk.SINGLE,
                             font=self.font_style, width=50, height=10)
        listbox.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        
        for item in items:
            listbox.insert(tk.END, item)
        
        selected = []
        
        def on_confirm():
            nonlocal selected
            selections = listbox.curselection()
            if len(selections) != required_num:
                messagebox.showerror("错误", f"请选择恰好 {required_num} 个项.")
                return
            selected = [items[i] for i in selections]
            select_win.destroy()
        
        def on_cancel():
            select_win.destroy()
        
        btn_frame = tk.Frame(select_win)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="确认", command=on_confirm,
                  font=self.font_style).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="取消", command=on_cancel,
                  font=self.font_style).pack(side=tk.LEFT, padx=5)
        
        select_win.wait_window()
        return selected
    
    def get_equation(self):
        """获取两点确定的直线方程"""
        if len(self.points) < 2:
            messagebox.showerror("错误", "至少需要两个点才能确定直线方程")
            return
        
        point_strings = self.select_items_dialog("选择点",
                                                 [f"{p['label']}({p['x']}, {p['y']})" for p in self.points],
                                                 2)
        if not point_strings:
            return
        
        try:
            points = self.parse_selected_points(point_strings)
            p1, p2 = points[0], points[1]
            x1, y1 = p1['x'], p1['y']
            x2, y2 = p2['x'], p2['y']
            
            # 计算直线方程
            if x1 == x2:
                equation = f"x = {sp.simplify(x1)}"
                expr = None
                func_type = 'x_constant'
                value = x1
            else:
                m = (y2 - y1) / (x2 - x1)
                b = y1 - m * x1
                equation = f"y = {sp.simplify(m)}x + {sp.simplify(b)}"
                expr = sp.simplify(m) * self.x + sp.simplify(b)
                func_type = 'y_expression'
                value = None
            
            # 显示结果
            result_win = tk.Toplevel(self.master)
            result_win.title("直线方程")
            
            tk.Label(result_win, text=f"点 {p1['label']} 和点 {p2['label']} 确定的直线方程:",
                     font=self.font_style).pack(padx=10, pady=5)
            tk.Label(result_win, text=equation, font=('Microsoft YaHei', 12, 'bold')).pack(padx=10, pady=5)
            
            tk.Button(result_win, text="添加为函数",
                      command=lambda: self.add_equation_as_function(result_win, expr, func_type, value,
                                                                    f"line_{p1['label']}{p2['label']}"),
                      font=self.font_style).pack(pady=10)
            
            self.log(f"计算直线方程: {p1['label']} 和 {p2['label']} -> {equation}")
        
        except Exception as e:
            messagebox.showerror("错误", f"计算失败: {e}")
    
    def add_equation_as_function(self, win, expr, func_type, value, label_prefix):
        """将方程添加为函数"""
        label = f"{label_prefix}"
        
        if func_type == 'x_constant':
            self.functions.append({
                'type': 'x_constant',
                'label': label,
                'value': value
            })
            self.func_listbox.insert(tk.END, f"{label}: x = {value}")
        else:
            self.functions.append({
                'type': 'y_expression',
                'label': label,
                'expr': expr
            })
            self.func_listbox.insert(tk.END, f"{label}: y = {expr}")
        
        messagebox.showinfo("成功", f"已添加函数 {label}.")
        win.destroy()
        self.plot_all()
        self.log(f"已添加函数: {label}")
    
    def calculate_distance(self):
        """计算两点距离"""
        if len(self.points) < 2:
            messagebox.showerror("错误", "至少需要两个点才能计算距离")
            return
        
        point_strings = self.select_items_dialog("选择点",
                                                 [f"{p['label']}({p['x']}, {p['y']})" for p in self.points],
                                                 2)
        if not point_strings:
            return
        
        try:
            points = self.parse_selected_points(point_strings)
            p1, p2 = points[0], points[1]
            x1, y1 = p1['x'], p1['y']
            x2, y2 = p2['x'], p2['y']
            
            distance = sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            simplified_distance = sp.simplify(distance)
            
            messagebox.showinfo("计算结果",
                                f"{p1['label']} 和 {p2['label']} 之间的距离 = {simplified_distance}")
            self.log(f"计算距离: {p1['label']} 和 {p2['label']} -> {simplified_distance}")
        
        except Exception as e:
            messagebox.showerror("错误", f"计算失败: {e}")
    
    def find_intersection_menu(self):
        """交点菜单选择"""
        menu_win = tk.Toplevel(self.master)
        menu_win.title("选择交点类型")
        menu_win.geometry("300x300")
        menu_win.transient(self.master)
        menu_win.grab_set()
        
        tk.Label(menu_win, text="请选择交点类型:", font=self.font_style).pack(pady=10)
        
        btn_frame = tk.Frame(menu_win)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="函数与函数", command=lambda: self.find_function_intersection(menu_win),
                  font=self.font_style, width=15).pack(pady=5)
        
        tk.Button(btn_frame, text="图形与函数", command=lambda: self.find_shape_function_intersection(menu_win),
                  font=self.font_style, width=15).pack(pady=5)
        
        tk.Button(btn_frame, text="取消", command=menu_win.destroy,
                  font=self.font_style, width=15).pack(pady=5)
    
    def find_function_intersection(self, menu_win):
        """求函数交点"""
        menu_win.destroy()
        
        if len(self.functions) < 2:
            messagebox.showerror("错误", "至少需要两个函数才能求交点")
            return
        
        func_strings = [
            f"{f['label']}: {'x = ' if f['type'] == 'x_constant' else 'y = '}{f.get('value', f.get('expr', ''))}"
            for f in self.functions]
        selected_funcs = self.select_items_dialog("选择函数", func_strings, 2)
        if not selected_funcs:
            return
        
        # 显示等待对话框
        wait_win = tk.Toplevel(self.master)
        wait_win.title("正在计算")
        wait_win.geometry("300x100")
        tk.Label(wait_win, text="正在计算交点，请稍候...", font=self.font_style).pack(expand=True)
        wait_win.transient(self.master)
        wait_win.grab_set()
        self.master.update()
        
        try:
            f1_label = selected_funcs[0].split(':')[0].strip()
            f2_label = selected_funcs[1].split(':')[0].strip()
            
            f1 = next(f for f in self.functions if f['label'] == f1_label)
            f2 = next(f for f in self.functions if f['label'] == f2_label)
            
            # 根据函数类型构建方程
            if f1['type'] == 'x_constant' and f2['type'] == 'x_constant':
                # 两个x=常数函数
                if f1['value'] == f2['value']:
                    solutions = [{self.x: f1['value'], self.y: self.y}]  # 无限交点
                else:
                    solutions = []  # 平行，无交点
            
            elif f1['type'] == 'x_constant' and f2['type'] == 'y_expression':
                # x=常数和y=表达式
                x_val = f1['value']
                y_val = f2['expr'].subs(self.x, x_val)
                solutions = [{self.x: x_val, self.y: y_val}]
            
            elif f1['type'] == 'y_expression' and f2['type'] == 'x_constant':
                # y=表达式和x=常数
                x_val = f2['value']
                y_val = f1['expr'].subs(self.x, x_val)
                solutions = [{self.x: x_val, self.y: y_val}]
            
            else:
                # 两个y=表达式函数
                eq1 = Eq(self.y, f1['expr'])
                eq2 = Eq(self.y, f2['expr'])
                
                # 在线程中求解
                solutions = self.find_intersection_threaded(eq1, eq2, f1_label, f2_label)
            
            wait_win.destroy()
            
            if not solutions:
                messagebox.showinfo("交点结果", "所选函数没有交点")
                self.log(f"求交点: {f1_label} 和 {f2_label} -> 无交点")
                return
            
            result_win = tk.Toplevel(self.master)
            result_win.title("交点结果")
            
            tk.Label(result_win, text=f"函数 {f1_label} 和 {f2_label} 的交点:",
                     font=self.font_style).pack(padx=10, pady=5)
            
            for idx, sol in enumerate(solutions):
                frame = tk.Frame(result_win)
                frame.pack(padx=10, pady=5, anchor=tk.W)
                
                x_val = sp.simplify(sol.get(self.x, '未确定'))
                y_val = sp.simplify(sol.get(self.y, '未确定'))
                
                tk.Label(frame, text=f"解 {idx + 1}: x = {x_val}, y = {y_val}",
                         font=self.font_style).pack(side=tk.LEFT)
                
                tk.Button(frame, text="添加为点",
                          command=lambda x=x_val, y=y_val: self.add_solution_point(result_win, x, y),
                          font=self.font_style).pack(side=tk.LEFT, padx=10)
            
            self.log(f"求交点: {f1_label} 和 {f2_label} -> 找到 {len(solutions)} 个交点")
        
        except Exception as e:
            wait_win.destroy()
            messagebox.showerror("错误", f"求解失败: {e}")
    
    def find_shape_function_intersection(self, menu_win):
        """求图形与函数的交点"""
        menu_win.destroy()
        
        if len(self.shapes) < 1 or len(self.functions) < 1:
            messagebox.showerror("错误", "至少需要有一个图形和一个函数才能求交点")
            return
        
        # 选择图形
        shape_strings = [f"{s['label']} ({s['type']})" for s in self.shapes]
        selected_shape = self.select_items_dialog("选择图形", shape_strings, 1, False)
        if not selected_shape:
            return
        
        # 选择函数
        func_strings = [
            f"{f['label']}: {'x = ' if f['type'] == 'x_constant' else 'y = '}{f.get('value', f.get('expr', ''))}"
            for f in self.functions]
        selected_func = self.select_items_dialog("选择函数", func_strings, 1, False)
        if not selected_func:
            return
        
        try:
            shape_label = selected_shape[0].split(' ')[0]
            func_label = selected_func[0].split(':')[0].strip()
            
            shape = next(s for s in self.shapes if s['label'] == shape_label)
            func = next(f for f in self.functions if f['label'] == func_label)
            
            # 显示等待对话框
            wait_win = tk.Toplevel(self.master)
            wait_win.title("正在计算")
            wait_win.geometry("300x100")
            tk.Label(wait_win, text="正在计算交点，请稍候...", font=self.font_style).pack(expand=True)
            wait_win.transient(self.master)
            wait_win.grab_set()
            self.master.update()
            
            # 根据图形类型和函数类型计算交点
            solutions = []
            
            if shape['type'] == 'circle':
                # 圆与函数的交点
                center = shape['center']
                radius = shape['radius']
                
                cx = center['x']
                cy = center['y']
                r = radius
                
                if func['type'] == 'x_constant':
                    # 圆与x=常数的交点
                    x_val = func['value']
                    # 代入圆的方程 (x - cx)^2 + (y - cy)^2 = r^2
                    equation = Eq((x_val - cx) ** 2 + (self.y - cy) ** 2, r ** 2)
                    y_solutions = solve(equation, self.y)
                    
                    for y_sol in y_solutions:
                        solutions.append({self.x: x_val, self.y: y_sol})
                
                elif func['type'] == 'y_expression':
                    # 圆与y=表达式的交点
                    # 代入圆的方程 (x - cx)^2 + (func['expr'] - cy)^2 = r^2
                    equation = Eq((self.x - cx) ** 2 + (func['expr'] - cy) ** 2, r ** 2)
                    x_solutions = solve(equation, self.x)
                    
                    for x_sol in x_solutions:
                        y_sol = func['expr'].subs(self.x, x_sol)
                        solutions.append({self.x: x_sol, self.y: y_sol})
            
            elif shape['type'] == 'polygon':
                # 多边形与函数的交点
                # 这里简化处理，只计算多边形各边与函数的交点
                points = shape['points']
                n = len(points)
                
                for i in range(n):
                    p1 = points[i]
                    p2 = points[(i + 1) % n]
                    
                    # 构建线段方程
                    x1, y1 = p1['x'], p1['y']
                    x2, y2 = p2['x'], p2['y']
                    
                    if x1 == x2:
                        # 垂直线段
                        segment_eq = Eq(self.x, x1)
                        if func['type'] == 'x_constant':
                            if func['value'] == x1:
                                # 整条线段都是交点
                                y_min = min(y1, y2)
                                y_max = max(y1, y2)
                                solutions.append({self.x: x1, self.y: (y_min, y_max)})
                        elif func['type'] == 'y_expression':
                            y_val = func['expr'].subs(self.x, x1)
                            if (y_val >= min(y1, y2) and y_val <= max(y1, y2)):
                                solutions.append({self.x: x1, self.y: y_val})
                    else:
                        # 非垂直线段
                        m = (y2 - y1) / (x2 - x1)
                        b = y1 - m * x1
                        segment_eq = Eq(self.y, m * self.x + b)
                        
                        if func['type'] == 'x_constant':
                            x_val = func['value']
                            if (x_val >= min(x1, x2) and x_val <= max(x1, x2)):
                                y_val = m * x_val + b
                                solutions.append({self.x: x_val, self.y: y_val})
                        
                        elif func['type'] == 'y_expression':
                            # 解方程组
                            eq1 = Eq(self.y, func['expr'])
                            eq2 = Eq(self.y, m * self.x + b)
                            
                            try:
                                sol = solve((eq1, eq2), (self.x, self.y))
                                if sol:
                                    x_sol = sol[0][0]
                                    y_sol = sol[0][1]
                                    if (x_sol >= min(x1, x2) and x_sol <= max(x1, x2)):
                                        solutions.append({self.x: x_sol, self.y: y_sol})
                            except:
                                pass
            
            wait_win.destroy()
            
            if not solutions:
                messagebox.showinfo("交点结果", "所选图形和函数没有交点")
                self.log(f"求交点: {shape_label} 和 {func_label} -> 无交点")
                return
            
            result_win = tk.Toplevel(self.master)
            result_win.title("交点结果")
            
            tk.Label(result_win, text=f"图形 {shape_label} 和函数 {func_label} 的交点:",
                     font=self.font_style).pack(padx=10, pady=5)
            
            text_area = scrolledtext.ScrolledText(result_win, width=60, height=10, font=self.font_style)
            text_area.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
            
            output = []
            for idx, sol in enumerate(solutions):
                x_val = sp.simplify(sol.get(self.x, '未确定'))
                y_val = sp.simplify(sol.get(self.y, '未确定'))
                
                if isinstance(y_val, tuple):
                    output.append(f"解 {idx + 1}: 线段 x = {x_val}, y ∈ [{y_val[0]}, {y_val[1]}]")
                else:
                    output.append(f"解 {idx + 1}: x = {x_val}, y = {y_val}")
                    
                    btn_frame = tk.Frame(result_win)
                    btn_frame.pack(pady=2)
                    
                    tk.Button(btn_frame, text=f"添加解 {idx + 1} 为点",
                              command=lambda x=x_val, y=y_val: self.add_solution_point(result_win, x, y),
                              font=self.font_style).pack(side=tk.LEFT, padx=5)
            
            text_area.insert(tk.END, "\n".join(output))
            text_area.config(state=tk.DISABLED)
            
            self.log(f"求交点: {shape_label} 和 {func_label} -> 找到 {len(solutions)} 个交点")
        
        except Exception as e:
            messagebox.showerror("错误", f"求解失败: {e}")
    
    def find_intersection_threaded(self, eq1, eq2, f1_label, f2_label):
        """在线程中求解函数交点"""
        try:
            solutions = []
            
            # 尝试符号解
            try:
                symbolic_solutions = solve((eq1, eq2), (self.x, self.y), dict=True, check=False)
                if symbolic_solutions:
                    solutions.extend(symbolic_solutions)
                    self.log(f"找到 {len(symbolic_solutions)} 个符号解")
            except:
                self.log("符号求解失败，尝试数值解")
            
            # 如果符号解不够，尝试数值解
            if not solutions:
                # 使用nsolve进行数值求解
                try:
                    # 选择一个初始点
                    x0 = 0
                    numerical_solution = nsolve((eq1, eq2), (self.x, self.y), (x0, 0))
                    solutions.append({self.x: numerical_solution[0], self.y: numerical_solution[1]})
                    self.log("找到数值解")
                except:
                    self.log("数值求解失败")
            
            return solutions
        except Exception as e:
            self.log(f"求解失败: {e}")
            return []
    
    def add_solution_point(self, win, x, y):
        """将解添加为点"""
        label = chr(65 + len(self.points))
        self.points.append({'label': label, 'x': x, 'y': y})
        self.point_listbox.insert(tk.END, f"{label}({x}, {y})")
        messagebox.showinfo("成功", f"已添加点 {label}.")
        self.plot_all()
        self.log(f"已添加点: {label}({x}, {y})")
    
    def triangle_area(self):
        """计算三角形面积"""
        if len(self.points) < 3:
            messagebox.showerror("错误", "至少需要三个点才能计算三角形面积")
            return
        
        point_strings = self.select_items_dialog("选择点",
                                                 [f"{p['label']}({p['x']}, {p['y']})" for p in self.points],
                                                 3)
        if not point_strings:
            return
        
        try:
            points = self.parse_selected_points(point_strings)
            p1, p2, p3 = points[0], points[1], points[2]
            
            x1, y1 = p1['x'], p1['y']
            x2, y2 = p2['x'], p2['y']
            x3, y3 = p3['x'], p3['y']
            
            # 使用绝对值确保面积为正
            area = sp.Abs((x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2)) / 2)
            simplified_area = sp.simplify(area)
            
            messagebox.showinfo("计算结果",
                                f"三角形 {p1['label']}{p2['label']}{p3['label']} 的面积 = {simplified_area}")
            self.log(f"计算三角形面积: {p1['label']}{p2['label']}{p3['label']} -> {simplified_area}")
        
        except Exception as e:
            messagebox.showerror("错误", f"计算失败: {e}")
    
    def solve_unknown_menu(self):
        """解未知点菜单"""
        menu_win = tk.Toplevel(self.master)
        menu_win.title("解未知点")
        menu_win.geometry("400x400")
        menu_win.transient(self.master)
        menu_win.grab_set()
        
        tk.Label(menu_win, text="请选择约束类型:", font=self.font_style).pack(pady=10)
        
        constraint_types = [
            "在函数上",
            "距离约束",
            "斜率约束",
            "中点约束",
            "点对称约束",
            "三点共线",
            "平行约束",
            "垂直约束"
        ]
        
        btn_frame = tk.Frame(menu_win)
        btn_frame.pack(pady=10, fill=tk.BOTH, expand=True)
        
        for i, constraint in enumerate(constraint_types):
            btn = tk.Button(btn_frame, text=constraint,
                            command=lambda c=constraint: self.add_constraint(menu_win, c),
                            font=self.font_style, height=2)
            btn.grid(row=i // 2, column=i % 2, padx=5, pady=5, sticky="nsew")
        
        for i in range(2):
            btn_frame.columnconfigure(i, weight=1)
        for i in range((len(constraint_types) + 1) // 2):
            btn_frame.rowconfigure(i, weight=1)
        
        self.constraints = []
        self.constraint_listbox = tk.Listbox(menu_win, height=5, font=self.font_style)
        self.constraint_listbox.pack(pady=10, padx=10, fill=tk.X)
        
        btn_frame2 = tk.Frame(menu_win)
        btn_frame2.pack(pady=10)
        
        tk.Button(btn_frame2, text="求解", command=lambda: self.solve_with_constraints(menu_win),
                  font=self.font_style).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame2, text="清空约束", command=self.clear_constraints,
                  font=self.font_style).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame2, text="取消", command=menu_win.destroy,
                  font=self.font_style).pack(side=tk.LEFT, padx=5)
    
    def add_constraint(self, menu_win, constraint_type):
        """添加约束"""
        try:
            if constraint_type == "在函数上":
                func_str = simpledialog.askstring("函数约束", "输入函数表达式 (如: y=2*x+1 或 x=3):")
                if not func_str:
                    return
                
                if '=' not in func_str:
                    raise ValueError("函数格式错误")
                
                left_side, expr_str = func_str.split('=', 1)
                left_side = left_side.strip().lower()
                expr_str = expr_str.strip()
                
                if left_side == 'y':
                    expr = self.parse_expression(expr_str)
                    self.constraints.append(Eq(self.y, expr))
                    self.constraint_listbox.insert(tk.END, f"在函数上: y = {expr}")
                
                elif left_side == 'x':
                    value = self.parse_expression(expr_str)
                    self.constraints.append(Eq(self.x, value))
                    self.constraint_listbox.insert(tk.END, f"在函数上: x = {value}")
                
                else:
                    raise ValueError("函数应以'y='或'x='开头")
            
            elif constraint_type == "距离约束":
                data = simpledialog.askstring("距离约束", "格式: 已知点x,y; 距离值\n例如: 2,3;5")
                if not data:
                    return
                
                point_str, distance_str = data.split(';')
                x0, y0 = map(self.parse_expression, point_str.split(','))
                d = self.parse_expression(distance_str)
                self.constraints.append(Eq((self.x - x0) ** 2 + (self.y - y0) ** 2, d ** 2))
                self.constraint_listbox.insert(tk.END, f"距离约束: 到点({x0},{y0})的距离为{d}")
            
            elif constraint_type == "斜率约束":
                data = simpledialog.askstring("斜率约束", "格式: 已知点x,y; 斜率值\n例如: 2,3;0.5")
                if not data:
                    return
                
                point_str, slope_str = data.split(';')
                x0, y0 = map(self.parse_expression, point_str.split(','))
                m = self.parse_expression(slope_str)
                self.constraints.append(Eq((self.y - y0) / (self.x - x0), m))
                self.constraint_listbox.insert(tk.END, f"斜率约束: 到点({x0},{y0})的斜率为{m}")
            
            elif constraint_type == "中点约束":
                data = simpledialog.askstring("中点约束", "格式: 点AxA,yA; 点BxB,yB\n例如: 1,2;3,4")
                if not data:
                    return
                
                pointA_str, pointB_str = data.split(';')
                xA, yA = map(self.parse_expression, pointA_str.split(','))
                xB, yB = map(self.parse_expression, pointB_str.split(','))
                self.constraints.append(Eq(self.x, (xA + xB) / 2))
                self.constraints.append(Eq(self.y, (yA + yB) / 2))
                self.constraint_listbox.insert(tk.END, f"中点约束: 是点({xA},{yA})和点({xB},{yB})的中点")
            
            elif constraint_type == "点对称约束":
                data = simpledialog.askstring("点对称约束", "格式: 对称中心x,y\n例如: 2,3")
                if not data:
                    return
                
                center_str = data
                x0, y0 = map(self.parse_expression, center_str.split(','))
                # 这里需要另一个点，但简化处理，假设已知另一个点
                self.constraints.append(Eq(self.x, 2 * x0 - self.x))  # 简化表示
                self.constraints.append(Eq(self.y, 2 * y0 - self.y))  # 简化表示
                self.constraint_listbox.insert(tk.END, f"点对称约束: 关于点({x0},{y0})对称")
            
            elif constraint_type == "三点共线":
                data = simpledialog.askstring("三点共线", "格式: 点AxA,yA; 点BxB,yB\n例如: 1,2;3,4")
                if not data:
                    return
                
                pointA_str, pointB_str = data.split(';')
                xA, yA = map(self.parse_expression, pointA_str.split(','))
                xB, yB = map(self.parse_expression, pointB_str.split(','))
                # 三点共线意味着斜率相等
                self.constraints.append(Eq((self.y - yA) / (self.x - xA), (yB - yA) / (xB - xA)))
                self.constraint_listbox.insert(tk.END, f"三点共线: 与点({xA},{yA})和点({xB},{yB})共线")
            
            elif constraint_type == "平行约束":
                data = simpledialog.askstring("平行约束", "格式: 直线斜率\n例如: 0.5")
                if not data:
                    return
                
                slope_str = data
                m = self.parse_expression(slope_str)
                # 这里需要另一个点来确定直线，但简化处理
                self.constraints.append(Eq(self.y, m * self.x + self.y - m * self.x))  # 简化表示
                self.constraint_listbox.insert(tk.END, f"平行约束: 斜率为{m}")
            
            elif constraint_type == "垂直约束":
                data = simpledialog.askstring("垂直约束", "格式: 直线斜率\n例如: 0.5")
                if not data:
                    return
                
                slope_str = data
                m = self.parse_expression(slope_str)
                # 垂直意味着斜率乘积为-1
                self.constraints.append(Eq((self.y - 0) / (self.x - 0), -1 / m))  # 简化表示，假设过原点
                self.constraint_listbox.insert(tk.END, f"垂直约束: 与斜率为{m}的直线垂直")
            
            self.log(f"添加约束: {constraint_type}")
        
        except Exception as e:
            messagebox.showerror("输入错误", f"格式错误: {e}")
    
    def clear_constraints(self):
        """清空约束列表"""
        self.constraints = []
        self.constraint_listbox.delete(0, tk.END)
        self.log("已清空约束")
    
    def solve_with_constraints(self, menu_win):
        """使用约束求解未知点"""
        if not self.constraints:
            messagebox.showerror("错误", "请至少添加一个约束")
            return
        
        try:
            solutions = solve(self.constraints, (self.x, self.y), dict=True)
            
            if not solutions:
                messagebox.showinfo("解方程结果", "无解")
                self.log("解未知点: 无解")
                return
            
            result_win = tk.Toplevel(self.master)
            result_win.title("解方程结果")
            
            text_area = scrolledtext.ScrolledText(result_win, width=60, height=15, font=self.font_style)
            text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
            
            output = []
            for idx, sol in enumerate(solutions):
                x_val = sp.simplify(sol.get(self.x, '未确定'))
                y_val = sp.simplify(sol.get(self.y, '未确定'))
                output.append(f"解 {idx + 1}:")
                output.append(f"  x = {x_val}")
                output.append(f"  y = {y_val}")
                output.append("-" * 40)
                
                # 添加按钮以便将解添加为点
                btn_frame = tk.Frame(result_win)
                btn_frame.pack(pady=5)
                
                tk.Button(btn_frame, text=f"添加解 {idx + 1} 为点",
                          command=lambda x=x_val, y=y_val: self.add_solution_point(result_win, x, y),
                          font=self.font_style).pack(side=tk.LEFT, padx=5)
            
            text_area.insert(tk.END, "\n".join(output))
            text_area.config(state=tk.DISABLED)
            
            menu_win.destroy()
            self.log(f"解未知点: 找到 {len(solutions)} 个解")
        
        except Exception as e:
            messagebox.showerror("解方程错误", f"求解失败: {e}")
    
    def create_shape_menu(self):
        """创建图形菜单"""
        menu_win = tk.Toplevel(self.master)
        menu_win.title("创建图形")
        menu_win.geometry("300x300")
        menu_win.transient(self.master)
        menu_win.grab_set()
        
        tk.Label(menu_win, text="请选择图形类型:", font=self.font_style).pack(pady=10)
        
        shape_types = [
            "圆",
            "三角形",
            "四边形",
            "多边形"
        ]
        
        btn_frame = tk.Frame(menu_win)
        btn_frame.pack(pady=10)
        
        for shape_type in shape_types:
            btn = tk.Button(btn_frame, text=shape_type,
                            command=lambda s=shape_type: self.create_shape_type(menu_win, s),
                            font=self.font_style, width=15)
            btn.pack(pady=5)
        
        tk.Button(btn_frame, text="取消", command=menu_win.destroy,
                  font=self.font_style, width=15).pack(pady=5)
    
    def create_shape_type(self, menu_win, shape_type):
        """创建特定类型的图形"""
        menu_win.destroy()
        
        try:
            if shape_type == '圆':
                self.create_circle()
            elif shape_type == '三角形':
                self.create_polygon(3)
            elif shape_type == '四边形':
                self.create_polygon(4)
            elif shape_type == '多边形':
                sides = simpledialog.askinteger("多边形边数", "请输入多边形的边数:", parent=self.master, minvalue=3)
                if sides:
                    self.create_polygon(sides)
        
        except Exception as e:
            messagebox.showerror("错误", f"创建图形失败: {e}")
    
    def create_circle(self):
        """创建圆"""
        if len(self.points) < 1:
            messagebox.showerror("错误", "至少需要一个点作为圆心")
            return
        
        point_strings = self.select_items_dialog("选择圆心点",
                                                 [f"{p['label']}({p['x']}, {p['y']})" for p in self.points],
                                                 1)
        if not point_strings:
            return
        
        radius_str = simpledialog.askstring("输入半径", "请输入圆的半径:", parent=self.master)
        if not radius_str:
            return
        
        try:
            center_point = self.parse_selected_points(point_strings)[0]
            radius = self.parse_expression(radius_str)
            
            label = f"⊙{center_point['label']}"
            self.shapes.append({
                'type': 'circle',
                'label': label,
                'center': center_point,
                'radius': radius
            })
            
            self.shape_listbox.insert(tk.END, f"{label}(r={radius})")
            self.log(f"已创建圆 {label}，半径 {radius}")
            self.plot_all()
        
        except Exception as e:
            messagebox.showerror("错误", f"创建圆失败: {e}")
    
    def create_polygon(self, sides):
        """创建多边形"""
        if len(self.points) < sides:
            messagebox.showerror("错误", f"至少需要 {sides} 个点来创建多边形")
            return
        
        point_strings = self.select_items_dialog(f"选择 {sides} 个顶点",
                                                 [f"{p['label']}({p['x']}, {p['y']})" for p in self.points],
                                                 sides)
        if not point_strings or len(point_strings) != sides:
            return
        
        try:
            points = self.parse_selected_points(point_strings)
            shape_types = {
                3: '三角形',
                4: '四边形',
                5: '五边形',
                6: '六边形'
            }
            
            shape_type = shape_types.get(sides, f"{sides}边形")
            label = f"{shape_type}_{''.join([p['label'] for p in points])}"
            
            self.shapes.append({
                'type': 'polygon',
                'label': label,
                'points': points,
                'sides': sides
            })
            
            self.shape_listbox.insert(tk.END, f"{label}")
            self.log(f"已创建{shape_type} {label}")
            self.plot_all()
        
        except Exception as e:
            messagebox.showerror("错误", f"创建{shape_type}失败: {e}")
    
    def test_properties(self):
        """测试图形性质"""
        if len(self.shapes) < 1:
            messagebox.showerror("错误", "至少需要有一个图形才能测试性质")
            return
        
        # 选择要测试的图形
        items = [f"{s['label']} ({s['type']})" for s in self.shapes]
        selected_item = self.select_items_dialog("选择要测试的图形", items, 1, False)
        if not selected_item:
            return
        
        try:
            item = selected_item[0]
            shape_label = item.split(' ')[0]
            shape = next(s for s in self.shapes if s['label'] == shape_label)
            
            result = ""
            
            if shape['type'] == 'polygon':
                if shape['sides'] == 3:
                    # 测试三角形性质
                    result = self.test_triangle_properties(shape)
                elif shape['sides'] == 4:
                    # 测试四边形性质
                    result = self.test_quadrilateral_properties(shape)
            
            if result:
                messagebox.showinfo("性质测试结果", result)
                self.log(f"测试图形性质: {shape_label} -> {result}")
            else:
                messagebox.showinfo("性质测试", "该图形类型的性质测试尚未实现")
        
        except Exception as e:
            messagebox.showerror("错误", f"测试性质失败: {e}")
    
    def test_triangle_properties(self, triangle):
        """测试三角形性质"""
        points = triangle['points']
        p1, p2, p3 = points
        
        # 创建SymPy三角形对象
        try:
            sym_triangle = SymTriangle(
                Point(float(p1['x'].evalf()), float(p1['y'].evalf())),
                Point(float(p2['x'].evalf()), float(p2['y'].evalf())),
                Point(float(p3['x'].evalf()), float(p3['y'].evalf()))
            )
            
            result = f"三角形 {triangle['label']} 的性质:\n"
            
            # 检查是否等边
            if sym_triangle.is_equilateral():
                result += "• 是等边三角形\n"
            
            # 检查是否等腰
            if sym_triangle.is_isosceles():
                result += "• 是等腰三角形\n"
            
            # 检查是否直角三角形
            if sym_triangle.is_right():
                result += "• 是直角三角形\n"
            
            # 计算面积
            area = sym_triangle.area
            result += f"• 面积: {area}\n"
            
            return result
        
        except Exception as e:
            return f"测试三角形性质时出错: {e}"
    
    def test_quadrilateral_properties(self, quadrilateral):
        """测试四边形性质"""
        points = quadrilateral['points']
        if len(points) != 4:
            return "不是四边形"
        
        p1, p2, p3, p4 = points
        
        # 创建点对象
        try:
            points_list = [
                Point(float(p1['x'].evalf()), float(p1['y'].evalf())),
                Point(float(p2['x'].evalf()), float(p2['y'].evalf())),
                Point(float(p3['x'].evalf()), float(p3['y'].evalf())),
                Point(float(p4['x'].evalf()), float(p4['y'].evalf()))
            ]
            
            result = f"四边形 {quadrilateral['label']} 的性质:\n"
            
            # 检查是否平行四边形
            def is_parallelogram(p1, p2, p3, p4):
                # 检查对边是否平行
                v1 = p2 - p1
                v2 = p4 - p3
                v3 = p3 - p2
                v4 = p1 - p4
                
                return v1.is_parallel(v2) and v3.is_parallel(v4)
            
            if is_parallelogram(points_list[0], points_list[1], points_list[2], points_list[3]):
                result += "• 是平行四边形\n"
                
                # 检查是否矩形
                def is_rectangle(p1, p2, p3, p4):
                    v1 = p2 - p1
                    v2 = p3 - p2
                    return v1.dot(v2) == 0  # 检查相邻边是否垂直
                
                if is_rectangle(points_list[0], points_list[1], points_list[2], points_list[3]):
                    result += "• 是矩形\n"
                    
                    # 检查是否正方形
                    def is_square(p1, p2, p3, p4):
                        # 检查所有边是否相等
                        d1 = p1.distance(p2)
                        d2 = p2.distance(p3)
                        return d1 == d2
                    
                    if is_square(points_list[0], points_list[1], points_list[2], points_list[3]):
                        result += "• 是正方形\n"
                
                # 检查是否菱形
                def is_rhombus(p1, p2, p3, p4):
                    # 检查所有边是否相等
                    d1 = p1.distance(p2)
                    d2 = p2.distance(p3)
                    return d1 == d2
                
                if is_rhombus(points_list[0], points_list[1], points_list[2], points_list[3]):
                    result += "• 是菱形\n"
            
            return result
        
        except Exception as e:
            return f"测试四边形性质时出错: {e}"


if __name__ == "__main__":
    root = tk.Tk()
    app = GeometryApp(root)
    root.mainloop()