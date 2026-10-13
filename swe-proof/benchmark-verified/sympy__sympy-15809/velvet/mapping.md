# mapping.md — sympy__sympy-15809

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 28d913d3cead6c5646307ffa6540b21d65059dfd` (sympy 1.4), states the
type abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each axiom.

Repo file under change: `sympy/functions/elementary/miscellaneous.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `constructMinMax (idv : Int) (rawArgs : List Int)` | `MinMaxBase.__new__(cls, *args, **assumptions)` — `sympy/functions/elementary/miscellaneous.py:341` | the modeled changed function (the shared lattice-extremum constructor for `Max`/`Min`) |
| `processArgs` *(opaque; `processArgs_nil` is A-consumed)* | the unchanged normalisation pipeline run inside `__new__`: `_new_args_filter` → `_collapse_arguments` → `_find_localzeros` (`miscellaneous.py:347–360`, producing the local `args`) | unchanged argument-normalisation helper chain the constructor invokes |
| `idv : Int` | `cls.identity` — `Max.identity = S.NegativeInfinity` (`miscellaneous.py:731`), `Min.identity = S.Infinity` (`miscellaneous.py:796`) | the lattice identity element returned for the empty collection |
| `minMaxResult` | the result-decision tail of `__new__` (`miscellaneous.py:361–371`): `if not args: return cls.identity` / `if len(args)==1: return list(args).pop()` / else build the `Expr` object | pure spec: the result as a function of the normalised-member count |
| `MinMaxResult.identityResult` | `return cls.identity` (`miscellaneous.py:362`) | empty-collection branch |
| `MinMaxResult.single` | `return list(args).pop()` (`miscellaneous.py:365`) | single-survivor branch |
| `MinMaxResult.combined` | `Expr.__new__(cls, _args, ...)` extremum object (`miscellaneous.py:368–370`) | two-or-more-survivor branch |
| `MinMaxErr.noArguments` | the REMOVED guard `raise ValueError("The Max/Min functions must have arguments.")` (`miscellaneous.py:342–343`, pre-patch) | the failure the change eliminates (appears only in the pre-patch skeleton) |

The change itself (`patch.diff`): the two lines `if not args: / raise
ValueError(...)` at `miscellaneous.py:342–343` are DELETED, so a no-argument call
falls through the (unchanged) pipeline to the `if not args: return cls.identity`
tail at `:361–362`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the raw `*args` tuple of `__new__` | `rawArgs : List Int` | each SymPy argument is an opaque handle ↔ a distinct `Int`; the empty tuple ↔ `[]`; tuple length ↔ `rawArgs.length`. Only the COUNT of surviving members and the empty/non-empty distinction are observed, so an injective handle encoding is faithful (G-CONF bridges by indexing distinct sympy objects to distinct ints). |
| the normalised `args` set after the pipeline | `processArgs rawArgs : List Int` | the surviving-member multiset ↔ a `List Int` of the same cardinality; emptiness ↔ `[]`; `len(args)` ↔ `(processArgs rawArgs).length`. |
| `cls.identity` (`S.Infinity` / `S.NegativeInfinity`) | `idv : Int` | the identity element is an opaque handle ↔ a distinct `Int`; observed only by equality with the returned value. For `Min`, `idv ↔ oo`; for `Max`, `idv ↔ -oo`. |
| the returned SymPy object | `MinMaxResult` | `identityResult idv ↔ cls.identity`; `single a ↔` the lone surviving arg; `combined ms ↔` the built `Max`/`Min` object whose `.args` are the survivors. |
| `raise ValueError(...)` (pre-patch only) | `Except.error MinMaxErr.noArguments` | the eliminated failure; the post-patch constructor never takes this leg on the empty input — it returns `Except.ok (identityResult idv)`. |

The constructor's result for a NON-empty input is governed by `processArgs`,
modeled `opaque` with no asserted contract, so the spec makes no claim about which
members survive — it only pins the COUNT-driven dispatch and, load-bearingly, the
empty case. The ordering/collapse/local-zero logic of the pipeline is unchanged by
the patch and therefore deliberately left abstract (directive 7: do not over-claim
an unchanged callee).

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `processArgs` / `processArgs_nil` ↔ the normalisation pipeline (A-consumed)
**Callee:** the UNCHANGED chain `frozenset(cls._new_args_filter(args))` →
`cls._collapse_arguments(args, **assumptions)` → `cls._find_localzeros(args,
**assumptions)` inside `MinMaxBase.__new__` (`miscellaneous.py:347–360`). It is
modeled `opaque` and carries exactly ONE consumed axiom:

    processArgs_nil :  processArgs [] = []

i.e. normalising NO raw arguments yields NO surviving members. This is the
weakest fact the empty-input result depends on (with `processArgs [] = []`, the
post-patch fall-through lands in the `if not args: return cls.identity` branch).
We deliberately assert nothing else about the pipeline (it filters absorbing
elements, raises `ValueError` on non-comparable args such as `I`, collapses
nested extrema, etc.) — none of that is changed by the patch and none of it is
load-bearing for the modeled behaviour (directive 7).

**Soundness check (G-AX):** G-AX runs against the UNPATCHED base repo (the gates
apply NO patch for G-AX — it validates UNCHANGED callees), so every assertion
must hold on the base image. `axiom_check.py` runs the REAL pipeline
(`_new_args_filter`/`_collapse_arguments`/`_find_localzeros`) in-container on the
empty input for BOTH `Max` and `Min` and asserts the normalised set is empty
(`processArgs_nil`). The deleted guard sits in `__new__` ABOVE this pipeline, so
the pipeline itself is reached and behaves identically pre- and post-patch —
`processArgs_nil` is therefore a genuine unchanged-callee fact, base-valid. It
additionally establishes the NON-EMPTY A-reference legs (unchanged by the patch,
hence base-valid): a single-surviving input returns that member verbatim, and a
two-or-more input builds a `Max`/`Min` object — i.e. the `single`/`combined`
`MinMaxResult` legs are real. The 0-survivor → `cls.identity` leg (`Max() == -oo`,
`Min() == oo`) is the PATCHED-constructor behaviour: it is unreachable on the base
repo (the guard intercepts the empty call) and is the MODELED function's own
result, not an unchanged-callee fact — so it is deliberately NOT checked by G-AX.
It is validated instead by **G-RESOLVE** (the official `test_Min`/`test_Max`
assert `Min() == oo`, `Max() == -oo`) and **G-CONF** (which applies the gold
patch and asserts the empty case returns `cls.identity`). Imports only the repo
under test. Exit 0 iff every obligation holds.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`15809`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates the
COUNT-driven dispatch of `constructMinMax` (the R/I ops) to Python and leaves the
A-tagged `processArgs` as the REAL repo pipeline; the oracle is the gold-patched
`Max`/`Min` constructor itself. Both are compared on the observable outcome
(raises vs returns; and for returns, identity-element / lone-arg / built-object,
with the empty case asserted to return `cls.identity`).
