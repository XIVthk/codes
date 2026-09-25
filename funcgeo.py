import tkinter as tk
import re
import time
import threading
from tkinter import simpledialog, messagebox, scrolledtext, ttk
import sympy as sp
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from sympy import symbols, Eq, solve, sqrt, sin, cos, tan, cot, log, exp, I, pi, nsolve, Polygon, Point, Segment, Line, Circle
from sympy.geometry import Triangle as SymTriangle


class ConstraintDialog(tk.Toplevel):
    def __init__(self, parent, title, points, functions):
        super().__init__(parent)
        self.title(title)
        self.geometry("600x400")
        self.transient(parent)
        self.grab_set()
        
        self.points = points
        self.functions = functions
        self.result = None
        self.x, self.y = symbols('x y')
        
        self.font_style = ('Microsoft YaHei', 10)
        self.title_font = ('Microsoft YaHei', 11, 'bold')
        
        self.main_frame = tk.Frame(self, padx=15, pady=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        self.create_description_area()
        
        self.content_frame = tk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True, pady=10)
    
    def create_description_area(self):
        desc_frame = tk.Frame(self.main_frame)
        desc_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(
            desc_frame,
            text="约束说明",
            font=self.title_font,
            fg="#2c3e50"
        ).pack(anchor=tk.W)
        
        ttk.Separator(desc_frame, orient='horizontal').pack(fill=tk.X, pady=5)
        
        self.desc_text = tk.Text(
            desc_frame,
            height=4,
            wrap=tk.WORD,
            font=self.font_style,
            bg=self.cget('bg'),
            relief=tk.FLAT,
            state=tk.DISABLED
        )
        self.desc_text.pack(fill=tk.X)
        
        self.set_description()
    
    def set_description(self):
        raise Exception("子类必须重写该方法！")
    
    def create_point_selector(self, frame, label_text):
        tk.Label(frame, text=label_text, font=self.font_style).pack(pady=5, anchor=tk.W)
        
        point_var = tk.StringVar()
        point_combo = ttk.Combobox(frame, textvariable=point_var, font=self.font_style)
        point_values = [f"{p['label']}({p['x']}, {p['y']})" for p in self.points]
        point_values.append("直接输入坐标 (例如: 3,0 或 (5, sin(π/2)) 或 O(0,0))")
        point_combo['values'] = point_values
        point_combo['state'] = 'normal'
        point_combo.pack(pady=5, fill=tk.X, padx=2)
        
        return point_var
    
    def create_function_selector(self, frame, label_text):
        tk.Label(frame, text=label_text, font=self.font_style).pack(pady=5, anchor=tk.W)
        
        func_var = tk.StringVar()
        func_combo = ttk.Combobox(frame, textvariable=func_var, font=self.font_style)
        func_values = [
            f"{f['label']}: {'x = ' if f['type'] == 'x_constant' else 'y = '}{f.get('value', f.get('expr', ''))}"
            for f in self.functions
        ]
        func_values.append("直接输入函数 (例如: y = 3x 或 y = 2sin(x) 或 x = 5)")
        func_combo['values'] = func_values
        func_combo['state'] = 'normal'
        func_combo.pack(pady=5, fill=tk.X, padx=2)
        
        return func_var
    
    def create_value_entry(self, frame, label_text):
        tk.Label(frame, text=label_text, font=self.font_style).pack(pady=5, anchor=tk.W)
        
        value_var = tk.StringVar()
        value_entry = tk.Entry(frame, textvariable=value_var, font=self.font_style)
        value_entry.pack(pady=5, fill=tk.X, padx=2)
        
        return value_var
    
    def create_buttons(self, frame):
        btn_frame = tk.Frame(frame)
        btn_frame.pack(pady=15)
        
        tk.Button(
            btn_frame,
            text="确认",
            command=self.on_confirm,
            font=self.font_style,
            width=10,
            bg="#3498db",
            fg="white",
            relief=tk.RAISED
        ).pack(side=tk.LEFT, padx=10)
        
        tk.Button(
            btn_frame,
            text="取消",
            command=self.destroy,
            font=self.font_style,
            width=10,
            bg="#e74c3c",
            fg="white",
            relief=tk.RAISED
        ).pack(side=tk.LEFT, padx=10)
    
    def on_confirm(self):
        raise Exception("子类必须重写该方法！")
    
    def parse_point(self, point_str):
        if not point_str or point_str.strip() == "":
            return None
        
        cleaned = point_str.strip().replace(' ', '')
        
        label_pattern = r'^([A-Za-z]+)\(([^)]+)\)$'
        label_match = re.match(label_pattern, cleaned)
        if label_match:
            label = label_match.group(1)
            coords = label_match.group(2)
            try:
                x_str, y_str = coords.split(',', 1)
                x_str = self._add_multiplication_signs(x_str)
                y_str = self._add_multiplication_signs(y_str)
                x = sp.sympify(x_str)
                y = sp.sympify(y_str)
                for p in self.points:
                    if p['label'] == label:
                        return p
                return {'label': label, 'x': x, 'y': y}
            except:
                pass
        
        coord_patterns = [
            r'^\(([^,]+),([^)]+)\)$',
            r'^([^,]+),([^,]+)$'
        ]
        for pattern in coord_patterns:
            coord_match = re.match(pattern, cleaned)
            if coord_match:
                try:
                    x_str = coord_match.group(1)
                    y_str = coord_match.group(2)
                    x_str = self._add_multiplication_signs(x_str)
                    y_str = self._add_multiplication_signs(y_str)
                    x = sp.sympify(x_str)
                    y = sp.sympify(y_str)
                    for p in self.points:
                        if sp.simplify(p['x'] - x) == 0 and sp.simplify(p['y'] - y) == 0:
                            return p
                    return {'label': f'({x}, {y})', 'x': x, 'y': y}
                except:
                    pass
        
        return None
    
    def parse_function(self, func_str):
        if not func_str or func_str.strip() == "":
            return None
        
        cleaned = func_str.strip().replace(' ', '')
        
        label_pattern = r'^([^:]+):(.+)$'
        label_match = re.match(label_pattern, cleaned)
        if label_match:
            label = label_match.group(1).strip()
            expr_part = label_match.group(2).strip()
            for f in self.functions:
                if f['label'] == label:
                    return f
            return self._parse_function_expression(expr_part, label)
        
        return self._parse_function_expression(cleaned, f'function')
    
    def _add_multiplication_signs(self, expr_str):
        if not expr_str:
            return expr_str
        
        patterns = [
            (r'(\d)([a-zA-Z(])', r'\1*\2'),
            (r'([a-zA-Z])(\()', r'\1*\2'),
            (r'(\))([a-zA-Z0-9(])', r'\1*\2'),
            (r'([a-zA-Z])([a-zA-Z])', r'\1*\2')
        ]
        
        result = expr_str
        for pattern, replacement in patterns:
            result = re.sub(pattern, replacement, result)
        
        return result
    
    def _parse_function_expression(self, expr_str, label):
        if '=' not in expr_str:
            return None
        
        try:
            left, right = expr_str.split('=', 1)
            left = left.strip().lower()
            right = right.strip()
            
            right = self._add_multiplication_signs(right)
            
            if left == 'x':
                value = sp.sympify(right)
                for f in self.functions:
                    if f['type'] == 'x_constant' and sp.simplify(f['value'] - value) == 0:
                        return f
                return {'type': 'x_constant', 'label': label, 'value': value}
            
            elif left == 'y':
                expr = sp.sympify(right)
                for f in self.functions:
                    if f['type'] == 'y_expression' and sp.simplify(f['expr'] - expr) == 0:
                        return f
                return {'type': 'y_expression', 'label': label, 'expr': expr}
        
        except Exception as e:
            print(f"函数解析错误: {e}")
            pass
        
        return None


