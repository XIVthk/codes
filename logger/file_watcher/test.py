import ctypes
import json
import os
import threading
import time

# 加载 DLL
if os.name == 'nt':
    lib = ctypes.CDLL('./file_watcher.dll')
else:
    lib = ctypes.CDLL('./libfile_watcher.so')

# 设置函数签名
lib.watcher_create.argtypes = [ctypes.c_char_p]
lib.watcher_create.restype = ctypes.c_void_p

lib.watcher_destroy.argtypes = [ctypes.c_void_p]
lib.watcher_destroy.restype = None

lib.watcher_next_event.argtypes = [ctypes.c_void_p]
lib.watcher_next_event.restype = ctypes.c_char_p

lib.watcher_free_string.argtypes = [ctypes.c_char_p]
lib.watcher_free_string.restype = None

class FileWatcher:
    def __init__(self, path):
        self.handle = lib.watcher_create(path.encode())
        self.running = True
        
    def close(self):
        if self.handle:
            lib.watcher_destroy(self.handle)
            self.handle = None
    
    def next_event(self):
        if not self.handle:
            return None
        result = lib.watcher_next_event(self.handle)
        if result:
            event = json.loads(result.decode())
            lib.watcher_free_string(result)
            return event
        return None

# 在你的 logger 里使用
def watch_folder(path, logger):
    watcher = FileWatcher(path)
    logger.log("*", f"开始监控: {path}")
    
    try:
        while True:
            event = watcher.next_event()
            if event:
                if event['type'] == 'created':
                    logger.log("+", f"新增: {event['path']}")
                elif event['type'] == 'deleted':
                    logger.log("-", f"删除: {event['path']}")
                elif event['type'] == 'modified':
                    logger.log("/", f"修改: {event['path']}")
                elif event['type'] in ['moved_to', 'moved_from']:
                    logger.log(";", f"移动: {event['path']}")
            time.sleep(0.1)
    except KeyboardInterrupt:
        logger.log("*", "停止监控")
    finally:
        watcher.close()

# 测试
if __name__ == "__main__":
    from logger_core import Logger
    logger = Logger()
    
    # 监控当前目录
    watch_folder(".", logger)