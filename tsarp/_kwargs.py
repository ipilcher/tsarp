# SPDX-License-Identifier: LGPL-3.0-or-later


"""\
Typed dictionaries for keyword arguments

Copyright 2026 Ian Pilcher <arequipeno@gmail.com>
"""


import argparse
import collections.abc
import typing


class AddArgumentKwargs[T](typing.TypedDict, total=False):
    """Keyword arguments passed to the :mod:`argparse`
    :meth:`~argparse._ActionsContainer.add_argument` method.

    See Also:
        * https://docs.python.org/3/library/argparse.html#the-add-argument-method
    """
    type: argparse._ActionType
    """See
    https://docs.python.org/3/library/argparse.html#type.
    """

    default: T
    """See
    https://docs.python.org/3/library/argparse.html#default.
    """

    required: bool
    """See
    https://docs.python.org/3/library/argparse.html#required.
    """

    choices: collections.abc.Iterable[T]
    """See
    https://docs.python.org/3/library/argparse.html#choices.
    """

    action: str | type[argparse.Action]
    """See
    https://docs.python.org/3/library/argparse.html#action.
    """

    nargs: str
    """See
    https://docs.python.org/3/library/argparse.html#nargs.
    """

    help: str
    """See
    https://docs.python.org/3/library/argparse.html#help.
    """

    metavar: str
    """See
    https://docs.python.org/3/library/argparse.html#metavar.
    """

    deprecated: bool
    """See
    https://docs.python.org/3/library/argparse.html#deprecated.
    """

    dest: str
    """See
    https://docs.python.org/3/library/argparse.html#dest.
    """


class ArgParserKwargs(typing.TypedDict, total=False):
    """Keyword arguments passed to the :class:`argparse.ArgumentParser`
    constructor.

    See Also:
        * https://docs.python.org/3/library/argparse.html#argumentparser-objects
    """
    prog: str
    """See
    https://docs.python.org/3/library/argparse.html#prog.
    """

    usage: str
    """See
    https://docs.python.org/3/library/argparse.html#usage.
    """

    description: str
    """See
    https://docs.python.org/3/library/argparse.html#description.
    """

    epilog: str
    """See
    https://docs.python.org/3/library/argparse.html#epilog.
    """

    parents: collections.abc.Sequence[argparse.ArgumentParser]
    """See
    https://docs.python.org/3/library/argparse.html#parents.
    """

    formatter_class: type[argparse.HelpFormatter]
    """See
    https://docs.python.org/3/library/argparse.html#formatter-class.
    """

    prefix_chars: str
    """See
    https://docs.python.org/3/library/argparse.html#prefix-chars.
    """

    fromfile_prefix_chars: str
    """See
    https://docs.python.org/3/library/argparse.html#fromfile-prefix-chars.
    """

    conflict_handler: str
    """See
    https://docs.python.org/3/library/argparse.html#conflict-handler.
    """

    add_help: bool
    """See
    https://docs.python.org/3/library/argparse.html#add-help.
    """

    allow_abbrev: bool
    """See
    https://docs.python.org/3/library/argparse.html#allow-abbrev.
    """

    exit_on_error: bool
    """See
    https://docs.python.org/3/library/argparse.html#exit-on-error.
    """

    suggest_on_error: bool
    """See
    https://docs.python.org/3/library/argparse.html#suggest-on-error.
    """

    color: bool
    """See
    https://docs.python.org/3/library/argparse.html#color.
    """


class AddSubparsersKwargs(typing.TypedDict, total=False):
    """Keyword arguments passed to the :mod:`argparse`
    :meth:`~argparse.ArgumentParser.add_subparsers` method.

    See Also:
        * https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_subparsers
    """
    title: str
    """See
    https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_subparsers.
    """

    description: str
    """See
    https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_subparsers.
    """

    prog: str
    """See
    https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_subparsers.
    """

    parser_class: type[argparse.ArgumentParser]
    """See
    https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_subparsers.
    """

    # See https://github.com/python/typeshed/issues/16309
    #action: str | type[argparse.Action]
    action: type[argparse.Action]
    """See
    https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_subparsers.
    """

    required: bool
    """See
    https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_subparsers.
    """

    help: str
    """See
    https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_subparsers.
    """

    metavar: str
    """See
    https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_subparsers.
    """


# kate: tab-width 8; indent-width 4; replace-tabs on;