class PointSymmetryDialog(ConstraintDialog):
    
    def __init__(self, parent, points, functions):
        super().__init__(parent, "点对称约束", points, functions)
        self.create_widgets()
    
    def create_widgets(self):
        main_frame = tk.Frame(self.main_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.center_var = self.create_point_selector(main_frame, "对称中心:")
        self.known_var = self.create_point_selector(main_frame, "已知点:")
        
        self.create_buttons(main_frame)
    
    def set_description(self):
        description = (
            "功能：求解一个未知点P，使其关于指定的对称中心O与已知点A成中心对称。\n\n"
            "中心对称定义：如果点O是线段PA的中点，则点P与点A关于点O成中心对称。\n\n"
            "计算公式：设对称中心为O(x₀, y₀)，已知点为A(x₁, y₁)，\n"
            "则对称点P(x, y)的坐标满足：\n"
            "x = 2x₀ - x₁\n"
            "y = 2y₀ - y₁\n\n"
            "示例：若对称中心为O(0,0)，已知点为A(3,4)，则对称点P为(-3,-4)。\n"
            "输入说明：请选择或输入对称中心和已知点的坐标，可以是具体数值或包含符号的表达式。"
        )
        self.desc_text.config(state=tk.NORMAL)
        self.desc_text.delete(1.0, tk.END)
        self.desc_text.insert(tk.END, description)
        self.desc_text.config(state=tk.DISABLED)
    
    def on_confirm(self):
        center_point = self.parse_point(self.center_var.get())
        known_point = self.parse_point(self.known_var.get())
        
        if not center_point or not known_point:
            messagebox.showerror("错误", "请选择有效的点")
            return
        
        cx, cy = center_point['x'], center_point['y']
        kx, ky = known_point['x'], known_point['y']
        
        self.result = {
            'type': 'point_symmetry',
            'center': center_point,
            'known': known_point,
            'equations': [
                Eq(symbols('x'), 2 * cx - kx),
                Eq(symbols('y'), 2 * cy - ky)
            ],
            'description': f"关于{center_point['label']}与{known_point['label']}对称"
        }
        
        self.destroy()


class DistanceConstraintDialog(ConstraintDialog):
    
    def __init__(self, parent, points, functions):
        super().__init__(parent, "距离约束", points, functions)
        self.create_widgets()
    
    def create_widgets(self):
        main_frame = tk.Frame(self.main_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.point_var = self.create_point_selector(main_frame, "参考点:")
        self.distance_var = self.create_value_entry(main_frame, "距离值:")
        
        self.create_buttons(main_frame)
    
    def set_description(self):
        description = (
            "功能：限制未知点P到指定参考点A的距离为给定值d。满足该约束的点P的轨迹是以A为圆心、d为半径的圆。\n\n"
            "距离定义：平面上两点之间的直线距离，即欧几里得距离。\n\n"
            "计算公式：设参考点为A(x₀, y₀)，距离值为d，\n"
            "则未知点P(x, y)满足：\n"
            "(x - x₀)² + (y - y₀)² = d²\n\n"
            "示例：若参考点为A(0,0)，距离值为5，则点P的轨迹方程为x² + y² = 25。\n"
            "输入说明：请选择或输入参考点坐标，并输入距离值（可以是数值、变量或包含数学函数的表达式，如sqrt(2)或a+b）。"
        )
        self.desc_text.config(state=tk.NORMAL)
        self.desc_text.delete(1.0, tk.END)
        self.desc_text.insert(tk.END, description)
        self.desc_text.config(state=tk.DISABLED)
    
    def on_confirm(self):
        point = self.parse_point(self.point_var.get())
        distance_str = self.distance_var.get()
        
        if not point or not distance_str:
            messagebox.showerror("错误", "请选择有效的点和输入距离值")
            return
        
        try:
            x0, y0 = point['x'], point['y']
            d = sp.sympify(distance_str)
            
            self.result = {
                'type': 'distance',
                'point': point,
                'distance': d,
                'equations': [
                    Eq((symbols('x') - x0) ** 2 + (symbols('y') - y0) ** 2, d ** 2)
                ],
                'description': f"到点{point['label']}的距离为{d}"
            }
            
            self.destroy()
        except Exception as e:
            messagebox.showerror("错误", f"距离值格式错误: {e}")


class SlopeConstraintDialog(ConstraintDialog):
    
    def __init__(self, parent, points, functions):
        super().__init__(parent, "斜率约束", points, functions)
        self.create_widgets()
    
    def create_widgets(self):
        main_frame = tk.Frame(self.main_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.point_var = self.create_point_selector(main_frame, "参考点:")
        self.slope_var = self.create_value_entry(main_frame, "斜率值:")
        
        self.create_buttons(main_frame)
    
    def set_description(self):
        description = (
            "功能：限制未知点P与指定参考点A的连线斜率为给定值m。满足该约束的点P的轨迹是过点A且斜率为m的直线（点A除外）。\n\n"
            "斜率定义：直线上任意两点的纵坐标之差与横坐标之差的比值，即m = (y₂ - y₁)/(x₂ - x₁)。\n\n"
            "计算公式：设参考点为A(x₀, y₀)，斜率值为m，\n"
            "则未知点P(x, y)满足：\n"
            "(y - y₀) / (x - x₀) = m\n\n"
            "特殊情况：垂直直线的斜率为无穷大，无法直接表示，此时应使用x = x₀的形式。\n"
            "示例：若参考点为A(1,2)，斜率值为3，则点P的轨迹方程为(y-2)/(x-1) = 3，即y = 3x - 1（x ≠ 1）。\n"
            "输入说明：请选择或输入参考点坐标，并输入斜率值（可以是数值、分数或符号表达式，如1/2或tan(π/4)）。"
        )
        self.desc_text.config(state=tk.NORMAL)
        self.desc_text.delete(1.0, tk.END)
        self.desc_text.insert(tk.END, description)
        self.desc_text.config(state=tk.DISABLED)
    
    def on_confirm(self):
        point = self.parse_point(self.point_var.get())
        slope_str = self.slope_var.get()
        
        if not point or not slope_str:
            messagebox.showerror("错误", "请选择有效的点和输入斜率值")
            return
        
        try:
            x0, y0 = point['x'], point['y']
            m = sp.sympify(slope_str)
            
            self.result = {
                'type': 'slope',
                'point': point,
                'slope': m,
                'equations': [
                    Eq((symbols('y') - y0) / (symbols('x') - x0), m)
                ],
                'description': f"到点{point['label']}的斜率为{m}"
            }
            
            self.destroy()
        except Exception as e:
            messagebox.showerror("错误", f"斜率值格式错误: {e}")


class MidpointConstraintDialog(ConstraintDialog):
    
    def __init__(self, parent, points, functions):
        super().__init__(parent, "中点约束", points, functions)
        self.create_widgets()
    
    def create_widgets(self):
        main_frame = tk.Frame(self.main_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.point1_var = self.create_point_selector(main_frame, "第一个点:")
        self.point2_var = self.create_point_selector(main_frame, "第二个点:")
        
        self.create_buttons(main_frame)
    
    def set_description(self):
        description = (
            "功能：指定未知点P是两个已知点A和B的中点。即点P到点A和点P到点B的距离相等，且三点共线。\n\n"
            "中点定义：在线段AB上，到A、B两点距离相等的点。\n\n"
            "计算公式：设点A的坐标为(x₁, y₁)，点B的坐标为(x₂, y₂)，\n"
            "则中点P(x, y)的坐标满足：\n"
            "x = (x₁ + x₂) / 2\n"
            "y = (y₁ + y₂) / 2\n\n"
            "示例：若点A为(1,2)，点B为(3,6)，则其中点P为(2,4)。\n"
            "输入说明：请选择或输入两个已知点的坐标，系统将计算出这两点连线的中点坐标。"
        )
        self.desc_text.config(state=tk.NORMAL)
        self.desc_text.delete(1.0, tk.END)
        self.desc_text.insert(tk.END, description)
        self.desc_text.config(state=tk.DISABLED)
    
    def on_confirm(self):
        point1 = self.parse_point(self.point1_var.get())
        point2 = self.parse_point(self.point2_var.get())
        
        if not point1 or not point2:
            messagebox.showerror("错误", "请选择有效的点")
            return
        
        x1, y1 = point1['x'], point1['y']
        x2, y2 = point2['x'], point2['y']
        
        self.result = {
            'type': 'midpoint',
            'point1': point1,
            'point2': point2,
            'equations': [
                Eq(symbols('x'), (x1 + x2) / 2),
                Eq(symbols('y'), (y1 + y2) / 2)
            ],
            'description': f"是点{point1['label']}和点{point2['label']}的中点"
        }
        
        self.destroy()


class CollinearConstraintDialog(ConstraintDialog):
    
    def __init__(self, parent, points, functions):
        super().__init__(parent, "三点共线约束", points, functions)
        self.create_widgets()
    
    def create_widgets(self):
        main_frame = tk.Frame(self.main_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.point1_var = self.create_point_selector(main_frame, "第一个点:")
        self.point2_var = self.create_point_selector(main_frame, "第二个点:")
        
        self.create_buttons(main_frame)
    
    def set_description(self):
        description = (
            "功能：限制未知点P与两个已知点A和B位于同一条直线上，即三点共线。\n\n"
            "共线定义：三个或更多的点位于同一条直线上。对于三点A、B、P，当直线AB与直线AP的斜率相等时，三点共线。\n\n"
            "计算公式：设点A的坐标为(x₁, y₁)，点B的坐标为(x₂, y₂)，\n"
            "则未知点P(x, y)满足：\n"
            "(y - y₁) / (x - x₁) = (y₂ - y₁) / (x₂ - x₁)\n\n"
            "特殊情况：当直线垂直于x轴时（x₁ = x₂），公式简化为x = x₁。\n"
            "示例：若点A为(1,2)，点B为(3,6)，则满足条件的点P(x,y)需满足(y-2)/(x-1) = 2，即y = 2x。\n"
            "输入说明：请选择或输入两个已知点的坐标，系统将生成使三点共线的约束方程。"
        )
        self.desc_text.config(state=tk.NORMAL)
        self.desc_text.delete(1.0, tk.END)
        self.desc_text.insert(tk.END, description)
        self.desc_text.config(state=tk.DISABLED)
    
    def on_confirm(self):
        point1 = self.parse_point(self.point1_var.get())
        point2 = self.parse_point(self.point2_var.get())
        
        if not point1 or not point2:
            messagebox.showerror("错误", "请选择有效的点")
            return
        
        x1, y1 = point1['x'], point1['y']
        x2, y2 = point2['x'], point2['y']
        
        self.result = {
            'type': 'collinear',
            'point1': point1,
            'point2': point2,
            'equations': [
                Eq((symbols('y') - y1) / (symbols('x') - x1), (y2 - y1) / (x2 - x1))
            ],
            'description': f"与点{point1['label']}和点{point2['label']}共线"
        }
        
        self.destroy()


class FunctionConstraintDialog(ConstraintDialog):
    
    def __init__(self, parent, points, functions):
        super().__init__(parent, "在函数上约束", points, functions)
        self.create_widgets()
    
    def create_widgets(self):
        main_frame = tk.Frame(self.main_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.func_var = self.create_function_selector(main_frame, "选择函数:")
        
        self.create_buttons(main_frame)
    
    def set_description(self):
        description = (
            "功能：限制未知点P(x,y)位于指定的函数图像上，即点P的坐标满足该函数的方程。\n\n"
            "函数类型：支持两种形式的函数：\n"
            "1. 垂直直线：x = c（c为常数）\n"
            "2. 一般函数：y = f(x)（f(x)为关于x的表达式）\n\n"
            "输入格式：\n"
            "- 对于垂直直线，输入格式为 'x = c'（如x = 3或x = a+2）\n"
            "- 对于一般函数，输入格式为 'y = 表达式'（如y = 2x+3或y = sin(x)）\n"
            "支持省略乘法符号，如'y = 3x'等价于'y = 3*x'，'y = 2sin(x)'等价于'y = 2*sin(x)'\n\n"
            "示例：若函数为y = x² + 2x + 1，则点P(x,y)需满足y = x² + 2x + 1。\n"
            "输入说明：请从下拉列表选择已有函数或直接输入新的函数表达式。"
        )
        self.desc_text.config(state=tk.NORMAL)
        self.desc_text.delete(1.0, tk.END)
        self.desc_text.insert(tk.END, description)
        self.desc_text.config(state=tk.DISABLED)
    
    def on_confirm(self):
        func = self.parse_function(self.func_var.get())
        
        if not func:
            messagebox.showerror("错误", "请选择有效的函数")
            return
        
        if func['type'] == 'x_constant':
            self.result = {
                'type': 'on_function',
                'function': func,
                'equations': [Eq(symbols('x'), func['value'])],
                'description': f"在函数{func['label']}上: x = {func['value']}"
            }
        else:
            self.result = {
                'type': 'on_function',
                'function': func,
                'equations': [Eq(symbols('y'), func['expr'])],
                'description': f"在函数{func['label']}上: y = {func['expr']}"
            }
        
        self.destroy()


class ParallelConstraintDialog(ConstraintDialog):
    
    def __init__(self, parent, points, functions):
        super().__init__(parent, "平行约束", points, functions)
        self.create_widgets()
    
    def create_widgets(self):
        main_frame = tk.Frame(self.main_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.slope_var = self.create_value_entry(main_frame, "斜率值:")
        
        self.create_buttons(main_frame)
    
    def set_description(self):
        description = (
            "功能：限制未知点P所在的直线与斜率为m的直线平行。满足该约束的点P的轨迹是一组斜率为m的平行线。\n\n"
            "平行定义：平面上两条不相交的直线称为平行线，它们的斜率相等。\n\n"
            "计算公式：若已知直线的斜率为m，\n"
            "则未知点P(x, y)所在直线的方程满足：\n"
            "y = m·x + b\n"
            "其中b为直线在y轴上的截距（可以是任意常数）\n\n"
            "特殊情况：水平直线的斜率为0，方程形式为y = b；垂直直线的斜率为无穷大，方程形式为x = c。\n"
            "示例：与斜率为2的直线平行的直线方程为y = 2x + b，其中b可以是任意常数。\n"
            "输入说明：请输入已知直线的斜率值（可以是数值、分数或符号表达式，如1/2或tan(π/6)）。"
        )
        self.desc_text.config(state=tk.NORMAL)
        self.desc_text.delete(1.0, tk.END)
        self.desc_text.insert(tk.END, description)
        self.desc_text.config(state=tk.DISABLED)
    
    def on_confirm(self):
        slope_str = self.slope_var.get()
        
        if not slope_str:
            messagebox.showerror("错误", "请输入斜率值")
            return
        
        try:
            m = sp.sympify(slope_str)
            
            self.result = {
                'type': 'parallel',
                'slope': m,
                'equations': [
                    Eq(symbols('y'), m * symbols('x') + symbols('b'))
                ],
                'description': f"斜率为{m}"
            }
            
            self.destroy()
        except Exception as e:
            messagebox.showerror("错误", f"斜率值格式错误: {e}")


class PerpendicularConstraintDialog(ConstraintDialog):
    
    def __init__(self, parent, points, functions):
        super().__init__(parent, "垂直约束", points, functions)
        self.create_widgets()
    
    def create_widgets(self):
        main_frame = tk.Frame(self.main_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.slope_var = self.create_value_entry(main_frame, "斜率值:")
        
        self.create_buttons(main_frame)
    
    def set_description(self):
        description = (
            "功能：限制未知点P所在的直线与斜率为m的直线垂直（正交）。满足该约束的点P的轨迹是一组与已知直线垂直的直线。\n\n"
            "垂直定义：平面上两条相交成90度角的直线称为互相垂直，它们的斜率乘积为-1。\n\n"
            "计算公式：若已知直线的斜率为m，\n"
            "则与之垂直的直线的斜率为-1/m，其方程满足：\n"
            "y = (-1/m)·x + b\n"
            "其中b为直线在y轴上的截距（可以是任意常数）\n\n"
            "特殊情况：与水平直线（斜率为0）垂直的是垂直直线，方程形式为x = c；\n"
            "与垂直直线（斜率无穷大）垂直的是水平直线，方程形式为y = b。\n"
            "示例：与斜率为2的直线垂直的直线方程为y = (-1/2)x + b，其中b可以是任意常数。\n"
            "输入说明：请输入已知直线的斜率值（可以是数值、分数或符号表达式，但不能为0，如1/2或tan(π/4)）。"
        )
        self.desc_text.config(state=tk.NORMAL)
        self.desc_text.delete(1.0, tk.END)
        self.desc_text.insert(tk.END, description)
        self.desc_text.config(state=tk.DISABLED)
    
    def on_confirm(self):
        slope_str = self.slope_var.get()
        
        if not slope_str:
            messagebox.showerror("错误", "请输入斜率值")
            return
        
        try:
            m = sp.sympify(slope_str)
            
            self.result = {
                'type': 'perpendicular',
                'slope': m,
                'equations': [
                    Eq(symbols('y'), -1 / m * symbols('x') + symbols('b'))
                ],
                'description': f"与斜率为{m}的直线垂直"
            }
            
            self.destroy()
        except Exception as e:
            messagebox.showerror("错误", f"斜率值格式错误: {e}")


class GeometryApp:
    def __init__(self, master):
        self.master = master
        master.title("几何分析")
        master.geometry("1300x1000")
        
        master.attributes('-fullscreen', True)
        master.bind('<Escape>', lambda e: master.attributes('-fullscreen', False))
        master.bind('<F11>', lambda e: master.attributes('-fullscreen', True))
        
        self.font_style = ('Microsoft YaHei', 10)
        self.points = []
        self.functions = []
        self.shapes = []
        self.x, self.y = symbols('x y')
        
        main_frame = tk.Frame(master, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
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
        
        func_frame = tk.LabelFrame(left_frame, text="函数列表", font=self.font_style)
        func_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.func_listbox = tk.Listbox(func_frame, width=30, height=8, font=self.font_style, selectmode=tk.MULTIPLE)
        self.func_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        shape_frame = tk.LabelFrame(left_frame, text="图形列表", font=self.font_style)
        shape_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.shape_listbox = tk.Listbox(shape_frame, width=30, height=8, font=self.font_style, selectmode=tk.MULTIPLE)
        self.shape_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        btn_frame = tk.LabelFrame(left_frame, text="操作", font=self.font_style)
        btn_frame.pack(fill=tk.X, pady=5)
        
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
        
        right_frame = tk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
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
        
        log_frame = tk.LabelFrame(right_frame, text="操作日志", font=self.font_style)
        log_frame.pack(fill=tk.BOTH, expand=False, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, width=80, height=8, font=self.font_style)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_text.config(state=tk.DISABLED)
        
        self.plot_all()
        self.log("几何分析工具已启动")
    
    def log(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def plot_all(self):
        self.ax.clear()
        
        self.ax.axhline(0, color='black', lw=0.5)
        self.ax.axvline(0, color='black', lw=0.5)
        
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
        
        for func in self.functions:
            try:
                if func['type'] == 'x_constant':
                    x_val = float(complex(func['value'].evalf()).real)
                    self.ax.axvline(x=x_val, label=func['label'])
                    continue
                
                expr = func['expr']
                is_constant = not expr.has(self.x)
                
                if is_constant:
                    const_value = float(complex(expr.evalf()).real)
                    self.ax.axhline(y=const_value, label=func['label'], linestyle='-', color='orange')
                    continue
                
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
                
                f = sp.lambdify(self.x, expr, modules=['numpy'])
                y_values = f(x_range)
                y_values = np.real(y_values)
                valid = np.isfinite(y_values)
                
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
        
        for shape in self.shapes:
            try:
                if shape['type'] == 'circle':
                    center = shape['center']
                    radius = shape['radius']
                    
                    cx = complex(center['x'].evalf()).real
                    cy = complex(center['y'].evalf()).real
                    r = complex(radius.evalf()).real
                    
                    circle = plt.Circle((cx, cy), r, fill=False, color='blue')
                    self.ax.add_patch(circle)
                    
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
                    
                    x_vals.append(x_vals[0])
                    y_vals.append(y_vals[0])
                    
                    self.ax.plot(x_vals, y_vals, color='green', label=shape['label'])
                    
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
        label_match = re.match(r'^([A-Za-z]+)\(([^)]+)\)$', input_str)
        if label_match:
            label = label_match.group(1)
            coords_str = label_match.group(2)
            entry_label = self.point_label_var.get().strip()
            if entry_label:
                label = entry_label
            x_str, y_str = self.parse_coordinates(coords_str)
            return label, x_str, y_str
        
        entry_label = self.point_label_var.get().strip()
        if not entry_label:
            coords = input_str.strip()
            if coords == "(0,0)" or coords == "0,0" or coords == "（0,0）" or coords == "0，0":
                for p in self.points:
                    if p['label'] == 'O':
                        entry_label = chr(65 + len(self.points))
                        break
                else:
                    entry_label = 'O'
            else:
                entry_label = chr(65 + len(self.points))
        
        x_str, y_str = self.parse_coordinates(input_str)
        return entry_label, x_str, y_str
    
    def parse_coordinates(self, coord_str):
        coord_str = coord_str.replace(" ", "").replace("，", ",")
        
        if (coord_str.startswith("(") and coord_str.endswith(")")) or \
                (coord_str.startswith("（") and coord_str.endswith("）")):
            coord_str = coord_str[1:-1]
        
        parts = coord_str.split(",")
        if len(parts) != 2:
            raise ValueError("请输入两个坐标值，用逗号分隔")
        
        return parts[0], parts[1]
    
    def parse_expression(self, expr_str):
        try:
            expr_str = expr_str.replace('^', '**')
            expr_str = expr_str.replace('π', 'pi')
            expr_str = expr_str.replace('π', 'pi')
            expr_str = expr_str.replace('ｅ', 'E')
            
            patterns = [
                r'(\d)([a-zA-Z])',
                r'(\d)(\()',
                r'(\))([a-zA-Z])',
                r'(\))(\()'
            ]
            
            for pattern in patterns:
                expr_str = re.sub(pattern, r'\1*\2', expr_str)
            
            return sp.sympify(expr_str, evaluate=False)
        except Exception as e:
            raise ValueError(f"表达式解析失败: {e}\n输入的表达式: {expr_str}")
    
    def parse_selected_points(self, point_strings):
        selected_points = []
        for ps in point_strings:
            label_match = re.match(r'^([A-Za-z]+)', ps)
            if label_match:
                label = label_match.group(1)
                for p in self.points:
                    if p['label'] == label:
                        selected_points.append(p)
                        break
        return selected_points
    
    def add_point(self):
        input_str = simpledialog.askstring("输入点坐标",
                                           "请输入点坐标（格式: x,y 或 (x,y) 或 A(x,y)）:\n支持表达式如: 2+3, sin(π/2)",
                                           parent=self.master)
        if not input_str:
            return
        
        try:
            label, x_str, y_str = self.parse_point_input(input_str)
            x = self.parse_expression(x_str)
            y = self.parse_expression(y_str)
            
            for p in self.points:
                if sp.simplify(p['x'] - x) == 0 and sp.simplify(p['y'] - y) == 0:
                    if not messagebox.askyesno("确认",
                                               f"点 {p['label']}({p['x']}, {p['y']}) 已存在相同坐标，是否保留新点？"):
                        return
                    break
            
            for p in self.points:
                if p['label'] == label:
                    if not messagebox.askyesno("确认", f"点 {label} 已存在，是否替换？"):
                        return
                    self.points = [p for p in self.points if p['label'] != label]
                    self.point_listbox.delete(0, tk.END)
                    for p in self.points:
                        self.point_listbox.insert(tk.END, f"{p['label']}({p['x']}, {p['y']})")
                    break
            
            self.points.append({'label': label, 'x': x, 'y': y})
            self.point_listbox.insert(tk.END, f"{label}({x}, {y})")
            self.log(f"已添加点 {label}({x}, {y})")
            self.point_label_var.set("")
            self.plot_all()
        except Exception as e:
            messagebox.showerror("错误", f"无效输入: {e}")
    
    def add_function(self):
        func_str = simpledialog.askstring("输入函数",
                                          "请输入函数（格式: y=表达式 或 x=常数）:\n例如: y=2*x+1, y=sin(x), x=3",
                                          parent=self.master)
        if not func_str:
            return
        
        try:
            if '=' not in func_str:
                raise ValueError("函数格式错误，应包含等号")
            
            parts = func_str.split('=', 1)
            left_side = parts[0].strip().lower()
            expr_str = parts[1].strip()
            
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
        selected_points = self.point_listbox.curselection()
        for idx in reversed(selected_points):
            point_str = self.point_listbox.get(idx)
            label = re.match(r'^[A-Za-z]+', point_str).group()
            self.points = [p for p in self.points if p['label'] != label]
            self.point_listbox.delete(idx)
            self.log(f"已删除点 {label}")
        
        selected_funcs = self.func_listbox.curselection()
        for idx in reversed(selected_funcs):
            func_str = self.func_listbox.get(idx)
            label = func_str.split(':')[0].strip()
            self.functions = [f for f in self.functions if f['label'] != label]
            self.func_listbox.delete(idx)
            self.log(f"已删除函数 {label}")
        
        selected_shapes = self.shape_listbox.curselection()
        for idx in reversed(selected_shapes):
            shape_str = self.shape_listbox.get(idx)
            label = shape_str.split('(')[0].strip()
            self.shapes = [s for s in self.shapes if s['label'] != label]
            self.shape_listbox.delete(idx)
            self.log(f"已删除图形 {label}")
        
        self.plot_all()
    
    def select_items_dialog(self, title, items, required_num, multi_select=True):
        select_win = tk.Toplevel(self.master)
        select_win.title(title)
        select_win.geometry("500x400")
        select_win.transient(self.master)
        select_win.grab_set()
        
        tk.Label(select_win, text=f"请选择 {required_num} 个项:",
                 font=self.font_style).pack(padx=10, pady=5)
        
        listbox = tk.Listbox(select_win, selectmode=tk.MULTIPLE if multi_select else tk.SINGLE,
                             font=self.font_style, width=50, height=15)
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
            
            result_win = tk.Toplevel(self.master)
            result_win.title("直线方程")
            result_win.geometry("500x200")
            result_win.transient(self.master)
            
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
        menu_win = tk.Toplevel(self.master)
        menu_win.title("选择交点类型")
        menu_win.geometry("400x400")
        menu_win.transient(self.master)
        menu_win.grab_set()
        
        tk.Label(menu_win, text="请选择交点类型:", font=self.font_style).pack(pady=10)
        
        btn_frame = tk.Frame(menu_win)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="函数与函数", command=lambda: self.find_function_intersection(menu_win),
                  font=self.font_style, width=15, height=2).pack(pady=5)
        
        tk.Button(btn_frame, text="图形与函数", command=lambda: self.find_shape_function_intersection(menu_win),
                  font=self.font_style, width=15, height=2).pack(pady=5)
        
        tk.Button(btn_frame, text="图形与图形", command=lambda: self.find_shape_shape_intersection(menu_win),
                  font=self.font_style, width=15, height=2).pack(pady=5)
        
        tk.Button(btn_frame, text="取消", command=menu_win.destroy,
                  font=self.font_style, width=15, height=2).pack(pady=5)
    
    def find_function_intersection(self, menu_win):
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
        
        wait_win = tk.Toplevel(self.master)
        wait_win.title("正在计算")
        wait_win.geometry("300x100")
        wait_win.transient(self.master)
        tk.Label(wait_win, text="正在计算交点，请稍候...", font=self.font_style).pack(expand=True)
        wait_win.grab_set()
        self.master.update()
        
        try:
            f1_label = selected_funcs[0].split(':')[0].strip()
            f2_label = selected_funcs[1].split(':')[0].strip()
            
            f1 = next(f for f in self.functions if f['label'] == f1_label)
            f2 = next(f for f in self.functions if f['label'] == f2_label)
            
            if f1['type'] == 'x_constant' and f2['type'] == 'x_constant':
                if f1['value'] == f2['value']:
                    solutions = [{self.x: f1['value'], self.y: self.y}]
                else:
                    solutions = []
            
            elif f1['type'] == 'x_constant' and f2['type'] == 'y_expression':
                x_val = f1['value']
                y_val = f2['expr'].subs(self.x, x_val)
                solutions = [{self.x: x_val, self.y: y_val}]
            
            elif f1['type'] == 'y_expression' and f2['type'] == 'x_constant':
                x_val = f2['value']
                y_val = f1['expr'].subs(self.x, x_val)
                solutions = [{self.x: x_val, self.y: y_val}]
            
            else:
                eq1 = Eq(self.y, f1['expr'])
                eq2 = Eq(self.y, f2['expr'])
                
                solutions = self.find_intersection_threaded(eq1, eq2, f1_label, f2_label)
            
            wait_win.destroy()
            
            if not solutions:
                messagebox.showinfo("交点结果", "所选函数没有交点")
                self.log(f"求交点: {f1_label} 和 {f2_label} -> 无交点")
                return
            
            result_win = tk.Toplevel(self.master)
            result_win.title("交点结果")
            result_win.geometry("600x400")
            result_win.transient(self.master)
            
            tk.Label(result_win, text=f"函数 {f1_label} 和 {f2_label} 的交点:",
                     font=self.font_style).pack(padx=10, pady=5)
            
            text_area = scrolledtext.ScrolledText(result_win, width=60, height=15, font=self.font_style)
            text_area.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
            
            output = []
            for idx, sol in enumerate(solutions):
                x_val = sp.simplify(sol.get(self.x, '未确定'))
                y_val = sp.simplify(sol.get(self.y, '未确定'))
                
                output.append(f"解 {idx + 1}: x = {x_val}, y = {y_val}")
                
                btn_frame = tk.Frame(result_win)
                btn_frame.pack(pady=2)
                
                tk.Button(btn_frame, text=f"添加解 {idx + 1} 为点",
                          command=lambda x=x_val, y=y_val: self.add_solution_point(result_win, x, y),
                          font=self.font_style).pack(side=tk.LEFT, padx=5)
            
            text_area.insert(tk.END, "\n".join(output))
            text_area.config(state=tk.DISABLED)
            
            self.log(f"求交点: {f1_label} 和 {f2_label} -> 找到 {len(solutions)} 个交点")
        
        except Exception as e:
            wait_win.destroy()
            messagebox.showerror("错误", f"求解失败: {e}")
    
    def find_shape_function_intersection(self, menu_win):
        menu_win.destroy()
        
        if len(self.shapes) < 1 or len(self.functions) < 1:
            messagebox.showerror("错误", "至少需要有一个图形和一个函数才能求交点")
            return
        
        shape_strings = [f"{s['label']} ({s['type']})" for s in self.shapes]
        selected_shape = self.select_items_dialog("选择图形", shape_strings, 1, False)
        if not selected_shape:
            return
        
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
            
            wait_win = tk.Toplevel(self.master)
            wait_win.title("正在计算")
            wait_win.geometry("300x100")
            wait_win.transient(self.master)
            tk.Label(wait_win, text="正在计算交点，请稍候...", font=self.font_style).pack(expand=True)
            wait_win.grab_set()
            self.master.update()
            
            solutions = []
            
            if shape['type'] == 'circle':
                center = shape['center']
                radius = shape['radius']
                
                cx = center['x']
                cy = center['y']
                r = radius
                
                if func['type'] == 'x_constant':
                    x_val = func['value']
                    equation = Eq((x_val - cx) ** 2 + (self.y - cy) ** 2, r ** 2)
                    y_solutions = solve(equation, self.y)
                    
                    for y_sol in y_solutions:
                        solutions.append({self.x: x_val, self.y: y_sol})
                
                elif func['type'] == 'y_expression':
                    equation = Eq((self.x - cx) ** 2 + (func['expr'] - cy) ** 2, r ** 2)
                    x_solutions = solve(equation, self.x)
                    
                    for x_sol in x_solutions:
                        y_sol = func['expr'].subs(self.x, x_sol)
                        solutions.append({self.x: x_sol, self.y: y_sol})
            
            elif shape['type'] == 'polygon':
                points = shape['points']
                n = len(points)
                
                for i in range(n):
                    p1 = points[i]
                    p2 = points[(i + 1) % n]
                    
                    x1, y1 = p1['x'], p1['y']
                    x2, y2 = p2['x'], p2['y']
                    
                    if x1 == x2:
                        segment_eq = Eq(self.x, x1)
                        if func['type'] == 'x_constant':
                            if func['value'] == x1:
                                y_min = min(y1, y2)
                                y_max = max(y1, y2)
                                solutions.append({self.x: x1, self.y: (y_min, y_max)})
                        elif func['type'] == 'y_expression':
                            y_val = func['expr'].subs(self.x, x1)
                            if (y_val >= min(y1, y2) and y_val <= max(y1, y2)):
                                solutions.append({self.x: x1, self.y: y_val})
                    else:
                        m = (y2 - y1) / (x2 - x1)
                        b = y1 - m * x1
                        segment_eq = Eq(self.y, m * self.x + b)
                        
                        if func['type'] == 'x_constant':
                            x_val = func['value']
                            if (x_val >= min(x1, x2) and x_val <= max(x1, x2)):
                                y_val = m * x_val + b
                                solutions.append({self.x: x_val, self.y: y_val})
                        
                        elif func['type'] == 'y_expression':
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
            result_win.geometry("600x400")
            result_win.transient(self.master)
            
            tk.Label(result_win, text=f"图形 {shape_label} 和函数 {func_label} 的交点:",
                     font=self.font_style).pack(padx=10, pady=5)
            
            text_area = scrolledtext.ScrolledText(result_win, width=60, height=15, font=self.font_style)
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
    
    def find_shape_shape_intersection(self, menu_win):
        menu_win.destroy()
        
        if len(self.shapes) < 2:
            messagebox.showerror("错误", "至少需要有两个图形才能求交点")
            return
        
        shape_strings = [f"{s['label']} ({s['type']})" for s in self.shapes]
        selected_shape1 = self.select_items_dialog("选择第一个图形", shape_strings, 1, False)
        if not selected_shape1:
            return
        
        selected_shape2 = self.select_items_dialog("选择第二个图形", shape_strings, 1, False)
        if not selected_shape2:
            return
        
        try:
            shape1_label = selected_shape1[0].split(' ')[0]
            shape2_label = selected_shape2[0].split(' ')[0]
            
            shape1 = next(s for s in self.shapes if s['label'] == shape1_label)
            shape2 = next(s for s in self.shapes if s['label'] == shape2_label)
            
            wait_win = tk.Toplevel(self.master)
            wait_win.title("正在计算")
            wait_win.geometry("300x100")
            wait_win.transient(self.master)
            tk.Label(wait_win, text="正在计算交点，请稍候...", font=self.font_style).pack(expand=True)
            wait_win.grab_set()
            self.master.update()
            
            solutions = []
            
            if shape1['type'] == 'circle' and shape2['type'] == 'circle':
                center1 = shape1['center']
                center2 = shape2['center']
                r1 = shape1['radius']
                r2 = shape2['radius']
                
                cx1, cy1 = center1['x'], center1['y']
                cx2, cy2 = center2['x'], center2['y']
                
                d = sqrt((cx2 - cx1) ** 2 + (cy2 - cy1) ** 2)
                
                if d > r1 + r2 or d < abs(r1 - r2):
                    solutions = []
                else:
                    a = (r1 ** 2 - r2 ** 2 + d ** 2) / (2 * d)
                    h = sqrt(r1 ** 2 - a ** 2)
                    
                    x0 = cx1 + a * (cx2 - cx1) / d
                    y0 = cy1 + a * (cy2 - cy1) / d
                    
                    x3 = x0 + h * (cy2 - cy1) / d
                    y3 = y0 - h * (cx2 - cx1) / d
                    
                    x4 = x0 - h * (cy2 - cy1) / d
                    y4 = y0 + h * (cx2 - cx1) / d
                    
                    solutions = [
                        {self.x: x3, self.y: y3},
                        {self.x: x4, self.y: y4}
                    ]
            
            elif (shape1['type'] == 'circle' and shape2['type'] == 'polygon') or \
                    (shape1['type'] == 'polygon' and shape2['type'] == 'circle'):
                
                if shape1['type'] == 'circle':
                    circle = shape1
                    polygon = shape2
                else:
                    circle = shape2
                    polygon = shape1
                
                center = circle['center']
                radius = circle['radius']
                points = polygon['points']
                
                cx, cy = center['x'], center['y']
                r = radius
                
                n = len(points)
                for i in range(n):
                    p1 = points[i]
                    p2 = points[(i + 1) % n]
                    
                    x1, y1 = p1['x'], p1['y']
                    x2, y2 = p2['x'], p2['y']
                    
                    dx = x2 - x1
                    dy = y2 - y1
                    
                    dr2 = dx ** 2 + dy ** 2
                    
                    dcx = cx - x1
                    dcy = cy - y1
                    
                    t = (dcx * dx + dcy * dy) / dr2
                    
                    if 0 <= t <= 1:
                        nx = x1 + t * dx
                        ny = y1 + t * dy
                        
                        d = sqrt((nx - cx) ** 2 + (ny - cy) ** 2)
                        
                        if d <= r:
                            dt = sqrt(r ** 2 - d ** 2) / sqrt(dr2)
                            
                            t1 = t - dt
                            t2 = t + dt
                            
                            if 0 <= t1 <= 1:
                                x_int = x1 + t1 * dx
                                y_int = y1 + t1 * dy
                                solutions.append({self.x: x_int, self.y: y_int})
                            
                            if 0 <= t2 <= 1:
                                x_int = x1 + t2 * dx
                                y_int = y1 + t2 * dy
                                solutions.append({self.x: x_int, self.y: y_int})
            
            elif shape1['type'] == 'polygon' and shape2['type'] == 'polygon':
                points1 = shape1['points']
                points2 = shape2['points']
                
                n1 = len(points1)
                n2 = len(points2)
                
                for i in range(n1):
                    p1 = points1[i]
                    p2 = points1[(i + 1) % n1]
                    
                    x1, y1 = p1['x'], p1['y']
                    x2, y2 = p2['x'], p2['y']
                    
                    for j in range(n2):
                        p3 = points2[j]
                        p4 = points2[(j + 1) % n2]
                        
                        x3, y3 = p3['x'], p3['y']
                        x4, y4 = p4['x'], p4['y']
                        
                        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
                        
                        if denom != 0:
                            t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
                            u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom
                            
                            if 0 <= t <= 1 and 0 <= u <= 1:
                                x_int = x1 + t * (x2 - x1)
                                y_int = y1 + t * (y2 - y1)
                                solutions.append({self.x: x_int, self.y: y_int})
            
            wait_win.destroy()
            
            if not solutions:
                messagebox.showinfo("交点结果", "所选图形没有交点")
                self.log(f"求交点: {shape1_label} 和 {shape2_label} -> 无交点")
                return
            
            result_win = tk.Toplevel(self.master)
            result_win.title("交点结果")
            result_win.geometry("600x400")
            result_win.transient(self.master)
            
            tk.Label(result_win, text=f"图形 {shape1_label} 和图形 {shape2_label} 的交点:",
                     font=self.font_style).pack(padx=10, pady=5)
            
            text_area = scrolledtext.ScrolledText(result_win, width=60, height=15, font=self.font_style)
            text_area.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
            
            output = []
            for idx, sol in enumerate(solutions):
                x_val = sp.simplify(sol.get(self.x, '未确定'))
                y_val = sp.simplify(sol.get(self.y, '未确定'))
                
                output.append(f"解 {idx + 1}: x = {x_val}, y = {y_val}")
                
                btn_frame = tk.Frame(result_win)
                btn_frame.pack(pady=2)
                
                tk.Button(btn_frame, text=f"添加解 {idx + 1} 为点",
                          command=lambda x=x_val, y=y_val: self.add_solution_point(result_win, x, y),
                          font=self.font_style).pack(side=tk.LEFT, padx=5)
            
            text_area.insert(tk.END, "\n".join(output))
            text_area.config(state=tk.DISABLED)
            
            self.log(f"求交点: {shape1_label} 和 {shape2_label} -> 找到 {len(solutions)} 个交点")
        
        except Exception as e:
            messagebox.showerror("错误", f"求解失败: {e}")
    
    def find_intersection_threaded(self, eq1, eq2, f1_label, f2_label):
        try:
            solutions = []
            
            try:
                symbolic_solutions = solve((eq1, eq2), (self.x, self.y), dict=True, check=False)
                if symbolic_solutions:
                    solutions.extend(symbolic_solutions)
                    self.log(f"找到 {len(symbolic_solutions)} 个符号解")
            except:
                self.log("符号求解失败，尝试数值解")
            
            if not solutions:
                try:
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
        label = chr(65 + len(self.points))
        self.points.append({'label': label, 'x': x, 'y': y})
        self.point_listbox.insert(tk.END, f"{label}({x}, {y})")
        messagebox.showinfo("成功", f"已添加点 {label}.")
        self.plot_all()
        self.log(f"已添加点: {label}({x}, {y})")
    
    def triangle_area(self):
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
            
            area = sp.Abs((x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2)) / 2)
            simplified_area = sp.simplify(area)
            
            messagebox.showinfo("计算结果",
                                f"三角形 {p1['label']}{p2['label']}{p3['label']} 的面积 = {simplified_area}")
            self.log(f"计算三角形面积: {p1['label']}{p2['label']}{p3['label']} -> {simplified_area}")
        
        except Exception as e:
            messagebox.showerror("错误", f"计算失败: {e}")
    
    def solve_unknown_menu(self):
        menu_win = tk.Toplevel(self.master)
        menu_win.title("解未知点")
        menu_win.geometry("400x600")
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
        try:
            if constraint_type == "在函数上":
                dialog = FunctionConstraintDialog(self.master, self.points, self.functions)
                self.master.wait_window(dialog)
                
                if dialog.result:
                    self.constraints.extend(dialog.result['equations'])
                    self.constraint_listbox.insert(tk.END, dialog.result['description'])
            
            elif constraint_type == "距离约束":
                dialog = DistanceConstraintDialog(self.master, self.points, self.functions)
                self.master.wait_window(dialog)
                
                if dialog.result:
                    self.constraints.extend(dialog.result['equations'])
                    self.constraint_listbox.insert(tk.END, dialog.result['description'])
            
            elif constraint_type == "斜率约束":
                dialog = SlopeConstraintDialog(self.master, self.points, self.functions)
                self.master.wait_window(dialog)
                
                if dialog.result:
                    self.constraints.extend(dialog.result['equations'])
                    self.constraint_listbox.insert(tk.END, dialog.result['description'])
            
            elif constraint_type == "中点约束":
                dialog = MidpointConstraintDialog(self.master, self.points, self.functions)
                self.master.wait_window(dialog)
                
                if dialog.result:
                    self.constraints.extend(dialog.result['equations'])
                    self.constraint_listbox.insert(tk.END, dialog.result['description'])
            
            elif constraint_type == "点对称约束":
                dialog = PointSymmetryDialog(self.master, self.points, self.functions)
                self.master.wait_window(dialog)
                
                if dialog.result:
                    self.constraints.extend(dialog.result['equations'])
                    self.constraint_listbox.insert(tk.END, dialog.result['description'])
            
            elif constraint_type == "三点共线":
                dialog = CollinearConstraintDialog(self.master, self.points, self.functions)
                self.master.wait_window(dialog)
                
                if dialog.result:
                    self.constraints.extend(dialog.result['equations'])
                    self.constraint_listbox.insert(tk.END, dialog.result['description'])
            
            elif constraint_type == "平行约束":
                dialog = ParallelConstraintDialog(self.master, self.points, self.functions)
                self.master.wait_window(dialog)
                
                if dialog.result:
                    self.constraints.extend(dialog.result['equations'])
                    self.constraint_listbox.insert(tk.END, dialog.result['description'])
            
            elif constraint_type == "垂直约束":
                dialog = PerpendicularConstraintDialog(self.master, self.points, self.functions)
                self.master.wait_window(dialog)
                
                if dialog.result:
                    self.constraints.extend(dialog.result['equations'])
                    self.constraint_listbox.insert(tk.END, dialog.result['description'])
            
            self.log(f"添加约束: {constraint_type}")
        
        except Exception as e:
            messagebox.showerror("输入错误", f"格式错误: {e}")
    
    def clear_constraints(self):
        self.constraints = []
        self.constraint_listbox.delete(0, tk.END)
        self.log("已清空约束")
    
    def solve_with_constraints(self, menu_win):
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
            result_win.geometry("600x400")
            result_win.transient(self.master)
            
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
    
    def parse_vertex_input(self, input_str):
        input_str = input_str.replace(" ", "")
        
        if "," in input_str:
            labels = input_str.split(",")
        else:
            labels = list(input_str)
        
        labels = [label for label in labels if label]
        
        return labels
    
    def create_polygon(self, sides):
        if len(self.points) < sides:
            messagebox.showerror("错误", f"至少需要 {sides} 个点来创建多边形")
            return
        
        if sides == 3:
            point_strings = self.select_items_dialog(f"选择 {sides} 个顶点",
                                                     [f"{p['label']}({p['x']}, {p['y']})" for p in self.points],
                                                     sides)
            if not point_strings or len(point_strings) != sides:
                return
            
            points = self.parse_selected_points(point_strings)
        else:
            input_str = simpledialog.askstring("输入顶点顺序",
                                               f"请输入{sides}个顶点的标签（用逗号分隔或连续输入，如: A,B,C,D 或 ABCD）:",
                                               parent=self.master)
            if not input_str:
                return
            
            try:
                labels = self.parse_vertex_input(input_str)
                if len(labels) != sides:
                    messagebox.showerror("错误", f"请输入恰好 {sides} 个顶点标签")
                    return
                
                points = []
                for label in labels:
                    found = False
                    for p in self.points:
                        if p['label'].upper() == label.upper():
                            points.append(p)
                            found = True
                            break
                    
                    if not found:
                        messagebox.showerror("错误", f"找不到标签为 '{label}' 的点")
                        return
            except Exception as e:
                messagebox.showerror("错误", f"解析顶点输入失败: {e}")
                return
        
        try:
            shape_types = {
                3: 'Triangle',
                4: 'Quadrilateral',
                5: 'Pentagon',
                6: 'Hexagon'
            }
            
            shape_type = shape_types.get(sides, f"Polygon{sides}")
            
            label_parts = [p['label'] for p in points]
            label = f"{shape_type}_{'_'.join(label_parts)}"
            
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
        if len(self.shapes) < 1:
            messagebox.showerror("错误", "至少需要有一个图形才能测试性质")
            return
        
        items = [f"{s['label']} ({s['type']})" for s in self.shapes]
        selected_item = self.select_items_dialog("选择要测试的图形", items, 1, False)
        if not selected_item:
            return
        
        try:
            item = selected_item[0]
            shape_label = item.split(' ')[0]
            shape = next(s for s in self.shapes if s['label'] == shape_label)
            
            result = ""
            
            if shape['type'] == 'circle':
                center = shape['center']
                radius = shape['radius']
                
                cx = center['x']
                cy = center['y']
                r = radius
                
                area = sp.pi * r ** 2
                circumference = 2 * sp.pi * r
                
                result = f"Circle {shape_label} properties:\n"
                result += f"• 圆心: ({cx}, {cy})\n"
                result += f"• r: {r}\n"
                result += f"• S: {area}\n"
                result += f"• C: {circumference}\n"
            
            elif shape['type'] == 'polygon':
                points = shape['points']
                n = len(points)
                
                area = 0
                for i in range(n):
                    x1, y1 = points[i]['x'], points[i]['y']
                    x2, y2 = points[(i + 1) % n]['x'], points[(i + 1) % n]['y']
                    area += x1 * y2 - x2 * y1
                
                area = sp.Abs(area) / 2
                
                shape_types = {
                    3: 'Triangle',
                    4: 'Quadrilateral',
                    5: 'Pentagon',
                    6: 'Hexagon'
                }
                
                shape_type = shape_types.get(n, f"Polygon{n}")
                
                result = f"{shape_type} {shape_label} properties:\n"
                result += f"• 边数n: {n}\n"
                result += f"• S: {area}\n"
                
                if n == 3:
                    triangle_result = self.test_triangle_properties(shape)
                    result += triangle_result
            
            if result:
                messagebox.showinfo("性质测试结果", result)
                self.log(f"测试图形性质: {shape_label} -> {result}")
            else:
                messagebox.showinfo("性质测试", "该图形类型的性质测试尚未实现")
        
        except Exception as e:
            messagebox.showerror("错误", f"测试性质失败: {e}")
    
    def test_triangle_properties(self, triangle):
        points = triangle['points']
        p1, p2, p3 = points
        
        try:
            sym_triangle = SymTriangle(
                Point(float(p1['x'].evalf()), float(p1['y'].evalf())),
                Point(float(p2['x'].evalf()), float(p2['y'].evalf())),
                Point(float(p3['x'].evalf()), float(p3['y'].evalf()))
            )
            
            result = ""
            
            if sym_triangle.is_equilateral():
                result += "• 是等边三角形\n"
            
            if sym_triangle.is_isosceles():
                result += "• 是等腰三角形\n"
            
            if sym_triangle.is_right():
                result += "• 是直角三角形\n"
            
            area = sym_triangle.area
            result += f"• S: {area}\n"
            
            return result
        
        except Exception as e:
            return f"Error testing triangle properties: {e}"


if __name__ == "__main__":
    root = tk.Tk()
    app = GeometryApp(root)
    root.mainloop()