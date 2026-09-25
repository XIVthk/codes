import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from datetime import datetime
import random
import time
import re
import csv


class StudentPointsSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("学生积分系统")
        self.root.geometry("1200x800")  # 增加高度以容纳小组信息
        
        self.stu_file = "stu.json"
        self.record_file = "record.json"
        self.schedule_file = "schedule.txt"
        self.rules_file = "rules.json"
        self.last_week_file = "last_week.json"
        self.group_file = "group.json"
        
        self.initialize_files()
        
        self.students = self.read_stu()
        self.records = self.read_record()
        self.rules = self.read_rules()
        self.last_week_data = self.read_last_week()
        self.groups = self.read_groups()
        
        self.often_using = ['作业完成', '跑操缺勤', '课堂表现优秀', '迟到', '志愿服务', '违反纪律']
        self.members = ['班长', '学习委员', '纪律委员', '卫生委员', '电教委员', '文娱委员', '体育委员']
        
        self.sort_by_progress = False  # 是否按进步分数排序
        
        self.create_widgets()
        self.display_students()
        self.update_status_bar()
    
    def initialize_files(self):
        if not os.path.exists(self.stu_file):
            try:
                with open(self.stu_file, 'w', encoding='utf-8') as f:
                    json.dump({"points": {}}, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"创建stu.json文件时出错: {e}")
        
        if not os.path.exists(self.record_file):
            try:
                with open(self.record_file, 'w', encoding='utf-8') as f:
                    json.dump({}, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"创建record.json文件时出错: {e}")
        
        if not os.path.exists(self.schedule_file):
            try:
                with open(self.schedule_file, 'w', encoding='utf-8') as f:
                    f.write("暂无排班信息")
            except Exception as e:
                print(f"创建schedule.txt文件时出错: {e}")
        
        if not os.path.exists(self.rules_file):
            try:
                with open(self.rules_file, 'w', encoding='utf-8') as f:
                    json.dump({}, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"创建rules.json文件时出错: {e}")
        
        if not os.path.exists(self.last_week_file):
            try:
                with open(self.last_week_file, 'w', encoding='utf-8') as f:
                    json.dump({"points": {}}, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"创建last_week.json文件时出错: {e}")
        
        if not os.path.exists(self.group_file):
            try:
                with open(self.group_file, 'w', encoding='utf-8') as f:
                    json.dump({}, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"创建group.json文件时出错: {e}")
    
    def read_stu(self):
        try:
            with open(self.stu_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("points", {})
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"读取stu.json时出错: {e}")
            messagebox.showerror("错误", f"读取学生数据时出错: {e}")
            return {}
        except Exception as e:
            print(f"读取stu.json时发生未知错误: {e}")
            return {}
    
    def read_record(self):
        try:
            with open(self.record_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"读取record.json时出错: {e}")
            messagebox.showerror("错误", f"读取记录数据时出错: {e}")
            return {}
        except Exception as e:
            print(f"读取record.json时发生未知错误: {e}")
            return {}
    
    def read_rules(self):
        try:
            with open(self.rules_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
        except Exception as e:
            print(f"读取rules.json时发生未知错误: {e}")
            return {}
    
    def read_last_week(self):
        try:
            with open(self.last_week_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("points", {})
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
        except Exception as e:
            print(f"读取last_week.json时发生未知错误: {e}")
            return {}
    
    def read_groups(self):
        try:
            with open(self.group_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
        except Exception as e:
            print(f"读取group.json时发生未知错误: {e}")
            return {}
    
    def save_stu(self):
        try:
            data = {"points": self.students}
            with open(self.stu_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存学生数据时出错: {e}")
            messagebox.showerror("错误", f"保存学生数据时出错: {e}")
    
    def save_record(self):
        try:
            with open(self.record_file, 'w', encoding='utf-8') as f:
                json.dump(self.records, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存记录数据时出错: {e}")
            messagebox.showerror("错误", f"保存记录数据时出错: {e}")
    
    def save_rules(self):
        try:
            with open(self.rules_file, 'w', encoding='utf-8') as f:
                json.dump(self.rules, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存规则数据时出错: {e}")
            messagebox.showerror("错误", f"保存规则数据时出错: {e}")
    
    def save_last_week(self):
        try:
            data = {"points": self.last_week_data}
            with open(self.last_week_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存上周数据时出错: {e}")
            messagebox.showerror("错误", f"保存上周数据时出错: {e}")
    
    def save_groups(self):
        try:
            with open(self.group_file, 'w', encoding='utf-8') as f:
                json.dump(self.groups, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存小组数据时出错: {e}")
            messagebox.showerror("错误", f"保存小组数据时出错: {e}")
    
    def create_widgets(self):
        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="添加记录", command=self.add_record).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="删除记录", command=self.delete_record).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="重置积分", command=self.reset_points).grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="全部重置", command=self.all_reset).grid(row=0, column=3, padx=5)
        ttk.Button(button_frame, text="刷新", command=self.refresh).grid(row=0, column=4, padx=5)
        ttk.Button(button_frame, text="调试", command=self.debug_info).grid(row=0, column=5, padx=5)
        ttk.Button(button_frame, text="排班", command=self.arrange_duty).grid(row=0, column=6, padx=5)
        ttk.Button(button_frame, text="积分规则", command=self.manage_rules).grid(row=0, column=7, padx=5)
        ttk.Button(button_frame, text="导出数据", command=self.export_data).grid(row=0, column=8, padx=5)
        ttk.Button(button_frame, text="小组管理", command=self.manage_groups).grid(row=0, column=9, padx=5)
        ttk.Button(button_frame, text="按进步排序", command=self.toggle_sort).grid(row=0, column=10, padx=5)
        
        # 筛选框架
        filter_frame = ttk.Frame(self.root)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(filter_frame, text="筛选学生:").pack(side=tk.LEFT, padx=5)
        self.filter_var = tk.StringVar()
        self.filter_var.trace('w', self.filter_records)
        filter_combo = ttk.Combobox(filter_frame, textvariable=self.filter_var, state="readonly")
        filter_combo['values'] = ["全部学生"] + list(self.students.keys())
        filter_combo.current(0)
        filter_combo.pack(side=tk.LEFT, padx=5)
        
        student_frame = ttk.LabelFrame(self.root, text="学生积分")
        student_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.student_labels = {}
        for i in range(5):
            for j in range(9):
                frame = ttk.Frame(student_frame, relief="solid", borderwidth=1)
                frame.grid(row=i, column=j, padx=2, pady=2, sticky="nsew")
                
                student_frame.grid_rowconfigure(i, weight=1)
                student_frame.grid_columnconfigure(j, weight=1)
                
                name_label = ttk.Label(frame, text="", font=("Arial", 10, "bold"))
                name_label.pack(pady=(5, 0))
                
                points_label = ttk.Label(frame, text="", font=("Arial", 12))
                points_label.pack(pady=(0, 5))
                
                index = i * 9 + j
                self.student_labels[index] = (name_label, points_label, frame)
        
        # 小组信息框架
        group_frame = ttk.LabelFrame(self.root, text="小组积分")
        group_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.group_labels = {}
        group_container = ttk.Frame(group_frame)
        group_container.pack(fill=tk.X, padx=5, pady=5)
        
        for i in range(6):  # 最多显示6个小组
            frame = ttk.Frame(group_container, relief="solid", borderwidth=1)
            frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
            
            name_label = ttk.Label(frame, text="", font=("Arial", 10, "bold"))
            name_label.pack(pady=(5, 0))
            
            points_label = ttk.Label(frame, text="", font=("Arial", 12))
            points_label.pack(pady=(0, 5))
            
            self.group_labels[i] = (name_label, points_label, frame)
        
        record_frame = ttk.LabelFrame(self.root, text="积分记录")
        record_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        record_columns = ("序号", "姓名", "积分变化", "原因", "时间")
        self.record_tree = ttk.Treeview(record_frame, columns=record_columns, show="headings")
        self.record_tree.configure(selectmode="extended")
        
        for col in record_columns:
            self.record_tree.heading(col, text=col)
            self.record_tree.column(col, width=120)
        
        record_scrollbar = ttk.Scrollbar(record_frame, orient=tk.VERTICAL, command=self.record_tree.yview)
        self.record_tree.configure(yscrollcommand=record_scrollbar.set)
        
        self.record_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        record_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.time_label = ttk.Label(self.status_bar, text="", relief=tk.SUNKEN, anchor=tk.W)
        self.time_label.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=2)
        
        self.status_label = ttk.Label(self.status_bar, text="就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=2, expand=True)
        
        self.schedule_label = ttk.Label(self.status_bar, text="", relief=tk.SUNKEN, anchor=tk.W)
        self.schedule_label.pack(side=tk.RIGHT, fill=tk.X, padx=5, pady=2)
        
        self.display_records()
        self.load_schedule()
        self.display_groups()
    
    def update_status_bar(self):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=f"当前时间: {current_time}")
        self.root.after(1000, self.update_status_bar)
    
    def load_schedule(self):
        try:
            with open(self.schedule_file, 'r', encoding='utf-8') as f:
                schedule_text = f.read()
                if len(schedule_text) > 50:
                    schedule_text = schedule_text[:47] + "..."
                self.schedule_label.config(text=f"排班: {schedule_text}")
        except Exception as e:
            print(f"读取排班信息时出错: {e}")
            self.schedule_label.config(text="排班: 无信息")
    
    def arrange_duty(self):
        self.status_label.config(text="正在排班...")
        
        mem = self.members.copy()
        pl = []
        
        for i in range(7):
            if mem:
                idx = random.randint(0, len(mem) - 1)
                p = mem.pop(idx)
                pl.append(p)
        
        mem = self.members.copy()
        for i in range(2):
            if mem:
                idx = random.randint(0, len(mem) - 1)
                p = mem.pop(idx)
                pl.append(p)
        
        random.shuffle(pl)
        
        days = ["周一", "周二", "周三", "周四", "周五"]
        periods = ["上午", "下午"]
        
        schedule = []
        schedule_data = {}
        idx = 0
        
        for day in days:
            schedule_data[day] = {}
            if day == "周五":
                schedule.append(f"{day}全天: {pl[idx]}")
                schedule_data[day]["全天"] = pl[idx]
                idx += 1
            else:
                for period in periods:
                    schedule.append(f"{day}{period}: {pl[idx]}")
                    schedule_data[day][period] = pl[idx]
                    idx += 1
        
        try:
            with open(self.schedule_file, 'w', encoding='utf-8') as f:
                f.write(" | ".join(schedule))
            
            self.load_schedule()
            self.status_label.config(text="排班完成")
            
            DutyScheduleWindow(self, schedule_data)
        except Exception as e:
            print(f"保存排班信息时出错: {e}")
            self.status_label.config(text="排班失败")
            messagebox.showerror("错误", f"保存排班信息时出错: {e}")
    
    def display_students(self):
        for index in range(45):
            name_label, points_label, frame = self.student_labels[index]
            name_label.config(text="")
            points_label.config(text="")
            try:
                frame.configure(style="TFrame")
            except:
                pass
        
        if not self.students:
            name_label, points_label, frame = self.student_labels[0]
            name_label.config(text="无数据")
            points_label.config(text="请添加记录")
            return
        
        # 计算每个学生的进步分数
        student_progress = {}
        for name, current_points in self.students.items():
            last_week_points = self.last_week_data.get(name, 100)  # 默认上周为100分
            progress = current_points - last_week_points
            student_progress[name] = progress
        
        # 根据排序方式选择排序依据
        if self.sort_by_progress:
            # 按进步分数排序
            sorted_students = sorted(
                self.students.items(),
                key=lambda x: student_progress[x[0]],
                reverse=True
            )
        else:
            # 按当前积分排序
            sorted_students = sorted(self.students.items(), key=lambda x: x[1], reverse=True)
        
        for i, (name, points) in enumerate(sorted_students):
            if i >= 45:
                break
            
            # 计算进步分数
            last_week_points = self.last_week_data.get(name, 100)
            progress = points - last_week_points
            
            name_label, points_label, frame = self.student_labels[i]
            name_label.config(text=name)
            
            # 显示当前积分和进步分数
            if progress > 0:
                points_label.config(text=f"{points} (+{progress})", foreground="green")
            elif progress < 0:
                points_label.config(text=f"{points} ({progress})", foreground="red")
            else:
                points_label.config(text=f"{points} (±0)", foreground="black")
            
            try:
                if points >= 90:
                    frame.configure(style="Success.TFrame")
                elif points >= 60:
                    frame.configure(style="Warning.TFrame")
                else:
                    frame.configure(style="Danger.TFrame")
            except:
                pass
    
    def display_groups(self):
        # 清空小组显示
        for i in range(6):
            name_label, points_label, frame = self.group_labels[i]
            name_label.config(text="")
            points_label.config(text="")
        
        if not self.groups:
            name_label, points_label, frame = self.group_labels[0]
            name_label.config(text="无小组数据")
            points_label.config(text="请创建小组")
            return
        
        # 计算每个小组的平均分
        group_scores = {}
        for group_name, members in self.groups.items():
            total_score = 0
            valid_members = 0
            
            for member in members:
                if member in self.students:
                    total_score += self.students[member]
                    valid_members += 1
            
            if valid_members > 0:
                average_score = total_score / valid_members
                group_scores[group_name] = average_score
        
        # 按平均分排序
        sorted_groups = sorted(group_scores.items(), key=lambda x: x[1], reverse=True)
        
        # 显示小组信息
        for i, (group_name, average_score) in enumerate(sorted_groups):
            if i >= 6:  # 最多显示6个小组
                break
            
            name_label, points_label, frame = self.group_labels[i]
            name_label.config(text=group_name)
            points_label.config(text=f"{average_score:.1f}")
    
    def display_records(self, filter_student=None):
        for item in self.record_tree.get_children():
            self.record_tree.delete(item)
        
        if not self.records:
            self.record_tree.insert("", tk.END, values=("无记录", "", "", "", ""))
            return
        
        for record_id, record_data in self.records.items():
            if "students" in record_data:
                student_names = ", ".join(record_data["students"])
                students_list = record_data["students"]
            else:
                student_names = record_data.get("name", "")
                students_list = [record_data.get("name", "")]
            
            # 筛选记录
            if filter_student and filter_student != "全部学生":
                if filter_student not in students_list:
                    continue
            
            self.record_tree.insert("", tk.END, values=(
                record_id,
                student_names,
                record_data.get("point", ""),
                record_data.get("reason", ""),
                record_data.get("time", "")
            ))
    
    def filter_records(self, *args):
        if not hasattr(self, 'record_tree'):  # 添加检查
            return
        selected_student = self.filter_var.get()
        if selected_student:
            self.display_records(selected_student)
    
    def add_record(self):
        self.status_label.config(text="正在添加记录...")
        AddRecordWindow(self)
    
    def delete_record(self):
        selected = self.record_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请选择要删除的记录")
            return
        
        if messagebox.askyesno("确认", f"确定要删除选中的 {len(selected)} 条记录吗？"):
            self.status_label.config(text="正在删除记录...")
            
            for item in selected:
                item_values = self.record_tree.item(item, "values")
                
                if not item_values or item_values[0] == "无记录":
                    continue
                
                record_id = item_values[0]
                
                if record_id not in self.records:
                    continue
                
                record_data = self.records[record_id]
                point_change = record_data["point"]
                
                if "students" in record_data:
                    for student_name in record_data["students"]:
                        if student_name in self.students:
                            self.students[student_name] -= point_change
                else:
                    student_name = record_data["name"]
                    if student_name in self.students:
                        self.students[student_name] -= point_change
                
                del self.records[record_id]
            
            self.save_stu()
            self.save_record()
            
            self.display_students()
            self.display_groups()  # 更新小组显示
            self.display_records()
            self.status_label.config(text="记录已删除")
    
    def reset_points(self):
        self.status_label.config(text="正在重置积分...")
        ResetPointsWindow(self)
    
    def all_reset(self):
        if messagebox.askyesno("确认", "确定要重置所有学生的积分吗？"):
            self.status_label.config(text="正在重置所有积分...")
            
            # 保存当前数据到上周数据
            self.last_week_data = self.students.copy()
            self.save_last_week()
            
            # 重置所有学生积分
            for student in self.students:
                self.students[student] = 100
            
            self.save_stu()
            self.display_students()
            self.display_groups()  # 更新小组显示
            self.status_label.config(text="所有积分已重置，上周数据已保存")
    
    def refresh(self):
        self.status_label.config(text="正在刷新数据...")
        self.students = self.read_stu()
        self.records = self.read_record()
        self.rules = self.read_rules()
        self.last_week_data = self.read_last_week()
        self.groups = self.read_groups()
        self.display_students()
        self.display_groups()  # 更新小组显示
        self.display_records()
        
        # 更新筛选下拉框
        filter_combo = self.root.nametowidget(self.status_bar.master.winfo_children()[1].winfo_children()[1])
        filter_combo['values'] = ["全部学生"] + list(self.students.keys())
        
        self.status_label.config(text="数据已刷新")
    
    def debug_info(self):
        info = f"学生数据: {self.students}\n记录数据: {self.records}"
        messagebox.showinfo("调试信息", info)
    
    def parse_student_id_input(self, id_input):
        """解析学号输入，支持多种格式如: 1, 03, 15, 0043"""
        student_names = []
        id_list = [id_str.strip() for id_str in id_input.split(',')]
        
        for id_str in id_list:
            if not id_str:
                continue
            
            # 尝试转换为整数
            try:
                student_id = int(id_str)
            except ValueError:
                continue
            
            # 在学生列表中查找匹配的学生
            found = False
            for name in self.students.keys():
                # 使用正则表达式提取学号部分
                match = re.match(r'\[(\d+)\](.+)', name)
                if match:
                    id_in_name = int(match.group(1))
                    if id_in_name == student_id:
                        student_names.append(name)
                        found = True
                        break
            
            if not found:
                messagebox.showwarning("警告", f"未找到学号为 {student_id} 的学生")
        
        return student_names
    
    def manage_rules(self):
        self.status_label.config(text="正在管理积分规则...")
        RulesManagerWindow(self)
    
    def manage_groups(self):
        self.status_label.config(text="正在管理小组...")
        GroupManagerWindow(self)
    
    def toggle_sort(self):
        self.sort_by_progress = not self.sort_by_progress
        self.display_students()
        if self.sort_by_progress:
            self.status_label.config(text="已按进步分数排序")
        else:
            self.status_label.config(text="已按当前积分排序")
    
    def export_data(self):
        self.status_label.config(text="正在导出数据...")
        
        # 选择保存路径
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")],
            title="导出数据"
        )
        
        if not file_path:
            self.status_label.config(text="导出已取消")
            return
        
        try:
            # 导出学生积分数据
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['学号', '姓名', '当前积分', '上周积分', '进步分数'])
                
                for name, points in self.students.items():
                    # 提取学号和姓名
                    match = re.match(r'\[(\d+)\](.+)', name)
                    if match:
                        student_id = match.group(1)
                        student_name = match.group(2)
                        last_week_points = self.last_week_data.get(name, 100)
                        progress = points - last_week_points
                        writer.writerow([student_id, student_name, points, last_week_points, progress])
                    else:
                        last_week_points = self.last_week_data.get(name, 100)
                        progress = points - last_week_points
                        writer.writerow(['', name, points, last_week_points, progress])
            
            # 导出积分记录
            record_path = file_path.replace('.csv', '_records.csv')
            with open(record_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['记录ID', '学生', '积分变化', '原因', '时间'])
                
                for record_id, record_data in self.records.items():
                    if "students" in record_data:
                        student_names = ", ".join(record_data["students"])
                    else:
                        student_names = record_data.get("name", "")
                    
                    writer.writerow([
                        record_id,
                        student_names,
                        record_data.get("point", ""),
                        record_data.get("reason", ""),
                        record_data.get("time", "")
                    ])
            
            # 导出小组数据
            group_path = file_path.replace('.csv', '_groups.csv')
            with open(group_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['小组名称', '成员', '平均分'])
                
                for group_name, members in self.groups.items():
                    total_score = 0
                    valid_members = 0
                    
                    for member in members:
                        if member in self.students:
                            total_score += self.students[member]
                            valid_members += 1
                    
                    if valid_members > 0:
                        average_score = total_score / valid_members
                    else:
                        average_score = 0
                    
                    writer.writerow([group_name, ", ".join(members), f"{average_score:.1f}"])
            
            self.status_label.config(text=f"数据已导出到: {file_path}")
            messagebox.showinfo("导出成功", f"数据已成功导出到:\n{file_path}\n{record_path}\n{group_path}")
        
        except Exception as e:
            self.status_label.config(text="导出失败")
            messagebox.showerror("导出错误", f"导出数据时出错: {e}")


class DutyScheduleWindow(tk.Toplevel):
    def __init__(self, parent, schedule_data):
        super().__init__(parent.root)
        self.parent = parent
        self.title("排班结果")
        self.geometry("600x300")
        
        self.create_table(schedule_data)
        
        ttk.Button(self, text="关闭", command=self.destroy).pack(pady=10)
    
    def create_table(self, schedule_data):
        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ("时间段", "周一", '周二', "周三", "周四", "周五")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", height=3)
        
        self.tree.column("时间段", width=80)
        for col in columns[1:]:
            self.tree.column(col, width=100)
        
        for col in columns:
            self.tree.heading(col, text=col)
        
        morning_data = ["上午"]
        for day in columns[1:]:
            morning_data.append(schedule_data[day].get("上午", ""))
        self.tree.insert("", tk.END, values=morning_data)
        
        afternoon_data = ["下午"]
        for day in columns[1:]:
            afternoon_data.append(schedule_data[day].get("下午", ""))
        self.tree.insert("", tk.END, values=afternoon_data)
        
        friday_data = ["全天", "", "", "", "", schedule_data["周五"].get("全天", "")]
        self.tree.insert("", tk.END, values=friday_data)
        
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)


class AddRecordWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent.root)
        self.parent = parent
        self.title("添加记录")
        self.geometry("500x550")
        
        self.record_id = self.get_next_record_id()
        self.selected_students = []
        
        self.create_widgets()
    
    def get_next_record_id(self):
        if not self.parent.records:
            return "01"
        
        max_id = max([int(k) for k in self.parent.records.keys()])
        return f"{max_id + 1:02d}"
    
    def create_widgets(self):
        ttk.Label(self, text="事件序号:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Label(self, text=self.record_id).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(self, text="名字:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.name_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.name_var, state="readonly", width=20).grid(row=1, column=1, padx=5, pady=5,
                                                                                     sticky=tk.W)
        ttk.Button(self, text="选择学生", command=self.select_students).grid(row=1, column=2, padx=5, pady=5)
        
        ttk.Label(self, text="或输入学号:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.id_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.id_var, width=20).grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Button(self, text="添加学号", command=self.add_by_id).grid(row=2, column=2, padx=5, pady=5)
        
        ttk.Label(self, text="积分规则:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        self.rule_var = tk.StringVar()
        rule_combo = ttk.Combobox(self, textvariable=self.rule_var, state="readonly", width=20)
        rule_combo['values'] = list(self.parent.rules.keys())
        rule_combo.grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)
        rule_combo.bind('<<ComboboxSelected>>', self.apply_rule)
        
        ttk.Label(self, text="分数:").grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
        self.point_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.point_var).grid(row=4, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(self, text="原因:").grid(row=5, column=0, padx=5, pady=5, sticky=tk.W)
        self.reason_text = tk.Text(self, height=5, width=30)
        self.reason_text.grid(row=5, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(self, text="常用原因:").grid(row=6, column=0, padx=5, pady=5, sticky=tk.W)
        reason_frame = ttk.Frame(self)
        reason_frame.grid(row=6, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W)
        
        for i, reason in enumerate(self.parent.often_using):
            btn = ttk.Button(reason_frame, text=reason,
                             command=lambda r=reason: self.insert_reason(r))
            btn.grid(row=i // 3, column=i % 3, padx=2, pady=2)
        
        button_frame = ttk.Frame(self)
        button_frame.grid(row=7, column=0, columnspan=3, pady=10)
        
        ttk.Button(button_frame, text="确定", command=self.ok).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="取消", command=self.destroy).pack(side=tk.LEFT, padx=10)
    
    def apply_rule(self, event):
        rule_name = self.rule_var.get()
        if rule_name in self.parent.rules:
            rule = self.parent.rules[rule_name]
            self.point_var.set(str(rule["points"]))
            self.reason_text.delete("1.0", tk.END)
            self.reason_text.insert(tk.END, rule["reason"])
    
    def select_students(self):
        SelectStudentsWindow(self)
    
    def add_by_id(self):
        id_input = self.id_var.get()
        if not id_input:
            messagebox.showwarning("警告", "请输入学号")
            return
        
        student_names = self.parent.parse_student_id_input(id_input)
        if student_names:
            self.selected_students.extend(student_names)
            # 去重
            self.selected_students = list(set(self.selected_students))
            
            if len(self.selected_students) == 1:
                self.name_var.set(self.selected_students[0])
            else:
                self.name_var.set(f"{len(self.selected_students)}名学生")
            
            self.id_var.set("")  # 清空输入框
    
    def insert_reason(self, reason):
        self.reason_text.insert(tk.END, reason)
    
    def ok(self):
        if not self.selected_students:
            messagebox.showwarning("警告", "请选择至少一名学生")
            return
        
        try:
            points = int(self.point_var.get())
        except ValueError:
            messagebox.showwarning("警告", "请输入有效的分数")
            return
        
        reason = self.reason_text.get("1.0", tk.END).strip()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        record_data = {
            "students": self.selected_students,
            "point": points,
            "reason": reason,
            "time": current_time
        }
        
        self.parent.records[self.record_id] = record_data
        
        for student in self.selected_students:
            if student in self.parent.students:
                self.parent.students[student] += points
            else:
                self.parent.students[student] = points
        
        self.parent.save_stu()
        self.parent.save_record()
        
        self.parent.display_students()
        self.parent.display_groups()  # 更新小组显示
        self.parent.display_records()
        self.parent.status_label.config(text="记录已添加")
        
        self.destroy()


class ResetPointsWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent.root)
        self.parent = parent
        self.title("重置积分")
        self.geometry("400x300")
        
        self.selected_students = []
        
        self.create_widgets()
    
    def create_widgets(self):
        ttk.Label(self, text="选择学生:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.name_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.name_var, state="readonly", width=20).grid(row=0, column=1, padx=5, pady=5,
                                                                                     sticky=tk.W)
        ttk.Button(self, text="选择学生", command=self.select_students).grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Label(self, text="或输入学号:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.id_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.id_var, width=20).grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Button(self, text="添加学号", command=self.add_by_id).grid(row=1, column=2, padx=5, pady=5)
        
        button_frame = ttk.Frame(self)
        button_frame.grid(row=2, column=0, columnspan=3, pady=10)
        
        ttk.Button(button_frame, text="确定", command=self.ok).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="取消", command=self.destroy).pack(side=tk.LEFT, padx=10)
    
    def select_students(self):
        SelectStudentsWindow(self)
    
    def add_by_id(self):
        id_input = self.id_var.get()
        if not id_input:
            messagebox.showwarning("警告", "请输入学号")
            return
        
        student_names = self.parent.parse_student_id_input(id_input)
        if student_names:
            self.selected_students.extend(student_names)
            # 去重
            self.selected_students = list(set(self.selected_students))
            
            if len(self.selected_students) == 1:
                self.name_var.set(self.selected_students[0])
            else:
                self.name_var.set(f"{len(self.selected_students)}名学生")
            
            self.id_var.set("")  # 清空输入框
    
    def ok(self):
        if not self.selected_students:
            messagebox.showwarning("警告", "请选择至少一名学生")
            return
        
        if messagebox.askyesno("确认", f"确定要重置 {len(self.selected_students)} 名学生的积分吗？"):
            self.parent.status_label.config(text="正在重置积分...")
            for student in self.selected_students:
                self.parent.students[student] = 100
            self.parent.save_stu()
            self.parent.display_students()
            self.parent.display_groups()  # 更新小组显示
            self.parent.status_label.config(text="积分已重置")
            self.destroy()


class SelectStudentsWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("选择学生")
        self.geometry("300x400")
        
        self.create_widgets()
    
    def create_widgets(self):
        ttk.Label(self, text="选择学生:").pack(pady=5)
        
        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.listbox = tk.Listbox(frame, selectmode=tk.MULTIPLE)
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scrollbar.set)
        
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        for student in self.parent.parent.students:
            self.listbox.insert(tk.END, student)
        
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="确定", command=self.ok).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="取消", command=self.destroy).pack(side=tk.LEFT, padx=10)
    
    def ok(self):
        selected_indices = self.listbox.curselection()
        self.parent.selected_students = [self.listbox.get(i) for i in selected_indices]
        
        if self.parent.selected_students:
            if len(self.parent.selected_students) == 1:
                self.parent.name_var.set(self.parent.selected_students[0])
            else:
                self.parent.name_var.set(f"{len(self.parent.selected_students)}名学生")
        
        self.destroy()


class RulesManagerWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent.root)
        self.parent = parent
        self.title("积分规则管理")
        self.geometry("600x400")
        
        self.create_widgets()
        self.load_rules()
    
    def create_widgets(self):
        # 规则列表
        list_frame = ttk.LabelFrame(self, text="规则列表")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        columns = ("规则名称", "积分值", "原因")
        self.rules_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        for col in columns:
            self.rules_tree.heading(col, text=col)
            self.rules_tree.column(col, width=150)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.rules_tree.yview)
        self.rules_tree.configure(yscrollcommand=scrollbar.set)
        
        self.rules_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 按钮框架
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(button_frame, text="添加规则", command=self.add_rule).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="编辑规则", command=self.edit_rule).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="删除规则", command=self.delete_rule).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="关闭", command=self.destroy).pack(side=tk.RIGHT, padx=5)
    
    def load_rules(self):
        for item in self.rules_tree.get_children():
            self.rules_tree.delete(item)
        
        for rule_name, rule_data in self.parent.rules.items():
            self.rules_tree.insert("", tk.END, values=(
                rule_name,
                rule_data.get("points", ""),
                rule_data.get("reason", "")
            ))
    
    def add_rule(self):
        RuleEditorWindow(self, None)
    
    def edit_rule(self):
        selected = self.rules_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请选择要编辑的规则")
            return
        
        item = selected[0]
        rule_name = self.rules_tree.item(item, "values")[0]
        RuleEditorWindow(self, rule_name)
    
    def delete_rule(self):
        selected = self.rules_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请选择要删除的规则")
            return
        
        item = selected[0]
        rule_name = self.rules_tree.item(item, "values")[0]
        
        if messagebox.askyesno("确认", f"确定要删除规则 '{rule_name}' 吗？"):
            if rule_name in self.parent.rules:
                del self.parent.rules[rule_name]
                self.parent.save_rules()
                self.load_rules()
                self.parent.status_label.config(text="规则已删除")


