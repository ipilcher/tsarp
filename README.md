<!-- SPDX-License-Identifier: GPL-3.0-or-later -->

# TSArP - Type-Safe Argument Parser

Copyright 2026 Ian Pilcher <<arequipeno@gmail.com>>

## Overview

**TSArP** (pronounced like "zarp") is a wrapper around Python's `argparse`
module that supports static type-safety.


## Limitations

**TSArP** is very much alpha software.

* It currently supports only a fraction of the full functionality of
  `argparse`.

* Python 3.14 or later is required.

* Inheritance of schema attributes (types, groups, arguments, etc.) is not
  possible.

* The API is very much in flux.

* Lots of edge cases remain to be worked out.

Despite this, it is still useful.

## Use

The basic usage pattern is:

 1. Create any custom types (instances of `tsarp.Type`).

 2. Create a schema (a subclass of `tsarp.Schema`) for any subcommands and the
    top-level command-line interface.

 3. Call `tsarp.parse()`, passing the top-level schema class as the first
    argument.

 4. `tsarp.parse()` returns an instance of the top-level schema class
    (containing instances of any subcommand schemas that were invoked).

### See also

  * [API documentation](https://ipilcher.github.io/tsarp/)
  * [`example.py`](example.py)

