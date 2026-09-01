# SPDX-License-Identifier: LGPL-3.0-or-later


"""\
Argument (parameter, option, and flag) definitions

Copyright 2026 Ian Pilcher <arequipeno@gmail.com>
"""


import argparse
import builtins
import collections.abc
import dataclasses
import enum
import types
import typing

from . import _kwargs
from . import _type


# TODO: Use a proper sentinel in Python 3.15

class NoDefaultType(enum.Enum):
    """A singleton sentinel type, used to signify that an argument has no
    default value.
    """

    NO_DEFAULT = "NO_DEFAULT"
    """The :class:`NoDefaultType` singleton value."""


NO_DEFAULT: typing.Final = NoDefaultType.NO_DEFAULT
"""Unqualified name for the sentinel value."""


class _SchemaDescProto(typing.Protocol):
    """Typing stub for :class:`._schema.SchemaDescriptor`."""

    @property
    def mx_groups(self) -> collections.abc.Mapping[str, object]:
        """A view of the schema descriptor's
        :attr:`~._schema.SchemaDescriptor.mx_groups` attribute.
        """
        ...


#===============================================================================
#
#   Argument lifecycle
#   ==================
#
#                                     ⋮
#                             ┌───────┴────────┐
#                             │    Argument    │
#                             └───────┬────────┘
#                        ┌────────────┴────────────┐
#                ┌───────┴────────┐        ┌───────┴────────┐
#                │     Value      │        │     Switch     │
#                └───────┬────────┘        └───────┬────────┘
#           ┌────────────┴───────────┐ ┌───────────┴────────────┐
#   ┌───────┴────────┐        ┌──────┴─┴───────┐        ┌───────┴────────┐
#   │   Parameter    │        │     Option     │        │      Flag      │
#   └────────────────┘        └────────────────┘        └────────────────┘
#
#   1. Creation
#
#      During Schema subclass definition, Parameter, Option, and Flag objects
#      are created by calls to param(), opt(), and flag().  Init fields are set
#      by the dataclass __init__(); non-init fields (_type_hint,
#      _add_arg_kwargs, _name_or_flags) are not yet populated.  The objects are
#      stored as attributes of the subclass.
#
#   2. Classification (Schema.__init_subclass__)
#
#      Schema.__init_subclass__() iterates over the subclass's attributes,
#      recursing into any subcommands.  It identifies Argument instances, and
#      stores them in the arguments dict of the schema descriptor.  The dict
#      keys are the attribute names, which will be used as the *dest* argument
#      to argparse._ActionsContainer.add_argument().
#
#       Schema.__init_subclass__() also removes all library-related attributes
#       from the schema subclass object, including arguments.  They are
#       available only through the schema's descriptor.
#
#   3. Processing (_schema.parse)
#
#      _schema._process_arguments() retrieves the type hints for the Schema
#      subclass and calls Argument.add() for each argument.  Argument.add()
#      calls self._process(), which walks the argument's MRO via cooperative
#      super()._process() calls.  Each class in the chain populates its non-init
#      fields and adds its entries to _add_arg_kwargs.  After _process()
#      returns, add() calls add_argument() to register the argument with the
#      top-level or subcommand ArgumentParser (either directly or within an
#      argument group or mutually exclusive group).
#
#===============================================================================

