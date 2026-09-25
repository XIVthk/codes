"""
录制模块
"""
import time
import threading
from pynput import mouse, keyboard
from datetime import datetime
import os

class Recorder:
    def __init__(self):
        self.events = []
        self.recording = False
        self.start_time = None
        self.mouse_listener = None
        self.keyboard_listener = None
        self.last_time = 0
        
    def start(self):
        """开始录制"""
        self.events = []
        self.recording = True
        self.start_time = time.time()
        self.last_time = 0
        
        # 启动监听器
        self.mouse_listener = mouse.Listener(
            on_move=self.on_move,
            on_click=self.on_click,
            on_scroll=self.on_scroll
        )
        self.keyboard_listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        )
        self.mouse_listener.start()
        self.keyboard_listener.start()
        
        print("🎬 录制开始... (按 Ctrl+Shift+F12 停止)")
        
    def stop(self):
        """停止录制"""
        if not self.recording:
            return
            
        self.recording = False
        
        # 停止监听器
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            
        print(f"✅ 录制停止，共记录 {len(self.events)} 个事件")
        return self.events
        
    def on_move(self, x, y):
        if not self.recording:
            return
        current_time = time.time() - self.start_time
        # 过滤掉太密集的移动事件（减少脚本体积）
        if current_time - self.last_time >= 0.05:
            self.events.append({
                'type': 'move',
                'x': x,
                'y': y,
                'time': current_time
            })
            self.last_time = current_time
            
    def on_click(self, x, y, button, pressed):
        if not self.recording:
            return
        current_time = time.time() - self.start_time
        button_name = str(button).split('.')[-1]
        self.events.append({
            'type': 'click',
            'x': x,
            'y': y,
            'button': button_name,
            'pressed': pressed,
            'time': current_time
        })
        
    def on_scroll(self, x, y, dx, dy):
        if not self.recording:
            return
        current_time = time.time() - self.start_time
        self.events.append({
            'type': 'scroll',
            'x': x,
            'y': y,
            'dx': dx,
            'dy': dy,
            'time': current_time
        })
        
    def on_press(self, key):
        if not self.recording:
            return
        current_time = time.time() - self.start_time
        try:
            key_name = key.char
        except AttributeError:
            key_name = str(key).replace('Key.', '')
        self.events.append({
            'type': 'key',
            'key': key_name,
            'pressed': True,
            'time': current_time
        })
        
        # 停止快捷键检测
        try:
            if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                self.ctrl_pressed = True
            elif key == keyboard.Key.shift_l or key == keyboard.Key.shift_r:
                self.shift_pressed = True
            elif key == keyboard.Key.f12:
                if self.ctrl_pressed and self.shift_pressed:
                    self.stop()
        except:
            pass
            
    def on_release(self, key):
        if not self.recording:
            return
        current_time = time.time() - self.start_time
        try:
            key_name = key.char
        except AttributeError:
            key_name = str(key).replace('Key.', '')
        self.events.append({
            'type': 'key',
            'key': key_name,
            'pressed': False,
            'time': current_time
        })
        
        # 重置修饰键状态
        try:
            if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                self.ctrl_pressed = False
            elif key == keyboard.Key.shift_l or key == keyboard.Key.shift_r:
                self.shift_pressed = False
        except:
            pass

def save_to_script(events, filename=None):
    """将录制的事件保存为 .sc 脚本"""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recording_{timestamp}.sc"
    
    lines = []
    lines.append("# 录制时间: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    lines.append("")
    
    last_time = 0
    for event in events:
        # 添加延迟
        delay = event['time'] - last_time
        if delay > 0.05:  # 忽略小于50ms的延迟
            lines.append(f"DELAY {int(delay * 1000)}")
        
        # 生成命令
        if event['type'] == 'move':
            lines.append(f"MOVETO {int(event['x'])} {int(event['y'])}")
            
        elif event['type'] == 'click':
            button = event['button']
            if event['pressed']:
                lines.append(f"MOUSEDOWN {button}")
            else:
                lines.append(f"MOUSEUP {button}")
                
        elif event['type'] == 'scroll':
            # 滚动量取整
            amount = int(event['dy'] * 100) if event['dy'] else int(event['dx'])
            lines.append(f"SCROLL {amount}")
            
        elif event['type'] == 'key':
            key = event['key']
            # 处理特殊按键
            if key in ['ctrl', 'ctrl_l', 'ctrl_r']:
                key = 'ctrl'
            elif key in ['shift', 'shift_l', 'shift_r']:
                key = 'shift'
            elif key in ['alt', 'alt_l', 'alt_r']:
                key = 'alt'
            elif key == 'cmd':
                key = 'win'
                
            if event['pressed']:
                lines.append(f"KEYDOWN {key}")
            else:
                lines.append(f"KEYUP {key}")
                
        last_time = event['time']
    
    # 保存文件
    with open(filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"💾 脚本已保存: {filename}")
    return filename

def record():
    """录制主函数"""
    recorder = Recorder()
    recorder.ctrl_pressed = False
    recorder.shift_pressed = False
    
    print("=" * 50)
    print("按键精灵 - 录制器")
    print("=" * 50)
    print("按 Ctrl+Shift+F12 开始录制")
    print("按 Ctrl+Shift+F12 停止录制")
    print("")
    
    # 等待快捷键启动
    def on_hotkey():
        if not recorder.recording:
            recorder.start()
        else:
            events = recorder.stop()
            if events:
                save_to_script(events)
    
    # 监听全局热键
    hotkey_listener = keyboard.GlobalHotKeys({
        '<ctrl>+<shift>+<f12>': on_hotkey
    })
    hotkey_listener.start()
    
    try:
        hotkey_listener.join()
    except KeyboardInterrupt:
        print("\n👋 退出录制器")

if __name__ == "__main__":
    record()