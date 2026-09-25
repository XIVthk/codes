from __future__ import annotations
import re
from typing import Any, Never

DEBUG = False

def debug_print(*args):
    if DEBUG:
        print(*args)


class ParseError(Exception):
    def __init__(self, message: str, line: int = None, col: int = None):
        self.message = message
        self.line = line
        self.col = col
        if line is not None:
            full_msg = f"Line {line}"
            if col is not None:
                full_msg += f", column {col}"
            full_msg += f": {message}"
        else:
            full_msg = message
        super().__init__(full_msg)


class DConfObject:
    def __init__(self, data: dict, fields: list[str] = None):
        self._data = data
        self._fields = fields or list(data.keys())
    
    def __getitem__(self, key):
        if isinstance(key, int):
            if key < len(self._fields):
                field_name = self._fields[key]
                return self._data.get(field_name)
            raise IndexError(f"Index {key} out of range")
        elif isinstance(key, str):
            return self._data.get(key)
        raise TypeError(f"Key must be str or int, got {type(key)}")
    
    def __setitem__(self, key, value):
        if isinstance(key, int):
            if key < len(self._fields):
                field_name = self._fields[key]
                self._data[field_name] = value
            else:
                raise IndexError(f"Index {key} out of range")
        elif isinstance(key, str):
            self._data[key] = value
        else:
            raise TypeError(f"Key must be str or int, got {type(key)}")
    
    def __contains__(self, key):
        return key in self._data
    
    def get(self, key, default=None):
        return self._data.get(key, default)
    
    def keys(self):
        return self._data.keys()
    
    def values(self):
        return self._data.values()
    
    def items(self):
        return self._data.items()
    
    def __repr__(self):
        return f"DConfObject({self._data})"
    
    def to_dict(self):
        return self._data.copy()


