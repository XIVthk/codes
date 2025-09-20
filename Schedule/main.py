import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
import socketio
import threading
import json
import time
from typing import Dict, List, Tuple
import os

# 创建锁对象用于线程安全
db_lock = threading.Lock()
file_lock = threading.Lock()
# 创建 Socket.IO 客户端
sio = socketio.Client()
# 全局用户名变量
username: str = ""
# 原课表副本
original_timetable = {}


# 连接数据库
def get_db_connection() -> sqlite3.Connection:
    return sqlite3.connect('timetable.db')


# 初始化数据
def initialize_data() -> None:
    global original_timetable
    with db_lock:
        with get_db_connection() as conn:
            c = conn.cursor()
            try:
                c.execute('''CREATE TABLE IF NOT EXISTS users
                             (id INTEGER PRIMARY KEY,
                              username TEXT UNIQUE,
                              password TEXT,
                              is_admin INTEGER)''')
                c.execute('''CREATE TABLE IF NOT EXISTS classes
                             (id INTEGER PRIMARY KEY,
                              class_name TEXT UNIQUE)''')
                c.execute('''CREATE TABLE IF NOT EXISTS schedule
                             (id INTEGER PRIMARY KEY,
                              class_id INTEGER,
                              time TEXT,
                              course TEXT,
                              teacher TEXT,
                              is_swapped INTEGER DEFAULT 0,
                              week TEXT,
                              FOREIGN KEY (class_id) REFERENCES classes(id))''')
                c.execute('''CREATE TABLE IF NOT EXISTS swap_requests
                             (id INTEGER PRIMARY KEY,
                              request_teacher TEXT,
                              target_teacher TEXT,
                              class_id INTEGER,
                              time TEXT,
                              status TEXT,
                              week TEXT,
                              FOREIGN KEY (class_id) REFERENCES classes(id))''')
                
                c.execute("INSERT OR IGNORE INTO users (username, password, is_admin) VALUES (?,?,?)",
                          ("admin", "admin123", 1))
                try:
                    # 明确指定编码格式为 UTF-8
                    with open('info.txt', 'r', encoding='utf-8') as file:
                        for line in file:
                            line = line.strip()
                            if line and not line.startswith('#'):  # 过滤掉注释行
                                user, password = line.split('-')
                                c.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?,?)",
                                          (user, password))
                except FileNotFoundError:
                    pass
                
                # 插入班级数据
                classes = ['一年级一班', '一年级二班']
                for class_name in classes:
                    c.execute("INSERT OR IGNORE INTO classes (class_name) VALUES (?)", (class_name,))
                
                # 读取课表数据并插入到 schedule 表
                timetable = read_timetable()
                original_timetable = timetable.copy()
                for class_name, schedule in timetable.items():
                    c.execute("SELECT id FROM classes WHERE class_name =?", (class_name,))
                    class_id = c.fetchone()[0]
                    for time, course_info in schedule.items():
                        course = course_info["course"]
                        teacher = course_info["teacher"]
                        # 插入本周和下周的数据
                        for week in ["本周", "下周"]:
                            # 检查数据是否已经存在
                            c.execute(
                                "SELECT id FROM schedule WHERE class_id =? AND time =? AND course =? AND teacher =? AND week =?",
                                (class_id, time, course, teacher, week))
                            result = c.fetchone()
                            if not result:
                                c.execute(
                                    "INSERT INTO schedule (class_id, time, course, teacher, week) VALUES (?,?,?,?,?)",
                                    (class_id, time, course, teacher, week))
                
                conn.commit()
                print("数据库初始化成功")
            except Exception as e:
                print(f"初始化数据时出错: {e}")


