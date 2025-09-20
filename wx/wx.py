from wxauto import WeChat

wx = WeChat()
groups = []  # Groups to send
hints = ['SYS', 'Time', 'Self']
with open('GroupNames.txt', 'r', encoding='utf-8') as file:  # read file
    for lines in file:
        groups.append(line := lines.rstrip('\n'))
wx.AddListenChat((listen := groups.pop(0)))  # ListenChat = groups[0], groups.pop(0)

while True:  # main code
    get_msg = wx.GetListenMessage()  # get message from listen
    if get_msg:  # if get a message
        msg = list(get_msg.values())[0]  # get_msg: dict, msg: list
        for index in msg:  # check
            if listen in index:  # is listen's message?
                msg = index  # msg = listen's message
        if not msg[0][0] in hints:  # check system / time / self message
            for group in groups:
                wx.SendMsg(msg, group)  # send message