@dataclasses.dataclass(kw_only=True)
class Argument[T]:
    """Parent class of arguments (parameters, options, and flags).

    Note:
        In this class and its subclasses, fields whose names begin with an
        underscore are "non-init fields."  They do not exist until the argument
        is processed by :func:`._schema.parse`.
    """

    group: str | None
    """Name of the group to which the argument will be added (if any)."""

    help: str | None
    """See
    https://docs.python.org/3/library/argparse.html#help.
    """

    deprecated: bool
    """See
    https://docs.python.org/3/library/argparse.html#deprecated.
    """

    _name_or_flags: list[str] = dataclasses.field(init=False, repr=False)
    """See
    https://docs.python.org/3/library/argparse.html#name-or-flags.
    """

    _add_arg_kwargs: _kwargs.AddArgumentKwargs[T] = (
        dataclasses.field(init=False, repr=False)
    )
    """Keyword arguments to :mod:`argparse`
    :meth:`~argparse.ArgumentParser.add_argument`.
    """

    # TODO: _type_hint will be typing.TypeForm[T] in Python 3.15+
    _type_hint: object = dataclasses.field(init=False, repr=False)
    """The argument's type hint."""

    @staticmethod
    def _dest_to_name(dest: str) -> str:
        """Constructs an argument name from a destination (attribute name).

        Non-leading underscores in :arg:`dest` are converted to hyphens.
        (Leading underscores are preserved.)

        Args:
            dest: The name of the attribute in which the argument value will be
                stored.

        Returns:
            The constructed argument name.
        """
        base = dest.lstrip("_")
        prefix = "_" * (len(dest) - len(base))
        return prefix + base.replace("_", "-")

    def _process(self, dest: str, hint: object) -> None:
        """Process this argument.

        Sets the following:

        * :attr:`~Argument._type_hint`
        * :attr:`~Argument._add_arg_kwargs` keys:
            * ``deprecated``
            * ``help``

        Note:
            This method is the top level of a cooperative call chain.  It is
            invoked by a call to ``super()._process()`` in the ``_process()``
            method of the previous class in the MRO_ (:class:`Value` or
            :class:`Switch`).

        Args:
            dest: The name of the attribute in which the argument value will be
                stored.
            hint: The argument's type hint.

        .. _MRO:
           https://docs.python.org/3/glossary.html#term-method-resolution-order
        """
        self._type_hint = hint
        self._add_arg_kwargs = {"deprecated": self.deprecated}
        if self.help is not None:
            self._add_arg_kwargs["help"] = self.help

    def add(
            self,
            sd: _SchemaDescProto,
            ac: argparse._ActionsContainer,
            dest: str,
            hint: object
    ) -> None:
        """Add this argument to the parser or group identified by :arg:`ac`.

        Calls :meth:`self._process` to set all non-init fields and populate
        :attr:`~Argument._add_arg_kwargs` and then calls
        :meth:`~argparse._ActionsContainer.add_argument`.

        Args:
            sd: The descriptor of the schema to which this argument belongs.
            ac: The :mod:`argparse` parser, argument group, or mutually
                exclusive group to which the argument will be added.
            dest: The name of the attribute in which the argument value will be
                stored.
            hint: The argument's type hint.
        """
        self._process(dest, hint)
        ac.add_argument(*self._name_or_flags, **self._add_arg_kwargs)


