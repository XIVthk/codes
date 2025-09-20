import time
import random
from openai import OpenAI
from wxauto import WeChat
from functools import wraps
import json
import os


# ======= 基础设定 =======
class UnknownError(Exception): pass


# 用户数据文件
USER_DATA_FILE = "users.json"


# 尝试从文件加载用户数据，如果不存在则使用默认数据
def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        raise FileNotFoundError


# 保存用户数据到文件
def save_user_data(users_data):
    with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(users_data, f, ensure_ascii=False, indent=4)  # noqa


# 加载用户数据
users = load_user_data()

# 初始化微信和API
wx = WeChat()
at_me = f'@{wx.nickname}'

with open('APIs.txt', 'r') as f:
    api_key = f.read().strip()

with open('HINTs.txt', 'r', encoding='utf-8') as f:
    hint_info = f.read().strip()

client = OpenAI(
    api_key=api_key,
    base_url="https://api.moonshot.cn/v1",
)

# 为每个用户创建独立的对话历史
user_histories = {}
for username in users:
    user_histories[username] = [{
        "role": "system",
        "content": hint_info
    }]

# 全局请求时间控制
last_request_time = 0
MIN_REQUEST_INTERVAL = 1.5  # 最小请求间隔(秒)


# ======= 人类行为模拟函数 =======
def human_like_delay(min_sec=1, max_sec=3):
    """模拟人类操作的不确定延迟"""
    time.sleep(random.uniform(min_sec, max_sec))


def safe_send_message(chat_name, message, at_user=None):
    """
    安全的发送消息函数，添加人类行为模拟
    """
    try:
        # 先切换到目标聊天
        wx.ChatWith(chat_name)
        human_like_delay(1, 2)
        
        # 发送消息
        if at_user and chat_name != at_user:  # 群聊中才@
            wx.SendMsg(message, chat_name, at=at_user)
        else:
            wx.SendMsg(message, chat_name)
        
        # 发送后随机延迟
        human_like_delay(1, 2)
        
        # 切换回文件传输助手继续监听
        wx.ChatWith('文件传输助手')
        human_like_delay(1, 2)
        
        return True
    except Exception as e:
        print(f"发送消息失败: {str(e)}")
        # 重试机制
        time.sleep(10)
        return False


# ======= API错误处理 =======
def handle_api_error(error):
    """处理API错误并返回适当的用户消息"""
    error_str = str(error)
    
    if "429" in error_str or "overload" in error_str.lower():
        return "服务器暂时过载，请稍后再试。"
    elif "401" in error_str or "auth" in error_str.lower():
        return "API密钥错误，请检查配置。"
    elif "quota" in error_str.lower() or "balance" in error_str.lower():
        return "API额度已用完，请充值或联系管理员。"
    elif "content_filter" in error_str.lower():
        return "内容被过滤，请尝试其他问题。"
    else:
        return f"处理请求时出错: {error_str}"


# ======= 权限装饰器 =======
def permission_deco(func):
    @wraps(func)
    def wrapper(username, *args, **kwargs):
        # 检查用户是否存在，如果不存在则创建
        if username not in users:
            users[username] = {
                "register": "user",  # 默认用户权限
                "dialogues": 0,
                "last_reset": time.strftime("%Y-%m-%d")
            }
            # 为新用户创建对话历史
            user_histories[username] = [{
                "role": "system",
                "content": hint_info
            }]
            save_user_data(users)
        
        # 检查权限
        if users[username]["register"] != 'admin' and users[username]["dialogues"] >= 10:
            return "权限不足，今日对话次数已用完，请明日再试或联系管理员。"
        else:
            # 增加对话计数
            users[username]["dialogues"] += 1
            save_user_data(users)
            
            # 调用原始函数
            result = func(username, *args, **kwargs)
            return result
    
    return wrapper


