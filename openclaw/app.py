# app.py
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import json
import os
import threading
import uuid
import time
from datetime import datetime, timedelta
import traceback

# 获取项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 配置
API_KEY = os.environ.get("API_KEY")
if not API_KEY:
    raise ValueError("请设置环境变量 API_KEY")

BASE_URL = "https://api.siliconflow.cn/v1"
MODEL = "deepseek-ai/DeepSeek-V3"
DEBUG = True
SECRET_KEY = "myclaw-secret-key"

# 使用绝对路径
CHATS_DIR = os.path.join(BASE_DIR, "data/chats")
MEMORIES_DIR = os.path.join(BASE_DIR, "data/memories")
BOTS_FILE = os.path.join(BASE_DIR, "bots.json")

from core.ai import AI
from core.memory import Memory
from tools.parser import handle_tool_calls, tools_definition

app = Flask(__name__)
CORS(app)
app.secret_key = SECRET_KEY

# 确保目录存在
os.makedirs(MEMORIES_DIR, exist_ok=True)
os.makedirs(CHATS_DIR, exist_ok=True)

# ==================== 全局工作目录 ====================
# 初始为项目根目录，确保数据路径正确
current_working_dir = BASE_DIR

# ==================== 提醒系统（AI主动说话）====================
reminders = []  # 存储所有提醒
reminder_lock = threading.Lock()

def reminder_worker():
    """后台提醒线程 - 让AI主动说话"""
    while True:
        try:
            now = datetime.now()
            to_remove = []
            
            with reminder_lock:
                for reminder in reminders:
                    if reminder['time'] <= now:
                        trigger_ai_reminder(reminder)
                        to_remove.append(reminder)
                
                for r in to_remove:
                    reminders.remove(r)
            
            time.sleep(1)
        except Exception as e:
            print(f"提醒线程错误: {e}")
            time.sleep(5)

def trigger_ai_reminder(reminder):
    """触发AI主动说话提醒"""
    try:
        bot_name = reminder['bot_name']
        chat_id = reminder['chat_id']
        message = reminder['message']
        minutes = reminder['minutes']
        
        chat = load_chat(chat_id)
        bots = load_bots()
        
        if bot_name not in bots:
            print(f"Bot {bot_name} 不存在")
            return
        
        bot_config = bots[bot_name]
        ai = get_ai(bot_name, bot_config)
        
        reminder_prompt = f"""这是你之前主动设定的提醒：
- 时间：{minutes} 分钟后
- 提醒内容：{message}

现在时间到了，请主动提醒用户。可以用友好的语气，可以加一些表情。"""
        
        response = ai.ask(reminder_prompt)
        
        bot_msg = {
            'id': str(uuid.uuid4()),
            'sender': bot_name,
            'content': f"⏰ {response}",
            'time': datetime.now().isoformat(),
            'type': 'bot'
        }
        
        chat['messages'].append(bot_msg)
        chat['updated_at'] = datetime.now().isoformat()
        save_chat(chat_id, chat)
        
        print(f"🤖 {bot_name} 主动提醒: {response[:50]}...")
        
    except Exception as e:
        print(f"触发AI提醒失败: {e}")

def add_ai_reminder(bot_name, chat_id, minutes, message):
    """添加一个让AI主动说话的提醒"""
    reminder_time = datetime.now() + timedelta(minutes=minutes)
    reminder = {
        'id': str(uuid.uuid4()),
        'bot_name': bot_name,
        'chat_id': chat_id,
        'time': reminder_time,
        'minutes': minutes,
        'message': message,
        'created_at': datetime.now().isoformat()
    }
    
    with reminder_lock:
        reminders.append(reminder)
    
    reminders.sort(key=lambda x: x['time'])
    return reminder

# 启动提醒线程
reminder_thread = threading.Thread(target=reminder_worker, daemon=True)
reminder_thread.start()

