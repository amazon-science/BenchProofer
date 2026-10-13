# mapping.md — sympy__sympy-23534

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 832c24fec1046eaa544a4cab4c69e3af3e651759`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each axiom.

Repo file under change: `sympy/core/symbol.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `buildSeq (names : List String) (cls : SymCls)` | the sequence-input branch of `symbols(names, *, cls=Symbol, **args)` — `sympy/core/symbol.py:793-796` (the `else:` arm that loops over a non-`str` `names`) | the modeled changed function: builds one object-group per element name |
| `buildName` *(axiom — A-consumed)* | `symbols(name, cls=…, **args)` invoked on a SINGLE element (the `str`-input branch, `sympy/core/symbol.py:737-790`) | unchanged community callee: the per-element builder the loop recurses into |
| `buildName_cls` *(axiom — A-consumed)* | property of the `str`-input branch: `cls(literal(name), **args)` / `cls(s, **args)` construct objects of class `cls` (`symbol.py:744`, `:782`, `:784`) | the weakest relied-on contract: every built object carries the requested class |
| `expand (names : List String) (cls : SymCls)` | the result list `result` accumulated by the `else:` loop, post-fix | pure spec: the per-element groups, each built under the SAME `cls` |
| `SymCls` (`.sym`/`.func`/`.wild`) | the `cls` keyword argument's value (`Symbol` / `Function` / `Wild`) and, dually, the class of each produced object (`Symbol` / `UndefinedFunction` / `Wild`) | the observable property the issue + F2P test constrain (`type(...)`) |

The pre-patch repo symbol the change fixes (refinement audit only, not named in
the consumer spec view): the recursive call at `symbol.py:794`, which at
base_commit reads `result.append(symbols(name, **args))` — the `**args` dict
carries assumption flags but NOT `cls` (a keyword-only parameter, defaulted to
`Symbol`), so each nested group is built as the default leaf kind.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the `cls` keyword (a class object: `Symbol`/`Function`/`Wild`) AND the class of a produced object | `SymCls` (`.sym`/`.func`/`.wild`) | `Symbol ↔ .sym`; `Function ↔ .func`; `Wild ↔ .wild`. On the object side: `type(o) == Symbol ↔ .sym`, `type(o) == UndefinedFunction ↔ .func` (the metaclass instance `Function(name)` yields), `type(o) == Wild ↔ .wild`. The F2P test observes exactly `type(...)`. |
| a `names` sequence element (a single name `str`, possibly a range like `'q:2'`) | Lean `String` | element `nameᵢ` ↔ the `i`-th `String` in `names`; `len(names)` ↔ `names.length`; order preserved |
| `symbols(name, cls=C, **args)` on a single element → a `tuple`/object of built objects | `buildName name cls : List SymCls` | the per-element result flattened to the list of its leaf objects' class tags; we model only the class each object carries (the sole tested property) |
| the outer `else` result `type(names)(result)` (a `tuple`/`list` of per-element groups) | `expand names cls : List (List SymCls)` | each inner group = one element's `buildName`; the outer container's element ORDER is the bijection (the `tuple`/`list` wrapper is identity on element content/order) |

Only the CLASS of each produced object is modeled, because that is the entire
content of the fix and the only property the FAIL_TO_PASS test
(`type(symbols(('q:2','u:2'), cls=Function)[0][0]) == UndefinedFunction`)
observes. Names/assumption flags are passed through identically by both the
buggy and fixed code (the bug touches `cls` alone), so they are out of scope of
the differential.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `buildName` / `buildName_cls` ↔ the single-name `symbols` branch (A-consumed)
**Callee:** `symbols(name, cls=C, **args)` invoked on ONE element — the
`isinstance(names, str)` branch of `sympy/core/symbol.py` (lines 737-790). This
branch is UNCHANGED by the patch; the loop in the `else:` arm recurses into it
once per element. Its constructions are `cls(literal(name), **args)`
(`symbol.py:744`) for a plain name and `cls(s, **args)` /
`cls(literal(s), **args)` (`symbol.py:782`, `:784`) for a range — in every case
the produced object is an instance of (the metaclass of) `cls`.

The axioms encode only the obligation the sequence builder relies on:
`buildName_cls` — every object the per-name builder returns carries the
requested class `c`. We pin NOTHING about the names, count, or assumption flags
(directive 7: weakest sufficient contract). This is the property the fix needs:
once `cls` reaches the per-name builder, the per-name builder does the rest.

**Soundness check (G-AX):** `axiom_check.py` runs the REAL `symbols(name,
cls=C, **args)` on boundary name forms (plain, numeric range `q:2`, alpha range
`a:d`, multi-range, with assumption flags) for each `C ∈ {Symbol, Function,
Wild}`, and asserts every produced object's class matches `C` (the
`buildName_cls` ensures). Imports only `sympy`. Exit 0 iff sound.

There is **no A-reference** here: the sequence-level loop is modeled deeply (the
`expand` fold + the verified `while`); only the per-element builder is
axiomatized, and it is the genuinely unchanged callee. There is no consumed
axiom about the function under change.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`23534`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
the `else`-branch loop (R/I-tagged ops: iterate elements in order, recurse with
`cls` propagated, wrap with `type(names)`) to Python and leaves the per-element
`symbols(name, cls=…)` call as the REAL repo callee (A-tagged → run real
callee, not the axiom model). The oracle is the patched `symbols` at
base_commit. Both are compared on the CLASS tag of every produced leaf object.
