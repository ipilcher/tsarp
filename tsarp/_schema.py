# SPDX-License-Identifier: LGPL-3.0-or-later


"""\
Command line schema definition and parsing

Copyright 2026 Ian Pilcher <arequipeno@gmail.com>
"""


import argparse
import collections.abc
import dataclasses
import typing

from . import _arg
from . import _group
from . import _kwargs
from . import _type


class _SchemaDescParent:
    """\
    Move :attr:`.all` out of :class:`SchemaDescriptor` to work around Mypy bug

    See Also:
      * https://github.com/python/mypy/issues/21906
    """

    all: typing.Final[dict[type[Schema], SchemaDescriptor[Schema]]] = {}
    """The :class:`SchemaDescriptor` for every :class:`Schema` subclass."""

    @staticmethod
    def __check_sd_cls[T: Schema](
            sd: SchemaDescriptor[Schema], schema_cls: type[T]
    ) -> typing.TypeGuard[SchemaDescriptor[T]]:
        """:class:`~typing.TypeGuard` helper for :meth:`get_descriptor`."""
        return sd.schema_cls is schema_cls

    @classmethod
    def get_descriptor[T: Schema](
            cls, schema_cls: type[T]
    ) -> SchemaDescriptor[T]:
        """Gets the descriptor for a schema.

        Args:
            schema_cls: The :class:`Schema` subclass whose descriptor will be
                returned.

        Returns:
            The :class:`SchemaDescriptor` for :arg:`schama_cls`.
        """
        sd = cls.all[schema_cls]
        assert cls.__check_sd_cls(sd, schema_cls)
        return sd


@dataclasses.dataclass(kw_only=True)
class SchemaDescriptor[T: Schema](_SchemaDescParent):
    """Information about a :class:`Schema` subclass.

    Every "concrete" subclass of :class:`Schema` has a corresponding
    :class:`SchemaDescriptor` instance, which is stored in
    :attr:`_SchemaDescParent.all`.  The descriptor stores information about the
    subclass, without polluting its namespace.

    Note:
      * A concrete subclass is a subclass that is defined with any class
        arguments (:arg:`custom_types` or :arg:`parser_kwargs`) or any groups,
        arguments, or subcommands.

      * Concrete subclasses cannot themselves be subclassed.  Attempting to do
        so will raise a :class:`TypeError`.
    """

    schema_cls: type[T]
    """The :class:`Schema` subclass which this object describes."""

    custom_types: collections.abc.Iterable[_type.Type[typing.Any]]
    """Custom types to be registered with the described schema's parsers."""

    parser_kwargs: _kwargs.ArgParserKwargs
    """Arguments passed to parser constructors for the described schema.

    The parser constructor is either :class:`ArgumentParser()
    <argparse.ArgumentParser>` (for a top-level parser) or
    :meth:`~argparse.add_parser` (for a subcommand parser).
    """

    subcommands_dest: str | None
    """\
    The name of the attribute that will hold the name of the invoked subcommand.
    """

    arguments: dict[str, _arg.Argument[object]]
    """All argument descriptors for the described schema.

    Note:
        Positional arguments must be added to parsers in the order in which they
        are defined in their schema.  `Python dictionaries`_ preserve the
        insertion order of their contents (since Python 3.7), so this "just
        works" when :func:`_process_arguments` iterates through this field.

    .. _`Python dictionaries`:
       https://docs.python.org/3/reference/datamodel.html#dictionaries
    """

    arg_groups: dict[str, _group.ArgumentGroup]
    """Argument group descriptors for the described schema."""

    mx_groups: dict[str, _group.MXGroup]
    """Mutually exclusive group descriptors for the described schema."""

    subcmds: dict[str, SchemaDescriptor[Schema]]
    """Subcommand schema descriptors for the described schema."""

    cli_parser: argparse.ArgumentParser | None = (
        dataclasses.field(init=False, default=None)
    )
    """Parser used when the described schema is used as a top-level CLI."""