class DConfParser:
    def __init__(self):
        self.public = {}
        self.__private = {}
        self.text = ""
        self.structs = {}
        self.instances = {}
        self.defaults = {}
        self.functions = {}
        self._lines = []
        self._line_num = 0

    def _get_location(self, idx: int) -> tuple[int, int]:
        line_num = self._line_num
        if idx < len(self._lines) and line_num > 0:
            line_content = self._lines[line_num - 1]
            col = idx + 1
            return line_num, col
        return line_num, None

    def _error(self, message: str, line_idx: int = None, col: int = None) -> None:
        if line_idx is None:
            line_idx = self._line_num
        raise ParseError(message, line_idx, col)

    def parse_stream(self, stream):
        content = stream.read()
        return self.parse_string(content)

    def parse_file(self, filepath: str) -> DConfParser:
        with open(filepath, 'r', encoding='utf-8') as f:
            return self.parse_stream(f)

    def parse_string(self, content: str) -> DConfParser:
        self._lines = content.splitlines()
        i = 0
        n = len(self._lines)

        while i < n:
            raw_line = self._lines[i]
            self._line_num = i + 1
            line = raw_line.strip()
            if not line:
                i += 1
                continue

            try:
                if line.startswith("public . {"):
                    i, self.public = self._parse_public_block(i)
                elif line.startswith("private . {"):
                    i, self.__private = self._parse_public_block(i)
                elif line.startswith("text . {"):
                    i, self.text = self._parse_text_block(i)
                elif line.startswith("#inc struct"):
                    i, struct_def = self._parse_struct(i)
                    self.structs[struct_def["name"]] = struct_def
                elif line.startswith("#inc function"):
                    i, func_def = self._parse_function(i)
                    if func_def:
                        self.functions[func_def["name"]] = func_def
                else:
                    default_match = re.match(r'^default\s+"([^"]+)"\s*{', line)
                    if default_match:
                        inst_name = default_match.group(1)
                        i, data = self._parse_default_block(i)
                        if data:
                            self.defaults[inst_name] = data
                        continue

                    struct_match = re.match(
                        r'^(\w+)\s+"([^"]+)"(?:\s+@([\w\s]+))?\s*{', line
                    )
                    if struct_match:
                        type_name = struct_match.group(1)
                        inst_name = struct_match.group(2)
                        inheritance = struct_match.group(3)
                        if type_name in self.structs:
                            i, data, fields = self._parse_struct_instance(i, type_name, inheritance)
                            obj = DConfObject(data, fields)
                            self.instances.setdefault(type_name, {})[inst_name] = obj
                        else:
                            i = self._skip_braced_block(i)
                        continue

                    i += 1
            except ParseError:
                raise
            except Exception as e:
                self._error(str(e), i + 1)

        return self

    def _parse_public_block(self, start_idx: int) -> tuple[int, dict]:
        i = start_idx + 1
        data = {}
        while i < len(self._lines):
            line = self._lines[i].strip()
            if line == "}":
                return i + 1, data
            match = re.match(r"(\w+):\s*(\w+)\s*=\s*(.+?)(?:,?)$", line)
            if match:
                key, typ, val = match.groups()
                data[key] = self._parse_value(val.strip().rstrip(","), typ, i)
            i += 1
        self._error("Unclosed block", start_idx)
        return i, data

    def _parse_text_block(self, start_idx: int) -> tuple[int, str]:
        i = start_idx + 1
        content = []
        while i < len(self._lines):
            line = self._lines[i]
            if line.strip() == "}":
                return i + 1, "\n".join(content)
            content.append(line)
            i += 1
        self._error("Unclosed text block", start_idx)
        return i, "\n".join(content)

    def _parse_struct(self, start_idx: int) -> tuple[int, dict]:
        header = self._lines[start_idx].strip()
        name_match = re.match(r"#inc\s+struct\s+(\w+)(?:\s+@([\w\s]+))?", header)
        if not name_match:
            self._error(f"Invalid struct definition: {header}", start_idx)
        name = name_match.group(1)
        bases = name_match.group(2).split() if name_match.group(2) else []

        i = start_idx + 1
        fields = {}
        constraints = {}
        defaults = {}
        inherit_all = False
        nested_structs = {}

        while i < len(self._lines):
            line = self._lines[i].strip()
            if line == "}":
                return i + 1, {
                    "name": name,
                    "bases": bases,
                    "fields": fields,
                    "constraints": constraints,
                    "defaults": defaults,
                    "inherit_all": inherit_all,
                    "nested_structs": nested_structs,
                }

            if line.strip() == "*," or line.strip() == "*":
                inherit_all = True
                i += 1
                continue

            nested_match = re.match(r'(\w+):\s*struct\s*=\s*(\w+)\s+"([^"]+)"\s*{', line)
            if nested_match:
                fname, struct_type, inst_name = nested_match.groups()
                nested_i, nested_data, nested_fields = self._parse_inline_nested_struct(i, struct_type, inst_name)
                fields[fname] = "struct"
                nested_structs[fname] = {
                    "type": struct_type,
                    "data": DConfObject(nested_data, nested_fields),
                    "fields": nested_fields
                }
                i = nested_i
                continue

            match = re.match(
                r"(\w+):\s*(\w+)(?:\s+(![\w*+?]+))?(?:\s*=\s*(.+?))?(?:,?)$", line
            )
            if match:
                fname, ftype, constr, default_str = match.groups()
                fields[fname] = ftype
                if constr:
                    constraints[fname] = constr
                if default_str:
                    defaults[fname] = self._parse_value(
                        default_str.strip().rstrip(","), ftype, i
                    )
            i += 1
        self._error(f"Unclosed struct '{name}'", start_idx)
        return i, {}

    def _parse_inline_nested_struct(
        self, start_idx: int, struct_type: str, inst_name: str
    ) -> tuple[int, dict, list[str]]:
        line = self._lines[start_idx].strip()
        brace_start = line.find('{')
        if brace_start == -1:
            self._error(f"Expected '{{' for nested struct '{inst_name}'", start_idx)

        brace_depth = 0
        end_pos = brace_start
        for idx, ch in enumerate(line[brace_start:], start=brace_start):
            if ch == '{':
                brace_depth += 1
            elif ch == '}':
                brace_depth -= 1
                if brace_depth == 0:
                    end_pos = idx
                    break
        else:
            self._error(f"Unclosed nested struct '{inst_name}'", start_idx)
        
        inner = line[brace_start+1:end_pos].strip()
        
        raw_values = []
        vals = self._split_line_values_with_star(inner, start_idx)
        for v in vals:
            raw_values.append(v)
        
        struct_def = self.structs.get(struct_type, {})
        if not struct_def:
            self._error(f"Unknown struct type '{struct_type}' for nested instance", start_idx)
        
        field_names = list(struct_def.get('fields', {}).keys())
        field_defaults = struct_def.get('defaults', {})
        
        result = {}
        for i, val in enumerate(raw_values):
            if i < len(field_names):
                result[field_names[i]] = val
        
        for fname, default_val in field_defaults.items():
            if fname not in result:
                result[fname] = default_val
        
        return start_idx + 1, result, field_names

    def _parse_function(self, start_idx: int) -> tuple[int, dict]:
        header = self._lines[start_idx].strip()
        name_match = re.search(r"#inc\s+function\s+(\w+)\s*<([^>]+)>\s*{", header)
        if not name_match:
            name_match = re.search(r"#inc\s+function\s+(\w+)\s*{", header)
            if not name_match:
                return self._skip_braced_block(start_idx), {}
            name = name_match.group(1)
            params = []
        else:
            name = name_match.group(1)
            params_str = name_match.group(2)
            params = []
            for param in params_str.split(","):
                param = param.strip()
                p_match = re.match(r"(\w+):\s*(\w+)", param)
                if p_match:
                    params.append({"name": p_match.group(1), "type": p_match.group(2)})

        i = start_idx
        while i < len(self._lines) and '{' not in self._lines[i]:
            i += 1
        if i >= len(self._lines):
            self._error(f"Expected '{{' for function '{name}'", start_idx)

        brace_depth = 0
        body_lines = []
        for j in range(i, len(self._lines)):
            line = self._lines[j]
            if brace_depth == 0 and '{' in line:
                brace_depth += line.count('{') - line.count('}')
                body_lines.append(line)
            elif brace_depth > 0:
                body_lines.append(line)
                brace_depth += line.count('{') - line.count('}')
                if brace_depth == 0:
                    end_idx = j + 1
                    break
        else:
            self._error(f"Unclosed function '{name}'", start_idx)

        if len(body_lines) >= 2:
            inner_lines = body_lines[1:-1]
        else:
            inner_lines = []

        ret_expr = None
        for inner_line in inner_lines:
            line = inner_line.strip()
            if line.startswith("ret"):
                ret_match = re.match(r"ret\s+(.+)", line)
                if ret_match:
                    ret_expr = ret_match.group(1).strip()
                    break
        
        if ret_expr is None:
            self._error(f"Function '{name}' missing 'ret' statement", start_idx)

        return end_idx, {
            "name": name,
            "params": params,
            "ret_expr": ret_expr,
        }

    def _get_all_fields_with_constraints(
        self, struct_name: str
    ) -> tuple[list[str], dict[str, Any], dict[str, str], dict[str, Any]]:
        if struct_name not in self.structs:
            self._error(f"Unknown struct type '{struct_name}'")

        struct = self.structs[struct_name]
        all_fields = []
        all_defaults = {}
        all_constraints = {}
        all_nested = {}

        for base in struct["bases"]:
            base_fields, base_defaults, base_constraints, base_nested = (
                self._get_all_fields_with_constraints(base)
            )
            for f in base_fields:
                if f not in all_fields:
                    all_fields.append(f)
            all_defaults.update(base_defaults)
            all_constraints.update(base_constraints)
            all_nested.update(base_nested)

        for fname, ftype in struct["fields"].items():
            if fname not in all_fields:
                all_fields.append(fname)
            if fname in struct["defaults"]:
                all_defaults[fname] = struct["defaults"][fname]
            if fname in struct["constraints"]:
                all_constraints[fname] = struct["constraints"][fname]

        all_nested.update(struct.get("nested_structs", {}))

        return all_fields, all_defaults, all_constraints, all_nested

    def _parse_nested_instance(
        self, start_idx: int, struct_type: str
    ) -> tuple[int, dict, list[str]]:
        i = start_idx
        while i < len(self._lines) and '{' not in self._lines[i]:
            i += 1
        if i >= len(self._lines):
            self._error(f"Expected '{{' for nested struct of type '{struct_type}'", start_idx)

        current_line = self._lines[i]
        brace_start = current_line.find('{')
        
        if brace_start != -1:
            brace_depth = 0
            end_pos = brace_start
            for idx, ch in enumerate(current_line[brace_start:], start=brace_start):
                if ch == '{':
                    brace_depth += 1
                elif ch == '}':
                    brace_depth -= 1
                    if brace_depth == 0:
                        end_pos = idx
                        break
            
            if end_pos > brace_start:
                inner = current_line[brace_start+1:end_pos].strip()
                raw_values = []
                vals = self._split_line_values_with_star(inner, i)
                for v in vals:
                    raw_values.append(v)
                
                struct_def = self.structs.get(struct_type, {})
                if not struct_def:
                    self._error(f"Unknown struct type '{struct_type}'", i)
                
                field_names = list(struct_def.get('fields', {}).keys())
                field_defaults = struct_def.get('defaults', {})
                
                result = {}
                for idx, val in enumerate(raw_values):
                    if idx < len(field_names):
                        result[field_names[idx]] = val
                
                for fname, default_val in field_defaults.items():
                    if fname not in result:
                        result[fname] = default_val
                
                return i + 1, result, field_names
        
        brace_depth = 0
        block_lines = []
        for j in range(i, len(self._lines)):
            line = self._lines[j]
            if brace_depth == 0 and '{' in line:
                brace_depth += line.count('{') - line.count('}')
                block_lines.append(line)
            elif brace_depth > 0:
                block_lines.append(line)
                brace_depth += line.count('{') - line.count('}')
                if brace_depth == 0:
                    end_idx = j + 1
                    break
        else:
            self._error(f"Unclosed nested struct of type '{struct_type}'", i)

        if len(block_lines) >= 2:
            inner_lines = block_lines[1:-1]
        else:
            inner_lines = []

        raw_values = []
        for raw_line in inner_lines:
            line = raw_line.strip()
            if not line:
                continue
            if line.endswith(','):
                line = line[:-1].rstrip()
            vals = self._split_line_values_with_star(line, j)
            for v in vals:
                raw_values.append(v)

        struct_def = self.structs.get(struct_type, {})
        if not struct_def:
            self._error(f"Unknown struct type '{struct_type}'", i)
        
        field_names = list(struct_def.get('fields', {}).keys())
        field_defaults = struct_def.get('defaults', {})
        
        result = {}
        for idx, val in enumerate(raw_values):
            if idx < len(field_names):
                result[field_names[idx]] = val
        
        for fname, default_val in field_defaults.items():
            if fname not in result:
                result[fname] = default_val
        
        return end_idx, result, field_names

    def _parse_struct_instance(
        self,
        start_idx: int,
        type_name: str,
        inheritance: str | None,
    ) -> tuple[int, dict, list[str]]:
        i = start_idx
        while i < len(self._lines) and "{" not in self._lines[i]:
            i += 1
        if i >= len(self._lines):
            self._error(f"Expected '{{' for instance of '{type_name}'", start_idx)

        brace_depth = 0
        block_lines = []
        for j in range(i, len(self._lines)):
            line = self._lines[j]
            if brace_depth == 0 and "{" in line:
                brace_depth += line.count("{") - line.count("}")
                block_lines.append(line)
            elif brace_depth > 0:
                block_lines.append(line)
                brace_depth += line.count("{") - line.count("}")
                if brace_depth == 0:
                    end_idx = j + 1
                    break
        else:
            self._error(f"Unclosed instance of '{type_name}'", i)

        if len(block_lines) >= 2:
            inner_lines = block_lines[1:-1]
        else:
            inner_lines = []

        raw_values = []
        j = 0
        while j < len(inner_lines):
            raw_line = inner_lines[j].strip()
            if not raw_line:
                j += 1
                continue
            if raw_line.endswith(","):
                raw_line = raw_line[:-1].rstrip()

            nested_match = re.match(r'^(\w+)\s+"([^"]+)"\s*{', raw_line)
            if nested_match:
                nested_type = nested_match.group(1)
                nested_i, nested_data, nested_fields = self._parse_nested_instance(
                    start_idx + j, nested_type
                )
                raw_values.append(DConfObject(nested_data, nested_fields))
                lines_consumed = nested_i - (start_idx + j)
                j += lines_consumed
                continue

            if ":" in raw_line and not raw_line.startswith('"'):
                parts = raw_line.split(":", 1)
                key = parts[0].strip()
                val_str = parts[1].strip()
                raw_values.append(("keyval", key, val_str))
                j += 1
                continue

            vals = self._split_line_values_with_star(raw_line, start_idx + j)
            for v in vals:
                raw_values.append(v)
            j += 1

        field_names, field_defaults, field_constraints, field_nested = (
            self._get_all_fields_with_constraints(type_name)
        )

        result = {}
        val_idx = 0
        field_idx = 0
        total_fields = len(field_names)

        while field_idx < total_fields:
            fname = field_names[field_idx]
            constraint = field_constraints.get(fname, "")
            is_nested = fname in field_nested
            is_vararg = (constraint in ("!*", "!+") or 
                        (constraint.startswith("!") and constraint[1:].isdigit())) and not is_nested

            keyval_found = None
            kv_val = None
            for idx, item in enumerate(raw_values):
                if isinstance(item, tuple) and len(item) == 3 and item[0] == "keyval" and item[1] == fname:
                    keyval_found = idx
                    kv_val = item[2]
                    break

            if keyval_found is not None:
                result[fname] = self._parse_value(kv_val, "any", start_idx)
                raw_values.pop(keyval_found)
                field_idx += 1
                continue

            if is_nested:
                if val_idx < len(raw_values) and isinstance(raw_values[val_idx], DConfObject):
                    result[fname] = raw_values[val_idx]
                    val_idx += 1
                else:
                    nested_info = field_nested[fname]
                    result[fname] = nested_info["data"]
                field_idx += 1
                continue

            if is_vararg:
                varargs = []
                while val_idx < len(raw_values):
                    val = raw_values[val_idx]
                    if val == "__END_VARARG__":
                        val_idx += 1
                        break
                    if val == "__SKIP__":
                        if constraint == "!*":
                            pass
                        elif constraint == "!+":
                            self._error(f"Field '{fname}' requires at least one value", start_idx)
                    else:
                        varargs.append(val)
                    val_idx += 1

                if constraint == "!+":
                    if len(varargs) == 0:
                        self._error(f"Field '{fname}' requires at least one value", start_idx)
                elif constraint.startswith("!") and constraint[1:].isdigit():
                    expected = int(constraint[1:])
                    if len(varargs) != expected:
                        self._error(
                            f"Field '{fname}' requires exactly {expected} values, got {len(varargs)}",
                            start_idx
                        )

                result[fname] = varargs if varargs else None
            else:
                if val_idx < len(raw_values):
                    val = raw_values[val_idx]
                    if val == "__SKIP__":
                        result[fname] = field_defaults.get(fname)
                    else:
                        result[fname] = val
                    val_idx += 1
                else:
                    result[fname] = field_defaults.get(fname)

                if result[fname] is None and fname not in field_defaults:
                    result[fname] = None

            field_idx += 1

        if inheritance:
            base_names = inheritance.split()
            for base in base_names:
                _, base_defaults, _, _ = self._get_all_fields_with_constraints(base)
                for fname, val in base_defaults.items():
                    if fname not in result or result[fname] is None:
                        result[fname] = val

        return end_idx, result, field_names

    def _split_line_values_with_star(self, line: str, line_idx: int) -> list[Any]:
        values = []
        current = []
        in_quotes = False
        i = 0
        n = len(line)

        while i < n:
            ch = line[i]

            if ch == '.' and i + 2 < n and line[i:i+3] == '...':
                if not in_quotes:
                    if current:
                        val_str = ''.join(current).strip()
                        if val_str:
                            if val_str == '*':
                                values.append('__SKIP__')
                            else:
                                values.append(self._parse_value(val_str, 'any', line_idx))
                        current = []
                    i += 3
                    if i < n and line[i] == ',':
                        i += 1
                    values.append('__END_VARARG__')
                    continue
                else:
                    current.append(ch)
                    i += 1
                    continue

            if ch == '"':
                in_quotes = not in_quotes
                current.append(ch)
            elif ch == ',' and not in_quotes:
                val_str = ''.join(current).strip()
                if val_str:
                    if val_str == '*':
                        values.append('__SKIP__')
                    else:
                        values.append(self._parse_value(val_str, 'any', line_idx))
                current = []
            else:
                current.append(ch)
            i += 1

        if current:
            val_str = ''.join(current).strip()
            if val_str:
                if val_str == '*':
                    values.append('__SKIP__')
                else:
                    values.append(self._parse_value(val_str, 'any', line_idx))
        return values

    def _parse_default_block(self, start_idx: int) -> tuple[int, dict]:
        i = start_idx
        while i < len(self._lines) and "{" not in self._lines[i]:
            i += 1
        if i >= len(self._lines):
            self._error("Expected '{' for default block", start_idx)

        brace_depth = 0
        block_lines = []
        for j in range(i, len(self._lines)):
            line = self._lines[j]
            if brace_depth == 0 and "{" in line:
                brace_depth += line.count("{") - line.count("}")
                block_lines.append(line)
            elif brace_depth > 0:
                block_lines.append(line)
                brace_depth += line.count("{") - line.count("}")
                if brace_depth == 0:
                    end_idx = j + 1
                    break
        else:
            self._error("Unclosed default block", i)

        if len(block_lines) >= 2:
            inner_lines = block_lines[1:-1]
        else:
            inner_lines = []

        data = {}
        for raw_line in inner_lines:
            line = raw_line.strip()
            if not line:
                continue
            if line.endswith(","):
                line = line[:-1].rstrip()
            match = re.match(r"(\w+):\s*(\w+)\s*=\s*(.+)$", line)
            if match:
                key, typ, val = match.groups()
                data[key] = self._parse_value(val.strip(), typ, i)
        return end_idx, data

    def _parse_value(self, value_str: str, _type: str, line_idx: int) -> Any:
        value_str = value_str.strip()
        if value_str.startswith('"') and value_str.endswith('"'):
            return value_str[1:-1]
        if value_str.lower() == "true":
            return True
        if value_str.lower() == "false":
            return False
        if value_str.lower() == "null":
            return None
        try:
            if '.' in value_str:
                return float(value_str)
            return int(value_str)
        except ValueError:
            self._error(f"Invalid value '{value_str}' for type '{_type}'", line_idx)
            return value_str

    def _skip_braced_block(self, start_idx: int) -> int:
        i = start_idx
        brace_depth = 0
        started = False
        while i < len(self._lines):
            line = self._lines[i]
            if not started and "{" in line:
                started = True
            if started:
                brace_depth += line.count("{") - line.count("}")
                if brace_depth == 0:
                    return i + 1
            i += 1
        return i

    def get_public(self) -> dict:
        return self.public

    def get_private(self) -> Never:
        raise PermissionError("Private arguments are protected.")

    def get_struct(self, name: str) -> dict:
        return self.instances.get(name, {})

    def get_default(self, name: str) -> DConfObject | None:
        return self.defaults.get(name)

    def call(self, func_name: str, *args, **kwargs) -> Any:
        if func_name not in self.functions:
            raise AttributeError(f"Function '{func_name}' not defined")
        func = self.functions[func_name]
        ret_expr = func["ret_expr"]
        if not ret_expr:
            return None

        parts = [p.strip() for p in ret_expr.split(",")]
        results = []
        for part in parts:
            if "." in part:
                obj_path = part.split(".")
                obj_name = obj_path[0]
                attr_path = ".".join(obj_path[1:])

                obj = None
                for param, arg in zip(func["params"], args):
                    if param["name"] == obj_name:
                        obj = arg
                        break
                if obj is None:
                    for struct_name, instances in self.instances.items():
                        if obj_name in instances:
                            obj = instances[obj_name]
                            break
                if obj is None and obj_name == "private":
                    raise PermissionError("Private arguments cannot be accessed")
                if obj is None:
                    results.append(None)
                else:
                    current = obj
                    for attr in attr_path.split("."):
                        if isinstance(current, DConfObject):
                            current = current.get(attr)
                        elif isinstance(current, dict):
                            current = current.get(attr)
                        else:
                            current = None
                            break
                    results.append(current)
            else:
                if part in kwargs:
                    results.append(kwargs[part])
                elif args:
                    found = False
                    for param, arg in zip(func["params"], args):
                        if param["name"] == part:
                            results.append(arg)
                            found = True
                            break
                    if not found:
                        for struct_name, instances in self.instances.items():
                            if part in instances:
                                results.append(instances[part])
                                found = True
                                break
                        if not found:
                            results.append(part)
                else:
                    results.append(part)

        return results[0] if len(results) == 1 else tuple(results)

    def __getitem__(self, key: str) -> DConfObject | None:
        return self.defaults.get(key)


def load_dconf(filepath: str) -> DConfParser:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    parser = DConfParser()
    return parser.parse_string(content)


def load_dconf_from_string(content: str) -> DConfParser:
    parser = DConfParser()
    return parser.parse_string(content)