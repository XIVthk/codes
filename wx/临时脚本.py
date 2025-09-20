from wxauto import WeChat

wx = WeChat()
print('正在监听。')
hints = ['SYS', 'Time', 'Self']

while True:
    if wx.CheckNewMessage():
        get_next_msg = wx.GetNextNewMessage()
        while True:
            if not (who := list(get_next_msg.values())[0][0][0]) in hints:
                msg = list(get_next_msg.values())[0][0][1]
                break
            else:
                list(get_next_msg.values())[0].pop(0)
        who = list(get_next_msg.values())[0][0][0]
        if not 'q' in msg:
            wx.SendMsg('[Auto Reply]我暂时没有时间，如有急事请发送‘q’，我会尽快处理。', who)
            print('[弱提醒]', who, '发来了一条消息，已自动回复。')
        else:
            wx.SendMsg('[Auto Reply]请稍等，我会尽快处理。', who)
            print('[强提醒]', who, '找你有急事，已自动回复，请快速处理。')