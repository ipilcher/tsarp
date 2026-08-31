# SPDX-FileCopyrightText: 2026 Ian Pilcher <arequipeno@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later


"""Sphinx configuration for **TSArP**."""


import os
import sys
import annotationlib
import enum
import inspect
import itertools

import docutils
import sphinx.util.logging
import sphinx.domains.python
import sphinx.util.docfields
import sphinx.util.inspect
import sphinx.util.typing


project = 'TSArP'
copyright = '2026, Ian Pilcher'
author = 'Ian Pilcher'

autodoc_use_legacy_class_based = True
autodoc_typehints = 'description'
autodoc_typehints_description_target = "documented_params"
add_module_names = False

# Always run 'make clean' after changing this
_PRIVATE = os.getenv('TSARP_PRIVATE') is not None

nitpicky = True
sys.path.insert(0, os.path.abspath(".."))

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc', 'sphinx.ext.autosummary',
    'sphinx.ext.napoleon', 'sphinx.ext.intersphinx'
]

exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', '_templates']
intersphinx_mapping = {'python': ('https://docs.python.org/3', None)}

nitpick_ignore = [('py:meth', 'self._process'), ('py:class', 'T')]
nitpick_ignore_regex = [
    (r'py:.*', r'argparse(\..*)?'),
    (r'py:.*', r'.*\.__annotate__')
]

napoleon_custom_sections = [('Class Arguments', 'params_style')]
napoleon_preprocess_types = True


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'pydata_sphinx_theme'
#html_sidebars = {'**': ['page-toc']}
#html_theme_options = {'secondary_sidebar_items': []}
#html_theme = 'sphinx_rtd_theme'
#html_theme_options = {"nosidebar": True}  # Alabaster only?
html_static_path = ['_static']

autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'private-members': False,
    #'special-members': '__init_subclass__',
    'inherited-members': False,
}

autodoc_member_order = 'bysource'
autodoc_inherit_docstrings = False

autosummary_generate = _PRIVATE


if _PRIVATE:

    tags.add('internal')

    autodoc_default_options |= {
        'private-members': True,
        'special-members': '__new__,__init_subclass__',
        'show-inheritance': True,
        'ignore-module-all': True
    }

    templates_path = ['_templates']
    autosummary_ignore_module_all = True
    autosummary_imported_members = False


# Make RTD tables wrap text in cells.
html_js_files = [
    (None, {
        'body': (
            'document.head.insertAdjacentHTML("beforeend", '
            '"<style>'
            '.wy-table-responsive table td, '
            '.wy-table-responsive table th { '
            'white-space: normal !important; '
            '}'
            '</style>")'
        )
    })
]

# Create a role that can be used to highlight function/method argument names.
#
# For example:
#
#   The behavior of the :func:`frobulate` method depends on the value of the
#   :arg:`flibbertygibbet` parameter.
#
# The settings below work well with the pydata theme.

rst_prolog = """
.. raw:: html

   <style type="text/css">
     .arg {
       font-family: monospace, monospace;
       font-size: 105%;
       font-weight: bold;
     }
   </style>

.. role:: arg
   :class: arg

.. default-role:: arg
"""


#===============================================================================
#
#   Auto-doc event hooks
#
#===============================================================================

_log = sphinx.util.logging.getLogger(__name__)

# List of hooks to be added
hooks = []

# Decorator to add callbacks to the hook list
def connect(event, *, priority=500):
    def add_hook(func):
        hooks.append((event, func, priority))
        return func
    return add_hook


#-------------------------------------------------------------------------------
#
#   Inject the public form of the root document for non-private builds.
#
#   The on-disk index.rst holds the internal (autosummary) form.  For public
#   builds we replace it in memory here.
#
#-------------------------------------------------------------------------------

_INDEX_PUBLIC = """\
TSArP
=====

.. automodule:: tsarp
   :members:
"""

@connect('source-read')
def inject_public_index(app, docname, source):
    if not _PRIVATE and docname == app.config.root_doc:
        source[0] = _INDEX_PUBLIC


#-------------------------------------------------------------------------------
#
#   Make the class (or exception) being documented available to
#   later autodoc-skip-member callbacks.
#
#-------------------------------------------------------------------------------

from sphinx.ext.autodoc._legacy_class_based._documenters import ClassDocumenter
from sphinx.ext.autodoc._property_types import _ClassDefProperties

current_class = None

# Returns the class being documented in an autodoc-skip-member event.
# Must be called only when obj_type is 'class' or 'exception'.
def get_class():
    if globals().get('autodoc_use_legacy_class_based', False):
        function_name = 'filter_members'
        local_name = 'self'
        sphinx_class = ClassDocumenter
        attr_name = 'object'
    else:
        function_name = '_filter_members'
        local_name = 'props'
        sphinx_class = _ClassDefProperties
        attr_name = '_obj'
    frame = inspect.currentframe()
    while (frame := frame.f_back) is not None:
        if frame.f_code.co_name == function_name:
            sphinx_obj = frame.f_locals[local_name]
            assert isinstance(sphinx_obj, sphinx_class)
            return getattr(sphinx_obj, attr_name)
    return None

