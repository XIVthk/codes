# *-* coding: utf-8 *-*
from __future__ import annotations
import datetime
import json
import os
from typing import Any
import re

class NonConnection(Exception): pass
def is_connected(func):
    def wrapper(self, *args, **kwargs):
        if not self.status:
            raise NonConnection("Table not connected")
        return func(self, *args, **kwargs)
    return wrapper

class Table:
    def __init__(self, file_name: str | bytes, table_name: str | None = None, fields: dict[str, type] | None = None):
        self.file_name = file_name
        self.fields = fields
        self.table_name = table_name
        self.status = False  # False: not connected, True: connected/created
        self.length = 0

    def create_table(self):
        with open(f"{self.file_name}.mdb", 'w') as f:
            _meta = {
                "create_time": str(datetime.datetime.now()),
                "version": 1,
                "table_name": self.table_name,
                "fields": [{"type": t, "name": name} for name, t in self.fields.items()],
                "length": self.length,
            }
            f.write(json.dumps(_meta, ensure_ascii=False, indent=4))
        self.status = True
    
    def connect_table(self):
        # try to FIND original table file
        if not os.path.exists(f"{self.file_name}.mdb"):
            print(f"Table {self.file_name} not found")
            # try to FIND a table
            tables = [f for f in os.listdir('.') if f.endswith('.mdb')]
            if not tables:
                raise FileNotFoundError("No table found")
            tables.sort(); table = tables[0]
            print(f"Table Changing: {self.file_name} -> {table}")
            self.file_name = table
        else:
            table = self.file_name
            print(f"Table Found: {table}")
        
        # try to connect table
        with open(f"{table}.mdb", 'r') as f:
            _meta = json.load(f)["meta"]
            self.table_name = _meta["table_name"]
            self.fields = {_["name"]: _["type"] for _ in _meta["fields"]}
            self.length = _meta["length"]
        self.status = True
    
    @is_connected
    def add_data(self, data: list[tuple[str, ...]] | dict[str, Any]):
        dt = {}
        if type(data) == list:
            for item in data:  # a single field
                if not type(item) == tuple:
                    raise TypeError("Data must be a tuple")
                if not type(item[0]) == str:
                    raise TypeError("Data[0] must be a string")
                if item[0] not in self.fields:
                    raise ValueError(f"Data[0] {item[0]} not found in table {self.table_name}")
                if not isinstance(item[1], self.fields[item[0]]):
                    raise TypeError(f"Data[1] must be a(n) {self.fields[item[0]]}")
                dt[item[0]] = item[1]
        else:
            for name, val in data.items():
                # Compliance check
                if name not in self.fields:
                    raise ValueError(f"Data {name} not found in table {self.table_name}")
                if not isinstance(val, self.fields[name]):
                    raise TypeError(f"Data {name} must be a(n) {self.fields[name]}")
            dt = data
        for name in self.fields:
            if name not in dt:
                dt[name] = None  # default value
        if "id" not in dt:
            dt["id"] = self.length + 1
        self.length += 1
        with open(f"{self.file_name}.mdb", 'a') as f:
            f.write(json.dumps(dt, ensure_ascii=False, indent=4) + "\n")
    
    insert = add_data

    def __iter__(self):
        with open(f"{self.file_name}.mdb", 'r') as f:
            for line in f:
                yield json.loads(line)

    @is_connected
    def select(self, expr: C | str, columns: str = "*"):
        """Select data from table"""
        try: expr = C(expr)
        except TypeError:
            raise TypeError("Expr must be a C(condition) object")
        condition = expr.exprs
        for row in self:
            if condition.exec(row):
                if columns == "*":
                    yield row
                else:
                    yield {name: row[name] for name in columns.split(",")}
    
    @is_connected
    def delete(self, expr: C | str):
        """Delete data from table"""
        try: expr = C(expr)
        except TypeError:
            raise TypeError("Expr must be a C(condition) object")
        condition = expr.exprs
        with open(f"{self.file_name}.mdb", 'w') as f:
            for row in self:
                if not condition.exec(row):
                    f.write(json.dumps(row, ensure_ascii=False, indent=4) + "\n")
        self.length = len(self)


class C:
    """Condition class with DNF support using &= and |= operators."""
    def __init__(self, expr=None):
        if expr is None:
            self.ors = [] 
        elif isinstance(expr, str):
            self.ors = [[expr.strip()]] 
        elif isinstance(expr, C):
            self.ors = [clause[:] for clause in expr.ors] 
        else:
            raise TypeError("C expects a string, another C, or None")

    def __iand__(self, other):
        if isinstance(other, str):
            other = C(other)
        if not isinstance(other, C):
            return NotImplemented
        new_ors = []
        for a in self.ors:
            for b in other.ors:
                new_ors.append(a + b)
        self.ors = new_ors
        return self

    def __and__(self, other):
        new_c = C()
        new_c.ors = [a[:] for a in self.ors]
        new_c &= other
        return new_c

    def __ior__(self, other):
        if isinstance(other, str):
            other = C(other)
        if not isinstance(other, C):
            return NotImplemented
        self.ors.extend(other.ors)
        return self

    def __or__(self, other):
        new_c = C()
        new_c.ors = [a[:] for a in self.ors]
        new_c |= other
        return new_c

    def _eval_expr(self, expr: str, row: dict) -> bool:
        ops = ["==", "!=", "<=", ">=", "<", ">", "not in", "is not", "is", "in"]
        for op in ops:
            if op in expr:
                left, right = expr.split(op, 1)
                left = left.strip()
                right = right.strip()
                return eval(f"row[{left!r}] {op} {right}",
                            {"row": row, "__builtins__": None}, {})
        raise ValueError(f"No valid operator found in expression: {expr}")

    def exec(self, row: dict[str, Any]) -> bool:
        for and_clause in self.ors:
            if all(self._eval_expr(expr, row) for expr in and_clause):
                return True
        return False

    def __repr__(self):
        parts = []
        for clause in self.ors:
            if len(clause) == 1:
                parts.append(clause[0])
            else:
                parts.append("[" + ", ".join(clause) + "]")
        return "(" + ", ".join(parts) + ")"

    def __bool__(self):
        return bool(self.ors)