# ==================== 数据管理 ====================
def load_bots():
    if os.path.exists(BOTS_FILE):
        with open(BOTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        save_bots({})
        return {}

def save_bots(bots):
    with open(BOTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(bots, f, ensure_ascii=False, indent=2)

def load_chats():
    chats = []
    if os.path.exists(CHATS_DIR):
        for f in os.listdir(CHATS_DIR):
            if f.endswith('.json'):
                chat_id = f[:-5]
                try:
                    with open(os.path.join(CHATS_DIR, f), 'r', encoding='utf-8') as cf:
                        chat_data = json.load(cf)
                        last_msg = ""
                        if chat_data.get('messages') and len(chat_data['messages']) > 0:
                            last_msg = chat_data['messages'][-1].get('content', '')
                        chats.append({
                            'id': chat_id,
                            'name': chat_data.get('name', chat_id),
                            'type': chat_data.get('type', 'group'),
                            'updated_at': chat_data.get('updated_at', ''),
                            'last_message': last_msg[:50] + ('...' if len(last_msg) > 50 else '')
                        })
                except:
                    continue
    chats.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
    return chats

def save_chat(chat_id, chat_data):
    with open(os.path.join(CHATS_DIR, f"{chat_id}.json"), 'w', encoding='utf-8') as f:
        json.dump(chat_data, f, ensure_ascii=False, indent=2)

def load_chat(chat_id):
    with open(os.path.join(CHATS_DIR, f"{chat_id}.json"), 'r', encoding='utf-8') as f:
        return json.load(f)

# ==================== AI 实例缓存 ====================
ai_instances = {}
memory_instances = {}

def get_ai(bot_name, bot_config):
    key = f"{bot_name}"
    if key not in ai_instances:
        ai_instances[key] = AI(
            system_prompt=bot_config['prompt'],
            api_key=API_KEY,
            base_url=BASE_URL,
            model=MODEL
        )
    return ai_instances[key]

def get_memory(bot_name):
    key = f"{bot_name}"
    if key not in memory_instances:
        memory_instances[key] = Memory(memory_dir=os.path.join(MEMORIES_DIR, bot_name))
    return memory_instances[key]

# ==================== 路由 ====================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chats', methods=['GET'])
def get_chats():
    return jsonify({'success': True, 'chats': load_chats()})

@app.route('/api/chat/<chat_id>', methods=['GET'])
def get_chat(chat_id):
    try:
        return jsonify({'success': True, 'chat': load_chat(chat_id)})
    except:
        return jsonify({'success': False, 'error': '聊天不存在'})

@app.route('/api/chat/new', methods=['POST'])
def new_chat():
    data = request.json
    chat_type = data.get('type', 'group')
    name = data.get('name', '新聊天')
    bot_name = data.get('bot_name')
    
    chat_id = str(uuid.uuid4())[:8]
    chat_data = {
        'id': chat_id,
        'name': name,
        'type': chat_type,
        'bot_name': bot_name,
        'messages': [],
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    save_chat(chat_id, chat_data)
    return jsonify({'success': True, 'chat_id': chat_id})

@app.route('/api/chat/<chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    try:
        chat_file = os.path.join(CHATS_DIR, f"{chat_id}.json")
        if os.path.exists(chat_file):
            os.remove(chat_file)
            return jsonify({'success': True, 'message': '聊天已删除'})
        return jsonify({'success': False, 'error': '聊天不存在'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/bots', methods=['GET'])
def get_bots():
    return jsonify({'success': True, 'bots': load_bots()})

@app.route('/api/bots', methods=['POST'])
def update_bots():
    bots = request.json
    save_bots(bots)
    ai_instances.clear()
    memory_instances.clear()
    return jsonify({'success': True})

# ==================== 工作目录相关 API ====================
@app.route('/api/working-dir', methods=['GET'])
def get_working_dir():
    global current_working_dir
    return jsonify({
        'success': True,
        'path': current_working_dir,
        'home': os.path.expanduser('~'),
        'base': BASE_DIR  # 返回项目根目录供前端参考
    })

@app.route('/api/working-dir', methods=['POST'])
def set_working_dir():
    global current_working_dir
    data = request.json
    new_path = data.get('path', '')
    
    try:
        if not os.path.isabs(new_path):
            new_path = os.path.join(current_working_dir, new_path)
        
        new_path = os.path.normpath(new_path)
        
        if not os.path.exists(new_path):
            return jsonify({'success': False, 'error': '路径不存在'})
        if not os.path.isdir(new_path):
            return jsonify({'success': False, 'error': '不是目录'})
        
        current_working_dir = new_path
        os.chdir(new_path)
        
        return jsonify({'success': True, 'path': current_working_dir})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/working-dir/up', methods=['POST'])
def go_up():
    global current_working_dir
    try:
        parent = os.path.dirname(current_working_dir)
        if parent and parent != current_working_dir:
            current_working_dir = parent
            os.chdir(parent)
            return jsonify({'success': True, 'path': current_working_dir})
        return jsonify({'success': False, 'error': '已经在根目录'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ==================== 文件树 API ====================
@app.route('/api/file-tree', methods=['GET'])
def get_file_tree():
    global current_working_dir
    path = request.args.get('path', current_working_dir)
    show_hidden = request.args.get('show_hidden', 'false').lower() == 'true'
    
    def format_size(size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}TB"
    
    def scan_dir(dir_path, depth=0, max_depth=2):
        if depth > max_depth:
            return {'name': os.path.basename(dir_path), 'type': 'dir', 'children': [], 'has_more': True}
        
        try:
            items = []
            for item in sorted(os.listdir(dir_path)):
                if not show_hidden and item.startswith('.'):
                    continue
                
                full_path = os.path.join(dir_path, item)
                try:
                    if os.path.isdir(full_path):
                        sub_dir = scan_dir(full_path, depth + 1, max_depth)
                        items.append({
                            'name': item,
                            'type': 'dir',
                            'path': full_path,
                            'children': sub_dir['children'],
                            'has_more': sub_dir.get('has_more', False)
                        })
                    else:
                        size = os.path.getsize(full_path)
                        items.append({
                            'name': item,
                            'type': 'file',
                            'path': full_path,
                            'ext': os.path.splitext(item)[1].lower(),
                            'size': size,
                            'size_str': format_size(size)
                        })
                except (PermissionError, OSError):
                    items.append({
                        'name': item,
                        'type': 'unknown',
                        'path': full_path,
                        'error': '无权限'
                    })
            
            return {'name': os.path.basename(dir_path), 'type': 'dir', 'path': dir_path, 'children': items}
        except PermissionError:
            return {'name': os.path.basename(dir_path), 'type': 'dir', 'path': dir_path, 'children': [], 'error': '无权限访问'}
    
    try:
        tree = scan_dir(path)
        return jsonify({
            'success': True,
            'tree': tree,
            'path': path,
            'home': os.path.expanduser('~')
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ==================== 提醒查看 API ====================
@app.route('/api/reminders', methods=['GET'])
def get_reminders():
    with reminder_lock:
        reminder_list = []
        for r in reminders:
            minutes_left = int((r['time'] - datetime.now()).total_seconds() / 60)
            reminder_list.append({
                'id': r['id'],
                'bot_name': r['bot_name'],
                'time': r['time'].isoformat(),
                'message': r['message'],
                'minutes_left': minutes_left
            })
        return jsonify({'success': True, 'reminders': reminder_list})

@app.route('/api/reminders/<reminder_id>', methods=['DELETE'])
def cancel_reminder(reminder_id):
    with reminder_lock:
        global reminders
        reminders = [r for r in reminders if r['id'] != reminder_id]
    return jsonify({'success': True, 'message': '提醒已取消'})

# ==================== 发送消息流式接口 ====================
@app.route('/api/send/stream', methods=['POST'])
def send_message_stream():
    data = request.json
    chat_id = data.get('chat_id')
    message = data.get('message')
    sender = data.get('sender', '你')
    
    def generate():
        global current_working_dir
        
        chat = load_chat(chat_id)
        
        user_msg = {
            'id': str(uuid.uuid4()),
            'sender': sender,
            'content': message,
            'time': datetime.now().isoformat(),
            'type': 'user'
        }
        chat['messages'].append(user_msg)
        chat['updated_at'] = datetime.now().isoformat()
        save_chat(chat_id, chat)
        
        yield f"data: {json.dumps({'type': 'user_message', 'message': user_msg})}\n\n"
        
        bots = load_bots()
        
        if len(bots) == 0:
            yield f"data: {json.dumps({'type': 'error', 'message': '没有可用的Bot'})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            return
        
        if chat['type'] == 'single':
            bot_name = chat.get('bot_name')
            if bot_name and bot_name in bots:
                for chunk in process_bot_reply_stream(bot_name, bots[bot_name], message, chat_id, current_working_dir):
                    yield f"data: {json.dumps(chunk)}\n\n"
        else:
            mentioned_bots = []
            for name in bots:
                if f"@{name}" in message:
                    mentioned_bots.append(name)
            
            if not mentioned_bots:
                mentioned_bots = list(bots.keys())
            
            for name in mentioned_bots:
                for chunk in process_bot_reply_stream(name, bots[name], message, chat_id, current_working_dir):
                    yield f"data: {json.dumps(chunk)}\n\n"
        
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    
    return app.response_class(generate(), mimetype='text/event-stream')

def process_bot_reply_stream(bot_name, bot_config, user_message, chat_id, working_dir):
    ai = get_ai(bot_name, bot_config)
    memory = get_memory(bot_name)
    
    chat = load_chat(chat_id)
    memories = memory.search(user_message)[:3]
    
    # 构建对话历史上下文
    context = ""
    recent_messages = chat['messages'][-6:]
    for msg in recent_messages:
        if msg['type'] == 'user':
            context += f"{msg['sender']}: {msg['content']}\n"
        elif msg['type'] == 'bot':
            context += f"{msg['sender']}: {msg['content']}\n"
    
    # 强制工具调用指令
    tool_instruction = """
【重要规则】
当用户要求执行任何命令（如 cd、dir、python、git 等）时，你必须通过调用提供的工具（如 run_command）来实际执行，不能自己模拟或假装执行。
工具调用会返回真实结果，你只需基于结果回复即可。
如果你需要切换目录，请使用 cd 命令（会被自动识别并更新工作目录）。
"""
    
    full_prompt = tool_instruction + f"""
当前工作目录: {working_dir}

这是最近的对话历史：
{context}

现在用户说：{user_message}
"""
    
    if memories:
        full_prompt += "\n\n相关记忆：\n" + "\n".join(memories)
    
    # 先发送开始标记
    reply_id = str(uuid.uuid4())
    yield {
        'type': 'bot_start',
        'bot_name': bot_name,
        'reply_id': reply_id,
        'time': datetime.now().isoformat()
    }
    
    # 调用 AI（先尝试工具调用）
    result = ai.ask_with_tools(full_prompt, tools_definition)
    
    collected_content = []
    
    if isinstance(result, list):  # 有工具调用
        # 发送工具开始事件（每个工具一个事件）
        for tool_call in result:
            try:
                args = json.loads(tool_call.function.arguments)
            except:
                args = {}
            yield {
                'type': 'tool_start',
                'tool_name': tool_call.function.name,
                'arguments': args,
                'bot_name': bot_name,
                'reply_id': reply_id
            }
        
        # 处理工具调用 - 传入当前工作目录
        tool_results = handle_tool_calls(result, current_dir=working_dir)
        
        # 检查是否有目录切换
        for tool_call, tool_result in zip(result, tool_results):
            try:
                output_data = json.loads(tool_result['output'])
                
                # 检查是否有目录切换指令
                if output_data.get('action') == 'change_directory':
                    try:
                        new_path = output_data['path']
                        if not os.path.isabs(new_path):
                            new_path = os.path.join(working_dir, new_path)
                        new_path = os.path.normpath(new_path)
                        
                        print(f"[目录切换] 从 {working_dir} 到 {new_path}")
                        if os.path.exists(new_path) and os.path.isdir(new_path):
                            global current_working_dir
                            current_working_dir = new_path
                            os.chdir(new_path)
                            output_data['message'] = f"已切换到目录: {new_path}"
                            output_data['success'] = True
                            print(f"[目录切换] 成功，当前目录: {current_working_dir}")
                        else:
                            output_data['success'] = False
                            output_data['error'] = "目录不存在"
                        
                        tool_result['output'] = json.dumps(output_data)
                    except Exception as e:
                        print(f"切换目录失败: {e}")
            except Exception as e:
                print(f"解析工具结果失败: {e}")
        
        # 将工具结果返回给 AI
        for tool_result in tool_results:
            print(tool_result)
            ai.history.append({
                "role": "tool",
                "tool_call_id": tool_result.get("tool_call_id", "unknown"),
                "content": tool_result["output"]
            })
        
        # 获取最终回复（流式）
        try:
            stream = ai.client.chat.completions.create(
                model=MODEL,
                messages=ai.history,
                max_tokens=ai.max_tokens,
                temperature=ai.temperature,
                stream=True
            )
            
            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    collected_content.append(delta.content)
                    yield {
                        'type': 'bot_chunk',
                        'bot_name': bot_name,
                        'reply_id': reply_id,
                        'content': delta.content
                    }
            
            final_content = "".join(collected_content)
            ai._add_history("assistant", final_content)
        except Exception as e:
            error_msg = f"AI 回复出错: {str(e)}"
            yield {
                'type': 'bot_chunk',
                'bot_name': bot_name,
                'reply_id': reply_id,
                'content': error_msg
            }
            final_content = error_msg
        
    else:  # 直接回答
        final_content = result
        yield {
            'type': 'bot_chunk',
            'bot_name': bot_name,
            'reply_id': reply_id,
            'content': result
        }
    
    # 保存记忆
    if len(final_content) > 50:
        memory.save(f"用户问：{user_message}\n我回答：{final_content}", tags=[bot_name, "chat"])
    
    # 创建 Bot 消息对象
    bot_msg = {
        'id': str(uuid.uuid4()),
        'sender': bot_name,
        'content': final_content,
        'time': datetime.now().isoformat(),
        'type': 'bot'
    }
    
    # 保存到聊天记录
    try:
        chat = load_chat(chat_id)
        chat['messages'].append(bot_msg)
        chat['updated_at'] = datetime.now().isoformat()
        save_chat(chat_id, chat)
    except Exception as e:
        print(f"保存聊天记录失败: {e}")
    
    # 发送结束标记
    yield {
        'type': 'bot_end',
        'bot_name': bot_name,
        'reply_id': reply_id,
        'full_content': final_content,
        'time': datetime.now().isoformat(),
        'message': bot_msg
    }

if __name__ == '__main__':
    app.run(debug=DEBUG)