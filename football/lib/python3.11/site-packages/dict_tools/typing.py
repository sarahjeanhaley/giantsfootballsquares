from typing import get_args
from typing import Type
from typing import Union


class _SpecialForm:
    __slots__ = ("_name", "__doc__", "_getitem")

    def __init__(self, getitem):
        self._getitem = getitem
        self._name = getitem.__name__
        self.__doc__ = getitem.__doc__

    def __getitem__(self, parameters):
        return self._getitem(self, parameters)


class ComputedValue:
    ...


# Types for type-hinting, they cannot be used in casting
@_SpecialForm
def Computed(self, type_: Type):
    """
    The "Computed" type indicates that a variable is the result of internal computation.
    It is not used by any function and effects no change.
    The variable's value is associated with the function soley for reference.

    Example:

    .. code-block:: python

      from dict_tools import typing


      def function(arg1: typing.Computed[str]):
          ...
    """
    return Union[type_, ComputedValue]


def is_computed(type_):
    """Returns True if type_ is Computed type."""
    return (
        hasattr(type_, "__origin__")
        and type_.__origin__ is Union
        and ComputedValue in get_args(type_)
    )


class SensitiveValue:
    ...


@_SpecialForm
def Sensitive(self, type_: Type):
    """
    The "Sensitive" type indicates that a variable contains data that should be protected from being displayed to users.

    Example:

    .. code-block:: python

      from dict_tools import typing


      def function(arg1: typing.Sensitive[str]):
          ...
    """
    return Union[type_, SensitiveValue]
