from flask import Flask, request
from flask_socketio import SocketIO

# 创建 Flask 应用和 SocketIO 实例
app = Flask(__name__)
socketio = SocketIO(app)

# 存储已连接用户的信息，键为用户名（统一转换为小写），值为对应的 Socket.IO 会话 ID
connected_users = {}

# 标记是否为第一次请求
is_first_request = True


def record_user_connection(username, sid):
    """
    记录用户的连接信息
    :param username: 用户名
    :param sid: 会话 ID
    """
    lower_username = username.lower()
    connected_users[lower_username] = sid
    print(f"用户 {username} 已连接，连接 ID: {sid}")
    print(f"当前连接用户: {connected_users}")


def remove_user_connection(sid):
    """
    移除断开连接用户的信息
    :param sid: 会话 ID
    """
    for username, user_sid in connected_users.items():
        if user_sid == sid:
            del connected_users[username]
            print(f"用户 {username} 已断开连接")
            print(f"当前连接用户: {connected_users}")
            break


def forward_swap_request(data):
    """
    转发换课请求给目标教师
    :param data: 换课请求数据
    """
    target_teacher = data.get('target_teacher')
    if target_teacher:
        lower_target_teacher = target_teacher.lower()
        print(f"当前连接用户: {connected_users}")
        if lower_target_teacher in connected_users:
            target_sid = connected_users[lower_target_teacher]
            socketio.emit('swap_request', data, room=target_sid)
            print(f"已将换课请求转发给 {target_teacher}")
        else:
            print(f"目标教师 {target_teacher} 未连接到服务器，无法转发换课请求")
    else:
        print("换课请求中未提供目标教师信息，无法处理")


# 处理用户连接事件
@socketio.on('user_connect')
def handle_user_connect(data):
    print(f"收到 user_connect 事件，数据: {data}")
    try:
        username = data.get('username')
        if username:
            record_user_connection(username, request.sid)
            # 发送连接确认消息给客户端
            socketio.emit('user_connect_ack', {'status': 'success'}, room=request.sid)
        else:
            # 若未提供用户名，发送连接失败消息给客户端
            socketio.emit('user_connect_ack', {'status': 'failed', 'message': '用户名未提供'}, room=request.sid)
    except Exception as e:
        print(f"处理 user_connect 事件时出现异常: {e}")


# 处理用户断开连接事件
@socketio.on('disconnect')
def handle_disconnect():
    remove_user_connection(request.sid)


# 处理换课请求事件
@socketio.on('swap_request')
def handle_swap_request(data):
    print(f"收到换课请求，数据: {data}")
    forward_swap_request(data)


# 处理登录成功后发送的用户信息
@socketio.on('login_success')
def handle_login_success(data):
    username = data.get('username')
    sid = request.sid
    if username:
        record_user_connection(username, sid)
        print(f"用户 {username} 登录成功，连接 ID: {sid}")
        print(f"当前连接用户: {connected_users}")
        socketio.emit('user_connect_ack', {'status': 'success'}, room=sid)
    else:
        socketio.emit('user_connect_ack', {'status': 'failed', 'message': '用户名未提供'}, room=sid)


# 确保服务器完全启动后再接收连接
@app.before_request
def before_request():
    global is_first_request
    if is_first_request:
        print("服务器已完全启动，开始接收连接...")
        is_first_request = False


if __name__ == '__main__':
    socketio.run(app, debug=True)
