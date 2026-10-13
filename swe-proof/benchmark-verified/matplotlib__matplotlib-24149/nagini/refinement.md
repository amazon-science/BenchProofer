# refinement.md — matplotlib__matplotlib-24149

The operation-by-operation correspondence between `model.py`'s implementation
(the two selection functions, the `any_finite` and `first_finite_value` deep
models, and the two axiomatized callees) and `patch.diff` (the gold patch). Each
step is tagged
**R** (type refinement), **A-consumed** (the proof uses an axiom's `Ensures`),
**A-reference** (a deep model is validated == a real callee by axiom_check.py /
G-AX), or **I** (identical concrete operation). The claim: *any implementation
that verifies against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies cleanly at `base_commit`
and is the real correctness oracle, G-RESOLVE).

The gold patch adds, to each of the two `try` blocks in `Axes._convert_dx`, an
`except StopIteration` clause that falls back from the first-finite selector to
the first-element-unconditional selector:

```
             try:
                 x0 = cbook._safe_first_finite(x0)
             except (TypeError, IndexError, KeyError):
                 pass
+            except StopIteration:
+                x0 = cbook.safe_first_element(x0)

             try:
                 x = cbook._safe_first_finite(xconv)
             except (TypeError, IndexError, KeyError):
                 x = xconv
+            except StopIteration:
+                x = cbook.safe_first_element(xconv)
```

The `try/except StopIteration: fall back to safe_first_element` control flow is
modelled deeply as the explicit choice
`if any_finite(seq): first_finite(seq) else: first_unconditional(seq)` — the
`StopIteration`-raising domain of `_safe_first_finite` (the list path) is exactly
`not any_finite(seq)` (mapping.md §3.1), so guarding the call by `any_finite` and
taking the `safe_first_element` fallback otherwise is the faithful, raise-free
skeleton of the patched `try/except`.

## A. The `x0` selection site — hunk 1 (`_axes.py:2181-2184` + added clause)

