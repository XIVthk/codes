import os
import platform

def build():
    system = platform.system()
    
    if system == "Windows":
        cmd = "g++ -shared -o file_watcher.dll watcher.cpp -static-libgcc -static-libstdc++"
    elif system == "Linux":
        cmd = "g++ -shared -fPIC -o libfile_watcher.so watcher.cpp"
    elif system == "Darwin":  # macOS
        cmd = "g++ -shared -fPIC -o libfile_watcher.dylib watcher.cpp"
    
    print(f"Running: {cmd}")
    os.system(cmd)
    print("Build complete!")

if __name__ == "__main__":
    build()