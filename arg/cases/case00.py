# cases/case00.py
import time
import json
import os

class Case:
    def __init__(self, terminal):
        self.terminal = terminal
        self.step = 0
        self.player_name = ""
        self.cwd = "/home"
        self.seed = self._calculate_seed()
        self.fs = self.build_fs()
        self.questions_answered = {}
        self.questions = [
            ("q1", "死者的死因是？", "窒息"),
            ("q2", "凶手的名字是？", "李四"),
            ("q3", "凶手的幸运数字是？", "7"),
            ("q4", "案发地点是？", "仓库"),
            ("q5", "凶器是？", "绳子")
        ]
        self.start_time = None
        self.questions_windows = []
        self.quack_triggered = False
    
    def _calculate_seed(self):
        timestamp = int(time.strftime("%Y%m%d%H%M%S"))
        seed = timestamp // 315 * 1.4 * 1.9
        seed = int(seed)
        
        # 保存到 cases/seed.json
        seed_file = os.path.join(os.path.dirname(__file__), 'seed.json')
        try:
            with open(seed_file, 'w') as f:
                json.dump({'seed': seed, 'timestamp': timestamp}, f)
        except:
            pass
        
        return seed
    
    def build_fs(self):
        return {
            "/": {
                "home": {
                    "teach.exe": {
                        "function": self.teach,
                        "timestamp": "2026-06-30 14:00:00"
                    }
                },
                "case00": {
                    "evidence": {
                        "2026": {}
                    }
                }
            }
        }
    
    def teach(self, args, flags):
        """teach.exe 的执行逻辑"""
        if "-a" in flags or "--admin" in flags:
            import os
            username = os.getlogin()
            path = f"C:/Users/{username}/Documents/case00_key.txt"
            self.terminal.subterm_bg(path)
            self._generate_arg_file(username)
            return "权限提升成功。已解锁隐藏路径。"
        else:
            return "This is a teaching executable file.\nUsage: teach.exe --admin"
    
    def _generate_arg_file(self, username):
        """在用户 Documents 目录生成 ARG 文件"""
        docs_path = f"C:/Users/{username}/Documents"
        try:
            os.makedirs(docs_path, exist_ok=True)
            with open(f"{docs_path}/case00_key.txt", 'w') as f:
                f.write(f"case00_seed: {self.seed}\n")
                f.write("password: Quack_2026\n")
                f.write("Hint: Use 'cd /case00/evidence/2026' in the game.\n")
        except:
            pass
    
    def call_quack(self):
        """解锁后执行"""
        if self.quack_triggered:
            return
        self.quack_triggered = True
        
        self.terminal.create_window(
            name='quack_reward',
            title='Quack',
            geometry='300x150',
            widget_type='label',
            text='[Quack +1]'
        )
        self.terminal.show_window('quack_reward')
    
    def on_start(self):
        self.start_time = time.time()
        
        # ★ 1. 先创建 subterm 窗口（但先不显示）
        self.terminal.create_window(
            name='subterm',
            title='System "pause" - DUCK',
            geometry='600x250+820+30',
            widget_type='text'
        )
        # ★ 2. 强制刷新窗口内容
        subterm_window = self.terminal.window_manager.get_window('subterm')
        if subterm_window:
            subterm_window.update_idletasks()
        # ★ 3. 再显示窗口
        self.terminal.show_window('subterm')
        
        # 设置加密目录
        self.terminal.vfs.set_metadata(
            "/case00/evidence/2026",
            {
                "status": "enc",
                "password": "Quack_2026",
                "callback": self.call_quack
            }
        )
        
        self.terminal.out("=" * 50)
        self.terminal.out(" 案件 #00 - 新手教程")
        self.terminal.out("=" * 50)
        self.terminal.out("\n[SYSTEM] 正在加载案件...")
        self.terminal.out("[SYSTEM] 你好，探员。")
        
        self.step = 0
        self._teach_step_1()
    
    def _teach_step_1(self):
        """教学步骤 1：ls"""
        self.terminal.subterm("鸭鸭: 嘿！新手！我是橡胶鸭，你的指引者。")
        self.terminal.subterm("鸭鸭: 让我们从最简单的命令开始。")
        self.terminal.subterm("鸭鸭: 输入 <b>ls</b> 看看当前目录有什么。")
        self.step = 1
        self.terminal.get_input(self._teach_handler)
    
    def _teach_handler(self, cmd):
        """教学命令处理器"""
        # 先执行命令
        self.terminal.handle_input(cmd)
        
        if self.step == 1:
            if cmd.strip().lower() == "ls":
                self.terminal.subterm("鸭鸭: 干得漂亮！你看到了 teach.exe。")
                self.terminal.subterm("鸭鸭: 现在试试 <b>pwd</b> 看看你在哪里。")
                self.step = 2
                self.terminal.get_input(self._teach_handler)
            else:
                self.terminal.subterm("鸭鸭: 输入 <b>ls</b> 看看目录内容。")
                self.terminal.get_input(self._teach_handler)
        
        elif self.step == 2:
            if cmd.strip().lower() == "pwd":
                self.terminal.subterm("鸭鸭: 对！你在 /home。")
                self.terminal.subterm("鸭鸭: 接下来试试 <b>cd /</b> 回到根目录。")
                self.step = 3
                self.terminal.get_input(self._teach_handler)
            else:
                self.terminal.subterm("鸭鸭: 输入 <b>pwd</b> 查看当前路径。")
                self.terminal.get_input(self._teach_handler)
        
        elif self.step == 3:
            if cmd.strip().lower() == "cd /":
                self.terminal.subterm("鸭鸭: 好！你到根目录了。")
                self.terminal.subterm("鸭鸭: 现在试试 <b>ls</b> 看看根目录有什么。")
                self.step = 4
                self.terminal.get_input(self._teach_handler)
            else:
                self.terminal.subterm("鸭鸭: 输入 <b>cd /</b> 回到根目录。")
                self.terminal.get_input(self._teach_handler)
        
        elif self.step == 4:
            if cmd.strip().lower() == "ls":
                self.terminal.subterm("鸭鸭: 看到了吗？有个 case00 目录。")
                self.terminal.subterm("鸭鸭: 试试 <b>cd case00</b> 进去。")
                self.step = 5
                self.terminal.get_input(self._teach_handler)
            else:
                self.terminal.subterm("鸭鸭: 输入 <b>ls</b> 看看根目录。")
                self.terminal.get_input(self._teach_handler)
        
        elif self.step == 5:
            if cmd.strip().lower() == "cd case00":
                self.terminal.subterm("鸭鸭: 进去了！")
                self.terminal.subterm("鸭鸭: 现在试试 <b>open teach.exe</b> 看看。")
                self.step = 6
                self.terminal.get_input(self._teach_handler)
            else:
                self.terminal.subterm("鸭鸭: 输入 <b>cd case00</b> 进入目录。")
                self.terminal.get_input(self._teach_handler)
        
        elif self.step == 6:
            if cmd.strip().lower() == "open teach.exe":
                self.terminal.subterm("鸭鸭: 这只是个教学文件。")
                self.terminal.subterm("鸭鸭: 用 <b>execute teach.exe</b> 运行它。")
                self.step = 7
                self.terminal.get_input(self._teach_handler)
            else:
                self.terminal.subterm("鸭鸭: 输入 <b>open teach.exe</b> 查看内容。")
                self.terminal.get_input(self._teach_handler)
        
        elif self.step == 7:
            if cmd.strip().lower() == "execute teach.exe":
                self.terminal.subterm("鸭鸭: 很好！现在你学会了 5 个基础命令。")
                self.terminal.subterm("鸭鸭: 接下来，尝试破解一下这个案件。")
                self._start_hack_sequence()
            else:
                self.terminal.subterm("鸭鸭: 输入 <b>execute teach.exe</b> 运行它。")
                self.terminal.get_input(self._teach_handler)
    
    def _start_hack_sequence(self):
        """黑客动画序列"""
        self.step = 100
        
        # 显示伪代码滚动
        code_lines = [
            "duck@send case00/",
            "int i = 0;",
            "for(auto& f : files) {",
            "    auto sen = decrypt(f);",
            "    connect(COMPUTER);",
            "    if(sen.valid()) {",
            "        upload(sen);",
            "        i++;",
            "    }",
            "}",
            "for(int j = 0; j < i; j++) {",
            "    auto result = analyze(case00[j]);",
            "    if(result.confidence > 0.95) {",
            "        break;",
            "    }",
            "}",
            "execve(\"/bin/bash\", {\"-c\", \"rm -rf /tmp/case00_cache\"}, NULL);",
            "connect(TERMINAL);",
            "wait_for_input();"
        ]
        
        for line in code_lines:
            self.terminal.subterm(f"<i><color=grey>{line}</color></i>")
        
        # 显示进度条窗口
        self.terminal.create_window(
            name='progress',
            title='正在接收...',
            geometry='400x120',
            widget_type='progress',
            label='正在接收：case00/'
        )
        self.terminal.show_window('progress')
        
        # 进度条跑完后启动破案
        self.terminal.window_manager.root.after(3000, self._start_questions)
    
    def _start_questions(self):
        """启动多窗口问答"""
        self.terminal.close_window('progress')
        self.terminal.subterm("鸭鸭: 开始破案吧！回答所有问题即可结案。")
        
        # 弹出所有问题窗口
        for q_id, question, answer in self.questions:
            self._create_question_window(q_id, question, answer)
    
    def _create_question_window(self, q_id, question, answer):
        """创建单个问题窗口"""
        def on_submit(value):
            if value.strip() == answer:
                self.questions_answered[q_id] = True
                self.terminal.close_window(f'question_{q_id}')
                self._check_all_answered()
            else:
                entry_data = self.terminal.window_manager.get_widget(f'question_{q_id}')
                if entry_data and 'entry' in entry_data:
                    entry_data['entry'].delete(0, 'end')
        
        self.terminal.create_window(
            name=f'question_{q_id}',
            title='调查',
            geometry='400x150',
            widget_type='entry',
            label=question,
            button_text='确认',
            callback=on_submit
        )
        self.terminal.show_window(f'question_{q_id}')
        self.questions_windows.append(f'question_{q_id}')
    
    def _check_all_answered(self):
        """检查是否所有问题都已回答"""
        if len(self.questions_answered) == len(self.questions):
            self._show_summary()
    
    def _show_summary(self):
        """显示汇总窗口"""
        # 关闭所有问题窗口
        for win_name in self.questions_windows:
            self.terminal.close_window(win_name)
        self.questions_windows = []
        
        # 构建汇总文本
        summary_lines = []
        q_map = {q_id: (q, a) for q_id, q, a in self.questions}
        for q_id in self.questions_answered:
            q, a = q_map[q_id]
            summary_lines.append(f"「{q}」 <u>{a}</u>")
        
        summary_text = "\n".join(summary_lines)
        
        # 显示汇总窗口
        self.terminal.create_window(
            name='summary',
            title='结案报告',
            geometry='500x300',
            widget_type='label',
            text=summary_text
        )
        self.terminal.show_window('summary')
        
        # 鸭鸭说话（取焦）
        elapsed = int(time.time() - self.start_time)
        minutes = elapsed // 60
        seconds = elapsed % 60
        
        self.terminal.subterm(f"鸭鸭: 恭喜！你用时 {minutes} 分 {seconds} 秒……")
        self.terminal.subterm("鸭鸭: 破获了已经破获了三年的案件。")
        self.terminal.subterm("鸭鸭: 你可以继续探索文件系统。")
        
        self.terminal.window_manager.focus_window('subterm')
        
        # 进入自由探索模式
        self.step = 200
        self.terminal.out("\n[SYSTEM] 案件 #00 完成。")
        self.terminal.out("\n你可以继续探索文件系统，或输入 <b>exit</b> 回到主菜单。")
        self.terminal.get_input(self.on_free_mode)
    
    def on_free_mode(self, cmd):
        """自由探索模式"""
        if cmd.strip().lower() == "exit":
            self.terminal.out("\n[SYSTEM] 退出案件...")
            self.terminal.running = False
            return
        
        self.terminal.handle_input(cmd)
        self.terminal.get_input(self.on_free_mode)
    
    def handle_command(self, cmd, args, flags):
        return None