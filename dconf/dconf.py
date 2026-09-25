from __future__ import annotations
from enum import Enum
from typing import Any, Optional
from dconf_parser import load_dconf_from_string, DConfParser, ParseError


class Type(Enum):
    STRUCT = "struct"
    FUNCTION = "function"


class DConf:
    def __init__(self):
        self.public = {}
        self.__private = {}
        self.text = ""
        self._structs = []
        self._instances = []
        self._functions = []
        self._defaults = []
        self._text_lines = []

    def set_public(self, key: str, value: Any, value_type: str = "str") -> DConf:
        self.public[key] = (value_type, value)
        return self

    def set_private(self, key: str, value: Any, value_type: str = "str") -> DConf:
        self.__private[key] = (value_type, value)
        return self

    def set_text(self, text: str) -> DConf:
        self.text = text
        return self

    def add_text_line(self, line: str) -> DConf:
        self._text_lines.append(line)
        return self

    def add_struct(self, name: str, fields: dict, bases: list = None, inherit_all: bool = False) -> DConf:
        """
        添加结构体定义
        Args:
            name: 结构体名称
            fields: {字段名: (类型, 约束, 默认值)} 
            bases: 基础结构体名称列表
            inherit_all: 是否继承所有字段（默认 False）
        
        约束可选: '!*' (0次或多次), '!+' (1次或多次), '!?' (0次或1次), '!数字' (固定次数)
        Example (fields):
            {"name": ("str", None, None), 
             "age": ("int", None, 18), 
             "tags": ("str", "!*", None)} 
        """
        self._structs.append({
            "name": name,
            "bases": bases or [],
            "fields": fields,
            "inherit_all": inherit_all
        })
        return self

    def add_instance(self, struct_name: str, instance_name: str, args: list, inheritance: list = None) -> DConf:
        """
        添加结构体实例
        Args:
            struct_name: 结构体名称
            instance_name: 实例名称
            args: 位置参数列表，支持特殊标记：
                - '*' : 使用默认值（跳过当前字段）
                - '...' : 变长字段结束标记
                - None : 表示 null
                - 字符串: 自动加引号
        
        Example (args):
            ["Zhang San", 25, "zhang@example.com"]
            
            ["Li Si", "*", "13900139000"]
            
            ["Wang Wu", 28, "wang@example.com", 1001, "Engineering", "tag1", "tag2", "...", "P7"]
            
            ["Zhao Liu", 28, "zhao@example.com", 1001, "Engineering", "...", "P8"]
        """
        self._instances.append({
            "struct_name": struct_name,
            "instance_name": instance_name,
            "args": args,
            "inheritance": inheritance or []
        })
        return self

    def add_function(self, name: str, params: list, ret_expr: str) -> DConf:
        """
        添加函数定义
        Args:
            name: 函数名称
            params: [(参数名, 类型), ...] 如 [("p", "person"), ("q", "info")]
            ret_expr: 返回值表达式，如 "p.name" 或 "p.name, p.age"
        """
        self._functions.append({
            "name": name,
            "params": params,
            "ret_expr": ret_expr
        })
        return self

    def add_default(self, name: str, args: dict, inheritance: list = None) -> DConf:
        """
        添加 default 匿名实例
        Args:
            name: 实例名称
            args: {字段名: (类型, 值)}
            inheritance: 基础结构体名称列表
        """
        self._defaults.append({
            "name": name,
            "args": args,
            "inheritance": inheritance or []
        })
        return self

    def _format_value(self, value: Any, value_type: str) -> str:
        if value is None:
            return "null"
        elif value_type == "str":
            return f'"{value}"'
        elif value_type == "bool":
            return "true" if value else "false"
        else:
            return str(value)

    def _format_fields(self, fields: dict) -> str:
        lines = []
        for fname, (ftype, constraint, default) in fields.items():
            line = f"    {fname}: {ftype}"
            if constraint:
                line += f" {constraint}"
            if default is not None:
                line += f" = {self._format_value(default, ftype)}"
            lines.append(line + ",")
        return "\n".join(lines)

    def _format_args(self, args: list) -> str:
        """格式化位置参数，处理特殊标记"""
        result = []
        for arg in args:
            if arg == "*":
                result.append("*")
            elif arg == "...":
                result.append("...,")
            elif isinstance(arg, str):
                result.append(f'"{arg}"')
            elif arg is None:
                result.append("null")
            else:
                result.append(str(arg))
        return ", ".join(result).rstrip(",")

    def _format_default_args(self, args: dict) -> str:
        lines = []
        for key, (typ, val) in args.items():
            lines.append(f"    {key}: {typ} = {self._format_value(val, typ)},")
        return "\n".join(lines)

    def dump(self) -> str:
        lines = []

        if self.public:
            lines.append("public . {")
            for key, (typ, val) in self.public.items():
                lines.append(f"    {key}: {typ} = {self._format_value(val, typ)},")
            lines.append("}")
            lines.append("")

        if self.__private:
            lines.append("private . {")
            for key, (typ, val) in self.__private.items():
                lines.append(f"    {key}: {typ} = {self._format_value(val, typ)},")
            lines.append("}")
            lines.append("")

        if self.text or self._text_lines:
            lines.append("text . {")
            if self.text:
                lines.append(f"    {self.text}")
            for line in self._text_lines:
                lines.append(f"    {line}")
            lines.append("}")
            lines.append("")

        for struct in self._structs:
            inherit = ""
            if struct["bases"]:
                inherit = " @" + " @".join(struct["bases"])
            if struct["inherit_all"]:
                lines.append(f"#inc struct {struct['name']}{inherit} {{")
                lines.append("    *,")
            else:
                lines.append(f"#inc struct {struct['name']}{inherit} {{")
            lines.append(self._format_fields(struct["fields"]))
            lines.append("}")
            lines.append("")

        for func in self._functions:
            if func["params"]:
                params_str = ", ".join([f"{p[0]}: {p[1]}" for p in func["params"]])
                lines.append(f"#inc function {func['name']} <{params_str}> {{")
            else:
                lines.append(f"#inc function {func['name']} {{")
            lines.append(f"    ret {func['ret_expr']}")
            lines.append("}")
            lines.append("")

        for inst in self._instances:
            inh = ""
            if inst["inheritance"]:
                inh = " @" + " @".join(inst["inheritance"])
            lines.append(f"{inst['struct_name']} \"{inst['instance_name']}\"{inh} {{")
            lines.append(f"    {self._format_args(inst['args'])}")
            lines.append("}")
            lines.append("")

        for default in self._defaults:
            inh = ""
            if default["inheritance"]:
                inh = " @" + " @".join(default["inheritance"])
            lines.append(f"default \"{default['name']}\"{inh} {{")
            lines.append(self._format_default_args(default["args"]))
            lines.append("}")
            lines.append("")

        return "\n".join(lines).rstrip()

    def dump_file(self, filepath: str) -> None:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.dump())

    def load(self, content: str) -> DConf:
        parser = load_dconf_from_string(content)
        self.public = parser.get_public()
        self.text = parser.text
        return self

    def load_file(self, filepath: str) -> DConf:
        with open(filepath, "r", encoding="utf-8") as f:
            return self.load(f.read())

    def get_private(self) -> None:
        raise PermissionError("Private arguments are protected.")


def dconf_from_string(content: str) -> DConf:
    return DConf().load(content)


def dconf_from_file(filepath: str) -> DConf:
    return DConf().load_file(filepath)