class Schema:
    """Abstract base class for top-level and subcommand schemas.

    .. NOTE:
        Class parameter documentation is automatically pulled from the
        __init_subclass__ Args: section by the inject_init_subclass_params
        Sphinx event hook.  This works even if __init_subclass__ is skipped in
        the generated documentation.

        The 'Registering custom types or actions' link target must be in this
        docstring, so that it will be included in the generated reST document
        when __init_subclass__ is skipped.

    .. _`Registering custom types or actions`:
        https://docs.python.org/3/library/argparse.html#registering-custom-types-or-actions
    """

    def __init_subclass__(
            cls,
            *,
            custom_types: collections.abc.Iterable[_type.Type[typing.Any]] = (),
            **parser_kwargs: typing.Unpack[_kwargs.ArgParserKwargs]
    ) -> None:
        """Creates a :class:`SchemaDescriptor` for every concrete subclass of
        :class:`Schema`.

        See :class:`SchemaDescriptor` for the definition of a concrete subclass.

        Args:
            custom_types: Custom types to be registered with the schema's
                parsers.  (See `Registering custom types or actions`_.)
            parser_kwargs: Arguments passed to the schema's parser constructors.
                A parser constructor is either :class:`ArgumentParser()
                <argparse.ArgumentParser>` (for a top-level parser) or
                :meth:`~argparse.add_parser` (for a subcommand parser).

        Note:
            This function's parameter documentation is automatically copied to
            the **Class Parameters** section above.
        """
        for parent in cls.__mro__[1:]:
            if parent in SchemaDescriptor.all:
                raise TypeError(
                    f"{cls.__name__} extends concrete {parent.__name__}"
                )
        arguments: dict[str, _arg.Argument[object]] = {}
        arg_groups: dict[str, _group.ArgumentGroup] = {}
        mx_groups: dict[str, _group.MXGroup] = {}
        subcmds: dict[str, SchemaDescriptor[Schema]] = {}
        subcommands_dest: str | None = None
        # NOTE: Assumes that argument order is preserved in the dict returned by
        # vars().  Custom metaclass, class decorator, etc., could change it.
        for name, value in vars(cls).items():
            if isinstance(value, _arg.Argument):
                arguments[name] = value
                if isinstance(value, Subcommands):
                    if subcommands_dest is not None:
                        raise TypeError(
                            "subcommands() called multiple times in class"
                        )
                    subcommands_dest = name
            elif isinstance(value, _group.ArgumentGroup):
                arg_groups[name] = value
            elif isinstance(value, _group.MXGroup):
                mx_groups[name] = value
            elif isinstance(value, SchemaDescriptor):
                subcmds[name] = value
        if not any((
            custom_types, parser_kwargs,
            arguments, arg_groups, mx_groups, subcmds
        )):
            # Not a "concrete" subclass.  (See SchemaDescriptor docstring.)
            return
        if subcmds and not subcommands_dest:
            raise TypeError("subcmd() called without subcommands()")
        for name in {
            *arguments, *arg_groups, *mx_groups, *subcmds
        }:
            delattr(cls, name)
        sd = SchemaDescriptor(
            schema_cls=cls,
            custom_types=custom_types,
            parser_kwargs=parser_kwargs or {},
            subcommands_dest=subcommands_dest,
            arguments=arguments,
            arg_groups=arg_groups,
            mx_groups=mx_groups,
            subcmds=subcmds
        )
        SchemaDescriptor.all[cls] = sd


def subcmd[T: Schema](schema_cls: type[T]) -> T | None:
    """Use a schema as a subcommand.

    Important:
        This function should only be called inside a :class:`Schema` subclass
        definition.

    Args:
        schema_cls: A schema (a subclass of :class:`Schema`) to be used as a
            subcommand.

    Returns:
        An opaque descriptor that represents the schema.

    Note:
        The stated return type (``T | None``) represents the type of the target
        attribute in a parsed schema instance, not the runtime type of the
        descriptor.
    """
    if not (isinstance(schema_cls, type) and issubclass(schema_cls, Schema)):
        raise TypeError(f"Not a subclass of Schema: {schema_cls!r}")
    return typing.cast(T, SchemaDescriptor.all[schema_cls])


