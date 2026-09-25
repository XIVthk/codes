from typing import Any, Callable
from enum import Enum


class OutputHolder:
    def __init__(self) -> None:
        self._value: Any = None

    @property
    def value(self) -> Any:
        return self._value

    @value.setter
    def value(self, val: Any) -> None:
        self._value = val

    def __bool__(self) -> bool:
        return self._value is not None


class ErrorHolder:
    def __init__(self) -> None:
        self._error: Exception | None = None

    @property
    def error(self) -> Exception | None:
        return self._error

    @error.setter
    def error(self, exc: Exception) -> None:
        self._error = exc

    def __bool__(self) -> bool:
        return self._error is not None


class _Data:
    __slots__ = ('value',)
    
    def __init__(self, value: Any) -> None:
        self.value = value


class _ActionType(Enum):
    Condition = 1
    Pass = 2


class Action:
    def __init__(self, *, action: _ActionType = _ActionType.Condition) -> None:
        self._action = action

    def _call(self, data: _Data, bindings: dict = None) -> Any:
        raise NotImplementedError(
            f"Subclass {self.__class__.__name__} must implement _call()"
        )

    def __rshift__(self, other: 'Action') -> 'Action':
        if self._action == _ActionType.Condition:
            if isinstance(other, _Branch):
                return _IfElseAction(self, other.true_action, other.false_action)
            else:
                return _IfAction(self, other)
        elif self._action == _ActionType.Pass:
            return _SeqAction(self, other)
        else:
            raise TypeError(f"Unknown action type: {self._action}")

    def __matmul__(self, other: 'Action') -> '_Branch':
        return _Branch(self, other)

    def __and__(self, other: 'Action') -> 'Action':
        return _AndCondition(self, other)

    def __or__(self, other: 'Action') -> 'Action':
        return _OrCondition(self, other)


class _AndCondition(Action):
    def __init__(self, left: Action, right: Action) -> None:
        super().__init__(action=_ActionType.Condition)
        self._left = left
        self._right = right

    def _call(self, data: _Data, bindings: dict = None) -> bool:
        return bool(self._left._call(data, bindings)) and bool(self._right._call(data, bindings))


class _OrCondition(Action):
    def __init__(self, left: Action, right: Action) -> None:
        super().__init__(action=_ActionType.Condition)
        self._left = left
        self._right = right

    def _call(self, data: _Data, bindings: dict = None) -> bool:
        return bool(self._left._call(data, bindings)) or bool(self._right._call(data, bindings))


class _Branch:
    __slots__ = ('true_action', 'false_action')
    
    def __init__(self, true_action: Action, false_action: Action) -> None:
        self.true_action = true_action
        self.false_action = false_action


class _IfAction(Action):
    def __init__(self, condition: Action, then_action: Action) -> None:
        super().__init__(action=_ActionType.Pass)
        self._condition = condition
        self._then = then_action

    def _call(self, data: _Data, bindings: dict = None) -> tuple[Any, bool]:
        cond_result = self._condition._call(data, bindings)
        if isinstance(cond_result, tuple) and cond_result[1]:
            return cond_result
        if cond_result:
            result = self._then._call(data, bindings)
            if isinstance(result, tuple):
                return result
        return (None, False)


class _IfElseAction(Action):
    def __init__(self, condition: Action, then_action: Action, else_action: Action) -> None:
        super().__init__(action=_ActionType.Pass)
        self._condition = condition
        self._then = then_action
        self._else = else_action

    def _call(self, data: _Data, bindings: dict = None) -> tuple[Any, bool]:
        cond_result = self._condition._call(data, bindings)
        if isinstance(cond_result, tuple) and cond_result[1]:
            return cond_result
        if cond_result:
            result = self._then._call(data, bindings)
            if isinstance(result, tuple):
                return result
        else:
            result = self._else._call(data, bindings)
            if isinstance(result, tuple):
                return result
        return (None, False)


class _SeqAction(Action):
    def __init__(self, first: Action, second: Action) -> None:
        super().__init__(action=_ActionType.Pass)
        self._first = first
        self._second = second

    def _call(self, data: _Data, bindings: dict = None) -> tuple[Any, bool]:
        result = self._first._call(data, bindings)
        if isinstance(result, tuple) and result[1]:
            return result
        return self._second._call(data, bindings)


class Template(Action):
    def __init__(self, *, id: str) -> None:
        super().__init__(action=_ActionType.Pass)
        self.id = id

    def _call(self, data: _Data, bindings: dict = None) -> None:
        if bindings is None or self.id not in bindings:
            raise RuntimeError(f"Template '{self.id}' not bound")
        binding = bindings[self.id]
        if isinstance(binding, tuple):
            func, *args = binding
            func(*args)
        else:
            binding()


class ActionChain:
    def __init__(self, *actions: Action) -> None:
        self._actions = list(actions)
        self._bindings: dict | None = None

    def __getitem__(self, index: int) -> Action:
        return self._actions[index]

    def __setitem__(self, index: int, value: Action) -> None:
        self._actions[index] = value

    def __lshift__(self, bindings: dict[str, tuple | Callable]) -> '_BoundActionChain':
        return _BoundActionChain(self, bindings)

    def __ilshift__(self, bindings: dict[str, tuple | Callable]) -> 'ActionChain':
        self._bindings = bindings
        return self

    def __or__(self, data: Any) -> Any:
        if self._bindings is not None:
            return self._execute_with_bindings(data, self._bindings)
        if self._contains_template():
            raise RuntimeError(
                "ActionChain contains Template but no bindings. Use << or <<= first."
            )
        return self._execute_with_bindings(data, {})

    def _contains_template(self) -> bool:
        def _check(action: Action) -> bool:
            if isinstance(action, Template):
                return True
            if isinstance(action, _IfAction):
                return _check(action._condition) or _check(action._then)
            if isinstance(action, _IfElseAction):
                return _check(action._condition) or _check(action._then) or _check(action._else)
            if isinstance(action, _SeqAction):
                return _check(action._first) or _check(action._second)
            if isinstance(action, _AndCondition):
                return _check(action._left) or _check(action._right)
            if isinstance(action, _OrCondition):
                return _check(action._left) or _check(action._right)
            return False
        for act in self._actions:
            if _check(act):
                return True
        return False

    def _execute_with_bindings(self, data: Any, bindings: dict) -> Any:
        d = _Data(data)
        self._execute(d, bindings)
        return d.value

    def _execute(self, data: _Data, bindings: dict) -> None:
        for action in self._actions:
            result = action._call(data, bindings)
            if isinstance(result, tuple) and result[1]:
                break


class _BoundActionChain:
    def __init__(self, chain: ActionChain, bindings: dict) -> None:
        self._chain = chain
        self._bindings = bindings

    def __or__(self, data: Any) -> Any:
        d = _Data(data)
        self._chain._execute(d, self._bindings)
        return d.value


AC = ActionChain