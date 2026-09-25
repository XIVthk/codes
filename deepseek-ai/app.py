import os
import requests
import json
import time
import base64
from flask import Flask, request, Response, jsonify, send_from_directory, stream_with_context
from flask_cors import CORS
from werkzeug.utils import secure_filename
from datetime import datetime
import warnings
import re
warnings.filterwarnings('ignore')

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# ========== DeepSeek‑Flash 原生多模态配置 ==========
DEEPSEEK_API = "https://api.deepseek.com/v1/chat/completions"
API_KEY = os.environ.get("API_KEY", "")
if not API_KEY:
    raise ValueError("API_KEY 环境变量未设置")
MODEL_NAME = "deepseek-chat"

# 文件上传仅用于前端图片临时压缩（前端做完压缩后base64直接存前端，后端不再做识图）
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 获取当前真实日期
def get_current_date_info():
    now = datetime.now()
    date_str = now.strftime("%Y年%m月%d日")
    weekday = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][now.weekday()]
    return date_str, weekday

# ========== 工具定义 ==========
TOOLS_DEFINITION = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "搜索互联网获取最新信息。当用户询问实时新闻、最新动态、需要查询当前信息时使用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词，应简洁明确"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_link",
            "description": "读取指定URL的网页内容。当用户提供链接要求阅读、总结网页内容时使用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "完整的网页URL，以http://或https://开头"}
                },
                "required": ["url"]
            }
        }
    }
]

def search_web(query):
    """使用 Bing 搜索"""
    from bs4 import BeautifulSoup
    import urllib.parse
    encoded_query = urllib.parse.quote(query)
    url = f"https://cn.bing.com/search?q={encoded_query}&count=5"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    try:
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        for result in soup.select('#b_results .b_algo')[:5]:
            title_elem = result.select_one('h2 a')
            snippet_elem = result.select_one('.b_caption p')
            if title_elem:
                title = title_elem.get_text().strip()
                link = title_elem.get('href', '')
                snippet = snippet_elem.get_text().strip() if snippet_elem else ''
                if link.startswith('/'):
                    link = 'https://cn.bing.com' + link
                if title:
                    results.append(f"• **{title}**\n  {snippet[:200] if snippet else ''}\n  {link}")
        if results:
            return f"## 🔍 搜索结果：「{query}」\n\n" + "\n\n".join(results)
        else:
            return f"未找到关于「{query}」的搜索结果"
    except Exception as e:
        print(f"搜索失败: {e}")
        return f"搜索失败：{str(e)}"

def read_link(url):
    """读取网页内容"""
    try:
        from bs4 import BeautifulSoup
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        response = requests.get(url, headers=headers, timeout=20, verify=False)
        response.raise_for_status()
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find('title')
        title_text = title.get_text().strip() if title else "无标题"
        for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
            element.decompose()
        main_content = soup.find('article') or soup.find('main') or soup.body
        text = main_content.get_text(separator='\n', strip=True) if main_content else ""
        lines = [line.strip() for line in text.splitlines() if line.strip() and len(line.strip()) > 10]
        text = '\n'.join(lines)
        if len(text) > 5000:
            text = text[:5000] + "\n\n...(内容已截断)"
        if len(text) < 50:
            return f"无法提取有效内容。\n\n**链接：** {url}"
        return f"## 📄 {title_text}\n\n**来源：** {url}\n\n{text}"
    except Exception as e:
        return f"读取失败：{str(e)}\n\n**链接：** {url}"

def execute_tool(tool_name, arguments):
    """执行工具并返回结果"""
    if tool_name == "search_web":
        return search_web(arguments.get("query", ""))
    elif tool_name == "read_link":
        return read_link(arguments.get("url", ""))
    return f"未知工具：{tool_name}"

