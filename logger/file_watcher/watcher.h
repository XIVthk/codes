#pragma once
#ifdef _WIN32
    #define EXPORT __declspec(dllexport)
#else
    #define EXPORT
#endif

extern "C" {
    // 创建一个监控器，返回句柄
    EXPORT void* watcher_create(const char* path);
    
    // 销毁监控器
    EXPORT void watcher_destroy(void* handle);
    
    // 获取下一个事件，返回 JSON 字符串（调用者需要 free）
    EXPORT char* watcher_next_event(void* handle);
    
    // 释放事件字符串
    EXPORT void watcher_free_string(char* str);
}