import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import showinfo, showerror, askyesno
from pathlib import Path
import random as r
from uuid import uuid4

from sqlalchemy import label

START_WIN = 0
GAME = 1

class RCCS:
    # Randomly Choose Card System
    """
    用户行为：
    rccs = RCCS(...)
    card = rccs.draw()  # card: tuple(str, uuid4)
    ...
    rccs.update(id=card[1], status=False)
    """

    READY_TO_USE = 0    # 卡牌未被抽取，READY
    USING = 1           # 卡牌正在被使用，IN_HAND
    BIN = 2             # 卡牌在回收站内，RECYCLED
    USED = 3            # 卡牌已被使用，PLAYED
    DELETED = 4         # 卡牌已被永久删除，DELETED (从BIN中删除的卡牌才会有此状态)

    def __init__(self, card_pool: str | Path, sep: str = "\n", bin_size: int = 3):
        if isinstance(card_pool, str):
            card_pool = Path(card_pool)
        if not isinstance(card_pool, Path) or not card_pool.exists():
            raise ValueError("Card pool must be a valid file path.")
        self.card_pool = card_pool
        with open(self.card_pool, "r", encoding="utf-8") as f:
            self.cards: list = f.read().split(sep)
        
        self.cards = list(filter(lambda x: x.strip(), self.cards))  # 去除空行
        self.cards = list(set(self.cards))  # 去除重复卡牌
        self.cards_without_deleted = self.cards.copy()  # 保存未删除卡牌的初始列表
        self.used_cards: list = []  # 已被使用的卡牌列表，用于存储已被使用的卡牌内容
        self.bin: list[tuple[uuid4, str]] = []  # 回收站，用于存储回收站内的卡牌内容，每个元素为元组(唯一 ID, 卡牌内容)
        self.binrm = None # 上一个被完全删除的卡牌
        self.bin_size = bin_size  # 回收站容量限制

        # self.cards 在以下不允许再被使用，但并未真正删除，以便后续可能的重置操作
        # del self.cards
        
        self.card_data = {uuid4(): (self.READY_TO_USE, card) for card in self.cards}  # 卡牌状态字典，键为唯一 ID，值为元组(status: bool, card: str)
        # self.card_data 内无 USED 状态的卡牌，已被移入 self.used_cards
        # self.card_data 内无 BIN 状态的卡牌，已被移入 self.bin
        # self.card_data 初始时所有卡牌均为 READY_TO_USE 状态，可以包含 USING 状态的卡牌
    
    def update(self, id, status: int = USED):
        """从外部接收卡牌状态并更新
        参数:
            id: 卡牌的唯一 ID
            status: 卡牌的新状态，默认值为 self.USED
        """
        for uid, (_, card) in self.card_data.items():
            if uid == id:
                self.card_data[uid] = (status, card)
                break
        self._update()

    def _update(self):
        """
        删除 card_data 中 status 为 USED 的卡牌，将其转入 self.used_cards
        删除 card_data 中 status 为 BIN 的卡牌，将其转入 self.bin
        该方法在每次 update 后自动调用
        """
        self.used_cards.extend([card for uid, (status, card) in self.card_data.items() if status == self.USED])
        self.bin.extend([(uid, card) for uid, (status, card) in self.card_data.items() if status == self.BIN])
        self.card_data = {uid: (status, card) for uid, (status, card) in self.card_data.items() if status != self.USED and status != self.BIN}
        if len(self.bin) > self.bin_size:
            self.binrm = self.bin[abs(len(self.bin) - self.bin_size) - 1][1]  # 记录被删除的卡牌
            # 超出回收站容量，删除最早进入回收站的卡牌
            self.bin = self.bin[-self.bin_size:]

    def getbin(self) -> tuple[list[tuple[uuid4, str]], str | None]:
        return self.bin, self.binrm
    
    def rerm(self):
        self.binrm = None

    def draw(self) -> tuple[str, uuid4]:
        """抽取一张未被抽取的卡牌，返回卡牌内容和唯一 ID"""
        available_cards = [(card, uid) for uid, (status, card) in self.card_data.items() if status == self.READY_TO_USE]
        if not available_cards:
            return None, None
        card, uid = r.choice(available_cards)
        self.card_data[uid] = (self.USING, card)
        return card, uid

    def is_empty(self) -> bool:
        """判断卡牌池是否为空"""
        return all(status != self.READY_TO_USE for status, card in self.card_data.values())


