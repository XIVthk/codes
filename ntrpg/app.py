# app.py - 确保以点开头的命令都被解析
import os
import re
from flask import Flask, render_template, request, jsonify
from openai import OpenAI
from parse import parse_cmd, Mode

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'trpg-secret-key-2024')

# AI配置
AI_API_KEY = os.environ.get('API_KEY')
AI_BASE_URL = os.environ.get('BASE_URL', 'https://api.siliconflow.cn/v1')
AI_MODEL = os.environ.get('MODEL', 'deepseek-ai/DeepSeek-V3')

SYSTEM_PROMPT = """你是一个TRPG地下城主(DM)。根据玩家选择的规则(D&D/CoC/其他)来主持游戏。
职责：营造沉浸氛围、推进剧情、扮演NPC、引导玩家使用骰子命令。
使用第二人称"你"称呼玩家。"""

game_sessions = {}

class AIDM:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.client = OpenAI(api_key=AI_API_KEY, base_url=AI_BASE_URL) if AI_API_KEY else None
        self.history = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    def ask(self, question: str) -> str:
        if not self.client:
            return "⚠️ API密钥未配置"
        try:
            self.history.append({"role": "user", "content": question})
            response = self.client.chat.completions.create(
                model=AI_MODEL, messages=self.history, max_tokens=2048, temperature=0.8
            )
            answer = response.choices[0].message.content
            self.history.append({"role": "assistant", "content": answer})
            if len(self.history) > 50:
                self.history = [self.history[0]] + self.history[-40:]
            return answer
        except Exception as e:
            return f"❌ AI错误: {str(e)}"
    
    def clear_history(self):
        self.history = [self.history[0]]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    session_id = data.get('session_id', 'default')
    message = data.get('message', '').strip()
    username = data.get('username', '玩家')
    
    if not message:
        return jsonify({'error': '消息为空'}), 400
    
    if session_id not in game_sessions:
        game_sessions[session_id] = AIDM(session_id)
    
    ai_dm = game_sessions[session_id]
    
    # 关键：所有以 . 开头的命令都先尝试 parse_cmd
    if message.startswith('.'):
        parse_result = parse_cmd(message, username, Mode.CoC)
        if parse_result is not None:
            # parse_cmd 返回了结果，直接返回
            result_str = str(parse_result)
            if isinstance(parse_result, tuple) and len(parse_result) > 1:
                result_str = str(parse_result[1])
            return jsonify({'response': result_str, 'is_command': True})
    
    # 不是命令，交给AI
    ai_response = ai_dm.ask(message)
    return jsonify({'response': ai_response, 'is_command': False})

@app.route('/api/clear', methods=['POST'])
def clear_history():
    data = request.json
    session_id = data.get('session_id', 'default')
    if session_id in game_sessions:
        game_sessions[session_id].clear_history()
    return jsonify({'success': True})

if __name__ == '__main__':
    if not AI_API_KEY:
        print("⚠️ 请设置环境变量: set API_KEY=your-api-key")
    app.run(debug=True, host='0.0.0.0', port=5000)