class RuleEditorWindow(tk.Toplevel):
    def __init__(self, parent, rule_name):
        super().__init__(parent)
        self.parent = parent
        self.rule_name = rule_name
        self.title("编辑规则" if rule_name else "添加规则")
        self.geometry("400x300")
        
        self.create_widgets()
    
    def create_widgets(self):
        ttk.Label(self, text="规则名称:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.name_var = tk.StringVar(value=self.rule_name or "")
        ttk.Entry(self, textvariable=self.name_var).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(self, text="积分值:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.points_var = tk.StringVar()
        if self.rule_name and self.rule_name in self.parent.parent.rules:
            self.points_var.set(str(self.parent.parent.rules[self.rule_name]["points"]))
        ttk.Entry(self, textvariable=self.points_var).grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(self, text="原因:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.reason_text = tk.Text(self, height=5, width=30)
        if self.rule_name and self.rule_name in self.parent.parent.rules:
            self.reason_text.insert(tk.END, self.parent.parent.rules[self.rule_name]["reason"])
        self.reason_text.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        
        button_frame = ttk.Frame(self)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="保存", command=self.save_rule).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="取消", command=self.destroy).pack(side=tk.LEFT, padx=10)
    
    def save_rule(self):
        rule_name = self.name_var.get().strip()
        if not rule_name:
            messagebox.showwarning("警告", "请输入规则名称")
            return
        
        try:
            points = int(self.points_var.get())
        except ValueError:
            messagebox.showwarning("警告", "请输入有效的积分值")
            return
        
        reason = self.reason_text.get("1.0", tk.END).strip()
        if not reason:
            messagebox.showwarning("警告", "请输入原因")
            return
        
        # 如果是编辑现有规则且名称改变，需要删除旧规则
        if self.rule_name and self.rule_name != rule_name and self.rule_name in self.parent.parent.rules:
            del self.parent.parent.rules[self.rule_name]
        
        # 保存规则
        self.parent.parent.rules[rule_name] = {
            "points": points,
            "reason": reason
        }
        
        self.parent.parent.save_rules()
        self.parent.load_rules()
        self.parent.parent.status_label.config(text="规则已保存")
        self.destroy()


class GroupManagerWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent.root)
        self.parent = parent
        self.title("小组管理")
        self.geometry("600x500")
        
        self.create_widgets()
        self.load_groups()
    
    def create_widgets(self):
        # 小组列表
        list_frame = ttk.LabelFrame(self, text="小组列表")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        columns = ("小组名称", "成员数量", "平均分")
        self.groups_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        for col in columns:
            self.groups_tree.heading(col, text=col)
            self.groups_tree.column(col, width=150)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.groups_tree.yview)
        self.groups_tree.configure(yscrollcommand=scrollbar.set)
        
        self.groups_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 按钮框架
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(button_frame, text="添加小组", command=self.add_group).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="编辑小组", command=self.edit_group).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="删除小组", command=self.delete_group).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="关闭", command=self.destroy).pack(side=tk.RIGHT, padx=5)
    
    def load_groups(self):
        for item in self.groups_tree.get_children():
            self.groups_tree.delete(item)
        
        for group_name, members in self.parent.groups.items():
            # 计算平均分
            total_score = 0
            valid_members = 0
            
            for member in members:
                if member in self.parent.students:
                    total_score += self.parent.students[member]
                    valid_members += 1
            
            if valid_members > 0:
                average_score = total_score / valid_members
            else:
                average_score = 0
            
            self.groups_tree.insert("", tk.END, values=(
                group_name,
                f"{len(members)}人",
                f"{average_score:.1f}"
            ))
    
    def add_group(self):
        GroupEditorWindow(self, None)
    
    def edit_group(self):
        selected = self.groups_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请选择要编辑的小组")
            return
        
        item = selected[0]
        group_name = self.groups_tree.item(item, "values")[0]
        GroupEditorWindow(self, group_name)
    
    def delete_group(self):
        selected = self.groups_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请选择要删除的小组")
            return
        
        item = selected[0]
        group_name = self.groups_tree.item(item, "values")[0]
        
        if messagebox.askyesno("确认", f"确定要删除小组 '{group_name}' 吗？"):
            if group_name in self.parent.groups:
                del self.parent.groups[group_name]
                self.parent.save_groups()
                self.load_groups()
                self.parent.display_groups()  # 更新主界面小组显示
                self.parent.status_label.config(text="小组已删除")


