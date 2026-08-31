# TSArP Coverage of argparse Features


## `ArgumentParser` Constructor Parameters (`ArgParserKwargs`)

All 15 constructor parameters are exposed via the `parser_kwargs` class argument on `Schema`
subclasses (and also on subcommand schemas):

| Parameter | Exposed |
|---|---|
| `prog` | ✅ |
| `usage` | ✅ |
| `description` | ✅ |
| `epilog` | ✅ |
| `parents` | ✅ |
| `formatter_class` | ✅ |
| `prefix_chars` | ✅ |
| `fromfile_prefix_chars` | ✅ |
| `argument_default` | ✅ |
| `conflict_handler` | ✅ |
| `add_help` | ✅ |
| `allow_abbrev` | ✅ |
| `exit_on_error` | ✅ |
| `suggest_on_error` | ✅ |
| `color` | ✅ |


## `add_argument()` Parameters

TSArP maps three argument kinds to `add_argument()`: `param()` (positional), `opt()`
(value-taking option), and `flag()` (boolean switch).

| Parameter | `param()` | `opt()` | `flag()` | Notes |
|---|---|---|---|---|
| name/flags | ✅ auto | ✅ auto | ✅ auto | Inferred from attribute name; `--` prefix and `_`→`-` conversion applied for options/flags. Short form via TSArP's own `short=` kwarg. |
| `action` | ❌ | ❌ | hardcoded `store_true` | Only `store_true` is reachable. No access to `store_false`, `store_const`, `append`, `append_const`, `count`, `extend`, `version`, `BooleanOptionalAction`, or custom `Action` subclasses. |
| `nargs` | partial | ❌ | ❌ | `param()` silently sets `nargs='?'` when a default is provided, otherwise leaves it unset. Users cannot specify `nargs` directly; `'*'`, `'+'`, and integer-N forms are unreachable. |
| `const` | ❌ | ❌ | ❌ | Not exposed at all. |
| `default` | ✅ | ✅ | ❌ | `flag()` has no `default`; `store_true` implicitly gives `False`. |
| `type` | ✅ | ✅ | ❌ | Can be a callable or an TSArP `Type` registered name. TSArP also infers `type` from the attribute's type hint when not provided. |
| `choices` | ✅ | ✅ | ❌ | |
| `required` | ❌ | implicit | ❌ | For `opt()`, TSArP passes `required=True` when no default is given. Users cannot set it directly. For `param()`, requiredness is entirely determined by whether `default` is provided. |
| `help` | ✅ | ✅ | ✅ | |
| `metavar` | ✅ | ✅ | ❌ | `flag()` takes no value so metavar is irrelevant. |
| `dest` | ❌ | ❌ | ❌ | Always inferred from the attribute name; users cannot override it. |
| `deprecated` | ✅ | ✅ | ✅ | |


## Argument Groups (`add_argument_group`)

| Feature | Exposed |
|---|---|
| `title` | ✅ via `group(title=...)` |
| `description` | ✅ via `group(description=...)` |
| `argument_default` kwarg | ❌ |
| `conflict_handler` kwarg | ❌ |


## Mutually Exclusive Groups (`add_mutually_exclusive_group`)

| Feature | Exposed |
|---|---|
| `required` | ✅ via `mxgroup(required=...)` |
| Nesting inside an argument group | ✅ via TSArP's own `mxgroup(group=...)` kwarg |


## Subcommands

| Feature | Exposed |
|---|---|
| `add_subparsers()` `title` | ✅ via `AddSubparsersKwargs` |
| `add_subparsers()` `description` | ✅ |
| `add_subparsers()` `prog` | ✅ |
| `add_subparsers()` `parser_class` | ✅ |
| `add_subparsers()` `action` | ✅ |
| `add_subparsers()` `required` | ✅ |
| `add_subparsers()` `help` | ✅ |
| `add_subparsers()` `metavar` | ✅ |
| `add_subparsers()` `dest` | ❌ always the attribute name |
| `add_parser()` `help` (entry in parent's subcommand list) | ❌ not in `ArgParserKwargs` |
| `add_parser()` `aliases` | ❌ |
| `add_parser()` `deprecated` | ❌ |


## Custom Types / Actions

| Feature | Exposed |
|---|---|
| `register('type', name, factory)` | ✅ via the `Type` class and `custom_types=` class parameter |
| `register('action', ...)` | ❌ |


## Parse Methods and Other `ArgumentParser` Methods

| Feature | Exposed |
|---|---|
| `parse_args(args)` | ✅ via `parse(schema_cls, args)` |
| `parse_args(namespace=...)` | ❌ |
| `parse_known_args()` | ❌ |
| `parse_intermixed_args()` | ❌ |
| `parse_known_intermixed_args()` | ❌ |
| `set_defaults()` | ❌ |
| `get_default()` | ❌ |
| `print_usage()` | ❌ |
| `print_help()` | ❌ |
| `format_usage()` | ❌ |
| `format_help()` | ❌ |
| `exit()` | ❌ |
| `error()` | ❌ |
| `convert_arg_line_to_args()` | ❌ |


## Other argparse Objects

| Feature | Exposed |
|---|---|
| `Namespace` | ❌ TSArP returns schema instances instead |
| `FileType` | ❌ (also deprecated in 3.14) |
| `BooleanOptionalAction` | ❌ |
| `ArgumentError` / `ArgumentTypeError` | ❌ not re-exported (still raisable from user type callables) |


## Summary of Key Gaps

The most significant features that are absent from TSArP are:

1. **`nargs`** — multi-value arguments (`'*'`, `'+'`, integer N) are entirely unreachable.
   Optional positionals (`'?'`) are reachable only implicitly.
2. **`action`** — only `store_true` (via `flag()`) is reachable. `store_false`,
   `store_const`, `append`, `append_const`, `count`, `extend`, `version`, and custom
   `Action` subclasses are all unreachable.
3. **`const`** — no access at all, which also blocks `store_const`/`append_const` and the
   `nargs='?'` const-on-presence behavior for options.
4. **`dest` override** — always driven by the attribute name; cannot be set independently.
5. **Subcommand `aliases` and `deprecated`** — `add_parser()` parameters not reachable via
   `ArgParserKwargs`.
6. **Subcommand `help`** — the per-subcommand help string shown in the parent parser's
   listing is not reachable.
7. **All secondary parse methods** — `parse_known_args`, both intermixed variants, etc.
8. **Parser utility methods** — `set_defaults`, `print_help`, `format_help`, `exit`,
   `error`, etc.
