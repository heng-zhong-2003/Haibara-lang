from typing import Any, Callable
import sys
from colorama import Fore, Style
from dataclasses import dataclass
from frontend.cst_to_gir import TransHaibara

class ScopeSep:
    """
    Special separator value used to indicate the beginning of a scope
    in the implementation of `ValueEnv`.
    """

    def __init__(self) -> None:
        pass

# type for runtime values in the environment of the interpreter
type ValueType = str | bool | ScopeSep | None
# represents types of variables in Haibara (the object language), may be
# extended to structural representation (algebraic data type) in the future
type VarType = str


@dataclass
class ValueEnvEntry:
    ty: VarType
    val: ValueType


class ValueEnv:
    """Identifier-(runtime) value table that supports nested scopes"""

    def __init__(self) -> None:
        # map { var_name |-> stack of (<type>, <value>) pairs }
        # When `enter_scope` called, a `ScopeSep()` is pushed into all stacks;
        # when `exit_scope` called, for all stacks, the elements are poped out
        # up to the first `ScopeSep()` met (that sep also deleted).
        self.name_type_value_map: dict[str, list[ValueEnvEntry]] = {}

    def enter_scope(self) -> None:
        for _, stk in self.name_type_value_map.items():
            stk.append(ValueEnvEntry('ScopeSep', ScopeSep()))

    def exit_scope(self) -> None:
        for _, stk in self.name_type_value_map.items():
            while True:
                stack_top = stk.pop()
                match stack_top:
                    case ScopeSep():
                        break
                    case _:
                        pass

    def get_value_of_variable(self, identifier: str) -> ValueType:
        """
        Return the value of the newest declaration of `identifier`. Error
        and exit if `identifier` not declared at all.
        """
        if identifier not in self.name_type_value_map:
            sys.exit('Error: cannot `get_value` of an undefined identifier.')
        stk: list[ValueEnvEntry] = self.name_type_value_map[identifier]
        for i in range(len(stk) - 1, -1, -1):
            match stk[i]:
                case ScopeSep():
                    pass
                case _:
                    return stk[i].val
        # Undefined because there is only scope seperators in `identifier`'s stack
        sys.exit('Error: cannot `get_value` of an undefined identifier.')

    def declare_variable(self, identifier: str, ty: VarType) -> None:
        """
        Add a new variable to current scope. Sets its runtime value to `None`.
        If the same identifier already in outer-layer scope, the old declaration
        will be shadowed until current scope is exited.
        If the same identifier exists in the current scope, then that occurrence
        (together with its value) will be shadowed forever (since it will be
        deleted when exiting the current scope).
        """
        pass

    def assign_variable(self, identifier: str, new_value: ValueType) -> None:
        """
        Assign `new_value` to the newest (closest to the stack top) declaration
        of `identifier`. Error and exit if `identifier` not declared at all.
        """
        pass
