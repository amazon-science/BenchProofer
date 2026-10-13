# refinement.md — sympy__sympy-23534

Maps every operation in `implementation_symbols` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses the
axiom), **A-reference** (deep-model callee validated == real callee by G-AX),
**I** (identical concrete op).

The fix is the one-line change in the sequence (`else`) branch of `symbols`:
the recursive call `symbols(name, **args)` → `symbols(name, cls=cls, **args)`.
The impl models the whole branch structure (string-token base case + sequence
recursion) so the bug is observable at the spec.

| # | impl op (`implementation_symbols`) | patch.diff / repo counterpart | tag | note |
|---|---|---|---|---|
| 1 | `match names with \| NameSpec.tok s => …` | `if isinstance(names, str):` arm | R | dispatch on token-vs-sequence; `NameSpec.tok ↔ str` (mapping.md) |
| 2 | `return SymResult.leaf cls s` | string arm: construct objects of class `cls` from the token | R | the constructed leaf is TAGGED with the requested class `cls`; the unchanged token-parsing internals (range expansion / escape handling / scalar-vs-tuple collapsing) are abstracted to the class-tag they carry, which is the only component the fix touches. `SymResult.leaf cls s ↔ symbols(token, cls=cls)`. |
| 3 | `\| NameSpec.seq items => … for nm in items.attach do …` | `else: for name in names:` loop over the sequence | I | per-element iteration over the input container, same order |
| 4 | `implementation_symbols cls nm.val` (recursive, **threading `cls`**) | `result.append(symbols(name, cls=cls, **args))` — THE FIX | R | the recursion carries the requested class to every sub-spec; mirrors the patched recursive call. (Pre-patch dropped `cls` → `defaultClass`.) |
| 5 | `result := result ++ [ … ]` / `return SymResult.node result` | `result.append(...)` then `return type(names)(result)` | I | accumulate sub-results into a same-shape container (`SymResult.node ↔ type(names)(...)`) |

Every step is R or I — no changed-inexpressible op, no consumed axiom, no opaque
A-reference callee. The constructed-leaf result is modeled CONCRETELY as a
class-tagged leaf (`SymResult.leaf cls s`) rather than an opaque callee, so the
proof of `correct_symbols` discharges entirely by structural induction with no
`_prop`. `axioms: []`; `axiom_check.py` is a skip stub. The R/I legs are
mechanically refuted by G-CONF against the patched `sympy.symbols`.