# Hook to set current_class; ensure it runs first
@connect('autodoc-skip-member', priority=0)
def set_current_class(app, obj_type, name, obj, skip, options):
    global current_class
    if obj_type in ('class', 'exception'):
        current_class = get_class()
    else:
        current_class = None
    return None


#-------------------------------------------------------------------------------
#
#   Don't document __init__ arguments or members of opaque classes
#
#-------------------------------------------------------------------------------

import tsarp._group

def is_opaque(cls):
    return (
        isinstance(cls, type)
        and annotationlib.get_annotations(cls).get(
            tsarp._group.OPAQUE_ANNOTATION_NAME, False
        )
    )

# Suppress the __init__ arguments
@connect('autodoc-process-signature')
def remove_opaque_args(
    app, obj_type, name, obj, options, signature, return_annotation
):
    if (
        not _PRIVATE
        and obj_type in ('class', 'exception')
        and is_opaque(obj)
    ):
        return '', None
    return None

# Suppress members (and skip the annotation itself to avoid warnings)
@connect('autodoc-skip-member')
def skip_opaque_members(app, obj_type, name, obj, skip, options):
    if (
        name == tsarp._group.OPAQUE_ANNOTATION_NAME
        or (
            not _PRIVATE
            and obj_type in ('class', 'exception')
            and current_class is not None
            and is_opaque(current_class)
        )
    ):
        return True
    return None


#-------------------------------------------------------------------------------
#
#   Document Enum __new__ methods correctly.
#
#-------------------------------------------------------------------------------

@connect('autodoc-process-docstring')
def fix_enum_new(app, obj_type, name, obj, options, lines):
    if (
        obj_type != 'method'
        or obj.__name__ != '__new__'
        or obj.__module__ != 'enum'
        or not (mod_name := app.env.temp_data.get('autodoc:module'))
    ):
        return
    cls_name = name.removeprefix(mod_name + '.').removesuffix('.__new__')
    try:
        ns = sys.modules[mod_name]
        for part in cls_name.split('.'):
            ns = getattr(ns, part)
        if isinstance(ns, type) and issubclass(ns, enum.Enum):
            # This may raise an AttributeError, so do it before clearing lines
            doc = inspect.cleandoc(ns._new_member_.__doc__).split('\n')
            lines.clear()
            lines.extend(doc)
    except AttributeError:
        return


#-------------------------------------------------------------------------------
#
#   Add PEP-695 generic indicators to classes, functions, and methods
#
#-------------------------------------------------------------------------------

_warned = False

@connect('autodoc-process-signature')
def add_pep695_generics_to_signature(
    app, obj_type, name, obj, options, signature, return_annotation
):
    global _warned
    if not globals().get('autodoc_use_legacy_class_based', False):
        if not _warned:
            _log.warning('PEP-695 hook requires autodoc legacy path')
            _warned = True
        return signature, return_annotation
    if not isinstance(options, dict):
        # Dynamic path (used by autosummary) passes _AutoDocumenterOptions;
        # its mangle_signature() cannot handle the [T] prefix.
        return signature, return_annotation
    if (
        obj_type in ('class', 'function', 'method')
        and hasattr(obj, "__type_params__")
        and len(obj.__type_params__) > 0
    ):
        params = f"[{', '.join(p.__name__ for p in obj.__type_params__)}]"
        if signature is not None:
            signature = params + signature
        else:
            signature = params + '()'
    return signature, return_annotation


#-------------------------------------------------------------------------------
#
#   De-mangle private class attribute names.
#
#-------------------------------------------------------------------------------

# Mangled names to be skipped.
mangled_names = {}

# For every name-mangled attribute in the class, create an attribute with its
# original, unmangled name (and the same value).  If necessary, also create an
# attribute with the name mangled as Sphinx expects, if it is different than the
# actual mangled name.  (See https://github.com/sphinx-doc/sphinx/pull/14554.)
@connect('autodoc-process-docstring')
def alias_mangled_attributes(app, obj_type, name, obj, options, lines):
    if obj_type == 'module':
        mangled_names.clear()
    elif obj_type in ('class', 'exception') and isinstance(obj, type):
        runtime_prefix = f'_{obj.__name__.lstrip('_')}__'
        mangled = []
        for runtime_name, value in list(getattr(obj, '__dict__', {}).items()):
            if runtime_name.startswith(runtime_prefix):
                orig_name = f'__{runtime_name.removeprefix(runtime_prefix)}'
                sphinx_name = f'_{obj.__name__}{orig_name}'
                setattr(obj, orig_name, value)
                mangled.append(runtime_name)
                if sphinx_name != runtime_name:
                    setattr(obj, sphinx_name, value)
                    mangled.append(sphinx_name)
        if mangled:
            mangled_names[obj] = mangled

# Skip attributes in the class's mangled name list
@connect('autodoc-skip-member')
def skip_mangled_members(app, obj_type, name, obj, skip, options):
    if obj_type in ('class', 'exception'):
        if name in mangled_names.get(current_class, ()):
            return True
    return None