class Subcommands(_arg.Argument[object]):
    """Wraps an :class:`~._kwargs.AddSubparsersKwargs` in an
    :class:`~._arg.Argument`.

    Args:
        kwargs: Arguments that will be passed to
            :meth:`~argparse.ArgumentParser.add_subparsers` when adding
            subcommands to a schema.
    """

    def __init__(
            self, **kwargs: typing.Unpack[_kwargs.AddSubparsersKwargs]
    ) -> None:
        super().__init__(group=None, help=None, deprecated=False)
        self.kwargs: typing.Final = kwargs

    def _process(self, dest: str, hint: object) -> None:
        """Never called (see :meth:`add`)."""
        raise NotImplementedError

    def add(
            self,
            sd: _arg._SchemaDescProto,
            ac: argparse._ActionsContainer,
            dest: str,
            hint: object
    ) -> None:
        """Overrides :meth:`Argument.add() <._arg.Argument.add>` to make it a
        no-op.
        """
        pass


def subcommands(
        **kwargs: typing.Unpack[_kwargs.AddSubparsersKwargs]
) -> str | None:
    """Enable subcommands in a schema.

    Assigning the result of this function to an attribute designates that
    attribute as the destination, which will hold the name of the chosen
    subcommand (or ``None``).

    Important:
        This function should only be called inside a :class:`Schema` subclass
        definition, and it can only be called once per schema.

    Args:
        kwargs: Arguments that will be passed to
            :meth:`~argparse.ArgumentParser.add_subparsers`.

    Returns:
        An opaque descriptor that represents the schema's subcommand registry.

    Note:
        The stated return type (``str | None``) represents the type of the
        target attribute in a parsed schema instance, not the runtime type of
        the descriptor.
    """
    return typing.cast(str, Subcommands(**kwargs))


def _process_schema[T: Schema](
        sd: SchemaDescriptor[T],
        parser: argparse.ArgumentParser,
        parent_args: collections.abc.Set[str]
) -> None:
    """Process a top-level or subcommand schema.

    Args:
        sd: The schema's descriptor.
        parser: The top-level or subcommand parser with which to register types,
            groups, arguments, subcommands, etc.
        parent_args: Names of all arguments in parent schemas.
    """
    for t in sd.custom_types:
        parser.register("type", t.name, t.factory)
    argparse_groups: dict[str, argparse._ArgumentGroup] = {}
    _process_arg_groups(sd, parser, argparse_groups)
    _process_mx_groups(sd, parser, argparse_groups)
    _process_arguments(sd, parser, parent_args, argparse_groups)
    _process_subcommands(sd, parser, parent_args)


def _process_arg_groups[T: Schema](
        sd: SchemaDescriptor[T],
        parser: argparse.ArgumentParser,
        argparse_groups: dict[str, argparse._ArgumentGroup]
) -> None:
    """Process the argument groups in a schema.

    Args:
        sd: The schema's descriptor.
        parser: The parser with which to register argument groups.
        argparse_groups: Collects all of the parsers :mod:`argparse` argument
            groups and mutually exclusive groups.
    """
    for name, grp in sd.arg_groups.items():
        argparse_group = parser.add_argument_group(grp.title, grp.desc)
        argparse_groups[name] = argparse_group


def _process_mx_groups[T: Schema](
        sd: SchemaDescriptor[T],
        parser: argparse.ArgumentParser,
        argparse_groups: dict[str, argparse._ArgumentGroup]
) -> None:
    """Process the mutually exclusive groups in a schema.

    Args:
        sd: The schema's descriptor.
        parser: The parser with which to register mutually exclusive groups.
        argparse_groups: Collects all of the parsers :mod:`argparse` argument
            groups and mutually exclusive groups.
    """
    ac: argparse._ActionsContainer
    for name, mxg in sd.mx_groups.items():
        if mxg.group is not None:
            ac = argparse_groups[mxg.group]
        else:
            ac = parser
        argparse_mxg = ac.add_mutually_exclusive_group(required=mxg.required)
        argparse_groups[name] = argparse_mxg


