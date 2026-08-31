# SPDX-License-Identifier: LGPL-3.0-or-later


"""\
Custom argument types

Copyright 2026 Ian Pilcher <arequipeno@gmail.com>
"""


import collections.abc
import dataclasses
import typing


@dataclasses.dataclass(frozen=True)
class Type[T]:
    """A custom argument type.

    Instances are passed in the :arg:`custom_types` parameter of a
    :class:`.Schema` subclass definition and are registered via
    :meth:`argparse.ArgumentParser.register`.

    See Also:
      * https://docs.python.org/3/library/argparse.html#registering-custom-types-or-actions
    """

    __names: typing.ClassVar[typing.Final[set[str]]] = set()
    """All custom type names."""

    name: str
    """The name under which the type is registered with the schema.

    Passed as the ``value`` argument to
    :meth:`~argparse.ArgumentParser.register` and used as the ``type``
    keyword argument to :meth:`~argparse.ArgumentParser.add_argument`.
    """

    factory: collections.abc.Callable[[str], T]
    """A callable that converts a command-line string to the desired type.

    Passed as the ``object`` argument to
    :meth:`~argparse.ArgumentParser.register`.
    """

    def __new__(
            cls, name: str, factory: collections.abc.Callable[[str], T]
    ) -> typing.Self:
        """Ensure that no two instances have the same :arg:`name`."""
        if name in cls.__names:
            raise ValueError(f"Duplicate custom type name: {name}")
        new = super().__new__(cls)
        cls.__names.add(name)
        return new


# kate: tab-width 8; indent-width 4; replace-tabs on;
