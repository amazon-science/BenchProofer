# mapping.md — sympy__sympy-16792

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 09786a173e7a0a488f46dd6000177c23e5d24eed`, states the type
abstraction (the Lean↔Python bijection used by G-CONF), and records the pinned
fuzz seed.

Repo file under change: `sympy/utilities/codegen.py`.
Changed method: `CodeGen.routine(self, name, expr, argument_sequence=None,
global_vars=None)` (`codegen.py:577`). The behavioural change lives in the
`argument_sequence is not None` branch's fall-through arm (`codegen.py:738–743`
pre-patch); a second hunk (`codegen.py:695–714`) extracts a local
`dimensions(s)` helper without changing behaviour (a pure refactor).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `buildArgList (requests : List ArgSpec)` | the construction of the positional argument list for the requested `argument_sequence` — the `for symbol in argument_sequence:` loop, `codegen.py:738–743` | the modeled changed behaviour: turn each requested symbol into a positional argument, attaching dimension metadata to array-like ones |
| `ArgSpec.alreadyResolved : Bool` | whether `symbol` is found in `name_arg_dict` (`try: name_arg_dict[symbol]`, `codegen.py:740`) | the requested symbol was already turned into an argument while scanning the expression (reuse it verbatim) vs. it must be built fresh (the `except KeyError:` arm, `codegen.py:741`) |
| `ArgSpec.prior : Arg` | `name_arg_dict[symbol]` (`codegen.py:740`) | the already-built argument reused unchanged |
| `ArgSpec.arrayLike : Bool` | `isinstance(symbol, MatrixSymbol)` for the **normalized** requested symbol reaching the fall-through arm (the post-patch guard at `codegen.py:744` reads `isinstance(symbol, (IndexedBase, MatrixSymbol))`, but the `IndexedBase` disjunct is unreachable there: `routine()` replaces every requested `IndexedBase` by its `.label` — a plain `Symbol` — at `codegen.py:719–727`, *before* this loop) | whether the normalized requested symbol owns a shape (array-like) vs. a plain scalar |
| `ArgSpec.extents : List Int` | `symbol.shape` of the normalized symbol (`codegen.py` post-patch helper `dimensions(s)`) | the per-axis extents of an array-like symbol |
| `extentBounds (extents)` | the helper `dimensions(s) = [(S.Zero, dim - 1) for dim in s.shape]` (`codegen.py:698–700` post-patch) | the dimension metadata: each axis `d` ↦ inclusive bound pair `(0, d-1)` |
| `argFor (e : ArgSpec)` | one iteration of the `for symbol in argument_sequence:` loop body (`codegen.py:738–743`) | the argument produced for one requested symbol |
| `Arg.bounds : List (Int × Int)` | the `dimensions` attribute of the produced `InputArgument` (passed via `**metadata`) (`Variable.dimensions`, `codegen.py:330`) | the argument's dimension metadata (empty ⇒ scalar; non-empty ⇒ array-like, later emitted by reference) |
| `out : List Arg` | the rebuilt `arg_list = new_args` (`codegen.py:743`) | the requested positional argument list |

No callee is consumed as a contract. Every observable is computed from the
inputs (the per-symbol kind and shape); there is no opaque oracle and no
`axiom_check.py` (no axioms in the bundle).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| a requested `argument_sequence` | `List ArgSpec` | the ordered requested symbols ↔ the list of per-request descriptors; order + count preserved |
| `symbol in name_arg_dict` (resolved) | `ArgSpec.alreadyResolved : Bool` | found ↔ `true` (reuse `prior`); `KeyError` ↔ `false` (build fresh) |
| `isinstance(symbol, MatrixSymbol)` on the normalized requested symbol (see the normalization note below) | `ArgSpec.arrayLike : Bool` | array-like (owns a shape) ↔ `true`; plain `Symbol` ↔ `false` |
| `symbol.shape` (a tuple of axis extents) | `ArgSpec.extents : List Int` | `(d₀, d₁, …)` ↔ `[d₀, d₁, …]` |
| `Argument.dimensions` attribute | `Arg.bounds : List (Int × Int)` | `None`/empty (no metadata) ↔ `[]`; `[(lo₀,hi₀), …]` (sympy `Integer` pairs) ↔ `[(lo₀,hi₀), …]` (the SAME pairs as plain ints). `dimensions(s) = [(0, d-1) …]` ↔ `extentBounds` exactly. |
| the produced positional `arg_list` | `List Arg` | the list of per-symbol arguments, in requested order |

Lean `Int` carries the axis extents and bounds exactly (sympy uses
`S.Zero`/`Integer` literals for these bounds — order-and-value, not float).

**Sequence-normalization note (the fall-through arm's reachable domain).**
`routine()` normalizes the user-supplied `argument_sequence` BEFORE the modeled
fall-through loop: every `IndexedBase` entry is replaced by its `.label`, a
plain `Symbol` with no `.shape` (`codegen.py:719–727`, unchanged by the patch).
The modeled loop therefore only ever sees `MatrixSymbol` (array-like) or plain
`Symbol` (scalar) requests. The bijection above is stated over this
**normalized** sequence: a requested `IndexedBase` maps to an `ArgSpec` for its
label — `alreadyResolved` iff the label is in `name_arg_dict` (e.g. the base
occurred as `Indexed` in the expression, in which case the prior argument
carries the extent bounds computed at scan time), else fresh with
`arrayLike = false` (its label is a shapeless `Symbol`, so the real patched
code attaches no dimension metadata: `.dimensions = None ↔ []`). Verified
against the real patched `routine()`: `IndexedBase('A', shape=(3,))` absent
from the expression yields `.dimensions = None` (scalar leg), matching the
model's `arrayLike = false` request; the same base occurring in the expression
resolves to a prior argument with bounds `[(0, 2)]`, matching the
`alreadyResolved`/`prior` leg. `conformance_check.py` fuzzes IndexedBase
requests through this normalization alongside MatrixSymbol/Symbol ones.

**Resolved-symbol note (A-reference-free).** For a requested symbol that *was*
already built (`alreadyResolved = true`), its prior `Arg` is reused verbatim on
both legs; that prior was itself produced by the earlier array-symbol arm
(`codegen.py:704–714`), which post-patch uses the SAME `dimensions(s)` helper.
So the reused metadata equals `extentBounds` of its extents on both legs and
cancels in the G-CONF diff. The discriminating observable is the **fresh** arm:
whether a freshly-built array-like argument receives its dimension metadata
(post-patch) or empty metadata (pre-patch). G-CONF fuzzes the fresh arm (the
constant expression `1.0` ⇒ every requested symbol is absent from the
expression ⇒ every request takes the fresh arm — the exact issue scenario),
including IndexedBase requests exercised through the normalization pass.

## 3. Callee provenance

None. The fix attaches metadata computed directly from each requested symbol's
own kind and shape; it calls no unchanged community callee whose contract the
proof must borrow. The two `do`-block operations — selecting `prior` vs. a fresh
argument, and (for the fresh array-like case) computing `extentBounds` — are
concrete, transliterated directly by G-CONF (I/R legs). Hence there is no
consumed axiom and no `axiom_check.py` (opaque/absent ⇒ no checked-axiom
contract to validate; cf. django__django-12050).

The pre-patch repo symbols the change touches (refinement audit only, not in the
consumer spec view): the inline `dims = []; for dim in array.shape: …` block
(`codegen.py:706–710`, replaced by the `dimensions(s)` helper — behaviour
identical) and the fall-through `new_args.append(InputArgument(symbol))`
(`codegen.py:742`, which dropped all metadata — the bug).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`16792`** so the
consumer-side verdict (§11.3) is reproducible. It drives the REAL patched
`CCodeGen().routine("f", 1.0, argument_sequence=…)` in-process (no Docker/DB)
and reads each produced argument's `.dimensions`, diffing against the shadow
`argList` over the requested order. The expression is the constant `1.0` so
every requested symbol is absent from it — exactly the issue's "array argument
does not appear in the wrapped expr". Fuzzes MatrixSymbol (array-like, random
shapes) vs. plain Symbol (scalar) vs. IndexedBase (normalized to its label ⇒
scalar at the modeled loop) sequences of length 1–5, plus the F2P boundary
`MatrixSymbol('x', 2, 1)` and IndexedBase boundaries.