@dataclasses.dataclass(kw_only=True)
class Value[T](Argument[T]):
    """Parent class of arguments with types (parameters and options).

    Note:
      * See :class:`Argument` for documentation of :attr:`~Argument.group`,
        :attr:`~Argument.help`, and :attr:`~Argument.deprecated`.
    """

    default: T | NoDefaultType
    """See
    https://docs.python.org/3/library/argparse.html#default.
    """

    type: collections.abc.Callable[[str], T] | _type.Type[T] | None
    """See
    https://docs.python.org/3/library/argparse.html#type.
    """

    choices: collections.abc.Iterable[T] | None
    """See
    https://docs.python.org/3/library/argparse.html#choices.
    """

    metavar: str | None
    """See
    https://docs.python.org/3/library/argparse.html#metavar.
    """

    __stypes: typing.ClassVar[typing.Final] = (
        (types.NoneType, types.EllipsisType)
    )
    """Sentinel types for :meth:`__resolve_type`."""

    @property
    def _required(self) -> bool:
        """Is this argument required (i.e., has no default value)?"""
        return self.default is NO_DEFAULT

    @classmethod
    def __resolve_type(cls, hint: object) -> builtins.type[T]:
        """Resolves a type hint to its corresponding concrete type.

        Args:
            hint: The type hint.

        Returns:
            The concrete type (class object) represented by :arg:`hint`.

        Raises:
            ValueError: If :arg:`hint` does not represent a single concrete type
                (possibly in a union with a sentinel type).
        """
        if hint is None:
            raise ValueError("No type hint")
        if hint in cls.__stypes:
            raise ValueError(f"Hint contains no concrete types: {hint}")
        origin = typing.get_origin(hint)
        if origin is types.UnionType:
            hints = [h for h in typing.get_args(hint) if h not in cls.__stypes]
            if len(hints) == 0:
                raise ValueError(f"Hint contains no concrete types: {hint}")
            if len(hints) > 1:
                raise ValueError(
                    f"Hint contains multiple concrete types: {hint}"
                )
            hint = hints[0]
            origin = typing.get_origin(hint)
        if origin is not None:
            raise ValueError(f"Hint is a non-union parameterized type: {hint}")
        if not isinstance(hint, type):
            raise ValueError(f"Hint does not identify a concrete type: {hint}")
        return hint

    def _process(self, dest: str, hint: object) -> None:
        """Process this argument.

        Sets the following:

        * :attr:`~Argument._add_arg_kwargs` keys:
            * ``type``
            * ``default``
            * ``choices``
            * ``metavar``

        Note:
            This method is part of a cooperative call chain.  It is invoked by a
            call to ``super()._process()`` in the ``_process()`` method of the
            previous class in the MRO_ (:class:`Parameter` or :class:`Option`),
            and it calls ``super()._process()`` to invoke the ``_process()``
            method of the next class in the MRO (:class:`Switch` or
            :class:`Argument`).

        Args:
            dest: The name of the attribute in which the argument value will be
                stored.
            hint: The argument's type hint.
        """
        super()._process(dest, hint)
        if self.type is None:
            self._add_arg_kwargs["type"] = self.__resolve_type(hint)
        elif isinstance(self.type, _type.Type):
            self._add_arg_kwargs["type"] = self.type.name
        else:
            self._add_arg_kwargs["type"] = self.type
        if self.default is not NO_DEFAULT:
            self._add_arg_kwargs["default"] = self.default
        if self.choices is not None:
            self._add_arg_kwargs["choices"] = self.choices
        if self.metavar is not None:
            self._add_arg_kwargs["metavar"] = self.metavar

    def add(
            self,
            sd: _SchemaDescProto,
            ac: argparse._ActionsContainer,
            dest: str,
            hint: object
    ) -> None:
        """Overrides :meth:`Argument.add` to check for required values in MX
        groups.

        Args:
            sd: The descriptor of the schema to which this argument belongs.
            ac: The :mod:`argparse` parser, argument group, or mutually
                exclusive group to which the argument will be added.
            dest: The name of the attribute in which the argument value will be
                stored.
            hint: The argument's type hint.
        """
        if self._required and self.group in sd.mx_groups:
            raise TypeError(
                f"Can't add argument without default to MX group: {dest}"
            )
        super().add(sd, ac, dest, hint)


@dataclasses.dataclass(kw_only=True)
class Switch[T](Argument[T]):
    """Parent class of non-positional arguments (options and flags).

    Note:
        See :class:`Argument` for documentation of :attr:`~Argument.group`,
        :attr:`~Argument.help`, and :attr:`~Argument.deprecated`.
    """

    short: str | None
    """The "short" version of the option or flag (if any)."""

    def _process(self, dest: str, hint: object) -> None:
        """
        Process this argument.

        Sets the following:

        * :attr:`~Argument._name_or_flags`
        * :attr:`~Argument._add_arg_kwargs` keys:
            * ``dest``

        Note:
            This method is part of a cooperative call chain.  It is invoked by a
            call to ``super()._process()`` in the ``_process()`` method of the
            previous class in the MRO_ (:class:`Flag` or :class:`Value`), and it
            calls ``super()._process()`` to invoke the ``_process()`` method of
            the next class in the MRO (:class:`Argument`).

        Args:
            dest: The name of the attribute in which the argument value will be
                stored.
            hint: The argument's type hint.
        """
        super()._process(dest, hint)
        self._name_or_flags = ["--" + self._dest_to_name(dest)]
        if self.short is not None:
            if not (
                len(self.short) == 2
                and self.short[0] == "-"
                and self.short[1].isalnum()
            ):
                raise ValueError(f"Invalid short option name: {self.short}")
            self._name_or_flags.append(self.short)
        self._add_arg_kwargs["dest"] = dest


