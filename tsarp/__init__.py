# SPDX-License-Identifier: LGPL-3.0-or-later


"""\
Type-Safe Argument Parser

Copyright 2026 Ian Pilcher <arequipeno@gmail.com>
"""


import sys


__version__ = "0.0.1"


if sys.version_info < (3, 14):
    raise ImportError(
        f"{__name__} requires Python 3.14+ (currently {sys.version.split()[0]})"
    )


from ._type import Type
from ._group import group, mxgroup, ArgumentGroup, MXGroup
from ._arg import param, opt, flag, NoDefaultType
from ._schema import Schema, parse, subcmd, subcommands
from ._kwargs import ArgParserKwargs, AddSubparsersKwargs


__all__ = (
    "Schema",
    "parse",
    "subcmd",
    "subcommands",
    "NoDefaultType",
    "Type",
    "flag",
    "group",
    "mxgroup",
    "opt",
    "param",
    "ArgumentGroup",
    "MXGroup",
    "ArgParserKwargs",
    "AddSubparsersKwargs"
)


# kate: tab-width 8; indent-width 4; replace-tabs on;
