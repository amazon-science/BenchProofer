# refinement.md — sympy__sympy-15809

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`constructMinMax` `do` block, plus the `minMaxResult` pure model and the
`processArgs_nil` axiom) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A** (axiomatized callee — **A-consumed** where the
proof uses the axiom's `ensures`, **A-reference** where a deep model is validated
== the real callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`);
the A leg and this narrative are audited by **G-EQ**. Claim: any impl verifying
against this frozen spec, refined per the map below, is behaviourally equal to the
gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The extremum constructor — `MinMaxBase.__new__` (`miscellaneous.py:341`)

Gold hunk:
```
 class MinMaxBase(Expr, LatticeOp):
     def __new__(cls, *args, **assumptions):
-        if not args:
-            raise ValueError("The Max/Min functions must have arguments.")

         args = (sympify(arg) for arg in args)
```
The two-line empty-argument guard is DELETED, so an empty call falls through the
unchanged pipeline to the pre-existing `if not args: return cls.identity` tail.

| # | Solution.lean impl op (`constructMinMax`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `rawArgs : List Int` | the `*args` tuple of `__new__` | R | each SymPy argument ↔ a distinct `Int` handle; empty tuple ↔ `[]` (mapping.md §2). Only count + emptiness are observed. |
| A2 | parameter `idv : Int` | `cls.identity` (`Min.identity = oo`, `Max.identity = -oo`) | R | identity element ↔ opaque `Int`, observed by equality with the result (mapping.md §2). |
| A3 | `match processArgs rawArgs with …` | `frozenset(_new_args_filter(...))` → `_collapse_arguments` → `_find_localzeros` (the unchanged `args` normalisation, `miscellaneous.py:347–360`) | A-consumed | the normalisation chain is an UNCHANGED callee, modeled `opaque`; the proof consumes exactly `processArgs_nil` (`processArgs [] = []`). No claim about non-empty survivors (directive 7). G-AX validates `processArgs_nil` against the real pipeline. |
| A4 | `[] ⇒ Except.ok (identityResult idv)` | `if not args: return cls.identity` (`:361–362`) | I | identical control op: empty surviving set ⇒ return the identity element. THIS is the branch the deleted guard previously made unreachable for an empty call. |
| A5 | `[a] ⇒ Except.ok (single a)` | `if len(args) == 1: return list(args).pop()` (`:364–365`) | I | identical: lone survivor returned verbatim. Unchanged by the patch. |
| A6 | `a :: b :: rest ⇒ Except.ok (combined …)` | `Expr.__new__(cls, _args, ...)` extremum object (`:367–370`) | I | identical: two-or-more survivors ⇒ build the `Max`/`Min` object. Unchanged by the patch. |

Discriminating content of the change — an empty argument list must yield the
identity element, NOT a failure — lives in the postcondition `rawArgs = [] →
out = Except.ok (identityResult idv)` together with `minMaxResult`'s empty branch
(which depends on `processArgs_nil`). `Solution_prepatch.lean` reproduces the
pre-patch guard (`if rawArgs = [] then Except.error noArguments`) and **fails**
exactly that clause (G-DIFF: the goal `¬ rawArgs = []` is unprovable).

## B. No separate axioms beyond `processArgs_nil`

`processArgs` is `opaque` with no general contract; the single consumed axiom
`processArgs_nil` is the empty-normalisation fact. There is NO axiom about the
function under change (`__new__` itself), and no dead axiom: `processArgs_nil` is
used by `prove_correct` (via `simp_all [minMaxResult, processArgs_nil]`) to
discharge both the `out = minMaxResult …` and the empty-case postconditions.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The operation that genuinely *changed* — removing the
empty-input rejection so the empty collection's extremum is the identity element —
is modeled directly by the empty branch of `minMaxResult`/the `do` block (A4, an
I op reachable on the empty input), and the spec pins it via the empty-case
postcondition. The only consumed axiom (`processArgs_nil`) covers an UNCHANGED
helper, not the function under change.

## D. verify(Solution) ⇒ resolved

`constructMinMax` verifies only if (i) its output equals the count-driven
`minMaxResult` dispatch on every input and (ii) on the empty input it returns the
identity element. By A1–A2 (`*args ↔ List Int`, `cls.identity ↔ idv`) and A4–A6
(the three result legs are identical concrete ops, transliterated by G-CONF), the
verified constructor equals the gold-patched `MinMaxBase.__new__` on the tested
inputs; by G-AX (run on the base repo) the real normalisation pipeline satisfies
`processArgs_nil` (A-consumed) and the non-empty single/combined legs are real;
the empty → identity leg (A4 on the empty input — the patched-constructor
behaviour, unreachable on base) is validated by G-RESOLVE and by G-CONF, which
applies the gold patch and confirms the R/I transliteration agrees with
`patch.diff`'s behaviour (the gold-patched `Max`/`Min` constructor) on ≥10⁵
inputs including the empty call. Therefore a model satisfying
this spec, refined by the map above, is the gold patch up to type refinement and
the one audited unchanged callee — and the gold patch resolves (G-RESOLVE). Trust
points are exactly the two of plan §1.1: axiom soundness (G-AX) and refinement
fidelity (this doc, G-EQ + G-CONF).
