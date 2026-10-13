# mapping.md — sphinx-doc__sphinx-7757

## Symbol binding (file:line @ base_commit 212fd67b9f0b4fae6a7c3501fdf1a9a5b2801329)

- Modeled function: `signature_from_str` — `sphinx/util/inspect.py:514-557`.
  The patch touches the **parameter-default alignment** block, lines 518-537
  (pre-patch): the construction of `params` from `args.posonlyargs` and
  `args.args` and the wiring of `args.defaults` onto them.
- Lean triple: `problem_spec_positionalDefaults` / `implementation_positionalDefaults`
  / `correct_positionalDefaults` in `Solution.lean`.

## What the modeled behavior is

`signature_from_str` parses a signature string into an `ast.arguments`. For the
positional parameters there are two consecutive groups:

- `args.posonlyargs` — the positional-only parameters (count `nPosonly`);
- `args.args` — the positional-or-keyword parameters (count `nArgs`);

and `args.defaults` is the flat list of default-value expressions for the
positional parameters, which by Python's rule fill the **rightmost**
`len(args.defaults)` positional parameters across BOTH groups combined.

The modeled value is: for each positional parameter, in order (posonly first,
then regular), the default expression text it carries (`some d`) or absence of a
default (`none`). In the real code each entry becomes a `Parameter(...,
default=...)`; the rendering of an `ast` default node back to source text
(`ast_unparse`) and the construction of `Parameter` objects are downstream of the
alignment and unchanged by the patch.

## The bug and the fix (refinement.md has the op table)

- **Pre-patch** (lines 523-537): positional-only parameters were built with NO
  `default=` at all (`Parameter(arg.arg, POSITIONAL_ONLY, annotation=...)`), so
  they could never carry a default; and the regular-arg loop aligned defaults
  against `len(args.args)` only — `args.defaults[-len(args.args) + i]` — ignoring
  the positional-only group. So a default belonging to a positional-only
  parameter (e.g. `b=0` in `(a, b=0, /, c=1)`) was dropped, and when posonly
  defaults were present the regular-arg indexing was also off.
- **Post-patch**: `defaults = list(args.defaults)` is left-padded with
  `Parameter.empty` up to `positionals = nPosonly + nArgs`
  (`for _ in range(len(defaults), positionals): defaults.insert(0, empty)`), then
  posonly parameter `i` takes `defaults[i]` and regular parameter `i` takes
  `defaults[i + posonlyargs]` — a single alignment across the whole positional
  run.

## Lean ↔ Python type bijection (G-CONF + G-AX use this)

| Python | Lean | bijection |
|---|---|---|
| `len(args.posonlyargs)` | `nPosonly : Nat` | count of positional-only params |
| `len(args.args)` | `nArgs : Nat` | count of positional-or-keyword params |
| `args.defaults` (list of `ast` expr nodes) | `defaults : List String` | each default modeled by its `ast_unparse` text; ORDER preserved; `len` is what the alignment uses |
| per-param `default`: `Parameter.empty` vs `ast_unparse(node)` | `Option String`: `none` vs `some text` | empty ↔ `none`, a rendered default ↔ `some text` |
| the positional `params` list (posonly then regular), each param's `default` field | `result : List (Option String)` of length `nPosonly + nArgs` | i-th entry is the i-th positional parameter's default |

The precondition `len(args.defaults) ≤ nPosonly + nArgs` holds for every
well-formed signature (you cannot have more defaults than positional
parameters); it is the binder hypothesis of `correct_positionalDefaults`.

## Callee provenance + flag deps

- `hasattr(args, "posonlyargs")` is True on every Python ≥ 3.8 (the supported
  range; the test is `skipif(sys.version_info < (3, 8))`). The modeled behavior
  is the `posonlyargs`-present configuration; `nPosonly = 0` recovers the
  no-posonly case, so no separate flag axis is needed.
- `ast_unparse` (the default-node → text renderer) and `Parameter(...)`
  construction are NOT modeled callees consumed by an axiom — they are subsumed
  into the `defaults : List String` input and the `Option String` result. No
  `opaque`/`axiom` callee contract is declared (G-AX is a skip stub).

## G-CONF fuzz seed

Pinned seed: **7757** (also in `conformance_check.py`).