class Game:
    def __init__(self, root, card_pool: str | Path):
        self.root = root
        self.fullscreen = False
        self.root.title("Once Upon a Time")
        self.root.attributes("-fullscreen", self.fullscreen)
        self.root.bind("<Escape>", lambda e: self.toggle_fullscreen() if self.fullscreen else exit(0))
        self.root.bind("<F11>", self.toggle_fullscreen)

        self.status = START_WIN
        self.rccs = RCCS(card_pool)
        
        self.font = "Consolas"
        self.cards_now: dict[uuid4, str] = {}  # 当前在手卡牌的唯一 ID 字典，键为唯一 ID，值为卡牌内容
        self.card_widgets = {}  # 当前在手卡牌的 Label 组件字典，键为唯一 ID，值为 Label 组件(和卡牌内容)
        self.card_num = None

        self.start_win()

    def toggle_fullscreen(self, event=None):
        self.fullscreen = not self.fullscreen
        self.root.attributes("-fullscreen", self.fullscreen)
    
    def start_win(self):
        self.root.geometry("400x350")
        self.start_win_frame = tk.Frame(self.root)
        self.start_win_frame.pack()
        tk.Label(self.start_win_frame, text="从前从前", font=(self.font, 24)).pack(pady=20)
        tk.Button(self.start_win_frame, text="单人游戏", font=(self.font, 18), command=self.start_game).pack(pady=10)
        tk.Button(self.start_win_frame, text="多人游戏", font=(self.font, 18), command=self.multiplayer_game).pack(pady=10)
        tk.Button(self.start_win_frame, text="退出游戏", font=(self.font, 18), command=lambda: exit(0)).pack(pady=10)

    def multiplayer_game(self):
        showinfo("多人游戏", "多人游戏暂未实现")

    def start_game(self):
        if not self.fullscreen: self.toggle_fullscreen()
        self.status = GAME
        self.start_win_frame.destroy()
        self.root.geometry("800x600")
        self.game_win()

    def game_win(self):
        self.game_frame = tk.LabelFrame(self.root, text="输入区域", font=(self.font, 14))
        self.game_frame.pack(fill=tk.BOTH, padx=10, pady=10, side=tk.LEFT, expand=True)
        self.input_text = tk.Text(self.game_frame, font=(self.font, 14), wrap=tk.WORD)
        self.input_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 右半部分分栏，right_frame 包含 tool_frame 和 card_frame，是父容器
        self.right_frame = tk.Frame(self.root)
        self.right_frame.pack(fill=tk.BOTH, side=tk.RIGHT, expand=True)

        self.tool_frame = tk.LabelFrame(self.right_frame, text="工具区域", font=(self.font, 14), height=270)
        self.tool_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        self.tool_frame.pack_propagate(False)  # 防止子组件改变父组件大小
        self.tool_widgets()

        self.card_frame = tk.LabelFrame(self.right_frame, text="卡牌区域", font=(self.font, 14))
        self.card_frame.pack(fill=tk.BOTH, padx=10, pady=(5, 10), expand=True)
        self.card_init()

        self.bin_frame = tk.LabelFrame(self.right_frame, text="回收站", font=(self.font, 14), height=300)
        self.bin_frame.pack(fill=tk.X, padx=10, pady=(5, 10))
        self.bin_frame.pack_propagate(False)  # 防止子组件改变父组件大小

    def tool_widgets(self):
        pass
    
    def card_init(self):
        self.ask_level = tk.Toplevel(self.root)
        self.ask_level.geometry("300x150")
        self.ask_level.focus()
        self.ask_level.grab_set()
        tk.Label(self.ask_level, text="每次出现的卡牌数量：", font=(self.font, 14)).pack(pady=10)
        self.card_num_entry = tk.Entry(self.ask_level, font=(self.font, 14))
        self.card_num_entry.pack(pady=10)
        tk.Button(self.ask_level, text="确认", font=(self.font, 14), command=lambda: self.confirm_asklevel()).pack(pady=10)
    
    def confirm_asklevel(self):
        level = self.card_num_entry.get()
        try:
            level = int(level)
            if level <= 0:
                raise ValueError
        except ValueError:
            showerror("Err", "请输入一个正整数")
            return
        self.card_num = level
        self.ask_level.destroy()
        self.draw_cards()

    def draw_cards(self, num: int = None, update_occure: bool = False):
        if num is None: num = self.card_num
        else: update_occure = True

        for _ in range(num):
            card, uid = self.rccs.draw()
            if card is None:  # 卡牌池已空，静默
                break
            self.cards_now[uid] = card
            
            card_label = tk.Label(
                self.card_frame,
                text=card,
                font=(self.font, 14, "italic"),   # 斜体
                relief="groove",                  # 边框
                borderwidth=2,                    # 边框粗细
                bg="lightcyan",                   # 背景
                fg="navy",                        # 文字
                padx=15,                          # 左右内边距
                pady=8,                           # 上下内边距
                width=15,                         # 固定宽度
                anchor="center",                  # 文字居中
                cursor="hand2"                    # 鼠标悬停时的光标
            )

            self.card_widgets[uid] = (card_label, card)

            card_label.bind("<Enter>", 
                       lambda e, lbl=card_label: lbl.config(relief="raised"))
            card_label.bind("<Leave>", 
                       lambda e, lbl=card_label: lbl.config(relief="groove"))  
            card_label.bind("<Button-3>", 
                       lambda e, uid=uid: self.intobin(uid))

            card_label.pack(pady=8)
        if not update_occure:
            self.match_text_and_cards()
            self.update()
    
    def intobin(self, uid: uuid4) -> bool:
        confirm = askyesno("提示", "是否将这张卡牌放入回收站？")
        if not confirm: return False
        self.rccs.update(id=uid, status=RCCS.BIN)

        if uid in self.card_widgets:
            label, _ = self.card_widgets[uid]
            label.destroy()
            del self.card_widgets[uid]
            del self.cards_now[uid]
        
        self.show_bin_cards()
        return True

    def show_bin_cards(self):
        """显示回收站中的卡牌"""
        for widget in self.bin_frame.winfo_children():
            widget.destroy()
        
        bin_cards, binrm = self.rccs.getbin()
        if binrm:
            lbl = tk.Label(
                self.bin_frame,
                text=f"已永久删除卡牌: {binrm}",
                font=(self.font, 12, "italic"),
                fg="red",
                pady=4
            )
            lbl.pack()
            lbl.after(3000, lambda: lbl.destroy())
            self.rccs.rerm()
        
        for uid, card_text in bin_cards:
            if uid in self.card_widgets:
                continue
                
            # 创建回收站样式的卡牌
            bin_label = tk.Label(
                self.bin_frame,
                text=f"BIN: {card_text}",
                font=(self.font, 14, "italic"),
                relief="sunken",
                borderwidth=1,
                bg="#E0E0E0",    # 更灰的背景
                fg="#808080",    # 更灰的文字
                padx=12,
                pady=6,
                width=14,
                anchor="center",
                cursor="hand2"
            )
            
            bin_label.bind("<Enter>", 
                       lambda e, lbl=bin_label: lbl.config(relief="raised"))
            bin_label.bind("<Leave>", 
                       lambda e, lbl=bin_label: lbl.config(relief="sunken"))
            
            bin_label.bind("<Button-3>", 
                        lambda e, u=uid: self.remove_from_bin(u))
            
            bin_label.pack(pady=4)
    
    def remove_from_bin(self, uid: uuid4) -> bool:
        confirm = askyesno("提示", "确认要完全删除这张卡牌？")
        if not confirm: return False
        self.rccs.update(id=uid, status=RCCS.USED)
        self.show_bin_cards()
        return True
    
    def match_text_and_cards(self):
        text = self.input_text.get("1.0", tk.END).strip()
        if not text:
            self.root.after(100, self.match_text_and_cards)  # 这里不能只return，否则无法继续检测输入！
            return
        
        used_uid = []

        for uid, card in self.cards_now.items():
            if card in text:
                start_pos = self.input_text.search(card, "1.0", tk.END)
                if start_pos:
                    line_start = start_pos.split('.')[0]
                    char_start = int(start_pos.split('.')[1])
                    end_pos = f"{line_start}.{char_start + len(card)}"
                    
                    self.input_text.tag_add("lightblue", start_pos, end_pos)
                    self.input_text.tag_config("lightblue", background="lightblue", font=(self.font, 14, "bold italic"))
                    
                    used_uid.append(uid)
        
        for uid in used_uid:  # 不能在for内del self.cards_now[uid]，会导致迭代器错误！
            # 标记卡牌为已使用
            self.rccs.update(id=uid, status=RCCS.USED)
            self.mark_card_as_used(uid)
        
        self.root.after(100, self.match_text_and_cards)
    
    def mark_card_as_used(self, uid):
        if uid in self.card_widgets:
            label, card_text = self.card_widgets[uid]
            
            label.config(
                text=card_text,
                fg="gray",            # 文字变灰
                bg="lightgray",       # 背景变灰
                relief="sunken",      # 凹下去
                font=(self.font, 14, "italic overstrike")
            )
            
            label.unbind("<Enter>")
            label.unbind("<Leave>")
            
            if uid in self.cards_now:
                del self.cards_now[uid]
            label.after(5000, label.destroy)  # 5秒后销毁
    
    def update(self):
        # 如果cards_now数量与card_num相差>=1，继续抽卡直到相等
        if self.rccs.is_empty() and not self.cards_now:  # 卡牌池已空且无已用卡牌
            showinfo("提示", "卡牌已抽取完毕")
            # 先这样处理吧
            return
        if self.rccs.is_empty():  # 卡牌池已空但仍有未用卡牌
            pass  # 继续迭代检查，但暂时静默，等待用户使用完手牌
        elif (sub := abs(len(self.cards_now) - self.card_num)) >= 1:
            self.draw_cards(sub, update_occure=True)  # 补充手牌至card_num
        self.root.after(100, self.update)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    game = Game(root, "cards.txt")
    game.run()