# ======= 询问AI函数 =======
@permission_deco
def ask_ai(username, question: str) -> str:
    # 使用该用户特定的历史记录
    user_history = user_histories[username]
    
    user_history.append({"role": "user", "content": question})
    
    # 全局请求频率控制
    global last_request_time
    current_time = time.time()
    if current_time - last_request_time < MIN_REQUEST_INTERVAL:
        sleep_time = MIN_REQUEST_INTERVAL - (current_time - last_request_time)
        time.sleep(sleep_time)
    last_request_time = time.time()
    
    max_retries = 3
    retry_delay = 2  # 初始重试延迟(s)
    
    for attempt in range(max_retries):
        try:
            completion = client.chat.completions.create(
                model="kimi-k2-0711-preview",
                messages=user_history,
                temperature=0.6,
            )
            
            ai_reply = completion.choices[0].message.content
            user_history.append({"role": "assistant", "content": ai_reply})
            
            return ai_reply
        
        except Exception as e:
            if attempt == max_retries - 1:
                # 最后一次尝试也失败
                return handle_api_error(e)
            
            if "429" in str(e) or "overload" in str(e).lower():
                # 速率限制错误，等待后重试
                print(f"API过载，第{attempt + 1}次重试，等待{retry_delay}秒...")
                time.sleep(retry_delay)
                retry_delay *= 2  # 指数退避策略
            else:
                # 其他错误，直接返回错误信息
                return handle_api_error(e)


# ======= 管理命令处理 =======
def handle_admin_command(username, command):
    if users[username]["register"] != "admin":
        return "权限不足，需要管理员权限。"
    
    parts = command.split()
    if parts[0] == "#exit":
        return "EXIT_PROGRAM"
    
    if len(parts) < 2:
        return "无效的管理命令。使用格式: #command [参数]"
    
    cmd = parts[0]
    target_user = parts[1]
    
    if cmd == "#adduser" and target_user not in users:
        users[target_user] = {
            "register": "user",
            "dialogues": 0,
            "last_reset": time.strftime("%Y-%m-%d")
        }
        user_histories[target_user] = [{
            "role": "system",
            "content": hint_info
        }]
        save_user_data(users)
        return f"已添加用户 {target_user}。"
    
    elif cmd == "#setadmin" and target_user in users:
        users[target_user]["register"] = "admin"
        save_user_data(users)
        return f"已将 {target_user} 设置为管理员。"
    
    elif cmd == "#reset" and target_user in users:
        users[target_user]["dialogues"] = 0
        save_user_data(users)
        return f"已重置 {target_user} 的对话计数。"
    
    elif cmd == "#status" and target_user in users:
        return f"用户 {target_user}: 权限={users[target_user]['register']}, 对话数={users[target_user]['dialogues']}"
    
    else:
        return "无效的管理命令或用户不存在。"


# ======= 消息检查函数 =======
def check_new_message():
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
        
        wx.ChatWith('文件传输助手')


# ======= 主循环 =======
print("Listening...")

wx.ChatWith('文件传输助手')
running = True

while running:
    try:
        if msgs := check_new_message():
            match len(msgs):
                case 2:
                    chat = None
                    sender, content = msgs
                case 3:
                    chat, sender, content = msgs
                case _:
                    raise UnknownError
            
            # 处理管理命令(以#开头)
            if content.startswith("#"):
                response = handle_admin_command(sender, content)
                
                # 检查是否是退出命令
                if response == "EXIT_PROGRAM":
                    print("收到管理员退出指令，程序将退出...")
                    running = False
                    break
                
                if chat:
                    safe_send_message(chat, response, sender)
                else:
                    safe_send_message(sender, response)
                continue
            
            # ======= 处理普通对话 =======
            if chat:
                if at_me in content:
                    # 从内容中移除@标记
                    clean_content = content.replace(at_me, "").strip()
                    if clean_content:
                        aire = ask_ai(sender, clean_content)
                        safe_send_message(chat, aire, sender)
            else:
                aire = ask_ai(sender, content)
                safe_send_message(sender, aire)
            
        
        wx.ChatWith('文件传输助手')
        # 添加短暂延迟避免过高CPU占用
        time.sleep(0.5)
    
    except KeyboardInterrupt:
        print("\n程序已手动停止。")
        break
    except Exception as e:
        print(f"发生错误: {str(e)}")
        wx.ChatWith('文件传输助手')
        time.sleep(5)

print("程序已正常退出。")