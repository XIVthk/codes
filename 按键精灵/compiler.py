"""
编译模块
"""
import pyautogui as pg
import time
from typing import Any, Callable, List, Tuple, Union
import re
from functools import partial

# 全局变量存储
VARS = {}
FUNCS = {}
KEYWORDS = [
    # 控制流
    "IF", "ELIF", "ELSE", "ENDIF",
    "WHILE", "ENDWHILE",
    "FOR", "ENDFOR", "TO",

    # 布尔值
    "TRUE", "FALSE", "NONE",
    
    # 鼠标操作
    "CLICK", "MOVETO", "DRAGTO", "MOUSEDOWN", "MOUSEUP", "SCROLL",
    
    # 键盘操作
    "PRESS", "HOTKEY", "KEYDOWN", "KEYUP",
    
    # 图像识别
    "FIND",
    
    # 函数
    "FUNC", "FUNCTION", "ENDFUNC", "CALL", "DO",
    
    # 变量与输出
    "LET", "PRINT",
    
    # 其他
    "DELAY",
    
    # 特殊变量
    "_FOUND", "_X", "_Y",

    # 参数
    "RIGHT", "LEFT", "MIDDLE", "ABS", "ABSOLUTE", "REL", "RELATIVE"
]

Action = Union[
    Tuple[Callable, List[Any]],
    Tuple[str, Any],
    Tuple[str, str, List[str]],
    Tuple[str, List[str]]
]

def evaluate_expression(parts: List[str]):
    expr = ' '.join(parts).strip()
    safe_globals = {'__builtins__': {}}
    safe_locals = {**VARS, 'True': True, 'False': False}
    try:
        return eval(expr, safe_globals, safe_locals)
    except Exception as e:
        raise ValueError(f"表达式求值失败: {expr}\n错误: {e}")

def evaluate_condition(parts):
    expr = ' '.join(parts).strip()
    expr = re.sub(r'(!|~)(\s*)([a-zA-Z_][a-zA-Z0-9_]*)', r'not \3', expr)
    expr = re.sub(r'\bAND\b', 'and', expr, flags=re.IGNORECASE)
    expr = re.sub(r'\bOR\b', 'or', expr, flags=re.IGNORECASE)
    expr = re.sub(r'\bNOT\b', 'not', expr, flags=re.IGNORECASE)
    safe_globals = {'__builtins__': {}}
    safe_locals = {**VARS, 'True': True, 'False': False, 'None': None}
    try:
        result = eval(expr, safe_globals, safe_locals)
        return bool(result)
    except Exception as e:
        raise ValueError(f"条件表达式求值失败: {expr}\n错误: {e}")

def handle_click(args: List[str]) -> Tuple[int, str]:
    times = 1
    clicktype = "left"
    errors = []
    if len(args) not in (1, 2, 3):
        errors.append(ValueError("CLICK 必须有 1、2 或 3 个参数"))
        raise ExceptionGroup("CLICK", errors)

    if len(args) >= 2:
        if args[1].isdigit():
            times = int(args[1])
        else:
            errors.append(ValueError("CLICK 次数必须是数字"))
    if len(args) == 3:
        clicktype = args[2].lower()
        if clicktype not in ["left", "right", "middle"]:
            errors.append(ValueError("CLICK 按键类型必须是 left、right 或 middle"))
    if errors:
        raise ExceptionGroup("CLICK", errors)
    return times, clicktype

def handle_move(args: List[str]) -> Tuple[float, float, str]:
    x = y = None
    mode = "absolute"
    errors = []
    if len(args) not in (3, 4):
        errors.append(ValueError("MOVETO 必须有 3 或 4 个参数"))
        raise ExceptionGroup("MOVETO", errors)

    try:
        x = float(args[1])
        y = float(args[2])
    except ValueError:
        errors.append(ValueError("MOVETO 的 x 和 y 必须是数字"))

    if len(args) == 4:
        mode = args[3].lower()
        if mode in ["abs", "absolute"]:
            mode = "absolute"
        elif mode in ["rel", "relative"]:
            mode = "relative"
        else:
            errors.append(ValueError("MOVETO 模式必须是 abs、absolute、rel 或 relative"))
    if errors:
        raise ExceptionGroup("MOVETO", errors)
    return x, y, mode

