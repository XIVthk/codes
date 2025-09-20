from tkinter import *
from random import choice

class RandomChoice:
    def __init__(self):
        self.root = Tk()
        self.root.geometry('300x800')
        self.root.title('RandomChoice')
        self.user_lst = []

        self.get_from_user = Entry(self.root, font=('SourceHanSansSC-Bold', 15))
        self.get_from_user.pack(pady=10)

        self.add_button = Button(self.root, text="添加至列表", command=self.add_to_list, font=('SourceHanSansSC-Bold', 15))
        self.add_button.pack(pady=5)

        self.list_label = Label(self.root, text="当前列表: []", font=('SourceHanSansSC-Bold', 15))
        self.list_label.pack(pady=5)

        self.choose_button = Button(self.root, text="随机选择", command=self.choose_randomly, font=('SourceHanSansSC-Bold', 15))
        self.choose_button.pack(pady=5)
        
        self.delete_button = Button(self.root, text="清空列表", command=self.delete_list, font=('SourceHanSansSC-Bold', 15))
        self.delete_button.pack(pady=6)

        self.result_label = Label(self.root, text="", font=('SourceHanSansSC-Bold', 15))
        self.result_label.pack(pady=10)

        self.root.mainloop()

    def add_to_list(self):
        user_input = self.get_from_user.get()
        if user_input:
            self.user_lst.append(user_input)
            self.get_from_user.delete(0, END)
            list_text = "当前列表:\n" + "\n".join(self.user_lst)
            self.list_label.config(text=list_text)
        else:
            self.result_label.config(text="请输入些东西!", fg="red")
    
    
    def delete_list(self):
        self.user_lst.clear()
        list_text = "当前列表: []"
        self.list_label.config(text=list_text)

    def choose_randomly(self):
        if self.user_lst:
            chosen = choice(self.user_lst)
            self.result_label.config(text=f"选择: {chosen}", fg="black")
        else:
            self.result_label.config(text="列表是空的!", fg="red")

if __name__ == "__main__":
    random_choice = RandomChoice()