import sqlite3
import json


# 初始化数据库
def init_database():
    try:
        with sqlite3.connect('timetable.db') as conn:
            c = conn.cursor()
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
            
            # 插入班级数据
            classes = ['一年级一班', '一年级二班']
            for class_name in classes:
                c.execute("INSERT OR IGNORE INTO classes (class_name) VALUES (?)", (class_name,))
            
            # 读取课表数据并插入到 schedule 表
            try:
                with open('Sche.txt', 'r', encoding='utf-8') as file:
                    timetable = json.load(file)
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
            except FileNotFoundError:
                print("未找到课表文件 Sche.txt")
            except json.JSONDecodeError as e:
                print(f"课表文件 Sche.txt 格式错误: {e}")
            
            conn.commit()
            print("数据库初始化成功")
    except Exception as e:
        print(f"数据库初始化出错: {e}")


if __name__ == "__main__":
    init_database()