def validate_messages(messages):
    """DeepSeek限制：image_url块仅允许出现在user角色"""
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content")
        if role != "user":
            if isinstance(content, list):
                for block in content:
                    if block.get("type") == "image_url":
                        return False, f"格式错误：{role}消息不允许携带图片块，图片仅支持user消息"
    return True, ""

# ========== 路由 ==========
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    data = request.json
    messages = data.get('messages', [])
    system_prompt = data.get('system_prompt', 'You are a helpful assistant. 请用中文回复。')
    temperature = data.get('temperature', 0.7)
    reasoning_effort = data.get('reasoning_effort', 'medium')
    enable_tools = data.get('enable_tools', True)

    full_messages = [{"role": "system", "content": system_prompt}] + messages
    ok, err_msg = validate_messages(full_messages)
    if not ok:
        return jsonify({"error": err_msg}),400

    def generate():
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": MODEL_NAME,
            "messages": full_messages,
            "temperature": temperature,
            "stream": True,
            "max_tokens": 16384
        }
        if enable_tools:
            payload["tools"] = TOOLS_DEFINITION
        if reasoning_effort != "none":
            payload["reasoning_effort"] = reasoning_effort

        max_tool_rounds = 2
        current_round = 0
        current_messages = full_messages.copy()

        while current_round < max_tool_rounds:
            current_round += 1
            try:
                response = requests.post(DEEPSEEK_API, headers=headers, json=payload, stream=True, timeout=180, verify=False)
                tool_calls_collector = {}
                final_content = ""
                final_reasoning = ""
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            data_str = line[6:]
                            if data_str == '[DONE]':
                                break
                            try:
                                chunk = json.loads(data_str)
                                delta = chunk.get('choices', [{}])[0].get('delta', {})
                                if 'content' in delta and delta['content']:
                                    final_content += delta['content']
                                    yield f"data: {json.dumps({'type': 'content', 'content': delta['content']})}\n\n"
                                if 'reasoning_content' in delta and delta['reasoning_content']:
                                    if reasoning_effort != "none":
                                        final_reasoning += delta['reasoning_content']
                                        yield f"data: {json.dumps({'type': 'reasoning', 'content': delta['reasoning_content']})}\n\n"
                                if 'tool_calls' in delta:
                                    for tool_call in delta['tool_calls']:
                                        idx = tool_call.get('index', 0)
                                        if idx not in tool_calls_collector:
                                            tool_calls_collector[idx] = {
                                                'id': tool_call.get('id', ''),
                                                'type': tool_call.get('function', 'function'),
                                                'function': {'name': '', 'arguments': ''}
                                            }
                                        if 'id' in tool_call:
                                            tool_calls_collector[idx]['id'] = tool_call['id']
                                        if 'function' in tool_call:
                                            if 'name' in tool_call['function']:
                                                tool_calls_collector[idx]['function']['name'] = tool_call['function']['name']
                                            if 'arguments' in tool_call['function']:
                                                tool_calls_collector[idx]['function']['arguments'] += tool_call['function']['arguments']
                                        if tool_call.get('function', {}).get('name'):
                                            tool_name = tool_call['function']['name']
                                            try:
                                                args = json.loads(tool_call['function']['arguments']) if tool_call['function']['arguments'] else {}
                                                query = args.get('query', args.get('url', '未知'))
                                            except:
                                                query = tool_call['function']['arguments'][:50]
                                            yield f"data: {json.dumps({'type': 'tool_call_start', 'tool': tool_name, 'query': query})}\n\n"
                            except json.JSONDecodeError:
                                pass
                if not tool_calls_collector:
                    break
                yield f"data: {json.dumps({'type': 'tool_executing', 'count': len(tool_calls_collector)})}\n\n"
                assistant_message = {
                    "role": "assistant",
                    "content": final_content or None,
                    "tool_calls": [
                        {
                            "id": tc['id'],
                            "type": tc['type'],
                            "function": tc['function']
                        }
                        for tc in tool_calls_collector.values()
                    ]
                }
                current_messages.append(assistant_message)
                tool_results = []
                for tc in tool_calls_collector.values():
                    tool_name = tc['function']['name']
                    try:
                        arguments = json.loads(tc['function']['arguments'])
                    except:
                        arguments = {}
                    yield f"data: {json.dumps({'type': 'tool_executing', 'tool': tool_name})}\n\n"
                    tool_result = execute_tool(tool_name, arguments)
                    tool_results.append({
                        "role": "tool",
                        "tool_call_id": tc['id'],
                        "content": tool_result
                    })
                    yield f"data: {json.dumps({'type': 'tool_result', 'tool': tool_name, 'result': tool_result[:500]})}\n\n"
                current_messages.extend(tool_results)
                payload["messages"] = current_messages
                ok_loop, err_loop = validate_messages(current_messages)
                if not ok_loop:
                    yield f"data: {json.dumps({'type':'error','content':err_loop})}\n\n"
                    break
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'content': f'错误：{str(e)}'})}\n\n"
                break
        yield f"data: {json.dumps({'type': 'end'})}\n\n"
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    messages = data.get('messages', [])
    system_prompt = data.get('system_prompt', 'You are a helpful assistant. 请用中文回复。')
    temperature = data.get('temperature', 0.7)
    enable_tools = data.get('enable_tools', True)

    full_messages = [{"role": "system", "content": system_prompt}] + messages
    ok, err_msg = validate_messages(full_messages)
    if not ok:
        return jsonify({"error": err_msg}),400

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL_NAME,
        "messages": full_messages,
        "temperature": temperature,
        "stream": False,
        "max_tokens": 16384
    }
    if enable_tools:
        payload["tools"] = TOOLS_DEFINITION

    max_rounds = 2
    current_round = 0
    current_messages = full_messages.copy()
    while current_round < max_rounds:
        current_round +=1
        response = requests.post(DEEPSEEK_API, headers=headers, json=payload, timeout=60, verify=False)
        if response.status_code !=200:
            return jsonify({"error": response.text}), response.status_code
        result = response.json()
        assistant_message = result['choices'][0]['message']
        if not assistant_message.get('tool_calls'):
            return jsonify({
                "reply": assistant_message.get('content', ''),
                "tool_calls": []
            })
        tool_results = []
        tool_calls_info = []
        for tool_call in assistant_message['tool_calls']:
            tool_name = tool_call['function']['name']
            arguments = json.loads(tool_call['function']['arguments'])
            tool_calls_info.append({"name":tool_name, "arguments":arguments})
            tool_result = execute_tool(tool_name, arguments)
            tool_results.append({
                "tool_call_id": tool_call['id'],
                "role":"tool",
                "content": tool_result
            })
        current_messages.append(assistant_message)
        current_messages.extend(tool_results)
        payload["messages"] = current_messages
        ok_loop, err_loop = validate_messages(current_messages)
        if not ok_loop:
            return jsonify({"error":err_loop}),400
    return jsonify({
        "reply":"已达到最大工具调用轮数",
        "tool_calls":[]
    })

if __name__ == '__main__':
    if not API_KEY:
        print("\n" + "="*50)
        print("⚠️ 未找到 API Key！")
        print("请设置环境变量 API_KEY")
        print("Windows: set API_KEY=your_key_here")
        print("Linux/Mac: export API_KEY=your_key_here")
        print("="*50 + "\n")
    else:
        date_str, weekday = get_current_date_info()
        print(f"✅ API Key 已加载")
        print(f"📅 当前日期: {date_str} {weekday}")
        print(f"📡 使用模型: {MODEL_NAME} 原生多模态，图片直接进入对话上下文")
        print(f"🔧 工具调用: 已启用 (search_web, read_link)")
        print(f"👁️ 视觉识别：原生多模态，移除Ollama，移除独立识图接口")
        print(f"🌐 访问地址: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