#===============================================================================
#
#   Parameter
#   =========
#
#   Fields:
#
#   ┌─────────────────┬──────────┬────────────────────┐
#   │      Name       │ Defined  │        Set         │
#   ├─────────────────┼──────────┼────────────────────┤
#   │ group           │ Argument │ Parameter.__init__ │
#   │ help            │ Argument │ Parameter.__init__ │
#   │ metavar         │  Value   │ Parameter.__init__ │
#   │ deprecated      │ Argument │ Parameter.__init__ │
#   │ default         │  Value   │ Parameter.__init__ │
#   │ type            │  Value   │ Parameter.__init__ │
#   │ choices         │  Value   │ Parameter.__init__ │
#   │ _add_arg_kwargs │ Argument │    (see below)     │
#   │ _name_or_flags  │ Argument │ Parameter._process │
#   │ _type_hint      │ Argument │ Argument._process  │
#   └─────────────────┴──────────┴────────────────────┘
#
#   _add_arg_kwargs:
#
#   ┌────────────┬────────────────────┐
#   │    Name    │        Set         │
#   ├────────────┼────────────────────┤
#   │ type       │   Value._process   │
#   │ default    │   Value._process   │
#   │ required   │         --         │
#   │ choices    │   Value._process   │
#   │ action     │         --         │
#   │ nargs      │ Parameter._process │
#   │ help       │ Argument._process  │
#   │ metavar    │   Value._process   │
#   │ deprecated │ Argument._process  │
#   │ dest       │         --         │
#   └────────────┴────────────────────┘
#
#===============================================================================

@dataclasses.dataclass(kw_only=True)
class Parameter[T](Value[T]):
    """A positional argument.

    Note:
      * See :class:`Argument` for documentation of :attr:`~Argument.group`,
        :attr:`~Argument.help`, and :attr:`~Argument.deprecated`.
      * See :class:`Value` for documentation of :attr:`~Value.default`,
        :attr:`~Value.type`, :attr:`~Value.choices`, and :attr:`~Value.metavar`.
    """

    def _process(self, dest: str, hint: object) -> None:
        """Process this parameter.

        Sets the following:

        * :attr:`~Argument._name_or_flags`
        * :attr:`~Argument._add_arg_kwargs` keys:
            * ``nargs``

        Note:
            This method is part of a cooperative call chain.  It calls
            ``super()._process()`` to invoke the ``_process()`` method of the
            next class in the MRO_ (:class:`Value`).

            (The MRO of this class is :class:`Parameter` → :class:`Value` →
            :class:`Argument`.)

        Args:
            dest: The name of the attribute in which the argument value will be
                stored.
            hint: The argument's type hint.
        """
        super()._process(dest, hint)
        self._name_or_flags = [dest]
        if not self._required:
            self._add_arg_kwargs["nargs"] = "?"


def param[T](
        *,
        default: T | NoDefaultType=NO_DEFAULT,
        type: collections.abc.Callable[[str], T] | _type.Type[T] | None=None,
        choices: collections.abc.Iterable[T] | None=None,
        group: str | None=None,
        help: str | None=None,
        metavar: str | None=None,
        deprecated: bool=False
) -> T:
    """Define a parameter (positional argument).

    Important:
        This function should only be called inside a :class:`Schema` subclass
        definition.

    Note:
      * When the :arg:`type` argument is not provided, its value can sometimes
        be inferred from the parameter's type hint.  This is only possible if
        the type hint is either a single concrete type (:class:`int`,
        :class:`float`, :class:`ipaddress.IPv4Address`, etc.) or a union
        containing a single concrete type and a sentinel type.
        :class:`~types.NoneType` (``None``) and :class:`~types.EllipsisType`
        (``...``) are recognized as sentinel types.

        If the type hint does not conform to this requirement, the :arg:`type`
        argument is required.

      * A parameter's destination (the name of its targeted
        :class:`~._schema.Schema` subclass attribute) is used verbatim as its
        display name.  I.e., no underscore-to-hyphen replacement is performed.
        The display name can be overridden by setting the parameter's
        :arg:`metavar`.

        (In contrast, the names of flags and options are constructed by
        replacing non-leading underscores in their destination with hyphens and
        prepending ``--``.  For example, ``debug_level`` becomes
        ``--debug-level``.)

    Args:
        default: See https://docs.python.org/3/library/argparse.html#default.
        type: See https://docs.python.org/3/library/argparse.html#type.  (As
            noted, this can be inferred from the argument's type hint in most
            cases.)
        choices: See https://docs.python.org/3/library/argparse.html#choices.
        group: The name of the argument group to which the parameter will be
            added (if any).
        help: See https://docs.python.org/3/library/argparse.html#help.
        metavar: See https://docs.python.org/3/library/argparse.html#metavar.
        deprecated: See
            https://docs.python.org/3/library/argparse.html#deprecated.

    Returns:
        An opaque descriptor that represents the parameter.

    Note:
        The stated return type (``T``) represents the type of the target
        attribute in a parsed schema instance, not the runtime type of the
        descriptor.
    """
    p = Parameter(
        default=default,
        type=type,
        choices=choices,
        group=group,
        help=help,
        metavar=metavar,
        deprecated=deprecated
    )
    return typing.cast(T, p)


