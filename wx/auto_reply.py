from wxauto import WeChat

wx = WeChat()
whom_dict = {}
tup = []
get = []
reply = []
hints = ['SYS', 'Time', 'Self']
with open('AutoReply.txt', 'r', encoding='utf-8') as file:
    for lines in file:
        tup.append(lines.rstrip('\n'))
    for tup_str in tup:
        a, b = tup_str.split('-')
        get.append(a)
        reply.append(b)


def make_string(_keywords: list[str]):
    _str = '您具体想咨询什么问题？（请键入序号）\n'
    for ind, kwd in enumerate(_keywords):
        _str += f'{ind + 1}. 关于 {kwd} 的问题\n'
    return _str
    

while True:
    keywords = []
    temp_list = []
    if wx.CheckNewMessage():
        get_next_msg = wx.GetNextNewMessage()
        while True:
            if not (who := list(get_next_msg.values())[0][0][0]) in hints:
                msg = list(get_next_msg.values())[0][0][1]
                break
            else:
                list(get_next_msg.values())[0].pop(0)
        if who in whom_dict:
            if (intmsg := int(msg)) < len(whom_dict[who]):
                wx.SendMsg(reply[get.index(whom_dict[who][intmsg - 1])], who)
            else:
                wx.SendMsg('您输入的数字不在列表中哦。')
                del whom_dict[who]
        else:
            for index, keyword in enumerate(get):
                if keyword in msg:
                    keywords.append(index)
            if len(keywords) == 1:
                wx.SendMsg(reply[keywords[0]], who)
            elif len(keywords) == 0:
                wx.SendMsg(make_string(get))
            else:
                for index in keywords:
                    temp_list.append(get[index])
                wx.SendMsg(make_string(temp_list))
                whom_dict[who] = temp_list