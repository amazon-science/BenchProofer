# mapping.md — django__django-11749

## Symbol binding (file:line @ base_commit 350123f3)

Changed function: `call_command` in
`django/core/management/__init__.py`. The patched region is the construction of
the `parse_args` list (lines 132–138 @ base_commit), which decides which
keyword-passed option values are forwarded to `parser.parse_args()`.

Pre-patch predicate (line 137):
```python
for opt in parser_actions if opt.required and opt.dest in options
```
Post-patch (lines 130–142 of patched file): a pre-computed set
```python
mutually_exclusive_required_options = {
    opt for group in parser._mutually_exclusive_groups
        for opt in group._group_actions if group.required
}
```
and predicate
```python
for opt in parser_actions if (
    opt.dest in options and
    (opt.required or opt in mutually_exclusive_required_options))
```

## Modeled function

`requiredOptionArgs` (neutral behavioral name; the repo symbol is not named in
the spec view). It computes the list of `"<flag>=<value>"` strings appended to
the positional-args prefix and forwarded to the argument parser.

## Lean ↔ Python type bijection (G-CONF / G-AX use this)

| Python | Lean |
|---|---|
| an argparse action object | `structure ParserAction` with `id : Nat` (object identity), `optionStrings : List String` (`option_strings`), `required : Bool`, `dest : String` |
| `parser_actions` (flattened) | `actions : List ParserAction` |
| a mutually-exclusive group | `structure ExclusiveGroup` with `required : Bool`, `groupActions : List ParserAction` |
| `parser._mutually_exclusive_groups` | `groups : List ExclusiveGroup` |
| the keys of the caller's `**options` (the RAW keyword names, before any renaming) | `optionKeys : List String` |
| `arg_options` (key→value, both stringified) — `options` REKEYED through `opt_mapping`, a DIFFERENT dict from `options` | `argOptions : List (String × String)` (assoc list, key = `dest` after renaming, value = stringified arg value) |
| `opt.dest in options` (membership against the RAW caller keys) | `destInOptions optionKeys opt` = `optionKeys.any (· = opt.dest)` |
| `arg_options[opt.dest]` (RAISES `KeyError` when the value table does not carry that dest) | `argOptions.lookup opt.dest : Option String` — `none` at an uncarried dest |
| `min(opt.option_strings)` (lexicographic; RAISES `ValueError` on an empty flag list) | `leastFlag? opt.optionStrings : Option String` — `none` on `[]`, else the foldl minimum with `String` `<` |
| the comprehension element, which produces no value when its `min(...)` OR its `arg_options[...]` subscript raises | `renderArg?` / `renderAll` return `none`, and the whole result is `Option (List String)` |
| `'{}={}'.format(flag, value)` | `flag ++ "=" ++ value` |
| `opt in mutually_exclusive_required_options` (object identity) | `inRequiredGroup groups opt` — `opt.id` appears in some required group's actions (structural `==` on `ParserAction`, where `id` carries identity) |
| the positional prefix `parse_args = [str(a) for a in args]` | `parseArgsPrefix : List String` (frame-pinned, unchanged by the fix) |

Object identity: Python uses set membership `opt in {…}` on action objects
(identity). The `id : Nat` field models that identity; the group's
`groupActions` reference the SAME action objects that appear in `actions`, so a
group action and its `actions` entry share `id` and compare equal.

## Callee provenance / flag deps

No unchanged callee needs an axiom. `min` (lexicographic minimum) and string
formatting are modeled directly (`leastFlag?`, `++`) — I-tagged identical ops,
not axioms. There is therefore no consumed axiom and no A-reference callee;
`axiom_check.py` is a skip stub.

## The two dict-shaped inputs are DISTINCT (why there are two binders)

The patched comprehension tests membership against one dict and reads the value
out of another:

```python
opt_mapping = {min(s_opt.option_strings).lstrip('-').replace('-', '_'): s_opt.dest
               for s_opt in parser._actions if s_opt.option_strings}   # line 116-119
arg_options = {opt_mapping.get(key, key): value
               for key, value in options.items()}                      # line 120
...
'{}={}'.format(min(opt.option_strings), arg_options[opt.dest])          # line 136/141
for opt in parser_actions if (opt.dest in options and ...)
```

`arg_options` is `options` REKEYED: a caller key matching some action's
flag-derived name (`min(option_strings)` stripped of dashes, dashes to
underscores) is replaced by that action's `dest`. So `opt.dest in options` does
NOT imply `opt.dest in arg_options`, and the model carries the two as separate
binders — `optionKeys` for the membership test, `argOptions` for the value.
Collapsing them into one would model a function the repo does not compute.

Measured against the real repo at the patched commit, with a command declaring a
required mutually-exclusive group holding `--x` (dest `shop`) and `--shop` (dest
`shop_id`):

```
call_command(cmd, shop='foo')
opt_mapping['shop'] = 'shop_id'
options     = {'shop': 'foo'}
arg_options = {'shop_id': 'foo'}      <-- key 'shop' ABSENT (rekeyed)
selected: dest='shop' flags=['--x'] required=False in_required_group=True
-> KeyError: 'shop' at django/core/management/__init__.py:141
```

## Callee partiality (both operations)

BOTH operations in the comprehension element are PARTIAL, and the model states
what the source guarantees rather than totalizing either:

* `min` raises `ValueError: min() arg is an empty sequence` on an action
  declaring no option flag (a positional), and such an action is selected
  whenever it is required (individually or via a required group) and its `dest`
  was named. Modeled by `leastFlag? : Option String`.
* `arg_options[opt.dest]` raises `KeyError` when the value table does not carry
  the selected action's `dest` — reachable exactly as measured above, and newly
  reachable *because* the patch's group disjunct selects actions the pre-patch
  predicate did not. Modeled by `argOptions.lookup opt.dest : Option String`.

The construction therefore produces no value at either point, which is why the
whole result is `Option (List String)` and `renderAll` propagates either failure
across the selected run. `conformance_check.py` compares the two sides as
`list | None` — the shadow reaching `None` structurally, the oracle by evaluating
the real unguarded `min(...)` and the real unguarded subscript and catching
`ValueError`/`KeyError` — and reports how many fuzzed cases reached each branch
separately, failing if either went unexercised.

The fix depends on the parser flag `group.required` (a mutually-exclusive group
contributes its actions to the forwarded set ONLY when `required=True`); G-CONF
fuzzes both `required` values per group, and draws `optionKeys` / `argOptions`
independently so the aligned, named-but-uncarried and carried-but-unnamed
configurations are all covered.

## G-CONF fuzz seed

Pinned seed: `11749`.