def _process_arguments[T: Schema](
        sd: SchemaDescriptor[T],
        parser: argparse.ArgumentParser,
        parent_args: collections.abc.Set[str],
        argparse_groups: dict[str, argparse._ArgumentGroup]
) -> None:
    """Process the arguments in a schema.

    Args:
        sd: The schema's descriptor.
        parser: The parser with which to register arguments.
        parent_args: Names of all arguments in parent schemas.
        argparse_groups: All of the parsers :mod:`argparse` argument groups and
            mutually exclusive groups.
    """
    type_hints = typing.get_type_hints(sd.schema_cls)
    in_opt_params = False
    ac: argparse._ActionsContainer
    # See ordering note in SchemaDescriptor.arguments
    for name, argument in sd.arguments.items():
        if name in parent_args:
            raise TypeError(f"Argument name shadows parent: {name}")
        if isinstance(argument, _arg.Parameter):
            if argument._required:
                if in_opt_params:
                    raise TypeError(
                        "Required parameter after optional parameter"
                    )
            else:
                in_opt_params = True
        if argument.group is not None:
            ac = argparse_groups[argument.group]
        else:
            ac = parser
        argument.add(sd, ac, name, type_hints.get(name))


def _process_subcommands[T: Schema](
        sd: SchemaDescriptor[T],
        parser: argparse.ArgumentParser,
        parent_args: collections.abc.Set[str]
) -> None:
    """Process the subcommands in a schema.

    Args:
        sd: The schema's descriptor.
        parser: The parser with which to register subcommands.
        parent_args: Names of all arguments in parent schemas.
    """
    dest = sd.subcommands_dest
    if dest is None:
        return
    subcommands = sd.arguments[dest]
    assert isinstance(subcommands, Subcommands)
    subparsers_action = parser.add_subparsers(dest=dest, **subcommands.kwargs)
    for name, subdesc in sd.subcmds.items():
        subparser = subparsers_action.add_parser(name, **subdesc.parser_kwargs)
        _process_schema(subdesc, subparser, parent_args | sd.arguments.keys())


def _parse_schema[T: Schema](
        ns: argparse.Namespace, sd: SchemaDescriptor[T]
) -> T:
    """Create a populated schema instance from a parsed
    :class:`~argparse.Namespace`.

    Args:
        ns: The :class:`argparse.Namespace`, returned by
            :meth:`~argparse.ArgumentParser.parse_args`.
        sd: The descriptor for the schema to be instantiated and populated.

    Returns:
        A populated schema instance.
    """
    parsed = sd.schema_cls()
    for name in sd.arguments.keys():
        # TODO - check type?
        setattr(parsed, name, getattr(ns, name))
    sc_name = getattr(ns, sd.subcommands_dest) if sd.subcommands_dest else None
    for name, sc_desc in sd.subcmds.items():
        if name == sc_name:
            setattr(parsed, name, _parse_schema(ns, sc_desc))
        else:
            setattr(parsed, name, None)
    return parsed


def parse[T: Schema](
        schema_cls: type[T],
        args: collections.abc.Sequence[str] | None=None
) -> T:
    """Parse a command line with a schema.

    Args:
        schema_cls: A schema (a subclass of :class:`Schema`) to be used as a
            top-level parser.
        args: The command-line arguments to parse.  If ``None``,
            :data:`sys.argv` is parsed.

    Returns:
        An instance of :arg:`schema_cls`, with its attributes set to the
        parsed values.
    """
    if not (isinstance(schema_cls, type) and issubclass(schema_cls, Schema)):
        raise TypeError(f"Not a subclass of Schema: {schema_cls!r}")
    sd = SchemaDescriptor.get_descriptor(schema_cls)
    if sd.cli_parser is None:
        sd.cli_parser = argparse.ArgumentParser(**sd.parser_kwargs)
        _process_schema(sd, sd.cli_parser, frozenset())
    ns = sd.cli_parser.parse_args(args)
    parsed = _parse_schema(ns, sd)
    return parsed


# kate: tab-width 8; indent-width 4; replace-tabs on;