# 读取课表文件
def read_timetable() -> Dict[str, Dict[str, Dict[str, str]]]:
    try:
        file_path = os.path.abspath('Sche.txt')
        print(f"尝试读取文件: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            if not data:
                print("课表文件 Sche.txt 内容为空")
            print(f"读取到的课表数据: {data}")  # 添加调试信息
            return data
    except FileNotFoundError:
        print("未找到课表文件 Sche.txt")
        return {}
    except json.JSONDecodeError as e:
        print(f"课表文件 Sche.txt 格式错误: {e}")
        return {}


# 保存课表到文件
def save_timetable(timetable: Dict[str, Dict[str, Dict[str, str]]]) -> None:
    with file_lock:
        try:
            file_path = os.path.abspath('Sche.txt')
            print(f"尝试保存文件到: {file_path}")
            print(f"保存的课表数据: {timetable}")  # 添加调试信息
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(timetable, file, ensure_ascii=False, indent=4)
            print("课表已保存到 Sche.txt")
        except FileNotFoundError as e:
            print(f"文件未找到: {e}，请检查文件路径是否正确。")
        except PermissionError as e:
            print(f"没有权限写入文件: {e}，请检查文件权限。")
        except json.JSONDecodeError as e:
            print(f"JSON 编码错误: {e}，请检查课表数据格式。")
        except Exception as e:
            import traceback
            print(f"保存课表到文件时出错: {e}")
            traceback.print_exc()  # 打印详细的错误堆栈信息


# 登录函数
def login() -> None:
    global username
    username = entry_username.get()
    password = entry_password.get()
    with db_lock:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT id, is_admin FROM users WHERE username =? AND password =?", (username, password))
            result = c.fetchone()
    if result:
        user_id, is_admin = result
        root.destroy()
        sio.emit('login_success', {'username': username})
        if is_admin:
            admin_dashboard(user_id, username)
        else:
            teacher_dashboard(user_id, username)
    else:
        messagebox.showerror("登录失败", "用户名或密码错误")


# 教师工作台
def teacher_dashboard(user_id: int, username: str) -> None:
    global teacher_window
    teacher_window = tk.Tk()
    teacher_window.title(f"教师 - {username} 工作台")
    teacher_window.geometry("800x600")  # 设置窗口大小
    
    # 创建班级选项卡
    class_tab_control = ttk.Notebook(teacher_window)
    
    timetable = read_timetable()
    print(f"加载的课表数据: {timetable}")  # 添加调试信息
    classes = list(timetable.keys())
    
    if not classes:
        print("未找到班级信息")
        return
    
    for class_name in classes:
        class_tab = ttk.Frame(class_tab_control)
        class_tab_control.add(class_tab, text=class_name)
        
        # 创建周次和日期选项卡
        day_tab_control = ttk.Notebook(class_tab)
        day_tab_control.pack(expand=1, fill="both")
        
        schedule = timetable[class_name]
        days = ["周一", "周二"]  # 可根据实际情况扩展
        for day in days:
            day_tab = ttk.Frame(day_tab_control)
            day_tab_control.add(day_tab, text=day)
            
            row = 0
            for time, course_info in schedule.items():
                if day in time:
                    course = course_info["course"]
                    teacher = course_info["teacher"]
                    time_label = tk.Label(day_tab, text=time)
                    time_label.grid(row=row, column=0, padx=10, pady=5)
                    
                    course_label = tk.Label(day_tab, text=course)
                    course_label.grid(row=row, column=1, padx=10, pady=5)
                    
                    teacher_label = tk.Label(day_tab, text=teacher)
                    teacher_label.grid(row=row, column=2, padx=10, pady=5)
                    
                    if teacher == username:
                        # 自己的课程，加粗显示，无换课操作
                        time_label.config(font=('TkDefaultFont', 10, 'bold'))
                        course_label.config(font=('TkDefaultFont', 10, 'bold'))
                        teacher_label.config(font=('TkDefaultFont', 10, 'bold'))
                        operation_label = tk.Label(day_tab, text="")
                    else:
                        def send_swap_request(time=time, class_name=class_name, target_teacher=teacher):
                            def select_swap_course():
                                swap_window = tk.Toplevel()
                                swap_window.title("选择交换课程")
                                swap_window.geometry("800x600")
                                
                                # 创建周次选项卡
                                week_tab_control = ttk.Notebook(swap_window)
                                week_tab_control.pack(expand=1, fill="both")
                                
                                weeks = ["本周", "下周"]
                                for week in weeks:
                                    week_tab = ttk.Frame(week_tab_control)
                                    week_tab_control.add(week_tab, text=week)
                                    
                                    # 创建日期选项卡
                                    day_tab_control = ttk.Notebook(week_tab)
                                    day_tab_control.pack(expand=1, fill="both")
                                    
                                    for day in days:
                                        day_tab = ttk.Frame(day_tab_control)
                                        day_tab_control.add(day_tab, text=day)
                                        
                                        row = 0
                                        with db_lock:
                                            with get_db_connection() as conn:
                                                c = conn.cursor()
                                                c.execute(
                                                    "SELECT id, time, course FROM schedule WHERE teacher =? AND class_id = (SELECT id FROM classes WHERE class_name =?) AND time LIKE? AND week =?",
                                                    (username, class_name, f"%{day}%", week))
                                                my_courses = c.fetchall()
                                                print(
                                                    f"查询到的 {username} 在 {class_name} 班级 {day} {week} 的课程: {my_courses}")  # 添加调试信息
                                        
                                        if not my_courses:
                                            no_course_label = tk.Label(day_tab, text="今日没有您的课哦")
                                            no_course_label.grid(row=row, column=0, padx=10, pady=5)
                                        else:
                                            for course_id, course_time, course_name in my_courses:
                                                time_label = tk.Label(day_tab, text=course_time,
                                                                      font=('TkDefaultFont', 10, 'bold'))
                                                time_label.grid(row=row, column=0, padx=10, pady=5)
                                                
                                                course_label = tk.Label(day_tab, text=course_name,
                                                                        font=('TkDefaultFont', 10, 'bold'))
                                                course_label.grid(row=row, column=1, padx=10, pady=5)
                                                
                                                def on_click(selected_course_id=course_id, selected_time=course_time,
                                                             selected_course=course_name):
                                                    # 检查 Socket.IO 连接状态
                                                    if not sio.connected:
                                                        messagebox.showerror("错误", "未连接到 Socket.IO 服务器")
                                                        return
                                                    try:
                                                        with db_lock:
                                                            with get_db_connection() as conn:
                                                                c = conn.cursor()
                                                                c.execute("SELECT id FROM classes WHERE class_name =?",
                                                                          (class_name,))
                                                                class_id = c.fetchone()[0]
                                                                # 查询目标课程的 class_id
                                                                c.execute(
                                                                    "SELECT class_id FROM schedule WHERE teacher =? AND time =? AND week =?",
                                                                    (target_teacher, time, week))
                                                                target_class_id_result = c.fetchone()
                                                                target_class_id = target_class_id_result[
                                                                    0] if target_class_id_result else None
                                                                # 获取目标课程的名称
                                                                c.execute(
                                                                    "SELECT course FROM schedule WHERE teacher =? AND time =? AND week =?",
                                                                    (target_teacher, time, week))
                                                                target_course_result = c.fetchone()
                                                                target_course = target_course_result[
                                                                    0] if target_course_result else None
                                                                request_data = {
                                                                    'request_teacher': username,
                                                                    'target_teacher': target_teacher,
                                                                    'class_id': class_id,
                                                                    'time': time,
                                                                    'week': week,
                                                                    'selected_course_id': selected_course_id,
                                                                    'selected_time': selected_time,
                                                                    'selected_course': selected_course,
                                                                    'target_class_id': target_class_id,
                                                                    'class_name': class_name,
                                                                    'course': target_course  # 更新 course 字段为目标课程名称
                                                                }
                                                                print(f"发送的换课请求数据: {request_data}")  # 添加调试信息
                                                                sio.emit('swap_request', request_data)
                                                        messagebox.showinfo("换课请求",
                                                                            f"已发送 {week} {time} 的换课请求")
                                                        swap_window.destroy()
                                                    except Exception as e:
                                                        print(f"发送换课请求时出错: {e}")
                                                        messagebox.showerror("错误", f"发送换课请求时出错: {e}")
                                                
                                                select_button = tk.Button(day_tab, text="选择",
                                                                          command=lambda: on_click())
                                                select_button.grid(row=row, column=2, padx=10, pady=5)
                                                row += 1
                            
                            select_swap_course()
                        
                        operation_label = tk.Button(day_tab, text="换课", command=send_swap_request)
                    operation_label.grid(row=row, column=3, padx=10, pady=5)
                    row += 1
    
    class_tab_control.pack(expand=1, fill="both")
    
    # 处理换课响应
    @sio.on('swap_response')
    def handle_swap_response(data):
        print(f"收到换课响应，数据: {data}")  # 添加调试信息
        
        if data['status'] == 'rejected':
            messagebox.showinfo("换课结果", "对方拒绝了换课申请。")
        elif data['status'] == 'approved':
            messagebox.showinfo("换课结果", "换课申请已批准。")
            
            # 更新数据库中的课程信息
            print("开始更新数据库中的课程信息...")
            if not update_database(data):
                print("数据库更新失败，跳过后续操作")
                return
            print("数据库课程信息更新成功。")
            
            # 更新内存中的课表
            print("开始更新内存中的课表...")
            if not update_in_memory_timetable(data):
                print("内存课表更新失败，跳过后续操作")
                return
            print("内存课表更新成功。")
            
            # 保存课表数据到文件
            print("开始保存课表数据到文件...")
            if not save_timetable_to_file():
                print("课表数据保存到文件失败，跳过后续操作")
                return
            print("课表数据保存到文件成功。")
            
            # 刷新界面
            print("开始刷新界面...")
            refresh_teacher_dashboard()
            print("界面刷新成功。")
    
    def update_database(data):
        with db_lock:
            with get_db_connection() as conn:
                c = conn.cursor()
                try:
                    # 更新原课程信息
                    c.execute(
                        "UPDATE schedule SET teacher =?, is_swapped = 1 WHERE class_id =? AND time =? AND week =?",
                        (data['target_teacher'], data['class_id'], data['time'], data['week']))
                    # 更新选择的课程信息
                    c.execute(
                        "UPDATE schedule SET teacher =?, is_swapped = 1 WHERE class_id =? AND time =? AND week =?",
                        (data['request_teacher'], data['target_class_id'], data['target_time'], data['week']))
                    conn.commit()
                    print("数据库课程信息已更新")
                    return True
                except sqlite3.Error as e:
                    print(f"数据库更新失败: {e}")
                    return False
    
    def update_in_memory_timetable(data):
        class_name = data['class_name']
        target_class_name = data['target_class_name']
        print(f"更新前的课表数据: {original_timetable}")  # 添加调试信息
        if class_name in original_timetable and data['time'] in original_timetable[class_name]:
            original_timetable[class_name][data['time']]['teacher'] = data['target_teacher']
        if target_class_name in original_timetable and data['target_time'] in original_timetable[target_class_name]:
            original_timetable[target_class_name][data['target_time']]['teacher'] = data['request_teacher']
        print(f"更新后的课表数据: {original_timetable}")  # 添加调试信息
        return True
    
    def save_timetable_to_file():
        try:
            save_timetable(original_timetable)
            print("课表数据已成功保存到 Sche.txt")
            return True
        except Exception as e:
            print(f"保存课表数据到 Sche.txt 时出错: {e}")
            import traceback
            traceback.print_exc()  # 打印详细的错误堆栈信息
            return False
    
    def refresh_teacher_dashboard():
        teacher_window.destroy()
        teacher_dashboard(user_id, username)
    
    teacher_window.mainloop()


# 管理员工作台
def admin_dashboard(user_id: int, username: str) -> None:
    admin_window = tk.Tk()
    admin_window.title(f"管理员 - {username} 工作台")
    admin_window.geometry("800x600")  # 设置窗口大小
    
    # 创建班级选项卡
    class_tab_control = ttk.Notebook(admin_window)
    
    timetable = read_timetable()
    classes = list(timetable.keys())
    
    if not classes:
        print("未找到班级信息")
        return
    
    # 创建 Treeview 组件
    tree = ttk.Treeview(admin_window, columns=("班级", "时间", "课程", "教师", "状态"), show="headings")
    tree.heading("班级", text="班级")
    tree.heading("时间", text="时间")
    tree.heading("课程", text="课程")
    tree.heading("教师", text="教师")
    tree.heading("状态", text="状态")
    tree.pack(expand=1, fill="both")
    
    for class_name in classes:
        class_tab = ttk.Frame(class_tab_control)
        class_tab_control.add(class_tab, text=class_name)
        
        # 创建周次和日期选项卡
        day_tab_control = ttk.Notebook(class_tab)
        day_tab_control.pack(expand=1, fill="both")
        
        schedule = timetable[class_name]
        days = ["周一", "周二"]  # 可根据实际情况扩展
        for day in days:
            day_tab = ttk.Frame(day_tab_control)
            day_tab_control.add(day_tab, text=day)
            
            row = 0
            for time, course_info in schedule.items():
                if day in time:
                    course = course_info["course"]
                    teacher = course_info["teacher"]
                    with db_lock:
                        with get_db_connection() as conn:
                            c = conn.cursor()
                            c.execute(
                                "SELECT is_swapped FROM schedule WHERE class_id = (SELECT id FROM classes WHERE class_name =?) AND time =? AND course =? AND teacher =?",
                                (class_name, time, course, teacher))
                            result = c.fetchone()
                            if result:
                                is_swapped = result[0]
                                status = "已交换" if is_swapped else "正常"
                            else:
                                status = "正常"
                    
                    time_label = tk.Label(day_tab, text=time)
                    time_label.grid(row=row, column=0, padx=10, pady=5)
                    
                    course_label = tk.Label(day_tab, text=course)
                    course_label.grid(row=row, column=1, padx=10, pady=5)
                    
                    teacher_label = tk.Label(day_tab, text=teacher)
                    teacher_label.grid(row=row, column=2, padx=10, pady=5)
                    
                    status_label = tk.Label(day_tab, text=status)
                    status_label.grid(row=row, column=3, padx=10, pady=5)
                    
                    # 标记交换的课程为红色
                    if is_swapped:
                        time_label.config(fg="red")
                        course_label.config(fg="red")
                        teacher_label.config(fg="red")
                        status_label.config(fg="red")
                    row += 1
    
    class_tab_control.pack(expand=1, fill="both")
    
    # 处理换课批准通知
    @sio.on('admin_notification')
    def handle_admin_notification(data):
        messagebox.showinfo("换课通知",
                            f"{data['time']} {data['course']} 与 {data['target_time']} {data['target_course']} 交换。")
        # 更新表格状态
        with db_lock:
            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute(
                    "SELECT id FROM schedule WHERE class_id = (SELECT id FROM classes WHERE class_name =?) AND time =? AND course =? AND teacher =?",
                    (data['class_name'], data['time'], data['course'], data['teacher']))
                result = c.fetchone()
                if result:
                    schedule_id = result[0]
                    item = tree.get_children()[schedule_id - 1]
                    tree.item(item,
                              values=(data['class_name'], data['time'], data['course'], data['teacher'], "已交换"))
                c.execute(
                    "SELECT id FROM schedule WHERE class_id = (SELECT id FROM classes WHERE class_name =?) AND time =? AND course =? AND teacher =?",
                    (data['target_class_name'], data['target_time'], data['target_course'], data['target_teacher']))
                result = c.fetchone()
                if result:
                    schedule_id = result[0]
                    item = tree.get_children()[schedule_id - 1]
                    tree.item(item, values=(
                        data['target_class_name'], data['target_time'], data['target_course'], data['target_teacher'],
                        "已交换"))
    
    admin_window.mainloop()


# 主窗口
root = tk.Tk()
root.title("课表管理系统 - 登录")
root.geometry("400x300")  # 设置登录窗口大小

label_username = tk.Label(root, text="用户名:")
label_username.pack(pady=10)
entry_username = tk.Entry(root)
entry_username.pack(pady=5)

label_password = tk.Label(root, text="密码:")
label_password.pack(pady=10)
entry_password = tk.Entry(root, show="*")
entry_password.pack(pady=5)

button_login = tk.Button(root, text="登录", command=login)
button_login.pack(pady=20)

# 初始化数据
initialize_data()


# 连接 Socket.IO 服务器
def connect_socketio() -> None:
    global username
    max_retries = 5
    retries = 0
    while retries < max_retries:
        try:
            sio.connect('http://localhost:5000')
            print("已连接到 Socket.IO 服务器")
            break
        except Exception as e:
            retries += 1
            print(f"连接 Socket.IO 服务器失败（第 {retries} 次重试）: {e}")
            if retries == max_retries:
                print("达到最大重试次数，放弃连接。")
                return
        time.sleep(1)  # 每次重试前等待 1 秒
    
    @sio.on('connect')
    def on_connect():
        if not username:
            print("用户名未定义，无法发送用户连接信息")
            return
        time.sleep(1)  # 连接成功后等待 1 秒
        try:
            data = {'username': username}
            print(f"准备发送 user_connect 事件，数据: {data}")
            sio.emit('user_connect', data)
            print(f"已发送用户连接信息，用户名: {username}")
        except Exception as e:
            print(f"发送用户连接信息时出错: {e}")
    
    @sio.on('disconnect')
    def on_disconnect():
        print(f"已断开与 Socket.IO 服务器的连接，用户: {username}")
    
    @sio.on('user_connect_ack')
    def on_user_connect_ack(data):
        if data.get('status') == 'success':
            print(f"用户 {username} 连接信息已成功记录在服务器")
        else:
            print(f"用户 {username} 连接信息记录失败: {data.get('message')}")


# 启动 Socket.IO 连接线程
socketio_thread = threading.Thread(target=connect_socketio)
socketio_thread.start()


# 处理换课请求
@sio.on('swap_request')
def handle_incoming_swap_request(data):
    print(f"收到换课请求，数据: {data}")  # 添加调试信息
    
    def response_window():
        response_win = tk.Toplevel()
        response_win.title("换课请求")
        response_win.geometry("600x300")  # 增大窗口大小
        
        class_name = data.get('class_name', '未知班级')
        time = data.get('time', '未知时间')
        week = data.get('week', '未知周次')
        course = data.get('course', '未知课程')
        request_teacher = data.get('request_teacher', '未知教师')
        selected_time = data.get('selected_time', '未知时间')
        selected_course = data.get('selected_course', '未知课程')
        
        # 更改显示格式
        label_text = f"（{request_teacher}）{week} {time}，{class_name}，{course} <-> （{username}）{week} {selected_time}，{class_name}，{selected_course}"
        label = tk.Label(response_win, text=label_text)
        label.pack(pady=20)
        
        def accept_swap():
            try:
                sio.emit('swap_response', {
                    'request_teacher': data['request_teacher'],
                    'target_teacher': data['target_teacher'],
                    'class_id': data['class_id'],
                    'time': data['time'],
                    'status': 'approved',
                    'target_class_id': data['target_class_id'],
                    'target_time': data['selected_time'],
                    'class_name': class_name,
                    'course': course,
                    'target_class_name': class_name,
                    'target_course': data['selected_course'],
                    'teacher': data['target_teacher'],
                    'target_teacher': data['request_teacher'],
                    'week': week
                })
                sio.emit('admin_notification', {
                    'time': data['time'],
                    'course': course,
                    'target_time': data['selected_time'],
                    'target_course': data['selected_course'],
                    'class_name': class_name,
                    'target_class_name': class_name,
                    'teacher': data['target_teacher'],
                    'target_teacher': data['request_teacher'],
                    'week': week
                })
                response_win.destroy()
            except KeyError as e:
                print(f"处理换课请求时缺少必要的键: {e}")
                messagebox.showerror("错误", f"处理换课请求时缺少必要的键: {e}")
        
        def reject_swap():
            sio.emit('swap_response', {
                'request_teacher': data['request_teacher'],
                'target_teacher': data['target_teacher'],
                'class_id': data['class_id'],
                'time': data['time'],
                'status': 'rejected',
                'class_name': class_name,
                'course': course,
                'week': week
            })
            response_win.destroy()
        
        accept_button = tk.Button(response_win, text="接受", command=accept_swap)
        accept_button.pack(side=tk.LEFT, padx=30)
        reject_button = tk.Button(response_win, text="拒绝", command=reject_swap)
        reject_button.pack(side=tk.RIGHT, padx=30)
    
    messagebox.showinfo("换课请求", "有老师找您换课。")
    response_window()


root.mainloop()