| # | model.py impl op (`select_position_x0`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `seq: List[int]` | `x0` (a list / numpy array of coordinates) | R | each coordinate abstracted to its finiteness flag; `seq[k] != 0` ↔ `safe_isfinite(x0[k])` (mapping.md §2). |
| A2 | `if any_finite(ToSeq(seq))` | the implicit "the `_safe_first_finite` generator yields at least one value" — i.e. no `StopIteration` is raised | A-reference (deep) + R | the StopIteration-domain is modelled deeply by the front-recursive `@Pure` fold `any_finite`; `any_finite(seq) == False` ↔ the real generator is empty ↔ `_safe_first_finite` raises (mapping.md §3.1, §3.3). Validated against the real callee by axiom_check.py (G-AX). |
| A3 | `first_finite(ToSeq(seq))` (the `if` branch) | `x0 = cbook._safe_first_finite(x0)` (the normal-return path) | A-consumed | `first_finite` is the weakest contract on `_safe_first_finite` that still grounds the result in the input: under `any_finite` it returns THE first finite element of the input (`Result() == first_finite_value(s)` — the element's value/identity, which in particular is finite). The proof consumes this `Ensures` to discharge the strengthened postcondition (1). G-AX confirms (against the real callee) that `_safe_first_finite` returns exactly that first finite element. |
| A4 | `first_unconditional(ToSeq(seq))` (the `else` branch) | `x0 = cbook.safe_first_element(x0)` (the added `except StopIteration` clause) | A-consumed | `first_unconditional` is the weakest contract on `safe_first_element`: it returns the first element (`Result() == s[0]`). The proof consumes this `Ensures` to discharge postcondition (2). G-AX confirms it. |
| A5 | `return rep` | the value `x0` ends up bound to, fed to `convert(x0 + ddx) - x` | I + R | the chosen representative flows on as the single anchor coordinate; the abstraction tracks only its finiteness (R), and "a value is produced (no exception escapes)" is the identical totality property (I). |
| A6 | `Requires(MustTerminate(2))` (precondition) | the selection block is bounded, loop-free code that always returns (falls out of the `try/except` + generator semantics) | I | total correctness: the patched code never diverges, so the model demands termination. Closes the vacuous-nontermination same-spec rival (G-PANEL-1 atk_4: correct value computed, then an endless loop before the return — verified under partial correctness, but its faithful real patch hangs `Axes.bar` and every F2P/P2P test, so it does NOT resolve). |

## B. The `xconv` selection site — hunk 2 (`_axes.py:2186-2189` + added clause)

`select_position_xconv` mirrors `select_position_x0` step-for-step against the
second hunk; the only difference in the real code is the non-`StopIteration`
fallback (`x = xconv` vs `pass`), which is outside the modelled behaviour (it
concerns `TypeError/IndexError/KeyError`, not the all-non-finite regression).

| # | model.py impl op (`select_position_xconv`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | parameter `seq: List[int]` | `xconv` (already unit-converted ndarray of coordinates) | R | finiteness-flag abstraction, as A1 (mapping.md §2). |
| B2 | `if any_finite(ToSeq(seq))` | the "generator yields a value / no StopIteration" condition for `xconv` | A-reference (deep) + R | as A2: deep `any_finite` ↔ real finite-element existence; G-AX-validated. |
| B3 | `first_finite(ToSeq(seq))` | `x = cbook._safe_first_finite(xconv)` (normal path) | A-consumed | as A3 (the result is pinned to `first_finite_value(s)`, the input's first finite element; mapping.md §3.1). |
| B4 | `first_unconditional(ToSeq(seq))` | `x = cbook.safe_first_element(xconv)` (added `except StopIteration` clause) | A-consumed | as A4 (mapping.md §3.2). |
| B5 | `return rep` | the value `x` ends up bound to, used in `convert(x0 + ddx) - x` | I + R | as A5. |
| B6 | `Requires(MustTerminate(2))` (precondition) | the selection block always returns | I | as A6 (total correctness / anti-vacuous-nontermination). |

## C. The differential witnesses (G-DIFF)

The discriminating content of the change — when the coordinate sequence has
**no** finite element, the selection must STILL produce a value (the first
element) rather than crash — lives in the `else` branch
(`first_unconditional`, A4/B4) plus the totality of the call.

- `model_prepatch.py` reverts hunk 1: `select_position_x0` drops the `else`
  branch and calls `first_finite(ToSeq(seq))` unconditionally. Under the
  function's precondition `len(seq) > 0` (which does **not** imply `any_finite`),
  `first_finite`'s `Requires(any_finite(s))` cannot be discharged on the
  all-non-finite input — the verifier reports exactly *"The precondition of
  function first_finite might not hold. Assertion any_finite(s) might not hold."*
  That is the spec sensing the missing `except StopIteration` (the crash).
- `model_prepatch_2.py` reverts hunk 2 the same way for `select_position_xconv`
  — the independent differential witness for the second site.

Each prepatch keeps the shared spec **byte-identical** (verified: axioms / pure /
pre / post / invariants regions hash-equal across all three files).

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, A-reference, or I. The operation that
genuinely *changed* — adding the `except StopIteration: safe_first_element(...)`
fallback — is modelled **deeply** as the `if any_finite … else …` choice
(A2/A4, B2/B4), guarded by the spelled-out `any_finite` fold (an A-reference
validated by G-AX). The two stdlib-style selectors `_safe_first_finite` /
`safe_first_element` are **unchanged** callees the patched code invokes; they are
the two A-consumed axioms, whose soundness G-AX checks against the real callees.
No axiom is dead: both `first_finite` (A3/B3) and `first_unconditional` (A4/B4)
have their `Ensures` consumed to discharge postconditions (1) and (2)
respectively. There is no axiom about the function under change (`_convert_dx`
itself is modelled, not axiomatized).

The selected representative's **value/identity** (not merely its finiteness) is
pinned by a second spelled-out front-recursive `@Pure` fold,
`first_finite_value` (pure region) — an **A-reference**: it is a structural
function of the input carrier (it skips leading non-finite flags and yields the
first finite element), so postcondition (1) (`Result() == first_finite_value(seq)`
under `any_finite`) and the `first_finite` axiom (`Ensures(Result() ==
first_finite_value(s))`) are dischargeable ONLY by actually selecting the input's
first finite element — not by echoing a constant of the asserted property (the
directive-8 ungrounded-marker hole the prior `Result() != 0` left open). G-AX
validates `first_finite_value` against the real `_safe_first_finite` (it returns
exactly the value at the first-finite index, with distinct finite floats so the
selected position is observable). It is NOT a consumed axiom; it is the witness
the postcondition and the axiom are pinned to.

## E. verify(model) ⇒ resolved

Each selection function carries `Requires(MustTerminate(2))`, so a verifying
implementation must actually RETURN (total correctness): a rival that computes
the right representative and then loops forever — the batch G-PANEL-1 atk_4
same-spec impl, whose faithful real patch hangs `Axes.bar` and every F2P/P2P
test — leaks the caller's termination obligation and is rejected
("Obligation leak check failed"). Beyond that, each selection function
verifies only if (1) under `any_finite` the result is
**the input's first finite element** (`Result() == first_finite_value(seq)`,
consuming the `first_finite` axiom — pinning the element's value/identity, so a
constant-echo cannot discharge it, and the representative the downstream
`convert(x0 + ddx) - x` consumes is the genuinely-selected coordinate, which the
datetime/timedelta units path `test_bar_timedelta` depends on) and (2) under
`not any_finite` the result is the first element — i.e. a value is produced at
all, consuming the `first_unconditional` axiom; the verifier rejects any impl
that, like the prepatch, fails to handle the all-non-finite case (G-DIFF), and
rejects any impl that fabricates a representative not equal to the input's first
finite element (the strengthened postcondition (1), batch05 G-EQ refinement). By R (coordinate
sequence ↔ `List[int]` finiteness flags, representative float ↔ flag) and by
G-AX (the two selectors meet their axioms against the real
`cbook._safe_first_finite` / `cbook.safe_first_element`, and `any_finite` matches
real finite-element existence including the base_commit StopIteration domain),
the verified selection equals the patched `try/except StopIteration` logic on
every input — in particular it does not raise on the all-NaN input the F2P test
`test_bar_all_nan` exercises (`ax.bar([np.nan], [np.nan])` now returns a bar with
a non-finite position instead of crashing), and the leading-NaN / all-finite P2P
cases are unchanged (the `if any_finite` branch returns the first finite element
as before). Therefore a model satisfying this spec, refined by the map above, is
the gold patch up to type refinement and audited callees — and the gold patch
resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1: axiom
soundness (G-AX) and refinement fidelity (this document, G-EQ).
