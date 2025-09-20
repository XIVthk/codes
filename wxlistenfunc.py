from wxauto import WeChat

wx = WeChat()

def check_new_message() -> tuple[str, str] | tuple[str, str, str]:
    """
    检查微信的新消息。
    """
    if wx.CheckNewMessage():
        next_msg = wx.GetNextNewMessage()
            
        for chat_name, messages in next_msg.items():
            for message in messages:
                sender = message[0]
                content = message[1]
                if sender == chat_name:
                    return sender, content
                else:
                    return chat_name, sender, content
