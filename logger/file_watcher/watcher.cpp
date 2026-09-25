#include "watcher.h"
#include <string>
#include <map>
#include <thread>
#include <chrono>
#include <cstring>
#include <sstream>

#ifdef __linux__
#include <sys/inotify.h>
#include <unistd.h>
#include <fcntl.h>
#endif

#ifdef _WIN32
#include <windows.h>
#endif

class FileWatcher {
private:
    std::string path;
    bool running;
    std::thread worker;
    
#ifdef __linux__
    int fd;
    std::map<int, std::string> watch_map;
#endif
    
#ifdef _WIN32
    HANDLE dir_handle;
    OVERLAPPED overlapped;
    char notify_buffer[1024];
#endif

public:
    FileWatcher(const char* p) : path(p), running(true) {
#ifdef __linux__
        fd = inotify_init1(IN_NONBLOCK);
        if (fd >= 0) {
            int wd = inotify_add_watch(fd, path.c_str(), 
                IN_CREATE | IN_DELETE | IN_MODIFY | IN_MOVED_TO | IN_MOVED_FROM);
            watch_map[wd] = path;
        }
#endif
    }
    
    ~FileWatcher() {
        running = false;
        if (worker.joinable()) worker.join();
#ifdef __linux__
        for (auto& [wd, _] : watch_map) inotify_rm_watch(fd, wd);
        if (fd >= 0) close(fd);
#endif
    }
    
    std::string next_event() {
#ifdef __linux__
        char buffer[4096];
        int len = read(fd, buffer, sizeof(buffer));
        if (len > 0) {
            int i = 0;
            while (i < len) {
                inotify_event* event = (inotify_event*)&buffer[i];
                
                std::string type;
                if (event->mask & IN_CREATE) type = "created";
                else if (event->mask & IN_DELETE) type = "deleted";
                else if (event->mask & IN_MODIFY) type = "modified";
                else if (event->mask & IN_MOVED_TO) type = "moved_to";
                else if (event->mask & IN_MOVED_FROM) type = "moved_from";
                
                if (!type.empty()) {
                    std::stringstream ss;
                    ss << "{\"type\":\"" << type << "\","
                       << "\"path\":\"" << event->name << "\"}";
                    i += sizeof(inotify_event) + event->len;
                    return ss.str();
                }
                i += sizeof(inotify_event) + event->len;
            }
        }
#endif
        return "";
    }
};

// C 接口实现
extern "C" {
    EXPORT void* watcher_create(const char* path) {
        return new FileWatcher(path);
    }
    
    EXPORT void watcher_destroy(void* handle) {
        delete (FileWatcher*)handle;
    }
    
    EXPORT char* watcher_next_event(void* handle) {
        auto watcher = (FileWatcher*)handle;
        std::string event = watcher->next_event();
        if (event.empty()) return nullptr;
        
        char* result = (char*)malloc(event.size() + 1);
        strcpy(result, event.c_str());
        return result;
    }
    
    EXPORT void watcher_free_string(char* str) {
        free(str);
    }
}