def handle_hotkey(args: List[str]) -> List[str]:
    hotkeys = []
    errors = []
    if len(args) < 2:
        raise ExceptionGroup("HOTKEY", [ValueError("HOTKEY 至少需要 1 个按键")])
    for arg in args[1:]:
        arg = arg.strip("[,]")
        if arg.lower() not in pg.KEYBOARD_KEYS:
            errors.append(ValueError(f"HOTKEY 按键 {arg} 无效"))
        hotkeys.append(arg.lower())
    if errors:
        raise ExceptionGroup("HOTKEY", errors)
    return hotkeys

def replace_vars(args: List[str]) -> List[str]:
    new_args = []
    for arg in args:
        if arg in VARS:
            new_args.append(str(VARS[arg]))
        else:
            new_args.append(arg)
    return new_args

def find_image(img_path, timeout=3):
    try:
        pos = pg.locateOnScreen(img_path)
        if pos:
            x, y = pg.center(pos)
            VARS["_FOUND"] = True
            VARS["_X"] = x
            VARS["_Y"] = y
        else:
            VARS["_FOUND"] = False
            VARS["_X"] = None
            VARS["_Y"] = None
    except Exception:
        VARS["_FOUND"] = False
        VARS["_X"] = None
        VARS["_Y"] = None