#===============================================================================
#
#   Option
#   ======
#
#   Fields:
#
#   ┌─────────────────┬──────────┬───────────────────┐
#   │      Name       │ Defined  │        Set        │
#   ├─────────────────┼──────────┼───────────────────┤
#   │ group           │ Argument │  Option.__init__  │
#   │ help            │ Argument │  Option.__init__  │
#   │ metavar         │  Value   │  Option.__init__  │
#   │ deprecated      │ Argument │  Option.__init__  │
#   │ default         │  Value   │  Option.__init__  │
#   │ type            │  Value   │  Option.__init__  │
#   │ choices         │  Value   │  Option.__init__  │
#   │ short           │  Switch  │  Option.__init__  │
#   │ _add_arg_kwargs │ Argument │    (see below)    │
#   │ _name_or_flags  │ Argument │  Switch._process  │
#   │ _type_hint      │ Argument │ Argument._process │
#   └─────────────────┴──────────┴───────────────────┘
#
#   _add_arg_kwargs:
#
#   ┌────────────┬───────────────────┐
#   │    Name    │        Set        │
#   ├────────────┼───────────────────┤
#   │ type       │  Value._process   │
#   │ default    │  Value._process   │
#   │ required   │  Option._process  │
#   │ choices    │  Value._process   │
#   │ action     │        --         │
#   │ nargs      │        --         │
#   │ help       │ Argument._process │
#   │ metavar    │  Value._process   │
#   │ deprecated │ Argument._process │
#   │ dest       │  Switch._process  │
#   └────────────┴───────────────────┘
#
#===============================================================================

@dataclasses.dataclass
class Option[T](Value[T], Switch[T]):
    """A non-positional argument that takes a value.

    Note:
      * See :class:`Argument` for documentation of :attr:`~Argument.group`,
        :attr:`~Argument.help`, and :attr:`~Argument.deprecated`.
      * See :class:`Value` for documentation of :attr:`~Value.default`,
        :attr:`~Value.type`, :attr:`~Value.choices`, and :attr:`~Value.metavar`.
      * See :class:`Switch` for documentation of :attr:`~Switch.short`.
    """

    def _process(self, dest: str, hint: object) -> None:
        """Process this option.

        Sets the following:

        * :attr:`~Argument._add_arg_kwargs` keys:
            * ``required``

        Note:
            This method is part of a cooperative call chain.  It calls
            ``super()._process()`` to invoke the ``_process()`` method of the
            next class in the MRO_ (:class:`Value`).

            (The MRO of this class is :class:`Option` → :class:`Value` →
            :class:`Switch` → :class:`Argument`.)

        Args:
            dest: The name of the attribute in which the argument value will be
                stored.
            hint: The argument's type hint.
        """
        super()._process(dest, hint)
        if self._required:
            self._add_arg_kwargs["required"] = True


def opt[T](
        *,
        default: T | NoDefaultType=NO_DEFAULT,
        type: collections.abc.Callable[[str], T] | _type.Type[T] | None=None,
        choices: collections.abc.Iterable[T] | None=None,
        group: str | None=None,
        short: str | None=None,
        help: str | None=None,
        metavar: str | None=None,
        deprecated: bool=False
) -> T:
    """Define an option (a non-positional argument that takes a value).

    Important:
        This function should only be called inside a :class:`Schema` subclass
        definition.

    Note:
        When the :arg:`type` argument is not provided, its value can sometimes
        be inferred from the option's type hint.  This is only possible if the
        type hint is either a single concrete type (:class:`int`,
        :class:`float`, :class:`ipaddress.IPv4Address`, etc.) or a union
        containing a single concrete type and a sentinel type.
        :class:`~types.NoneType` (``None``) and :class:`~types.EllipsisType`
        (``...``) are recognized as sentinel types.

        If the type hint does not conform to this requirement, the :arg:`type`
        argument is required.

    Args:
        default: See https://docs.python.org/3/library/argparse.html#default.
        type: See https://docs.python.org/3/library/argparse.html#type.  (As
            noted, this can be inferred from the option's type hint in most
            cases.)
        choices: See https://docs.python.org/3/library/argparse.html#choices.
        group: The name of the argument group to which the option will be added
            (if any).
        short: The short form of the option name (a hyphen followed by a single
            alphanumeric character).
        help: See https://docs.python.org/3/library/argparse.html#help.
        metavar: See https://docs.python.org/3/library/argparse.html#metavar.
        deprecated: See
            https://docs.python.org/3/library/argparse.html#deprecated.

    Returns:
        An opaque descriptor that represents the option.

    Note:
        The stated return type (``T``) represents the type of the target
        attribute in a parsed schema instance, not the runtime type of the
        descriptor.
    """
    o = Option(
        default=default,
        type=type,
        choices=choices,
        group=group,
        short=short,
        help=help,
        metavar=metavar,
        deprecated=deprecated
    )
    return typing.cast(T, o)


