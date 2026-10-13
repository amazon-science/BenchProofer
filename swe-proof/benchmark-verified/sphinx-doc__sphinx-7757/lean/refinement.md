# refinement.md — sphinx-doc__sphinx-7757

Maps every operation in `implementation_positionalDefaults` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op). Every step is R, A, or I.

## Modeled function: the positional-parameter default alignment in `signature_from_str`

Post-patch repo code (`patch.diff`), the modeled block:
```python
defaults = list(args.defaults)
params = []
if hasattr(args, "posonlyargs"):
    posonlyargs = len(args.posonlyargs)
    positionals = posonlyargs + len(args.args)
else:
    posonlyargs = 0
    positionals = len(args.args)

for _ in range(len(defaults), positionals):
    defaults.insert(0, Parameter.empty)

if hasattr(args, "posonlyargs"):
    for i, arg in enumerate(args.posonlyargs):
        if defaults[i] is Parameter.empty:
            default = Parameter.empty
        else:
            default = ast_unparse(defaults[i])
        ...
        params.append(Parameter(arg.arg, POSITIONAL_ONLY, default=default, ...))

for i, arg in enumerate(args.args):
    if defaults[i + posonlyargs] is Parameter.empty:
        default = Parameter.empty
    else:
        default = ast_unparse(defaults[i + posonlyargs])
    ...
    params.append(Parameter(arg.arg, POSITIONAL_OR_KEYWORD, default=default, ...))
```

Lean impl (`implementation_positionalDefaults`): an imperative `Id.run do` that
starts from the supplied defaults (as `some`) and left-pads with `none` up to the
total positional count — yielding, per positional parameter in order, its default
or `none`. This is the same single alignment-across-the-whole-positional-run that
the patch introduces; the per-group `for` loops + `defaults[i]` / `defaults[i +
posonlyargs]` reads in the patch are exactly "the i-th positional parameter takes
the i-th entry of the padded defaults list", which is what the left-pad produces.

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `nPosonly nArgs : Nat`, `defaults : List String` | `len(args.posonlyargs)`, `len(args.args)`, `[ast_unparse(d) for d in args.defaults]` | **R** | counts ↔ `Nat`; the default-expression list ↔ `List String` via `ast_unparse` text (mapping.md bijection). The result `List (Option String)` ↔ the per-`Parameter` `default` field (`empty`↔`none`). |
| 2 | `let positionals := nPosonly + nArgs` | `positionals = posonlyargs + len(args.args)` | **I** | total positional count; identical arithmetic. (`hasattr(args,"posonlyargs")` is always true on the supported Py≥3.8 range — mapping.md; `nPosonly=0` recovers the else-branch.) |
| 3 | `let mut padded := defaults.map some` | `defaults = list(args.defaults)` (then each entry rendered by `ast_unparse`) | **R** | the supplied defaults, newest model carries each as `some text`; copy of the defaults list. |
| 4 | `for _ in [padded.length:positionals] do padded := none :: padded` | `for _ in range(len(defaults), positionals): defaults.insert(0, Parameter.empty)` | **I** | the FIXED operation: left-pad the defaults list with "no default" up to the positional count, so the supplied defaults land on the rightmost positions across BOTH groups. `Parameter.empty` ↔ `none`; `insert(0, …)` ↔ `none :: …`. |
| 5 | `return padded` (length `positionals`) | the two `for … enumerate(...)` loops reading `defaults[i]` / `defaults[i+posonlyargs]` and appending `Parameter(..., default=...)` | **I** (the alignment, deeply modeled) | after the left-pad, posonly param `i` reads `defaults[i]` and regular param `i` reads `defaults[i + posonlyargs]` — i.e. positional parameter `j` (0-based over the whole run) reads `padded[j]`. Iterating both groups in order and reading the padded list positionally is exactly returning `padded`. The `ast_unparse`/`empty` per-entry branch is the `some`/`none` already carried by `padded` (op 3/4). |

All impl-region ops are **R/I** — there is NO A-tagged (axiom) content, so the
impl is NOT all-A-tagged: `conf_skip = false`, and `conformance_check.py`
differential-tests the R/I shadow against an in-process replica of the post-patch
alignment.

## Soundness check (verify ⟹ correct)

- `problem_spec_positionalDefaults` pins `result` to a single closed equation:
  `replicate (nPosonly+nArgs - defaults.length) none ++ defaults.map some`.
  Directive 5 frame: every one of the `nPosonly+nArgs` result positions is fixed
  — the leading positions are exactly `none`, the trailing `defaults.length`
  positions are exactly the supplied defaults in order; nothing is left
  unconstrained. Directive 8: the result is grounded entirely in the inputs
  (`nPosonly`, `nArgs`, `defaults`), no ungrounded oracle.
- The discriminating clause is the placement of defaults across the WHOLE
  positional run. For `nPosonly=2, nArgs=1, defaults=["0","1"]` the spec demands
  `[none, some "0", some "1"]` (the second positional-only parameter carries its
  default). The prepatch impl gives positional-only parameters `none`
  unconditionally and aligns the single regular default within the regular group
  only, yielding `[none, none, some "1"]` — the `b=0` default vanishes. So the
  carried gold proof cannot close against the prepatch impl (G-DIFF/G-PANEL).
- This is exactly what the F2P test `test_signature_from_str_positionaly_only_args`
  exercises: `(a, b=0, /, c=1)` must give `b.default == '0'` and `c.default ==
  '1'` (post-patch); pre-patch `b`'s default was lost.
- G-CONF confirms the R/I shadow == an in-process replica of the post-patch
  alignment, over the modeled abstraction (param-group counts × default-list
  lengths × default contents) plus ≥1e5 fuzzed points (0 disagreements).