def compile_code(code: str) -> List[Action]:
    actions_line = []
    condition_stack = []
    loop_stack = []
    func_stack = []
    func_body = []
    current_func = None

    for raw_line in code.splitlines():
        original_line = raw_line.strip()
        if not original_line or original_line.startswith("#"):
            continue

        parts = original_line.split()
        cmd = parts[0].upper()

        # 函数定义
        if cmd in ("FUNC", "FUNCTION"):
            if len(parts) != 2:
                raise ExceptionGroup("FUNC", [ValueError("FUNC 必须有 1 个参数 (函数名)")])
            if current_func:
                raise ExceptionGroup("FUNC", [ValueError("不能在函数内定义函数")])
            current_func = parts[1]
            func_body = []
            func_stack.append(current_func)
            continue

        elif cmd == "ENDFUNC":
            if not current_func:
                raise ExceptionGroup("ENDFUNC", [ValueError("ENDFUNC 没有对应的 FUNC")])
            FUNCS[current_func] = func_body
            current_func = None
            func_stack.pop()
            continue

        if current_func:
            func_body.append(original_line)
            continue

        # 控制流命令
        if cmd == "IF":
            actions_line.append(('IF', parts[1:]))
            continue
        elif cmd == "ELIF":
            actions_line.append(('ELIF', parts[1:]))
            continue
        elif cmd == "ELSE":
            actions_line.append(('ELSE',))
            continue
        elif cmd == "ENDIF":
            actions_line.append(('ENDIF',))
            continue
        elif cmd == "WHILE":
            def make_condition_func(cond_parts):
                return lambda: evaluate_condition(cond_parts)
            condition_func = make_condition_func(parts[1:])
            actions_line.append(('WHILE', condition_func, None))
            loop_stack.append(len(actions_line) - 1)
            continue
        elif cmd == "ENDWHILE":
            if not loop_stack:
                raise SyntaxError("ENDWHILE 没有对应的 WHILE")
            while_idx = loop_stack.pop()
            false_target = len(actions_line) + 1
            old_while = actions_line[while_idx]
            actions_line[while_idx] = ('WHILE', old_while[1], false_target)
            actions_line.append(('JUMP', while_idx))
            continue
        elif cmd == "FOR":
            if len(parts) != 6 or parts[2] != '=' or parts[4].upper() != 'TO':
                raise SyntaxError("FOR 语法: FOR 变量 = 起始值 TO 结束值")
            var_name = parts[1]
            start_expr = parts[3]
            end_expr = parts[5]
            actions_line.append(('ASSIGN', var_name, [start_expr]))
            def make_condition_func(var, end):
                return lambda: evaluate_condition([var, '<=', end])
            condition_func = make_condition_func(var_name, end_expr)
            while_idx = len(actions_line)
            actions_line.append(('WHILE', condition_func, None))
            loop_stack.append((while_idx, var_name))
            continue
        elif cmd == "ENDFOR":
            if not loop_stack:
                raise SyntaxError("ENDFOR 没有对应的 FOR")
            while_idx, var_name = loop_stack.pop()
            actions_line.append(('ASSIGN', var_name, [var_name, '+', '1']))
            actions_line.append(('JUMP', while_idx))
            false_target = len(actions_line)
            old_while = actions_line[while_idx]
            actions_line[while_idx] = ('WHILE', old_while[1], false_target)
            continue

        # 普通命令
        if cmd in ("CALL", "DO"):
            if len(parts) != 2:
                raise ExceptionGroup("CALL", [ValueError("CALL 必须有 1 个参数 (函数名)")])
            func_name = parts[1]
            if func_name not in FUNCS:
                raise ExceptionGroup("CALL", [ValueError(f"函数 {func_name} 未定义")])
            func_code = "\n".join(FUNCS[func_name])
            func_actions = compile_code(func_code)
            actions_line.extend(func_actions)
            continue

        if cmd in ("LET", "PRINT"):
            if cmd == "LET":
                if len(parts) >= 4 and parts[2] == '=':
                    var_name = parts[1]
                    expr_parts = parts[3:]
                    actions_line.append(('ASSIGN', var_name, expr_parts))
                else:
                    raise SyntaxError("LET 语法错误")
            elif cmd == "PRINT":
                expr_parts = parts[1:]
                actions_line.append(('PRINT', expr_parts))
            continue

        if cmd == "FIND":
            img_path = parts[1].strip('"\'')
            timeout = 3.0
            i = 2
            while i < len(parts):
                if parts[i].upper() == 'TIMEOUT':
                    timeout = float(parts[i+1])
                    i += 2
                else:
                    i += 1
            actions_line.append((find_image, [img_path, timeout]))
            continue

        parts = replace_vars(parts)

        if cmd == "CLICK":
            times, clicktype = handle_click(parts)
            for _ in range(times):
                if clicktype == "left":
                    actions_line.append((pg.click, []))
                elif clicktype == "right":
                    actions_line.append((pg.rightClick, []))
                elif clicktype == "middle":
                    actions_line.append((pg.middleClick, []))
        elif cmd == "MOVETO":
            x, y, mode = handle_move(parts)
            if mode == "absolute":
                actions_line.append((pg.moveTo, [x, y]))
            else:
                actions_line.append((pg.moveRel, [x, y]))
        elif cmd == "MOUSEDOWN":
            if len(parts) not in (1, 2):
                raise ExceptionGroup("MOUSEDOWN", [ValueError("MOUSEDOWN 可以有 0 或 1 个参数 (按键类型)")])
            button = "left" if len(parts) == 1 else parts[1].lower()
            if button not in ["left", "right", "middle"]:
                raise ExceptionGroup("MOUSEDOWN", [ValueError(f"MOUSEDOWN 按键 {button} 无效")])
            actions_line.append((partial(pg.mouseDown, button=button), []))
        elif cmd == "MOUSEUP":
            if len(parts) not in (1, 2):
                raise ExceptionGroup("MOUSEUP", [ValueError("MOUSEUP 可以有 0 或 1 个参数 (按键类型)")])
            button = "left" if len(parts) == 1 else parts[1].lower()
            if button not in ["left", "right", "middle"]:
                raise ExceptionGroup("MOUSEUP", [ValueError(f"MOUSEUP 按键 {button} 无效")])
            actions_line.append((partial(pg.mouseUp, button=button), []))
        elif cmd == "DRAGTO":
            x, y, mode = handle_move(parts)
            if mode == "absolute":
                actions_line.append((pg.dragTo, [x, y]))
            else:
                actions_line.append((pg.dragRel, [x, y]))
        elif cmd == "KEYDOWN":
            if len(parts) != 2:
                raise ExceptionGroup("KEYDOWN", [ValueError("KEYDOWN 必须有 1 个参数 (按键)")])
            key = parts[1].lower()
            if key not in pg.KEYBOARD_KEYS:
                raise ExceptionGroup("KEYDOWN", [ValueError(f"KEYDOWN 按键 {key} 无效")])
            actions_line.append((partial(pg.keyDown, key=key), []))
        elif cmd == "KEYUP":
            if len(parts) != 2:
                raise ExceptionGroup("KEYUP", [ValueError("KEYUP 必须有 1 个参数 (按键)")])
            key = parts[1].lower()
            if key not in pg.KEYBOARD_KEYS:
                raise ExceptionGroup("KEYUP", [ValueError(f"KEYUP 按键 {key} 无效")])
            actions_line.append((partial(pg.keyUp, key=key), []))
        elif cmd == "DELAY":
            if len(parts) != 2:
                raise ExceptionGroup("DELAY", [ValueError("DELAY 必须有 1 个参数 (毫秒)")])
            ms = float(parts[1])
            actions_line.append((time.sleep, [ms / 1000.0]))
        elif cmd == "PRESS":
            if len(parts) != 2:
                raise ExceptionGroup("PRESS", [ValueError("PRESS 必须有 1 个参数 (按键)")])
            key = parts[1].lower()
            if key not in pg.KEYBOARD_KEYS:
                raise ExceptionGroup("PRESS", [ValueError(f"PRESS 按键 {key} 无效")])
            actions_line.append((pg.press, [key]))
        elif cmd == "HOTKEY":
            hotkeys = handle_hotkey(parts)
            actions_line.append((pg.hotkey, hotkeys))
        elif cmd == "SCROLL":
            if len(parts) != 2:
                raise ExceptionGroup("SCROLL", [ValueError("SCROLL 必须有 1 个参数 (滚动量)")])
            amount = int(float(parts[1]))
            actions_line.append((pg.scroll, [amount]))
        elif cmd in [key.upper() for key in VARS.keys()]:
            ori_key = next(k for k in VARS.keys() if k.upper() == cmd)
            actions_line.append((VARS.update, {ori_key: parts[-1]}))
        else:
            raise ExceptionGroup("未知命令", [ValueError(f"未知命令: {cmd}")])

    return actions_line

