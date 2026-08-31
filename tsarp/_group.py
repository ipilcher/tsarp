# SPDX-License-Identifier: LGPL-3.0-or-later


"""\
Argument groups and mutually exclusive groups

Copyright 2026 Ian Pilcher <arequipeno@gmail.com>
"""


import dataclasses
import typing


OPAQUE_ANNOTATION_NAME: typing.Final = f"<<{__name__}.opaque>>"
"""Annotation name for :func:`opaque`."""


def opaque[T](cls: type[T]) -> type[T]:
    """Marks a class as opaque, for documentation purposes.

    Adds an annotation to the decorated class, which is consumed by a Sphinx
    event hook.

    Args:
        cls: The class to be marked as opaque.

    Returns:
        :arg:`cls` (annotated as opaque).
    """
    if "__slots__" in cls.__dict__:
        raise TypeError(f"Cannot decorate slot-based class: {cls.__name__}")
    if "__annotations__" not in cls.__dict__:
        cls.__annotations__ = {}
    assert OPAQUE_ANNOTATION_NAME not in cls.__annotations__
    cls.__annotations__[OPAQUE_ANNOTATION_NAME] = True
    return cls


class Group:
    """Parent class of group descriptors (argument groups and mutually exclusive
    groups).
    """
    pass


@opaque
@dataclasses.dataclass
class ArgumentGroup(Group):
    """An opaque descriptor that describes an argument group.

    See Also:
      * https://docs.python.org/3/library/argparse.html#argument-groups
      * :func:`group`

    .. NOTE: This docstring is included in the *public* API documentation.
    """
#    :meta public:
#    """

    title: str | None=None
    """See :func:`group`."""

    desc: str | None=None
    """See :func:`group`."""


def group(
        title: str | None=None, description: str | None=None
) -> ArgumentGroup:
    """Creates an argument group descriptor.

    Args:
        title: The argument group title.
        description: The argument group description.

    Returns:
        A new argument group descriptor.
    """
    return ArgumentGroup(title, description)


@opaque
@dataclasses.dataclass(kw_only=True)
class MXGroup(Group):
    """An opaque descriptor that describes a mutually exclusive group.

    See Also:
      * https://docs.python.org/3/library/argparse.html#mutual-exclusion
      * :func:`mxgroup`

    .. NOTE: This docstring is included in the *public* API documentation.
    """
#    :meta public:
#    """

    required: bool=False
    """See :func:`mxgroup`."""

    group: str | None=None
    """See :func:`mxgroup`."""


def mxgroup(*, required: bool=False, group: str | None=None) -> MXGroup:
    """Creates a mutually exclusive group descriptor.

    Args:
        required: If ``True``, one of the options in the group must be provided.
        group: Name of the argument group to which the mutually exclusive group
            will be added.  (If ``None``, the mutually exclusive group will be
            added directly to the top-level or subcommand parser.)

    Returns:
        A new mutually exclusive group descriptor.
    """
    return MXGroup(required=required, group=group)


# kate: tab-width 8; indent-width 4; replace-tabs on;
