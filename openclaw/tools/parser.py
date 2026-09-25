#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
解析AI回复的函数
=======================
工作状态: Done
"""
from dataclasses import dataclass
import json
import os
from tools.executor import Commandor
from tools.context import ProjectContexter

@dataclass
class Operation:
    """
    操作类
    """
    type: str
    command: str | list[str] = None
    kwargs: dict[str, str] = None
    file: str = None
    content: str = None
    new_name: str = None
    dir: str = None
    language: str = None

# 初始化工具实例
cmd_executor = Commandor()
context_viewer = None

def handle_tool_calls(tool_calls, current_dir=None):
    """
    处理AI想调用的工具
    Args:
        tool_calls: AI返回的tool_calls列表
        current_dir: 当前工作目录（可选）
    Returns:
        每个工具调用的结果列表
    """
    results = []
    
    for tool_call in tool_calls:
        # 安全获取 tool_call_id（对象用.id，字典用.get）
        if hasattr(tool_call, 'id'):
            tool_call_id = tool_call.id
        elif isinstance(tool_call, dict) and 'id' in tool_call:
            tool_call_id = tool_call['id']
        else:
            tool_call_id = 'unknown'
            print(f"[警告] 无法获取 tool_call_id: {tool_call}")
        
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        
        # 处理不同的工具
        if function_name == "run_command":
            cmd = arguments.get("command")
            cwd = arguments.get("cwd", current_dir)
            
            # 命令规范化
            normalized_cmd = cmd
            
            # 处理 Windows 的 cd /d X: 格式
            if cmd.strip().startswith("cd /d "):
                parts = cmd.strip().split(maxsplit=2)
                if len(parts) >= 3:
                    normalized_cmd = f"cd {parts[2]}"
            
            # 处理 pushd 命令
            elif cmd.strip().startswith("pushd "):
                parts = cmd.strip().split(maxsplit=1)
                if len(parts) == 2:
                    normalized_cmd = f"cd {parts[1]}"
            
            # 处理 "cd.."（无空格）
            elif cmd.strip() == "cd.." or cmd.strip().startswith("cd.."):
                path_part = cmd.strip()[4:]
                if path_part:
                    normalized_cmd = f"cd ..{path_part}"
                else:
                    normalized_cmd = "cd .."
            
            # 检测是否是 cd 命令
            is_cd = False
            cd_path = None
            
            if normalized_cmd.strip().startswith("cd "):
                parts = normalized_cmd.strip().split(maxsplit=1)
                if len(parts) == 2:
                    is_cd = True
                    cd_path = parts[1]
            elif normalized_cmd.strip() == "cd.." or normalized_cmd.strip().startswith("cd.."):
                is_cd = True
                cd_path = ".." + normalized_cmd.strip()[4:]
            elif normalized_cmd.strip() == "cd":
                is_cd = True
                cd_path = "."
            
            if is_cd:
                output_data = {
                    "success": True,
                    "action": "change_directory",
                    "path": cd_path,
                    "message": f"准备切换到目录: {cd_path}"
                }
            else:
                result = cmd_executor.execute(cmd, cwd=cwd)
                output_data = {
                    "success": result.success,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode
                }
            
            output = {
                "tool_call_id": tool_call_id,
                "output": json.dumps(output_data, ensure_ascii=False)
            }
        
        elif function_name == "read_file":
            filepath = arguments.get("filepath")
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                output_data = {"success": True, "content": content}
            except Exception as e:
                output_data = {"success": False, "error": str(e)}
            
            output = {
                "tool_call_id": tool_call_id,
                "output": json.dumps(output_data, ensure_ascii=False)
            }
        
        elif function_name == "write_file":
            filepath = arguments.get("filepath")
            content = arguments.get("content")
            mode = arguments.get("mode", "w")
            try:
                with open(filepath, mode, encoding='utf-8') as f:
                    f.write(content)
                output_data = {"success": True, "message": f"已写入 {filepath}"}
            except Exception as e:
                output_data = {"success": False, "error": str(e)}
            
            output = {
                "tool_call_id": tool_call_id,
                "output": json.dumps(output_data, ensure_ascii=False)
            }
        
        elif function_name == "list_files":
            path = arguments.get("path", current_dir or ".")
            try:
                files = os.listdir(path)
                output_data = {"success": True, "files": files}
            except Exception as e:
                output_data = {"success": False, "error": str(e)}
            
            output = {
                "tool_call_id": tool_call_id,
                "output": json.dumps(output_data, ensure_ascii=False)
            }
        
        elif function_name == "get_project_context":
            path = arguments.get("path", current_dir or ".")
            global context_viewer
            context_viewer = ProjectContexter(path)
            output_data = {"success": True, "context": context_viewer.display_project_context()}
            
            output = {
                "tool_call_id": tool_call_id,
                "output": json.dumps(output_data, ensure_ascii=False)
            }
        
        elif function_name == "save_memory":
            from core.memory import Memory
            content = arguments.get("content")
            tags = arguments.get("tags", [])
            mem = Memory()
            mem.save(content, tags)
            output_data = {"success": True, "message": "记忆已保存"}
            
            output = {
                "tool_call_id": tool_call_id,
                "output": json.dumps(output_data, ensure_ascii=False)
            }
        
        elif function_name == "set_reminder":
            minutes = arguments.get("minutes", 1)
            message = arguments.get("message", "提醒")
            output_data = {
                "success": True, 
                "message": f"已设置 {minutes} 分钟后提醒：{message}",
                "reminder_data": {
                    "minutes": minutes,
                    "message": message
                }
            }
            
            output = {
                "tool_call_id": tool_call_id,
                "output": json.dumps(output_data, ensure_ascii=False)
            }
        
        elif function_name == "search_web":
            query = arguments.get("query")
            max_results = arguments.get("max_results", 5)
            
            try:
                from ddgs import DDGS
                print(f"搜索关键词: {query}")
                
                with DDGS() as ddgs:
                    search_results = []  # 改名为 search_results
                    for r in ddgs.text(query, max_results=max_results):
                        print(f"找到结果: {r.get('title', '')[:50]}")
                        search_results.append({
                            "title": r.get("title", ""),
                            "body": r.get("body", ""),
                            "href": r.get("href", "")
                        })
                
                output_data = {
                    "success": True,
                    "results": search_results,  # 使用 search_results
                    "message": f"找到 {len(search_results)} 条结果"
                }
                output = {
                    "tool_call_id": tool_call_id,
                    "output": json.dumps(output_data, ensure_ascii=False)
                }
                results.append(output)  # 追加到外层 results
            except Exception as e:
                output_data = {
                    "success": False,
                    "error": f"搜索失败: {str(e)}"
                }
                output = {
                    "tool_call_id": tool_call_id,
                    "output": json.dumps(output_data, ensure_ascii=False)
                }
                results.append(output)  # 也追加到外层 results
        
        else:
            output_data = {"success": False, "error": f"未知工具: {function_name}"}
            output = {
                "tool_call_id": tool_call_id,
                "output": json.dumps(output_data, ensure_ascii=False)
            }
        
        print(output)
        results.append(output)
    
    return results


# 工具定义（给AI看的）
tools_definition = [
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "执行系统命令（ls, dir, python, git等）",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "要执行的命令"
                    },
                    "cwd": {
                        "type": "string",
                        "description": "工作目录（可选）"
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取文件内容",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "文件路径"
                    }
                },
                "required": ["filepath"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "写入文件（会覆盖原有内容，除非用追加模式）",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "文件路径"
                    },
                    "content": {
                        "type": "string",
                        "description": "要写入的内容"
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["w", "a"],
                        "description": "w=覆盖，a=追加"
                    }
                },
                "required": ["filepath", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "列出目录下的文件",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "目录路径"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_project_context",
            "description": "获取当前项目的结构、最近更改等信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "项目路径"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_memory",
            "description": "保存重要信息到长期记忆",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "要记住的内容"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "标签（可选）"
                    }
                },
                "required": ["content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_reminder",
            "description": "设置一个定时提醒，让你自己在指定时间后主动说话提醒用户",
            "parameters": {
                "type": "object",
                "properties": {
                    "minutes": {
                        "type": "integer",
                        "description": "多少分钟后主动提醒"
                    },
                    "message": {
                        "type": "string",
                        "description": "提醒的内容，比如'喝水'、'休息一下'"
                    }
                },
                "required": ["minutes", "message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "搜索网络，获取最新信息。当用户问新闻、查询资料、找东西时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "返回结果数量（默认5）",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }
    }
]