def run(actions: List[Action]):
    pc = 0
    rt_condition_stack = []

    while pc < len(actions):
        action = actions[pc]
        try:
            if isinstance(action, tuple) and len(action) >= 1 and isinstance(action[0], str):
                cmd = action[0]

                if cmd in ('IF', 'ELIF', 'ELSE', 'ENDIF', 'WHILE', 'JUMP'):
                    if cmd == 'IF':
                        cond_parts = action[1]
                        condition = evaluate_condition(cond_parts)
                        rt_condition_stack.append({'branch_taken': condition, 'executing': condition})
                        pc += 1
                        continue
                    elif cmd == 'ELIF':
                        if not rt_condition_stack:
                            raise RuntimeError("ELIF 没有对应的 IF")
                        block = rt_condition_stack[-1]
                        if block['branch_taken']:
                            block['executing'] = False
                        else:
                            condition = evaluate_condition(action[1])
                            block['branch_taken'] = condition
                            block['executing'] = condition
                        pc += 1
                        continue
                    elif cmd == 'ELSE':
                        if not rt_condition_stack:
                            raise RuntimeError("ELSE 没有对应的 IF")
                        block = rt_condition_stack[-1]
                        if block['branch_taken']:
                            block['executing'] = False
                        else:
                            block['executing'] = True
                            block['branch_taken'] = True
                        pc += 1
                        continue
                    elif cmd == 'ENDIF':
                        if not rt_condition_stack:
                            raise RuntimeError("ENDIF 没有对应的 IF")
                        rt_condition_stack.pop()
                        pc += 1
                        continue
                    elif cmd == 'WHILE':
                        _, condition_func, false_target = action
                        if condition_func():
                            pc += 1
                        else:
                            pc = false_target
                        continue
                    elif cmd == 'JUMP':
                        _, target = action
                        pc = target
                        continue

                else:
                    if rt_condition_stack and not rt_condition_stack[-1]['executing']:
                        pc += 1
                        continue

                    if cmd == 'PRINT':
                        _, expr_parts = action
                        value = evaluate_expression(expr_parts)
                        print(value)
                    elif cmd == 'ASSIGN':
                        _, var_name, expr_parts = action
                        value = evaluate_expression(expr_parts)
                        VARS[var_name] = value
                    else:
                        raise RuntimeError(f"未知执行指令: {cmd}")

                    pc += 1
                    continue

            else:
                if rt_condition_stack and not rt_condition_stack[-1]['executing']:
                    pc += 1
                    continue
                func, args = action
                func(*args)
                pc += 1

        except Exception as e:
            raise RuntimeError(f"执行错误 (动作 {pc}): {e}")

if __name__ == "__main__":
    test_code = """
FUNC test
    PRINT "hello world"
ENDFUNC

FUNC test2
    PRINT "hello world2"
ENDFUNC

CALL test
CALL test2
"""

    try:
        actions = compile_code(test_code)
        print(f"编译成功，生成 {len(actions)} 个动作")
        run(actions)
    except ExceptionGroup as eg:
        print("编译错误：")
        for e in eg.exceptions:
            print(f"   - {e}")
    except Exception as e:
        print(f"错误：{e}")
