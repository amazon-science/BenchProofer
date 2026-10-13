# refinement.md — sympy__sympy-16450

Operation correspondence between `implementation_posify` and the gold
`patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real callee by
G-AX/G-CONF), **I** (identical concrete op).

No axiom is declared or consumed. The single changed operation (which declared
property set is handed to the replacement-symbol constructor) is modeled DEEPLY:
the filter predicate `signUndetermined` and the augmented declaration
`assertPositive` are spelled out in Lean. The only opaque dependency is the
symbol-construction+inference closure, carried as a pair — the total domain
question `declAccepted` and the operation `resolveAssumptions` on that domain —
both tagged **A-reference** and validated against the real callee by G-CONF. Every
row is **R**, **A-reference**, or **I**. G-AX is a skip stub (no consumed axiom).

## `implementation_posify` ↔ the scalar branch of `posify`

The gold patch turns

```python
reps = {s: Dummy(s.name, positive=True)                          # PRE-PATCH
             for s in eq.free_symbols if s.is_positive is None}
```

into

```python
reps = {s: Dummy(s.name, positive=True, **s.assumptions0)        # POST-PATCH
             for s in eq.free_symbols if s.is_positive is None}
```

with the surrounding `eq.subs(reps)` and the returned inverse map unchanged.
The observable behavior is the property record (`assumptions0`) of each
replacement symbol — and, since the constructor is partial, whether the call
produces records at all.

| Lean op | patch.diff / source counterpart | tag | note |
|---|---|---|---|
| recursion over `a :: as` | dict-comprehension over `eq.free_symbols` | R | a symbol ↦ its `assumptions0`; the set comprehension ↦ a structural recursion. Order not observable (G-CONF compares as a multiset) |
| `if signUndetermined a` | `if s.is_positive is None` | I | filter predicate; `is_positive is None ⟺ 'positive' ∉ assumptions0` (fuzz-verified, mapping.md) |
| `assertPositive a` = `("positive",true) :: a` | `positive=True, **s.assumptions0` (kwargs to `Dummy`) | A-reference | the EDITED op: the replacement is declared with the original symbol's full property set **augmented** by positivity, not bare positivity. Modeled deeply; the leading pair is the explicit keyword and the tail is the splatted record, which is what makes a record that already states `positive` supply it twice |
| `if h : declAccepted (assertPositive a) = true` | the `Dummy(...)` call either completing or not | A-reference | the constructor is PARTIAL (duplicate keyword, or values that cannot hold together). The Lean shape asks the total question first; the real code asks it by making the call. Validated == "the real call completes" by G-CONF |
| `resolveAssumptions (assertPositive a) h` | `Dummy(s.name, **decl).assumptions0` | A-reference | the UNCHANGED construction+inference closure, as an operation on its domain: applicable only together with the yes-answer `h`, so no term names the record of a declaration that has none. G-CONF validates the composite against the real `posify` replacement records |
| `(… ).map (fun rs => r :: rs)` / `none` | `reps = { … }` ; `eq.subs` ; return inverse map, or the call RAISING | R | the bundle observes the list of replacement records, or the absence of any (`Option`); `subs`/inverse-map bookkeeping is identity relabeling, not an observable of the modeled property |

## Why the definedness leg is part of the modeled behavior

`Dummy(name, positive=True, **s.assumptions0)` does not complete for every
symbol. For a sign-undetermined symbol whose properties cannot hold together with
positivity it raises `InconsistentAssumptions`, and then `posify` has no value at
all: measured at 74 of the 3280 sign-undetermined symbols reachable from 1-, 2- and
3-key declarations (2.26%; see mapping.md for the enumeration and the reproduction
commands). Pre-patch, `posify(Symbol('x', rational=False, irrational=False))`
returns `(_x, {_x: x})`; post-patch the same call raises. So the exceptional
outcome is a behavior of the patched routine, and a model that claimed a total
result would be describing neither version.

The definedness is scoped to the KEPT symbols, and that scoping is itself part of
the behavior: the declaration a NOT-replaced symbol would give rise to is never
formed by the real routine (it is the one that would supply `positive` twice), so
its refusal cannot make the call valueless. `conformance_check.py` asserts both
directions and fails unless it has exercised a valued case, a valueless case, and
a case where a not-replaced symbol's would-be declaration is refused while the
call still returns.

## Why the domain is carried as a dependent argument

A total oracle over declarations makes `map` and `filter` commute in the model:
"apply the oracle to every symbol, select afterwards" is then propositionally
equal to "select, then apply". In Python those two are not the same program — the
first forms a declaration for a symbol the filter excludes, and that declaration
is refused — so a total model admits an implementation whose patch raises on the
F2P input. Neither an `Option`-valued total oracle nor a returned call trace closes
that gap by itself: a pure total term can always be evaluated and discarded.

Carrying the partial operation as an operation on its DOMAIN does close it. With
`resolveAssumptions` applicable only together with `declAccepted decl = true`, an
implementation whose definedness depends on a not-replaced symbol's declaration is
no longer provably equal to the spec: the spec's `dite` scopes definedness to the
kept declarations, whether an excluded declaration is accepted is an opaque
question, and an implementation that propagates the answer cannot be shown to
agree. (Mechanically confirmed, see the audit record below.) The same repair is
recorded on `astropy__astropy-7671` for the same class of hole.

What remains admitted is an implementation that ASKS the domain question at every
symbol and discards the answer for the ones it does not replace. That is
behaviour-preserving: the faithful Python of "ask" is a probe that completes
whichever way it comes out, so such a patch resolves. It ships as the positive
control `pos-probe-every-symbol` in `properties.py` rather than being left
undocumented.

## Independently-observable behavior (G-DIFF)

- `Solution_prepatch.lean`: the replacement record is built from a bare
  positivity assertion (`resolveAssumptions [("positive", true)] h`) instead of
  `resolveAssumptions (assertPositive a) h`, dropping the original symbol's other
  declared properties. The carried correctness script fails to close: for any `a`
  carrying a property beyond positivity (e.g. `("finite", true)`),
  `resolveAssumptions [("positive",true)]` need not equal
  `resolveAssumptions (("positive",true) :: a)`, and the two definedness questions
  are different questions as well. This is the single fixed behavior.
  (FAIL_TO_PASS: `test_posify`.)

## Audit record — the totality hole and its closure

The earlier revision of this bundle declared
`opaque resolveAssumptions : Assumptions → Assumptions`, a TOTAL pure function on
every declaration list, and a total `result : List Assumptions`. Two consequences
were recorded against it:

- **G-EQ / G-PANEL-1 (spec-too-weak), BROKEN.** `atk_13.lean` (map-then-filter:
  apply the oracle to every symbol, select afterwards) and `atk_14.lean` (a
  precomputed zip/lookup list) both closed `correct_posify` with clean axioms,
  and both refined to patches that raise `TypeError` on the first assertion of
  `test_posify` — applied, `resolved=False`, F2P `test_posify` and P2P
  `test_separatevars` failing.
- **G-PANEL-2 (faithfulness).** The total model claimed a result for a
  sign-undetermined symbol carrying `rational=False, irrational=False`, where the
  patched routine raises. The differential check had not caught it because it
  swallowed the exception (`except Exception: continue`); it now asserts the raise
  correspondence in both directions instead.

Both records are the same defect, and the repair is the one above. Confirmed
mechanically in a scratch worktree, on the repaired spec:

- the `atk_13` shape re-encoded against the repaired spec (definedness propagated
  from every symbol, selection afterwards) is REFUTED: with the acceptance of the
  excluded symbol's declaration bound to `false` — an admissible reading of an
  opaque predicate — the attack's value at `[[("positive", true)]]` is `none`
  where the spec demands `some []`, and the refutation elaborates;
- the gold implementation still verifies with axioms `[propext, Quot.sound]`;
- the probe-and-discard residual verifies, and is shipped as a positive control.