#-------------------------------------------------------------------------------
#
#   Link to arbitrary sections of the standard library documentation for things
#   that can't be resolved properly.  (E.g., argparse's add_parser() method,
#   which is only documented indirectly in the Subcommands section.)
#
#-------------------------------------------------------------------------------

REF_SECTIONS = {
    ('meth', 'argparse.add_parser'): ('argparse', 'subcommands')
}

@connect('missing-reference')
def resolve(app, env, node, contnode):
    ref_info = REF_SECTIONS.get((node.get('reftype'), node.get('reftarget')))
    if ref_info is None:
        return None
    # NOTE: Shape of "normalized" tuple may change in the future
    base_url = app.config.intersphinx_mapping['python'][1][0]
    print(f"*** base_url = {base_url!r}")
    url = f'{base_url}/library/{ref_info[0]}.html#{ref_info[1]}'
    anchor_node = docutils.nodes.reference('', '', internal=False, refuri=url)
    anchor_node.append(contnode)
    return anchor_node


#-------------------------------------------------------------------------------
#
#   Use __init_subclass__ Args section as Class Arguments section of class
#   docstring
#
#-------------------------------------------------------------------------------

# Create and add new :classarg and :classargtype field types
sphinx.domains.python.PyObject.doc_field_types.append(
    sphinx.domains.python.PyTypedField(
        "classarg",
        label="Class Parameters",
        names=("classarg",),
        typerolename="obj",
        typenames=("classargtype",),
    )
)

# Clear class (and exception) and object caches, so they'll see the new types
sphinx.domains.python.PyObject._doc_field_type_map = {}
sphinx.domains.python.PyClasslike._doc_field_type_map = {}

# Find the existing PyTypedField for :param, :parameter, :arg, etc.
param_field = next(
    f for f in sphinx.domains.python.PyObject.doc_field_types
    if f.name == 'parameter'
)

# Param field prefixes (':param', ':parameter', ':arg', ':argument', etc.)
param_prefixes = tuple(':' + p for p in param_field.names)

# Type field prefixes (':paramtype' and ':type')
type_prefixes = tuple(':' + t for t in param_field.typenames)

# Type or param field prefixes (':param', ':arg', ':type', etc.)
all_prefixes = param_prefixes + type_prefixes

@connect('autodoc-process-docstring', priority=1000)
def inject_init_subclass_params(app, obj_type, name, obj, options, lines):
    if obj_type != 'class' or '__init_subclass__' not in obj.__dict__:
        return
    # Get __init_subclass__'s docstring, if any
    func = obj.__dict__['__init_subclass__'].__func__
    if not (rst_lines := (inspect.getdoc(func) or '').splitlines()):
        return
    app.emit(
        'autodoc-process-docstring', 'method',
        f'{name}.__init_subclass__', func, options, rst_lines
    )
    # Collect lines that make up :param and :type fields
    param_lines = []
    typed_params = set()  # params that have an explicit type in the docstring
    in_field = False
    for line in rst_lines:
        prefix, _, remainder = line.partition(' ')
        if prefix in all_prefixes:
            in_field = True
            if prefix in type_prefixes:
                field_type = 'classargtype'
                typed_params.add(remainder.partition(':')[0].strip())
            else:
                field_type = 'classarg'
            param_lines.append(f':{field_type} {remainder}')
        elif in_field:
            if line[:1].isspace() or not line.strip():
                # Leading whitespace or empty line continues the field
                param_lines.append(line)
            else:
                in_field = False
    # Handle argument type annotations
    mode = (
        'smart'
        if app.config.autodoc_typehints_format == 'short'
        else 'fully-qualified'
    )
    sig = sphinx.util.inspect.signature(
        func, type_aliases=app.config.autodoc_type_aliases
    )
    # Skip the first argument (usually named 'cls')
    for param in itertools.islice(sig.parameters.values(), 1, None):
        if param.annotation is param.empty or param.name in typed_params:
            continue
        type_str = sphinx.util.typing.stringify_annotation(
            param.annotation, mode
        )
        type_line = f':classargtype {param.name}: {type_str}'
        arg_prefix = f':classarg {param.name}:'
        # Find the :classarg field for this param
        for i, line in enumerate(param_lines, start=1):  # NOTE: start=1
            if line.startswith(arg_prefix):
                break
        else:
            # No description for this param
            continue
        # Find the line after the :classarg field
        for i, line in enumerate(param_lines[i:], i):
            if not(line[:1].isspace() or not line.strip()):
                break
        else:
            # Nothing after :classarg field; add :classargtype at end
            i = len(param_lines)
        param_lines.insert(i, type_line)
    if param_lines:
        lines.append('')
        lines.extend(param_lines)


#-------------------------------------------------------------------------------
#
#   Register all the hooks
#
#-------------------------------------------------------------------------------

def setup(app):
    for hook in hooks:
        app.connect(hook[0], hook[1], priority=hook[2])


# kate: indent-width 4; replace-tabs on;