class GroupEditorWindow(tk.Toplevel):
    def __init__(self, parent, group_name):
        super().__init__(parent)
        self.parent = parent
        self.group_name = group_name
        self.title("编辑小组" if group_name else "添加小组")
        self.geometry("500x400")
        
        self.selected_students = []
        if group_name and group_name in self.parent.parent.groups:
            self.selected_students = self.parent.parent.groups[group_name].copy()
        
        self.create_widgets()
    
    def create_widgets(self):
        ttk.Label(self, text="小组名称:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.name_var = tk.StringVar(value=self.group_name or "")
        ttk.Entry(self, textvariable=self.name_var).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(self, text="选择学生:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.name_display_var = tk.StringVar()
        if self.selected_students:
            if len(self.selected_students) == 1:
                self.name_display_var.set(self.selected_students[0])
            else:
                self.name_display_var.set(f"{len(self.selected_students)}名学生")
        ttk.Entry(self, textvariable=self.name_display_var, state="readonly", width=20).grid(row=1, column=1, padx=5,
                                                                                             pady=5, sticky=tk.W)
        ttk.Button(self, text="选择学生", command=self.select_students).grid(row=1, column=2, padx=5, pady=5)
        
        ttk.Label(self, text="或输入学号:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.id_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.id_var, width=20).grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Button(self, text="添加学号", command=self.add_by_id).grid(row=2, column=2, padx=5, pady=5)
        
        button_frame = ttk.Frame(self)
        button_frame.grid(row=3, column=0, columnspan=3, pady=10)
        
        ttk.Button(button_frame, text="保存", command=self.save_group).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="取消", command=self.destroy).pack(side=tk.LEFT, padx=10)
    
    def select_students(self):
        SelectGroupStudentsWindow(self)
    
    def add_by_id(self):
        id_input = self.id_var.get()
        if not id_input:
            messagebox.showwarning("警告", "请输入学号")
            return
        
        # 修正层级关系访问
        app = self.parent.parent  # 获取主应用程序实例
        student_names = app.parse_student_id_input(id_input)  # 直接使用 app
        if student_names:
            self.selected_students.extend(student_names)
            # 去重
            self.selected_students = list(set(self.selected_students))
            
            if len(self.selected_students) == 1:
                self.name_display_var.set(self.selected_students[0])
            else:
                self.name_display_var.set(f"{len(self.selected_students)}名学生")
            
            self.id_var.set("")  # 清空输入框
    
    def save_group(self):
        group_name = self.name_var.get().strip()
        if not group_name:
            messagebox.showwarning("警告", "请输入小组名称")
            return
        
        if not self.selected_students:
            messagebox.showwarning("警告", "请选择至少一名学生")
            return
        
        # 如果是编辑现有小组且名称改变，需要删除旧小组
        if self.group_name and self.group_name != group_name and self.group_name in self.parent.parent.groups:
            del self.parent.parent.groups[self.group_name]
        
        # 保存小组
        self.parent.parent.groups[group_name] = self.selected_students
        self.parent.parent.save_groups()
        self.parent.load_groups()
        self.parent.parent.display_groups()  # 更新主界面小组显示
        self.parent.parent.status_label.config(text="小组已保存")
        self.destroy()


class SelectGroupStudentsWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("选择学生")
        self.geometry("300x400")
        
        self.create_widgets()
    
    def create_widgets(self):
        ttk.Label(self, text="选择学生:").pack(pady=5)
        
        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.listbox = tk.Listbox(frame, selectmode=tk.MULTIPLE)
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scrollbar.set)
        
        # 修正层级关系访问
        app = self.parent.parent.parent  # 获取主应用程序实例
        for i, student in enumerate(app.students):  # 直接使用 app.students
            self.listbox.insert(tk.END, student)
            if student in self.parent.selected_students:
                self.listbox.select_set(i)
        
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="确定", command=self.ok).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="取消", command=self.destroy).pack(side=tk.LEFT, padx=10)
    
    def ok(self):
        selected_indices = self.listbox.curselection()
        self.parent.selected_students = [self.listbox.get(i) for i in selected_indices]
        
        if self.parent.selected_students:
            if len(self.parent.selected_students) == 1:
                self.parent.name_display_var.set(self.parent.selected_students[0])
            else:
                self.parent.name_display_var.set(f"{len(self.parent.selected_students)}名学生")
        
        self.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    
    style = ttk.Style()
    style.configure("Success.TFrame", background="#d4edda")
    style.configure("Warning.TFrame", background="#fff3cd")
    style.configure("Danger.TFrame", background="#f8d7da")
    
    app = StudentPointsSystem(root)
    root.mainloop()