#===============================================================================
#
#   Flag
#   ====
#
#   Fields:
#
#   ┌─────────────────┬──────────┬───────────────────┐
#   │      Name       │ Defined  │        Set        │
#   ├─────────────────┼──────────┼───────────────────┤
#   │ group           │ Argument │   Flag.__init__   │
#   │ help            │ Argument │   Flag.__init__   │
#   │ deprecated      │ Argument │   Flag.__init__   │
#   │ short           │  Switch  │   Flag.__init__   │
#   │ _add_arg_kwargs │ Argument │    (see below)    │
#   │ _name_or_flags  │ Argument │  Switch._process  │
#   │ _type_hint      │ Argument │ Argument._process │
#   └─────────────────┴──────────┴───────────────────┘
#
#   _add_arg_kwargs:
#
#   ┌────────────┬───────────────────┐
#   │    Name    │        Set        │
#   ├────────────┼───────────────────┤
#   │ type       │        --         │
#   │ default    │        --         │
#   │ required   │        --         │
#   │ choices    │        --         │
#   │ action     │   Flag._process   │
#   │ nargs      │        --         │
#   │ help       │ Argument._process │
#   │ metavar    │        --         │
#   │ deprecated │ Argument._process │
#   │ dest       │  Switch._process  │
#   └────────────┴───────────────────┘
#
#===============================================================================

@dataclasses.dataclass
class Flag(Switch[bool]):
    """A boolean flag.

    Note:
      * See :class:`Argument` for documentation of :attr:`~Argument.group`,
        :attr:`~Argument.help`, and :attr:`~Argument.deprecated`.
      * See :class:`Switch` for documentation of :attr:`~Switch.short`.
    """

    def _process(self, dest: str, hint: object) -> None:
        """Process this flag.

        Sets the following:

        * :attr:`~Argument._add_arg_kwargs` keys:
            * ``action``

        Note:
            This method is part of a cooperative call chain.  It calls
            ``super()._process()`` to invoke the ``_process()`` method of the
            next class in the MRO_ (:class:`Switch`).

            (The MRO of this class is :class:`Flag` → :class:`Switch` →
            :class:`Argument`.)

        Args:
            dest: The name of the attribute in which the argument value will be
                stored.
            hint: The argument's type hint.
        """
        super()._process(dest, hint)
        self._add_arg_kwargs["action"] = "store_true"


def flag(
        *,
        group: str | None=None,
        short: str | None=None,
        help: str | None=None,
        deprecated: bool=False
) -> bool:
    """Define a boolean flag.

    Important:
        This function should only be called inside a :class:`Schema` subclass
        definition.

    Args:
        group: The name of the argument group to which the flag will be added
            (if any).
        short: The short form of the flag name (a hyphen followed by a single
            alphanumeric character).
        help: See https://docs.python.org/3/library/argparse.html#help.
        deprecated: See
            https://docs.python.org/3/library/argparse.html#deprecated.

    Returns:
        An opaque descriptor that represents the flag.

    Note:
        The stated return type (``bool``) represents the type of the target
        attribute in a parsed schema instance, not the runtime type of the
        descriptor.
    """
    f = Flag(
        group=group,
        short=short,
        help=help,
        deprecated=deprecated
    )
    return typing.cast(bool, f)


# kate: tab-width 8; indent-width 4; replace-tabs on;
