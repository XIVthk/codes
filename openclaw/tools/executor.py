#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
命令执行模块
=======================
说明：
    当AI输出命令时，会在此处调用命令，至于对工作环境 (即cwd) 的管理还是留给另一个模块吧
    并没有做安全检查，因为AI输出的命令会先被人工检查一遍，确认 (enter y) 之后再执行，所以没有必要禁止一些命令的运行
    工作状态: Done
"""
import subprocess as subp
from dataclasses import dataclass
from enum import Enum
import platform


class RunMode(Enum):
    SAFETY = False
    STRICT = True

@dataclass
class CommandResult:
    success: bool
    returncode: int 
    stdout: str | None = None
    stderr: str | None = None
    error: Exception | None = None

class Commandor:
    def __init__(self):
        self.last_result: CommandResult | None = None
        self.is_windows = "win" in platform.system().lower()

    def execute(
        self,
        cmd: str | list[str],
        capture_output: bool = True,
        check: RunMode | bool = False,
        re_raise: bool = False,
        **kwargs
    ) -> CommandResult:
        """
        执行命令并返回结果

        Args:
            cmd: 要执行的命令，字符串或列表
            capture_output: 是否捕获输出，默认True
            check: 是否检查返回码，默认False (RunMode.SAFETY)
            re_raise: 是否重新抛出异常，默认False
                - 如果为True，命令失败时会重新抛出异常
                - 如果为False，命令失败时返回包含错误信息的CommandResult
            **kwargs: 其他参数，参考subprocess.run
        """
        if not isinstance(cmd, (str, list)): 
            raise TypeError("Expected str or list, got", type(cmd))
        import shlex
        cmd = shlex.split(cmd) if isinstance(cmd, str) else cmd
        
        if self.is_windows:
            if kwargs.get("shell") is None:
                kwargs["shell"] = True
        else:
            if kwargs.get("shell") is None:
                kwargs["shell"] = False

        run_kwargs = {
            "capture_output": capture_output,
            "text": True,
            "check": check if isinstance(check, bool) else check.value,
            **kwargs
        }

        try:
            result = subp.run(cmd, **run_kwargs)

            cmd_result = CommandResult(
                success=result.returncode == 0,
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr
            )

            if re_raise and result.returncode != 0:
                raise subp.CalledProcessError(
                    result.returncode, cmd, 
                    output=result.stdout, 
                    stderr=result.stderr
                )
            
        except subp.CalledProcessError as e:
            cmd_result = CommandResult(
                success=False,
                returncode=e.returncode,
                error=e,
                stdout=e.output,
                stderr=e.stderr
            )
            if re_raise:
                raise e
            
        except FileNotFoundError as e:
            if re_raise:
                raise e
            else:
                cmd_result = CommandResult(
                    success=False,
                    returncode=1,
                    error=e,
                    stderr=f"Command not found: {cmd[0]}"
                )
            
        except Exception as e:
            if re_raise:
                raise e
            else:
                cmd_result = CommandResult(
                    success=False,
                    returncode=1,
                    error=e
                )
        
        self.last_result = cmd_result
        return cmd_result
    
    def __call__(
            self,
            cmd: str | list[str],
            mode: RunMode | bool = RunMode.STRICT,
            re_raise: bool = False,
            **kwargs
        ) -> CommandResult:
        """
        执行命令并返回结果

        Args:
            cmd: 要执行的命令，字符串或列表
            mode: 执行模式，默认Runmode.STRICT (True)
            re_raise: 是否重新抛出异常，默认False
                - 如果为True，命令失败时会重新抛出异常
                - 如果为False，命令失败时返回包含错误信息的CommandResult
            **kwargs: 其他参数，参考subprocess.run
        
        Examples:
            >>> cmd = Commandor()
            >>> print(cmd("echo Hello World"))
            CommandResult(success=True, returncode=0, stdout='Hello World\n', stderr='', error=None)

            >>> print(cmd("This Command Not Exist", check=True, re_raise=True))
            Traceback (most recent call last):
            ...
            subprocess.CalledProcessError: Command '['This', 'Command', 'Not', 'Exist']' returned non-zero exit status 1.

            >>> print(cmd(["python", "-c", "print('Hello World')"], check=True, shell=False).stdout)
            Hello World
        
        """
        if not isinstance(mode, (RunMode, bool)): raise TypeError("Expected RunMode or bool, got", type(mode))
        if kwargs.get("check") is not None: mode = RunMode(kwargs["check"]) if isinstance(kwargs["check"], bool) else RunMode[kwargs["check"]]; del kwargs["check"]
        return self.execute(cmd, check=mode.value, re_raise=re_raise, **kwargs)

if __name__ == "__main__":
    cmd = Commandor()
    print(cmd("This Command Not Exist", check=True, re_raise=False))
